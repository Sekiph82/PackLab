"""Debounced, revision-aware autosave for editable project state."""

from __future__ import annotations

import threading
from enum import StrEnum
from typing import Any

from PySide6.QtCore import QObject, Signal

from .project import ProjectError, ProjectManager, RevisionConflict


class SaveStatus(StrEnum):
    CLEAN = "clean"
    PENDING = "pending"
    SAVING = "saving"
    SAVED = "saved"
    ERROR = "error"
    CONFLICT = "conflict"


class AutosaveService(QObject):
    status_changed = Signal(str)
    error_changed = Signal(str)

    def __init__(self, manager: ProjectManager, *, debounce_seconds: float = 0.25) -> None:
        super().__init__()
        self.manager = manager
        self.debounce_seconds = max(0.01, debounce_seconds)
        self.status = SaveStatus.CLEAN
        self._pending: dict[str, Any] | None = None
        self._base_revision: int | None = None
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def schedule(self, state: dict[str, Any]) -> None:
        with self._lock:
            if self.manager.metadata is None:
                raise ProjectError("cannot autosave without an open project")
            self._pending = dict(state)
            self._base_revision = self.manager.metadata.revision
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_seconds, self.flush)
            self._timer.daemon = True
            self._timer.start()
        self._set_status(SaveStatus.PENDING)

    def flush(self) -> SaveStatus:
        with self._lock:
            state = self._pending
            base_revision = self._base_revision
            self._pending = None
            self._base_revision = None
            self._timer = None
        if state is None or base_revision is None:
            return self.status
        self._set_status(SaveStatus.SAVING)
        try:
            self.manager.commit_edit(state, expected_revision=base_revision)
        except RevisionConflict as error:
            self._set_status(SaveStatus.CONFLICT, str(error))
        except (ProjectError, OSError) as error:
            self._set_status(SaveStatus.ERROR, str(error))
        else:
            self._set_status(SaveStatus.SAVED)
        return self.status

    def shutdown_flush(self) -> SaveStatus:
        if self._timer is not None:
            self._timer.cancel()
        return self.flush()

    def _set_status(self, status: SaveStatus, error: str | None = None) -> None:
        self.status = status
        self.status_changed.emit(status.value)
        if error:
            self.error_changed.emit(error[:256])

