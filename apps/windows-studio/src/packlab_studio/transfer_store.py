"""Crash-safe, resumable receiver-side storage for PackLab Transfer V1."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from packlab_core.transfer_protocol import (
    CompletionAcknowledgement,
    TransferCreate,
    TransferErrorCode,
    TransferProtocolError,
    TransferStatus,
)


class TransferStoreError(TransferProtocolError):
    pass


@dataclass(frozen=True, slots=True)
class ReceiverTransferState:
    transfer_id: str
    receiver_id: str
    capture_id: str
    package_name: str
    total_bytes: int
    package_sha256: str
    confirmed_bytes: int = 0
    state: str = "receiving"
    verification: dict[str, object] | None = None

    def status(self) -> TransferStatus:
        return TransferStatus(
            transfer_id=self.transfer_id,
            confirmed_bytes=self.confirmed_bytes,
            total_bytes=self.total_bytes,
            state=self.state,
            package_sha256=self.package_sha256,
            next_offset=self.confirmed_bytes,
        )


@dataclass(frozen=True, slots=True)
class VerificationResult:
    transfer_id: str
    verified: bool
    expected_sha256: str
    actual_sha256: str
    bytes_received: int


class ResumableTransferStore:
    """One transfer maps to one `.part` file and one atomic JSON checkpoint."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _part(self, transfer_id: str) -> Path:
        return self.root / f"{transfer_id}.part"

    def _checkpoint(self, transfer_id: str) -> Path:
        return self.root / f"{transfer_id}.json"

    def _read(self, transfer_id: str) -> ReceiverTransferState:
        try:
            value = json.loads(self._checkpoint(transfer_id).read_text(encoding="utf-8"))
            state = ReceiverTransferState(**value)
        except (OSError, ValueError, TypeError) as error:
            raise TransferStoreError(TransferErrorCode.UNKNOWN_TRANSFER, "transfer checkpoint is unavailable") from error
        if self._part(transfer_id).exists() and self._part(transfer_id).stat().st_size != state.confirmed_bytes:
            raise TransferStoreError(TransferErrorCode.INTERNAL_ERROR, "checkpoint and part byte counts differ")
        return state

    def _write_checkpoint(self, state: ReceiverTransferState) -> None:
        target = self._checkpoint(state.transfer_id)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{state.transfer_id}-", suffix=".checkpoint", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(asdict(state), handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    def create(self, request: TransferCreate) -> ReceiverTransferState:
        checkpoint = self._checkpoint(request.transfer_id)
        if checkpoint.exists():
            current = self._read(request.transfer_id)
            identity = (current.receiver_id, current.capture_id, current.package_name, current.total_bytes, current.package_sha256)
            requested = (request.receiver_id, request.capture_id, request.package_name, request.total_bytes, request.package_sha256)
            if identity != requested:
                raise TransferStoreError(TransferErrorCode.CONFLICTING_CHUNK, "transfer identity conflicts with checkpoint")
            return current
        state = ReceiverTransferState(
            transfer_id=request.transfer_id, receiver_id=request.receiver_id, capture_id=request.capture_id,
            package_name=request.package_name, total_bytes=request.total_bytes, package_sha256=request.package_sha256,
        )
        self._part(request.transfer_id).write_bytes(b"")
        self._write_checkpoint(state)
        return state

    def status(self, transfer_id: str) -> TransferStatus:
        return self._read(transfer_id).status()

    def put_chunk(self, transfer_id: str, *, offset: int, payload: bytes, chunk_sha256: str) -> TransferStatus:
        state = self._read(transfer_id)
        if state.state in {"verified", "complete"}:
            return state.status()
        if state.state == "cancelled":
            raise TransferStoreError(TransferErrorCode.CANCELLED, "transfer is cancelled; resume explicitly")
        actual_chunk = hashlib.sha256(payload).hexdigest()
        if actual_chunk != chunk_sha256:
            raise TransferStoreError(TransferErrorCode.BAD_REQUEST, "chunk digest does not match bytes")
        if offset < 0 or offset + len(payload) > state.total_bytes:
            raise TransferStoreError(TransferErrorCode.BAD_REQUEST, "chunk range is outside package")
        part = self._part(transfer_id)
        if offset < state.confirmed_bytes:
            existing = part.read_bytes()[offset : offset + len(payload)]
            if existing == payload:
                return state.status()
            raise TransferStoreError(TransferErrorCode.CONFLICTING_CHUNK, "retransmitted bytes conflict with checkpoint")
        if offset != state.confirmed_bytes:
            raise TransferStoreError(TransferErrorCode.OUT_OF_ORDER, "chunk does not begin at next required offset")
        with part.open("ab") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        updated = replace(state, confirmed_bytes=state.confirmed_bytes + len(payload))
        self._write_checkpoint(updated)
        return updated.status()

    def cancel(self, transfer_id: str) -> TransferStatus:
        state = self._read(transfer_id)
        if state.state in {"verified", "complete"}:
            raise TransferStoreError(TransferErrorCode.BAD_REQUEST, "verified transfer cannot be cancelled")
        updated = replace(state, state="cancelled")
        self._write_checkpoint(updated)
        return updated.status()

    def resume(self, transfer_id: str) -> TransferStatus:
        state = self._read(transfer_id)
        if state.state == "cancelled":
            state = replace(state, state="receiving")
            self._write_checkpoint(state)
        return state.status()

    def verify(self, transfer_id: str) -> VerificationResult:
        state = self._read(transfer_id)
        if state.confirmed_bytes != state.total_bytes:
            raise TransferStoreError(TransferErrorCode.BAD_REQUEST, "package is incomplete")
        actual = hashlib.sha256(self._part(transfer_id).read_bytes()).hexdigest()
        verified = actual == state.package_sha256
        updated = replace(
            state,
            state="verified" if verified else "checksum_failed",
            verification={"expected_sha256": state.package_sha256, "actual_sha256": actual, "bytes_received": state.confirmed_bytes},
        )
        self._write_checkpoint(updated)
        return VerificationResult(transfer_id, verified, state.package_sha256, actual, state.confirmed_bytes)

    def publish_verified(self, transfer_id: str, destination: str | Path) -> Path:
        state = self._read(transfer_id)
        if state.state != "verified":
            raise TransferStoreError(TransferErrorCode.CHECKSUM_MISMATCH, "only a checksum-verified transfer may be published")
        output = Path(destination)
        if output.exists():
            raise TransferStoreError(TransferErrorCode.BAD_REQUEST, "destination already exists")
        output.parent.mkdir(parents=True, exist_ok=True)
        os.replace(self._part(transfer_id), output)
        self._write_checkpoint(replace(state, state="complete"))
        return output

    def completion_ack(self, transfer_id: str, *, authenticated: bool) -> CompletionAcknowledgement:
        state = self._read(transfer_id)
        return CompletionAcknowledgement(transfer_id, state.package_sha256, state.state in {"verified", "complete"}, authenticated, state.state)
