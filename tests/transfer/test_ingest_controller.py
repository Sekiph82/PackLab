from __future__ import annotations

import hashlib
import json
import struct
import zipfile
from pathlib import Path

import pytest

from packlab_core.packscan import PackScanError, write_packscan
from packlab_core.packscan import container as container_module
from packlab_studio.ingest import DeterministicFilePicker, ImportService, IngestController
from packlab_studio.quarantine import QuarantineStore


def _package(path: Path, repo_root: Path) -> Path:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = "ingest-capture"
    manifest["payloads"][0]["size_bytes"] = 3
    manifest["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})


def test_drop_and_picker_use_one_validating_service(tmp_path: Path, repo_root: Path) -> None:
    package = _package(tmp_path / "capture.packscan", repo_root)
    controller = IngestController(ImportService())
    dropped = controller.ingest_dropped([package])
    selected = controller.ingest_from_picker(DeterministicFilePicker(package))
    assert dropped[0].state == selected.state == "validated"
    assert dropped[0].capture_id == selected.capture_id == "ingest-capture"
    assert dropped[0].source_channel == "drop"
    assert selected.source_channel == "picker"


def test_drop_order_duplicates_extensions_directories_and_missing_paths_are_structured(tmp_path: Path, repo_root: Path) -> None:
    package = _package(tmp_path / "capture.packscan", repo_root)
    text = tmp_path / "capture.txt"
    text.write_text("not a package", encoding="utf-8")
    directory = tmp_path / "folder.packscan"
    directory.mkdir()
    controller = IngestController(ImportService())
    results = controller.ingest_dropped([package, package, text, directory, tmp_path / "missing.packscan"])
    assert [result.error_code for result in results] == [None, "duplicate_selection", "unsupported_extension", "directory_not_file", "missing_path"]
    assert controller.ingest_from_picker(DeterministicFilePicker(None)).error_code == "picker_cancelled"


def test_invalid_package_is_not_imported(tmp_path: Path) -> None:
    bad = tmp_path / "bad.packscan"
    bad.write_bytes(b"not zip")
    result = ImportService().import_path(bad, source_channel="drop")
    assert result.state == "rejected"


def test_malformed_deep_json_and_large_integer_are_quarantined(tmp_path: Path) -> None:
    malformed_values = {
        "deep": (b"[" * 1_100, "corrupt_manifest"),
        "integer": (b'{"value":' + b"9" * 5_000 + b"}", "corrupt_manifest"),
        "version": (
            json.dumps({"schema_version": "2.0.0"}).encode("utf-8"),
            "unsupported_future_version",
        ),
    }
    store = QuarantineStore(tmp_path / "quarantine")
    service = ImportService(quarantine=store)

    for label, (manifest, expected_error) in malformed_values.items():
        package = tmp_path / f"{label}.packscan"
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", manifest)
            archive.writestr("metadata/photos.json", b"{}")
            archive.writestr("checksums.json", b"{}")
        result = service.import_path(package, source_channel="drop")
        assert result.state == "quarantined"
        assert result.error_code == expected_error
    assert len(list(store.packages.glob("*.packscan"))) == len(malformed_values)


@pytest.mark.parametrize(
    ("raw_name", "declare_utf8"),
    [(b"a\x00e.bin", False), (b"a\x01e.bin", False), (b"a\xffe.bin", True)],
)
def test_packscan_preflight_rejects_noncanonical_raw_zip_names_before_zipfile(
    tmp_path: Path, monkeypatch, raw_name: bytes, declare_utf8: bool
) -> None:
    package = tmp_path / "raw-name.packscan"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("one.bin", b"1")
    payload = package.read_bytes()
    assert payload.count(b"one.bin") == 2
    forged = bytearray(payload.replace(b"one.bin", raw_name))
    if declare_utf8:
        local_header = forged.find(b"PK\x03\x04")
        central_header = forged.find(b"PK\x01\x02")
        local_flags = struct.unpack_from("<H", forged, local_header + 6)[0]
        central_flags = struct.unpack_from("<H", forged, central_header + 8)[0]
        struct.pack_into("<H", forged, local_header + 6, local_flags | 0x0800)
        struct.pack_into("<H", forged, central_header + 8, central_flags | 0x0800)
    package.write_bytes(forged)

    def unexpected_zipfile_materialization(*args, **kwargs):
        raise AssertionError("raw NUL entry names must fail before ZipFile materialization")

    monkeypatch.setattr(container_module.zipfile, "ZipFile", unexpected_zipfile_materialization)
    with pytest.raises(PackScanError) as error:
        container_module._load_archive(package)
    assert error.value.code == "unsafe_path"


def test_packscan_preflight_requires_utf8_flag_for_non_ascii_raw_names(
    tmp_path: Path, monkeypatch
) -> None:
    package = tmp_path / "unflagged-utf8.packscan"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("café.bin", b"1")
    payload = bytearray(package.read_bytes())
    local_header = payload.find(b"PK\x03\x04")
    central_header = payload.find(b"PK\x01\x02")
    assert local_header >= 0 and central_header >= 0
    local_flags = struct.unpack_from("<H", payload, local_header + 6)[0]
    central_flags = struct.unpack_from("<H", payload, central_header + 8)[0]
    struct.pack_into("<H", payload, local_header + 6, local_flags & ~0x0800)
    struct.pack_into("<H", payload, central_header + 8, central_flags & ~0x0800)
    package.write_bytes(payload)

    def unexpected_zipfile_materialization(*args, **kwargs):
        raise AssertionError("unflagged non-ASCII names must fail before ZipFile materialization")

    monkeypatch.setattr(container_module.zipfile, "ZipFile", unexpected_zipfile_materialization)
    with pytest.raises(PackScanError) as error:
        container_module._load_archive(package)
    assert error.value.code == "unsafe_path"


def test_oversized_package_is_quarantined_without_copying_it_unboundedly(
    tmp_path: Path, repo_root: Path, monkeypatch
) -> None:
    package = _package(tmp_path / "oversized.packscan", repo_root)
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_BYTES", 1)
    quarantine = QuarantineStore(tmp_path / "quarantine")
    result = ImportService(quarantine=quarantine).import_path(package, source_channel="drop")

    assert result.state == "quarantined"
    assert result.error_code == "package_too_large"
    assert not list((tmp_path / "quarantine" / "packages").glob("*.packscan"))
    records = list((tmp_path / "quarantine" / "records").glob("*.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record["events"][-1]["package_preserved"] is False


def test_expansion_limited_package_is_quarantined_before_raw_publication(
    tmp_path: Path, repo_root: Path, monkeypatch
) -> None:
    package = _package(tmp_path / "expansion-limited.packscan", repo_root)
    monkeypatch.setattr(container_module, "MAX_PACKSCAN_TOTAL_UNCOMPRESSED_BYTES", 1)
    quarantine = QuarantineStore(tmp_path / "quarantine")
    result = ImportService(quarantine=quarantine).import_path(package, source_channel="network")

    assert result.state == "quarantined"
    assert result.error_code == "package_expands_too_large"
    assert len(list((tmp_path / "quarantine" / "packages").glob("*.packscan"))) == 1
    assert not list((tmp_path / "raw").glob("*.packscan"))
