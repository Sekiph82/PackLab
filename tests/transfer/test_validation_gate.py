from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from packlab_core.packscan import write_packscan
from packlab_studio.ingest import ImportService


def _manifest(repo_root: Path, *, version: str = "1.0.0") -> dict[str, object]:
    value = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    value["schema_version"] = version
    value["capture_id"] = "validation-capture"
    value["payloads"][0]["size_bytes"] = 3
    value["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    value["payloads"][1]["size_bytes"] = 2
    value["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return value


def _valid(path: Path, repo_root: Path) -> Path:
    return write_packscan(path, _manifest(repo_root), {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})


def test_validation_precedes_atomic_extraction(tmp_path: Path, repo_root: Path) -> None:
    package = _valid(tmp_path / "valid.packscan", repo_root)
    result, extracted = ImportService().validate_then_extract(package, tmp_path / "payloads", source_channel="network")
    assert result.state == "validated"
    assert extracted is not None and (extracted / "manifest.json").exists()


def test_future_version_checksum_and_unsafe_zip_never_publish_extraction(tmp_path: Path, repo_root: Path) -> None:
    future = tmp_path / "future.packscan"
    files = {"manifest.json": json.dumps(_manifest(repo_root, version="2.0.0")).encode(), "metadata/photos.json": b"{}", "images/0001.jpg": b"IMG", "checksums.json": b"{}"}
    with zipfile.ZipFile(future, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    result, extracted = ImportService().validate_then_extract(future, tmp_path / "future-payloads", source_channel="drop")
    assert result.error_code == "unsupported_future_version" and extracted is None
    assert not (tmp_path / "future-payloads").exists()

    valid = _valid(tmp_path / "checksum.packscan", repo_root)
    with zipfile.ZipFile(valid, "a") as archive:
        archive.writestr("images/0001.jpg", b"CORRUPT")
    result, extracted = ImportService().validate_then_extract(valid, tmp_path / "checksum-payloads", source_channel="drop")
    assert result.error_code in {"duplicate_entry", "checksum_mismatch", "checksum_mismatch_authoritative"} and extracted is None
    assert not (tmp_path / "checksum-payloads").exists()

    unsafe = tmp_path / "unsafe.packscan"
    with zipfile.ZipFile(unsafe, "w") as archive:
        archive.writestr("../escape.bin", b"bad")
    result, extracted = ImportService().validate_then_extract(unsafe, tmp_path / "unsafe-payloads", source_channel="drop")
    assert result.error_code == "unsafe_path" and extracted is None
    assert not (tmp_path / "unsafe-payloads").exists()
