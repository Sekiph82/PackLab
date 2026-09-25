from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from packlab_studio.ingest import ImportService
from packlab_studio.raw_store import RawEvidenceStore, RawStoreError


def test_raw_store_is_content_addressed_and_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "capture.packscan"
    source.write_bytes(b"validated-package")
    store = RawEvidenceStore(tmp_path / "raw")
    first = store.store(source, capture_id="capture", source_channel="drop")
    second = store.store(source, capture_id="capture", source_channel="drop")
    digest = hashlib.sha256(b"validated-package").hexdigest()
    assert first == second
    assert first.package_sha256 == digest and store.verify(digest)
    metadata = json.loads((tmp_path / "raw" / f"{digest}.json").read_text(encoding="utf-8"))
    assert metadata == asdict(first)
    assert str(tmp_path) not in json.dumps(metadata)


def test_raw_store_fails_on_identity_conflict_and_detects_mutation(tmp_path: Path) -> None:
    source = tmp_path / "capture.packscan"
    source.write_bytes(b"same-bytes")
    store = RawEvidenceStore(tmp_path / "raw")
    record = store.store(source, capture_id="capture-a", source_channel="drop")
    with pytest.raises(RawStoreError, match="identity_conflict"):
        store.store(source, capture_id="capture-b", source_channel="drop")
    package = tmp_path / "raw" / record.raw_filename
    package.chmod(0o644)
    package.write_bytes(b"mutated")
    assert not store.verify(record.package_sha256)


def test_import_service_can_promote_only_validated_package_to_raw_store(tmp_path: Path, repo_root: Path) -> None:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = "raw-capture"
    manifest["payloads"][0]["size_bytes"] = 3
    manifest["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    from packlab_core.packscan import write_packscan

    package = write_packscan(tmp_path / "capture.packscan", manifest, {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})
    service = ImportService().with_raw_store(RawEvidenceStore(tmp_path / "raw"))
    assert service.import_path(package, source_channel="network").state == "raw_stored"
