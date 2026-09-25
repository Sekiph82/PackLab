"""Executable V1 wire harness for the sender/receiver/ingest production boundary."""

from __future__ import annotations

import hashlib
import json
import ssl
import urllib.request
from pathlib import Path

from tests.transfer.tls_test_material import create_test_tls_identity

from packlab_core.packscan import write_packscan
from packlab_core.transfer_protocol import TransferCreate
from packlab_studio.receiver import PackLabReceiver


def _package(path: Path, repo_root: Path) -> Path:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = "wire-harness-capture"
    manifest["payloads"][0]["size_bytes"] = 3
    manifest["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})


class WireSender:
    def __init__(self, receiver: PackLabReceiver, identity) -> None:
        self.receiver = receiver
        self.identity = identity
        self.context = ssl.create_default_context(cafile=str(identity.certificate_path))
        self.context.check_hostname = False
        self.base = f"https://127.0.0.1:{receiver.port}"
        self.token = ""

    def request(self, path: str, *, method: str = "GET", body: object | None = None, headers: dict[str, str] | None = None) -> dict[str, object]:
        data = body if isinstance(body, bytes) else json.dumps(body, sort_keys=True, separators=(",", ":")).encode() if body is not None else None
        request = urllib.request.Request(f"{self.base}{path}", method=method, data=data, headers={"Content-Type": "application/json", **(headers or {})})
        with urllib.request.urlopen(request, context=self.context) as response:
            return json.loads(response.read())

    def pair(self) -> None:
        offer = self.receiver.pairing_offer(host="127.0.0.1")
        result = self.request("/v1/pair", method="POST", body={"offer": offer.public_dict(), "pairing_code": offer.pairing_code, "tls_certificate_fingerprint": offer.tls_certificate_fingerprint})
        self.token = str(result["session_token"])

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def create(self, message: dict[str, object]) -> None:
        self.request("/v1/transfers", method="POST", body=message, headers=self.auth_headers())

    def status(self, transfer_id: str) -> dict[str, object]:
        return self.request(f"/v1/transfers/{transfer_id}", headers=self.auth_headers())

    def chunk(self, transfer_id: str, offset: int, payload: bytes) -> None:
        self.request(f"/v1/transfers/{transfer_id}/chunks", method="POST", body=payload, headers={**self.auth_headers(), "Content-Type": "application/octet-stream", "X-PackLab-Offset": str(offset), "X-PackLab-Chunk-SHA256": hashlib.sha256(payload).hexdigest()})

    def control(self, transfer_id: str, action: str) -> dict[str, object]:
        return self.request(f"/v1/transfers/{transfer_id}/{action}", method="POST", headers=self.auth_headers())

    def complete(self, transfer_id: str) -> dict[str, object]:
        return self.request(f"/v1/transfers/{transfer_id}/complete", method="POST", headers=self.auth_headers())


def test_executable_shared_wire_sender_resume_receiver_restart_and_exactly_once_ingest(tmp_path: Path, repo_root: Path) -> None:
    identity = create_test_tls_identity(tmp_path / "tls")
    package = _package(tmp_path / "capture.packscan", repo_root)
    payload = package.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    receiver = PackLabReceiver(tmp_path / "receiver", receiver_id="wire-receiver", tls_identity=identity)
    receiver.start()
    try:
        sender = WireSender(receiver, identity)
        sender.pair()
        fixture = json.loads((repo_root / "tests/fixtures/transfer-protocol-v1-golden.json").read_text(encoding="utf-8"))
        create = {**fixture["create"], "receiver_id": receiver.receiver_id, "transfer_id": "wire-transfer", "capture_id": "wire-harness-capture", "package_name": package.name, "total_bytes": len(payload), "package_sha256": digest}
        TransferCreate.from_dict(create)
        sender.create(create)
        split = len(payload) // 2
        sender.chunk("wire-transfer", 0, payload[:split])
        (tmp_path / "sender-state.json").write_text(json.dumps({"transfer_id": "wire-transfer", "package_sha256": digest, "receiver_id": receiver.receiver_id}), encoding="utf-8")
        receiver.stop()
        restarted = PackLabReceiver(tmp_path / "receiver", receiver_id="wire-receiver", tls_identity=identity)
        restarted.start()
        try:
            resumed = WireSender(restarted, identity)
            resumed.pair()
            assert resumed.status("wire-transfer")["next_offset"] == split
            resumed.control("wire-transfer", "cancel")
            resumed.control("wire-transfer", "resume")
            resumed.chunk("wire-transfer", split, payload[split:])
            acknowledgement = resumed.complete("wire-transfer")
            assert acknowledgement["transfer_id"] == "wire-transfer" and acknowledgement["verified"] is True and acknowledgement["state"] == "complete"
            second = resumed.complete("wire-transfer")
            assert second == acknowledgement
            assert len(list((tmp_path / "receiver" / "raw").glob("*.packscan"))) == 1
            assert len(list((tmp_path / "receiver" / "reports").glob("*.json"))) == 1
            assert (tmp_path / "receiver" / "ingest-index.json").is_file()
        finally:
            restarted.stop()
    finally:
        receiver.stop()
