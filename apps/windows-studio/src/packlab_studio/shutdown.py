"""Bounded, non-blocking Studio shutdown coordination."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from PySide6.QtCore import QObject, QTimer, Signal

from .jobs import JobManager, JobState


class ShutdownState(StrEnum):
    IDLE = "idle"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed-out"


@dataclass(frozen=True, slots=True)
class ShutdownResult:
    state: ShutdownState
    errors: tuple[str, ...] = ()


class ShutdownCoordinator(QObject):
    state_changed = Signal(str)
    finished = Signal(object)

    def __init__(self, manager: JobManager, *, timeout_seconds: float = 2.0, poll_ms: int = 20) -> None:
        super().__init__()
        self.manager = manager
        self.timeout_seconds = max(0.05, timeout_seconds)
        self.poll_ms = max(1, poll_ms)
        self.state = ShutdownState.IDLE
        self._deadline = 0.0
        self._callback: Callable[[ShutdownResult], None] | None = None

    def begin(self, callback: Callable[[ShutdownResult], None] | None = None) -> ShutdownResult | None:
        if self.state is ShutdownState.CANCELLING:
            return None
        active = self.manager.active_jobs()
        if not active:
            result = ShutdownResult(ShutdownState.COMPLETED)
            self._publish(result)
            if callback:
                callback(result)
            return result
        self._callback = callback
        self.state = ShutdownState.CANCELLING
        self._deadline = time.monotonic() + self.timeout_seconds
        self.state_changed.emit(self.state.value)
        for job in active:
            if job.cancellable:
                self.manager.request_cancel(job.job_id)
            else:
                job.add_message("shutdown cannot cancel this job")
        QTimer.singleShot(0, self._poll)
        return None

    def _poll(self) -> None:
        active = self.manager.active_jobs()
        if not active:
            errors = tuple(job.error or job.message for job in self.manager.jobs() if job.state is JobState.FAILED)
            result = ShutdownResult(ShutdownState.FAILED if errors else ShutdownState.COMPLETED, errors)
            self._publish(result)
            return
        if time.monotonic() >= self._deadline:
            result = ShutdownResult(ShutdownState.TIMED_OUT, tuple(job.job_id for job in active))
            self._publish(result)
            return
        QTimer.singleShot(self.poll_ms, self._poll)

    def _publish(self, result: ShutdownResult) -> None:
        self.state = result.state
        self.state_changed.emit(result.state.value)
        callback = self._callback
        self._callback = None
        self.finished.emit(result)
        if callback:
            callback(result)

