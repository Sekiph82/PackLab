"""Stable, route-independent QMainWindow dock topology."""

from __future__ import annotations

from enum import StrEnum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QLabel, QMainWindow

from .jobs import JobManager, JobPanel


class DockId(StrEnum):
    SCENE = "packlab.dock.scene"
    PROPERTIES = "packlab.dock.properties"
    JOBS = "packlab.dock.jobs"
    LOGS = "packlab.dock.logs"


class WorkspaceName(StrEnum):
    LIBRARY = "library"
    CAPTURE_INBOX = "capture-inbox"
    RECONSTRUCTION = "reconstruction"
    EDITOR = "editor"
    SETTINGS = "settings"


class WorkspaceManager:
    """Owns dock instances and their stable saveState/restoreState identity."""

    def __init__(self, window: QMainWindow, *, job_manager: JobManager | None = None) -> None:
        self.window = window
        self.job_manager = job_manager
        self._docks: dict[DockId, QDockWidget] = {}
        self._create_docks()
        self.reset_to_default(WorkspaceName.LIBRARY)

    @property
    def docks(self) -> dict[DockId, QDockWidget]:
        return dict(self._docks)

    def _create_docks(self) -> None:
        specs = {
            DockId.SCENE: ("Scene / Objects", Qt.DockWidgetArea.LeftDockWidgetArea),
            DockId.PROPERTIES: ("Properties / Inspector", Qt.DockWidgetArea.RightDockWidgetArea),
            DockId.JOBS: ("Jobs / Activity", Qt.DockWidgetArea.BottomDockWidgetArea),
            DockId.LOGS: ("Logs", Qt.DockWidgetArea.BottomDockWidgetArea),
        }
        for dock_id, (title, area) in specs.items():
            dock = QDockWidget(title, self.window)
            dock.setObjectName(dock_id.value)
            dock.setAllowedAreas(
                Qt.DockWidgetArea.LeftDockWidgetArea
                | Qt.DockWidgetArea.RightDockWidgetArea
                | Qt.DockWidgetArea.BottomDockWidgetArea
            )
            dock.setWidget(JobPanel(self.job_manager) if dock_id is DockId.JOBS and self.job_manager is not None else QLabel(title))
            self.window.addDockWidget(area, dock)
            self._docks[dock_id] = dock

    def reset_to_default(self, workspace: WorkspaceName | str) -> None:
        name = WorkspaceName(workspace)
        for dock in self._docks.values():
            dock.show()
        if name is WorkspaceName.SETTINGS:
            self._docks[DockId.SCENE].hide()
        elif name is WorkspaceName.CAPTURE_INBOX:
            self._docks[DockId.PROPERTIES].hide()
        elif name is WorkspaceName.LIBRARY:
            self._docks[DockId.LOGS].hide()
        self._restore_default_areas()

    def _restore_default_areas(self) -> None:
        self.window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._docks[DockId.SCENE])
        self.window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._docks[DockId.PROPERTIES])
        self.window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._docks[DockId.JOBS])
        self.window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._docks[DockId.LOGS])
