"""Stable neck/closure mating references with explicit, non-compatibility offsets."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import StrEnum

from .bounding_dimensions import NormalizedMeasurementGeometry
from .cross_section_measurement import (
    CROSS_SECTION_METHOD_VERSION,
    CrossSectionMeasurement,
    CrossSectionSelection,
    measure_cross_section,
)
from .design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    ParameterType,
    resolve_design_model_feature,
    revise_design_model_revision,
)
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

MATING_REFERENCE_CONTRACT = "packlab.neck-closure-mating-references.v1"


class MatingReferenceError(ValueError):
    """Raised when a mating reference is stale, unbound, or malformed."""


class MatingReferenceStatus(StrEnum):
    ALIGNED = "ALIGNED"
    AXIS_MISMATCH_REVIEW_REQUIRED = "AXIS_MISMATCH_REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class MatingReferencePolicy:
    minimum_sections_per_feature: int = 2
    minimum_points_per_section: int = 12
    maximum_radial_residual: float = 0.25
    maximum_axis_misalignment: float = 0.25
    maximum_axis_center_spread: float = 0.25

    def __post_init__(self) -> None:
        for name in ("minimum_sections_per_feature", "minimum_points_per_section"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                raise MatingReferenceError(f"{name}_invalid")
        for name in (
            "maximum_radial_residual",
            "maximum_axis_misalignment",
            "maximum_axis_center_spread",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0.0
            ):
                raise MatingReferenceError(f"{name}_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.mating-reference-policy.v1",
            "minimum_sections_per_feature": self.minimum_sections_per_feature,
            "minimum_points_per_section": self.minimum_points_per_section,
            "maximum_radial_residual": self.maximum_radial_residual,
            "maximum_axis_misalignment": self.maximum_axis_misalignment,
            "maximum_axis_center_spread": self.maximum_axis_center_spread,
        }


@dataclass(frozen=True, slots=True)
class MatingReferencePlane:
    reference_id: str
    feature_id: str
    role: str
    origin: tuple[float, float, float]
    normal: tuple[float, float, float]
    offset_from_axis_origin: float
    support_measurement_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "reference_id": self.reference_id,
            "feature_id": self.feature_id,
            "role": self.role,
            "origin": list(self.origin),
            "normal": list(self.normal),
            "offset_from_axis_origin": self.offset_from_axis_origin,
            "support_measurement_ids": list(self.support_measurement_ids),
        }


@dataclass(frozen=True, slots=True)
class MatingReferenceResult:
    status: MatingReferenceStatus
    reasons: tuple[str, ...]
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    source_model_revision_id: str
    neck_feature_id: str
    closure_feature_id: str
    reference_set_id: str
    canonical_axis_origin: tuple[float, float, float]
    canonical_axis_direction: tuple[float, float, float]
    neck_plane: MatingReferencePlane
    closure_plane: MatingReferencePlane
    inter_plane_offset: float
    axis_misalignment: float
    model: DesignModelRevision | None
    coordinate_unit: str
    review_required: bool
    policy: MatingReferencePolicy

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": MATING_REFERENCE_CONTRACT,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "source_model_revision_id": self.source_model_revision_id,
            },
            "feature_ids": {
                "neck": self.neck_feature_id,
                "closure": self.closure_feature_id,
            },
            "canonical_axis": {
                "origin": list(self.canonical_axis_origin),
                "direction": list(self.canonical_axis_direction),
            },
            "planes": {
                "neck": self.neck_plane.as_dict(),
                "closure": self.closure_plane.as_dict(),
            },
            "offsets": {
                "closure_from_neck": self.inter_plane_offset,
                "unit": self.coordinate_unit,
            },
            "axis_misalignment": self.axis_misalignment,
            "model_revision_id": self.model.revision_id if self.model else None,
            "review_required": self.review_required,
            "thread_compatibility_claimed": False,
            "seal_compatibility_claimed": False,
            "manufacturing_alignment_claimed": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "scan_master_mutated": False,
            "policy": self.policy.as_dict(),
        }


def create_neck_closure_mating_references(
    scan_master: ScanMasterRevision,
    geometry: NormalizedMeasurementGeometry,
    model: DesignModelRevision,
    neck_feature_id: str,
    closure_feature_id: str,
    neck_sections: tuple[CrossSectionSelection, ...],
    closure_sections: tuple[CrossSectionSelection, ...],
    *,
    expected_scan_master_revision_id: str,
    expected_model_revision_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    policy: MatingReferencePolicy = MatingReferencePolicy(),
) -> MatingReferenceResult:
    """Create stable mating planes and axis from two parent-bound section sets."""
    _validate_parents(
        scan_master,
        geometry,
        model,
        expected_scan_master_revision_id,
        expected_model_revision_id,
    )
    if not isinstance(policy, MatingReferencePolicy):
        raise MatingReferenceError("mating_reference_policy_invalid")
    neck_feature = _resolve_feature(model, neck_feature_id, "neck")
    closure_feature = _resolve_feature(model, closure_feature_id, "closure")
    neck_measurements = _measure_sections(geometry, neck_sections, "neck", policy)
    closure_measurements = _measure_sections(geometry, closure_sections, "closure", policy)
    if not _enough_and_spread(neck_measurements, policy):
        raise MatingReferenceError("neck_axis_section_support_or_spread_invalid")
    if not _enough_and_spread(closure_measurements, policy):
        raise MatingReferenceError("closure_axis_section_support_or_spread_invalid")

    neck_center = _mean_xy(neck_measurements)
    closure_center = _mean_xy(closure_measurements)
    misalignment = math.hypot(
        neck_center[0] - closure_center[0], neck_center[1] - closure_center[1]
    )
    axis_origin = (neck_center[0], neck_center[1], 0.0)
    neck_z = max(item.center[2] for item in neck_measurements)
    closure_z = min(item.center[2] for item in closure_measurements)
    reference_set_id = _reference_id(neck_feature_id, closure_feature_id)
    neck_plane = _plane(
        reference_set_id,
        neck_feature_id,
        "neck_reference_plane",
        axis_origin,
        neck_z,
        neck_measurements,
    )
    closure_plane = _plane(
        reference_set_id,
        closure_feature_id,
        "closure_reference_plane",
        (closure_center[0], closure_center[1], axis_origin[2]),
        closure_z,
        closure_measurements,
    )
    offset = closure_z - neck_z
    if misalignment > policy.maximum_axis_misalignment:
        return MatingReferenceResult(
            MatingReferenceStatus.AXIS_MISMATCH_REVIEW_REQUIRED,
            ("neck_and_closure_axes_exceed_alignment_policy",),
            scan_master.revision_id,
            mesh_sha256(scan_master.mesh),
            model.revision_id,
            neck_feature_id,
            closure_feature_id,
            reference_set_id,
            axis_origin,
            (0.0, 0.0, 1.0),
            neck_plane,
            closure_plane,
            offset,
            misalignment,
            None,
            model.coordinate_unit,
            True,
            policy,
        )

    payload = {
        "contract": MATING_REFERENCE_CONTRACT,
        "reference_set_id": reference_set_id,
        "source_model_revision_id": model.revision_id,
        "scan_master_revision_id": scan_master.revision_id,
        "scan_master_geometry_sha256": mesh_sha256(scan_master.mesh),
        "neck_feature_id": neck_feature.feature_id,
        "closure_feature_id": closure_feature.feature_id,
        "canonical_axis_origin": list(axis_origin),
        "canonical_axis_direction": [0.0, 0.0, 1.0],
        "neck_plane": neck_plane.as_dict(),
        "closure_plane": closure_plane.as_dict(),
        "inter_plane_offset": offset,
        "axis_misalignment": misalignment,
        "neck_support_count": sum(item.sample_count for item in neck_measurements),
        "closure_support_count": sum(item.sample_count for item in closure_measurements),
        "neck_maximum_residual": max(item.maximum_radial_residual for item in neck_measurements),
        "closure_maximum_residual": max(
            item.maximum_radial_residual for item in closure_measurements
        ),
        "coordinate_unit": model.coordinate_unit,
        "thread_compatibility_claimed": False,
        "seal_compatibility_claimed": False,
        "manufacturing_alignment_claimed": False,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
    }
    parameter = DesignModelParameter(
        "mating_reference_" + reference_set_id.removeprefix("mating-reference:"),
        payload,
        ParameterType.OBJECT,
    )
    existing = tuple(
        item for item in model.parameters if item.parameter_id != parameter.parameter_id
    )
    try:
        updated = revise_design_model_revision(
            model,
            parameters=(*existing, parameter),
            features=model.features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise MatingReferenceError("mating_reference_model_revision_invalid") from error
    return MatingReferenceResult(
        MatingReferenceStatus.ALIGNED,
        ("parent_bound_axis_and_reference_planes_created",),
        scan_master.revision_id,
        mesh_sha256(scan_master.mesh),
        model.revision_id,
        neck_feature.feature_id,
        closure_feature.feature_id,
        reference_set_id,
        axis_origin,
        (0.0, 0.0, 1.0),
        neck_plane,
        closure_plane,
        offset,
        misalignment,
        updated,
        model.coordinate_unit,
        False,
        policy,
    )


def _validate_parents(
    scan_master: ScanMasterRevision,
    geometry: NormalizedMeasurementGeometry,
    model: DesignModelRevision,
    expected_scan_master_revision_id: str,
    expected_model_revision_id: str,
) -> None:
    if not isinstance(scan_master, ScanMasterRevision):
        raise MatingReferenceError("scan_master_revision_required")
    if not isinstance(geometry, NormalizedMeasurementGeometry):
        raise MatingReferenceError("normalized_capture_geometry_required")
    if not isinstance(model, DesignModelRevision):
        raise MatingReferenceError("design_model_revision_required")
    digest = mesh_sha256(scan_master.mesh)
    manifest = scan_master.manifest
    if (
        scan_master.revision_id != expected_scan_master_revision_id
        or manifest.get("scan_master_revision_id") != scan_master.revision_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != digest
        or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or manifest.get("mold_use_authorized") is not False
    ):
        raise MatingReferenceError("selected_scan_master_parent_stale_or_invalid")
    raw_scale = manifest.get("scale_state")
    if not isinstance(raw_scale, str):
        raise MatingReferenceError("scan_master_scale_state_invalid")
    try:
        scale_state = ScaleState(raw_scale)
    except ValueError as error:
        raise MatingReferenceError("scan_master_scale_state_invalid") from error
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise MatingReferenceError("scan_master_scale_state_unauthorized")
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    if (
        geometry.source_geometry_id != manifest.get("parent_object_geometry_revision_id")
        or geometry.scale_state is not scale_state
        or geometry.scale_provenance_id != manifest.get("scale_provenance_id")
        or geometry.coordinate_unit != unit
        or geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY"
        or geometry.generated is not False
    ):
        raise MatingReferenceError("capture_geometry_parent_or_authority_mismatch")
    if (
        model.revision_id != expected_model_revision_id
        or model.project_id != scan_master.project_id
        or model.fitted_to_scan_master_revision_id != scan_master.revision_id
        or model.scan_master_geometry_sha256 != digest
        or model.scale_state is not scale_state
        or model.coordinate_unit != unit
        or model.scale_provenance_id != manifest.get("scale_provenance_id")
        or model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or model.mold_use_authorized is not False
    ):
        raise MatingReferenceError("design_model_parent_or_authority_mismatch")


def _resolve_feature(
    model: DesignModelRevision, feature_id: str, role: str
) -> DesignModelFeatureReference:
    try:
        feature = resolve_design_model_feature(model, feature_id)
    except DesignModelError as error:
        raise MatingReferenceError(f"{role}_feature_stale_or_ambiguous") from error
    allowed = {FeatureKind.NECK, FeatureKind.FINISH} if role == "neck" else {FeatureKind.CAP}
    if feature.feature_kind not in allowed:
        raise MatingReferenceError(f"{role}_feature_kind_invalid")
    return feature


def _measure_sections(
    geometry: NormalizedMeasurementGeometry,
    selections: tuple[CrossSectionSelection, ...],
    role: str,
    policy: MatingReferencePolicy,
) -> tuple[CrossSectionMeasurement, ...]:
    if not isinstance(selections, tuple) or any(
        not isinstance(item, CrossSectionSelection) for item in selections
    ):
        raise MatingReferenceError(f"{role}_section_selections_must_be_immutable_tuple")
    if len(selections) > 128:
        raise MatingReferenceError(f"{role}_section_count_out_of_bounds")
    if len({item.selection_id for item in selections}) != len(selections):
        raise MatingReferenceError(f"{role}_section_selection_ids_not_unique")
    measured: list[CrossSectionMeasurement] = []
    for selection in selections:
        if (
            selection.source_geometry_id != geometry.source_geometry_id
            or selection.normalized_geometry_revision != geometry.normalized_geometry_revision
            or selection.plane_normal != (0.0, 0.0, 1.0)
            or selection.planarity_tolerance > policy.maximum_radial_residual
        ):
            raise MatingReferenceError(f"{role}_section_parent_or_plane_invalid")
        try:
            section = measure_cross_section(
                geometry,
                selection,
                current_geometry_id=geometry.source_geometry_id,
                current_normalized_geometry_revision=geometry.normalized_geometry_revision,
                current_scale_provenance_id=geometry.scale_provenance_id,
            )
        except ValueError as error:
            raise MatingReferenceError(f"{role}_cross_section_rejected:{error}") from error
        if (
            section.method_version != CROSS_SECTION_METHOD_VERSION
            or section.sample_count < policy.minimum_points_per_section
            or section.maximum_radial_residual > policy.maximum_radial_residual
        ):
            raise MatingReferenceError(f"{role}_section_quality_invalid")
        measured.append(section)
    if len({item.center[2] for item in measured}) != len(measured):
        raise MatingReferenceError(f"{role}_section_heights_not_unique")
    return tuple(measured)


def _enough_and_spread(
    sections: tuple[CrossSectionMeasurement, ...], policy: MatingReferencePolicy
) -> bool:
    if len(sections) < policy.minimum_sections_per_feature:
        return False
    center = _mean_xy(sections)
    return all(
        math.hypot(item.center[0] - center[0], item.center[1] - center[1])
        <= policy.maximum_axis_center_spread
        for item in sections
    )


def _mean_xy(sections: tuple[CrossSectionMeasurement, ...]) -> tuple[float, float]:
    return (
        math.fsum(item.center[0] for item in sections) / len(sections),
        math.fsum(item.center[1] for item in sections) / len(sections),
    )


def _reference_id(neck_feature_id: str, closure_feature_id: str) -> str:
    payload = f"{MATING_REFERENCE_CONTRACT}:{neck_feature_id}:{closure_feature_id}"
    return "mating-reference:" + hashlib.sha256(payload.encode()).hexdigest()


def _plane(
    reference_set_id: str,
    feature_id: str,
    role: str,
    axis_origin: tuple[float, float, float],
    z_value: float,
    measurements: tuple[CrossSectionMeasurement, ...],
) -> MatingReferencePlane:
    plane_id = (
        "mating-plane:"
        + hashlib.sha256(f"{reference_set_id}:{role}:{feature_id}".encode()).hexdigest()
    )
    return MatingReferencePlane(
        plane_id,
        feature_id,
        role,
        (axis_origin[0], axis_origin[1], z_value),
        (0.0, 0.0, 1.0),
        z_value - axis_origin[2],
        tuple(item.measurement_id for item in measurements),
    )


__all__ = [
    "MATING_REFERENCE_CONTRACT",
    "MatingReferenceError",
    "MatingReferencePlane",
    "MatingReferencePolicy",
    "MatingReferenceResult",
    "MatingReferenceStatus",
    "create_neck_closure_mating_references",
]
