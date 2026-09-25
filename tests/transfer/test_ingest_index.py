from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from packlab_studio.ingest_index import IngestIdentityConflict, IngestIndex, IngestIndexRecord


def test_index_is_idempotent_and_fail_closed_for_identity_ambiguity(tmp_path: Path) -> None:
    index = IngestIndex(tmp_path / "index.json")
    first = IngestIndexRecord("capture", "a" * 64, "raw/a.packscan")
    assert index.register(first) == first
    assert index.lookup("capture", "a" * 64) == first
    with pytest.raises(IngestIdentityConflict, match="capture_id_conflict"):
        index.lookup("capture", "b" * 64)
    with pytest.raises(IngestIdentityConflict, match="digest_identity_ambiguity"):
        index.register(IngestIndexRecord("other", "a" * 64, "raw/a.packscan"))
    reopened = IngestIndex(tmp_path / "index.json")
    assert reopened.records() == [first]


def test_concurrent_same_identity_has_one_authority(tmp_path: Path) -> None:
    index = IngestIndex(tmp_path / "index.json")
    record = IngestIndexRecord("capture", "a" * 64, "raw/a.packscan")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(index.register, [record] * 4))
    assert results == [record] * 4
    assert index.records() == [record]
