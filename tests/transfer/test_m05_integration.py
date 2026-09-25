from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from packlab_core.packscan import write_packscan
from packlab_core.transfer_protocol import TransferCreate
from packlab_studio.receiver import PackLabReceiver


def _valid_package(path: Path, repo_root: Path, *, capture_id: str = "integration-capture") -> Path:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = capture_id
    manifest["payloads"][0]["size_bytes"] = 3
    manifest["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})


def _invalid_zip(path: Path, *, manifest: bytes = b"{}", extra: dict[str, bytes] | None = None) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("manifest.json", manifest)
        archive.writestr("metadata/photos.json", b"{}")
        if extra:
            for name, data in extra.items():
                archive.writestr(name, data)
    return path


def _corrupt(path: Path, repo_root: Path) -> Path:
    path.write_bytes(b"not-a-zip")
    return path


def _missing_photo(path: Path, repo_root: Path) -> Path:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = "missing-photo"
    return _invalid_zip(path, manifest=json.dumps(manifest).encode())


def _transfer(receiver: PackLabReceiver, package: Path, transfer_id: str, *, capture_id: str = "integration-capture", declared_digest: str | None = None, split: int = 11) -> tuple[object, object]:
    data = package.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    split = min(split, len(data))
    request = TransferCreate("receiver", transfer_id, capture_id, package.name, len(data), declared_digest or digest)
    receiver.create_transfer(request.to_dict(), token_authenticated=True)
    receiver.put_chunk(transfer_id, offset=0, payload=data[:split], chunk_sha256=hashlib.sha256(data[:split]).hexdigest(), token_authenticated=True)
    receiver.put_chunk(transfer_id, offset=split, payload=data[split:], chunk_sha256=hashlib.sha256(data[split:]).hexdigest(), token_authenticated=True)
    return receiver.complete(transfer_id, token_authenticated=True)


def test_resumed_receiver_restart_imports_once_through_raw_index_and_report(tmp_path: Path, repo_root: Path) -> None:
    package = _valid_package(tmp_path / "capture.packscan", repo_root)
    data = package.read_bytes()
    first = PackLabReceiver(tmp_path, receiver_id="receiver", certificate_fingerprint="pin")
    request = TransferCreate("receiver", "transfer", "integration-capture", package.name, len(data), hashlib.sha256(data).hexdigest())
    first.create_transfer(request.to_dict(), token_authenticated=True)
    first.put_chunk("transfer", offset=0, payload=data[:7], chunk_sha256=hashlib.sha256(data[:7]).hexdigest(), token_authenticated=True)

    restarted = PackLabReceiver(tmp_path, receiver_id="receiver", certificate_fingerprint="pin")
    assert restarted.status("transfer", token_authenticated=True).next_offset == 7
    restarted.put_chunk("transfer", offset=7, payload=data[7:], chunk_sha256=hashlib.sha256(data[7:]).hexdigest(), token_authenticated=True)
    ack, result = restarted.complete("transfer", token_authenticated=True)
    assert ack.verified and result.state == "reported"
    assert len(list((tmp_path / "raw").glob("*.packscan"))) == 1
    assert len(list((tmp_path / "reports").glob("*.json"))) == 1
    duplicate_ack, duplicate = _transfer(restarted, package, "transfer-duplicate")
    assert duplicate_ack.verified and duplicate.state == "duplicate"
    assert len(list((tmp_path / "raw").glob("*.packscan"))) == 1


def test_cancel_retry_and_checksum_failure_never_publish_unverified_package(tmp_path: Path, repo_root: Path) -> None:
    package = _valid_package(tmp_path / "capture.packscan", repo_root)
    data = package.read_bytes()
    receiver = PackLabReceiver(tmp_path, receiver_id="receiver", certificate_fingerprint="pin")
    request = TransferCreate("receiver", "cancelled", "cancel-capture", package.name, len(data), hashlib.sha256(data).hexdigest())
    receiver.create_transfer(request.to_dict(), token_authenticated=True)
    receiver.put_chunk("cancelled", offset=0, payload=data[:5], chunk_sha256=hashlib.sha256(data[:5]).hexdigest(), token_authenticated=True)
    receiver.cancel("cancelled", token_authenticated=True)
    receiver.transfers.resume("cancelled")
    receiver.put_chunk("cancelled", offset=5, payload=data[5:], chunk_sha256=hashlib.sha256(data[5:]).hexdigest(), token_authenticated=True)
    assert receiver.complete("cancelled", token_authenticated=True)[0].verified

    ack, result = _transfer(receiver, package, "bad-digest", capture_id="bad-digest", declared_digest="a" * 64)
    assert not ack.verified and result is None
    assert receiver.status("bad-digest", token_authenticated=True).state == "checksum_failed"
    assert not (tmp_path / "capture_inbox" / "bad-digest.packscan").exists()


@pytest.mark.parametrize(
    ("name", "builder"),
    [
        ("corrupt", _corrupt),
        ("missing-photo", _missing_photo),
        ("bad-manifest", lambda path, repo: _invalid_zip(path, manifest=b"not-json")),
        ("future", lambda path, repo: _invalid_zip(path, manifest=json.dumps({"schema_version": "2.0.0", "capture_id": "future"}).encode(), extra={"checksums.json": b"{}"})),
        ("unsafe", lambda path, repo: _invalid_zip(path, extra={"../escape.bin": b"bad"})),
    ],
)
def test_invalid_transfers_are_quarantined_and_never_reach_raw_store(tmp_path: Path, repo_root: Path, name, builder) -> None:
    package = builder(tmp_path / f"{name}.packscan", repo_root)
    receiver = PackLabReceiver(tmp_path, receiver_id="receiver", certificate_fingerprint="pin")
    ack, result = _transfer(receiver, package, f"{name}-transfer", capture_id=f"{name}-capture")
    assert ack.verified and result.state == "quarantined"
    assert not list((tmp_path / "raw").glob("*.packscan"))
    assert list((tmp_path / "quarantine" / "packages").glob("*.packscan"))
