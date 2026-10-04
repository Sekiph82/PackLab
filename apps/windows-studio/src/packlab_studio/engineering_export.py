"""Source-explicit Scan Mesh and editable Design Model export workflow for Studio."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from packlab_core.cad_brep import CadBrepRepresentationRevision
from packlab_core.cad_mesh_export import export_design_model_obj_glb
from packlab_core.cad_preview import CadPreviewMeshRevision
from packlab_core.cad_step_export import export_design_model_step
from packlab_core.cad_stl_export import export_design_model_stl
from packlab_core.design_model import DesignModelRevision
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision


class ExportSourceKind(StrEnum):
    SCAN_MESH = "scan_mesh"
    DESIGN_MODEL = "design_model"


@dataclass(frozen=True, slots=True)
class DesignModelExportSource:
    """Exact current Design Model and derived CAD inputs supplied by Studio authority."""

    model: DesignModelRevision
    representation: CadBrepRepresentationRevision
    preview: CadPreviewMeshRevision
    part_name: str


DestinationProvider = Callable[[ExportSourceKind, Path], str | Path | None]
DesignModelSourceProvider = Callable[[], DesignModelExportSource | None]


class EngineeringExportView(QWidget):
    """Export UI that keeps captured Scan Mesh and editable Design Model paths distinct."""

    SCAN_FORMATS = (("PLY", "ply"), ("OBJ", "obj"), ("GLB", "glb"))
    DESIGN_FORMATS = (
        ("STEP", "step"),
        ("STL", "stl"),
        ("OBJ + GLB", "obj_glb"),
    )

    def __init__(
        self,
        project_manager: Any = None,
        *,
        design_model_source_provider: DesignModelSourceProvider | None = None,
        destination_provider: DestinationProvider | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("packlab.view.engineering-export")
        self.project_manager = project_manager
        self.design_model_source_provider = design_model_source_provider
        self.destination_provider = destination_provider

        self.source_selector = QComboBox(self)
        self.source_selector.setObjectName("packlab.export.source")
        self.source_selector.addItem("Scan Mesh / Scan Master", ExportSourceKind.SCAN_MESH.value)
        self.source_selector.addItem(
            "Editable Design Model / CAD", ExportSourceKind.DESIGN_MODEL.value
        )
        self.source_summary = QLabel(self)
        self.source_summary.setObjectName("packlab.export.source-summary")
        self.available_formats = QLabel(self)
        self.available_formats.setObjectName("packlab.export.available-formats")
        self.format_selector = QComboBox(self)
        self.format_selector.setObjectName("packlab.export.format")
        self.disclaimer = QLabel(
            "Exports are derived files. DEFERRED_OWNER_VALIDATION; physical accuracy, "
            "mold use, and manufacturing suitability are not established.",
            self,
        )
        self.disclaimer.setObjectName("packlab.export.physical-disclaimer")
        self.disclaimer.setWordWrap(True)
        self.export_button = QPushButton("Export selected source", self)
        self.export_button.setObjectName("packlab.export.run")
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setObjectName("packlab.export.cancel")
        self.status = QLabel("No export requested.", self)
        self.status.setObjectName("packlab.export.status")
        self.status.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Source type", self.source_selector)
        form.addRow("Selected authority", self.source_summary)
        form.addRow("Available formats", self.available_formats)
        form.addRow("Format", self.format_selector)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.disclaimer)
        layout.addWidget(self.export_button)
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.status)

        self.source_selector.currentIndexChanged.connect(self.refresh_source)
        self.export_button.clicked.connect(self.export_selected)
        self.cancel_button.clicked.connect(self.cancel_export)
        self.refresh_source()

    @property
    def selected_source_kind(self) -> ExportSourceKind:
        return ExportSourceKind(self.source_selector.currentData(Qt.ItemDataRole.UserRole))

    def refresh_source(self, *_args: object) -> None:
        source_kind = self.selected_source_kind
        formats: tuple[tuple[str, str], ...] = ()
        summary = ""
        if source_kind is ExportSourceKind.SCAN_MESH:
            source = self._scan_source()
            if source is None:
                summary = "No selected persisted Scan Master revision is available."
            else:
                manifest = source.manifest
                scale_state = _manifest_string(manifest, "scale_state", "unknown")
                unit = (
                    "mm_unverified"
                    if scale_state == ScaleState.METRIC_UNVERIFIED.value
                    else "reconstruction_units"
                )
                summary = (
                    "Authority: Scan Master (captured Scan Mesh); "
                    f"revision: {source.revision_id}; unit: {unit}; scale: {scale_state}; "
                    "physical validation: DEFERRED_OWNER_VALIDATION; mold use: not authorized."
                )
                formats = self.SCAN_FORMATS
        else:
            source = self._design_source()
            if source is None:
                self.source_summary.setText(
                    "No active Design Model source is connected. Select an exact Design Model, "
                    "CAD/BREP, and preview through the Studio design authority."
                )
                self.available_formats.setText("None")
                self.format_selector.clear()
                self.export_button.setEnabled(False)
                return
            model = source.model
            parent_id = (
                model.standalone_root.revision_id
                if model.standalone_root is not None
                else model.parent_binding_revision_id
            )
            summary = (
                f"Authority: editable Design Model ({model.parent_kind.value}, parent {parent_id}); "
                f"revision: {model.revision_id}; unit: {model.coordinate_unit}; "
                f"scale: {model.scale_state.value}; CAD/BREP: {source.representation.revision_id}; "
                "physical validation: DEFERRED_OWNER_VALIDATION; mold use: not authorized."
            )
            formats = self._design_formats_for(source)

        self.source_summary.setText(summary)
        self.available_formats.setText(", ".join(label for label, _value in formats) or "None")
        self.format_selector.clear()
        for label, value in formats:
            self.format_selector.addItem(label, value)
        self.export_button.setEnabled(source is not None and bool(formats))

    def cancel_export(self) -> None:
        self.status.setText("Export cancelled; no domain service was called.")

    def export_selected(self) -> None:
        self.refresh_source()
        if not self.export_button.isEnabled():
            self.status.setText("Export unavailable; select a valid source and format.")
            return
        source_kind = self.selected_source_kind
        format_value = self.format_selector.currentData(Qt.ItemDataRole.UserRole)
        if not isinstance(format_value, str):
            self.status.setText("Export unavailable; no format is selected.")
            return
        try:
            destination = self._choose_destination(source_kind)
            if destination is None:
                self.cancel_export()
                return
            if source_kind is ExportSourceKind.SCAN_MESH:
                revision = self._scan_source()
                if revision is None:
                    raise RuntimeError("selected Scan Master revision is unavailable")
                result = self.project_manager.export_selected_scan_master(
                    revision.revision_id,
                    destination_relative_dir=self._scan_relative_destination(destination, revision),
                    formats=(format_value,),
                )
            else:
                source = self._design_source()
                if source is None:
                    raise RuntimeError("active Design Model source is unavailable")
                result = self._export_design_model(source, format_value, destination)
        except Exception as error:
            self.status.setText(f"Export failed: {error}")
            return
        self.status.setText(f"Export complete: {result}")

    def _scan_source(self) -> ScanMasterRevision | None:
        if self.project_manager is None or self.project_manager.current is None:
            return None
        try:
            return self.project_manager.selected_scan_master_revision()
        except Exception:
            return None

    def _design_source(self) -> DesignModelExportSource | None:
        if self.design_model_source_provider is None:
            return None
        try:
            source = self.design_model_source_provider()
        except Exception:
            return None
        if not isinstance(source, DesignModelExportSource) or not self._design_source_is_exact(
            source
        ):
            return None
        return source

    @staticmethod
    def _design_source_is_exact(source: DesignModelExportSource) -> bool:
        model = source.model
        representation = source.representation
        preview = source.preview
        if not isinstance(model, DesignModelRevision):
            return False
        if not isinstance(representation, CadBrepRepresentationRevision):
            return False
        if not isinstance(preview, CadPreviewMeshRevision):
            return False
        expected_parent = (
            model.standalone_root.revision_id
            if model.standalone_root is not None
            else model.parent_binding_revision_id
        )
        unit_state_consistent = (
            model.scale_state is ScaleState.RELATIVE
            and model.coordinate_unit == "reconstruction_units"
        ) or (
            model.scale_state is ScaleState.METRIC_UNVERIFIED
            and model.coordinate_unit == "mm_unverified"
        )
        return (
            isinstance(source.part_name, str)
            and bool(source.part_name.strip())
            and unit_state_consistent
            and representation.source_design_model_revision_id == model.revision_id
            and representation.parent_kind is model.parent_kind
            and representation.parent_authority_revision_id == expected_parent
            and preview.source_design_model_revision_id == model.revision_id
            and preview.source_brep_revision_id == representation.revision_id
            and preview.parent_kind == model.parent_kind.value
            and preview.parent_authority_revision_id == expected_parent
            and representation.scale_state is model.scale_state
            and representation.coordinate_unit == model.coordinate_unit
            and preview.scale_state == model.scale_state.value
            and preview.coordinate_unit == model.coordinate_unit
            and representation.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
            and representation.mold_use_authorized is False
            and model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
            and model.mold_use_authorized is False
            and preview.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
            and preview.mold_use_authorized is False
        )

    @classmethod
    def _design_formats_for(cls, source: DesignModelExportSource) -> tuple[tuple[str, str], ...]:
        valid_mm = (
            source.model.scale_state is ScaleState.METRIC_UNVERIFIED
            and source.model.coordinate_unit == "mm_unverified"
        )
        return tuple(
            (label, value)
            for label, value in cls.DESIGN_FORMATS
            if value not in {"step", "stl"} or valid_mm
        )

    def _choose_destination(self, source_kind: ExportSourceKind) -> Path | None:
        project_layout = getattr(self.project_manager, "layout", None)
        initial = project_layout.path("export") if project_layout is not None else Path.cwd()
        if self.destination_provider is not None:
            selected = self.destination_provider(source_kind, initial)
        else:
            selected = QFileDialog.getExistingDirectory(
                self,
                "Choose export destination folder",
                str(initial),
                QFileDialog.Option.ShowDirsOnly,
            )
        if selected is None or not str(selected).strip():
            return None
        path = Path(selected)
        if not path.is_dir():
            raise RuntimeError("export destination must be an existing folder")
        resolved = path.resolve()
        layout = getattr(self.project_manager, "layout", None)
        if layout is not None:
            export_root = layout.path("export").resolve()
            try:
                resolved.relative_to(export_root)
            except ValueError as error:
                raise RuntimeError(
                    "engineering exports must stay under the project export folder"
                ) from error
        return resolved

    def _scan_relative_destination(self, destination: Path, revision: ScanMasterRevision) -> str:
        layout = getattr(self.project_manager, "layout", None)
        if layout is None:
            raise RuntimeError("open a project before exporting a Scan Master")
        project_root = layout.root.resolve()
        try:
            relative_parent = destination.relative_to(project_root)
        except ValueError as error:
            raise RuntimeError("Scan Mesh exports must stay inside the open project") from error
        if not relative_parent.parts or relative_parent.parts[0].casefold() != "export":
            raise RuntimeError("Scan Mesh exports must stay under the project export folder")
        digest = re.fullmatch(r"scan-master:([0-9a-f]{64})", revision.revision_id)
        if digest is None:
            raise RuntimeError("selected Scan Master revision identity is invalid")
        target = relative_parent / f"scan-master-{digest.group(1)[:12]}"
        return target.as_posix()

    def _export_design_model(
        self, source: DesignModelExportSource, format_value: str, destination: Path
    ) -> object:
        stem = _safe_stem(source.part_name, source.model.revision_id)
        if format_value == "step":
            return export_design_model_step(
                source.model,
                source.representation,
                destination / f"{stem}.step",
                part_name=source.part_name,
            )
        if format_value == "stl":
            return export_design_model_stl(
                source.model, source.representation, destination / f"{stem}.stl"
            )
        if format_value == "obj_glb":
            return export_design_model_obj_glb(
                source.model,
                source.representation,
                source.preview,
                destination / f"{stem}.obj",
                destination / f"{stem}.glb",
            )
        raise RuntimeError("unsupported Design Model export format")


def _manifest_string(manifest: dict[str, object], key: str, fallback: str) -> str:
    value = manifest.get(key)
    return value if isinstance(value, str) and value else fallback


def _safe_stem(part_name: str, revision_id: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", part_name).strip("._-")[:80]
    if stem:
        return stem
    digest = re.search(r"([0-9a-f]{12})$", revision_id)
    return f"design-model-{digest.group(1) if digest else 'export'}"


__all__ = [
    "DesignModelExportSource",
    "EngineeringExportView",
    "ExportSourceKind",
]
