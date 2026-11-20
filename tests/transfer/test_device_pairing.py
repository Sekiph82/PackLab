"""PL-0452: pair once, then long-lived revocable device sessions (no new pairing code)."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import pytest
from tests.transfer.test_loopback_receiver import _pair, _request
from tests.transfer.tls_test_material import create_test_tls_identity

from packlab_core.pairing import DeviceRegistry, PairingStore
from packlab_core.transfer_protocol import TransferProtocolError
from packlab_core.transfer_security import PairingAuthenticator
from packlab_studio.receiver import PackLabReceiver


def _paired(now: list[float], registry: DeviceRegistry):
    pairing = PairingStore(clock=lambda: now[0])
    authenticator = PairingAuthenticator(
        pairing, clock=lambda: now[0], session_ttl_seconds=30, devices=registry
    )
    offer = pairing.create_offer(
        receiver_instance_id="r", host="localhost", port=8443, tls_certificate_fingerprint="pin"
    )
    credential = authenticator.authenticate_pairing(
        offer,
        receiver_instance_id="r",
        pairing_code=offer.pairing_code,
        certificate_fingerprint_value="pin",
        device_name="iPhone17,3",
    )
    return authenticator, credential


def _session(
    authenticator: PairingAuthenticator,
    device_id: str,
    secret: str,
    now: float,
    *,
    nonce: str | None = None,
    receiver: str = "r",
):
    return authenticator.authenticate_device(
        receiver_instance_id=receiver,
        expected_receiver_instance_id="r",
        device_id=device_id,
        device_secret=secret,
        nonce=nonce or uuid.uuid4().hex,
        timestamp=now,
        certificate_fingerprint_value="pin",
    )


def test_pairing_once_issues_a_device_credential_that_opens_fresh_sessions_after_restart(
    tmp_path: Path,
) -> None:
    now = [1000.0]
    path = tmp_path / "paired-devices.json"
    authenticator, credential = _paired(now, DeviceRegistry(path, clock=lambda: now[0]))
    assert credential.device_id and credential.device_secret
    assert credential.device_secret not in repr(credential)
    stored = path.read_text(encoding="utf-8")
    # Only the secret's hash is at rest; never the secret or a session token.
    assert credential.device_secret not in stored and credential.token not in stored
    assert json.loads(stored)["devices"][0]["device_name"] == "iPhone17,3"

    # Studio restart: a new authenticator over the persisted registry, no pairing offer.
    now[0] = 5000.0
    restarted = PairingAuthenticator(
        PairingStore(clock=lambda: now[0]),
        clock=lambda: now[0],
        session_ttl_seconds=30,
        devices=DeviceRegistry(path, clock=lambda: now[0]),
    )
    first = _session(restarted, credential.device_id, credential.device_secret, now[0])
    second = _session(restarted, credential.device_id, credential.device_secret, now[0])
    assert first.token != second.token and first.device_id == credential.device_id
    restarted.require_session(
        receiver_instance_id="r", token=first.token, certificate_fingerprint_value="pin"
    )
    now[0] += 31
    with pytest.raises(TransferProtocolError, match="expired_pairing"):
        restarted.require_session(
            receiver_instance_id="r", token=first.token, certificate_fingerprint_value="pin"
        )


def test_wrong_secret_unknown_device_replay_stale_and_wrong_receiver_fail_closed() -> None:
    now = [1000.0]
    authenticator, credential = _paired(now, DeviceRegistry(clock=lambda: now[0]))
    device_id, secret = credential.device_id or "", credential.device_secret or ""
    with pytest.raises(TransferProtocolError, match="unpaired"):
        _session(authenticator, device_id, secret + "x", now[0])
    with pytest.raises(TransferProtocolError, match="unpaired"):
        _session(authenticator, "unknown-device", secret, now[0])
    nonce = uuid.uuid4().hex
    _session(authenticator, device_id, secret, now[0], nonce=nonce)
    with pytest.raises(TransferProtocolError, match="replayed_request"):
        _session(authenticator, device_id, secret, now[0], nonce=nonce)
    with pytest.raises(TransferProtocolError, match="replayed_request"):
        _session(authenticator, device_id, secret, now[0] - 301)
    with pytest.raises(TransferProtocolError, match="replayed_request"):
        _session(authenticator, device_id, secret, now[0], nonce="short")
    with pytest.raises(TransferProtocolError, match="wrong_receiver"):
        _session(authenticator, device_id, secret, now[0], receiver="other")


def test_revoked_device_is_rejected_and_loses_its_live_sessions(tmp_path: Path) -> None:
    now = [1000.0]
    path = tmp_path / "paired-devices.json"
    authenticator, credential = _paired(now, DeviceRegistry(path, clock=lambda: now[0]))
    device_id, secret = credential.device_id or "", credential.device_secret or ""
    live = _session(authenticator, device_id, secret, now[0])
    assert authenticator.revoke_device(device_id)
    for token in (live.token, credential.token):
        with pytest.raises(TransferProtocolError, match="unpaired|device_revoked"):
            authenticator.require_session(
                receiver_instance_id="r", token=token, certificate_fingerprint_value="pin"
            )
    with pytest.raises(TransferProtocolError, match="device_revoked"):
        _session(authenticator, device_id, secret, now[0])
    # Revocation survives a restart.
    reloaded = DeviceRegistry(path, clock=lambda: now[0])
    assert not reloaded.is_active(device_id)
    with pytest.raises(TransferProtocolError, match="device_revoked"):
        reloaded.authenticate(device_id, secret, nonce=uuid.uuid4().hex, timestamp=now[0])


def test_unreadable_registry_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "paired-devices.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(TransferProtocolError, match="internal_error"):
        DeviceRegistry(path)


def test_https_pair_then_device_session_uploads_without_a_new_code(tmp_path: Path) -> None:
    identity = create_test_tls_identity(tmp_path / "tls")
    receiver = PackLabReceiver(tmp_path / "receiver", receiver_id="receiver", tls_identity=identity)
    receiver.start()
    base = f"https://127.0.0.1:{receiver.port}"
    try:
        offer = receiver.pairing_offer(host="127.0.0.1")
        status, paired = _request(
            base,
            "/v1/pair",
            identity=identity,
            method="POST",
            body={
                "offer": offer.public_dict(),
                "pairing_code": offer.pairing_code,
                "tls_certificate_fingerprint": offer.tls_certificate_fingerprint,
                "device_name": "iPhone17,3",
            },
        )
        assert (
            status == 200
            and isinstance(paired["device_id"], str)
            and isinstance(paired["device_secret"], str)
        )
        receiver.stop()
        restarted = PackLabReceiver(
            tmp_path / "receiver", receiver_id="receiver", tls_identity=identity
        )
        restarted.start()
        base = f"https://127.0.0.1:{restarted.port}"
        try:
            request = {
                "message": "device_session",
                "protocol": "packlab-transfer",
                "protocol_version": "1",
                "receiver_instance_id": "receiver",
                "device_id": paired["device_id"],
                "device_secret": paired["device_secret"],
                "nonce": uuid.uuid4().hex,
                "timestamp": time.time(),
            }
            status, session = _request(
                base, "/v1/session", identity=identity, method="POST", body=request
            )
            assert (
                status == 200
                and session["message"] == "session_acknowledgement"
                and "device_secret" not in session
            )
            create = {
                "message": "create_transfer",
                "protocol": "packlab-transfer",
                "protocol_version": "1",
                "transport": "https",
                "receiver_id": "receiver",
                "transfer_id": "after-restart",
                "capture_id": "c",
                "package_name": "c.packscan",
                "total_bytes": 1,
                "package_sha256": "a" * 64,
            }
            assert (
                _request(
                    base,
                    "/v1/transfers",
                    identity=identity,
                    method="POST",
                    body=create,
                    token=str(session["session_token"]),
                )[0]
                == 201
            )
            status, replay = _request(
                base, "/v1/session", identity=identity, method="POST", body=request
            )
            assert status == 400 and replay["error_code"] == "replayed_request"
            assert restarted.revoke_device(str(paired["device_id"]))
            status, revoked = _request(
                base,
                "/v1/transfers/after-restart",
                identity=identity,
                token=str(session["session_token"]),
            )
            assert status == 400 and revoked["error_code"] == "unpaired"
            status, revoked = _request(
                base,
                "/v1/session",
                identity=identity,
                method="POST",
                body={**request, "nonce": uuid.uuid4().hex},
            )
            assert status == 400 and revoked["error_code"] == "device_revoked"
            assert str(paired["device_secret"]) not in json.dumps(revoked)
            # A one-time pairing code still works after a revoke (pair again).
            token, _ = _pair(restarted, identity)
            assert token
        finally:
            restarted.stop()
    finally:
        receiver.stop()
