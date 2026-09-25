"""Sender-side completion gate for authenticated receiver acknowledgements."""

from __future__ import annotations

from dataclasses import dataclass, replace

from packlab_core.transfer_protocol import (
    CompletionAcknowledgement,
    TransferErrorCode,
    TransferProtocolError,
    TransferStatus,
)


@dataclass(frozen=True, slots=True)
class SenderTransferState:
    transfer_id: str
    package_sha256: str
    total_bytes: int
    confirmed_bytes: int = 0
    phase: str = "connecting"
    error: str | None = None


class SenderTransferController:
    def __init__(self, *, transfer_id: str, package_sha256: str, total_bytes: int) -> None:
        self._state = SenderTransferState(transfer_id, package_sha256, total_bytes)

    @property
    def state(self) -> SenderTransferState:
        return self._state

    def confirmed_status(self, status: TransferStatus) -> SenderTransferState:
        if status.transfer_id != self._state.transfer_id or status.package_sha256 != self._state.package_sha256:
            raise TransferProtocolError(TransferErrorCode.CONFLICTING_CHUNK, "receiver status has a different transfer identity")
        if status.confirmed_bytes < self._state.confirmed_bytes:
            raise TransferProtocolError(TransferErrorCode.OUT_OF_ORDER, "receiver status moved backwards")
        if status.confirmed_bytes > self._state.total_bytes:
            raise TransferProtocolError(TransferErrorCode.BAD_REQUEST, "receiver confirmed too many bytes")
        phase = "verifying" if status.confirmed_bytes == self._state.total_bytes else "transferring"
        self._state = replace(self._state, confirmed_bytes=status.confirmed_bytes, phase=phase, error=None)
        return self._state

    def cancel(self) -> SenderTransferState:
        self._state = replace(self._state, phase="cancelled")
        return self._state

    def apply_completion_ack(self, acknowledgement: CompletionAcknowledgement) -> SenderTransferState:
        if acknowledgement.transfer_id != self._state.transfer_id or acknowledgement.package_sha256 != self._state.package_sha256:
            self._state = replace(self._state, phase="retryable_failure", error="acknowledgement_identity_mismatch")
            return self._state
        if not acknowledgement.authenticated or not acknowledgement.verified:
            self._state = replace(self._state, phase="retryable_failure", error="receiver_verification_required")
            return self._state
        self._state = replace(self._state, confirmed_bytes=self._state.total_bytes, phase="completed", error=None)
        return self._state
