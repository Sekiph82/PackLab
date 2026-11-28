"""Minimal production Studio shell; domain services are injected later."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import datetime
from functools import partial
from pathlib import Path

from PySide6.QtCore import QByteArray, QPoint, QSettings, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QActionGroup, QCloseEvent, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .autosave import AutosaveService
from .branding import application_icon
from .build_model import BuildBackend, BuildModelController, BuildModelView, BuildResult
from .capture_inbox import CaptureInboxView
from .design_workbench import DesignWorkbench
from .diagnostics import DiagnosticBundle, DiagnosticsBundleService
from .engineering_export import (
    DesignModelExportSource,
    DestinationProvider,
    EngineeringExportView,
    ExportSourceKind,
)
from .history import Operation
from .i18n import LANGUAGES, SETTINGS_KEY, set_language, tr, translate_widget_tree
from .jobs import JobManager
from .labels_view import LabelsView, install_design_workbench
from .mask_correction import MaskCorrectionView
from .measure_view import MeasureDesignView
from .model_viewer import ModelViewerView
from .navigation import (
    NavigationController,
    NavigationPanel,
    PageHeader,
    Route,
    RouteStack,
    ScanMasterEditorView,
    SettingsView,
)
from .package_families_view import PackageFamiliesView
from .packaging_library_audit import PackagingLibraryAuditStore
from .packaging_library_browser import (
    LibraryRelatedRecord,
    LinkedProjectRevision,
    PackagingLibraryBrowserService,
    ProjectPreviewResolution,
)
from .preferences import (
    DEFAULT_GEOMETRY,
    PreferencesStore,
    WindowPreferences,
    documents_folder,
    sanitize_geometry,
)
from .project import ProjectManager
from .project_parts import ScenePanel
from .receiver_session import ReceiverSession
from .recovery import RecoveryItem, RecoveryManager, RecoveryStatus
from .scan_master_promotion import ScanMasterPromotionAction, ScanMasterPromotionRequest
from .shutdown import ShutdownCoordinator
from .version import current_build_info
from .workspace import DockId, WorkspaceManager

AUTOSAVE_DRAFT_JOB = "autosave-design-draft"
AUTOSAVE_DRAFT_PATH = "autosave/design-model-draft.json"
AUTOSAVE_DELAY_MS = 2000
_POINTER_LABELS = {
    "active_design_model_revision_id": "Design Model",
    "active_scan_master_revision_id": "Scan Master",
    "selected_part": "Part selection",
}
_RECOVERY_LABELS = {AUTOSAVE_DRAFT_JOB: "Unsaved Design Model edits (autosaved draft)"}
# Restored geometry is the client area; keep room for the title bar and frame on screen (F5).
_FRAME_TOP, _FRAME_EDGE = 40, 8
_OPEN_PROJECT_HELP = (
    "Choose File > Open Project… and pick the project folder (the one that contains "
    "raw, working and .packlab-layout.json). If the folder is on a removable or network "
    "drive, connect it first."
)


def project_display_name(root: str | Path) -> str:
    """The project name from working/project.json; the folder name when unreadable (F6)."""

    try:
        value = json.loads((Path(root) / "working" / "project.json").read_text(encoding="utf-8"))
        name = value.get("name") if isinstance(value, dict) else None
    except (OSError, ValueError):
        name = None
    return name if isinstance(name, str) and name.strip() else Path(root).name or str(root)


class RecoveryDialog(QDialog):
    """Shown on open when the last session ended uncleanly; one Accept/Discard per item."""

    def __init__(self, window: StudioMainWindow) -> None:
        super().__init__(window)
        self.setObjectName("packlab.dialog.recovery")
        self.setWindowTitle("Recover after an unexpected exit")
        self.setModal(True)
        grid = QGridLayout(self)
        grid.addWidget(
            QLabel("PackLab did not close cleanly last time. Recover or discard each item:"),
            0,
            0,
            1,
            3,
        )
        self.buttons: dict[str, tuple[QPushButton, QPushButton]] = {}
        for row, item in enumerate(window.recovery_items, 1):
            label = _RECOVERY_LABELS.get(item.job_id, f"Job {item.job_id}")
            grid.addWidget(QLabel(f"{label}\n{item.status.value}: {item.reason}"), row, 0)
            accept = QPushButton("Recover" if item.job_id == AUTOSAVE_DRAFT_JOB else "Accept")
            discard = QPushButton("Discard")
            if item.status is RecoveryStatus.INVALID:  # changed/missing: Discard only
                accept.setText("Invalid")
                accept.setEnabled(False)
            accept.setObjectName(f"packlab.recovery.accept.{item.item_id}")
            discard.setObjectName(f"packlab.recovery.discard.{item.item_id}")
            accept.clicked.connect(partial(self._resolve, window.accept_recovery, item.item_id))
            discard.clicked.connect(partial(self._resolve, window.discard_recovery, item.item_id))
            grid.addWidget(accept, row, 1)
            grid.addWidget(discard, row, 2)
            self.buttons[item.item_id] = (accept, discard)

    def _resolve(self, action: Callable[[str], object], item_id: str) -> None:
        action(item_id)
        for button in self.buttons[item_id]:
            button.setEnabled(False)
        if not any(button.isEnabled() for pair in self.buttons.values() for button in pair):
            self.accept()


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
        self._settings = (
            None
            if settings_path is None
            else QSettings(str(settings_path), QSettings.Format.IniFormat)
        )
        # Language is applied at construction (restart to change); default English.
        set_language("en" if self._settings is None else self._settings.value(SETTINGS_KEY, "en"))
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
        self.recovery_items: tuple[RecoveryItem, ...] = ()
        self.recovery_dialog: RecoveryDialog | None = None
        self.portability_dialog: QMessageBox | None = None
        self.error_dialog: QMessageBox | None = None
        self._restored_geometry = DEFAULT_GEOMETRY
        self._recovery_project: str | None = None
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(AUTOSAVE_DELAY_MS)
        self.autosave_timer.timeout.connect(self.autosave_draft)
        self.save_indicator = QLabel("")
        self.save_indicator.setObjectName("packlab.status.save")
        self.statusBar().addPermanentWidget(self.save_indicator)
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
        self._fallback_design_export = design_model_export_source_provider
        self.route_stack = RouteStack(
            design_workbench=self.design_workbench,
            ingest_controller=ingest_controller,
            receiver=receiver,
            receiver_session_factory=receiver_session_factory,
            project_manager=self.project_manager,
            packaging_library_service=packaging_library_service,
            design_model_export_source_provider=self._design_export_source,
            export_destination_provider=export_destination_provider,
            job_manager=self.job_manager,
        )
        self._default_project_root = (
            None if default_project_root is None else Path(default_project_root)
        )
        self.build_model = BuildModelController(
            self.job_manager, self.project_manager, backend=build_backend
        )
        self._wire_build_model()
        measure = self.route_stack.views[Route.MEASURE_DESIGN]
        if self.scan_master_request_provider is None and isinstance(measure, MeasureDesignView):
            # Editor > Promote uses the cleaned object selection from Measure & Design.
            self.scan_master_request_provider = measure.promotion_request
            measure.draft_changed.connect(self._on_draft_changed)
            measure.draft_saved.connect(self._on_draft_saved)
        editor = self.route_stack.views[Route.EDITOR]
        if isinstance(editor, ScanMasterEditorView):
            editor.promotion_requested.connect(self._promote_scan_master_from_editor)
        families = self.route_stack.views[Route.PACKAGE_FAMILIES]
        if isinstance(families, PackageFamiliesView):
            families.export_requested.connect(self._export_family_part)
            # A Design Model opened for Labels takes the Exports page back from the family.
            self.design_workbench.changed.connect(families.yield_export)
        self.navigation_panel.route_requested.connect(self.navigation.navigate)
        self.page_header = PageHeader()
        self.page_header.show_route(self.navigation.current_route)
        self.route_stack.show_route(self.navigation.current_route)
        self.navigation.route_changed.connect(
            lambda value: self.route_stack.show_route(Route(value))
        )
        self.navigation.route_changed.connect(
            lambda value: self.page_header.show_route(Route(value))
        )
        self.navigation.route_changed.connect(
            lambda value: self.navigation_panel.select_route(Route(value))
        )
        splitter = QSplitter(self)
        splitter.setObjectName("packlab.main.splitter")
        page = QWidget(splitter)
        page.setObjectName("packlab.page")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(self.page_header)
        # F14: a tall page scrolls instead of pushing the Jobs dock out of the window.
        self.route_scroll = QScrollArea(page)
        self.route_scroll.setObjectName("packlab.page.scroll")
        self.route_scroll.setWidgetResizable(True)
        self.route_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.route_scroll.setWidget(self.route_stack)
        page_layout.addWidget(self.route_scroll, 1)
        splitter.addWidget(self.navigation_panel)
        splitter.addWidget(page)
        splitter.setCollapsible(0, False)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([self.navigation_panel.minimumWidth(), 10_000])
        self.setCentralWidget(splitter)
        install_design_workbench(self)
        self.workspace = WorkspaceManager(self, job_manager=self.job_manager)
        self._wire_scene_panel()
        self.navigation.set_project_context(self.project_manager)
        self._sync_project_state()
        self._restore_preferences()
        self._build_menus()
        translate_widget_tree(self)  # static texts; no-op in English
        if self._default_project_root is not None:
            self.ensure_project()

    # ------------------------------------------------------------- menus (PL-0454/0455)

    MAX_RECENT_PROJECTS = 8

    def _build_menus(self) -> None:
        # Injectable choosers keep the menu actions testable offscreen.
        self.choose_new_project_path: Callable[[], str] = lambda: QFileDialog.getSaveFileName(
            self, "New project folder", str(self.dialog_folder()), "PackLab project folder (*)"
        )[0]
        self.choose_open_project_path: Callable[[], str] = lambda: QFileDialog.getExistingDirectory(
            self, "Open PackLab project", str(self.dialog_folder())
        )
        file_menu = self.menuBar().addMenu("&File")
        file_menu.setObjectName("packlab.menu.file")
        self.new_project_action = file_menu.addAction("&New Project…", self._new_project_from_menu)
        self.open_project_action = file_menu.addAction(
            "&Open Project…", self._open_project_from_menu
        )
        self.recent_menu = file_menu.addMenu("Open &Recent")
        self.recent_menu.setToolTipsVisible(True)
        self.close_project_action = file_menu.addAction(
            "&Close Project", self._close_project_from_menu
        )
        file_menu.addSeparator()
        self.portability_action = file_menu.addAction(
            "&Portability report…", self.show_portability_report
        )
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.setObjectName("packlab.menu.edit")
        self.undo_action = edit_menu.addAction("&Undo selection", self.undo)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.redo_action = edit_menu.addAction("&Redo selection", self.redo)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        view_menu = self.menuBar().addMenu("&View")
        view_menu.setObjectName("packlab.menu.view")
        for dock in self.workspace.docks.values():
            view_menu.addAction(dock.toggleViewAction())
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.setObjectName("packlab.menu.help")
        self.diagnostic_bundle_action = help_menu.addAction(
            "Create &diagnostic bundle", self._diagnostic_bundle_from_menu
        )
        language_menu = help_menu.addMenu("&Language")
        language_menu.setObjectName("packlab.menu.language")
        group = QActionGroup(self)
        self.language_actions = {}
        settings_view = self.route_stack.views[Route.SETTINGS]
        assert isinstance(settings_view, SettingsView)
        for code, name in LANGUAGES.items():
            action = language_menu.addAction(name, partial(self.set_ui_language, code))
            action.setCheckable(True)
            action.setChecked(settings_view.language.currentData() == code)
            group.addAction(action)
            self.language_actions[code] = action
        settings_view.language.activated.connect(
            lambda index: self.set_ui_language(str(settings_view.language.itemData(index)))
        )
        self.project_manager.add_listener(lambda _metadata: self._refresh_project_menu())
        self._refresh_project_menu()

    def set_ui_language(self, code: str) -> None:
        """Persist the UI language; it is applied on the next start (PL-0464)."""
        if code not in LANGUAGES:
            return
        if self._settings is not None:
            self._settings.setValue(SETTINGS_KEY, code)
        settings_view = self.route_stack.views[Route.SETTINGS]
        if isinstance(settings_view, SettingsView):
            settings_view.language.setCurrentIndex(settings_view.language.findData(code))
            # Shown in both languages: the current UI may not be the chosen one.
            settings_view.language_note.setText(
                "Language changes apply after restarting PackLab Studio.\n"
                "Dil değişikliği PackLab Studio yeniden başlatıldığında uygulanır."
            )
        self.language_actions[code].setChecked(True)
        self._menu_status(tr("Language changes apply after restarting PackLab Studio."))

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
        self.portability_action.setEnabled(layout is not None)
        self.undo_action.setEnabled(self.project_manager.can_undo())
        self.redo_action.setEnabled(self.project_manager.can_redo())
        self.recent_menu.clear()
        for item in self.recent_projects():
            action = self.recent_menu.addAction(project_display_name(item))
            action.setToolTip(item)
            action.setStatusTip(item)
            action.triggered.connect(partial(self._open_project_path, item))
        self.recent_menu.setEnabled(not self.recent_menu.isEmpty())
        name = None if self.project_manager.current is None else self.project_manager.current.name
        # "[*]" shows "*" while the Design Model has unsaved (autosaved-only) edits.
        self.setWindowTitle(f"PackLab Studio — {name}[*]" if name else "PackLab Studio[*]")

    def _menu_status(self, text: str) -> None:
        self.statusBar().showMessage(text, 15000)

    def dialog_folder(self) -> Path:
        """Start folder for project dialogs: beside the open project, the last used folder,
        else Documents/PackLab; never the bare user home with its dot-folders (F15)."""

        layout = self.project_manager.layout
        if layout is not None:
            return layout.root.parent
        if self._settings is not None:
            last = str(self._settings.value("dialogs/last_folder", "") or "")
            if last and Path(last).is_dir():
                return Path(last)
        return documents_folder()

    def _remember_folder(self, chosen: str) -> None:
        if self._settings is not None:
            self._settings.setValue("dialogs/last_folder", str(Path(chosen).parent))

    def show_error(self, title: str, reason: str, next_step: str) -> QMessageBox:
        """A visible, non-blocking error with the reason and what to do next (F4)."""

        box = QMessageBox(self)
        box.setObjectName("packlab.dialog.error")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(title)
        box.setText(reason)
        box.setInformativeText(next_step)
        box.open()
        self.error_dialog = box
        return box

    def _new_project_from_menu(self) -> None:
        chosen = self.choose_new_project_path()
        if not chosen:
            return
        self._remember_folder(chosen)
        try:
            self.new_project(chosen, Path(chosen).name)
            self._menu_status(tr("Created project {path}").format(path=chosen))
        except Exception as error:
            self._menu_status(tr("New project failed: {error}").format(error=error))
            self.show_error(
                "New project failed",
                f"PackLab could not create a project in\n{chosen}\n\nReason: {error}",
                "Choose an empty folder you can write to, for example Documents\\PackLab.",
            )

    def _open_project_from_menu(self) -> None:
        chosen = self.choose_open_project_path()
        if chosen:
            self._remember_folder(chosen)
            self._open_project_path(chosen)

    def _open_project_path(self, path: str) -> None:
        try:
            self.open_project(path)
            self._menu_status(tr("Opened project {path}").format(path=path))
        except Exception as error:
            self._menu_status(tr("Open project failed: {error}").format(error=error))
            self.show_error(
                "Project could not be opened",
                f"PackLab could not open\n{path}\n\nReason: {error}",
                _OPEN_PROJECT_HELP,
            )

    def _close_project_from_menu(self) -> None:
        try:
            self.close_project()
            self._menu_status(tr("Project closed"))
        except Exception as error:  # e.g. a build is still running
            self._menu_status(tr("Close project failed: {error}").format(error=error))

    # ------------------------------------------------- history, autosave, recovery (PL-0456)

    def undo(self) -> Operation | None:
        return self._history_step(self.project_manager.undo, "Undo")

    def redo(self) -> Operation | None:
        return self._history_step(self.project_manager.redo, "Redo")

    def _history_step(self, step: Callable[[], Operation | None], label: str) -> Operation | None:
        try:
            operation = step()
        except Exception as error:
            self._menu_status(f"{label} failed: {error}")
            operation = None
        else:
            if operation is None:
                self._menu_status(f"Nothing to {label.lower()}.")
            else:
                parameters = operation.parameters
                undone = label == "Undo"
                target = parameters.get("before" if undone else "after")
                what = _POINTER_LABELS.get(str(parameters.get("pointer")), "selection")
                self._menu_status(f"{label}: current {what} is now {target or 'none'}")
        self._refresh_project_menu()
        return operation

    def _on_draft_changed(self) -> None:
        self.setWindowModified(True)
        self.save_indicator.setText(tr("Design Model: unsaved edits (autosave pending)"))
        self.autosave_timer.start()

    def autosave_draft(self) -> bool:
        """Write the unsaved Design Model draft to temp/ and checkpoint it for crash recovery."""

        measure = self.route_stack.views[Route.MEASURE_DESIGN]
        layout, recovery = self.project_manager.layout, self.project_manager.recovery
        draft = measure.draft() if isinstance(measure, MeasureDesignView) else None
        if draft is None or layout is None or recovery is None:
            return False
        try:
            target = layout.path("temp", AUTOSAVE_DRAFT_PATH)
            target.parent.mkdir(parents=True, exist_ok=True)
            ProjectManager._atomic_json(target, draft)
            recovery.checkpoint(
                AUTOSAVE_DRAFT_JOB, area="temp", relative_path=AUTOSAVE_DRAFT_PATH, resumable=True
            )
        except (OSError, ValueError) as error:
            self.save_indicator.setText(f"Autosave failed: {error}")
            return False
        self.save_indicator.setText(
            f"Design Model: unsaved edits autosaved {datetime.now():%H:%M:%S} "
            "(Save revision to keep them)"
        )
        return True

    def _on_draft_saved(self) -> None:
        self.autosave_timer.stop()
        self.setWindowModified(False)
        if self.project_manager.recovery is not None:
            self.project_manager.recovery.discard(AUTOSAVE_DRAFT_JOB)  # draft is superseded
        self.save_indicator.setText(tr("All changes saved"))

    def show_recovery_dialog(self) -> RecoveryDialog | None:
        if not self.recovery_items:
            return None
        self.recovery_dialog = RecoveryDialog(self)
        self.recovery_dialog.show()
        return self.recovery_dialog

    def show_portability_report(self) -> QMessageBox | None:
        try:
            report = self.project_manager.portability_report()
        except Exception as error:
            self._menu_status(f"Portability report failed: {error}")
            return None
        counts = Counter(item.classification.value for item in report.findings)
        missing = [
            item.reference_id
            for item in report.findings
            if item.classification.value in {"required-missing", "unsafe-link"}
        ]
        box = QMessageBox(self)
        box.setObjectName("packlab.dialog.portability")
        box.setWindowTitle("Portability report")
        box.setText(
            "This project is portable: everything it needs is inside the project folder."
            if report.portable
            else "This project is NOT portable: see the missing or unsafe items below."
        )
        lines = [f"{name}: {count}" for name, count in sorted(counts.items())]
        lines += [f"integrity {name}: {value}" for name, value in sorted(report.integrity.items())]
        lines += [f"raw evidence files: {report.raw_file_count}"]
        lines += [f"missing/unsafe: {item}" for item in missing[:10]]
        box.setInformativeText("\n".join(lines))
        box.setDetailedText(json.dumps(report.to_dict(), indent=1))
        box.open()
        self.portability_dialog = box
        return box

    def _diagnostic_bundle_from_menu(self) -> None:
        try:
            bundle = self.create_diagnostic_bundle()
            self._menu_status(tr("Diagnostic bundle written: {path}").format(path=bundle.path))
        except Exception as error:
            self._menu_status(tr("Diagnostic bundle failed: {error}").format(error=error))

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
            stored_limit = self._settings.value("build/max_concurrent", 2)
            try:
                settings.concurrent_builds.setValue(int(str(stored_limit)))
            except (TypeError, ValueError):
                pass  # keep the default
            settings.concurrent_builds.valueChanged.connect(
                lambda value: (
                    self._settings.setValue("build/max_concurrent", value)
                    if self._settings is not None
                    else None
                )
            )
            stored_quality = self._settings.value("build/quality", "fast")
            index = settings.build_quality.findData(str(stored_quality))
            if index >= 0:
                settings.build_quality.setCurrentIndex(index)
            settings.build_quality.currentIndexChanged.connect(
                lambda _index: (
                    self._settings.setValue("build/quality", settings.build_quality.currentData())
                    if self._settings is not None
                    else None
                )
            )
        self.build_model.set_max_concurrent(settings.concurrent_builds.value())
        self.build_model.set_quality(settings.build_quality.currentData())
        settings.build_quality.currentIndexChanged.connect(
            lambda _index: self.build_model.set_quality(settings.build_quality.currentData())
        )
        settings.concurrent_builds.valueChanged.connect(self.build_model.set_max_concurrent)
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
        builds.build_requested.connect(self.start_build)
        self.build_model.build_started.connect(lambda *_args: self.refresh_builds())
        self.build_model.build_finished.connect(lambda *_args: self.refresh_builds())
        self.navigation.route_changed.connect(
            lambda value: self.refresh_builds() if value == Route.RECONSTRUCTION.value else None
        )
        mask = self.route_stack.views[Route.MASK_CORRECTION]
        if isinstance(mask, MaskCorrectionView):
            mask.route_requested.connect(self.navigation.navigate)
        measure = self.route_stack.views[Route.MEASURE_DESIGN]
        if isinstance(measure, MeasureDesignView):
            # Next-step buttons hand the just-built model to Measure & Design, but never
            # replace a model the owner already has open there (it vanished on return).
            builds.route_requested.connect(
                lambda value: (
                    measure.use_latest_build(
                        None if builds.result is None else builds.result.model_path
                    )
                    if value == Route.MEASURE_DESIGN.value and measure.model is None
                    else None
                )
            )

    def _wire_scene_panel(self) -> None:
        """PL-0485: Scene / Objects lists the project's parts; selection drives the pages."""
        inbox = self.route_stack.views[Route.CAPTURE_INBOX]

        def entries() -> list:
            session = inbox.session if isinstance(inbox, CaptureInboxView) else None
            return [] if session is None else session.entries()

        self.scene_panel = ScenePanel(self.project_manager, self.job_manager, entries)
        dock = self.workspace.docks[DockId.SCENE]
        dock.setWidget(self.scene_panel)
        self.scene_panel.part_selected.connect(self._show_part)
        self.build_model.build_finished.connect(lambda *_args: self.scene_panel.refresh())
        measure = self.route_stack.views[Route.MEASURE_DESIGN]
        if isinstance(measure, MeasureDesignView):
            measure.part_provider = self.scene_panel.selected_cloud
        self._scene_project: str | None = None
        self.project_manager.add_listener(self._reveal_scene_panel)
        self.scene_panel.refresh()

    def _reveal_scene_panel(self, _metadata: object) -> None:
        """Opening a project that has part scans shows the Scene dock once."""
        layout = self.project_manager.layout
        root = None if layout is None else str(layout.root)
        if root == self._scene_project:
            return
        self._scene_project = root
        if any(state.status != "missing" for state in self.scene_panel.states.values()):
            self.workspace.docks[DockId.SCENE].show()

    def _show_part(self, part: object, paths: tuple[Path, ...]) -> None:
        viewer = self.route_stack.views[Route.MODEL_VIEWER]
        measure = self.route_stack.views[Route.MEASURE_DESIGN]
        if isinstance(measure, MeasureDesignView):
            label = None if part is None else tr(str(part).capitalize())
            measure.part_key = None if part is None else str(part)
            measure.show_part(label, self.scene_panel.selected_cloud() is not None)
        labels = self.route_stack.views[Route.LABELS]
        if isinstance(labels, LabelsView):
            labels.placement_provider = lambda: self.scene_panel.placement
            labels.show_part(None if part is None else str(part))
        if isinstance(viewer, ModelViewerView) and paths:
            viewer.load(*paths, background=True)  # 2 x 2.5M-point clouds froze the UI

    def refresh_builds(self) -> None:
        """Scan list on the Build 3D Model page: inbox scans + this project's builds."""
        inbox = self.route_stack.views[Route.CAPTURE_INBOX]
        builds = self.route_stack.views[Route.RECONSTRUCTION]
        if not isinstance(inbox, CaptureInboxView) or not isinstance(builds, BuildModelView):
            return
        session = inbox.session
        try:
            entries = [] if session is None else session.entries()
        except Exception:  # unreadable inbox index: show an empty list, never crash
            entries = []
        layout = self.project_manager.layout
        try:
            roles = self.project_manager.scan_part_roles()
        except Exception:  # unreadable project state: manifest roles still show
            roles = {}
        builds.refresh_history(entries, None if layout is None else layout.root, roles)

    def resume_paired_receiver(self) -> None:
        """Pair once: a paired phone can send without the owner opening Capture Inbox.

        Called only from the real launch path (app.run), never for test/smoke windows.
        """
        inbox = self.route_stack.views[Route.CAPTURE_INBOX]
        if isinstance(inbox, CaptureInboxView):
            inbox.resume_for_paired_devices()

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
        except Exception as error:  # surfaced in the inbox and a dialog; Studio stays usable
            self._inbox_note(f"Default project unavailable: {error}")
            self.show_error(
                "Your scans project could not be opened",
                f"PackLab could not open its default project\n{root}\n\nReason: {error}",
                _OPEN_PROJECT_HELP,
            )
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
        saved = self.preferences.load()
        area = self._available_work_area or self._current_work_area(saved.geometry)
        if area is not None:
            ax, ay, aw, ah = area
            area = (
                ax + _FRAME_EDGE,
                ay + _FRAME_TOP,
                aw - 2 * _FRAME_EDGE,
                ah - _FRAME_TOP - _FRAME_EDGE,
            )
        self._restored_geometry = sanitize_geometry(saved.geometry, bounds=area)
        self.setGeometry(*self._restored_geometry)
        if saved.maximized:
            self.showMaximized()
        if saved.fullscreen:
            self.showFullScreen()
        if saved.dock_state:
            self.restoreState(QByteArray.fromBase64(saved.dock_state.encode("ascii")))
            self._redock_offscreen_docks()
            QTimer.singleShot(0, self._redock_offscreen_docks)  # geometry settles on show
        try:
            self.navigation.navigate(Route(saved.last_route))
        except ValueError:
            self.navigation.navigate(Route.LIBRARY)
        self.navigation_panel.select_route(self.navigation.current_route)

    def _redock_offscreen_docks(self) -> None:
        """A saved floating dock that is not fully on a screen is docked again (PL-0464)."""
        screens = [screen.availableGeometry() for screen in QGuiApplication.screens()]
        for dock in self.workspace.docks.values():
            if dock.isFloating() and not any(
                area.contains(dock.frameGeometry()) for area in screens
            ):
                dock.setFloating(False)

    def _current_work_area(
        self, geometry: tuple[int, int, int, int]
    ) -> tuple[int, int, int, int] | None:
        """Available area of the screen holding the saved window centre, else the primary one.

        One screen, not the union bounding box: in mixed multi-monitor layouts the union
        contains regions no screen shows, which put title bars off-screen (F5)."""

        x, y, width, height = geometry
        screen = QGuiApplication.screenAt(QPoint(x + width // 2, y + height // 2))
        screen = screen or QGuiApplication.primaryScreen()
        if screen is None:
            return None
        rect = screen.availableGeometry()
        return rect.x(), rect.y(), rect.width(), rect.height()

    def _design_export_source(self) -> DesignModelExportSource | None:
        """Exports page Design Model: the active package-family part, else the fallback."""

        families = self.route_stack.views.get(Route.PACKAGE_FAMILIES)
        if isinstance(families, PackageFamiliesView):
            source = families.export_source()
            if source is not None:
                return source
        fallback = self._fallback_design_export
        return None if fallback is None else fallback()

    def _export_family_part(self) -> None:
        export_view = self.route_stack.views[Route.EXPORTS]
        self.navigation.navigate(Route.EXPORTS)
        if isinstance(export_view, EngineeringExportView):
            index = export_view.source_selector.findData(ExportSourceKind.DESIGN_MODEL.value)
            export_view.source_selector.setCurrentIndex(index)
            export_view.refresh_source()

    def _on_project_changed(self, _metadata: object) -> None:
        self._sync_project_state()

    def _sync_project_state(self) -> None:
        available = self.project_manager.current is not None
        self.recovery = self.project_manager.recovery
        self.recovery_items = self.project_manager.recovery_items
        layout = self.project_manager.layout
        root = None if layout is None else str(layout.root)
        if root != self._recovery_project:  # project opened, switched or closed
            self._recovery_project = root
            self.autosave_timer.stop()
            self.setWindowModified(False)
            self.save_indicator.setText("")
            if self.recovery_items:
                QTimer.singleShot(0, self.show_recovery_dialog)
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
        draft = None
        layout = self.project_manager.layout
        if item_id == AUTOSAVE_DRAFT_JOB and layout is not None:
            try:  # read before accepting; accept keeps the file, discard deletes it
                draft = json.loads(layout.path("temp", AUTOSAVE_DRAFT_PATH).read_text("utf-8"))
            except (OSError, ValueError):
                draft = None
        item = self.project_manager.accept_recovery(item_id)
        self._sync_project_state()
        measure = self.route_stack.views[Route.MEASURE_DESIGN]
        if (
            item is not None
            and item.status is RecoveryStatus.RESUMABLE  # digest still matches the checkpoint
            and isinstance(draft, dict)
            and isinstance(measure, MeasureDesignView)
        ):
            self.navigation.navigate(Route.MEASURE_DESIGN)
            measure.restore_draft(draft)
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
            # Normal (un-maximized) client geometry: x()/y() are the frame origin and drifted
            # the window up by a title bar each restart; the maximized size is no restore size.
            normal = (
                self.normalGeometry()
                if self.isMaximized() or self.isFullScreen()
                else self.geometry()
            )
            geometry = (
                (normal.x(), normal.y(), normal.width(), normal.height())
                if normal.isValid()  # invalid when maximized before the first show
                else self._restored_geometry
            )
            self.preferences.save(
                WindowPreferences(
                    geometry=geometry,
                    maximized=self.isMaximized(),
                    fullscreen=self.isFullScreen(),
                    dock_state=state,
                    last_route=self.navigation.current_route.value,
                )
            )
        super().closeEvent(event)

    def _finish_shutdown(self, _result: object) -> None:
        self.close()
