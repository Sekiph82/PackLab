"""Package families route: caps/closures, jerrycan, trigger/pump, tube and sachet/pouch.

Every button calls ``package_families`` (which calls core); this widget only collects
parameters, shows the result and hands the selected part to the Exports page.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, cast

import numpy as np
from PySide6.QtCore import QCoreApplication, QEventLoop, Qt, Signal
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from packlab_core.closure_workflow import ClosureWorkflowHistory
from packlab_core.design_model import FeatureKind
from packlab_core.oval_section_fit import SLICE_COUNT

from . import package_families as pf
from .closure_workflow import ClosureWorkflowController
from .engineering_export import DesignModelExportSource
from .i18n import tr
from .jobs import JobManager, JobState
from .measure_view import _display
from .model_viewer import ModelViewerView
from .viewport import MeshGeometry, SceneObjectKind, ViewportRenderMode, ViewportService

CAPTURED = "captured"
STANDALONE = "standalone"


class PackageFamiliesView(QWidget):
    """Family selector, key-dimension editor, closure workflow and export hand-off."""

    export_requested = Signal()  # owner asked to export the selected part (Exports page)
    design_changed = Signal()
    oval_fit_finished = Signal(object)  # worker thread -> UI thread (queued)
    oval_fit_progress = Signal(object)

    def __init__(
        self,
        project_manager: Any = None,
        *,
        artwork_chooser: Callable[[QWidget], str] | None = None,
        job_manager: JobManager | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("packlab.view.package-families")
        self.project_manager = project_manager
        self.job_manager = job_manager
        # PL-0492: the oval section fit runs on a worker thread; the result shown to the
        # owner is kept (Scan Master revision id, Scan Master, fit) and Create reuses it.
        self._oval_fit: tuple[str, Any, Any] | None = None
        self._fit_thread: threading.Thread | None = None
        self._fit_cancel = threading.Event()
        self.oval_fit_finished.connect(self._oval_fit_done)
        self.oval_fit_progress.connect(self._oval_fit_step)
        self._choose_artwork = artwork_chooser or (
            lambda parent: QFileDialog.getOpenFileName(
                parent, "Artwork (SVG or PNG)", "", "Artwork (*.svg *.png)"
            )[0]
        )
        self.design: pf.FamilyDesign | None = None
        self.closure_history: ClosureWorkflowHistory | None = None
        self.export_active = False
        self.spins: dict[str, QDoubleSpinBox] = {}

        self.viewer = ModelViewerView()
        self.viewer.open_button.hide()
        self.viewer.reload_button.hide()
        self.closure_controller = ClosureWorkflowController(self.viewer.service)

        def button(text: str, name: str, slot: Callable[[], object]) -> QPushButton:
            widget = QPushButton(text)
            widget.setObjectName(f"packlab.families.{name}")
            widget.clicked.connect(slot)
            return widget

        self.family = QComboBox()
        self.family.setObjectName("packlab.families.family")
        for key, label in pf.FAMILIES.items():
            self.family.addItem(label, key)
        self.source = QComboBox()
        self.source.setObjectName("packlab.families.source")
        self.preset = QComboBox()
        self.preset.setObjectName("packlab.families.preset")
        self.actor = QLineEdit(os.environ.get("USERNAME") or os.environ.get("USER") or "owner")
        self.parameters_box = QGroupBox("Key dimensions (mm_unverified)")
        self.parameters_form = QFormLayout(self.parameters_box)
        self.create_button = button("Create Design Model", "create", self.create_design)
        self.apply_button = button(
            "Apply dimensions (new revision)", "apply", self.apply_dimensions
        )
        self.save_button = button("Save revision to project", "save", self.save_design)
        self.open_button = button(
            "Open the project's current Design Model", "open-current", self.open_current
        )
        # PL-0492: the oval fit classifies the body; the owner confirms it before Create.
        self.confirm_shape = QCheckBox(tr("Owner confirms the detected section shape"))
        self.confirm_shape.setObjectName("packlab.families.confirm-shape")
        self.cancel_fit_button = button("Cancel the section fit", "cancel-fit", self.cancel_fit)
        self.cancel_fit_button.hide()
        self.show_closure = QCheckBox("Show closure / head")
        self.show_closure.setObjectName("packlab.families.show-closure")
        self.show_closure.setChecked(True)
        self.show_closure.toggled.connect(self.set_closure_visible)
        self.replace_button = button(
            "Replace closure with the dimensions above", "replace-closure", self.replace_closure
        )
        self.undo_button = button("Undo closure replacement", "undo-closure", self.undo_closure)
        self.redo_button = button("Redo closure replacement", "redo-closure", self.redo_closure)
        self.artwork_button = button("Place artwork on the front…", "artwork", self.place_artwork)
        self.artwork_preview = QLabel("")
        self.artwork_preview.setObjectName("packlab.families.artwork-preview")
        self.part = QComboBox()
        self.part.setObjectName("packlab.families.export-part")
        self.part.currentIndexChanged.connect(lambda _index: self.design_changed.emit())
        self.export_button = button("Export selected part…", "export", self.request_export)
        self.details = QLabel("Choose a package family.")
        self.details.setObjectName("packlab.families.details")
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status = QLabel("")
        self.status.setObjectName("packlab.families.status")
        self.status.setWordWrap(True)
        self.busy = QProgressBar()
        self.busy.setObjectName("packlab.families.busy")
        self.busy.setRange(0, 0)  # indeterminate
        self.busy.setMaximumHeight(10)
        self.busy.hide()

        family_box = QGroupBox("Package family")
        family_form = QFormLayout(family_box)
        family_form.addRow("Family", self.family)
        family_form.addRow("Start from", self.source)
        family_form.addRow("Preset", self.preset)
        family_form.addRow("Actor", self.actor)
        family_form.addRow(self.confirm_shape)
        family_form.addRow(self.cancel_fit_button)
        closure_box = QGroupBox("Closure workflow")
        closure_form = QFormLayout(closure_box)
        closure_form.addRow(self.show_closure)
        closure_form.addRow(self.replace_button)
        closure_form.addRow(self.undo_button)
        closure_form.addRow(self.redo_button)
        output_box = QGroupBox("Save and export")
        output_form = QFormLayout(output_box)
        output_form.addRow(self.save_button)
        output_form.addRow("Part", self.part)
        output_form.addRow(self.export_button)
        output_form.addRow(self.artwork_button)
        output_form.addRow(self.artwork_preview)

        controls = QWidget()
        column = QVBoxLayout(controls)
        for widget in (
            family_box,
            self.parameters_box,
            self.create_button,
            self.apply_button,
            self.open_button,
            closure_box,
            output_box,
        ):
            column.addWidget(widget)
        column.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidget(controls)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(400)
        layout = QHBoxLayout(self)
        layout.addWidget(scroll)
        right = QVBoxLayout()
        right.addWidget(self.status)
        right.addWidget(self.busy)
        right.addWidget(self.viewer, 1)
        right.addWidget(self.details)
        layout.addLayout(right, 1)

        self.family.currentIndexChanged.connect(self._family_changed)
        self.preset.currentIndexChanged.connect(self._preset_changed)
        self.source.currentIndexChanged.connect(lambda _index: self._preset_changed())
        self._project_seen: str | None = None
        self._family_changed()
        if hasattr(project_manager, "add_listener"):
            project_manager.add_listener(lambda _metadata: self._project_changed())

    def _project_changed(self) -> None:
        """Reset on project switch; refill container-derived defaults until a design exists."""

        current = getattr(self.project_manager, "current", None)
        project_id = None if current is None else current.project_id
        if project_id != self._project_seen:
            self._project_seen = project_id
            self.design, self.closure_history, self.export_active = None, None, False
            self.part.clear()
            self.viewer.service = ViewportService(self.viewer.service.adapter)
            self.viewer.redraw()
            self.details.setText("Choose a package family.")
        if self._oval_fit is not None and self._selected_scan_master_id() != self._oval_fit[0]:
            self._oval_fit = None  # another Scan Master: the owner must see and confirm anew
            self.confirm_shape.setChecked(False)
        if self.design is None and current is not None:
            self._preset_changed()

    def _selected_scan_master_id(self) -> str | None:
        try:
            value = self.project_manager.selected_scan_master_revision_id()
        except Exception:
            return None
        return value if isinstance(value, str) else None

    # ------------------------------------------------------------------ helpers

    @property
    def family_key(self) -> str:
        return str(self.family.currentData())

    @property
    def captured(self) -> bool:
        return self.source.currentData() == CAPTURED

    def _actor(self) -> str:
        return self.actor.text().strip() or "owner"

    def values(self) -> dict[str, float]:
        return {name: spin.value() for name, spin in self.spins.items()}

    def _manager(self) -> Any:
        manager = self.project_manager
        if manager is None or getattr(manager, "current", None) is None:
            raise pf.PackageFamilyError("open a project first (File > New/Open project)")
        return manager

    def _run(self, label: str, action: Callable[[], str]) -> bool:
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        # F7: visible busy state before the (UI-thread) work starts; repaint once.
        self.status.setText(
            tr("{label}: working, this can take up to a minute…").format(label=label)
        )
        self.busy.show()
        QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        try:
            self.status.setText(f"{label}: {action()}")
            return True
        except Exception as error:  # owner-facing: core refusals are shown, not raised
            self.status.setText(f"{label} failed: {error}")
            return False
        finally:
            self.busy.hide()
            QGuiApplication.restoreOverrideCursor()
            self._sync()

    def _container_document(self) -> dict[str, Any]:
        selected = self._manager().selected_design_model()
        if selected is None:
            raise pf.PackageFamilyError(
                "no project Design Model yet: fit and save the container in Measure & Design"
            )
        return selected[1]

    def _family_changed(self, *_args: object) -> None:
        family = self.family_key
        self.status.clear()  # F7: no stale message from the previous family
        self.source.blockSignals(True)
        self.source.clear()
        if family not in pf.STANDALONE_ONLY:
            self.source.addItem("Selected Scan Master / Design Model (captured)", CAPTURED)
        if family not in pf.CAPTURED_ONLY:
            self.source.addItem("Preset / parameters (standalone, no scan)", STANDALONE)
        self.source.setCurrentIndex(self.source.count() - 1 if family != "closure" else 0)
        self.source.blockSignals(False)
        self.preset.blockSignals(True)
        self.preset.clear()
        for name in pf.PRESETS[family]:
            self.preset.addItem(name, name)  # data = logic key; text may be translated
        self.preset.blockSignals(False)
        while self.parameters_form.rowCount():
            self.parameters_form.removeRow(0)
        self.spins = {}
        for name, label in pf.PARAMETERS[family]:
            spin = QDoubleSpinBox()
            spin.setObjectName(f"packlab.families.param.{name}")
            spin.setRange(0.0 if name == "thread_starts" else 0.1, 2000.0)
            spin.setDecimals(0 if name == "thread_starts" else 2)
            spin.setSuffix("" if name == "thread_starts" else " mm")
            self.spins[name] = spin
            self.parameters_form.addRow(tr(label), spin)
        self.confirm_shape.setVisible(family == "oval_bottle")
        self.confirm_shape.setChecked(False)
        self._oval_fit = None
        self._preset_changed()

    def _preset_key(self) -> str:
        data = self.preset.currentData()
        return data if isinstance(data, str) else self.preset.currentText()

    def _preset_changed(self, *_args: object) -> None:
        family = self.family_key
        values: dict[str, Any] = pf.default_parameters(family, self._preset_key())
        if family == "closure":
            try:
                _model, context = pf.container_context(self._container_document())
                values = pf.closure_defaults(context, self._preset_key())
            except Exception as error:
                self.status.setText(f"Closure: {error}")
        for name, spin in self.spins.items():
            if name in values:
                spin.setValue(float(values[name]))
        self._sync()

    def _sync(self) -> None:
        design = self.design
        closure = design is not None and design.family == "closure"
        self.apply_button.setEnabled(design is not None and design.family == self.family_key)
        self.save_button.setEnabled(design is not None)
        self.export_button.setEnabled(design is not None and bool(design.parts))
        self.replace_button.setEnabled(closure)
        history = self.closure_history
        self.undo_button.setEnabled(closure and history is not None and history.can_undo)
        self.redo_button.setEnabled(closure and history is not None and history.can_redo)
        self.artwork_button.setEnabled(design is not None and design.family == "pouch")
        for spin in self.spins.values():
            spin.setEnabled(not (self.family_key == "jerrycan" and self.captured))

    # ------------------------------------------------------------------ display

    def _show(self, design: pf.FamilyDesign) -> None:
        service = ViewportService(self.viewer.service.adapter)
        if design.parts:
            for part in design.parts:
                mesh = part.preview.mesh
                service.add_geometry(
                    part.name,
                    SceneObjectKind.CAP if part.is_cap else SceneObjectKind.DESIGN_MODEL,
                    MeshGeometry(_display(np.asarray(mesh.vertices)), mesh.triangles),
                )
            caps = [part.name for part in design.parts if part.is_cap]
            service.select(caps[0] if caps else design.parts[0].name)
        elif design.proxy_mesh is not None:
            mesh = design.proxy_mesh
            service.add_geometry(
                "pouch",
                SceneObjectKind.DESIGN_MODEL,
                MeshGeometry(_display(np.asarray(mesh.vertices)), mesh.triangles),
            )
        service.set_render_mode(ViewportRenderMode.SHADED)  # no wireframe look (F7)
        self.viewer.service = service
        self.closure_controller = ClosureWorkflowController(service)
        self.viewer.fit()
        self.viewer.status.setText(
            "Drag to orbit, right-drag to pan, wheel to zoom. Yellow = closure/head, "
            "cyan = container/body. Units: mm_unverified."
        )
        if not self.show_closure.isChecked():
            self.set_closure_visible(False)

    def _adopt(self, design: pf.FamilyDesign, *, reset_history: bool = True) -> None:
        self.design = design
        self.export_active = True
        if design.family == "closure" and (reset_history or self.closure_history is None):
            self.closure_history = ClosureWorkflowHistory(design.model)
        elif design.family != "closure":
            self.closure_history = None
        self.part.blockSignals(True)
        self.part.clear()
        for part in design.parts:
            self.part.addItem(part.name, part.name)
        self.part.blockSignals(False)
        index = self.family.findData(design.family)
        if index >= 0 and index != self.family.currentIndex():
            self.family.blockSignals(True)
            self.family.setCurrentIndex(index)
            self.family.blockSignals(False)
            self._family_changed()
        for name, spin in self.spins.items():
            value = design.parameters.get(name)
            if isinstance(value, (int, float)):
                spin.setValue(float(value))
        self._show(design)
        self.details.setText(
            pf.describe(design) + " Limits: " + "; ".join(pf.LIMITATIONS[design.family]) + "."
        )
        self.design_changed.emit()
        self._sync()

    def yield_export(self) -> None:
        self.export_active = False

    def export_source(self) -> DesignModelExportSource | None:
        design = self.design
        if design is None or not self.export_active:
            return None
        return design.export_source(str(self.part.currentData()))

    # ------------------------------------------------------------------ actions

    def create_design(self) -> None:
        if self.family_key == "oval_bottle" and self.captured:
            self._create_oval()
            return

        def action() -> str:
            family, preset, actor = self.family_key, self._preset_key(), self._actor()
            manager = self._manager()
            if family == "closure":
                design = pf.create_closure(
                    self._container_document(), self.values(), preset=preset, actor_id=actor
                )
            elif self.captured:
                scan_master = manager.selected_scan_master_revision()
                if scan_master is None:
                    raise pf.PackageFamilyError("no selected Scan Master in this project")
                if family == "jerrycan":
                    design = pf.fit_jerrycan_on_scan_master(scan_master, actor_id=actor)
                else:
                    design = pf.create_tube_on_scan_master(
                        scan_master, self.values(), preset=preset, actor_id=actor
                    )
            else:
                design = pf.create_standalone(
                    family,
                    self.values(),
                    project_id=manager.current.project_id,
                    preset=preset,
                    actor_id=actor,
                )
            self._adopt(design)
            return f"created {design.model.revision_id[:34]}… ({design.provenance}); not saved yet"

        self._run("Create", action)

    # ------------------------------------------------------------------ oval fit (PL-0492)

    def _create_oval(self) -> None:
        """Create from the fit the owner saw; without one, run the fit in the background."""
        if self._fit_thread is not None and self._fit_thread.is_alive():
            self.status.setText(tr("Create: the section fit is still running."))
            return
        try:
            manager = self._manager()
            revision_id = manager.selected_scan_master_revision_id()
            if revision_id is None:
                raise pf.PackageFamilyError("no selected Scan Master in this project")
            cached = self._oval_fit
            if cached is not None and cached[0] == revision_id:
                scan_master, fit = cached[1], cached[2]
                self._run("Create", lambda: self._adopt_oval(scan_master, fit))
                return
            scan_master = manager.selected_scan_master_revision()
        except Exception as error:
            self.status.setText(f"Create failed: {error}")
            return
        self._oval_fit = None
        self._fit_cancel.clear()
        job_id = self._fit_job_start()
        self.busy.show()
        self.cancel_fit_button.show()
        self.create_button.setEnabled(False)
        self.status.setText(tr("Create: fitting the oval sections in the background…"))
        cancel = self._fit_cancel

        def progress(done: int) -> None:
            if cancel.is_set():
                raise _FitCancelled
            self.oval_fit_progress.emit((job_id, done))

        def work() -> None:
            try:
                fit = pf.oval_section_fit(scan_master, progress=progress)
                self.oval_fit_finished.emit((job_id, revision_id, scan_master, fit, None))
            except Exception as error:  # reported on the UI thread
                self.oval_fit_finished.emit((job_id, revision_id, scan_master, None, error))

        self._fit_thread = threading.Thread(target=work, name="packlab-oval-fit", daemon=True)
        self._fit_thread.start()

    def _adopt_oval(self, scan_master: Any, fit: Any) -> str:
        design = pf.fit_oval_bottle_on_scan_master(
            scan_master,
            actor_id=self._actor(),
            owner_confirmed=self.confirm_shape.isChecked(),
            fit=fit,
        )
        self._adopt(design)
        return f"created {design.model.revision_id[:34]}… ({design.provenance}); not saved yet"

    def _fit_job_start(self) -> str | None:
        manager = self.job_manager
        if manager is None:
            return None
        job = manager.create("Oval / flat bottle section fit", "oval-section-fit")
        cancel = self._fit_cancel

        def hook() -> bool:
            cancel.set()
            return False  # CANCELLING until the worker reports back

        manager.register_cancel_hook(job.job_id, hook)
        manager.start(job.job_id)
        return job.job_id

    def _oval_fit_step(self, payload: object) -> None:
        job_id, done = cast(tuple[str | None, int], payload)
        fraction = min(0.95, done / (2.0 * SLICE_COUNT))
        self.busy.setRange(0, 100)
        self.busy.setValue(round(100 * fraction))
        manager = self.job_manager
        if manager is not None and job_id is not None:
            job = manager.get(job_id)
            if job.state in {JobState.RUNNING, JobState.CANCELLING} and fraction >= job.progress:
                manager.update_progress(job_id, fraction, f"{done} height slices fitted")

    def _oval_fit_done(self, payload: object) -> None:
        job_id, revision_id, scan_master, fit, error = cast(
            tuple[str | None, str, Any, Any, Exception | None], payload
        )
        self.busy.hide()
        self.busy.setRange(0, 0)
        self.cancel_fit_button.hide()
        self.create_button.setEnabled(True)
        manager = self.job_manager
        if isinstance(error, _FitCancelled):
            if manager is not None and job_id is not None:
                manager.finish_cancel(job_id)
            self.status.setText(tr("Create: the section fit was cancelled."))
            return
        if error is not None:
            if manager is not None and job_id is not None:
                manager.fail(job_id, str(error))
            self.status.setText(f"Create failed: {error}")
            return
        if manager is not None and job_id is not None:
            manager.succeed(job_id, f"{fit.classification.value} section fit")
        if self.family_key != "oval_bottle" or self._selected_scan_master_id() != revision_id:
            self.status.setText(tr("Create: the selection changed during the fit; press Create."))
            return
        self._oval_fit = (revision_id, scan_master, fit)
        self.confirm_shape.setChecked(False)  # the owner confirms the shape shown below
        self._run("Create", lambda: self._adopt_oval(scan_master, fit))

    def cancel_fit(self) -> None:
        if self._fit_thread is not None and self._fit_thread.is_alive():
            self._fit_cancel.set()
            self.status.setText(tr("Create: cancelling the section fit…"))

    def wait_for_fit(self, timeout: float | None = None) -> None:
        """Join the fit worker and deliver its queued result (tests)."""
        if self._fit_thread is not None:
            self._fit_thread.join(timeout)
        QCoreApplication.processEvents()

    def apply_dimensions(self) -> None:
        design = self.design
        if design is None:
            return

        def action() -> str:
            updated = pf.edit(design, self.values(), actor_id=self._actor())
            self._adopt(updated)
            return (
                f"revision {updated.model.revision_id[:34]}… "
                f"(previous {str(updated.model.previous_revision_id)[:30]}…); not saved yet"
            )

        self._run("Apply dimensions", action)

    def save_design(self) -> None:
        design = self.design
        if design is None:
            return

        def action() -> str:
            manager = self._manager()
            record = manager.persist_design_model_revision(
                design.as_dict(), expected_revision=manager.current.revision
            )
            return (
                f"saved {record['artifact_path']} as the project's current Design Model "
                f"({record.get('parent_kind')})"
            )

        self._run("Save", action)

    def open_current(self) -> None:
        def action() -> str:
            document = self._container_document()
            if "package_family_workflow" not in document:
                index = self.family.findData("closure")
                self.family.setCurrentIndex(index)
                self._preset_changed()
                return (
                    "the current Design Model is a fitted container; closure dimensions were "
                    "filled from it — press Create to add a cap"
                )
            design = pf.load_family_document(document)
            self._adopt(design)
            return f"opened {design.model.revision_id[:34]}… ({design.family})"

        self._run("Open", action)

    def set_closure_visible(self, visible: bool) -> None:
        design = self.design
        if design is None:
            return
        for part in design.parts:
            if part.is_cap:
                # ClosureWorkflowController refuses anything that is not a CAP scene object.
                self.closure_controller.set_visible(part.name, visible)
        self.viewer.redraw()

    def replace_closure(self) -> None:
        design = self.design
        history = self.closure_history
        if design is None or design.family != "closure" or history is None:
            return

        def action() -> str:
            scan_master = self._manager().selected_scan_master_revision()
            if scan_master is None:
                raise pf.PackageFamilyError("no selected Scan Master in this project")
            actor = self._actor()
            cap_id, cap_parameter, _values = pf.current_cap(design)
            base, new_cap, new_parameter = pf.replacement_base(
                design, self.values(), actor_id=actor
            )
            neck = next(
                item.feature_id for item in base.features if item.feature_kind is FeatureKind.NECK
            )
            mating = pf.closure_mating_references(
                scan_master,
                base,
                neck,
                new_cap,
                float(self.spins["closure_line"].value()),
                actor_id=actor,
            )
            result = self.closure_controller.replace(
                scan_master,
                history,
                base,
                mating,
                current_closure_feature_id=cap_id,
                replacement_closure_feature_id=new_cap,
                current_closure_parameter_ids=(cap_parameter,),
                replacement_closure_parameter_ids=(new_parameter,),
                expected_scan_master_revision_id=scan_master.revision_id,
                expected_current_model_revision_id=design.model.revision_id,
                expected_replacement_base_revision_id=base.revision_id,
                actor_id=actor,
                reason="Replace the closure from the Package families page.",
                created_at_utc=_now(),
            )
            self.closure_history = result.history
            self._adopt(
                pf.adopt_model(
                    design, result.model, extra={"closure_replacement": result.as_dict()}
                ),
                reset_history=False,
            )
            return f"closure replaced; revision {result.model.revision_id[:34]}…"

        self._run("Replace closure", action)

    def _closure_step(self, label: str, step: Callable[..., ClosureWorkflowHistory]) -> None:
        design = self.design
        history = self.closure_history
        if design is None or history is None:
            return

        def action() -> str:
            updated = step(history, actor_id=self._actor(), created_at_utc=_now())
            self.closure_history = updated
            self._adopt(pf.adopt_model(design, updated.current_revision), reset_history=False)
            return f"revision {updated.current_revision.revision_id[:34]}…"

        self._run(label, action)

    def undo_closure(self) -> None:
        self._closure_step("Undo closure replacement", self.closure_controller.undo)

    def redo_closure(self) -> None:
        self._closure_step("Redo closure replacement", self.closure_controller.redo)

    def place_artwork(self) -> None:
        design = self.design
        if design is None:
            return
        chosen = self._choose_artwork(self)
        if not chosen:
            return

        def action() -> str:
            updated = pf.attach_pouch_artwork(design, chosen, actor_id=self._actor())
            self._adopt(updated)
            pixmap = QPixmap(chosen)
            if not pixmap.isNull():
                self.artwork_preview.setPixmap(pixmap.scaledToWidth(220))
            asset = updated.extra["artwork"]["asset"]
            return (
                f"artwork {str(asset.get('content_sha256', ''))[:12]}… pinned to the front panel "
                f"centre; revision {updated.model.revision_id[:30]}…"
            )

        self._run("Artwork", action)

    def request_export(self) -> None:
        if self.export_source() is None:
            self.status.setText(
                "Export: create or open a family Design Model with a BREP part first."
            )
            return
        self.export_active = True
        self.export_requested.emit()


class _FitCancelled(Exception):
    """Raised from the fit progress callback when the owner cancels."""


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = ["PackageFamiliesView"]
