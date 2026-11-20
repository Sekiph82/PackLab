"""Labels route: label zones, artwork, dieline, material and Blender mockup (PL-0448)."""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QByteArray, QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from packlab_core.label_zone import LabelZoneBoundary, LabelZoneKind

from .design_workbench import (
    DESIGN_DOCUMENT_SUFFIX,
    DesignWorkbench,
    LabelZoneEntry,
    LabelZoneSuggestion,
    MockupJob,
    latest_project_design_model,
)
from .jobs import JobManager

if TYPE_CHECKING:
    from .shell import StudioMainWindow


def _text_error(error: Exception) -> str:
    return str(error) or type(error).__name__


class LabelsView(QWidget):
    """Owner surface over ``DesignWorkbench``; every button calls one core-backed action."""

    mockup_finished = Signal(object)

    def __init__(
        self,
        workbench: DesignWorkbench,
        *,
        job_manager: JobManager | None = None,
        project_root: Callable[[], Path | None] = lambda: None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("packlab.view.labels")
        self.workbench = workbench
        self.job_manager = job_manager
        self.project_root = project_root
        self.suggestion: LabelZoneSuggestion | None = None
        self.last_mockup: dict[str, object] | None = None
        self._render_thread: threading.Thread | None = None
        # Injectable choosers keep every action drivable offscreen.
        self.choose_design_model_path: Callable[[], str] = lambda: QFileDialog.getOpenFileName(
            self,
            "Open Design Model",
            str(self._start_folder()),
            f"PackLab Design Model (*{DESIGN_DOCUMENT_SUFFIX} *.json)",
        )[0]
        self.choose_artwork_path: Callable[[], str] = lambda: QFileDialog.getOpenFileName(
            self, "Import label artwork", str(self._start_folder()), "Artwork (*.svg *.png)"
        )[0]
        self.choose_directory: Callable[[str], str] = lambda title: (
            QFileDialog.getExistingDirectory(self, title, str(self._start_folder()))
        )

        self.model_summary = QLabel(workbench.summary(), self)
        self.model_summary.setObjectName("packlab.labels.model-summary")
        self.model_summary.setWordWrap(True)
        self.open_button = self._button("Open Design Model…", "open-design-model", self.open_model)
        self.project_model_button = self._button(
            "Use project Design Model", "use-project-design-model", self.use_project_model
        )
        model_box = QGroupBox("Design Model", self)
        model_layout = QVBoxLayout(model_box)
        model_layout.addWidget(self.model_summary)
        model_row = QHBoxLayout()
        model_row.addWidget(self.project_model_button)
        model_row.addWidget(self.open_button)
        model_layout.addLayout(model_row)

        self.kind = QComboBox(self)
        self.kind.setObjectName("packlab.labels.zone-kind")
        for kind in (LabelZoneKind.WRAP, LabelZoneKind.FRONT, LabelZoneKind.BACK):
            self.kind.addItem(kind.value.title(), kind.value)
        self.variant = QLineEdit(self)
        self.variant.setObjectName("packlab.labels.variant")
        self.variant.setPlaceholderText("variant name, e.g. front, back, wrap-v2")
        self.boundary: dict[str, QDoubleSpinBox] = {}
        boundary_row = QHBoxLayout()
        for name, value in (("u_min", 0.0), ("v_min", 0.1), ("u_max", 1.0), ("v_max", 0.9)):
            spin = QDoubleSpinBox(self)
            spin.setObjectName(f"packlab.labels.boundary.{name}")
            spin.setRange(0.0, 1.0)
            spin.setSingleStep(0.05)
            spin.setDecimals(3)
            spin.setValue(value)
            spin.setPrefix(f"{name} ")
            self.boundary[name] = spin
            boundary_row.addWidget(spin)
        self.suggest_button = self._button("Suggest zone", "suggest", self.suggest_zone)
        self.add_zone_button = self._button("Add label zone", "add-zone", self.add_zone)
        zone_box = QGroupBox("Label zone (curvature-checked on the exact CAD surface)", self)
        zone_form = QFormLayout(zone_box)
        zone_form.addRow("Kind", self.kind)
        zone_form.addRow("Variant", self.variant)
        zone_form.addRow("Placement (0..1 of the host face)", boundary_row)
        buttons = QHBoxLayout()
        buttons.addWidget(self.suggest_button)
        buttons.addWidget(self.add_zone_button)
        zone_form.addRow(buttons)

        self.zones = QListWidget(self)
        self.zones.setObjectName("packlab.labels.zones")
        self.zones.setMaximumHeight(110)
        self.fit = QComboBox(self)
        self.fit.setObjectName("packlab.labels.fit")
        for mode in ("CONTAIN", "COVER", "STRETCH"):
            self.fit.addItem(mode.title(), mode)
        self.import_button = self._button(
            "Import artwork (SVG/PNG)…", "import-artwork", self.import_artwork
        )
        self.dieline_button = self._button(
            "Export dieline SVG (mm)…", "export-dieline", self.export_dieline
        )
        self.artwork_preview = QLabel("No artwork.", self)
        self.artwork_preview.setObjectName("packlab.labels.artwork-preview")
        self.artwork_preview.setMinimumSize(QSize(240, 80))
        self.artwork_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labels_box = QGroupBox("Labels and artwork", self)
        labels_layout = QVBoxLayout(labels_box)
        labels_layout.addWidget(self.zones)
        row = QHBoxLayout()
        row.addWidget(QLabel("Fit", self))
        row.addWidget(self.fit)
        row.addWidget(self.import_button)
        row.addWidget(self.dieline_button)
        labels_layout.addLayout(row)
        labels_layout.addWidget(self.artwork_preview)

        self.material = QComboBox(self)
        self.material.setObjectName("packlab.labels.material")
        for preset in workbench.catalog.entries:
            self.material.addItem(preset.material.display_name, preset.material.material_id)
        self.material.setCurrentIndex(self.material.findData(workbench.material_id))
        self.render_button = self._button("Render mockup (Blender)…", "render", self.render_mockup)
        self.mockup_preview = QLabel("No mockup rendered.", self)
        self.mockup_preview.setObjectName("packlab.labels.mockup-preview")
        self.mockup_preview.setMinimumSize(QSize(240, 240))
        self.mockup_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        render_box = QGroupBox("Material and mockup (visual reference only)", self)
        render_form = QFormLayout(render_box)
        render_form.addRow("Material", self.material)
        render_form.addRow(self.render_button)
        render_form.addRow(self.mockup_preview)

        self.status = QLabel("Open a Design Model to place labels.", self)
        self.status.setObjectName("packlab.labels.status")
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        disclaimer = QLabel(
            "Dimensions are mm_unverified design geometry; print fit, colour and physical "
            "accuracy are DEFERRED_OWNER_VALIDATION.",
            self,
        )
        disclaimer.setWordWrap(True)

        left = QVBoxLayout()
        left.addWidget(model_box)
        left.addWidget(zone_box)
        left.addWidget(labels_box)
        right = QVBoxLayout()
        right.addWidget(render_box)
        right.addStretch(1)
        columns = QHBoxLayout()
        columns.addLayout(left, 3)
        columns.addLayout(right, 2)
        layout = QVBoxLayout(self)
        layout.addLayout(columns)
        layout.addWidget(self.status)
        layout.addWidget(disclaimer)

        self.material.currentIndexChanged.connect(self._material_changed)
        self.zones.currentRowChanged.connect(lambda _row: self._show_artwork())
        self.mockup_finished.connect(self._mockup_done)
        workbench.changed.connect(self.refresh)
        self.refresh()

    def _button(self, text: str, name: str, slot: Callable[[], object]) -> QPushButton:
        button = QPushButton(text, self)
        button.setObjectName(f"packlab.labels.{name}")
        button.clicked.connect(lambda _checked=False: slot())
        return button

    def _start_folder(self) -> Path:
        return self.project_root() or Path.home()

    def _run(self, action: Callable[[], str]) -> None:
        try:
            self.status.setText(action())
        except Exception as error:  # every core refusal is shown, never swallowed
            self.status.setText(f"Not done: {_text_error(error)}")

    @property
    def selected_entry(self) -> LabelZoneEntry | None:
        row = self.zones.currentRow()
        labels = self.workbench.labels
        return labels[row] if 0 <= row < len(labels) else None

    # ------------------------------------------------------------------ actions
    def open_model(self) -> None:
        path = self.choose_design_model_path()
        if not path:
            return
        self._run(lambda: f"Opened {self.workbench.open_document(path).part_name}.")

    def use_project_model(self, *, automatic: bool = False) -> None:
        """Open the newest Design Model revision Measure & Design saved in the project."""
        root = self.project_root()
        latest = latest_project_design_model(root) if root is not None else None
        if latest is None:
            if not automatic:
                self.status.setText(
                    "No Design Model saved in this project yet (Measure & Design > Save)."
                )
            return
        if automatic and self.workbench.session is not None:
            return
        self._run(
            lambda: f"Opened project Design Model {self.workbench.open_document(latest).part_name}."
        )

    def suggest_zone(self) -> None:
        def action() -> str:
            kind = LabelZoneKind(self.kind.currentData())
            self.suggestion = self.workbench.suggest_label_zone(kind)
            for name, value in self.suggestion.boundary.as_dict().items():
                self.boundary[name].setValue(value)
            if not self.variant.text().strip():
                self.variant.setText(kind.value)
            candidate = self.suggestion.candidate
            return (
                f"Suggested {candidate.surface_type.removeprefix('GeomAbs_').lower()} region "
                f"(|curvature| {candidate.maximum_absolute_curvature:.4f}/mm) at "
                f"z {candidate.center[2]:.1f} mm. Adjust the placement, then Add label zone."
            )

        self._run(action)

    def add_zone(self) -> None:
        def action() -> str:
            kind = LabelZoneKind(self.kind.currentData())
            if self.suggestion is None or self.suggestion.kind is not kind:
                self.suggestion = self.workbench.suggest_label_zone(kind)
            boundary = LabelZoneBoundary(*(self.boundary[name].value() for name in self.boundary))
            entry = self.workbench.add_label_zone(
                self.suggestion,
                boundary=boundary,
                variant_id=self.variant.text().strip() or None,
            )
            self.zones.setCurrentRow(len(self.workbench.labels) - 1)
            self.variant.clear()
            width, height = entry.size_mm
            return f"Added {entry.variant_id} label: {width:.1f} x {height:.1f} mm_unverified."

        self._run(action)

    def import_artwork(self) -> None:
        entry = self.selected_entry
        if entry is None:
            self.status.setText("Add or select a label zone first.")
            return
        path = self.choose_artwork_path()
        if not path:
            return

        def action() -> str:
            artwork = self.workbench.import_artwork(entry, path, fit_mode=self.fit.currentData())
            return (
                f"Placed {Path(path).name} ({artwork.asset.media_type}) on {entry.variant_id}, "
                f"fit {artwork.mapping.fit_mode}."
            )

        self._run(action)

    def export_dieline(self) -> None:
        entry = self.selected_entry
        if entry is None:
            self.status.setText("Add or select a label zone first.")
            return
        folder = self.choose_directory("Export dieline SVG to folder")
        if not folder:
            return

        def action() -> str:
            path, export = self.workbench.export_dieline_svg(entry, folder)
            return (
                f"Dieline written: {path} ({export.width_mm_unverified:.1f} x "
                f"{export.height_mm_unverified:.1f} mm incl. bleed and 10 mm scale mark)."
            )

        self._run(action)

    def render_mockup(self) -> None:
        if self._render_thread is not None and self._render_thread.is_alive():
            self.status.setText("A mockup render is already running.")
            return
        folder = self.choose_directory("Render mockup into folder")
        if not folder:
            return
        try:
            job = self.workbench.prepare_mockup(folder)
        except Exception as error:
            self.status.setText(f"Not done: {_text_error(error)}")
            return
        job_id = self._job_start()
        self.render_button.setEnabled(False)
        self.status.setText(f"Rendering FRONT, THREE_QUARTER, BACK with {job.executable.name}…")

        def work() -> None:
            try:
                job.run()
                self.mockup_finished.emit((job_id, job, None))
            except Exception as error:
                self.mockup_finished.emit((job_id, job, error))

        self._render_thread = threading.Thread(target=work, name="packlab-mockup", daemon=True)
        self._render_thread.start()

    def wait_for_render(self, timeout: float | None = None) -> None:
        if self._render_thread is not None:
            self._render_thread.join(timeout)

    # ------------------------------------------------------------------ state
    def _job_start(self) -> str | None:
        manager = self.job_manager
        if manager is None:
            return None
        job = manager.create("Render label mockup", "blender-mockup", cancellable=False)
        manager.start(job.job_id)
        return job.job_id

    def _mockup_done(self, payload: object) -> None:
        assert isinstance(payload, tuple)
        job_id: str | None = payload[0]
        job: MockupJob = payload[1]
        error: Exception | None = payload[2]
        self.render_button.setEnabled(True)
        manager = self.job_manager
        if error is not None:
            if manager is not None and job_id is not None:
                manager.fail(job_id, _text_error(error))
            self.status.setText(f"Mockup render failed: {_text_error(error)}")
            return
        if manager is not None and job_id is not None:
            manager.succeed(job_id, "mockup rendered")
        self.last_mockup = job.result
        image = job.root / "renders" / "standard_views" / "three_quarter.png"
        pixmap = QPixmap(str(image))
        if not pixmap.isNull():
            self.mockup_preview.setPixmap(
                pixmap.scaled(
                    QSize(320, 320),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.status.setText(f"Mockup rendered: {job.root / 'renders' / 'standard_views'}")

    def _material_changed(self, _index: int) -> None:
        value = self.material.currentData()
        if isinstance(value, str) and value != self.workbench.material_id:
            self.workbench.set_material(value)

    def refresh(self) -> None:
        self.model_summary.setText(self.workbench.summary())
        has_model = self.workbench.session is not None
        for widget in (self.suggest_button, self.add_zone_button, self.render_button):
            widget.setEnabled(has_model)
        row = self.zones.currentRow()
        self.zones.clear()
        for entry in self.workbench.labels:
            width, height = entry.size_mm
            artwork = (
                f"artwork {entry.artwork.asset.media_type}, fit {entry.artwork.mapping.fit_mode}"
                if entry.artwork is not None
                else "no artwork"
            )
            self.zones.addItem(
                f"{entry.variant_id} ({entry.kind.value}) {width:.1f} x {height:.1f} mm · {artwork}"
            )
        if self.workbench.labels:
            self.zones.setCurrentRow(min(max(row, 0), len(self.workbench.labels) - 1))
        for widget in (self.import_button, self.dieline_button):
            widget.setEnabled(bool(self.workbench.labels))
        self._show_artwork()

    def _show_artwork(self) -> None:
        entry = self.selected_entry
        if entry is None or entry.artwork is None:
            self.artwork_preview.setText("No artwork.")
            return
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(entry.artwork.content))
        if pixmap.isNull():
            self.artwork_preview.setText(entry.artwork.asset.media_type)
            return
        self.artwork_preview.setPixmap(
            pixmap.scaled(
                QSize(320, 90),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


__all__ = ["LabelsView", "install_design_workbench"]


def install_design_workbench(window: StudioMainWindow) -> None:
    """Connect the shared workbench to Exports, the library and the open project."""
    from .engineering_export import EngineeringExportView
    from .library_actions import LibraryActionsBar
    from .navigation import Route
    from .packaging_library_browser import (
        PackagingLibraryBrowserService,
        PackagingLibraryBrowserView,
    )

    workbench = window.design_workbench
    manager = window.project_manager
    stack = window.route_stack

    def selected_scan_master() -> object:
        return manager.selected_scan_master_revision() if manager.current is not None else None

    exports = stack.views[Route.EXPORTS]
    if isinstance(exports, EngineeringExportView):
        workbench.changed.connect(exports.refresh_source)
    labels = stack.views[Route.LABELS]
    if isinstance(labels, LabelsView):
        manager.add_listener(lambda _metadata: labels.use_project_model(automatic=True))
    library = stack.views[Route.LIBRARY]
    service = window.packaging_library_service
    if isinstance(library, PackagingLibraryBrowserView) and isinstance(
        service, PackagingLibraryBrowserService
    ):
        if service.sku_artwork_references_provider is None:
            service.sku_artwork_references_provider = workbench.sku_artwork_references
        bar = LibraryActionsBar(
            library, service, workbench, scan_master_provider=selected_scan_master
        )
        library_layout = library.layout()
        if isinstance(library_layout, QVBoxLayout):
            library_layout.insertWidget(0, bar)


__all__ = ["LabelsView", "install_design_workbench"]
