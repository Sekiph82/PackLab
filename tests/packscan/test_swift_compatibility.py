"""Windows-runnable compatibility checks for the committed Swift writer contract."""

from __future__ import annotations

import hashlib
import json
import re
import struct
import zipfile
import zlib
from pathlib import Path

import pytest

from packlab_core.packscan import PackScanError, read_packscan

_SWIFT_ENTRY_ORDER = ("manifest.json", "metadata/photos.json", "checksums.json", "images/0001.jpg")
_SWIFT_DOS_TIME_MIDNIGHT = 0x0000
_SWIFT_DOS_DATE_1980_JAN_1 = 0x0021
_SWIFT_UTF8_FLAG = 0x0800
_SWIFT_DEFLATE_METHOD = 0x0008


def _swift_input(repo_root: Path) -> tuple[dict[str, object], dict[str, bytes], dict[str, object]]:
    fixture_dir = repo_root / "tests" / "fixtures" / "packscan"
    fixture = json.loads(
        (fixture_dir / "swift-writer-contract-fixture.json").read_text(encoding="utf-8")
    )
    manifest = json.loads((fixture_dir / "manifest-valid.json").read_text(encoding="utf-8"))
    payloads = {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"}
    declared = manifest["payloads"]
    assert isinstance(declared, list)
    for item in declared:
        assert isinstance(item, dict)
        data = payloads[item["path"]]
        item["size_bytes"] = len(data)
        item["sha256"] = hashlib.sha256(data).hexdigest()
    return manifest, payloads, fixture


def _swift_canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _swift_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _swift_crc32(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xEDB88320 & -(crc & 1))
    return (~crc) & 0xFFFFFFFF


def _swift_raw_deflate(data: bytes) -> bytes:
    compressor = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-zlib.MAX_WBITS)
    return compressor.compress(data) + compressor.flush(zlib.Z_FINISH)


def _swift_source_derived_files(
    manifest: dict[str, object], payloads: dict[str, bytes]
) -> dict[str, bytes]:
    manifest_json = _swift_canonical_json(manifest)
    files = {"manifest.json": manifest_json}
    for name in sorted(payloads):
        files[name] = payloads[name]
    checksum_entries = {name: _swift_sha256(data) for name, data in files.items()}
    files["checksums.json"] = _swift_canonical_json(
        {
            "schema_version": "1.0.0",
            "algorithm": "sha256",
            "canonicalization": "sha256_32_bytes_lowercase_hex_64_chars_v1",
            "entries": checksum_entries,
        }
    )
    return files


def _append_swift_local_header(
    output: bytearray, name: str, data: bytes, compressed: bytes
) -> None:
    name_bytes = name.encode("utf-8")
    output.extend(
        struct.pack(
            "<IHHHHHIIIHH",
            0x04034B50,
            20,
            _SWIFT_UTF8_FLAG,
            _SWIFT_DEFLATE_METHOD,
            _SWIFT_DOS_TIME_MIDNIGHT,
            _SWIFT_DOS_DATE_1980_JAN_1,
            _swift_crc32(data),
            len(compressed),
            len(data),
            len(name_bytes),
            0,
        )
    )
    output.extend(name_bytes)
    output.extend(compressed)


def _append_swift_central_header(
    central: bytearray, name: str, data: bytes, compressed: bytes, offset: int
) -> None:
    name_bytes = name.encode("utf-8")
    central.extend(
        struct.pack(
            "<IHHHHHHIIIHHHHHII",
            0x02014B50,
            20,
            20,
            _SWIFT_UTF8_FLAG,
            _SWIFT_DEFLATE_METHOD,
            _SWIFT_DOS_TIME_MIDNIGHT,
            _SWIFT_DOS_DATE_1980_JAN_1,
            _swift_crc32(data),
            len(compressed),
            len(data),
            len(name_bytes),
            0,
            0,
            0,
            0,
            0,
            offset,
        )
    )
    central.extend(name_bytes)


def _build_source_derived_swift_package_bytes(files: dict[str, bytes]) -> bytes:
    output = bytearray()
    central = bytearray()
    offsets: dict[str, int] = {}
    compressed_by_name: dict[str, bytes] = {}
    for name in _SWIFT_ENTRY_ORDER:
        data = files[name]
        offsets[name] = len(output)
        compressed = _swift_raw_deflate(data)
        compressed_by_name[name] = compressed
        _append_swift_local_header(output, name, data, compressed)
    central_offset = len(output)
    for name in _SWIFT_ENTRY_ORDER:
        _append_swift_central_header(
            central, name, files[name], compressed_by_name[name], offsets[name]
        )
    output.extend(central)
    output.extend(
        struct.pack(
            "<IHHHHIIH",
            0x06054B50,
            0,
            0,
            len(_SWIFT_ENTRY_ORDER),
            len(_SWIFT_ENTRY_ORDER),
            len(central),
            central_offset,
            0,
        )
    )
    return bytes(output)


def _write_source_derived_swift_package(
    path: Path, manifest: dict[str, object], payloads: dict[str, bytes]
) -> tuple[Path, dict[str, bytes]]:
    files = _swift_source_derived_files(manifest, payloads)
    path.write_bytes(_build_source_derived_swift_package_bytes(files))
    return path, files


def test_swift_contract_fixture_validates_as_python_packscan(
    tmp_path: Path, repo_root: Path
) -> None:
    manifest, payloads, fixture = _swift_input(repo_root)
    package, files = _write_source_derived_swift_package(
        tmp_path / "swift-contract.packscan", manifest, payloads
    )
    report = read_packscan(package)
    with zipfile.ZipFile(package) as archive:
        infos = archive.infolist()
        assert [info.filename for info in infos] == fixture["expected_entry_order"]
        assert all(info.compress_type == zipfile.ZIP_DEFLATED for info in infos)
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in infos)
        assert all(info.flag_bits & _SWIFT_UTF8_FLAG for info in infos)
        assert all(info.extra == b"" for info in infos)
        assert json.loads(archive.read("metadata/photos.json")) == {}
        checksum_index = json.loads(archive.read("checksums.json"))
        assert set(checksum_index["entries"]) == {
            info.filename for info in infos if info.filename != "checksums.json"
        }
        assert archive.read("manifest.json") == files["manifest.json"]
        assert archive.read("checksums.json") == files["checksums.json"]
    assert report.manifest["schema_version"] == "1.0.0"
    assert report.payloads == payloads


def test_python_rejects_swift_contract_negative_manifest_hash_mutation(
    tmp_path: Path, repo_root: Path
) -> None:
    manifest, payloads, _ = _swift_input(repo_root)
    _, files = _write_source_derived_swift_package(
        tmp_path / "swift-contract.packscan", manifest, payloads
    )
    files = dict(files)
    files["images/0001.jpg"] = b"IMX"
    mutated_package = tmp_path / "swift-contract-mutated.packscan"
    mutated_package.write_bytes(_build_source_derived_swift_package_bytes(files))
    with pytest.raises(PackScanError, match="checksum_mismatch"):
        read_packscan(mutated_package)


def _swift_constant(source: str, name: str) -> int:
    match = re.search(rf"static let {name}: UInt16 = 0x([0-9a-fA-F]+)", source)
    assert match is not None
    return int(match.group(1), 16)


def test_swift_writer_source_and_header_contract_are_byte_level(repo_root: Path) -> None:
    source = (
        repo_root / "apps" / "ios-capture" / "PackLabCapture" / "PackScan" / "PackScanWriter.swift"
    ).read_text(encoding="utf-8")
    fixture = json.loads(
        (
            repo_root / "tests" / "fixtures" / "packscan" / "swift-writer-contract-fixture.json"
        ).read_text(encoding="utf-8")
    )
    expected = fixture["expected_zip"]
    assert "import Compression" not in source
    assert "import zlib" in source
    assert "deflateInit2_" in source
    assert "Z_BEST_COMPRESSION" in source
    assert "-MAX_WBITS" in source
    assert "dropFirst(2).dropLast(4)" not in source

    dos_time = _swift_constant(source, "dosTimeMidnight")
    dos_date = _swift_constant(source, "dosDate1980Jan1")
    flags = _swift_constant(source, "generalPurposeUTF8Flag")
    method = _swift_constant(source, "deflateMethod")
    assert dos_time == expected["dos_time"]
    assert dos_date == expected["dos_date"]
    assert flags == expected["general_purpose_flag"]
    assert method == expected["method"]
    assert expected["level"] == 9
    assert expected["raw_deflate_window_bits"] == -15

    crc = 0x12345678
    compressed_size = 9
    uncompressed_size = 3
    name = b"images/0001.jpg"
    local = (
        struct.pack(
            "<IHHHHHIIIHH",
            0x04034B50,
            20,
            flags,
            method,
            dos_time,
            dos_date,
            crc,
            compressed_size,
            uncompressed_size,
            len(name),
            0,
        )
        + name
    )
    local_fields = struct.unpack("<IHHHHHIIIHH", local[:30])
    assert local_fields == (
        0x04034B50,
        20,
        flags,
        method,
        dos_time,
        dos_date,
        crc,
        compressed_size,
        uncompressed_size,
        len(name),
        0,
    )
    assert local[30:] == name

    central = (
        struct.pack(
            "<IHHHHHHIIIHHHHHII",
            0x02014B50,
            20,
            20,
            flags,
            method,
            dos_time,
            dos_date,
            crc,
            compressed_size,
            uncompressed_size,
            len(name),
            0,
            0,
            0,
            0,
            0,
            42,
        )
        + name
    )
    central_fields = struct.unpack("<IHHHHHHIIIHHHHHII", central[:46])
    assert central_fields[0] == 0x02014B50
    assert central_fields[3:7] == (flags, method, dos_time, dos_date)
    assert central_fields[7:10] == (crc, compressed_size, uncompressed_size)
    assert central_fields[10:13] == (len(name), 0, 0)
    assert central_fields[-1] == 42
    assert central[46:] == name
