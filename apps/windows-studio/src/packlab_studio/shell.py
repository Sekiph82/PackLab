"""Minimal production Studio shell; domain services are injected later."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QByteArray, QStandardPaths, Qt
from PySide6.QtGui import QCloseEvent, QGuiApplication, QIcon
from PySide6.QtWidgets import QMainWindow, QSplitter

from .autosave import AutosaveService
from .diagnostics import DiagnosticBundle, DiagnosticsBundleService
from .jobs import JobManager
from .navigation import (
    NavigationController,
    NavigationPanel,
    Route,
    RouteStack,
    ScanMasterEditorView,
)
from .preferences import PreferencesStore, WindowPreferences
from .project import ProjectManager
from .recovery import RecoveryManager
from .scan_master_promotion import ScanMasterPromotionAction, ScanMasterPromotionRequest
from .shutdown import ShutdownCoordinator
from .version import current_build_info
from .workspace import WorkspaceManager


class StudioMainWindow(QMainWindow):
    """The single top-level PackLab Studio window."""

    WINDOW_OBJECT_NAME = "packlab.studio.main-window"

    def __init__(
        self,
        *,
        ingest_controller: object = None,
        receiver: object = None,
        preferences: PreferencesStore | None = None,
        diagnostics_root: str | Path | None = None,
        available_work_area: tuple[int, int, int, int] | None = None,
        scan_master_request_provider: Callable[[str, str], ScanMasterPromotionRequest | None]
        | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName(self.WINDOW_OBJECT_NAME)
        self.setWindowTitle("PackLab Studio")
        self.setWindowIcon(QIcon())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.preferences = preferences
        self.navigation = NavigationController()
        self.job_manager = JobManager()
        self.project_manager = ProjectManager(job_manager=self.job_manager)
        self.scan_master_promotion = ScanMasterPromotionAction(self.project_manager)
        self.scan_master_request_provider = scan_master_request_provider
        self.project_manager.add_listener(self._on_project_changed)
        self.autosave = AutosaveService(self.project_manager)
        self.recovery: RecoveryManager | None = None
        self.recovery_items: tuple[object, ...] = ()
        default_diagnostics_root = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
        self.diagnostics = DiagnosticsBundleService(
            diagnostics_root or Path(default_diagnostics_root or ".") / "diagnostics"
        )
        self._diagnostic_errors: list[dict[str, object]] = []
        self._available_work_area = available_work_area
        self.shutdown = ShutdownCoordinator(self.job_manager)
        self._shutdown_requested = False
        self.navigation_panel = NavigationPanel()
        self.route_stack = RouteStack(ingest_controller=ingest_controller, receiver=receiver)
        editor = self.route_stack.views[Route.EDITOR]
        if isinstance(editor, ScanMasterEditorView):
            editor.promotion_requested.connect(self._promote_scan_master_from_editor)
        self.navigation_panel.route_requested.connect(self.navigation.navigate)
        self.navigation.route_changed.connect(
            lambda value: self.route_stack.show_route(Route(value))
        )
        self.navigation.route_changed.connect(
            lambda value: self.navigation_panel.select_route(Route(value))
        )
        splitter = QSplitter(self)
        splitter.setObjectName("packlab.main.splitter")
        splitter.addWidget(self.navigation_panel)
        splitter.addWidget(self.route_stack)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)
        self.workspace = WorkspaceManager(self, job_manager=self.job_manager)
        self.navigation.set_project_context(self.project_manager)
        self._sync_project_state()
        self._restore_preferences()

    def _restore_preferences(self) -> None:
        if self.preferences is None:
            self.navigation_panel.select_route(Route.LIBRARY)
            return
        saved = self.preferences.load(bounds=self._available_work_area or self._current_work_area())
        self.setGeometry(*saved.geometry)
        if saved.maximized:
            self.showMaximized()
        if saved.fullscreen:
            self.showFullScreen()
        if saved.dock_state:
            self.restoreState(QByteArray.fromBase64(saved.dock_state.encode("ascii")))
        try:
            self.navigation.navigate(Route(saved.last_route))
        except ValueError:
            self.navigation.navigate(Route.LIBRARY)
        self.navigation_panel.select_route(self.navigation.current_route)

    def _current_work_area(self) -> tuple[int, int, int, int] | None:
        screens = QGuiApplication.screens()
        if not screens:
            return None
        geometries = [screen.availableGeometry() for screen in screens]
        left = min(rect.left() for rect in geometries)
        top = min(rect.top() for rect in geometries)
        right = max(rect.right() for rect in geometries)
        bottom = max(rect.bottom() for rect in geometries)
        return left, top, right - left + 1, bottom - top + 1

    def _on_project_changed(self, _metadata: object) -> None:
        self._sync_project_state()

    def _sync_project_state(self) -> None:
        available = self.project_manager.current is not None
        self.recovery = self.project_manager.recovery
        self.recovery_items = self.project_manager.recovery_items
        self.navigation_panel.set_project_available(available)
        self.route_stack.set_project_available(available)
        self.workspace.set_project_available(available)

    def _promote_scan_master_from_editor(self, actor_id: str, reason: str) -> None:
        editor = self.route_stack.views[Route.EDITOR]
        if not isinstance(editor, ScanMasterEditorView):
            return
        if self.scan_master_request_provider is None:
            editor.set_promotion_status("No eligible captured cleanup selection is loaded.")
            return
        metadata = self.project_manager.current
        if metadata is None:
            editor.set_promotion_status("Open a project before promoting Scan Master.")
            return
        try:
            request = self.scan_master_request_provider(actor_id, reason)
            if request is None:
                editor.set_promotion_status("Promotion cancelled; no revision was created.")
                return
            request = replace(request, actor_id=actor_id, reason=reason)
            revision = self.scan_master_promotion.promote(
                request, expected_project_revision=metadata.revision
            )
        except Exception as error:
            editor.set_promotion_status(f"Promotion rejected: {error}")
            return
        editor.set_promotion_status(
            f"Selected Scan Master {revision.revision_id}; "
            "DEFERRED_OWNER_VALIDATION; scale state inherited; mold_use_authorized=false."
        )

    def new_project(self, root: str | Path, name: str):
        return self.project_manager.new_project(root, name)

    def open_project(self, root: str | Path):
        return self.project_manager.open_project(root)

    def close_project(self, *, allow_active_jobs: bool = False) -> None:
        self.project_manager.close(allow_active_jobs=allow_active_jobs)

    def accept_recovery(self, item_id: str):
        item = self.project_manager.accept_recovery(item_id)
        self._sync_project_state()
        return item

    def discard_recovery(self, item_id: str):
        item = self.project_manager.discard_recovery(item_id)
        self._sync_project_state()
        return item

    def create_diagnostic_bundle(
        self, destination: str | Path | None = None, *, logs: str = ""
    ) -> DiagnosticBundle:
        errors = list(self._diagnostic_errors)
        errors.extend(
            {"job_id": job.job_id, "error": job.error, "message": job.message}
            for job in self.job_manager.jobs()
            if job.error
        )
        return self.diagnostics.create_bundle(
            destination,
            logs=logs,
            build_info=asdict(current_build_info()),
            project_summary=self.project_manager.project_summary(),
            active_jobs=[
                {
                    "job_id": job.job_id,
                    "state": job.state.value,
                    "progress": job.progress,
                    "message": job.message,
                }
                for job in self.job_manager.active_jobs()
            ],
            structured_errors=errors,
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._shutdown_requested and self.job_manager.active_jobs():
            event.ignore()
            self._shutdown_requested = True
            self.shutdown.begin(lambda result: self._finish_shutdown(result))
            return
        self.autosave.shutdown_flush()
        self.project_manager.close()
        if self.preferences is not None:
            state = self.saveState().toBase64().toStdString()
            self.preferences.save(
                WindowPreferences(
                    geometry=(self.x(), self.y(), self.width(), self.height()),
                    maximized=self.isMaximized(),
                    fullscreen=self.isFullScreen(),
                    dock_state=state,
                    last_route=self.navigation.current_route.value,
                )
            )
        super().closeEvent(event)

    def _finish_shutdown(self, _result: object) -> None:
        self.close()
