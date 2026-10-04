"""Deterministic, millimetre-labelled STEP export for one validated CAD solid."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import tempfile
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .cad_adapter import _shape_for_handle, probe_cad_runtime
from .cad_brep import CadBrepRepresentationRevision
from .cad_feature_map import map_design_model_features_to_brep
from .cad_validation import validate_cad_brep
from .design_model import DesignModelRevision
from .reconstruction import ScaleState

CAD_STEP_EXPORT_CONTRACT = "packlab.cad-step-export.v1"
_STEP_EXPORT_LOCK = threading.RLock()


class CadStepExportError(ValueError):
    """Raised when a BREP cannot be exported with explicit mm_unverified semantics."""


@dataclass(frozen=True, slots=True)
class CadStepExportRevision:
    export_id: str
    artifact_sha256: str
    artifact_size_bytes: int
    part_name: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    source_operation_id: str
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    binding_package: str
    binding_version: str
    kernel_version: str
    encoded_step_unit: str
    reopened_step_length_units: tuple[str, ...]
    feature_mapping: tuple[dict[str, object], ...]
    contract: str = CAD_STEP_EXPORT_CONTRACT
    authority_class: str = "DERIVED_ENGINEERING_EXPORT"

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": self.authority_class,
            "export_id": self.export_id,
            "artifact_sha256": self.artifact_sha256,
            "artifact_size_bytes": self.artifact_size_bytes,
            "part_name": self.part_name,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_brep_geometry_sha256": self.source_brep_geometry_sha256,
            "source_operation_id": self.source_operation_id,
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "encoded_step_unit": self.encoded_step_unit,
            "reopened_step_length_units": list(self.reopened_step_length_units),
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "physical_accuracy_inferred": False,
            "mold_or_manufacturing_suitability_inferred": False,
            "scan_master_promoted": False,
            "design_model_replaced": False,
            "cad_brep_replaced": False,
            "binding_package": self.binding_package,
            "binding_version": self.binding_version,
            "kernel_version": self.kernel_version,
            "feature_mapping": list(self.feature_mapping),
            "timestamp_policy": "source_design_model_created_at_utc",
            "limitations": [
                "mm_unit_is_numerically_encoded_from_mm_unverified_design_values",
                "step_round_trip_is_software_evidence_not_physical_accuracy_validation",
                "this_export_contract_accepts_one_validated_brep_solid",
            ],
        }


def export_design_model_step(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    output_path: str | Path,
    *,
    part_name: str,
) -> CadStepExportRevision:
    """Write and reopen one exact-model-bound BREP using STEP millimetre units."""
    if not isinstance(model, DesignModelRevision):
        raise CadStepExportError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise CadStepExportError("cad_brep_representation_required")
    if representation.source_design_model_revision_id != model.revision_id:
        raise CadStepExportError("cad_step_model_revision_mismatch")
    if representation.parent_kind is not model.parent_kind:
        raise CadStepExportError("cad_step_parent_authority_mismatch")
    parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if representation.parent_authority_revision_id != parent_revision:
        raise CadStepExportError("cad_step_parent_revision_mismatch")
    if representation.scale_state is not ScaleState.METRIC_UNVERIFIED:
        raise CadStepExportError("cad_step_mm_unverified_source_required")
    if representation.coordinate_unit != "mm_unverified":
        raise CadStepExportError("cad_step_mm_unverified_unit_required")
    if (
        representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized is not False
    ):
        raise CadStepExportError("cad_step_physical_authority_mismatch")
    if (
        not isinstance(part_name, str)
        or not part_name.strip()
        or len(part_name) > 128
        or not part_name.isascii()
        or any(ord(character) < 32 for character in part_name)
    ):
        raise CadStepExportError("cad_step_part_name_invalid")
    try:
        validation = validate_cad_brep(representation)
    except Exception as error:
        raise CadStepExportError("cad_step_brep_validation_failed") from error
    if not validation.valid_closed_solid:
        raise CadStepExportError("cad_step_valid_closed_solid_required")
    try:
        feature_mapping = map_design_model_features_to_brep(model, representation)
    except ValueError as error:
        raise CadStepExportError("cad_step_feature_mapping_failed") from error

    diagnostics = probe_cad_runtime()
    if (
        diagnostics.status.value != "READY"
        or not diagnostics.binding_version
        or not diagnostics.kernel_version
    ):
        raise CadStepExportError("cad_step_runtime_version_unavailable")
    step_capabilities = tuple(diagnostics.capability(name) for name in ("step_write", "step_read"))
    if any(
        capability is None or capability.status.value != "AVAILABLE"
        for capability in step_capabilities
    ):
        raise CadStepExportError("cad_step_capability_unavailable")

    destination = Path(output_path)
    if destination.suffix.lower() not in {".step", ".stp"}:
        raise CadStepExportError("cad_step_extension_invalid")
    if not destination.parent.is_dir():
        raise CadStepExportError("cad_step_destination_directory_missing")
    if destination.exists():
        raise CadStepExportError("cad_step_destination_exists")
    timestamp = _model_timestamp(model.created_at_utc)

    with _STEP_EXPORT_LOCK:
        try:
            step = importlib.import_module("OCP.STEPControl")
            ifselect = importlib.import_module("OCP.IFSelect")
            interface = importlib.import_module("OCP.Interface").Interface_Static
            reader = step.STEPControl_Reader
            if not step.STEPControl_Controller.Init_s():
                raise CadStepExportError("cad_step_controller_initialization_failed")
            previous_unit = interface.CVal_s("write.step.unit")
            previous_product_name = interface.CVal_s("write.step.product.name")
            if not previous_unit or not previous_product_name:
                raise CadStepExportError("cad_step_static_parameters_unavailable")
            if not interface.SetCVal_s("write.step.unit", "MM"):
                raise CadStepExportError("cad_step_mm_unit_configuration_failed")
            if not interface.SetCVal_s("write.step.product.name", part_name):
                interface.SetCVal_s("write.step.unit", previous_unit)
                raise CadStepExportError("cad_step_product_name_configuration_failed")
            try:
                with tempfile.NamedTemporaryFile(
                    prefix="packlab-step-",
                    suffix=destination.suffix.lower(),
                    dir=destination.parent,
                    delete=False,
                ) as temporary:
                    temporary_path = Path(temporary.name)
                writer = step.STEPControl_Writer()
                copied_shape = (
                    importlib.import_module("OCP.BRepBuilderAPI")
                    .BRepBuilderAPI_Copy(
                        _shape_for_handle(representation.shape_handle), True, False
                    )
                    .Shape()
                )
                if (
                    writer.Transfer(copied_shape, step.STEPControl_AsIs)
                    != ifselect.IFSelect_RetDone
                ):
                    raise CadStepExportError("cad_step_transfer_failed")
                if writer.Write(str(temporary_path)) != ifselect.IFSelect_RetDone:
                    raise CadStepExportError("cad_step_write_failed")
                contents = temporary_path.read_bytes()
                contents, replacements = re.subn(
                    rb"(FILE_NAME\('[^']*',')[^']*(')",
                    rb"\g<1>" + timestamp.encode("ascii") + rb"\2",
                    contents,
                    count=1,
                )
                if replacements != 1:
                    raise CadStepExportError("cad_step_file_timestamp_missing")
                step_label = part_name.replace("'", "''").encode("ascii")
                contents, product_replacements = re.subn(
                    rb"(?m)^(\s*#\d+\s*=\s*PRODUCT\(')[^']*','[^']*'",
                    lambda match: _replace_step_product_label(match, step_label),
                    contents,
                    count=1,
                )
                if product_replacements != 1:
                    raise CadStepExportError("cad_step_product_label_missing")
                temporary_path.write_bytes(contents)
                unit_reader = reader()
                if unit_reader.ReadFile(str(temporary_path)) != ifselect.IFSelect_RetDone:
                    raise CadStepExportError("cad_step_reopen_failed")
                if unit_reader.TransferRoots() <= 0:
                    raise CadStepExportError("cad_step_reopen_transfer_failed")
                sequence_type = importlib.import_module("OCP.TColStd").TColStd_SequenceOfAsciiString
                length_units = sequence_type()
                angle_units = sequence_type()
                solid_angle_units = sequence_type()
                unit_reader.FileUnits(length_units, angle_units, solid_angle_units)
                reopened_units = tuple(
                    length_units.Value(index).ToCString()
                    for index in range(1, length_units.Length() + 1)
                )
                if not reopened_units or any(
                    unit.lower() != "millimetre" for unit in reopened_units
                ):
                    raise CadStepExportError("cad_step_reopened_unit_not_millimetre")
                artifact_bytes = temporary_path.read_bytes()
                temporary_path.replace(destination)
            finally:
                interface.SetCVal_s("write.step.unit", previous_unit)
                interface.SetCVal_s("write.step.product.name", previous_product_name)
                if "temporary_path" in locals() and temporary_path.exists():
                    temporary_path.unlink()
        except CadStepExportError:
            raise
        except Exception as error:
            raise CadStepExportError("cad_step_backend_export_failed") from error

    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
    identity = {
        "contract": CAD_STEP_EXPORT_CONTRACT,
        "artifact_sha256": artifact_sha256,
        "model_revision_id": model.revision_id,
        "brep_revision_id": representation.revision_id,
        "parent_kind": representation.parent_kind.value,
        "parent_authority_revision_id": representation.parent_authority_revision_id,
        "part_name": part_name,
        "binding_version": diagnostics.binding_version,
        "kernel_version": diagnostics.kernel_version,
        "unit": "mm",
    }
    export_id = (
        "cad-step-export:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    )
    return CadStepExportRevision(
        export_id=export_id,
        artifact_sha256=artifact_sha256,
        artifact_size_bytes=len(artifact_bytes),
        part_name=part_name,
        source_design_model_revision_id=model.revision_id,
        source_brep_revision_id=representation.revision_id,
        source_brep_geometry_sha256=representation.geometry_sha256,
        source_operation_id=representation.source_operation_id,
        parent_kind=representation.parent_kind.value,
        parent_authority_revision_id=representation.parent_authority_revision_id,
        scale_state=representation.scale_state.value,
        coordinate_unit=representation.coordinate_unit,
        physical_accuracy_validation_status=representation.physical_accuracy_validation_status,
        mold_use_authorized=representation.mold_use_authorized,
        binding_package=diagnostics.binding_package,
        binding_version=diagnostics.binding_version,
        kernel_version=diagnostics.kernel_version,
        encoded_step_unit="millimetre",
        reopened_step_length_units=reopened_units,
        feature_mapping=tuple(reference.as_dict() for reference in feature_mapping.references),
    )


def _model_timestamp(value: str) -> str:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        timestamp = datetime.fromisoformat(normalized)
        if timestamp.tzinfo is None:
            raise ValueError("timezone_required")
        return timestamp.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError as error:
        raise CadStepExportError("cad_step_source_timestamp_invalid") from error


def _replace_step_product_label(match: re.Match[bytes], label: bytes) -> bytes:
    return match.group(1) + label + b"','" + label + b"'"


__all__ = [
    "CAD_STEP_EXPORT_CONTRACT",
    "CadStepExportError",
    "CadStepExportRevision",
    "export_design_model_step",
]
