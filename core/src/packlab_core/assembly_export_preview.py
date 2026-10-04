"""Validate bottle/closure placements and emit metadata for a later export handoff."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .design_model import (
    DesignModelFeatureReference,
    DesignModelParentKind,
    DesignModelRevision,
    FeatureKind,
    ParameterType,
)
from .mating_references import MatingReferenceResult, MatingReferenceStatus
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_RIGID_TOLERANCE = 1e-8


class AssemblyExportPreviewError(ValueError):
    """Raised when an assembly placement cannot be handed off safely."""


@dataclass(frozen=True, slots=True)
class AssemblyComponentPlacement:
    """A component feature's placement in the shared assembly coordinate frame."""

    model_revision_id: str
    feature_id: str
    coordinate_unit: str
    matrix: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class AssemblyExportPreview:
    """Validated deterministic relationships, without creating a CAD or STEP file."""

    assembly_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    assembly_model_revision_id: str
    mating_reference_set_id: str
    scale_state: ScaleState
    scale_provenance_id: str
    coordinate_unit: str
    components: tuple[dict[str, object], ...]
    mating_relationship: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.bottle-closure-assembly-export-preview.v1",
            "assembly_id": self.assembly_id,
            "scan_master": {
                "revision_id": self.scan_master_revision_id,
                "geometry_sha256": self.scan_master_geometry_sha256,
            },
            "assembly_model_revision_id": self.assembly_model_revision_id,
            "mating_reference_set_id": self.mating_reference_set_id,
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "coordinate_unit": self.coordinate_unit,
            "components": [dict(item) for item in self.components],
            "mating_relationship": dict(self.mating_relationship),
            "export_handoff_ready": True,
            "preview_relationships_only": True,
            "cad_geometry_exported": False,
            "step_exported": False,
            "physical_accuracy_validation_status": _DEFERRED,
            "certified_claimed": False,
            "mold_ready_claimed": False,
            "thread_compatibility_claimed": False,
            "seal_compatibility_claimed": False,
            "manufacturing_alignment_claimed": False,
            "scan_master_mutated": False,
        }


def validate_bottle_closure_assembly_for_export(
    scan_master: ScanMasterRevision,
    assembly_model: DesignModelRevision,
    bottle_model: DesignModelRevision,
    closure_model: DesignModelRevision,
    mating_references: MatingReferenceResult,
    bottle_placement: AssemblyComponentPlacement,
    closure_placement: AssemblyComponentPlacement,
    *,
    expected_scan_master_revision_id: str,
    expected_assembly_model_revision_id: str,
    expected_bottle_model_revision_id: str,
    expected_closure_model_revision_id: str,
    expected_mating_reference_set_id: str,
    bottle_feature_id: str,
    neck_feature_id: str,
    closure_feature_id: str,
) -> AssemblyExportPreview:
    """Validate exact component revisions, mating planes, and proper rigid placements."""
    if not isinstance(scan_master, ScanMasterRevision):
        raise AssemblyExportPreviewError("scan_master_revision_required")
    if not isinstance(mating_references, MatingReferenceResult):
        raise AssemblyExportPreviewError("mating_reference_result_required")
    if not all(
        isinstance(item, DesignModelRevision)
        for item in (assembly_model, bottle_model, closure_model)
    ):
        raise AssemblyExportPreviewError("assembly_design_model_revisions_required")
    if any(
        item.parent_kind is not DesignModelParentKind.CAPTURED_SCAN_MASTER
        for item in (assembly_model, bottle_model, closure_model)
    ):
        raise AssemblyExportPreviewError("captured_scan_master_parent_required")
    for model in (assembly_model, bottle_model, closure_model):
        assert model.parent_binding_revision_id is not None
        assert model.fitted_to_scan_master_revision_id is not None
        assert model.scan_master_geometry_sha256 is not None
        assert model.scale_provenance_id is not None
    assert assembly_model.scale_provenance_id is not None
    assembly_scale_provenance_id = assembly_model.scale_provenance_id
    digest = mesh_sha256(scan_master.mesh)
    manifest = scan_master.manifest
    if (
        scan_master.revision_id != expected_scan_master_revision_id
        or manifest.get("scan_master_revision_id") != scan_master.revision_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != digest
        or manifest.get("physical_accuracy_validation_status") != _DEFERRED
        or manifest.get("mold_use_authorized") is not False
    ):
        raise AssemblyExportPreviewError("assembly_scan_master_stale_or_unauthorized")
    if (
        assembly_model.revision_id != expected_assembly_model_revision_id
        or bottle_model.revision_id != expected_bottle_model_revision_id
        or closure_model.revision_id != expected_closure_model_revision_id
    ):
        raise AssemblyExportPreviewError("assembly_component_revision_stale")
    try:
        scale_state = ScaleState(str(manifest.get("scale_state")))
    except ValueError as error:
        raise AssemblyExportPreviewError("assembly_scan_master_scale_state_invalid") from error
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise AssemblyExportPreviewError("assembly_metric_scale_not_authorized")
    expected_unit = (
        "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    )
    models = (assembly_model, bottle_model, closure_model)
    for model in models:
        if (
            model.project_id != scan_master.project_id
            or model.fitted_to_scan_master_revision_id != scan_master.revision_id
            or model.scan_master_geometry_sha256 != digest
            or model.parent_binding_revision_id != assembly_model.parent_binding_revision_id
            or model.scale_state is not scale_state
            or model.scale_provenance_id != manifest.get("scale_provenance_id")
            or model.coordinate_unit != expected_unit
            or model.physical_accuracy_validation_status != _DEFERRED
            or model.mold_use_authorized is not False
        ):
            raise AssemblyExportPreviewError("assembly_component_parent_or_scale_mismatch")
    if (
        bottle_model.previous_revision_id != assembly_model.revision_id
        or closure_model.previous_revision_id != assembly_model.revision_id
    ):
        raise AssemblyExportPreviewError("assembly_component_not_derived_from_source_revision")

    bottle_feature = _feature(
        bottle_model,
        bottle_feature_id,
        {FeatureKind.BODY, FeatureKind.NECK, FeatureKind.FINISH},
        "bottle",
    )
    neck_feature = _feature(
        assembly_model, neck_feature_id, {FeatureKind.NECK, FeatureKind.FINISH}, "neck"
    )
    closure_feature = _feature(closure_model, closure_feature_id, {FeatureKind.CAP}, "closure")
    if (
        _feature(
            assembly_model,
            bottle_feature_id,
            {FeatureKind.BODY, FeatureKind.NECK, FeatureKind.FINISH},
            "assembly_bottle",
        )
        != bottle_feature
    ):
        raise AssemblyExportPreviewError("assembly_bottle_feature_revision_mismatch")
    if (
        _feature(
            assembly_model, neck_feature_id, {FeatureKind.NECK, FeatureKind.FINISH}, "assembly_neck"
        )
        != neck_feature
    ):
        raise AssemblyExportPreviewError("assembly_neck_feature_revision_mismatch")
    if (
        _feature(assembly_model, closure_feature_id, {FeatureKind.CAP}, "assembly_closure")
        != closure_feature
    ):
        raise AssemblyExportPreviewError("assembly_closure_feature_revision_mismatch")
    if (
        bottle_placement.model_revision_id != bottle_model.revision_id
        or bottle_placement.feature_id != bottle_feature_id
        or bottle_placement.coordinate_unit != bottle_model.coordinate_unit
        or closure_placement.model_revision_id != closure_model.revision_id
        or closure_placement.feature_id != closure_feature_id
        or closure_placement.coordinate_unit != closure_model.coordinate_unit
    ):
        raise AssemblyExportPreviewError("assembly_placement_component_or_unit_mismatch")

    reference_model = mating_references.model
    if (
        mating_references.status is not MatingReferenceStatus.ALIGNED
        or mating_references.review_required
        or not isinstance(reference_model, DesignModelRevision)
        or mating_references.source_model_revision_id != assembly_model.revision_id
        or reference_model.previous_revision_id != assembly_model.revision_id
        or reference_model.project_id != assembly_model.project_id
        or reference_model.parent_binding_revision_id != assembly_model.parent_binding_revision_id
        or reference_model.fitted_to_scan_master_revision_id != scan_master.revision_id
        or reference_model.scan_master_geometry_sha256 != digest
        or reference_model.scale_state is not scale_state
        or reference_model.scale_provenance_id != assembly_model.scale_provenance_id
        or reference_model.coordinate_unit != expected_unit
        or reference_model.physical_accuracy_validation_status != _DEFERRED
        or reference_model.mold_use_authorized is not False
        or mating_references.scan_master_revision_id != scan_master.revision_id
        or mating_references.scan_master_geometry_sha256 != digest
        or mating_references.reference_set_id != expected_mating_reference_set_id
        or mating_references.neck_feature_id != neck_feature_id
        or mating_references.closure_feature_id != closure_feature_id
        or mating_references.coordinate_unit != expected_unit
    ):
        raise AssemblyExportPreviewError("assembly_mating_references_stale_or_incompatible")
    _feature(
        reference_model, neck_feature_id, {FeatureKind.NECK, FeatureKind.FINISH}, "mating_neck"
    )
    _feature(reference_model, closure_feature_id, {FeatureKind.CAP}, "mating_closure")
    _validate_mating_parameter(mating_references)
    _validate_rigid_matrix(bottle_placement.matrix, "bottle")
    _validate_rigid_matrix(closure_placement.matrix, "closure")
    relationship = _validate_transformed_references(
        mating_references,
        bottle_placement.matrix,
        closure_placement.matrix,
    )

    components = tuple(
        sorted(
            (
                _component_payload("bottle", bottle_model, bottle_feature, bottle_placement),
                _component_payload("closure", closure_model, closure_feature, closure_placement),
            ),
            key=lambda item: str(item["role"]),
        )
    )
    identity = {
        "scan_master_revision_id": scan_master.revision_id,
        "scan_master_geometry_sha256": digest,
        "assembly_model_revision_id": assembly_model.revision_id,
        "mating_reference_set_id": mating_references.reference_set_id,
        "scale_state": scale_state.value,
        "scale_provenance_id": assembly_scale_provenance_id,
        "coordinate_unit": expected_unit,
        "components": components,
        "mating_relationship": relationship,
    }
    assembly_id = (
        "assembly-preview:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
    )
    return AssemblyExportPreview(
        assembly_id,
        scan_master.revision_id,
        digest,
        assembly_model.revision_id,
        mating_references.reference_set_id,
        scale_state,
        assembly_scale_provenance_id,
        expected_unit,
        components,
        relationship,
    )


def _feature(
    model: DesignModelRevision,
    feature_id: str,
    allowed_kinds: set[FeatureKind],
    role: str,
) -> DesignModelFeatureReference:
    matches = tuple(item for item in model.features if item.feature_id == feature_id)
    if len(matches) != 1 or matches[0].feature_kind not in allowed_kinds:
        raise AssemblyExportPreviewError(f"assembly_{role}_feature_stale_or_invalid")
    return matches[0]


def _validate_mating_parameter(result: MatingReferenceResult) -> None:
    if not isinstance(result.model, DesignModelRevision):
        raise AssemblyExportPreviewError("assembly_mating_reference_model_missing")
    matches = []
    for parameter in result.model.parameters:
        if parameter.value_type is not ParameterType.OBJECT:
            continue
        parameter_value = parameter.as_dict()["value"]
        if (
            isinstance(parameter_value, dict)
            and parameter_value.get("reference_set_id") == result.reference_set_id
        ):
            matches.append(parameter)
    if len(matches) != 1:
        raise AssemblyExportPreviewError("assembly_mating_reference_parameter_missing_or_ambiguous")
    value = matches[0].as_dict()["value"]
    if not isinstance(value, dict) or (
        value.get("contract") != "packlab.neck-closure-mating-references.v1"
        or value.get("source_model_revision_id") != result.source_model_revision_id
        or value.get("scan_master_revision_id") != result.scan_master_revision_id
        or value.get("scan_master_geometry_sha256") != result.scan_master_geometry_sha256
        or value.get("neck_feature_id") != result.neck_feature_id
        or value.get("closure_feature_id") != result.closure_feature_id
        or value.get("canonical_axis_origin") != list(result.canonical_axis_origin)
        or value.get("canonical_axis_direction") != list(result.canonical_axis_direction)
        or value.get("neck_plane") != result.neck_plane.as_dict()
        or value.get("closure_plane") != result.closure_plane.as_dict()
        or value.get("inter_plane_offset") != result.inter_plane_offset
        or value.get("coordinate_unit") != result.coordinate_unit
        or value.get("thread_compatibility_claimed") is not False
        or value.get("seal_compatibility_claimed") is not False
        or value.get("manufacturing_alignment_claimed") is not False
        or value.get("physical_accuracy_validation_status") != _DEFERRED
        or value.get("mold_use_authorized") is not False
    ):
        raise AssemblyExportPreviewError("assembly_mating_reference_parameter_invalid")


def _validate_rigid_matrix(matrix: tuple[float, ...], role: str) -> None:
    if (
        not isinstance(matrix, tuple)
        or len(matrix) != 16
        or any(
            isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item)
            for item in matrix
        )
        or any(
            abs(item - expected) > _RIGID_TOLERANCE
            for item, expected in zip(matrix[12:16], (0.0, 0.0, 0.0, 1.0), strict=True)
        )
    ):
        raise AssemblyExportPreviewError(f"assembly_{role}_transform_affine_invalid")
    columns = tuple(tuple(matrix[row * 4 + column] for row in range(3)) for column in range(3))
    for index, column in enumerate(columns):
        norm_squared = math.fsum(value * value for value in column)
        if abs(norm_squared - 1.0) > _RIGID_TOLERANCE:
            raise AssemblyExportPreviewError(f"assembly_{role}_transform_not_rigid")
        for other in columns[index + 1 :]:
            if abs(math.fsum(a * b for a, b in zip(column, other, strict=True))) > _RIGID_TOLERANCE:
                raise AssemblyExportPreviewError(f"assembly_{role}_transform_not_rigid")
    a, b, c = columns
    determinant = (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - b[0] * (a[1] * c[2] - a[2] * c[1])
        + c[0] * (a[1] * b[2] - a[2] * b[1])
    )
    if abs(determinant - 1.0) > _RIGID_TOLERANCE:
        raise AssemblyExportPreviewError(f"assembly_{role}_transform_not_proper_rotation")


def _validate_transformed_references(
    result: MatingReferenceResult,
    bottle_matrix: tuple[float, ...],
    closure_matrix: tuple[float, ...],
) -> dict[str, object]:
    axis = _unit_vector(result.canonical_axis_direction, "mating_axis")
    neck_normal = _unit_vector(result.neck_plane.normal, "neck_plane_normal")
    closure_normal = _unit_vector(result.closure_plane.normal, "closure_plane_normal")
    if (
        _distance(neck_normal, axis) > _RIGID_TOLERANCE
        or _distance(closure_normal, axis) > _RIGID_TOLERANCE
    ):
        raise AssemblyExportPreviewError("assembly_component_plane_normals_mismatch")
    bottle_axis = _rotate(bottle_matrix, axis)
    closure_axis = _rotate(closure_matrix, axis)
    bottle_normal = _rotate(bottle_matrix, neck_normal)
    closure_plane_normal = _rotate(closure_matrix, closure_normal)
    if _distance(bottle_axis, closure_axis) > _RIGID_TOLERANCE:
        raise AssemblyExportPreviewError("assembly_component_axes_mismatch")
    canonical_origin = _point3(result.canonical_axis_origin, "mating_axis_origin")
    bottle_axis_origin = _apply(bottle_matrix, canonical_origin)
    closure_axis_origin = _apply(closure_matrix, canonical_origin)
    origin_delta = tuple(
        closure_axis_origin[index] - bottle_axis_origin[index] for index in range(3)
    )
    axis_separation = tuple(
        origin_delta[index]
        - math.fsum(origin_delta[axis_index] * bottle_axis[axis_index] for axis_index in range(3))
        * bottle_axis[index]
        for index in range(3)
    )
    if math.sqrt(math.fsum(item * item for item in axis_separation)) > _RIGID_TOLERANCE:
        raise AssemblyExportPreviewError("assembly_component_axes_mismatch")
    if _distance(bottle_normal, closure_plane_normal) > _RIGID_TOLERANCE:
        raise AssemblyExportPreviewError("assembly_component_plane_normals_mismatch")
    neck_origin = _apply(bottle_matrix, _point3(result.neck_plane.origin, "neck_plane_origin"))
    closure_origin = _apply(
        closure_matrix, _point3(result.closure_plane.origin, "closure_plane_origin")
    )
    delta = tuple(closure_origin[index] - neck_origin[index] for index in range(3))
    signed_offset = math.fsum(delta[index] * bottle_axis[index] for index in range(3))
    lateral = tuple(delta[index] - signed_offset * bottle_axis[index] for index in range(3))
    if (
        isinstance(result.inter_plane_offset, bool)
        or not isinstance(result.inter_plane_offset, (int, float))
        or not math.isfinite(result.inter_plane_offset)
    ):
        raise AssemblyExportPreviewError("assembly_mating_plane_offset_invalid")
    tolerance = _RIGID_TOLERANCE * max(1.0, abs(result.inter_plane_offset))
    if (
        abs(signed_offset - result.inter_plane_offset) > tolerance
        or math.sqrt(math.fsum(value * value for value in lateral)) > tolerance
    ):
        raise AssemblyExportPreviewError("assembly_component_reference_planes_mismatch")
    return {
        "canonical_axis_origin": list(bottle_axis_origin),
        "closure_axis_origin": list(closure_axis_origin),
        "canonical_axis_direction": list(bottle_axis),
        "closure_axis_direction": list(closure_axis),
        "neck_plane_origin": list(neck_origin),
        "closure_plane_origin": list(closure_origin),
        "signed_inter_plane_offset": signed_offset,
        "coordinate_unit": result.coordinate_unit,
        "reference_planes_match_after_transform": True,
        "axis_match_after_transform": True,
        "thread_compatibility_claimed": False,
        "seal_compatibility_claimed": False,
    }


def _unit_vector(vector: tuple[float, float, float], role: str) -> tuple[float, float, float]:
    if len(vector) != 3 or any(
        isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item)
        for item in vector
    ):
        raise AssemblyExportPreviewError(f"assembly_{role}_invalid")
    magnitude = math.sqrt(math.fsum(item * item for item in vector))
    if abs(magnitude - 1.0) > _RIGID_TOLERANCE:
        raise AssemblyExportPreviewError(f"assembly_{role}_not_unit_length")
    return tuple(float(item) for item in vector)  # type: ignore[return-value]


def _point3(point: tuple[float, float, float], role: str) -> tuple[float, float, float]:
    if len(point) != 3 or any(
        isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item)
        for item in point
    ):
        raise AssemblyExportPreviewError(f"assembly_{role}_invalid")
    return tuple(float(item) for item in point)  # type: ignore[return-value]


def _apply(
    matrix: tuple[float, ...], point: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(
        math.fsum(matrix[row * 4 + column] * point[column] for column in range(3))
        + matrix[row * 4 + 3]
        for row in range(3)
    )  # type: ignore[return-value]


def _rotate(
    matrix: tuple[float, ...], vector: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(
        math.fsum(matrix[row * 4 + column] * vector[column] for column in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def _distance(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return math.sqrt(math.fsum((first[index] - second[index]) ** 2 for index in range(3)))


def _component_payload(
    role: str,
    model: DesignModelRevision,
    feature: DesignModelFeatureReference,
    placement: AssemblyComponentPlacement,
) -> dict[str, object]:
    return {
        "role": role,
        "component_revision_id": model.revision_id,
        "feature_id": feature.feature_id,
        "component_id": feature.component_id,
        "feature_kind": feature.feature_kind.value,
        "coordinate_unit": model.coordinate_unit,
        "transform_convention": "row_major_4x4_column_vectors_v1",
        "transform": list(placement.matrix),
    }


__all__ = [
    "AssemblyComponentPlacement",
    "AssemblyExportPreview",
    "AssemblyExportPreviewError",
    "validate_bottle_closure_assembly_for_export",
]
