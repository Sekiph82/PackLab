"""Central logical job state and its presentation-only activity panel."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"


TERMINAL_STATES = frozenset({JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED})
MAX_MESSAGE_LENGTH = 256


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class JobRecord:
    job_id: str
    title: str
    job_type: str
    state: JobState = JobState.QUEUED
    progress: float = 0.0
    created_at: str = field(default_factory=_now)
    started_at: str | None = None
    finished_at: str | None = None
    message: str = ""
    error: str | None = None
    cancellable: bool = True
    logs: list[str] = field(default_factory=list)

    def add_message(self, message: str) -> None:
        bounded = str(message)[:MAX_MESSAGE_LENGTH]
        self.message = bounded
        self.logs.append(bounded)
        del self.logs[:-50]


class JobManager(QObject):
    job_added = Signal(str)
    job_changed = Signal(str)
    history_changed = Signal()

    def __init__(self, *, history_limit: int = 100) -> None:
        super().__init__()
        self.history_limit = max(1, history_limit)
        self._jobs: dict[str, JobRecord] = {}
        self._order: list[str] = []
        self._cancel_hooks: dict[str, Callable[[], bool]] = {}

    def create(self, title: str, job_type: str, *, cancellable: bool = True, job_id: str | None = None) -> JobRecord:
        identifier = job_id or uuid.uuid4().hex
        if identifier in self._jobs:
            raise ValueError(f"duplicate job id: {identifier}")
        record = JobRecord(identifier, title[:MAX_MESSAGE_LENGTH], job_type[:MAX_MESSAGE_LENGTH], cancellable=cancellable)
        self._jobs[identifier] = record
        self._order.append(identifier)
        self._trim_history()
        self.job_added.emit(identifier)
        self.history_changed.emit()
        return record

    def get(self, job_id: str) -> JobRecord:
        try:
            return self._jobs[job_id]
        except KeyError as error:
            raise KeyError(f"unknown job: {job_id}") from error

    def jobs(self) -> tuple[JobRecord, ...]:
        return tuple(self._jobs[identifier] for identifier in self._order if identifier in self._jobs)

    def active_jobs(self) -> tuple[JobRecord, ...]:
        return tuple(job for job in self.jobs() if job.state not in TERMINAL_STATES)

    def start(self, job_id: str) -> JobRecord:
        job = self.get(job_id)
        if job.state is not JobState.QUEUED:
            raise ValueError("only queued jobs can start")
        job.state = JobState.RUNNING
        job.started_at = _now()
        self._changed(job)
        return job

    def update_progress(self, job_id: str, progress: float, message: str | None = None) -> JobRecord:
        job = self.get(job_id)
        if job.state not in {JobState.RUNNING, JobState.CANCELLING}:
            raise ValueError("progress requires an active job")
        bounded_progress = min(1.0, max(0.0, float(progress)))
        if bounded_progress < job.progress:
            raise ValueError("job progress cannot move backwards")
        job.progress = bounded_progress
        if message is not None:
            job.add_message(message)
        self._changed(job)
        return job

    def succeed(self, job_id: str, message: str = "completed") -> JobRecord:
        job = self.get(job_id)
        if job.state not in {JobState.RUNNING, JobState.CANCELLING}:
            raise ValueError("only active jobs can succeed")
        job.progress = 1.0
        job.state = JobState.SUCCEEDED
        job.finished_at = _now()
        job.add_message(message)
        self._changed(job)
        return job

    def fail(self, job_id: str, error: str, *, message: str = "failed") -> JobRecord:
        job = self.get(job_id)
        if job.state in TERMINAL_STATES:
            raise ValueError("terminal jobs cannot fail")
        job.state = JobState.FAILED
        job.error = str(error)[:MAX_MESSAGE_LENGTH]
        job.finished_at = _now()
        job.add_message(message)
        self._changed(job)
        return job

    def register_cancel_hook(self, job_id: str, hook: Callable[[], bool]) -> None:
        self.get(job_id)
        self._cancel_hooks[job_id] = hook

    def request_cancel(self, job_id: str) -> JobRecord:
        job = self.get(job_id)
        if not job.cancellable:
            raise ValueError("job is not cancellable")
        if job.state is JobState.QUEUED:
            job.state = JobState.CANCELLED
            job.finished_at = _now()
            job.add_message("cancelled before start")
        elif job.state is JobState.RUNNING:
            job.state = JobState.CANCELLING
            job.add_message("cancellation requested")
            hook = self._cancel_hooks.get(job_id)
            if hook is not None:
                try:
                    if hook():
                        job.state = JobState.CANCELLED
                        job.finished_at = _now()
                except Exception as error:
                    job.error = str(error)[:MAX_MESSAGE_LENGTH]
                    job.state = JobState.FAILED
                    job.finished_at = _now()
        self._changed(job)
        return job

    def _changed(self, job: JobRecord) -> None:
        self.job_changed.emit(job.job_id)
        self.history_changed.emit()

    def _trim_history(self) -> None:
        while len(self._order) > self.history_limit:
            removed = self._order.pop(0)
            self._jobs.pop(removed, None)
            self._cancel_hooks.pop(removed, None)


class JobPanel(QListWidget):
    """Read-only observer of JobManager; it never starts or stops jobs."""

    def __init__(self, manager: JobManager) -> None:
        super().__init__()
        self.setObjectName("packlab.panel.jobs")
        self.manager = manager
        manager.job_added.connect(self.refresh)
        manager.job_changed.connect(self.refresh)
        manager.history_changed.connect(self.refresh)
        self.refresh()

    def refresh(self, _job_id: str | None = None) -> None:
        self.clear()
        for job in self.manager.jobs():
            item = QListWidgetItem(f"{job.title} [{job.state.value}] {job.progress:.0%}")
            item.setData(0x0100, job.job_id)
            self.addItem(item)
