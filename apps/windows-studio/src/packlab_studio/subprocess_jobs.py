"""PackLab-owned subprocess adapter using the existing safe runner."""

from __future__ import annotations

import threading
from collections.abc import Sequence
from pathlib import Path

from packlab_core.subprocess_runner import ProcessResult, run_process

from .jobs import JobManager


class OwnedSubprocessJob:
    def __init__(
        self, manager: JobManager, job_id: str, args: Sequence[str], *, cwd: Path | None = None
    ) -> None:
        self.manager = manager
        self.job_id = job_id
        self.args = tuple(args)
        self.cwd = cwd
        self.cancel_event = threading.Event()
        self.result: ProcessResult | None = None
        manager.register_cancel_hook(job_id, self._cancel)

    def _cancel(self) -> bool:
        self.cancel_event.set()
        # The runner must report cleanup before the logical job becomes terminal.
        return False

    @property
    def cancellation_requested(self) -> bool:
        return self.cancel_event.is_set()

    def run(self) -> ProcessResult:
        self.manager.start(self.job_id)
        self.result = run_process(self.args, cancel_event=self.cancel_event, cwd=self.cwd)
        if self.result.cancelled:
            self.manager.finish_cancel(self.job_id, self.result.error)
        elif self.result.returncode == 0:
            self.manager.succeed(self.job_id)
        else:
            self.manager.fail(self.job_id, f"exit code {self.result.returncode}")
        return self.result
