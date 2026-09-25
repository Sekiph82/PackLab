from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from packlab_core.packscan import write_packscan
from packlab_studio.ingest import ImportService
from packlab_studio.quarantine import QuarantineStore


def test_quarantine_preserves_invalid_bytes_and_redacted_record_idempotently(tmp_path: Path) -> None:
    source = tmp_path / ".." / "private-supplier-name.packscan"
    source = source.resolve()
    source.write_bytes(b"corrupt-package")
    store = QuarantineStore(tmp_path / "quarantine")
    service = ImportService(quarantine=store)
    first = service.import_path(source, source_channel="network")
    second = service.import_path(source, source_channel="network")
    digest = hashlib.sha256(b"corrupt-package").hexdigest()
    assert first.state == second.state == "quarantined"
    assert (tmp_path / "quarantine" / "packages" / f"{digest}.packscan").read_bytes() == b"corrupt-package"
    record = json.loads((tmp_path / "quarantine" / "records" / f"{digest}.json").read_text(encoding="utf-8"))
    assert len(record["events"]) == 2
    assert str(tmp_path) not in json.dumps(record)
    assert source.exists()


def test_future_and_unsafe_packages_are_quarantined_without_normal_artifacts(tmp_path: Path) -> None:
    future = tmp_path / "future.packscan"
    future.write_bytes(b"future bytes")
    service = ImportService(quarantine=QuarantineStore(tmp_path / "q"))
    result = service.import_path(future, source_channel="drop")
    assert result.state == "quarantined"
    assert not (tmp_path / "imported").exists()


def _valid_package(path: Path, repo_root: Path, capture_id: str = "quarantine-matrix") -> Path:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = capture_id
    manifest["payloads"][0]["size_bytes"] = 3
    manifest["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})


def test_quarantine_matrix_covers_future_schema_checksum_and_malicious_name(tmp_path: Path, repo_root: Path) -> None:
    valid = _valid_package(tmp_path / "valid.packscan", repo_root)
    future = tmp_path / "future.packscan"
    with zipfile.ZipFile(valid) as source, zipfile.ZipFile(future, "w") as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == "manifest.json":
                value = json.loads(data)
                value["schema_version"] = "99.0.0"
                data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"
            target.writestr(item, data)
    mismatch = tmp_path / "mismatch.packscan"
    with zipfile.ZipFile(valid) as source, zipfile.ZipFile(mismatch, "w") as target:
        for item in source.infolist():
            target.writestr(item, b"BAD" if item.filename == "images/0001.jpg" else source.read(item.filename))
    unsafe = tmp_path / "unsafe.packscan"
    with zipfile.ZipFile(valid) as source, zipfile.ZipFile(unsafe, "w") as target:
        for item in source.infolist():
            target.writestr(item, source.read(item.filename))
        target.writestr("../escape.bin", b"bad")
    service = ImportService(quarantine=QuarantineStore(tmp_path / "q"))
    results = [service.import_path(path, source_channel="network") for path in (future, mismatch, unsafe)]
    assert [result.state for result in results] == ["quarantined", "quarantined", "quarantined"]
    assert "unsupported_future_version" in {result.error_code for result in results}
    assert "checksum_mismatch" in {result.error_code for result in results}
    assert {result.error_code for result in results} & {"unsafe_path", "extra_entry"}
    assert not list((tmp_path / "raw").glob("*"))
    assert len(list((tmp_path / "q" / "packages").glob("*.packscan"))) == 3
