from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from packlab_studio.ingest_index import IngestIdentityConflict, IngestIndex, IngestIndexRecord
from packlab_studio.raw_store import RawEvidenceStore


def test_index_is_idempotent_and_fail_closed_for_identity_ambiguity(tmp_path: Path) -> None:
    index = IngestIndex(tmp_path / "index.json")
    first = IngestIndexRecord("capture", "a" * 64, "raw/a.packscan")
    assert index.register(first) == first
    assert index.lookup("capture", "a" * 64) == first
    with pytest.raises(IngestIdentityConflict, match="capture_id_conflict") as capture_conflict:
        index.lookup("capture", "b" * 64)
    assert capture_conflict.value.capture_id == "capture"
    assert capture_conflict.value.existing_digest == "a" * 64
    assert capture_conflict.value.incoming_digest == "b" * 64
    with pytest.raises(IngestIdentityConflict, match="digest_identity_ambiguity"):
        index.register(IngestIndexRecord("other", "a" * 64, "raw/a.packscan"))
    reopened = IngestIndex(tmp_path / "index.json")
    assert reopened.records() == [first]


def test_index_reconstructs_missing_or_corrupt_state_from_immutable_raw_metadata(tmp_path: Path) -> None:
    raw = RawEvidenceStore(tmp_path / "raw")
    source = tmp_path / "source.packscan"
    source.write_bytes(b"immutable")
    stored = raw.store(source, capture_id="capture", source_channel="drop")
    index = IngestIndex(tmp_path / "index.json")
    assert index.verify_against_raw_metadata(tmp_path / "raw")[0].package_sha256 == stored.package_sha256
    (tmp_path / "index.json").write_text("{not-json", encoding="utf-8")
    rebuilt = index.verify_against_raw_metadata(tmp_path / "raw")
    assert rebuilt == index.records()


def test_index_refuses_reconstruction_when_raw_metadata_digest_is_tampered(tmp_path: Path) -> None:
    raw = RawEvidenceStore(tmp_path / "raw")
    source = tmp_path / "source.packscan"
    source.write_bytes(b"immutable")
    stored = raw.store(source, capture_id="capture", source_channel="drop")
    package = tmp_path / "raw" / stored.raw_filename
    package.chmod(0o666)
    package.write_bytes(b"tampered")
    with pytest.raises(IngestIdentityConflict, match="raw_metadata_digest_mismatch"):
        IngestIndex(tmp_path / "index.json").verify_against_raw_metadata(tmp_path / "raw")


def test_concurrent_same_identity_has_one_authority(tmp_path: Path) -> None:
    index = IngestIndex(tmp_path / "index.json")
    record = IngestIndexRecord("capture", "a" * 64, "raw/a.packscan")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(index.register, [record] * 4))
    assert results == [record] * 4
    assert index.records() == [record]
