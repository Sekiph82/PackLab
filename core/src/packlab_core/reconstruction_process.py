"""Bounded per-stage process evidence for reconstruction backends."""

from __future__ import annotations

import re
import threading
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

from .reconstruction import ReconstructionStageResult, StageStatus
from .subprocess_runner import run_process

MAX_STAGE_OUTPUT_CHARS = 16_384
_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:\\[^\r\n]+")
_POSIX_PATH = re.compile(r"(?<![\w])/(?:Users|home|private|tmp|var|workspace)/[^\r\n ]+")
_SECRET = re.compile(r"(?i)\b(?:token|password|secret|api[_-]?key)=\S+")


def redact_portable_output(value: str) -> str:
    """Remove portable-provenance secrets and machine-specific absolute paths."""

    redacted = _WINDOWS_PATH.sub("[REDACTED_PATH]", value)
    redacted = _POSIX_PATH.sub("[REDACTED_PATH]", redacted)
    return _SECRET.sub("[REDACTED_SECRET]", redacted)


def run_reconstruction_stage(
    stage_id: str,
    args: Sequence[str],
    *,
    timeout: float | None = None,
    cancel_event: threading.Event | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    max_output_chars: int = MAX_STAGE_OUTPUT_CHARS,
) -> ReconstructionStageResult:
    """Run one owned stage and normalize its bounded, portable evidence."""

    started = time.monotonic()
    result = run_process(
        args,
        timeout=timeout,
        cancel_event=cancel_event,
        cwd=cwd,
        env=env,
        max_output_chars=max_output_chars,
    )
    duration = max(0.0, time.monotonic() - started)
    if result.cancelled:
        status = StageStatus.CANCELLED
        reason = result.error or "stage cancelled"
    elif result.returncode == 0:
        status = StageStatus.SUCCEEDED
        reason = None
    else:
        status = StageStatus.FAILED
        reason = result.error or f"stage exited {result.returncode}"
    return ReconstructionStageResult(
        stage_id,
        status,
        result.returncode,
        duration,
        redact_portable_output(result.stdout),
        redact_portable_output(result.stderr),
        result.cancelled,
        reason,
    )
