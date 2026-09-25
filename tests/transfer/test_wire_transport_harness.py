"""Executable V1 wire harness for the sender/receiver/ingest production boundary."""

from __future__ import annotations

import hashlib
import json
import ssl
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from tests.transfer.tls_test_material import create_test_tls_identity

from packlab_core.packscan import write_packscan
from packlab_core.transfer_protocol import TransferCreate
from packlab_core.transfer_security import certificate_fingerprint
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
        self.paired_offer_fingerprint = ""

    def request(self, path: str, *, method: str = "GET", body: object | None = None, headers: dict[str, str] | None = None) -> dict[str, object]:
        data = body if isinstance(body, bytes) else json.dumps(body, sort_keys=True, separators=(",", ":")).encode() if body is not None else None
        request = urllib.request.Request(f"{self.base}{path}", method=method, data=data, headers={"Content-Type": "application/json", **(headers or {})})
        with urllib.request.urlopen(request, context=self.context) as response:
            return json.loads(response.read())

    def pair(self) -> None:
        offer = self.receiver.pairing_offer(host="127.0.0.1")
        live_fingerprint = certificate_fingerprint(self.identity.certificate_path)
        if offer.tls_certificate_fingerprint != live_fingerprint:
            raise AssertionError("pairing offer certificate fingerprint does not match the live certificate")
        self.paired_offer_fingerprint = live_fingerprint
        result = self.request("/v1/pair", method="POST", body={"offer": offer.public_dict(), "pairing_code": offer.pairing_code, "tls_certificate_fingerprint": offer.tls_certificate_fingerprint})
        self.token = str(result["session_token"])

    def restore_sender_state(self, path: Path, *, package_digest: str, receiver_id: str) -> PersistedSenderState:
        state = PersistedSenderState.from_dict(json.loads(path.read_text(encoding="utf-8")))
        if state.package_sha256 != package_digest or state.receiver_id != receiver_id:
            raise ValueError("persisted sender identity conflicts with the current package or receiver")
        self.sender_state = state
        return state

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


@dataclass(frozen=True, slots=True)
class PersistedSenderState:
    transfer_id: str
    package_sha256: str
    receiver_id: str

    def to_dict(self) -> dict[str, str]:
        return {"transfer_id": self.transfer_id, "package_sha256": self.package_sha256, "receiver_id": self.receiver_id}

    @classmethod
    def from_dict(cls, value: object) -> PersistedSenderState:
        if not isinstance(value, dict) or not all(isinstance(value.get(key), str) and value[key] for key in ("transfer_id", "package_sha256", "receiver_id")):
            raise ValueError("persisted sender state is incomplete")
        return cls(transfer_id=value["transfer_id"], package_sha256=value["package_sha256"], receiver_id=value["receiver_id"])


def _assert_completion_gate(acknowledgement: dict[str, object], state: PersistedSenderState) -> None:
    if not (
        acknowledgement.get("transfer_id") == state.transfer_id
        and acknowledgement.get("package_sha256") == state.package_sha256
        and acknowledgement.get("authenticated") is True
        and acknowledgement.get("verified") is True
        and acknowledgement.get("state") in {"verified", "complete"}
    ):
        raise AssertionError("completion acknowledgement failed the sender acceptance gate")


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
        sender_state_path = tmp_path / "sender-state.json"
        sender_state = PersistedSenderState("wire-transfer", digest, receiver.receiver_id)
        sender_state_path.write_text(json.dumps(sender_state.to_dict(), sort_keys=True), encoding="utf-8")
        del sender
        receiver.stop()
        restarted = PackLabReceiver(tmp_path / "receiver", receiver_id="wire-receiver", tls_identity=identity)
        restarted.start()
        try:
            resumed = WireSender(restarted, identity)
            resumed.pair()
            conflicting_state_path = tmp_path / "conflicting-sender-state.json"
            conflicting_state_path.write_text(json.dumps({"transfer_id": "wrong", "package_sha256": "0" * 64, "receiver_id": receiver.receiver_id}), encoding="utf-8")
            try:
                resumed.restore_sender_state(conflicting_state_path, package_digest=digest, receiver_id=receiver.receiver_id)
                raise AssertionError("conflicting persisted sender state must fail closed")
            except ValueError:
                pass
            restored = resumed.restore_sender_state(sender_state_path, package_digest=digest, receiver_id=receiver.receiver_id)
            assert resumed.status(restored.transfer_id)["next_offset"] == split
            resumed.control(restored.transfer_id, "cancel")
            resumed.control(restored.transfer_id, "resume")
            resumed.chunk(restored.transfer_id, split, payload[split:])
            acknowledgement = resumed.complete(restored.transfer_id)
            _assert_completion_gate(acknowledgement, restored)
            second = resumed.complete(restored.transfer_id)
            assert second == acknowledgement
            assert len(list((tmp_path / "receiver" / "raw").glob("*.packscan"))) == 1
            assert len(list((tmp_path / "receiver" / "reports").glob("*.json"))) == 1
            assert (tmp_path / "receiver" / "ingest-index.json").is_file()
        finally:
            restarted.stop()
    finally:
        receiver.stop()
