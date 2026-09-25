from __future__ import annotations

import hashlib
import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from packlab_core.packscan import write_packscan
from packlab_core.transfer_protocol import TransferProtocolError
from packlab_core.transfer_security import ensure_local_tls_identity
from packlab_studio.receiver import PackLabReceiver


def _package(path: Path, repo_root: Path) -> Path:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = "loopback-capture"
    manifest["payloads"][0]["size_bytes"] = 3
    manifest["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})


def _request(base: str, path: str, *, method: str = "GET", body: dict[str, object] | None = None, token: str | None = None) -> tuple[int, dict[str, object]]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{base}{path}", data=data, method=method, headers={"Content-Type": "application/json"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, context=ssl._create_unverified_context()) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def _pair(receiver: PackLabReceiver) -> tuple[str, str]:
    offer = receiver.pairing_offer(host="127.0.0.1")
    status, value = _request(
        f"https://127.0.0.1:{receiver.port}", "/v1/pair", method="POST",
        body={"offer": offer.public_dict(), "pairing_code": offer.pairing_code, "tls_certificate_fingerprint": offer.tls_certificate_fingerprint},
    )
    assert status == 200
    return str(value["session_token"]), offer.tls_certificate_fingerprint


def _identity_or_skip(tmp_path: Path):
    try:
        return ensure_local_tls_identity(tmp_path / "tls" / "receiver.crt", tmp_path / "tls" / "receiver.key")
    except TransferProtocolError as error:
        pytest.skip(f"ephemeral TLS loopback unavailable: {error.code}")


def test_tls_pair_partial_stop_restart_status_resume_and_verified_ingest(tmp_path: Path, repo_root: Path) -> None:
    identity = _identity_or_skip(tmp_path)
    receiver = PackLabReceiver(tmp_path, receiver_id="loopback-receiver", tls_identity=identity)
    receiver.start()
    try:
        token, _ = _pair(receiver)
        package = _package(tmp_path / "capture.packscan", repo_root)
        data = package.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        create = {"message": "create_transfer", "protocol": "packlab-transfer", "protocol_version": "1", "transport": "https", "receiver_id": receiver.receiver_id, "transfer_id": "loopback-transfer", "capture_id": "loopback-capture", "package_name": package.name, "total_bytes": len(data), "package_sha256": digest}
        assert _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers", method="POST", body=create, token=token)[0] == 201
        split = len(data) // 2
        headers_request = urllib.request.Request(f"https://127.0.0.1:{receiver.port}/v1/transfers/loopback-transfer/chunks", data=data[:split], method="POST", headers={"Authorization": f"Bearer {token}", "X-PackLab-Offset": "0", "X-PackLab-Chunk-SHA256": hashlib.sha256(data[:split]).hexdigest()})
        with urllib.request.urlopen(headers_request, context=ssl._create_unverified_context()) as response:
            assert response.status == 200
        receiver.stop()
        restarted = PackLabReceiver(tmp_path, receiver_id="loopback-receiver", tls_identity=identity)
        restarted.start()
        try:
            token, _ = _pair(restarted)
            status, value = _request(f"https://127.0.0.1:{restarted.port}", "/v1/transfers/loopback-transfer", token=token)
            assert status == 200 and value["next_offset"] == split
            request = urllib.request.Request(f"https://127.0.0.1:{restarted.port}/v1/transfers/loopback-transfer/chunks", data=data[split:], method="POST", headers={"Authorization": f"Bearer {token}", "X-PackLab-Offset": str(split), "X-PackLab-Chunk-SHA256": hashlib.sha256(data[split:]).hexdigest()})
            with urllib.request.urlopen(request, context=ssl._create_unverified_context()) as response:
                assert response.status == 200
            status, ack = _request(f"https://127.0.0.1:{restarted.port}", "/v1/transfers/loopback-transfer/complete", method="POST", token=token)
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
        status, value = _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers/missing")
        assert status == 400 and value["error_code"] == "unpaired"
        token, _ = _pair(receiver)
        for transfer_id, capture_id, digest in (("one", "one", "a" * 64), ("two", "two", "b" * 64)):
            body = {"message": "create_transfer", "protocol": "packlab-transfer", "protocol_version": "1", "transport": "https", "receiver_id": "receiver", "transfer_id": transfer_id, "capture_id": capture_id, "package_name": f"{transfer_id}.packscan", "total_bytes": 1, "package_sha256": digest}
            assert _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers", method="POST", body=body, token=token)[0] == 201
        first = _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers/one", token=token)
        second = _request(f"https://127.0.0.1:{receiver.port}", "/v1/transfers/two", token=token)
        assert first[1]["transfer_id"] == "one" and second[1]["transfer_id"] == "two"
    finally:
        receiver.stop()
