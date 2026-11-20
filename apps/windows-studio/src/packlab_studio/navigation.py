"""Stable Studio routes and the single-window navigation seam."""

from __future__ import annotations

import subprocess
import tempfile
import threading
from collections.abc import Callable, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
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

from .build_model import SUPPORTED_COLMAP_VERSIONS, BuildModelView
from .capture_inbox import CaptureInboxView
from .engine_config import discover_engines
from .engineering_export import EngineeringExportView
from .mask_correction import MaskCorrectionView
from .measure_view import MeasureDesignView
from .model_viewer import ModelViewerView
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
        form = QFormLayout()
        form.addRow("Actor", self.actor_input)
        form.addRow("Promotion reason", self.reason_input)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.promote_button)
        layout.addWidget(self.authority_status)
        layout.addWidget(self.status)
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
        if (
            probe
            and record.executable is not None
            and record.engine_id
            in {
                "colmap",
                "openmvs.interface_colmap",
            }
        ):
            try:
                result = (
                    probe_colmap(record.executable, runner=_probe_runner)
                    if record.engine_id == "colmap"
                    else probe_openmvs(record.executable, runner=_probe_runner)
                )
                version = result.version.text if result.version else "unknown"
                line += f" | version {version} ({result.status.value})"
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
        self.engines = QListWidget(self)
        self.engines.setObjectName("packlab.settings.engines")
        self.recheck_button = QPushButton("Re-check engines", self)
        self.recheck_button.setObjectName("packlab.settings.engines-recheck")
        self.recheck_button.clicked.connect(self.recheck_engines)
        self._engine_rows_ready.connect(self._show_engine_rows)
        layout = QVBoxLayout(self)
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
        self.recheck_button.setText("Checking engines…")
        threading.Thread(
            target=lambda: self._engine_rows_ready.emit(engine_rows(probe=True)),
            name="packlab-engine-probe",
            daemon=True,
        ).start()

    def _show_engine_rows(self, rows: list[str]) -> None:
        self.engines.clear()
        self.engines.addItems(rows)
        self.recheck_button.setEnabled(True)
        self.recheck_button.setText("Re-check engines")


# Routes that need an open project. Navigation and view gating both read this set.
PROJECT_ROUTES = frozenset(
    {Route.RECONSTRUCTION, Route.EDITOR, Route.MASK_CORRECTION, Route.EXPORTS}
)


class NavigationPanel(QWidget):
    route_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("packlab.navigation.panel")
        self.list = QListWidget(self)
        self.list.setObjectName("packlab.navigation.routes")
        for route in Route:
            item = QListWidgetItem(route.name.replace("_", " ").title())
            item.setData(0x0100, route.value)
            self.list.addItem(item)
        self.list.currentItemChanged.connect(self._on_item_changed)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)

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

# One widget factory per route; each receives the RouteStack keyword services (missing
# services are None). New routes: add a Route member and one entry here.
ROUTE_FACTORIES: dict[Route, RouteFactory] = {
    Route.LIBRARY: lambda s: PackagingLibraryBrowserView(s.get("packaging_library_service")),
    Route.CAPTURE_INBOX: lambda s: CaptureInboxView(
        ingest_controller=s.get("ingest_controller"),
        receiver=s.get("receiver"),
        session_factory=s.get("receiver_session_factory"),
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
        self.setCurrentWidget(self.views[route])

    def set_project_available(self, available: bool) -> None:
        for route in PROJECT_ROUTES:
            self.views[route].setEnabled(available)
        export_view = self.views[Route.EXPORTS]
        if isinstance(export_view, EngineeringExportView):
            export_view.refresh_source()
