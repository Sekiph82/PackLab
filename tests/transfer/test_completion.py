from __future__ import annotations

import hashlib

from packlab_core.transfer_protocol import CompletionAcknowledgement, TransferStatus
from packlab_studio.transfer_completion import SenderTransferController


def test_sender_progress_is_confirmed_and_completion_requires_authenticated_matching_ack() -> None:
    data = b"abcdefgh"
    digest = hashlib.sha256(data).hexdigest()
    controller = SenderTransferController(transfer_id="t", package_sha256=digest, total_bytes=len(data))
    state = controller.confirmed_status(TransferStatus("t", 4, 8, "receiving", digest, 4))
    assert state.confirmed_bytes == 4 and state.phase == "transferring"
    pending = controller.apply_completion_ack(CompletionAcknowledgement("t", digest, False, True, "checksum_failed"))
    assert pending.phase == "retryable_failure"
    controller.confirmed_status(TransferStatus("t", 8, 8, "verified", digest, 8))
    done = controller.apply_completion_ack(CompletionAcknowledgement("t", digest, True, True, "verified"))
    assert done.phase == "completed"


def test_sender_never_completes_on_wrong_digest_or_unauthenticated_ack() -> None:
    controller = SenderTransferController(transfer_id="t", package_sha256="a" * 64, total_bytes=1)
    wrong = controller.apply_completion_ack(CompletionAcknowledgement("t", "b" * 64, True, True, "verified"))
    assert wrong.phase == "retryable_failure"
    unauthenticated = controller.apply_completion_ack(CompletionAcknowledgement("t", "a" * 64, True, False, "verified"))
    assert unauthenticated.phase == "retryable_failure"
