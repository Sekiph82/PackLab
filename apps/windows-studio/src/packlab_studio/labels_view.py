"""Labels route: label zones, artwork, dieline, material and Blender mockup (PL-0448)."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from PySide6.QtCore import QByteArray, QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
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
    DesignWorkbenchError,
    LabelZoneEntry,
    LabelZoneSuggestion,
    MockupJob,
    label_preview_points,
    latest_project_design_model,
)
from .i18n import tr
from .jobs import JobManager
from .model_viewer import ModelViewerView
from .preferences import documents_folder
from .project import LABEL_PARTS, PROJECT_PARTS
from .viewport import MeshGeometry, PointCloudGeometry, SceneObjectKind, ViewportService

if TYPE_CHECKING:
    from .shell import StudioMainWindow


def _text_error(error: Exception) -> str:
    return str(error) or type(error).__name__


PART_CHOICES = (
    (None, "Project Design Model"),
    ("closure", "Closure"),
    ("body", "Body"),
    ("assembled", "Assembled"),
)
TOP_DISC = "top"  # closure top: flat disc/annulus zone (core LabelZoneKind.TOP)
# Zone kinds per part: closure skirt = wrap, top = disc; body side wall = wrap/front/back.
PART_KINDS: dict[str | None, tuple[tuple[str, str], ...]] = {
    None: (("wrap", "Wrap"), ("front", "Front"), ("back", "Back")),
    "body": (("wrap", "Wrap (side wall)"), ("front", "Front"), ("back", "Back")),
    "closure": (("wrap", "Wrap (skirt)"), (TOP_DISC, "Top disc")),
}


def _display(points: np.ndarray) -> tuple[tuple[float, float, float], ...]:
    """Design Model z-up mm -> viewer y-up."""
    return tuple((float(x), float(z), float(-y)) for x, y, z in points)


class LabelsView(QWidget):
    """Owner surface over ``DesignWorkbench``; every button calls one core-backed action."""

    mockup_finished = Signal(object)

    def __init__(
        self,
        workbench: DesignWorkbench,
        *,
        job_manager: JobManager | None = None,
        project_root: Callable[[], Path | None] = lambda: None,
        project_manager: Any = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("packlab.view.labels")
        self.workbench = workbench
        self.job_manager = job_manager
        self.project_root = project_root
        self.project_manager = project_manager
        self.suggestion: LabelZoneSuggestion | None = None
        self.last_mockup: dict[str, object] | None = None
        self._render_thread: threading.Thread | None = None
        self._mockup_job: MockupJob | None = None
        self._loaded_project_key: str | None = None
        # PL-0487: the project part the page works on (None = project's current Design Model).
        self.part: str | None = None
        self.placement_provider: Callable[[], tuple[str, Any, Any]] = lambda: ("none", None, ())
        self.stale_document: dict[str, Any] | None = None
        self.assembled_geometry: list[tuple[str, SceneObjectKind, Any]] = []
        # (key, geometry, label count, notes) of the last Assembled preview
        self._assembled_cache: tuple[str, list[Any], int, list[str]] | None = None
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
        self.part_selector = QComboBox(self)
        self.part_selector.setObjectName("packlab.labels.part")
        for key, text in PART_CHOICES:
            self.part_selector.addItem(tr(text), key)
        self.reapply_button = self._button(
            "Re-apply labels to the new Design Model", "reapply", self.reapply_labels
        )
        self.reapply_button.hide()
        model_box = QGroupBox("Design Model", self)
        model_layout = QVBoxLayout(model_box)
        part_row = QHBoxLayout()
        part_row.addWidget(QLabel("Part", self))
        part_row.addWidget(self.part_selector, 1)
        model_layout.addLayout(part_row)
        model_layout.addWidget(self.model_summary)
        model_layout.addWidget(self.reapply_button)
        model_layout.addWidget(self.project_model_button)
        model_layout.addWidget(self.open_button)

        self.kind = QComboBox(self)
        self.kind.setObjectName("packlab.labels.zone-kind")
        self._set_kinds(None)
        self.variant = QLineEdit(self)
        self.variant.setObjectName("packlab.labels.variant")
        self.variant.setPlaceholderText("variant name, e.g. front, back, wrap-v2")
        self.boundary: dict[str, QDoubleSpinBox] = {}
        boundary_row = QGridLayout()  # 2x2 so the page fits 1280 px screens (PL-0464)
        for index, (name, value) in enumerate(
            (("u_min", 0.0), ("v_min", 0.1), ("u_max", 1.0), ("v_max", 0.9))
        ):
            spin = QDoubleSpinBox(self)
            spin.setObjectName(f"packlab.labels.boundary.{name}")
            spin.setRange(0.0, 1.0)
            spin.setSingleStep(0.05)
            spin.setDecimals(3)
            spin.setValue(value)
            spin.setPrefix(f"{name} ")
            self.boundary[name] = spin
            boundary_row.addWidget(spin, index // 2, index % 2)
        self.suggest_button = self._button("Suggest zone", "suggest", self.suggest_zone)
        self.add_zone_button = self._button("Add label zone", "add-zone", self.add_zone)
        zone_box = QGroupBox("Label zone", self)
        zone_form = QFormLayout(zone_box)
        zone_hint = QLabel("Curvature-checked on the exact CAD surface.", self)
        zone_hint.setWordWrap(True)
        zone_form.addRow(zone_hint)
        zone_form.addRow("Kind", self.kind)
        zone_form.addRow("Variant", self.variant)
        zone_form.addRow("Placement (0..1)", boundary_row)
        # Top disc (closure top): radii in mm and artwork rotation about the axis.
        self.disc_outer = self._spin("disc-outer", 0.0, 1000.0, " mm", "0 = whole top face")
        self.disc_inner = self._spin("disc-inner", 0.0, 1000.0, " mm", "0 = no hole")
        self.disc_rotation = self._spin("disc-rotation", -360.0, 360.0, " deg", "")
        self.disc_row = QWidget(self)  # one narrow column (1280 px fit)
        disc_layout = QFormLayout(self.disc_row)
        disc_layout.setContentsMargins(0, 0, 0, 0)
        disc_layout.addRow("Outer radius", self.disc_outer)
        disc_layout.addRow("Inner radius", self.disc_inner)
        disc_layout.addRow("Rotation", self.disc_rotation)
        zone_form.addRow("Top disc", self.disc_row)
        self._sync_kind_widgets()
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
        row.addWidget(self.fit, 1)
        labels_layout.addLayout(row)
        labels_layout.addWidget(self.import_button)
        labels_layout.addWidget(self.dieline_button)
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
        render_box = QGroupBox("Material and mockup", self)
        render_form = QFormLayout(render_box)
        render_hint = QLabel("Visual reference only.", self)
        render_hint.setWordWrap(True)
        render_form.addRow(render_hint)
        self.material.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.material.setMinimumContentsLength(14)
        render_form.addRow("Material", self.material)
        self.cancel_render_button = self._button(
            "Cancel render", "cancel-render", self.cancel_render
        )
        self.cancel_render_button.setEnabled(False)
        render_form.addRow(self.render_button)
        render_form.addRow(self.cancel_render_button)
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
        # Assembled (PL-0487): both parts' Design Models + labels, placed (preview only).
        self.assembled_viewer = ModelViewerView()
        self.assembled_viewer.setObjectName("packlab.labels.assembled-viewer")
        self.assembled_viewer.open_button.hide()
        self.assembled_viewer.setMinimumSize(QSize(320, 320))
        self.assembled_viewer.hide()
        right = QVBoxLayout()
        right.addWidget(render_box)
        right.addWidget(self.assembled_viewer, 1)
        right.addStretch(1)
        columns = QHBoxLayout()
        columns.addLayout(left, 3)
        columns.addLayout(right, 2)
        layout = QVBoxLayout(self)
        layout.addLayout(columns)
        layout.addWidget(self.status)
        layout.addWidget(disclaimer)

        self.material.currentIndexChanged.connect(self._material_changed)
        self.kind.currentIndexChanged.connect(self._kind_changed)
        self.zones.currentRowChanged.connect(lambda _row: self._show_artwork())
        self.part_selector.currentIndexChanged.connect(
            lambda _index: self.show_part(self.part_selector.currentData())
        )
        self.mockup_finished.connect(self._mockup_done)
        workbench.changed.connect(self.refresh)
        self.refresh()

    def _button(self, text: str, name: str, slot: Callable[[], object]) -> QPushButton:
        button = QPushButton(text, self)
        button.setObjectName(f"packlab.labels.{name}")
        button.clicked.connect(lambda _checked=False: slot())
        return button

    def _start_folder(self) -> Path:
        return self.project_root() or documents_folder()  # F15: not the bare home

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

    def _project_design_model(self) -> tuple[str, bytes | Path] | None:
        """(key, source) of the project's current Design Model.

        Project authority (``selected_design_model``, moved by save/undo/redo) wins; the
        newest ``derived/design_model`` file is used only for projects without any
        Design Model authority record (saved before the authority existed).
        """
        manager = self.project_manager
        root = self.project_root()
        if root is None:
            return None
        if manager is not None and callable(getattr(manager, "selected_design_model", None)):
            selected = manager.selected_design_model()
            if selected is not None:
                record, document = selected
                return str(record["revision_id"]), json.dumps(document).encode("utf-8")
            if manager.has_design_model_authority():
                return None
        latest = latest_project_design_model(root)
        return (str(latest), latest) if latest is not None else None

    def use_project_model(self, *, automatic: bool = False) -> None:
        """Open the project's current Design Model (automatic: only when it changed)."""
        try:
            current = self._project_design_model()
        except Exception as error:  # tampered/missing authority file is shown, not hidden
            self.status.setText(f"Project Design Model unavailable: {_text_error(error)}")
            return
        if current is None:
            if not automatic:
                self.status.setText(
                    "No Design Model saved in this project yet (Measure & Design > Save)."
                )
            return
        key, source = current
        if automatic and key == self._loaded_project_key:
            return  # autosave/revision bump of the same selection: keep the labels
        self._loaded_project_key = key
        if isinstance(source, bytes):
            family = (json.loads(source).get("package_family_workflow") or {}).get("family_label")
            if family:  # Package Families revision (PL-0459): not a single-revolve jar/bottle
                self.status.setText(
                    "Labels currently support Measure & Design jar/bottle revisions; this "
                    f"{family} model isn't supported yet. Select the container revision "
                    "(Edit > Undo) or open a jar/bottle Design Model."
                )
                return
        part = key.removeprefix("design-model:")[:16] if isinstance(source, bytes) else ""
        self._run(
            lambda: (
                "Opened project Design Model "
                f"{self.workbench.open_document(source, part_name=part).part_name}."
            )
        )

    def suggest_zone(self) -> None:
        def action() -> str:
            kind = self._zone_kind()
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
            kind = self._zone_kind()
            if self.suggestion is None or self.suggestion.kind is not kind:
                self.suggestion = self.workbench.suggest_label_zone(kind)
            boundary = LabelZoneBoundary(*(self.boundary[name].value() for name in self.boundary))
            disc: dict[str, Any] = {}
            if kind is LabelZoneKind.TOP:  # 0 = whole top face / the face's own hole
                disc = {
                    "disc_outer_radius_mm": self.disc_outer.value() or None,
                    "disc_inner_radius_mm": self.disc_inner.value() or None,
                    "disc_rotation_degrees": self.disc_rotation.value(),
                }
            entry = self.workbench.add_label_zone(
                self.suggestion,
                boundary=None if disc else boundary,
                variant_id=self.variant.text().strip() or None,
                **disc,
            )
            self.zones.setCurrentRow(len(self.workbench.labels) - 1)
            self.variant.clear()
            width, height = entry.size_mm
            return (
                f"Added {entry.variant_id} label: {width:.1f} x {height:.1f} mm_unverified."
                + self._save_part_labels()
            )

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
                f"fit {artwork.mapping.fit_mode}." + self._save_part_labels()
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
        self._mockup_job = job
        job_id = self._job_start(job)
        self.render_button.setEnabled(False)
        self.cancel_render_button.setEnabled(True)
        self.status.setText(f"Rendering FRONT, THREE_QUARTER, BACK with {job.executable.name}…")

        def work() -> None:
            try:
                job.run()
                self.mockup_finished.emit((job_id, job, None))
            except Exception as error:
                self.mockup_finished.emit((job_id, job, error))

        self._render_thread = threading.Thread(target=work, name="packlab-mockup", daemon=True)
        self._render_thread.start()

    def cancel_render(self) -> None:
        job = self._mockup_job
        if job is None or self._render_thread is None or not self._render_thread.is_alive():
            return
        job.cancel()
        self.status.setText("Cancelling the mockup render (Blender is stopped)…")

    def wait_for_render(self, timeout: float | None = None) -> None:
        if self._render_thread is not None:
            self._render_thread.join(timeout)

    # ------------------------------------------------------------------ project parts (PL-0487)
    def _zone_kind(self) -> LabelZoneKind:
        return LabelZoneKind(self.kind.currentData())

    def _set_kinds(self, part: str | None) -> None:
        self.kind.blockSignals(True)
        self.kind.clear()
        for value, text in PART_KINDS.get(part, PART_KINDS[None]):
            self.kind.addItem(tr(text), value)
        self.kind.blockSignals(False)
        self.suggestion = None
        if hasattr(self, "disc_row"):
            self._sync_kind_widgets()

    def show_part(self, part: str | None) -> None:
        """Follow the Scene selection: work on that part's Design Model and labels."""
        part = part if part in PROJECT_PARTS else None
        index = self.part_selector.findData(part)
        if self.part_selector.currentIndex() != index:
            self.part_selector.blockSignals(True)
            self.part_selector.setCurrentIndex(index)
            self.part_selector.blockSignals(False)
        if part == self.part:
            return self.project_changed()
        self.part = part
        self._loaded_project_key = None
        self.stale_document = None
        self._set_kinds(part)
        self.assembled_viewer.setVisible(part == "assembled")
        self.mockup_preview.setVisible(part != "assembled")
        self.project_changed()

    def project_changed(self) -> None:
        """Project revision changed (save, undo, label edit): reload only what changed."""
        if self.part is None:
            self.use_project_model(automatic=True)
        elif self.part == "assembled":
            self.show_assembled()
        else:
            self._open_part(self.part)

    def _manager_ready(self) -> bool:
        manager = self.project_manager
        return (
            manager is not None
            and getattr(manager, "layout", None) is not None
            and callable(getattr(manager, "part_design_model", None))
        )

    def _open_part(self, part: str) -> None:
        name = tr(part.capitalize())
        try:
            found = self.project_manager.part_design_model(part) if self._manager_ready() else None
        except Exception as error:  # tampered/missing authority file is shown, not hidden
            self.status.setText(f"Not done: {_text_error(error)}")
            return
        if found is None:
            self._loaded_project_key = None
            self.stale_document = None
            if self.workbench.session is not None:
                self.workbench.close_document()
            else:
                self.refresh()
            self.status.setText(
                tr(
                    "No Design Model for {part} yet: select {part} in Scene, then Measure & "
                    "Design > Use selected part, fit and Save."
                ).format(part=name)
            )
            return
        record, document = found
        key = f"{part}:{record['revision_id']}"
        if key == self._loaded_project_key:
            return  # same part revision (e.g. our own label save): keep the session
        self._loaded_project_key = key
        self.stale_document = None

        def action() -> str:
            self.workbench.open_document(json.dumps(document).encode("utf-8"), part_name=part)
            labels = self.project_manager.part_labels(part)
            revision = str(record["revision_id"])
            if labels is None or not labels.get("labels"):
                return tr("{part} Design Model {revision} opened; no labels yet.").format(
                    part=name, revision=revision[:32]
                )
            if labels.get("design_model_revision_id") != revision:
                self.stale_document = labels
                self.refresh()
                return tr(
                    "Labels on {part} are STALE: placed on Design Model {old}, the part's "
                    "Design Model is now {new}. Re-apply labels to place them on the new model."
                ).format(
                    part=name,
                    old=str(labels.get("design_model_revision_id"))[:32],
                    new=revision[:32],
                )
            problems = self.workbench.restore_labels(
                labels, self.project_manager.read_label_artwork
            )
            text = tr("{part}: {count} label(s) restored on Design Model {revision}.").format(
                part=name, count=len(self.workbench.labels), revision=revision[:32]
            )
            return text + ("" if not problems else " " + "; ".join(problems))

        self._run(action)

    def _save_part_labels(self) -> str:
        """Persist the part's label document (status suffix; empty when not in part mode)."""
        part, manager = self.part, self.project_manager
        if part not in LABEL_PARTS or not self._manager_ready():
            return ""
        session = self.workbench.session
        if session is None or self._loaded_project_key != f"{part}:{session.model.revision_id}":
            # e.g. a file opened with Open Design Model while a part is selected
            return " " + tr(
                "Not saved in the project: the open Design Model is not the {part} Design Model."
            ).format(part=tr(str(part).capitalize()))
        document = self.workbench.label_document(str(part), manager.store_label_artwork)
        self.stale_document = None
        manager.record_part_labels(str(part), document)
        self.refresh()
        return " " + tr("Saved in the project ({part} labels, Design Model {revision}).").format(
            part=tr(str(part).capitalize()),
            revision=document["design_model_revision_id"][:32],
        )

    def reapply_labels(self) -> None:
        """Place stale labels (same kind, placement, artwork) on the part's new Design Model."""
        stale = self.stale_document
        if stale is None or self.workbench.session is None:
            return

        def action() -> str:
            self.workbench.labels = []
            problems = self.workbench.restore_labels(stale, self.project_manager.read_label_artwork)
            text = tr("{count} label(s) re-applied.").format(count=len(self.workbench.labels))
            text += self._save_part_labels()
            return text + ("" if not problems else " " + "; ".join(problems))

        self._run(action)

    def _part_workbench(self, part: str) -> tuple[DesignWorkbench | None, str]:
        """A workbench with ``part``'s Design Model and current labels (for Assembled)."""
        name = tr(part.capitalize())
        found = self.project_manager.part_design_model(part)
        if found is None:
            return None, tr("{part} has no Design Model yet").format(part=name)
        record, document = found
        workbench = DesignWorkbench()
        workbench.open_document(json.dumps(document).encode("utf-8"), part_name=part)
        labels = self.project_manager.part_labels(part)
        if labels is None:
            return workbench, ""
        if labels.get("design_model_revision_id") != record["revision_id"]:
            return workbench, tr("{part} labels are stale (re-apply them on {part})").format(
                part=name
            )
        problems = workbench.restore_labels(labels, self.project_manager.read_label_artwork)
        return workbench, "; ".join(problems)

    def show_assembled(self) -> None:
        """Both parts' Design Models and labels, the closure seated by the PL-0484 placement.

        The Blender mockup renders one Design Model, so Assembled shows a combined preview
        here instead. The closure's Design Model goes into the body's Design Model frame
        through the recorded frames: body_design <- body_cloud <- closure_cloud (placement)
        <- closure_design. Preview only; geometry authority stays with each Design Model.
        The result is cached until a Design Model, label document or placement changes.
        """
        self.assembled_geometry = []
        self.assembled_viewer.service = ViewportService(self.assembled_viewer.service.adapter)
        self.assembled_viewer.redraw()
        if self.workbench.session is not None:
            self.workbench.close_document()  # editing happens on Body / Closure
        self._loaded_project_key = None
        mockup_note = tr(
            "The Blender mockup renders one Design Model at a time: select Body or Closure "
            "to render each part. Assembled shows both parts with their labels below."
        )
        if not self._manager_ready():
            self.status.setText(tr("Open a project with Body and Closure parts first."))
            return
        status, record, _placed = self.placement_provider()
        if status != "placed" or record is None:
            self.status.setText(
                tr(
                    "Assembled labels need the closure placed on the body: select Assembled "
                    "in Scene and use Place closure on body."
                )
                + " "
                + mockup_note
            )
            return
        try:
            key = self._assembled_key(record)
            if self._assembled_cache is not None and self._assembled_cache[0] == key:
                _key, geometry_list, count, notes = self._assembled_cache
                self._show_assembled_geometry(geometry_list, count, notes, record, mockup_note)
                return
            transforms = {"body": np.eye(4), "closure": self._closure_in_body(record)}
            parts = {part: self._part_workbench(part) for part in ("body", "closure")}
        except Exception as error:
            self.status.setText(f"Not done: {_text_error(error)}")
            return
        missing = [note for workbench, note in parts.values() if workbench is None]
        if missing:
            self.status.setText("; ".join(missing) + ". " + mockup_note)
            return
        notes, count = [], 0
        for part, (workbench, note) in parts.items():
            assert workbench is not None and workbench.session is not None
            session = workbench.session
            transform = transforms[part]

            def placed(points: np.ndarray, transform: np.ndarray = transform) -> np.ndarray:
                return np.asarray(points, float) @ transform[:3, :3].T + transform[:3, 3]

            mesh = session.label_preview.mesh
            kind = SceneObjectKind.DESIGN_MODEL if part == "body" else SceneObjectKind.CAP
            geometry: Any = MeshGeometry(
                _display(placed(np.asarray(mesh.vertices))), mesh.triangles
            )
            self.assembled_geometry.append((part, kind, geometry))
            for index, entry in enumerate(workbench.labels):
                points, colors = label_preview_points(session, entry)
                if not len(points):
                    continue
                geometry = PointCloudGeometry(
                    _display(placed(points)), tuple(map(tuple, colors.tolist()))
                )
                self.assembled_geometry.append(
                    (f"{part}-label-{index}", SceneObjectKind.LABEL, geometry)
                )
                count += 1
            if note:
                notes.append(note)
        self._assembled_cache = (key, list(self.assembled_geometry), count, notes)
        self._show_assembled_geometry(self.assembled_geometry, count, notes, record, mockup_note)

    def _assembled_key(self, record: dict[str, Any]) -> str:
        manager = self.project_manager
        parts = {}
        for part in ("body", "closure"):
            found = manager.part_design_model(part)
            parts[part] = {
                "design": None if found is None else found[0]["revision_id"],
                "labels": manager.part_labels(part),
                "frame": manager.part_design_frame(part),
            }
        return json.dumps(
            {
                "graph": record["graph"].get("revision_id"),
                "sources": record.get("sources"),
                **parts,
            },
            sort_keys=True,
            default=str,
        )

    def _closure_in_body(self, record: dict[str, Any]) -> np.ndarray:
        """4x4 closure Design Model frame -> body Design Model frame (mm_unverified)."""
        manager = self.project_manager
        value = record.get("sources")
        sources: dict[str, Any] = value if isinstance(value, dict) else {}
        frames = {}
        for part in ("body", "closure"):
            name = tr(part.capitalize())
            frame = manager.part_design_frame(part)
            if frame is None:
                raise DesignWorkbenchError(
                    tr(
                        "the {part} Design Model has no recorded scan frame: fit it in Measure & "
                        "Design with Use selected part (promote, fit, save)"
                    ).format(part=name)
                )
            source = sources.get(part) or {}
            if source.get("cloud_sha256") != frame.get("source_cloud_sha256") or source.get(
                "frame"
            ) != frame.get("source_frame"):
                raise DesignWorkbenchError(
                    tr(
                        "the {part} Design Model was fitted to another cloud than the placed "
                        "one: place the closure again or refit {part}"
                    ).format(part=name)
                )
            frames[part] = np.asarray(frame["source_to_scan_master"], float).reshape(4, 4)
        relationship = record["graph"]["relationships"][0]["closure_on_body"]
        closure_on_body = np.asarray(relationship, float).reshape(4, 4)
        return frames["body"] @ closure_on_body @ np.linalg.inv(frames["closure"])

    def _show_assembled_geometry(
        self,
        geometry_list: list[tuple[str, SceneObjectKind, Any]],
        count: int,
        notes: list[str],
        record: dict[str, Any],
        mockup_note: str,
    ) -> None:
        self.assembled_geometry = list(geometry_list)
        service = ViewportService(self.assembled_viewer.service.adapter)
        for object_id, kind, geometry in self.assembled_geometry:
            service.add_geometry(object_id, kind, geometry)
        self.assembled_viewer.service = service
        self.assembled_viewer.fit()
        self.assembled_viewer.status.setText(
            tr("Assembled preview: Body + Closure Design Models, mm_unverified; visual only.")
        )
        self.status.setText(
            tr(
                "Assembled: Body and Closure with {count} label(s), closure seated by "
                "assembly {revision}."
            ).format(count=count, revision=str(record["graph"]["revision_id"])[:32])
            + (" " + "; ".join(notes) if notes else "")
            + " "
            + mockup_note
        )

    # ------------------------------------------------------------------ state
    def _job_start(self, mockup: MockupJob) -> str | None:
        manager = self.job_manager
        if manager is None:
            return None
        job = manager.create("Render label mockup", "blender-mockup", cancellable=True)
        # Jobs-panel cancel and window shutdown both kill Blender; the worker then reports.

        def cancel_hook() -> bool:
            mockup.cancel()
            return False  # CANCELLING until the worker reports back

        manager.register_cancel_hook(job.job_id, cancel_hook)
        manager.start(job.job_id)
        return job.job_id

    def _mockup_done(self, payload: object) -> None:
        assert isinstance(payload, tuple)
        job_id: str | None = payload[0]
        job: MockupJob = payload[1]
        error: Exception | None = payload[2]
        self.render_button.setEnabled(True)
        self.cancel_render_button.setEnabled(False)
        self._mockup_job = None
        manager = self.job_manager
        if error is not None and job.cancelled:
            if manager is not None and job_id is not None:
                manager.finish_cancel(job_id)
            self.status.setText("Mockup render cancelled; partial views were removed.")
            return
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

    def _spin(
        self, name: str, low: float, high: float, suffix: str, special: str
    ) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(self)
        spin.setObjectName(f"packlab.labels.{name}")
        spin.setRange(low, high)
        spin.setDecimals(2)
        spin.setSuffix(suffix)
        if special:
            spin.setToolTip(tr(special))
        return spin

    def _kind_changed(self, _index: int) -> None:
        self.suggestion = None
        self._sync_kind_widgets()
        self.status.setText(
            f"{self.kind.currentText()} label: Suggest zone, adjust the placement, then Add."
        )

    def _sync_kind_widgets(self) -> None:
        top = self.kind.currentData() == TOP_DISC
        self.disc_row.setEnabled(top)
        for spin in self.boundary.values():
            spin.setEnabled(not top)  # a top label is a centred disc: radii set its size

    def _material_changed(self, _index: int) -> None:
        value = self.material.currentData()
        if isinstance(value, str) and value != self.workbench.material_id:
            self.workbench.set_material(value)

    def refresh(self) -> None:
        self.model_summary.setText(self.workbench.summary())
        self.reapply_button.setVisible(self.stale_document is not None)
        self.reapply_button.setEnabled(
            self.stale_document is not None and self.workbench.session is not None
        )
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
        manager.add_listener(lambda _metadata: labels.project_changed())
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
            library_layout.addWidget(bar)  # below the browser, not above search


__all__ = ["LabelsView", "install_design_workbench"]
