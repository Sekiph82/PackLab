"""Deterministic rigid placement of a pinned library trigger/pump reference."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .assembly_graph import (
    AssemblyComponentInput,
    AssemblyComponentReference,
    AssemblyComponentRole,
    AssemblyGraphError,
    ParametricAssemblyGraph,
    validate_parametric_assembly_graph,
)
from .design_model import (
    DesignModelError,
    DesignModelRevision,
    FeatureKind,
    resolve_design_model_feature,
)
from .mating_references import MatingReferenceResult, MatingReferenceStatus
from .reconstruction import ScaleState
from .trigger_pump_library import ImportedTriggerPumpComponent

_TOLERANCE = 1e-8
_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class TriggerPumpAlignmentError(ValueError):
    """Raised when a library attachment cannot be aligned to exact mating references."""


@dataclass(frozen=True, slots=True)
class TriggerPumpAlignmentRevision:
    """Immutable placement relationship; it contains no geometry or compatibility verdict."""

    revision_id: str
    assembly_graph_revision_id: str
    library_import_id: str
    trigger_pump_model_revision_id: str
    trigger_pump_feature_id: str
    body_model_revision_id: str
    closure_model_revision_id: str
    mating_reference_set_id: str
    mating_source_model_revision_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    coordinate_unit: str
    scale_state: ScaleState
    placement_matrix: tuple[float, ...]
    physical_accuracy_validation_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.trigger-pump-alignment.v1",
            "revision_id": self.revision_id,
            "assembly_graph_revision_id": self.assembly_graph_revision_id,
            "library_import_id": self.library_import_id,
            "components": {
                "trigger_pump_model_revision_id": self.trigger_pump_model_revision_id,
                "trigger_pump_feature_id": self.trigger_pump_feature_id,
                "body_model_revision_id": self.body_model_revision_id,
                "closure_model_revision_id": self.closure_model_revision_id,
            },
            "mating_reference": {
                "reference_set_id": self.mating_reference_set_id,
                "source_model_revision_id": self.mating_source_model_revision_id,
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            },
            "coordinate_unit": self.coordinate_unit,
            "scale_state": self.scale_state.value,
            "placement": {
                "transform_convention": "row_major_4x4_column_vectors_v1",
                "matrix": list(self.placement_matrix),
            },
            "authority_class": "PARAMETRIC_ASSEMBLY_PLACEMENT",
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": False,
            "bottle_geometry_modified": False,
            "thread_compatibility_claimed": False,
            "seal_compatibility_claimed": False,
            "manufacturing_alignment_claimed": False,
        }


def align_library_trigger_pump(
    component: ImportedTriggerPumpComponent,
    graph: ParametricAssemblyGraph,
    current_components: tuple[AssemblyComponentInput, ...],
    mating_references: MatingReferenceResult,
    *,
    expected_body_model_revision_id: str,
    expected_closure_model_revision_id: str,
    expected_trigger_pump_model_revision_id: str,
    expected_mating_source_model_revision_id: str,
) -> TriggerPumpAlignmentRevision:
    """Align one explicit library-local frame to the exact captured closure reference plane."""
    if not isinstance(component, ImportedTriggerPumpComponent):
        raise TriggerPumpAlignmentError("library_trigger_pump_component_required")
    if not isinstance(mating_references, MatingReferenceResult):
        raise TriggerPumpAlignmentError("mating_reference_result_required")
    try:
        validate_parametric_assembly_graph(graph, current_components)
    except AssemblyGraphError as error:
        raise TriggerPumpAlignmentError(str(error)) from error
    references = {item.role: item for item in graph.components}
    body = references[AssemblyComponentRole.BODY]
    closure = references[AssemblyComponentRole.CLOSURE]
    pump = references[AssemblyComponentRole.TRIGGER_PUMP]
    if (
        body.model_revision_id != expected_body_model_revision_id
        or closure.model_revision_id != expected_closure_model_revision_id
        or pump.model_revision_id != expected_trigger_pump_model_revision_id
    ):
        raise TriggerPumpAlignmentError("assembly_component_revision_stale")
    pump_input = next(
        item for item in current_components if item.role is AssemblyComponentRole.TRIGGER_PUMP
    )
    pump_model = pump_input.model
    if not isinstance(pump_model, DesignModelRevision):
        raise TriggerPumpAlignmentError("trigger_pump_design_model_required")
    if (
        component.component_id != pump.component_id
        or component.coordinate_unit != pump.coordinate_unit
        or component.coordinate_unit != graph.coordinate_unit
        or component.scale_state is not graph.scale_state
        or pump.scale_state is not graph.scale_state
    ):
        raise TriggerPumpAlignmentError("trigger_pump_attachment_unit_or_scale_mismatch")
    try:
        pump_feature = resolve_design_model_feature(pump_model, pump.feature_id)
    except DesignModelError as error:
        raise TriggerPumpAlignmentError("trigger_pump_feature_stale") from error
    if pump_feature.feature_kind is not FeatureKind.TRIGGER_PUMP:
        raise TriggerPumpAlignmentError("trigger_pump_feature_invalid")

    _validate_mating_parent(
        body,
        closure,
        mating_references,
        expected_mating_source_model_revision_id,
    )
    source_axis = _unit(component.attachment_axis, "attachment_axis")
    source_normal = _unit(component.attachment_plane_normal, "attachment_plane_normal")
    target_axis = _unit(mating_references.canonical_axis_direction, "mating_axis")
    target_normal = _unit(mating_references.closure_plane.normal, "closure_plane_normal")
    if (
        _distance(source_axis, source_normal) > _TOLERANCE
        or _distance(target_axis, target_normal) > _TOLERANCE
    ):
        raise TriggerPumpAlignmentError("trigger_pump_attachment_axis_plane_mismatch")
    source_origin = _point(component.attachment_origin, "attachment_origin")
    target_origin = _point(mating_references.closure_plane.origin, "closure_plane_origin")
    rotation = _rotation_between(source_axis, target_axis)
    rotated_origin = _rotate_point(rotation, source_origin)
    translation = tuple(target_origin[index] - rotated_origin[index] for index in range(3))
    matrix = _matrix(rotation, translation)
    if (
        _distance(_apply(matrix, source_origin), target_origin) > _TOLERANCE
        or _distance(_rotate_vector(rotation, source_axis), target_axis) > _TOLERANCE
        or _distance(_rotate_vector(rotation, source_normal), target_normal) > _TOLERANCE
    ):
        raise TriggerPumpAlignmentError("trigger_pump_attachment_alignment_failed")
    identity = {
        "contract": "packlab.trigger-pump-alignment.v1",
        "assembly_graph_revision_id": graph.revision_id,
        "library_import_id": component.import_id,
        "trigger_pump_model_revision_id": pump.model_revision_id,
        "trigger_pump_feature_id": pump.feature_id,
        "body_model_revision_id": body.model_revision_id,
        "closure_model_revision_id": closure.model_revision_id,
        "mating_reference_set_id": mating_references.reference_set_id,
        "mating_source_model_revision_id": mating_references.source_model_revision_id,
        "scan_master_revision_id": mating_references.scan_master_revision_id,
        "scan_master_geometry_sha256": mating_references.scan_master_geometry_sha256,
        "coordinate_unit": graph.coordinate_unit,
        "scale_state": graph.scale_state.value,
        "placement_matrix": matrix,
    }
    revision_id = (
        "trigger-pump-alignment:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
    )
    return TriggerPumpAlignmentRevision(
        revision_id,
        graph.revision_id,
        component.import_id,
        pump.model_revision_id,
        pump.feature_id,
        body.model_revision_id,
        closure.model_revision_id,
        mating_references.reference_set_id,
        mating_references.source_model_revision_id,
        mating_references.scan_master_revision_id,
        mating_references.scan_master_geometry_sha256,
        graph.coordinate_unit,
        graph.scale_state,
        matrix,
        _DEFERRED,
    )


def _validate_mating_parent(
    body: AssemblyComponentReference,
    closure: AssemblyComponentReference,
    result: MatingReferenceResult,
    expected_source_revision_id: str,
) -> None:
    if (
        result.status is not MatingReferenceStatus.ALIGNED
        or result.review_required
        or result.model is None
        or result.source_model_revision_id != expected_source_revision_id
        or result.model.previous_revision_id != expected_source_revision_id
        or result.coordinate_unit != body.coordinate_unit
        or result.coordinate_unit != closure.coordinate_unit
        or result.scan_master_revision_id != body.scan_master_revision_id
        or result.scan_master_revision_id != closure.scan_master_revision_id
        or result.scan_master_geometry_sha256 != body.scan_master_geometry_sha256
        or result.scan_master_geometry_sha256 != closure.scan_master_geometry_sha256
        or body.scale_state is not closure.scale_state
        or result.model.scale_state is not body.scale_state
        or result.model.coordinate_unit != body.coordinate_unit
    ):
        raise TriggerPumpAlignmentError("trigger_pump_mating_reference_stale_or_incompatible")
    try:
        neck_feature = resolve_design_model_feature(result.model, result.neck_feature_id)
        closure_feature = resolve_design_model_feature(result.model, result.closure_feature_id)
    except DesignModelError as error:
        raise TriggerPumpAlignmentError("trigger_pump_mating_feature_stale") from error
    if neck_feature.feature_kind not in {FeatureKind.NECK, FeatureKind.FINISH}:
        raise TriggerPumpAlignmentError("trigger_pump_mating_neck_feature_invalid")
    if closure_feature.feature_kind is not FeatureKind.CAP:
        raise TriggerPumpAlignmentError("trigger_pump_mating_closure_feature_invalid")
    if result.closure_plane.feature_id != result.closure_feature_id:
        raise TriggerPumpAlignmentError("trigger_pump_mating_closure_plane_invalid")


def _unit(vector: tuple[float, float, float], field: str) -> tuple[float, float, float]:
    point = _point(vector, field)
    magnitude = math.sqrt(math.fsum(value * value for value in point))
    if abs(magnitude - 1.0) > _TOLERANCE:
        raise TriggerPumpAlignmentError(f"{field}_not_unit_length")
    return point


def _point(point: tuple[float, float, float], field: str) -> tuple[float, float, float]:
    if (
        not isinstance(point, tuple)
        or len(point) != 3
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in point
        )
    ):
        raise TriggerPumpAlignmentError(f"{field}_invalid")
    return tuple(float(value) for value in point)  # type: ignore[return-value]


def _rotation_between(
    source: tuple[float, float, float], target: tuple[float, float, float]
) -> tuple[float, ...]:
    cross = (
        source[1] * target[2] - source[2] * target[1],
        source[2] * target[0] - source[0] * target[2],
        source[0] * target[1] - source[1] * target[0],
    )
    cosine = max(-1.0, min(1.0, math.fsum(source[i] * target[i] for i in range(3))))
    if cosine > 1.0 - _TOLERANCE:
        return (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    if cosine < -1.0 + _TOLERANCE:
        basis = min(
            ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            key=lambda axis: abs(math.fsum(source[i] * axis[i] for i in range(3))),
        )
        axis = _normalize(
            (
                source[1] * basis[2] - source[2] * basis[1],
                source[2] * basis[0] - source[0] * basis[2],
                source[0] * basis[1] - source[1] * basis[0],
            )
        )
        return tuple(
            2.0 * axis[row] * axis[column] - (1.0 if row == column else 0.0)
            for row in range(3)
            for column in range(3)
        )
    skew = (0.0, -cross[2], cross[1], cross[2], 0.0, -cross[0], -cross[1], cross[0], 0.0)
    square = tuple(
        math.fsum(skew[row * 3 + k] * skew[k * 3 + column] for k in range(3))
        for row in range(3)
        for column in range(3)
    )
    return tuple(
        (1.0 if row == column else 0.0)
        + skew[row * 3 + column]
        + square[row * 3 + column] / (1.0 + cosine)
        for row in range(3)
        for column in range(3)
    )


def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    magnitude = math.sqrt(math.fsum(value * value for value in vector))
    return tuple(value / magnitude for value in vector)  # type: ignore[return-value]


def _rotate_point(rotation: tuple[float, ...], point: tuple[float, float, float]):
    return _rotate_vector(rotation, point)


def _rotate_vector(rotation: tuple[float, ...], vector: tuple[float, float, float]):
    return tuple(
        math.fsum(rotation[row * 3 + column] * vector[column] for column in range(3))
        for row in range(3)
    )


def _matrix(rotation: tuple[float, ...], translation: tuple[float, float, float]):
    return (
        rotation[0],
        rotation[1],
        rotation[2],
        translation[0],
        rotation[3],
        rotation[4],
        rotation[5],
        translation[1],
        rotation[6],
        rotation[7],
        rotation[8],
        translation[2],
        0.0,
        0.0,
        0.0,
        1.0,
    )


def _apply(matrix: tuple[float, ...], point: tuple[float, float, float]):
    return tuple(
        math.fsum(matrix[row * 4 + column] * point[column] for column in range(3))
        + matrix[row * 4 + 3]
        for row in range(3)
    )


def _distance(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return math.sqrt(math.fsum((first[index] - second[index]) ** 2 for index in range(3)))


__all__ = [
    "TriggerPumpAlignmentError",
    "TriggerPumpAlignmentRevision",
    "align_library_trigger_pump",
]
