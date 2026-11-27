"""Stable Studio routes and the single-window navigation seam."""

from __future__ import annotations

import subprocess
import tempfile
import threading
from collections.abc import Callable, Sequence
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QSize, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from packlab_core.engine_probe import (
    COLMAP_PROBE_POLICY,
    EngineId,
    EngineProbeStatus,
    parse_colmap_version,
    probe_engine,
    probe_openmvs,
)
from packlab_core.subprocess_runner import NO_WINDOW

from .build_model import SUPPORTED_COLMAP_VERSIONS, BuildModelView
from .capture_inbox import CaptureInboxView
from .design_workbench import DesignWorkbench
from .engine_config import discover_engines
from .engineering_export import EngineeringExportView
from .i18n import LANGUAGES, language, tr
from .labels_view import LabelsView
from .mask_correction import MaskCorrectionView
from .measure_view import MeasureDesignView
from .model_viewer import ModelViewerView
from .package_families_view import PackageFamiliesView
from .packaging_library_browser import PackagingLibraryBrowserView
from .version import AboutView


class Route(StrEnum):
    LIBRARY = "library"
    CAPTURE_INBOX = "capture-inbox"
    RECONSTRUCTION = "reconstruction"
    EDITOR = "editor"
    MASK_CORRECTION = "mask-correction"
    EXPORTS = "exports"
    SETTINGS = "settings"
    MODEL_VIEWER = "model-viewer"
    MEASURE_DESIGN = "measure-design"
    LABELS = "labels"
    PACKAGE_FAMILIES = "package-families"


# Navigation label / page title, one-line plain-language description, standard Qt icon.
ROUTE_TEXT: dict[Route, tuple[str, str, QStyle.StandardPixmap]] = {
    Route.LIBRARY: (
        "Packaging Library",
        "Browse, search and manage your saved packaging designs (SKUs).",
        QStyle.StandardPixmap.SP_DirHomeIcon,
    ),
    Route.CAPTURE_INBOX: (
        "Capture Inbox",
        "Receive scans from the iPhone or import a .packscan file.",
        QStyle.StandardPixmap.SP_ArrowDown,
    ),
    Route.RECONSTRUCTION: (
        "Build 3D Model",
        "Turn the photos of an imported scan into a 3D model (COLMAP / OpenMVS).",
        QStyle.StandardPixmap.SP_MediaPlay,
    ),
    Route.EDITOR: (
        "Scan Master",
        "Promote a cleaned scan to Scan Master, the measured reference copy of the real object.",
        QStyle.StandardPixmap.SP_DialogApplyButton,
    ),
    Route.MASK_CORRECTION: (
        "Mask Correction",
        "Fix the object outline in a photo by painting or erasing pixels.",
        QStyle.StandardPixmap.SP_DialogResetButton,
    ),
    Route.EXPORTS: (
        "Exports",
        "Save the Scan Master or Design Model as engineering files.",
        QStyle.StandardPixmap.SP_DialogSaveButton,
    ),
    Route.SETTINGS: (
        "Settings",
        "Language, automatic model building, reconstruction engines and version details.",
        QStyle.StandardPixmap.SP_FileDialogDetailedView,
    ),
    Route.MODEL_VIEWER: (
        "Model Viewer",
        "Look at a built 3D model: drag to rotate, right-drag to pan, wheel to zoom.",
        QStyle.StandardPixmap.SP_DesktopIcon,
    ),
    Route.MEASURE_DESIGN: (
        "Measure & Design",
        "Isolate the object, set real-world scale, measure it and create a Design Model.",
        QStyle.StandardPixmap.SP_FileDialogContentsView,
    ),
    Route.LABELS: (
        "Labels",
        "Place label zones and artwork on the Design Model and render mockups.",
        QStyle.StandardPixmap.SP_FileIcon,
    ),
    Route.PACKAGE_FAMILIES: (
        "Package Families",
        "Create size and closure variants from parametric package family templates.",
        QStyle.StandardPixmap.SP_DirIcon,
    ),
}


class PageHeader(QWidget):
    """Title and one-line description of the open page, above the route stack."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("packlab.page.header")
        self.title = QLabel(self)
        self.title.setObjectName("packlab.page.title")
        font = QFont(self.title.font())
        font.setPointSizeF(font.pointSizeF() * 1.5)
        font.setBold(True)
        self.title.setFont(font)
        self.description = QLabel(self)
        self.description.setObjectName("packlab.page.description")
        self.description.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 4)
        layout.addWidget(self.title)
        layout.addWidget(self.description)

    def show_route(self, route: Route) -> None:
        title, description, _icon = ROUTE_TEXT[route]
        self.title.setText(tr(title))
        self.description.setText(tr(description))


class NavigationError(ValueError):
    pass


class NavigationController(QObject):
    route_changed = Signal(str)
    project_changed = Signal(object)

    def __init__(self, *, initial_route: Route = Route.LIBRARY) -> None:
        super().__init__()
        self._route = Route(initial_route)
        self._project_context: Any = None

    @property
    def current_route(self) -> Route:
        return self._route

    @property
    def project_context(self) -> Any:
        return self._project_context

    def navigate(self, route: Route | str) -> Route:
        try:
            target = Route(route)
        except ValueError as error:
            raise NavigationError(f"unknown Studio route: {route}") from error
        if target != self._route:
            self._route = target
            self.route_changed.emit(target.value)
        return target

    def set_project_context(self, context: Any) -> None:
        self._project_context = context
        self.project_changed.emit(context)


class ScanMasterEditorView(QWidget):
    """Studio action surface; all authority and eligibility checks stay in core."""

    promotion_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("packlab.view.editor")
        self.actor_input = QLineEdit(self)
        self.actor_input.setObjectName("packlab.scan-master.actor")
        self.reason_input = QLineEdit(self)
        self.reason_input.setObjectName("packlab.scan-master.reason")
        self.promote_button = QPushButton("Promote to Scan Master", self)
        self.promote_button.setObjectName("packlab.scan-master.promote")
        self.authority_status = QLabel(
            "Before physical validation: DEFERRED_OWNER_VALIDATION; inherited scale state; "
            "mold_use_authorized=false.",
            self,
        )
        self.authority_status.setObjectName("packlab.scan-master.authority-status")
        self.status = QLabel("No promotion requested.", self)
        self.status.setObjectName("packlab.scan-master.status")
        # F13: one compact, explained card instead of full-width fields on an empty page.
        self.authority_status.setWordWrap(True)
        self.status.setWordWrap(True)
        self.actor_input.setPlaceholderText("e.g. your name")
        self.reason_input.setPlaceholderText("e.g. Cleaned jar scan, scale checked on the mat")
        intro = QLabel(
            "Scan Master is the official measured copy of the real object that later "
            "designs refer to. Promote the cleaned object you selected in Measure & Design. "
            "Your name and reason are stored in the audit history.",
            self,
        )
        intro.setWordWrap(True)
        plain = QLabel(
            "In plain words: the dimensions are not yet confirmed on the physical object and "
            "the model must not be used to make moulds.",
            self,
        )
        plain.setWordWrap(True)
        form = QFormLayout()
        form.addRow("Your name", self.actor_input)
        form.addRow("Reason", self.reason_input)
        button_row = QHBoxLayout()
        button_row.addWidget(self.promote_button)
        button_row.addStretch(1)
        card = QGroupBox("Promote to Scan Master", self)
        card.setMaximumWidth(760)
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(intro)
        card_layout.addLayout(form)
        card_layout.addLayout(button_row)
        card_layout.addWidget(self.authority_status)
        card_layout.addWidget(plain)
        card_layout.addWidget(self.status)
        layout = QVBoxLayout(self)
        layout.addWidget(card)
        layout.addStretch(1)
        self.promote_button.clicked.connect(self._request_promotion)

    def _request_promotion(self) -> None:
        actor = self.actor_input.text().strip()
        reason = self.reason_input.text().strip()
        if not actor or not reason:
            self.status.setText("Promotion requires an actor and reason.")
            return
        self.promotion_requested.emit(actor, reason)

    def set_promotion_status(self, text: str) -> None:
        self.status.setText(text)


def _probe_runner(executable: Path, arguments: Sequence[str]) -> tuple[int, str, str]:
    # OpenMVS prints its banner only to a log file in its working directory when not on a
    # console: run it in a scratch folder and read that log back.
    with tempfile.TemporaryDirectory(prefix="packlab-probe-") as scratch:
        completed = subprocess.run(
            [str(executable), *arguments],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=5.0,
            creationflags=NO_WINDOW,
            cwd=scratch,
        )
        stdout = completed.stdout or "".join(
            log.read_text(encoding="utf-8", errors="replace")
            for log in sorted(Path(scratch).glob("*.log"))
        )
    return completed.returncode, stdout[:4096], (completed.stderr or "")[:4096]


def probe_colmap(executable: Path, *, runner: Any = None) -> Any:
    """Probe against the versions the Build model command plan can drive (4.x options)."""
    return probe_engine(
        EngineId.COLMAP,
        executable,
        parse_colmap_version,
        supported_versions=SUPPORTED_COLMAP_VERSIONS,
        policy=COLMAP_PROBE_POLICY,
        runner=runner or _probe_runner,
    )


def engine_rows(*, probe: bool = False) -> list[str]:
    """One line per discovered engine executable: status, source, path, optional version."""
    rows: list[str] = []
    for record in discover_engines().records:
        line = f"{record.engine_id}: {record.status.value} via {record.source}"
        line += (
            f" | {record.executable}" if record.executable is not None else f" | {record.detail}"
        )
        # Every OpenMVS tool prints the same "OpenMVS x64 vX.Y" banner on -h (F11).
        if probe and record.executable is not None:
            try:
                result = (
                    probe_colmap(record.executable, runner=_probe_runner)
                    if record.engine_id == "colmap"
                    else probe_openmvs(record.executable, runner=_probe_runner)
                )
                if result.version is None:
                    line += f" | version not reported ({result.status.value})"
                else:
                    line += f" | version {result.version.text} ({result.status.value})"
                if record.engine_id == "colmap" and result.status is EngineProbeStatus.UNSUPPORTED:
                    line += " | Build model needs COLMAP " + ", ".join(SUPPORTED_COLMAP_VERSIONS)
            except Exception as error:  # a broken engine must not break Settings
                line += f" | probe failed: {type(error).__name__}"
        rows.append(line)
    return rows


class SettingsView(QWidget):
    """Settings route: Studio options, reconstruction engines, version/about details."""

    _engine_rows_ready = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("packlab.view.settings")
        self.auto_build = QCheckBox("Build model automatically after import", self)
        self.auto_build.setObjectName("packlab.settings.auto-build")
        self.auto_build.setChecked(True)
        self.concurrent_builds = QSpinBox(self)
        self.concurrent_builds.setObjectName("packlab.settings.concurrent-builds")
        self.concurrent_builds.setRange(1, 4)
        self.concurrent_builds.setValue(2)
        self.engines = QListWidget(self)
        self.engines.setObjectName("packlab.settings.engines")
        self.recheck_button = QPushButton("Re-check engines", self)
        self.recheck_button.setObjectName("packlab.settings.engines-recheck")
        self.recheck_button.clicked.connect(self.recheck_engines)
        self._engine_rows_ready.connect(self._show_engine_rows)
        self.language = QComboBox(self)
        self.language.setObjectName("packlab.settings.language")
        for code, name in LANGUAGES.items():
            self.language.addItem(name, code)
        self.language.setCurrentIndex(self.language.findData(language()))
        self.language_note = QLabel("", self)
        self.language_note.setObjectName("packlab.settings.language-note")
        language_form = QFormLayout()
        language_form.addRow(tr("Language"), self.language)
        language_form.addRow(self.language_note)
        language_form.addRow("Model builds at the same time", self.concurrent_builds)
        layout = QVBoxLayout(self)
        layout.addLayout(language_form)
        layout.addWidget(self.auto_build)
        layout.addWidget(QLabel("Reconstruction engines (COLMAP / OpenMVS)", self))
        layout.addWidget(self.engines)
        layout.addWidget(self.recheck_button)
        layout.addWidget(AboutView())
        layout.addStretch(1)
        self.refresh_engines()

    def refresh_engines(self) -> None:
        """Path discovery is cheap; version probes start the engines, so only on Re-check."""
        self._show_engine_rows(engine_rows())

    def recheck_engines(self) -> None:
        """Probe versions on a worker thread; the UI stays responsive meanwhile."""
        self.recheck_button.setEnabled(False)
        self.recheck_button.setText(tr("Checking engines…"))
        threading.Thread(
            target=lambda: self._engine_rows_ready.emit(engine_rows(probe=True)),
            name="packlab-engine-probe",
            daemon=True,
        ).start()

    def _show_engine_rows(self, rows: list[str]) -> None:
        self.engines.clear()
        self.engines.addItems(rows)
        self.recheck_button.setEnabled(True)
        self.recheck_button.setText(tr("Re-check engines"))


# Routes that need an open project. Navigation and view gating both read this set.
PROJECT_ROUTES = frozenset(
    {
        Route.RECONSTRUCTION,
        Route.EDITOR,
        Route.MASK_CORRECTION,
        Route.EXPORTS,
        Route.PACKAGE_FAMILIES,
    }
)


class NavigationPanel(QWidget):
    route_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("packlab.navigation.panel")
        self.list = QListWidget(self)
        self.list.setObjectName("packlab.navigation.routes")
        self.list.setIconSize(QSize(20, 20))
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.list.setSpacing(2)
        style = self.style()
        for route in Route:
            title, description, icon = ROUTE_TEXT[route]
            item = QListWidgetItem(style.standardIcon(icon), tr(title))
            item.setToolTip(tr(description))
            item.setData(0x0100, route.value)
            self.list.addItem(item)
        self.list.currentItemChanged.connect(self._on_item_changed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 0, 4)
        layout.addWidget(self.list)
        self.fit_to_labels()

    def fit_to_labels(self) -> None:
        """Wide enough for the longest label plus icon at the current font (no eliding)."""
        frame = 2 * self.list.frameWidth()
        scrollbar = self.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)
        width = self.list.sizeHintForColumn(0) + frame + scrollbar + 16
        self.list.setMinimumWidth(width)
        self.setMinimumWidth(width + 4)  # panel layout: 4 px left margin, 0 right

    def set_project_available(self, available: bool) -> None:
        # Capture Inbox is per-user, not per-project: it stays reachable without a project.
        gated = {route.value for route in PROJECT_ROUTES}
        for index in range(self.list.count()):
            item = self.list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) in gated:
                flags = item.flags()
                item.setFlags(
                    flags | Qt.ItemFlag.ItemIsEnabled
                    if available
                    else flags & ~Qt.ItemFlag.ItemIsEnabled
                )

    def select_route(self, route: Route) -> None:
        for index in range(self.list.count()):
            if self.list.item(index).data(0x0100) == route.value:
                self.list.setCurrentRow(index)
                return

    def _on_item_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is not None:
            self.route_requested.emit(str(current.data(0x0100)))


RouteFactory = Callable[[dict[str, Any]], QWidget]


def _project_root(project_manager: Any) -> Path | None:
    layout = getattr(project_manager, "layout", None)
    return layout.root if layout is not None else None


# One widget factory per route; each receives the RouteStack keyword services (missing
# services are None). New routes: add a Route member and one entry here.
ROUTE_FACTORIES: dict[Route, RouteFactory] = {
    Route.LIBRARY: lambda s: PackagingLibraryBrowserView(s.get("packaging_library_service")),
    Route.CAPTURE_INBOX: lambda s: CaptureInboxView(
        ingest_controller=s.get("ingest_controller"),
        receiver=s.get("receiver"),
        session_factory=s.get("receiver_session_factory"),
        project_manager=s.get("project_manager"),
    ),
    Route.RECONSTRUCTION: lambda s: BuildModelView(s.get("job_manager")),
    Route.EDITOR: lambda s: ScanMasterEditorView(),
    Route.MASK_CORRECTION: lambda s: MaskCorrectionView(),
    Route.EXPORTS: lambda s: EngineeringExportView(
        s.get("project_manager"),
        design_model_source_provider=s.get("design_model_export_source_provider"),
        destination_provider=s.get("export_destination_provider"),
    ),
    Route.SETTINGS: lambda s: SettingsView(),
    Route.MODEL_VIEWER: lambda s: ModelViewerView(),
    Route.MEASURE_DESIGN: lambda s: MeasureDesignView(s.get("project_manager")),
    Route.LABELS: lambda s: LabelsView(
        s.get("design_workbench") or DesignWorkbench(),
        job_manager=s.get("job_manager"),
        project_root=partial(_project_root, s.get("project_manager")),
        project_manager=s.get("project_manager"),
    ),
    Route.PACKAGE_FAMILIES: lambda s: PackageFamiliesView(s.get("project_manager")),
}


class RouteStack(QStackedWidget):
    def __init__(self, **services: Any) -> None:
        super().__init__()
        self.setObjectName("packlab.navigation.stack")
        self.services = services
        self.views: dict[Route, QWidget] = {}
        for route in Route:
            factory = ROUTE_FACTORIES.get(route)
            view: QWidget
            if factory is None:
                view = QLabel(route.name.replace("_", " ").title())
                view.setObjectName(f"packlab.view.{route.value}")
            else:
                view = factory(services)
            self.views[route] = view
            self.addWidget(view)

    def show_route(self, route: Route) -> None:
        # Only the visible page counts for the minimum size, so the surrounding scroll
        # area scrolls when *this* page needs it, not because of the tallest page.
        for key, view in self.views.items():
            policy = QSizePolicy.Policy.Preferred if key is route else QSizePolicy.Policy.Ignored
            view.setSizePolicy(policy, policy)
        self.setCurrentWidget(self.views[route])
        self.updateGeometry()

    # QStackedLayout answers height-for-width with the preferred height of *all* pages, so
    # the surrounding scroll area would scroll every page to the tallest one. Answer with
    # the visible page's minimum height: scrolling starts only when that page is cramped.
    def heightForWidth(self, _width: int) -> int:
        page = self.currentWidget()
        return -1 if page is None else page.minimumSizeHint().height()

    def set_project_available(self, available: bool) -> None:
        for route in PROJECT_ROUTES:
            self.views[route].setEnabled(available)
        export_view = self.views[Route.EXPORTS]
        if isinstance(export_view, EngineeringExportView):
            export_view.refresh_source()
