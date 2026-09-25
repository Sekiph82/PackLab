from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from packlab_core.transfer_protocol import TransferCreate
from packlab_studio.transfer_store import ResumableTransferStore, TransferStoreError


def _request(data: bytes = b"abcdefgh") -> TransferCreate:
    return TransferCreate("receiver", "transfer", "capture", "capture.packscan", len(data), hashlib.sha256(data).hexdigest())


def test_store_resumes_after_restart_and_duplicate_chunk_is_idempotent(tmp_path: Path) -> None:
    data = b"abcdefgh"
    first = ResumableTransferStore(tmp_path)
    first.create(_request(data))
    first.put_chunk("transfer", offset=0, payload=data[:3], chunk_sha256=hashlib.sha256(data[:3]).hexdigest())
    assert first.status("transfer").next_offset == 3
    restarted = ResumableTransferStore(tmp_path)
    duplicate = restarted.put_chunk("transfer", offset=0, payload=data[:3], chunk_sha256=hashlib.sha256(data[:3]).hexdigest())
    assert duplicate.next_offset == 3
    restarted.put_chunk("transfer", offset=3, payload=data[3:], chunk_sha256=hashlib.sha256(data[3:]).hexdigest())
    assert restarted.status("transfer").state == "receiving"


def test_store_rejects_gaps_conflicts_bad_chunks_and_identity_reuse(tmp_path: Path) -> None:
    data = b"abcdefgh"
    store = ResumableTransferStore(tmp_path)
    store.create(_request(data))
    with pytest.raises(TransferStoreError, match="out_of_order"):
        store.put_chunk("transfer", offset=2, payload=data[2:4], chunk_sha256=hashlib.sha256(data[2:4]).hexdigest())
    with pytest.raises(TransferStoreError, match="bad_request"):
        store.put_chunk("transfer", offset=0, payload=b"x", chunk_sha256=hashlib.sha256(b"y").hexdigest())
    store.put_chunk("transfer", offset=0, payload=data[:2], chunk_sha256=hashlib.sha256(data[:2]).hexdigest())
    with pytest.raises(TransferStoreError, match="conflicting_chunk"):
        store.put_chunk("transfer", offset=0, payload=b"xx", chunk_sha256=hashlib.sha256(b"xx").hexdigest())
    with pytest.raises(TransferStoreError, match="conflicts"):
        store.create(TransferCreate("receiver", "transfer", "different", "capture.packscan", len(data), hashlib.sha256(data).hexdigest()))


def test_cancel_resume_and_multi_chunk_completion(tmp_path: Path) -> None:
    data = b"0123456789"
    store = ResumableTransferStore(tmp_path)
    store.create(_request(data))
    store.put_chunk("transfer", offset=0, payload=data[:4], chunk_sha256=hashlib.sha256(data[:4]).hexdigest())
    store.cancel("transfer")
    with pytest.raises(TransferStoreError, match="cancelled"):
        store.put_chunk("transfer", offset=4, payload=data[4:6], chunk_sha256=hashlib.sha256(data[4:6]).hexdigest())
    store.resume("transfer")
    offset = 4
    while offset < len(data):
        chunk = data[offset : offset + 2]
        store.put_chunk("transfer", offset=offset, payload=chunk, chunk_sha256=hashlib.sha256(chunk).hexdigest())
        offset += len(chunk)
    result = store.verify("transfer")
    assert result.verified
    assert store.completion_ack("transfer", authenticated=True).verified
