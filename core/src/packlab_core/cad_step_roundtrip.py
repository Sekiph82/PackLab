"""Numerical, provenance-bound STEP read-back checks for derived CAD exports."""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from .cad_adapter import (
    _registered_shape_build,
    cad_shape_bounds,
    inspect_shape_topology,
    probe_cad_runtime,
)
from .cad_brep import CadBrepRepresentationRevision
from .design_model import DesignModelRevision
from .reconstruction import ScaleState

_PRODUCT_NAME = re.compile(rb"(?m)^\s*#\d+\s*=\s*PRODUCT\('((?:''|[^'])*)','")
_NUMERICAL_TOLERANCE_FLOOR = 1e-6
_NUMERICAL_TOLERANCE_RELATIVE = 1e-12


class CadStepRoundTripError(ValueError):
    """Raised when STEP data cannot be read or deviates from its exact CAD source."""


@dataclass(frozen=True, slots=True)
class CadStepRoundTripReport:
    report_id: str
    artifact_sha256: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    parent_kind: str
    parent_authority_revision_id: str
    part_name: str
    reopened_length_units: tuple[str, ...]
    solid_count: int
    part_names: tuple[str, ...]
    source_bounds: tuple[float, float, float, float, float, float]
    reopened_bounds: tuple[float, float, float, float, float, float]
    source_dimensions: tuple[float, float, float]
    reopened_dimensions: tuple[float, float, float]
    bounds_delta: tuple[float, float, float, float, float, float]
    maximum_bounds_delta: float
    numerical_tolerance: float
    tolerance_basis: str
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.cad-step-roundtrip-report.v1",
            "report_id": self.report_id,
            "status": "PASS",
            "artifact_sha256": self.artifact_sha256,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "part_name": self.part_name,
            "part_names": list(self.part_names),
            "reopened_length_units": list(self.reopened_length_units),
            "solid_count": self.solid_count,
            "source_bounds": list(self.source_bounds),
            "reopened_bounds": list(self.reopened_bounds),
            "source_dimensions": list(self.source_dimensions),
            "reopened_dimensions": list(self.reopened_dimensions),
            "bounds_delta": list(self.bounds_delta),
            "maximum_bounds_delta": self.maximum_bounds_delta,
            "numerical_tolerance": self.numerical_tolerance,
            "tolerance_basis": self.tolerance_basis,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "numerical_fidelity_only": True,
            "physical_accuracy_inferred": False,
            "manufacturing_tolerance_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


def validate_step_export_round_trip(
    path: str | Path,
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    *,
    expected_part_name: str,
) -> CadStepRoundTripReport:
    """Reopen one STEP file and compare units, topology, name and AABB numerically."""
    if not isinstance(model, DesignModelRevision):
        raise CadStepRoundTripError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise CadStepRoundTripError("cad_brep_representation_required")
    if (
        representation.source_design_model_revision_id != model.revision_id
        or representation.parent_kind is not model.parent_kind
        or representation.parent_authority_revision_id
        != (
            model.standalone_root.revision_id
            if model.standalone_root is not None
            else model.parent_binding_revision_id
        )
    ):
        raise CadStepRoundTripError("cad_step_roundtrip_source_authority_mismatch")
    if (
        representation.scale_state is not ScaleState.METRIC_UNVERIFIED
        or representation.coordinate_unit != "mm_unverified"
    ):
        raise CadStepRoundTripError("cad_step_roundtrip_mm_unverified_source_required")
    if (
        not isinstance(expected_part_name, str)
        or not expected_part_name.strip()
        or not expected_part_name.isascii()
        or any(ord(character) < 32 for character in expected_part_name)
    ):
        raise CadStepRoundTripError("cad_step_roundtrip_part_name_invalid")
    source_path = Path(path)
    if source_path.suffix.lower() not in {".step", ".stp"}:
        raise CadStepRoundTripError("cad_step_roundtrip_extension_invalid")
    if source_path.is_symlink() or not source_path.is_file():
        raise CadStepRoundTripError("cad_step_roundtrip_file_unavailable")
    try:
        artifact_bytes = source_path.read_bytes()
    except OSError as error:
        raise CadStepRoundTripError("cad_step_roundtrip_file_unreadable") from error
    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()

    diagnostics = probe_cad_runtime()
    step_read_capability = diagnostics.capability("step_read")
    if (
        diagnostics.status.value != "READY"
        or not diagnostics.binding_version
        or not diagnostics.kernel_version
        or step_read_capability is None
        or step_read_capability.status.value != "AVAILABLE"
    ):
        raise CadStepRoundTripError("cad_step_roundtrip_capability_unavailable")
    try:
        step = importlib.import_module("OCP.STEPControl")
        ifselect = importlib.import_module("OCP.IFSelect")
        if not step.STEPControl_Controller.Init_s():
            raise CadStepRoundTripError("cad_step_roundtrip_controller_init_failed")
        reader = step.STEPControl_Reader()
        if reader.ReadFile(str(source_path)) != ifselect.IFSelect_RetDone:
            raise CadStepRoundTripError("cad_step_roundtrip_unreadable")
        if reader.TransferRoots() <= 0:
            raise CadStepRoundTripError("cad_step_roundtrip_transfer_failed")
        shape = reader.OneShape()
        if shape.IsNull():
            raise CadStepRoundTripError("cad_step_roundtrip_shape_missing")
        units_module = importlib.import_module("OCP.TColStd")
        length_units = units_module.TColStd_SequenceOfAsciiString()
        angle_units = units_module.TColStd_SequenceOfAsciiString()
        solid_angle_units = units_module.TColStd_SequenceOfAsciiString()
        reader.FileUnits(length_units, angle_units, solid_angle_units)
        reopened_units = tuple(
            length_units.Value(index).ToCString() for index in range(1, length_units.Length() + 1)
        )
        if not reopened_units or any(unit.lower() != "millimetre" for unit in reopened_units):
            raise CadStepRoundTripError("cad_step_roundtrip_unit_mismatch")
        top_abs = importlib.import_module("OCP.TopAbs")
        top_exp = importlib.import_module("OCP.TopExp")
        explorer = top_exp.TopExp_Explorer(shape, top_abs.TopAbs_SOLID)
        solid_count = 0
        while explorer.More():
            solid_count += 1
            explorer.Next()
        if solid_count != representation.solid_count or solid_count <= 0:
            raise CadStepRoundTripError("cad_step_roundtrip_solid_count_mismatch")
        shape_build = _registered_shape_build(
            model,
            representation.source_operation_id,
            representation.source_input_ids,
            shape,
            solid_count,
        )
        topology = inspect_shape_topology(shape_build.shape_handle)
        if (
            not topology.kernel_valid
            or topology.solid_count != representation.solid_count
            or topology.shell_count <= 0
            or topology.closed_shell_count != topology.shell_count
            or topology.open_edge_count != 0
            or topology.nonmanifold_edge_count != 0
        ):
            raise CadStepRoundTripError("cad_step_roundtrip_topology_invalid")
        product_names = tuple(
            item.decode("ascii").replace("''", "'")
            for item in _PRODUCT_NAME.findall(artifact_bytes)
        )
        if expected_part_name not in product_names:
            raise CadStepRoundTripError("cad_step_roundtrip_part_name_mismatch")
        source_bounds = _interleaved_bounds(cad_shape_bounds(representation.shape_handle))
        reopened_bounds = _interleaved_bounds(cad_shape_bounds(shape_build.shape_handle))
    except CadStepRoundTripError:
        raise
    except Exception as error:
        raise CadStepRoundTripError("cad_step_roundtrip_readback_failed") from error

    if any(not math.isfinite(value) for value in (*source_bounds, *reopened_bounds)):
        raise CadStepRoundTripError("cad_step_roundtrip_bounds_invalid")
    deltas = (
        abs(source_bounds[0] - reopened_bounds[0]),
        abs(source_bounds[1] - reopened_bounds[1]),
        abs(source_bounds[2] - reopened_bounds[2]),
        abs(source_bounds[3] - reopened_bounds[3]),
        abs(source_bounds[4] - reopened_bounds[4]),
        abs(source_bounds[5] - reopened_bounds[5]),
    )
    maximum_delta = max(deltas)
    magnitude = max(1.0, *(abs(value) for value in source_bounds))
    tolerance = max(_NUMERICAL_TOLERANCE_FLOOR, magnitude * _NUMERICAL_TOLERANCE_RELATIVE)
    if maximum_delta > tolerance:
        raise CadStepRoundTripError("cad_step_roundtrip_bounds_drift_exceeded")
    source_dimensions = _dimensions(source_bounds)
    reopened_dimensions = _dimensions(reopened_bounds)
    identity = {
        "artifact_sha256": artifact_sha256,
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "parent_kind": representation.parent_kind.value,
        "parent_authority_revision_id": representation.parent_authority_revision_id,
        "part_name": expected_part_name,
        "reopened_length_units": reopened_units,
        "solid_count": solid_count,
        "source_bounds": source_bounds,
        "reopened_bounds": reopened_bounds,
        "numerical_tolerance": tolerance,
    }
    report_id = (
        "cad-step-roundtrip:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    return CadStepRoundTripReport(
        report_id=report_id,
        artifact_sha256=artifact_sha256,
        source_design_model_revision_id=model.revision_id,
        source_brep_revision_id=representation.revision_id,
        parent_kind=representation.parent_kind.value,
        parent_authority_revision_id=representation.parent_authority_revision_id,
        part_name=expected_part_name,
        reopened_length_units=reopened_units,
        solid_count=solid_count,
        part_names=product_names,
        source_bounds=source_bounds,
        reopened_bounds=reopened_bounds,
        source_dimensions=source_dimensions,
        reopened_dimensions=reopened_dimensions,
        bounds_delta=deltas,
        maximum_bounds_delta=maximum_delta,
        numerical_tolerance=tolerance,
        tolerance_basis=(
            "max(1e-6 mm, 1e-12 * max(1 mm, absolute source bound)); "
            "STEP/OCCT numerical serialization precision only, not a physical tolerance"
        ),
    )


def _interleaved_bounds(
    grouped_bounds: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    return (
        grouped_bounds[0],
        grouped_bounds[3],
        grouped_bounds[1],
        grouped_bounds[4],
        grouped_bounds[2],
        grouped_bounds[5],
    )


def _dimensions(
    bounds: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float]:
    return (bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])


__all__ = [
    "CadStepRoundTripError",
    "CadStepRoundTripReport",
    "validate_step_export_round_trip",
]
