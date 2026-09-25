from __future__ import annotations

import json

import pytest

from packlab_core.pairing import PairingOffer, PairingStore
from packlab_core.transfer_protocol import TransferProtocolError


def test_pairing_offer_has_manual_and_qr_forms_and_minimum_identity() -> None:
    now = [100.0]
    store = PairingStore(clock=lambda: now[0])
    offer = store.create_offer(receiver_instance_id="receiver", host="127.0.0.1", port=8443, tls_certificate_fingerprint="pin", ttl_seconds=60)
    parsed = PairingOffer.from_qr_payload(offer.qr_payload())
    assert parsed.public_dict() == offer.public_dict()
    identity = store.pair(parsed, receiver_instance_id="receiver", pairing_code=offer.pairing_code, tls_certificate_fingerprint="pin")
    assert identity.tls_certificate_fingerprint == "pin"
    assert store.paired_identity("receiver") == identity
    assert offer.pairing_code not in identity.__repr__()


def test_expired_wrong_pin_wrong_receiver_and_replay_are_rejected() -> None:
    now = [100.0]
    store = PairingStore(clock=lambda: now[0])
    offer = store.create_offer(receiver_instance_id="receiver", host="localhost", port=1, tls_certificate_fingerprint="pin")
    with pytest.raises(TransferProtocolError, match="wrong_pin"):
        store.pair(offer, receiver_instance_id="receiver", pairing_code=offer.pairing_code, tls_certificate_fingerprint="other")
    with pytest.raises(TransferProtocolError, match="wrong_receiver"):
        store.pair(offer, receiver_instance_id="other", pairing_code=offer.pairing_code, tls_certificate_fingerprint="pin")
    now[0] = 221.0
    with pytest.raises(TransferProtocolError, match="expired_pairing"):
        store.pair(offer, receiver_instance_id="receiver", pairing_code=offer.pairing_code, tls_certificate_fingerprint="pin")
    fresh = store.create_offer(receiver_instance_id="receiver", host="localhost", port=1, tls_certificate_fingerprint="pin")
    store.pair(fresh, receiver_instance_id="receiver", pairing_code=fresh.pairing_code, tls_certificate_fingerprint="pin")
    with pytest.raises(TransferProtocolError, match="replayed_pairing"):
        store.pair(fresh, receiver_instance_id="receiver", pairing_code=fresh.pairing_code, tls_certificate_fingerprint="pin")


def test_malformed_qr_and_wrong_version_fail_closed() -> None:
    with pytest.raises(TransferProtocolError, match="bad_request"):
        PairingOffer.from_qr_payload("not-json")
    payload = {"protocol": "packlab-transfer", "protocol_version": "2"}
    with pytest.raises(TransferProtocolError, match="unsupported_version"):
        PairingOffer.from_qr_payload(json.dumps(payload))
