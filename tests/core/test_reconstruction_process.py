from __future__ import annotations

import sys
import threading

from packlab_core.reconstruction import StageStatus
from packlab_core.reconstruction_process import run_reconstruction_stage


def _child(code: str) -> list[str]:
    return [sys.executable, "-c", code]


def test_stage_evidence_bounds_and_redacts_output() -> None:
    result = run_reconstruction_stage(
        "feature-extraction",
        _child(
            "import sys; print('C:\\\\private\\\\capture\\\\image.jpg token=SECRET'); "
            "print('x' * 1000, file=sys.stderr)"
        ),
        max_output_chars=120,
    )
    assert result.status is StageStatus.SUCCEEDED
    assert result.exit_code == 0
    assert result.duration_seconds >= 0
    assert len(result.stdout) <= 120
    assert len(result.stderr) <= 120
    assert "SECRET" not in result.stdout
    assert "private" not in result.stdout.lower()


def test_stage_failure_preserves_exit_and_is_machine_readable() -> None:
    result = run_reconstruction_stage("matching", _child("raise SystemExit(7)"))
    assert result.status is StageStatus.FAILED
    assert result.exit_code == 7
    assert result.failure_reason == "stage exited 7"


def test_stage_cancellation_is_distinct() -> None:
    event = threading.Event()
    event.set()
    result = run_reconstruction_stage("dense", _child("print('not run')"), cancel_event=event)
    assert result.status is StageStatus.CANCELLED
    assert result.cancelled is True


def test_pre_set_stage_cancellation_does_not_succeed() -> None:
    event = threading.Event()
    event.set()
    result = run_reconstruction_stage("dense", _child("print('not run')"), cancel_event=event)
    assert result.status is StageStatus.CANCELLED
    assert result.cancelled is True
    assert result.exit_code is None
