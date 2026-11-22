"""Stable, route-independent QMainWindow dock topology."""

from __future__ import annotations

from enum import StrEnum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QLabel, QMainWindow

from .i18n import tr
from .jobs import JobManager, JobPanel

QWIDGETSIZE_MAX = 16777215


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


# Scene/Properties/Logs have no content yet: hidden by default, reachable from View (PL-0464).
DEFAULT_VISIBLE_DOCKS = frozenset({DockId.JOBS})


class WorkspaceManager:
    """Owns dock instances and their stable saveState/restoreState identity."""

    def __init__(self, window: QMainWindow, *, job_manager: JobManager | None = None) -> None:
        self.window = window
        self.job_manager = job_manager
        self._docks: dict[DockId, QDockWidget] = {}
        self._create_docks()
        self.reset_to_default(WorkspaceName.LIBRARY)
        if job_manager is not None:
            job_manager.job_added.connect(self._update_jobs_dock)
            job_manager.job_changed.connect(self._update_jobs_dock)
            job_manager.history_changed.connect(self._update_jobs_dock)
        self._update_jobs_dock()

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
            dock = QDockWidget(tr(title), self.window)
            dock.setObjectName(dock_id.value)
            dock.setAllowedAreas(
                Qt.DockWidgetArea.LeftDockWidgetArea
                | Qt.DockWidgetArea.RightDockWidgetArea
                | Qt.DockWidgetArea.BottomDockWidgetArea
            )
            dock.setWidget(
                JobPanel(self.job_manager)
                if dock_id is DockId.JOBS and self.job_manager is not None
                else QLabel(tr(title))
            )
            self.window.addDockWidget(area, dock)
            self._docks[dock_id] = dock

    def reset_to_default(self, workspace: WorkspaceName | str) -> None:
        WorkspaceName(workspace)  # validated; every workspace shares one sane default now
        for dock_id, dock in self._docks.items():
            dock.setVisible(dock_id in DEFAULT_VISIBLE_DOCKS)
        self._restore_default_areas()

    def set_project_available(self, available: bool) -> None:
        # Visibility is the user's View-menu choice; only enablement follows the project.
        for dock_id in (DockId.SCENE, DockId.PROPERTIES):
            self._docks[dock_id].setEnabled(available)

    def _update_jobs_dock(self, _job_id: str | None = None) -> None:
        """Compact (about two rows) while idle; grows and shows itself when a job runs."""
        dock = self._docks[DockId.JOBS]
        panel = dock.widget()
        active = len(self.job_manager.active_jobs()) if self.job_manager is not None else 0
        row = panel.fontMetrics().height() + 6
        if active:
            dock.setWindowTitle(tr("Jobs ({count} running)").format(count=active))
            panel.setMinimumHeight(row * 4)
            panel.setMaximumHeight(QWIDGETSIZE_MAX)
            dock.show()
        else:
            dock.setWindowTitle(tr("Jobs (idle)"))
            panel.setMinimumHeight(0)
            panel.setMaximumHeight(row * 2 + 4)

    def _restore_default_areas(self) -> None:
        self.window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._docks[DockId.SCENE])
        self.window.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self._docks[DockId.PROPERTIES]
        )
        self.window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._docks[DockId.JOBS])
        self.window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._docks[DockId.LOGS])
