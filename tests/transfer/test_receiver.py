from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from packlab_core.transfer_protocol import TransferCreate, TransferProtocolError
from packlab_studio.receiver import PackLabReceiver, ReceiverError


def test_receiver_requires_tls_for_start_and_routes_verified_transfer_to_inbox(tmp_path: Path) -> None:
    receiver = PackLabReceiver(tmp_path, receiver_id="receiver", certificate_fingerprint="pin")
    offer = receiver.pairing_offer(host="127.0.0.1")
    credential = receiver.pair(offer, code=offer.pairing_code, certificate_fingerprint="pin")
    payload = b"opaque-packscan-bytes"
    request = TransferCreate("receiver", "transfer", "capture", "capture.packscan", len(payload), hashlib.sha256(payload).hexdigest())
    receiver.create_transfer(request.to_dict(), token_authenticated=True)
    receiver.put_chunk("transfer", offset=0, payload=payload, chunk_sha256=hashlib.sha256(payload).hexdigest(), token_authenticated=True)
    ack, result = receiver.complete("transfer", token_authenticated=True)
    assert ack.authenticated and ack.verified
    assert result is not None and result.source_channel == "network"
    assert (tmp_path / "capture_inbox" / "transfer.packscan").exists()
    assert credential.receiver_instance_id == "receiver"
    with pytest.raises(ReceiverError, match="HTTPS"):
        PackLabReceiver(tmp_path / "other").start()


def test_receiver_rejects_unpaired_direct_operations_and_keeps_distinct_transfers(tmp_path: Path) -> None:
    receiver = PackLabReceiver(tmp_path, receiver_id="receiver", certificate_fingerprint="pin")
    request = TransferCreate("receiver", "transfer", "capture", "capture.packscan", 1, "a" * 64)
    with pytest.raises(TransferProtocolError, match="unpaired"):
        receiver.create_transfer(request.to_dict())
    receiver.create_transfer(request.to_dict(), token_authenticated=True)
    second = TransferCreate("receiver", "second", "capture-2", "second.packscan", 1, "b" * 64)
    receiver.create_transfer(second.to_dict(), token_authenticated=True)
    assert receiver.status("transfer", token_authenticated=True).transfer_id == "transfer"
    assert receiver.status("second", token_authenticated=True).transfer_id == "second"
