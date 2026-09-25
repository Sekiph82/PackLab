from __future__ import annotations

import hashlib
import json
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import replace
from pathlib import Path

import pytest
from tests.transfer.tls_test_material import create_test_tls_identity

from packlab_core.packscan import write_packscan
from packlab_core.transfer_security import TLSIdentity
from packlab_studio.receiver import PackLabReceiver


def _package(path: Path, repo_root: Path) -> Path:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = "loopback-capture"
    manifest["payloads"][0]["size_bytes"] = 3
    manifest["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})


def _context(identity: TLSIdentity) -> ssl.SSLContext:
    context = ssl.create_default_context(cafile=str(identity.certificate_path))
    context.check_hostname = False
    return context


def _request(base: str, path: str, *, identity: TLSIdentity, method: str = "GET", body: dict[str, object] | None = None, token: str | None = None) -> tuple[int, dict[str, object]]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{base}{path}", data=data, method=method, headers={"Content-Type": "application/json"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, context=_context(identity)) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def _pair(receiver: PackLabReceiver, identity: TLSIdentity) -> tuple[str, str]:
    offer = receiver.pairing_offer(host="127.0.0.1")
    status, value = _request(
        f"https://127.0.0.1:{receiver.port}", "/v1/pair", identity=identity, method="POST",
        body={"offer": offer.public_dict(), "pairing_code": offer.pairing_code, "tls_certificate_fingerprint": offer.tls_certificate_fingerprint},
    )
    assert status == 200
    return str(value["session_token"]), offer.tls_certificate_fingerprint


def _identity_or_skip(tmp_path: Path) -> TLSIdentity:
    return create_test_tls_identity(tmp_path / "tls")


def test_tls_pair_partial_stop_restart_status_resume_and_verified_ingest(tmp_path: Path, repo_root: Path) -> None:
    identity = _identity_or_skip(tmp_path)
    receiver = PackLabReceiver(tmp_path, receiver_id="loopback-receiver", tls_identity=identity)
    receiver.start()
    try:
        token, _ = _pair(receiver, identity)
        package = _package(tmp_path / "capture.packscan", repo_root)
        data = package.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        create = {"message": "create_transfer", "protocol": "packlab-transfer", "protocol_version": "1", "transport": "https", "receiver_id": receiver.receiver_id, "transfer_id": "loopback-transfer", "capture_id": "loopback-capture", "package_name": package.name, "total_bytes": len(data), "package_sha256": digest}
        assert _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers", identity=identity, method="POST", body=create, token=token)[0] == 201
        split = len(data) // 2
        headers_request = urllib.request.Request(f"https://127.0.0.1:{receiver.port}/v1/transfers/loopback-transfer/chunks", data=data[:split], method="POST", headers={"Authorization": f"Bearer {token}", "X-PackLab-Offset": "0", "X-PackLab-Chunk-SHA256": hashlib.sha256(data[:split]).hexdigest()})
        with urllib.request.urlopen(headers_request, context=_context(identity)) as response:
            assert response.status == 200
        receiver.stop()
        restarted = PackLabReceiver(tmp_path, receiver_id="loopback-receiver", tls_identity=identity)
        restarted.start()
        try:
            token, _ = _pair(restarted, identity)
            status, value = _request(f"https://127.0.0.1:{restarted.port}", "/v1/transfers/loopback-transfer", identity=identity, token=token)
            assert status == 200 and value["next_offset"] == split
            request = urllib.request.Request(f"https://127.0.0.1:{restarted.port}/v1/transfers/loopback-transfer/chunks", data=data[split:], method="POST", headers={"Authorization": f"Bearer {token}", "X-PackLab-Offset": str(split), "X-PackLab-Chunk-SHA256": hashlib.sha256(data[split:]).hexdigest()})
            with urllib.request.urlopen(request, context=_context(identity)) as response:
                assert response.status == 200
            status, ack = _request(f"https://127.0.0.1:{restarted.port}", "/v1/transfers/loopback-transfer/complete", identity=identity, method="POST", token=token)
            assert status == 200 and ack["verified"] is True
            assert (tmp_path / "capture_inbox" / "loopback-transfer.packscan").is_file()
            assert list((tmp_path / "raw").glob("*.packscan"))
        finally:
            restarted.stop()
    finally:
        receiver.stop()


def test_tls_missing_auth_and_concurrent_transfer_ids_are_isolated(tmp_path: Path) -> None:
    identity = _identity_or_skip(tmp_path)
    receiver = PackLabReceiver(tmp_path, receiver_id="receiver", tls_identity=identity)
    receiver.start()
    try:
        status, value = _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers/missing", identity=identity)
        assert status == 400 and value["error_code"] == "unpaired"
        token, _ = _pair(receiver, identity)
        for transfer_id, capture_id, digest in (("one", "one", "a" * 64), ("two", "two", "b" * 64)):
            body = {"message": "create_transfer", "protocol": "packlab-transfer", "protocol_version": "1", "transport": "https", "receiver_id": "receiver", "transfer_id": transfer_id, "capture_id": capture_id, "package_name": f"{transfer_id}.packscan", "total_bytes": 1, "package_sha256": digest}
            assert _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers", identity=identity, method="POST", body=body, token=token)[0] == 201
        first = _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers/one", identity=identity, token=token)
        second = _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers/two", identity=identity, token=token)
        assert first[1]["transfer_id"] == "one" and second[1]["transfer_id"] == "two"
    finally:
        receiver.stop()


def test_tls_pin_mismatch_expiry_replay_wrong_receiver_and_secret_redaction(tmp_path: Path) -> None:
    identity = create_test_tls_identity(tmp_path / "tls-good")
    wrong_identity = create_test_tls_identity(tmp_path / "tls-wrong")
    receiver = PackLabReceiver(tmp_path / "receiver", receiver_id="receiver", tls_identity=identity)
    receiver.start()
    try:
        with pytest.raises(urllib.error.URLError):
            _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers/missing", identity=wrong_identity)
        expired = receiver.pairing_offer(host="127.0.0.1")
        receiver.pairings._offers[expired.pairing_id] = replace(expired, expires_at=time.time() - 1)
        status, value = _request(f"https://127.0.0.1:{receiver.port}", "/v1/pair", identity=identity, method="POST", body={"offer": expired.public_dict(), "pairing_code": expired.pairing_code, "tls_certificate_fingerprint": expired.tls_certificate_fingerprint})
        assert status == 400 and value["error_code"] == "expired_pairing"
        replay = receiver.pairing_offer(host="127.0.0.1")
        pair_body = {"offer": replay.public_dict(), "pairing_code": replay.pairing_code, "tls_certificate_fingerprint": replay.tls_certificate_fingerprint}
        assert _request(f"https://127.0.0.1:{receiver.port}", "/v1/pair", identity=identity, method="POST", body=pair_body)[0] == 200
        status, replay_error = _request(f"https://127.0.0.1:{receiver.port}", "/v1/pair", identity=identity, method="POST", body=pair_body)
        assert status == 400 and replay_error["error_code"] == "replayed_pairing"
        wrong = receiver.pairing_offer(host="127.0.0.1")
        wrong_body = {"offer": {**wrong.public_dict(), "receiver_instance_id": "other-receiver"}, "pairing_code": wrong.pairing_code, "tls_certificate_fingerprint": wrong.tls_certificate_fingerprint}
        status, wrong_error = _request(f"https://127.0.0.1:{receiver.port}", "/v1/pair", identity=identity, method="POST", body=wrong_body)
        assert status == 400 and wrong_error["error_code"] == "wrong_receiver"
        assert "pairing_code" not in json.dumps(wrong_error) and "session_token" not in json.dumps(wrong_error)
    finally:
        receiver.stop()
