"""Minimal production Studio shell; domain services are injected later."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, replace
from functools import partial
from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings, QStandardPaths, Qt
from PySide6.QtGui import QCloseEvent, QGuiApplication
from PySide6.QtWidgets import QFileDialog, QMainWindow, QSplitter

from .autosave import AutosaveService
from .branding import application_icon
from .build_model import BuildBackend, BuildModelController, BuildModelView, BuildResult
from .capture_inbox import CaptureInboxView
from .design_workbench import DesignWorkbench
from .diagnostics import DiagnosticBundle, DiagnosticsBundleService
from .engineering_export import DesignModelExportSource, DestinationProvider
from .jobs import JobManager
from .labels_view import install_design_workbench
from .measure_view import MeasureDesignView
from .model_viewer import ModelViewerView
from .navigation import (
    NavigationController,
    NavigationPanel,
    Route,
    RouteStack,
    ScanMasterEditorView,
    SettingsView,
)
from .packaging_library_audit import PackagingLibraryAuditStore
from .packaging_library_browser import (
    LibraryRelatedRecord,
    LinkedProjectRevision,
    PackagingLibraryBrowserService,
    ProjectPreviewResolution,
)
from .preferences import PreferencesStore, WindowPreferences
from .project import ProjectManager
from .receiver_session import ReceiverSession
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
        receiver_session_factory: Callable[[], ReceiverSession] | None = None,
        preferences: PreferencesStore | None = None,
        diagnostics_root: str | Path | None = None,
        available_work_area: tuple[int, int, int, int] | None = None,
        scan_master_request_provider: Callable[[str, str], ScanMasterPromotionRequest | None]
        | None = None,
        design_model_export_source_provider: Callable[[], DesignModelExportSource | None]
        | None = None,
        export_destination_provider: DestinationProvider | None = None,
        packaging_library_service: PackagingLibraryBrowserService | None = None,
        packaging_library_root: str | Path | None = None,
        packaging_library_preview_resolver: Callable[
            [LinkedProjectRevision], ProjectPreviewResolution | None
        ]
        | None = None,
        packaging_library_related_records_resolver: Callable[
            [str], tuple[LibraryRelatedRecord, ...]
        ]
        | None = None,
        default_project_root: str | Path | None = None,
        settings_path: str | Path | None = None,
        build_backend: BuildBackend | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName(self.WINDOW_OBJECT_NAME)
        self.setWindowTitle("PackLab Studio")
        self.setWindowIcon(application_icon())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.preferences = preferences
        self.navigation = NavigationController()
        self.job_manager = JobManager()
        self.project_manager = ProjectManager(job_manager=self.job_manager)
        self.packaging_library_audit_store: PackagingLibraryAuditStore | None = None
        if packaging_library_service is not None and packaging_library_root is not None:
            raise ValueError("provide a library service or root, not both")
        if packaging_library_service is None:
            configured_root = packaging_library_root
            if configured_root is None:
                app_data_root = QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.AppLocalDataLocation
                )
                configured_root = (
                    Path(app_data_root or Path.home() / ".local/share/PackLab Studio")
                    / "packaging-library"
                )
            self.packaging_library_audit_store = PackagingLibraryAuditStore(configured_root)
            packaging_library_service = PackagingLibraryBrowserService(
                self.packaging_library_audit_store,
                configured_root,
                preview_resolver=packaging_library_preview_resolver,
                related_records_resolver=packaging_library_related_records_resolver,
            )
        else:
            self.packaging_library_audit_store = getattr(
                packaging_library_service, "audit_store", None
            )
        self.packaging_library_service = packaging_library_service
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
        if receiver_session_factory is None:
            transfer_root = Path(default_diagnostics_root or Path.home() / ".packlab")
            receiver_session_factory = lambda: ReceiverSession(  # noqa: E731
                transfer_root / "transfer-inbox", tls_root=transfer_root / "transfer-tls"
            )
        self.navigation_panel = NavigationPanel()
        # One active Design Model for Labels, Exports and the library (PL-0448/0449/0460).
        self.design_workbench = DesignWorkbench()
        if design_model_export_source_provider is None:
            design_model_export_source_provider = self.design_workbench.export_source
        self.route_stack = RouteStack(
            design_workbench=self.design_workbench,
            ingest_controller=ingest_controller,
            receiver=receiver,
            receiver_session_factory=receiver_session_factory,
            project_manager=self.project_manager,
            packaging_library_service=packaging_library_service,
            design_model_export_source_provider=design_model_export_source_provider,
            export_destination_provider=export_destination_provider,
            job_manager=self.job_manager,
        )
        self._default_project_root = (
            None if default_project_root is None else Path(default_project_root)
        )
        self._settings = (
            None
            if settings_path is None
            else QSettings(str(settings_path), QSettings.Format.IniFormat)
        )
        self.build_model = BuildModelController(
            self.job_manager, self.project_manager, backend=build_backend
        )
        self._wire_build_model()
        measure = self.route_stack.views[Route.MEASURE_DESIGN]
        if self.scan_master_request_provider is None and isinstance(measure, MeasureDesignView):
            # Editor > Promote uses the cleaned object selection from Measure & Design.
            self.scan_master_request_provider = measure.promotion_request
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
        install_design_workbench(self)
        self.workspace = WorkspaceManager(self, job_manager=self.job_manager)
        self.navigation.set_project_context(self.project_manager)
        self._sync_project_state()
        self._restore_preferences()
        self._build_menus()
        if self._default_project_root is not None:
            self.ensure_project()

    # ------------------------------------------------------------- menus (PL-0454/0455)

    MAX_RECENT_PROJECTS = 8

    def _build_menus(self) -> None:
        # Injectable choosers keep the menu actions testable offscreen.
        self.choose_new_project_path: Callable[[], str] = lambda: QFileDialog.getSaveFileName(
            self, "New project folder", str(Path.home()), "PackLab project folder (*)"
        )[0]
        self.choose_open_project_path: Callable[[], str] = lambda: QFileDialog.getExistingDirectory(
            self, "Open PackLab project"
        )
        file_menu = self.menuBar().addMenu("&File")
        file_menu.setObjectName("packlab.menu.file")
        self.new_project_action = file_menu.addAction("&New Project…", self._new_project_from_menu)
        self.open_project_action = file_menu.addAction(
            "&Open Project…", self._open_project_from_menu
        )
        self.recent_menu = file_menu.addMenu("Open &Recent")
        self.close_project_action = file_menu.addAction(
            "&Close Project", self._close_project_from_menu
        )
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.setObjectName("packlab.menu.help")
        self.diagnostic_bundle_action = help_menu.addAction(
            "Create &diagnostic bundle", self._diagnostic_bundle_from_menu
        )
        self.project_manager.add_listener(lambda _metadata: self._refresh_project_menu())
        self._refresh_project_menu()

    def recent_projects(self) -> list[str]:
        if self._settings is None:
            return []
        value = self._settings.value("projects/recent", [])
        items: list[object] = (
            [value] if isinstance(value, str) else list(value) if isinstance(value, list) else []
        )
        return [str(item) for item in items if item][: self.MAX_RECENT_PROJECTS]

    def _refresh_project_menu(self) -> None:
        layout = self.project_manager.layout
        if layout is not None and self._settings is not None:
            root = str(layout.root)
            recent = [root, *[item for item in self.recent_projects() if item != root]]
            self._settings.setValue("projects/recent", recent[: self.MAX_RECENT_PROJECTS])
        self.close_project_action.setEnabled(layout is not None)
        self.recent_menu.clear()
        for item in self.recent_projects():
            action = self.recent_menu.addAction(item)
            action.triggered.connect(partial(self._open_project_path, item))
        self.recent_menu.setEnabled(not self.recent_menu.isEmpty())
        name = None if self.project_manager.current is None else self.project_manager.current.name
        self.setWindowTitle(f"PackLab Studio — {name}" if name else "PackLab Studio")

    def _menu_status(self, text: str) -> None:
        self.statusBar().showMessage(text, 15000)

    def _new_project_from_menu(self) -> None:
        chosen = self.choose_new_project_path()
        if not chosen:
            return
        try:
            self.new_project(chosen, Path(chosen).name)
            self._menu_status(f"Created project {chosen}")
        except Exception as error:
            self._menu_status(f"New project failed: {error}")

    def _open_project_from_menu(self) -> None:
        chosen = self.choose_open_project_path()
        if chosen:
            self._open_project_path(chosen)

    def _open_project_path(self, path: str) -> None:
        try:
            self.open_project(path)
            self._menu_status(f"Opened project {path}")
        except Exception as error:
            self._menu_status(f"Open project failed: {error}")

    def _close_project_from_menu(self) -> None:
        try:
            self.close_project()
            self._menu_status("Project closed")
        except Exception as error:  # e.g. a build is still running
            self._menu_status(f"Close project failed: {error}")

    def _diagnostic_bundle_from_menu(self) -> None:
        try:
            bundle = self.create_diagnostic_bundle()
            self._menu_status(f"Diagnostic bundle written: {bundle.path}")
        except Exception as error:
            self._menu_status(f"Diagnostic bundle failed: {error}")

    # ------------------------------------------------------------- build model (PL-0443/0453)

    def _wire_build_model(self) -> None:
        inbox = self.route_stack.views[Route.CAPTURE_INBOX]
        settings = self.route_stack.views[Route.SETTINGS]
        builds = self.route_stack.views[Route.RECONSTRUCTION]
        viewer = self.route_stack.views[Route.MODEL_VIEWER]
        assert isinstance(inbox, CaptureInboxView) and isinstance(settings, SettingsView)
        assert isinstance(builds, BuildModelView) and isinstance(viewer, ModelViewerView)
        if self._settings is not None:
            stored = self._settings.value("build/auto_after_import", True)
            settings.auto_build.setChecked(str(stored).lower() not in {"false", "0"})
            settings.auto_build.toggled.connect(
                lambda value: (
                    self._settings.setValue("build/auto_after_import", value)
                    if self._settings is not None
                    else None
                )
            )
        inbox.build_requested.connect(self.start_build)
        inbox.scan_imported.connect(
            lambda capture_id, digest: (
                self.start_build(capture_id, digest) if settings.auto_build.isChecked() else None
            )
        )
        self.build_model.build_started.connect(builds.track)
        self.build_model.build_finished.connect(self._on_build_finished)
        builds.open_model_requested.connect(self._open_in_viewer)
        builds.route_requested.connect(self.navigation.navigate)
        measure = self.route_stack.views[Route.MEASURE_DESIGN]
        if isinstance(measure, MeasureDesignView):
            # Next-step buttons hand the just-built model to Measure & Design.
            builds.route_requested.connect(
                lambda value: (
                    measure.use_latest_build(
                        None if builds.result is None else builds.result.model_path
                    )
                    if value == Route.MEASURE_DESIGN.value
                    else None
                )
            )

    def ensure_project(self):
        """Open (or create on first run) the per-user default project; no dialog needed."""
        if self.project_manager.current is not None or self._default_project_root is None:
            return self.project_manager.current
        root = self._default_project_root
        try:
            if root.exists():
                return self.project_manager.open_project(root)
            root.parent.mkdir(parents=True, exist_ok=True)
            return self.project_manager.new_project(root, "My scans")
        except Exception as error:  # surfaced in the inbox; Studio stays usable
            self._inbox_note(f"Default project unavailable: {error}")
            return None

    def _inbox_note(self, text: str) -> None:
        """Append to the inbox status so the import result stays visible."""
        inbox = self.route_stack.views[Route.CAPTURE_INBOX]
        if isinstance(inbox, CaptureInboxView):
            current = inbox.status_label.text()
            inbox.status_label.setText(f"{current}\n{text}" if current else text)

    def start_build(self, capture_id: str, package_sha256: str) -> str | None:
        inbox = self.route_stack.views[Route.CAPTURE_INBOX]
        assert isinstance(inbox, CaptureInboxView)
        session = inbox.session
        package = None if session is None else session.package_path(package_sha256)
        if package is None:
            self._inbox_note(f"Build model: scan {capture_id} is not in the inbox.")
            return None
        self.ensure_project()
        try:
            job_id = self.build_model.build(package, capture_id, package_sha256)
        except Exception as error:
            self._inbox_note(f"Build model could not start: {error}")
            return None
        self.navigation.navigate(Route.RECONSTRUCTION)
        return job_id

    def _on_build_finished(self, result: BuildResult) -> None:
        builds = self.route_stack.views[Route.RECONSTRUCTION]
        if isinstance(builds, BuildModelView):
            builds.show_result(result)
        if result.status == "succeeded" and result.model_path is not None:
            self._open_in_viewer(result.model_path, note=result.message)

    def _open_in_viewer(self, path: Path, note: str = "") -> None:
        viewer = self.route_stack.views[Route.MODEL_VIEWER]
        if isinstance(viewer, ModelViewerView) and viewer.load(Path(path)):
            if note:
                viewer.status.setText(f"{note} {viewer.status.text()}")
            self.navigation.navigate(Route.MODEL_VIEWER)

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
        capture_inbox = self.route_stack.views[Route.CAPTURE_INBOX]
        if isinstance(capture_inbox, CaptureInboxView):
            capture_inbox.shutdown()
        self.autosave.shutdown_flush()
        self.project_manager.close(allow_active_jobs=self._shutdown_requested)
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
