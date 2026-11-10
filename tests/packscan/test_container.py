"""Focused PackScan container integrity and ZIP-boundary tests."""

from __future__ import annotations

import hashlib
import json
import struct
import zipfile
from pathlib import Path

import pytest

from packlab_core.packscan import PackScanError, read_packscan, write_packscan
from packlab_core.packscan import container as container_module

CANONICALIZATION = "sha256_32_bytes_lowercase_hex_64_chars_v1"


def _manifest(
    repo_root: Path, *, image_size: int = 3, image_sha: str | None = None
) -> dict[str, object]:
    source = repo_root / "tests" / "fixtures" / "packscan" / "manifest-valid.json"
    value = json.loads(source.read_text(encoding="utf-8"))
    payloads = value["payloads"]
    assert isinstance(payloads, list)
    image = payloads[0]
    metadata = payloads[1]
    assert isinstance(image, dict) and isinstance(metadata, dict)
    image["size_bytes"] = image_size
    image["sha256"] = image_sha or hashlib.sha256(b"IMG").hexdigest()
    metadata["size_bytes"] = 2
    metadata["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return value


def _write_raw(path: Path, files: dict[str, bytes]) -> None:
    checksums = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    files = dict(files)
    files["checksums.json"] = (
        json.dumps(
            {
                "schema_version": "1.0.0",
                "algorithm": "sha256",
                "canonicalization": CANONICALIZATION,
                "entries": checksums,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        order = [
            name
            for name in ["manifest.json", "metadata/photos.json", "checksums.json"]
            if name in files
        ]
        order += sorted(name for name in files if name not in order)
        for name in order:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _valid_files(manifest: dict[str, object]) -> dict[str, bytes]:
    return {
        "manifest.json": (
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8"),
        "images/0001.jpg": b"IMG",
        "metadata/photos.json": b"{}",
    }


def test_writer_is_deterministic_and_reader_returns_validated_payloads(
    tmp_path: Path, repo_root: Path
) -> None:
    manifest = _manifest(repo_root)
    payloads = {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"}
    first = write_packscan(tmp_path / "first.packscan", manifest, payloads)
    second = write_packscan(tmp_path / "second.packscan", manifest, payloads)
    assert first.read_bytes() == second.read_bytes()
    report = read_packscan(first)
    assert report.payloads == payloads
    assert (
        report.checksums["manifest.json"]
        == hashlib.sha256(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
            + b"\n"
        ).hexdigest()
    )


def test_authoritative_checksum_mismatch_is_distinguished(tmp_path: Path, repo_root: Path) -> None:
    manifest = _manifest(repo_root, image_size=7, image_sha=hashlib.sha256(b"ORIGINAL").hexdigest())
    files = _valid_files(manifest)
    files["images/0001.jpg"] = b"ALTERED"
    _write_raw(tmp_path / "authoritative-mismatch.packscan", files)
    with pytest.raises(PackScanError, match="checksum_mismatch_authoritative"):
        read_packscan(tmp_path / "authoritative-mismatch.packscan")


def test_truncated_entry_is_distinguished(tmp_path: Path, repo_root: Path) -> None:
    manifest = _manifest(repo_root, image_size=5, image_sha=hashlib.sha256(b"12345").hexdigest())
    _write_raw(
        tmp_path / "truncated.packscan",
        {**_valid_files(manifest), "images/0001.jpg": b"12"},
    )
    with pytest.raises(PackScanError, match="truncated_entry"):
        read_packscan(tmp_path / "truncated.packscan")


def test_missing_extra_duplicate_and_traversal_entries_are_rejected(
    tmp_path: Path, repo_root: Path
) -> None:
    manifest = _manifest(repo_root)
    valid = _valid_files(manifest)
    missing = dict(valid)
    missing.pop("metadata/photos.json")
    _write_raw(tmp_path / "missing-control.packscan", missing)
    with pytest.raises(PackScanError, match="missing_entry"):
        read_packscan(tmp_path / "missing-control.packscan")

    extra = dict(valid)
    extra["diagnostics/undeclared.json"] = b"{}"
    _write_raw(tmp_path / "extra.packscan", extra)
    with pytest.raises(PackScanError, match="extra_entry"):
        read_packscan(tmp_path / "extra.packscan")

    duplicate_path = tmp_path / "duplicate.packscan"
    with zipfile.ZipFile(duplicate_path, "w") as archive:
        info = zipfile.ZipInfo("../escape.bin", date_time=(1980, 1, 1, 0, 0, 0))
        archive.writestr(info, b"bad")
        archive.writestr("images/0001.jpg", b"bad")
    with pytest.raises(PackScanError, match="unsafe_path"):
        read_packscan(duplicate_path)


def test_exact_and_casefold_duplicate_names_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicates.packscan"
    with zipfile.ZipFile(path, "w") as archive:
        for name in ("images/0001.jpg", "images/0001.jpg"):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            archive.writestr(info, b"x")
    with pytest.raises(PackScanError, match="duplicate_entry"):
        read_packscan(path)


def test_optional_derived_payloads_are_safe_when_omitted(tmp_path: Path, repo_root: Path) -> None:
    manifest = _manifest(repo_root)
    report = read_packscan(
        write_packscan(
            tmp_path / "omitted-derived.packscan",
            manifest,
            {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"},
        )
    )
    assert not any(path.startswith(("previews/", "diagnostics/")) for path in report.payloads)


@pytest.mark.parametrize(
    ("mutation_name", "mutate"),
    [
        ("empty-device-model", lambda manifest: manifest["device"].update({"model": ""})),
        (
            "malformed-os-version",
            lambda manifest: manifest["device"].update({"os_version": "iOS seventeen"}),
        ),
        (
            "invalid-device-identifier",
            lambda manifest: manifest["device"].update({"device_identifier": "bad id!"}),
        ),
        (
            "invalid-lens",
            lambda manifest: manifest["device"].update({"lens": ""}),
        ),
        (
            "invalid-source-provenance",
            lambda manifest: manifest["source_evidence"].update({"provenance": ""}),
        ),
        (
            "invalid-optional-started-at",
            lambda manifest: manifest.update({"started_at": "2026-09-23T10:00:00+03:00"}),
        ),
        (
            "invalid-optional-media-type",
            lambda manifest: manifest["payloads"][0].update({"media_type": "Image/JPEG"}),
        ),
    ],
)
def test_validate_packscan_rejects_manifest_schema_drift(
    tmp_path: Path, repo_root: Path, mutation_name: str, mutate
) -> None:
    manifest = _manifest(repo_root)
    mutate(manifest)
    _write_raw(tmp_path / f"{mutation_name}.packscan", _valid_files(manifest))
    with pytest.raises(PackScanError) as error:
        read_packscan(tmp_path / f"{mutation_name}.packscan")
    assert error.value.code == "schema_invalid"


def test_validate_packscan_rejects_checksum_schema_drift(tmp_path: Path, repo_root: Path) -> None:
    manifest = _manifest(repo_root)
    files = _valid_files(manifest)
    checksums = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    files["checksums.json"] = (
        json.dumps(
            {
                "schema_version": "1.0.0",
                "algorithm": "sha256",
                "canonicalization": "lowercase_hex_64_bytes",
                "entries": checksums,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    with zipfile.ZipFile(
        tmp_path / "checksum-schema-drift.packscan",
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with pytest.raises(PackScanError) as error:
        read_packscan(tmp_path / "checksum-schema-drift.packscan")
    assert error.value.code == "invalid_checksums"


def test_packscan_loader_rejects_compressed_package_over_limit(tmp_path: Path, monkeypatch) -> None:
    package = tmp_path / "small.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("entry.bin", b"payload")
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_BYTES", 1)
    with pytest.raises(PackScanError) as error:
        container_module._load_archive(package)
    assert error.value.code == "package_too_large"


def test_packscan_loader_bounds_control_entry_size(tmp_path: Path, repo_root: Path, monkeypatch) -> None:
    package = write_packscan(
        tmp_path / "valid.packscan",
        _manifest(repo_root),
        {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"},
    )
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_CONTROL_ENTRY_BYTES", 1)
    with pytest.raises(PackScanError) as error:
        container_module._load_archive(package)
    assert error.value.code == "control_entry_too_large"


def test_packscan_writer_refuses_control_entry_above_control_limit(
    tmp_path: Path, repo_root: Path, monkeypatch
) -> None:
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_CONTROL_ENTRY_BYTES", 1)
    with pytest.raises(PackScanError) as error:
        write_packscan(
            tmp_path / "control-too-large.packscan",
            _manifest(repo_root),
            {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"},
        )
    assert error.value.code == "control_entry_too_large"
    assert not (tmp_path / "control-too-large.packscan").exists()


def test_packscan_writer_refuses_declared_payload_above_entry_limit(
    tmp_path: Path, repo_root: Path, monkeypatch
) -> None:
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_ENTRY_BYTES", 2)
    with pytest.raises(PackScanError) as error:
        write_packscan(
            tmp_path / "too-large.packscan",
            _manifest(repo_root),
            {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"},
        )
    assert error.value.code == "entry_too_large"
    assert not (tmp_path / "too-large.packscan").exists()


def test_packscan_writer_removes_temp_when_compressed_limit_is_exceeded(
    tmp_path: Path, repo_root: Path, monkeypatch
) -> None:
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_BYTES", 1)
    destination = tmp_path / "too-large.packscan"
    with pytest.raises(PackScanError) as error:
        write_packscan(
            destination,
            _manifest(repo_root),
            {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"},
        )
    assert error.value.code == "package_too_large"
    assert not destination.exists()
    assert not list(tmp_path.glob(".packscan-*.tmp"))


def test_packscan_loader_bounds_central_directory_entry_count(tmp_path: Path, monkeypatch) -> None:
    package = tmp_path / "many-entries.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("one.bin", b"1")
        archive.writestr("two.bin", b"2")
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_ENTRIES", 1)
    with pytest.raises(PackScanError) as error:
        container_module._load_archive(package)
    assert error.value.code == "too_many_entries"


def test_packscan_loader_rejects_eocd_count_smaller_than_central_directory(
    tmp_path: Path, monkeypatch
) -> None:
    package = tmp_path / "forged-count.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("one.bin", b"1")
        archive.writestr("two.bin", b"2")
    payload = bytearray(package.read_bytes())
    eocd = payload.rfind(b"PK\x05\x06")
    assert eocd >= 0
    struct.pack_into("<H", payload, eocd + 8, 1)
    struct.pack_into("<H", payload, eocd + 10, 1)
    package.write_bytes(payload)

    def unexpected_zipfile_materialization(*args, **kwargs):
        raise AssertionError("ZipFile must not materialize a forged central directory")

    monkeypatch.setattr(container_module.zipfile, "ZipFile", unexpected_zipfile_materialization)

    with pytest.raises(PackScanError) as error:
        container_module._load_archive(package)
    assert error.value.code == "corrupt_zip"


@pytest.mark.parametrize(
    ("field_offset", "value", "expected_code"),
    [
        (4, 1, "corrupt_zip"),  # disk number
        (6, 1, "corrupt_zip"),  # central-directory disk number
        (10, 0xFFFF, "too_many_entries"),  # ZIP64 entry-count sentinel
    ],
)
def test_packscan_loader_rejects_multidisk_and_zip64_eocd(
    tmp_path: Path, field_offset: int, value: int, expected_code: str
) -> None:
    package = tmp_path / "unsupported-layout.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("one.bin", b"1")
    payload = bytearray(package.read_bytes())
    eocd = payload.rfind(b"PK\x05\x06")
    assert eocd >= 0
    struct.pack_into("<H", payload, eocd + field_offset, value)
    package.write_bytes(payload)

    with pytest.raises(PackScanError) as error:
        container_module._load_archive(package)
    assert error.value.code == expected_code


def test_packscan_loader_rejects_archive_comment_before_zipfile(
    tmp_path: Path, monkeypatch
) -> None:
    package = tmp_path / "commented.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("one.bin", b"1")
        archive.comment = b"not canonical PackScan framing"

    def unexpected_zipfile_materialization(*args, **kwargs):
        raise AssertionError("archive comments must fail before ZipFile materialization")

    monkeypatch.setattr(container_module.zipfile, "ZipFile", unexpected_zipfile_materialization)
    with pytest.raises(PackScanError) as error:
        container_module._load_archive(package)
    assert error.value.code == "corrupt_zip"


@pytest.mark.parametrize(
    ("files", "entry_limit", "total_limit", "expected_code"),
    [
        ({"large.bin": b"123"}, 2, 100, "entry_too_large"),
        ({"one.bin": b"12", "two.bin": b"34"}, 100, 3, "package_expands_too_large"),
    ],
)
def test_packscan_loader_bounds_declared_uncompressed_payloads(
    tmp_path: Path,
    monkeypatch,
    files: dict[str, bytes],
    entry_limit: int,
    total_limit: int,
    expected_code: str,
) -> None:
    package = tmp_path / "expanded.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_ENTRY_BYTES", entry_limit)
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_TOTAL_UNCOMPRESSED_BYTES", total_limit)
    with pytest.raises(PackScanError) as error:
        container_module._load_archive(package)
    assert error.value.code == expected_code


def test_extract_packscan_rejects_source_change_after_validation(
    tmp_path: Path, repo_root: Path, monkeypatch
) -> None:
    source = write_packscan(
        tmp_path / "capture.packscan",
        _manifest(repo_root),
        {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"},
    )
    original_validate = container_module.validate_packscan
    original_manifest = _manifest(repo_root)
    changed_manifest = json.loads(json.dumps(original_manifest))
    changed_manifest["payloads"][0]["sha256"] = hashlib.sha256(b"ALT").hexdigest()

    def validate_then_replace(package: Path):
        report = original_validate(package)
        replacement = tmp_path / "replacement.packscan"
        write_packscan(
            replacement,
            changed_manifest,
            {"images/0001.jpg": b"ALT", "metadata/photos.json": b"{}"},
        )
        replacement.replace(package)
        return report

    monkeypatch.setattr(container_module, "validate_packscan", validate_then_replace)
    destination = tmp_path / "extracted"
    with pytest.raises(PackScanError, match="changed between validation and extraction"):
        container_module.extract_packscan(source, destination)
    assert not destination.exists()

