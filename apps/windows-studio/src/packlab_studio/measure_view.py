"""Measure & Design route: object-only, scale, mm measurements, Scan Master, Design Model."""

from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from . import measure_design as md
from .i18n import tr
from .model_viewer import MODEL_FILTER, POINT_DISPLAY_BUDGET, ModelViewerView
from .scan_master_promotion import ScanMasterPromotionAction, ScanMasterPromotionRequest
from .viewport import MeshGeometry, PointCloudGeometry, SceneObjectKind, ViewportService

BAR_SETTING = "calibration/mat_bar_measured_mm"
_DESIGN_COLOR = "design"


def _display(points: np.ndarray) -> tuple[tuple[float, float, float], ...]:
    """Normalized z-up -> viewer y-up."""

    return tuple((float(x), float(z), float(-y)) for x, y, z in points)


def _colors(colors: np.ndarray | None, count: int) -> tuple[tuple[int, int, int], ...]:
    if colors is None or len(colors) != count:
        return ()
    values = np.clip(np.asarray(colors) * 255, 0, 255).astype(int)
    return tuple((int(r), int(g), int(b)) for r, g, b in values)


class MeasureDesignView(QWidget):
    """Buttons call ``measure_design``; core owns every authority decision."""

    draft_changed = Signal()  # unsaved Design Model edits exist (autosave trigger)
    draft_saved = Signal()  # the edits were saved as a project Design Model revision

    def __init__(
        self,
        project_manager: Any = None,
        *,
        file_chooser: Callable[[QWidget], str] | None = None,
        save_chooser: Callable[[QWidget, str], str] | None = None,
        settings: QSettings | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("packlab.view.measure-design")
        self.project_manager = project_manager
        self._choose_file = file_chooser or (
            lambda parent: QFileDialog.getOpenFileName(
                parent, "Open built model", "", MODEL_FILTER
            )[0]
        )
        self._choose_save = save_chooser or (
            lambda parent, name: QFileDialog.getSaveFileName(parent, "Save", name)[0]
        )
        self.settings = settings or QSettings()
        self.model: md.LoadedModel | None = None
        self.mesh_model: md.LoadedModel | None = None
        self.cameras: tuple[md.CameraPose, ...] = ()
        self.workspace: tuple[Path, Path] | None = None
        self.isolation: md.Isolation | None = None
        self.scale: md.ScaleResult | None = None
        self.frame: md.Frame | None = None
        self.measurements: md.Measurements | None = None
        self.scan_master: Any = None
        self.design: md.DesignState | None = None
        self.saved_design_path: Path | None = None
        self.dirty = False
        self._project_seen: str | None = None
        self._companion: Path | None = None
        # PL-0485: the Scene panel's selected part cloud, used instead of the latest build.
        self.part_provider: Callable[[], Path | None] | None = None
        self.part_label: str | None = None  # selected Scene part, None = no selection
        self.part_record: dict[str, Any] | None = None  # set when a combined part is loaded
        # PL-0487: Scene part key (closure/body/assembled) and the part the loaded model is.
        self.part_key: str | None = None
        self.loaded_part: str | None = None

        self.viewer = ModelViewerView()
        self.viewer.open_button.hide()
        self.viewer.reload_button.hide()

        def button(text: str, name: str, slot: Callable[[], object]) -> QPushButton:
            widget = QPushButton(text)
            widget.setObjectName(f"packlab.measure.{name}")
            widget.clicked.connect(slot)
            return widget

        self.open_button = button("Open built model…", "open", self.open_model)
        self.latest_button = button(
            "Use latest project build", "latest", lambda: self.use_latest_build()
        )
        # Brings the last loaded model back (also after a restart): per project in QSettings.
        self.reload_button = button("Reload last model", "reload", lambda: self.reload_last())
        # A newer build offered by the Build page while a model is open here.
        self.offered_build: Path | None = None
        self.newer_button = button(
            tr("A newer build is available — Load it"), "newer", lambda: self.load_offered()
        )
        self.newer_button.hide()
        self.isolate_button = button("1. Isolate object", "isolate", self.isolate)
        self.bar_mm = QDoubleSpinBox()
        self.bar_mm.setRange(80.0, 120.0)
        self.bar_mm.setDecimals(2)
        self.bar_mm.setSuffix(" mm")
        self.bar_mm.setValue(float(str(self.settings.value(BAR_SETTING, md.MAT_REFERENCE_BAR_MM))))
        self.bar_mm.valueChanged.connect(lambda value: self.settings.setValue(BAR_SETTING, value))
        self.marker_button = button(
            "2. Scale from mat markers", "marker-scale", self.scale_from_markers
        )
        self.point_a = QLineEdit()
        self.point_b = QLineEdit()
        self.known_mm = QDoubleSpinBox()
        self.known_mm.setRange(0.0, 5000.0)
        self.known_mm.setDecimals(2)
        self.known_mm.setSuffix(" mm")
        self.manual_button = button("Use manual reference", "manual-scale", self.scale_manually)
        self.measure_button = button("3. Measure (mm)", "measure", self.measure)
        self.report_button = button("Export dimension report…", "report", self.export_report)
        self.actor = QLineEdit(os.environ.get("USERNAME") or os.environ.get("USER") or "owner")
        self.reason = QLineEdit("Isolated, scaled jar from the built model.")
        self.promote_button = button("Promote Scan Master", "promote", self.promote)
        self.owner_review = QCheckBox("Owner review: accept partial scan / straight jar")
        self.fit_button = button("4. Fit Design Model", "fit", self.fit_design)
        self.height_mm = QDoubleSpinBox()
        self.diameter_mm = QDoubleSpinBox()
        for spin in (self.height_mm, self.diameter_mm):
            spin.setRange(1.0, 2000.0)
            spin.setDecimals(2)
            spin.setSuffix(" mm")
        self.apply_button = button("Apply dimensions", "apply", self.apply_dimensions)
        self.save_button = button("Save Design Model revision", "save", self.save_design)
        self.project_design = QLabel("")
        self.project_design.setObjectName("packlab.measure.project-design")
        self.project_design.setWordWrap(True)
        for spin in (self.height_mm, self.diameter_mm):
            spin.valueChanged.connect(lambda _value: self._mark_dirty())
        self.results = QLabel("Open the built model (dense PLY or textured OBJ).")
        self.results.setObjectName("packlab.measure.results")
        self.results.setWordWrap(True)
        self.results.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status = QLabel("")
        self.status.setObjectName("packlab.measure.status")
        self.status.setWordWrap(True)

        scale_box = QGroupBox("Scale and upright")
        scale_form = QFormLayout(scale_box)
        scale_form.addRow("Mat print check: 100 mm bar measures", self.bar_mm)
        scale_form.addRow(self.marker_button)
        scale_form.addRow("Manual point A (model units x, y, z)", self.point_a)
        scale_form.addRow("Manual point B", self.point_b)
        scale_form.addRow("Known A-B length", self.known_mm)
        scale_form.addRow(self.manual_button)
        scan_box = QGroupBox("Scan Master")
        scan_form = QFormLayout(scan_box)
        scan_form.addRow("Actor", self.actor)
        scan_form.addRow("Reason", self.reason)
        scan_form.addRow(self.promote_button)
        design_box = QGroupBox("Design Model (editable)")
        design_form = QFormLayout(design_box)
        design_form.addRow(self.project_design)
        design_form.addRow(self.owner_review)
        design_form.addRow(self.fit_button)
        design_form.addRow("Height", self.height_mm)
        design_form.addRow("Diameter", self.diameter_mm)
        design_form.addRow(self.apply_button)
        design_form.addRow(self.save_button)

        controls = QWidget()
        column = QVBoxLayout(controls)
        for widget in (
            self.open_button,
            self.latest_button,
            self.reload_button,
            self.newer_button,
            self.isolate_button,
            scale_box,
            self.measure_button,
            self.report_button,
            scan_box,
            design_box,
        ):
            column.addWidget(widget)
        column.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidget(controls)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(380)
        layout = QHBoxLayout(self)
        layout.addWidget(scroll)
        right = QVBoxLayout()
        right.addWidget(self.status)
        right.addWidget(self.viewer, 1)
        right.addWidget(self.results)
        layout.addLayout(right, 1)
        self._sync_buttons()
        if hasattr(project_manager, "add_listener"):
            project_manager.add_listener(lambda _metadata: self.refresh_project_design())
        self.refresh_project_design()

    # ------------------------------------------------------------ helpers

    def _mark_dirty(self) -> None:
        if self.design is not None:
            self.dirty = True
            self.draft_changed.emit()

    def refresh_project_design(self) -> None:
        """Show the project's current Design Model (authority state); reset on project switch."""

        manager = self.project_manager
        current = getattr(manager, "current", None)
        project_id = None if current is None else current.project_id
        if project_id != self._project_seen:
            self._project_seen = project_id
            self.design, self.dirty = None, False
            try:
                self.scan_master = (
                    None if current is None else manager.selected_scan_master_revision()
                )
            except Exception:  # unreadable Scan Master: Fit stays disabled
                self.scan_master = None
            self._sync_buttons()
        elif current is not None:
            # Selection changed in place (Edit > Undo/Redo): fit against the selected one.
            try:
                selected_id = manager.selected_scan_master_revision_id()
                if selected_id != getattr(self.scan_master, "revision_id", None):
                    self.scan_master = (
                        None if selected_id is None else manager.selected_scan_master_revision()
                    )
            except Exception:
                self.scan_master = None
            self._sync_buttons()
        if current is None:
            self.project_design.setText("Project Design Model: no project open.")
            return
        try:
            selected = manager.selected_design_model()
        except Exception as error:
            self.project_design.setText(f"Project Design Model unreadable: {error}")
            return
        if selected is None:
            self.project_design.setText("Project Design Model: none saved yet.")
            return
        record, _document = selected
        size = record.get("overall_dimensions_mm_unverified") or {}
        self.project_design.setText(
            f"Project Design Model (current): {record['revision_id'][:34]}… "
            f"H {float(size.get('height', 0)):.2f} × Ø {float(size.get('diameter', 0)):.2f} "
            + (
                f"mm_unverified; fitted to {str(record.get('scan_master_revision_id'))[:24]}…; "
                if record.get("scan_master_revision_id")
                else "mm_unverified; standalone design geometry (no Scan Master); "
            )
            + f"saved at project revision {record.get('project_revision')}"
        )

    def draft(self) -> dict[str, object] | None:
        """Unsaved editor state for autosave/crash recovery (re-fit + dimensions)."""

        if self.design is None:
            return None
        return {
            "contract": "packlab.studio-design-draft.v1",
            "scan_master_revision_id": self.design.model.fitted_to_scan_master_revision_id,
            "base_design_model_revision_id": self.design.model.revision_id,
            "owner_review": self.owner_review.isChecked(),
            "height_mm": self.height_mm.value(),
            "diameter_mm": self.diameter_mm.value(),
        }

    def restore_draft(self, draft: dict[str, Any]) -> bool:
        manager = self.project_manager

        def action() -> str:
            if draft.get("contract") != "packlab.studio-design-draft.v1":
                raise md.MeasureDesignError("autosaved draft has an unknown format")
            scan_master = manager.selected_scan_master_revision()
            if scan_master is None or scan_master.revision_id != draft.get(
                "scan_master_revision_id"
            ):
                raise md.MeasureDesignError("the draft's Scan Master is no longer selected")
            actor = self.actor.text().strip() or "owner"
            owner_review = bool(draft.get("owner_review"))
            self.scan_master = scan_master
            self.owner_review.setChecked(owner_review)
            fitted = md.fit_design_model(scan_master, actor_id=actor, owner_review=owner_review)
            self.design = md.edit_dimensions(
                fitted,
                height=float(draft["height_mm"]),
                diameter=float(draft["diameter_mm"]),
                actor_id=actor,
            )
            self.height_mm.setValue(self.design.height)
            self.diameter_mm.setValue(self.design.diameter)
            self._show_scan_master(self._design_geometry())
            self._mark_dirty()
            return (
                f"restored autosaved draft H {self.design.height:.2f} × "
                f"Ø {self.design.diameter:.2f} mm_unverified (not saved yet)"
            )

        return self._run("Recover draft", action)

    def _last_model_key(self) -> str:
        return f"measure/last_model/{self._project_id()}"

    def last_model(self) -> Path | None:
        value = self.settings.value(self._last_model_key())
        return Path(str(value)) if value and Path(str(value)).is_file() else None

    def offer_build(self, path: Path | None = None) -> bool:
        """Offer ``path`` (or the project's newest build) without replacing the open model."""
        layout = getattr(self.project_manager, "layout", None)
        if path is None and layout is not None:
            path = md.latest_built_model(layout.root)
        if path is None or (self.model is not None and self.model.path == Path(path)):
            return False
        self.offered_build = Path(path)
        self.newer_button.setToolTip(str(path))
        self.newer_button.show()
        self.status.setText(
            tr("A newer build is available: {name}. Your open model is kept.").format(
                name=Path(path).name
            )
        )
        return True

    def load_offered(self) -> bool:
        path = self.offered_build
        if path is None or not self.load(path):
            return False
        self.loaded_part = None  # a raw build, not the Scene part
        return True

    def reload_last(self) -> bool:
        """Load the last model again (resets isolate/scale/fit like a fresh open)."""
        path = self.last_model()
        if path is None:
            self.status.setText(tr("No model loaded yet in this project."))
            return False
        return self.load(path)

    def _sync_buttons(self) -> None:
        last = self.last_model()
        self.reload_button.setEnabled(last is not None)
        self.reload_button.setText(
            tr("Reload last model") if last is None else f"{tr('Reload last model')}: {last.name}"
        )
        self.reload_button.setToolTip("" if last is None else str(last))
        self.isolate_button.setEnabled(self.model is not None)
        scaled_ready = self.isolation is not None
        self.marker_button.setEnabled(
            scaled_ready and bool(self.cameras) and self.workspace is not None
        )
        self.manual_button.setEnabled(scaled_ready)
        self.measure_button.setEnabled(self.frame is not None)
        self.report_button.setEnabled(self.measurements is not None)
        self.promote_button.setEnabled(self.frame is not None)
        self.fit_button.setEnabled(self.scan_master is not None)
        for widget in (self.height_mm, self.diameter_mm, self.apply_button, self.save_button):
            widget.setEnabled(self.design is not None)

    def _run(self, label: str, action: Callable[[], str]) -> bool:
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            # ponytail: runs on the UI thread (marker scale ~10 s on 24 photos); move to
            # JobManager when the Build-model job service lands.
            self.status.setText(f"{label}: {action()}")
            return True
        except Exception as error:  # owner-facing: every core refusal is shown, not raised
            self.status.setText(f"{label} failed: {error}")
            return False
        finally:
            QGuiApplication.restoreOverrideCursor()
            self._sync_buttons()

    def _show(self, service: ViewportService) -> None:
        self.viewer.service = service
        self.viewer.fit()
        self.viewer.status.setText(
            "Drag to orbit, right-drag to pan, wheel to zoom. "
            "Units: mm_unverified after scale, reconstruction units before."
        )

    def _project_id(self) -> str:
        current = getattr(self.project_manager, "current", None)
        return current.project_id if current is not None else str(uuid.UUID(int=0))

    # ------------------------------------------------------------ steps

    def open_model(self) -> None:
        chosen = self._choose_file(self)
        if chosen:
            self.load(Path(chosen))

    def show_part(self, label: str | None, has_cloud: bool = True) -> None:
        """Name the selected project part on the load button (None: latest build)."""
        self.part_label = label
        if label is None:
            text = tr("Use latest project build")
        elif has_cloud:
            text = tr("Use selected part: {part}").format(part=label)
        else:
            text = tr("{part}: no scan yet").format(part=label)
        self.latest_button.setText(text)
        self.latest_button.setEnabled(label is None or has_cloud)

    def use_latest_build(self, path: Path | None = None) -> bool:
        """Load ``path`` (a just-finished build) or the newest build in the open project."""

        layout = getattr(self.project_manager, "layout", None)
        part = None
        if path is None and self.part_label is not None and self.part_provider is not None:
            path = self.part_provider()
            if path is None:  # never fall back to another build behind the owner's back
                self.status.setText(tr("{part}: no scan yet").format(part=self.part_label))
                return False
            part = self.part_key if self.part_key in ("closure", "body") else None
        if path is None and layout is not None:
            path = md.latest_built_model(layout.root)
        if path is None:
            self.status.setText("No built model in this project yet: run Build model first.")
            return False
        if self.model is not None and self.model.path == Path(path):
            self.loaded_part = part
            return True
        loaded = self.load(Path(path))
        if loaded:
            self.loaded_part = part  # its Design Model becomes that part's (PL-0487)
        return loaded

    def load(self, path: Path) -> bool:
        def action() -> str:
            self.loaded_part = None
            self.model = md.load_model(path)
            companion = md.companion_mesh_path(path) if self.model.triangles is None else None
            self.part_record = self._combined_part(path)
            if self.part_record is not None:
                companion = self._part_mesh(self.part_record)
            self.mesh_model = self.model if self.model.triangles is not None else None
            self._companion = companion
            self.workspace = md.find_colmap_workspace(path)
            self.cameras = md.read_colmap_cameras(self.workspace[1]) if self.workspace else ()
            self.isolation = self.scale = self.frame = self.measurements = None
            self.scan_master = self.design = None
            stride = max(1, len(self.model.points) // POINT_DISPLAY_BUDGET)
            service = ViewportService(self.viewer.service.adapter)
            service.add_geometry(
                "model",
                SceneObjectKind.SCAN_MESH,
                PointCloudGeometry(
                    tuple(map(tuple, self.model.points[::stride].tolist())),
                    _colors(
                        None if self.model.colors is None else self.model.colors[::stride],
                        len(self.model.points[::stride]),
                    ),
                ),
            )
            self._show(service)
            kind = "mesh" if self.model.triangles is not None else "point cloud"
            cams = (
                f"{len(self.cameras)} COLMAP cameras" if self.cameras else "no camera poses found"
            )
            self.results.setText(
                f"{path.name}: {len(self.model.points):,}-point {kind}, {cams}. "
                "Units: reconstruction units until scale is set."
            )
            self.settings.setValue(self._last_model_key(), str(path))
            self.offered_build = None
            self.newer_button.hide()
            return "loaded"

        return self._run("Open", action)

    def _combined_part(self, path: Path) -> dict[str, Any] | None:
        """The project's Combine-part record whose merged cloud is ``path`` (PL-0485)."""
        manager, layout = self.project_manager, getattr(self.project_manager, "layout", None)
        if layout is None or not hasattr(manager, "part_merges"):
            return None
        for record in manager.part_merges().values():
            artifact = record.get("artifact_path")
            if record.get("status") == "combined" and isinstance(artifact, str):
                if os.path.normcase(str(layout.root / artifact)) == os.path.normcase(str(path)):
                    return record
        return None

    def _part_mesh(self, record: dict[str, Any]) -> Path | None:
        layout = self.project_manager.layout
        artifact = record.get("mesh_artifact_path")
        if not isinstance(artifact, str):
            return None
        mesh = layout.path("derived", artifact.removeprefix("derived/"))
        if not mesh.is_file():
            raise md.MeasureDesignError(
                "the part surface mesh is missing or changed; combine again"
            )
        return mesh

    def isolate(self) -> None:
        model = self.model
        if model is None:
            return

        record = self.part_record

        def action() -> str:
            self.isolation = isolation = (
                md.isolate_object(model, self.cameras)
                if record is None
                else md.isolate_in_mat_frame(model)
            )
            self.scale = self.frame = self.measurements = None
            upright = md.upright_matrix(isolation)
            points = model.points[isolation.object_indices] @ upright[:3, :3].T + upright[:3, 3]
            service = ViewportService(self.viewer.service.adapter)
            colors = None if model.colors is None else model.colors[isolation.object_indices]
            service.add_geometry(
                "object",
                SceneObjectKind.SCAN_MESH,
                PointCloudGeometry(_display(points), _colors(colors, len(points))),
            )
            self._show(service)
            bottom = isolation.center
            top = isolation.center + isolation.normal * isolation.top
            self.point_a.setText(", ".join(f"{value:.6g}" for value in bottom))
            self.point_b.setText(", ".join(f"{value:.6g}" for value in top))
            self.results.setText(
                f"Object only: {len(isolation.object_indices):,} points kept of "
                f"{len(model.points):,}. Method {isolation.method}: "
                + "; ".join(isolation.notes)
                + ". Manual points prefilled with the object's base and top along its axis."
            )
            if record is not None:  # combined part: already mm, scale from its source builds
                note = self.results.text()
                self._set_scale(md.part_combine_scale(model, record))
                badge = (
                    "\nOWNER_CONFIRMED_UNVERIFIED: this part was combined on the owner's "
                    "confirmation although its scans disagree; a Scan Master or Design Model "
                    "built from it stays unverified."
                    if record.get("verification") == "OWNER_CONFIRMED_UNVERIFIED"
                    else ""
                )
                self.results.setText(f"{note}\n{self.results.text()}{badge}")
            return "isolated"

        self._run("Isolate", action)

    def _set_scale(self, scale: md.ScaleResult) -> str:
        assert self.model is not None and self.isolation is not None
        self.scale = scale
        self.frame = md.build_frame(
            self.model, self.isolation, scale, project_id=self._project_id()
        )
        self.measurements = None
        points = self.frame.apply(self.model.points[self.isolation.object_indices])
        service = ViewportService(self.viewer.service.adapter)
        colors = (
            None if self.model.colors is None else self.model.colors[self.isolation.object_indices]
        )
        service.add_geometry(
            "object",
            SceneObjectKind.SCAN_MESH,
            PointCloudGeometry(_display(points), _colors(colors, len(points))),
        )
        self._show(service)
        relative = 100 * scale.uncertainty / scale.mm_per_unit
        self.results.setText(
            f"Scale source: {scale.source} — {scale.mm_per_unit:.4g} mm per unit "
            f"(± {relative:.2g} %), {scale.details}. Upright: base-plane normal is +Z. "
            "State METRIC_UNVERIFIED (no physical validation)."
        )
        return scale.source

    def scale_from_markers(self) -> None:
        model, isolation, workspace = self.model, self.isolation, self.workspace
        if model is None or isolation is None or workspace is None:
            return

        def action() -> str:
            revision = "camera-" + md._sha256_file(workspace[1] / "images.bin")[:40]
            return self._set_scale(
                md.estimate_marker_scale(
                    model,
                    isolation,
                    self.cameras,
                    workspace[0],
                    revision,
                    print_correction=self.bar_mm.value() / md.MAT_REFERENCE_BAR_MM,
                )
            )

        self._run("Marker scale", action)

    def scale_manually(self) -> None:
        model = self.model
        if model is None or self.isolation is None:
            return

        def parse(text: str) -> tuple[float, float, float]:
            values = [float(item) for item in re.split(r"[,\s]+", text.strip()) if item]
            if len(values) != 3:
                raise md.MeasureDesignError("points need three numbers: x, y, z")
            return values[0], values[1], values[2]

        self._run(
            "Manual scale",
            lambda: self._set_scale(
                md.manual_scale(
                    model,
                    parse(self.point_a.text()),
                    parse(self.point_b.text()),
                    self.known_mm.value(),
                )
            ),
        )

    def measure(self) -> None:
        frame, model, isolation = self.frame, self.model, self.isolation
        if frame is None or model is None or isolation is None:
            return

        def action() -> str:
            self.measurements = result = md.measure(frame, model, isolation)
            lines = [f"{item.name.replace('_', ' ')}: {item.display}" for item in result.dimensions]
            lines.append(
                f"bounding box W×D×H: {result.bounding.width:.1f} × {result.bounding.depth:.1f} × "
                f"{result.bounding.height:.1f} mm_unverified"
            )
            lines.extend(result.notes)
            lines.append(f"scale source: {frame.scale.source}; METRIC_UNVERIFIED")
            self.results.setText("\n".join(lines))
            return "measured"

        self._run("Measure", action)

    def export_report(self) -> None:
        if self.measurements is None or self.frame is None:
            return
        target = self._choose_save(self, "dimension-report.json")
        if not target:
            return
        measurements, frame = self.measurements, self.frame

        def action() -> str:
            current = getattr(self.project_manager, "current", None)
            report = md.dimension_report(
                measurements,
                frame,
                project_id=self._project_id(),
                project_revision=f"r{current.revision}" if current is not None else "r0",
            )
            json_path, markdown_path = md.write_dimension_report(report, Path(target))
            return f"wrote {json_path.name} and {markdown_path.name}"

        self._run("Report", action)

    def promotion_request(self, actor_id: str, reason: str) -> ScanMasterPromotionRequest | None:
        """Shell ``scan_master_request_provider``: the cleaned object selection."""

        if self.model is None or self.isolation is None or self.frame is None:
            return None
        if self.mesh_model is None:
            companion = self._companion
            if companion is None:
                raise md.MeasureDesignError("promotion needs a mesh; open the built OBJ/PLY mesh")
            self.mesh_model = md.load_model(companion)
            record = self.part_record
            if record is not None and self.mesh_model.sha256 != record.get("mesh_sha256"):
                self.mesh_model = None
                raise md.MeasureDesignError(
                    "the part surface mesh changed on disk; combine the part again"
                )
        if self.frame.geometry.project_id != self._project_id():
            self.frame = md.build_frame(
                self.model, self.isolation, self.frame.scale, project_id=self._project_id()
            )
        return md.promotion_request(
            project_id=self._project_id(),
            model=self.model,
            mesh_model=self.mesh_model,
            isolation=self.isolation,
            frame=self.frame,
            actor_id=actor_id,
            reason=reason,
            part_record=self.part_record,
        )

    def promote(self) -> None:
        manager = self.project_manager
        if manager is None or getattr(manager, "current", None) is None:
            self.status.setText("Promote: open or create a project first (File menu).")
            return

        def action() -> str:
            request = self.promotion_request(self.actor.text().strip(), self.reason.text().strip())
            if request is None:
                raise md.MeasureDesignError("isolate and scale the object first")
            assert self.model is not None and self.frame is not None
            # PL-0487: the cloud -> Scan Master (= Design Model) frame, so placed parts can be
            # composed into Design Model frames later.
            source_frame = {
                "source_cloud_sha256": self.model.sha256,
                "source_frame": (
                    "part_combine_mat_frame_mm"
                    if self.part_record is not None
                    else "reconstruction_units"
                ),
                "part": self.loaded_part,
                "source_to_scan_master": [float(v) for v in self.frame.matrix.ravel()],
            }
            revision = ScanMasterPromotionAction(manager).promote(
                request,
                expected_project_revision=manager.current.revision,
                source_frame=source_frame,
            )
            self.scan_master = revision
            self._show_scan_master()
            return (
                f"Scan Master {revision.revision_id[:24]}… selected; "
                f"{len(revision.mesh.triangles):,} triangles; DEFERRED_OWNER_VALIDATION"
            )

        self._run("Promote", action)

    def _show_scan_master(self, design: MeshGeometry | None = None) -> None:
        service = ViewportService(self.viewer.service.adapter)
        if self.measurements is not None:
            points = self.measurements.points_mm[
                :: max(1, len(self.measurements.points_mm) // POINT_DISPLAY_BUDGET)
            ]
            service.add_geometry(
                "scan", SceneObjectKind.SCAN_MESH, PointCloudGeometry(_display(points))
            )
        elif self.scan_master is not None:
            vertices = np.asarray(self.scan_master.mesh.vertices)
            service.add_geometry(
                "scan", SceneObjectKind.SCAN_MESH, PointCloudGeometry(_display(vertices))
            )
        if design is not None:
            service.add_geometry(_DESIGN_COLOR, SceneObjectKind.DESIGN_MODEL, design)
            service.select(_DESIGN_COLOR)
        self._show(service)

    def _design_geometry(self) -> MeshGeometry:
        assert self.design is not None
        mesh = self.design.preview_mesh()
        return MeshGeometry(_display(np.asarray(mesh.vertices)), mesh.triangles)

    def fit_design(self) -> None:
        scan_master = self.scan_master
        if scan_master is None:
            return

        def action() -> str:
            self.design = md.fit_design_model(
                scan_master,
                actor_id=self.actor.text().strip() or "owner",
                owner_review=self.owner_review.isChecked(),
            )
            self.height_mm.setValue(self.design.height)
            self.diameter_mm.setValue(self.design.diameter)
            self._show_scan_master(self._design_geometry())
            self._mark_dirty()
            notes = "; ".join(self.design.notes)
            return (
                f"Design Model {self.design.model.revision_id[:26]}… fitted "
                f"(H {self.design.height:.2f}, Ø {self.design.diameter:.2f} mm_unverified)"
                + (f"; {notes}" if notes else "")
                + ". Overlay: yellow = Design Model, cyan = scan."
            )

        self._run("Fit Design Model", action)

    def apply_dimensions(self) -> None:
        design = self.design
        if design is None:
            return

        def action() -> str:
            self.design = md.edit_dimensions(
                design,
                height=self.height_mm.value(),
                diameter=self.diameter_mm.value(),
                actor_id=self.actor.text().strip() or "owner",
            )
            self._show_scan_master(self._design_geometry())
            self._mark_dirty()
            return (
                f"revision {self.design.model.revision_id[:26]}… "
                f"H {self.design.height:.2f} mm, Ø {self.design.diameter:.2f} mm; Scan Master unchanged"
            )

        self._run("Edit dimensions", action)

    def save_design(self) -> None:
        design = self.design
        if design is None:
            return
        name = design.model.revision_id.split(":")[-1][:32] + ".json"
        manager = self.project_manager

        def action() -> str:
            if getattr(manager, "current", None) is not None:
                # Project authority writes derived/design_model/<id>.json create-only and
                # selects it as the project's current Design Model (lineage: Scan Master).
                part = self.loaded_part
                record = manager.persist_design_model_revision(
                    design.as_dict(),
                    expected_revision=manager.current.revision,
                    **({"part": part} if part else {}),
                )
                target = manager.layout.root / record["artifact_path"]
                note = "now the project's current Design Model"
                if part:
                    note += tr(" and the {part} Design Model").format(part=tr(part.capitalize()))
            else:
                chosen = self._choose_save(self, f"design-model-{name}")
                if not chosen:
                    return "cancelled"
                target = Path(chosen)
                with target.open("x", encoding="utf-8") as handle:  # append-only
                    json.dump(design.as_dict(), handle, sort_keys=True, indent=1, default=str)
                note = "no project open: file only, not in project authority"
            self.saved_design_path = target
            self.dirty = False
            self.draft_saved.emit()
            return f"saved {target}; {note}"

        self._run("Save Design Model", action)
