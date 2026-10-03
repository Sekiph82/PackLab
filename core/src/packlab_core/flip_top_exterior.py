"""Observed exterior component parameters for a simple flip-top closure."""

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
    revise_design_model_revision,
    stable_feature_id,
)
from .design_profile_fit import DesignModelProfileFit, ProfileFitStatus
from .design_profile_zones import (
    DesignProfileZones,
    ProfileZoneError,
    ProfileZoneStatus,
    detect_design_profile_zones,
)
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

FLIP_TOP_EXTERIOR_CONTRACT = "packlab.flip-top-exterior.v1"


class FlipTopExteriorError(ValueError):
    """Raised when a flip-top exterior input is stale or lacks captured support."""


class FlipTopExteriorStatus(StrEnum):
    FITTED = "FITTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class FlipTopExteriorPolicy:
    minimum_sections_per_region: int = 2
    minimum_points_per_section: int = 12
    maximum_radial_residual: float = 0.25
    maximum_ellipse_relative_difference: float = 0.12
    maximum_region_radius_relative_spread: float = 0.12
    maximum_region_center_spread: float = 0.5

    def __post_init__(self) -> None:
        for name in ("minimum_sections_per_region", "minimum_points_per_section"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                raise FlipTopExteriorError(f"{name}_invalid")
        for name in (
            "maximum_radial_residual",
            "maximum_ellipse_relative_difference",
            "maximum_region_radius_relative_spread",
            "maximum_region_center_spread",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0.0
            ):
                raise FlipTopExteriorError(f"{name}_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.flip-top-exterior-policy.v1",
            "minimum_sections_per_region": self.minimum_sections_per_region,
            "minimum_points_per_section": self.minimum_points_per_section,
            "maximum_radial_residual": self.maximum_radial_residual,
            "maximum_ellipse_relative_difference": self.maximum_ellipse_relative_difference,
            "maximum_region_radius_relative_spread": self.maximum_region_radius_relative_spread,
            "maximum_region_center_spread": self.maximum_region_center_spread,
        }


@dataclass(frozen=True, slots=True)
class FlipTopExteriorResult:
    status: FlipTopExteriorStatus
    reasons: tuple[str, ...]
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    feature: DesignModelFeatureReference
    base_measurement_ids: tuple[str, ...]
    lid_measurement_ids: tuple[str, ...]
    hinge_reference_measurement_ids: tuple[str, ...]
    model: DesignModelRevision | None
    base_diameter: float | None
    lid_envelope_diameter: float | None
    base_z_range: tuple[float, float] | None
    lid_z_range: tuple[float, float] | None
    hinge_reference_center: tuple[float, float, float] | None
    coordinate_unit: str
    review_required: bool
    policy: FlipTopExteriorPolicy

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": FLIP_TOP_EXTERIOR_CONTRACT,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "feature_id": self.feature.feature_id,
            },
            "exterior": {
                "base_diameter": self.base_diameter,
                "lid_envelope_diameter": self.lid_envelope_diameter,
                "base_z_range": list(self.base_z_range) if self.base_z_range else None,
                "lid_z_range": list(self.lid_z_range) if self.lid_z_range else None,
                "coordinate_unit": self.coordinate_unit,
            },
            "hinge_reference_region": {
                "center": list(self.hinge_reference_center)
                if self.hinge_reference_center
                else None,
                "selection_count": len(self.hinge_reference_measurement_ids),
                "hinge_mechanism_confirmed": False,
                "reference_is_observed_section_center": True,
            },
            "measurement_ids": {
                "base": list(self.base_measurement_ids),
                "lid": list(self.lid_measurement_ids),
                "hinge_reference": list(self.hinge_reference_measurement_ids),
            },
            "model_revision_id": self.model.revision_id if self.model else None,
            "review_required": self.review_required,
            "latch_inferred": False,
            "seal_performance_inferred": False,
            "internal_mechanism_inferred": False,
            "wall_thickness_inferred": False,
            "manufacturing_dimensions_inferred": False,
            "scan_master_mutated": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "policy": self.policy.as_dict(),
        }


def fit_flip_top_exterior(
    scan_master: ScanMasterRevision,
    geometry: NormalizedMeasurementGeometry,
    profile_fit: DesignModelProfileFit,
    profile_zones: DesignProfileZones,
    model: DesignModelRevision,
    base_selections: tuple[CrossSectionSelection, ...],
    lid_selections: tuple[CrossSectionSelection, ...],
    hinge_reference_selections: tuple[CrossSectionSelection, ...],
    *,
    expected_scan_master_revision_id: str,
    expected_model_revision_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    policy: FlipTopExteriorPolicy = FlipTopExteriorPolicy(),
) -> FlipTopExteriorResult:
    """Create a review-required editable exterior component from selected sections.

    Selection groups are caller-specified surface references. In particular,
    `hinge_reference_selections` identify an observed reference region only;
    they do not prove a hinge, joint, latch, or mechanism.
    """
    _validate_parents(
        scan_master,
        geometry,
        profile_fit,
        profile_zones,
        model,
        expected_scan_master_revision_id,
        expected_model_revision_id,
    )
    if not isinstance(policy, FlipTopExteriorPolicy):
        raise FlipTopExteriorError("flip_top_exterior_policy_invalid")
    groups = (base_selections, lid_selections, hinge_reference_selections)
    if any(
        not isinstance(group, tuple)
        or any(not isinstance(item, CrossSectionSelection) for item in group)
        for group in groups
    ):
        raise FlipTopExteriorError("section_selection_groups_must_be_immutable_tuples")

    all_selections = (*base_selections, *lid_selections, *hinge_reference_selections)
    if len({item.selection_id for item in all_selections}) != len(all_selections):
        raise FlipTopExteriorError("duplicate_section_selection_id")
    measured_groups: list[tuple[CrossSectionMeasurement, ...]] = []
    for label, selections in zip(("base", "lid", "hinge_reference"), groups, strict=True):
        measured_groups.append(
            _measure_group(
                geometry,
                selections,
                label,
                scan_master,
                policy,
            )
        )
    base, lid, hinge = measured_groups

    reasons: list[str] = []
    if not _region_is_consistent(base, policy):
        reasons.append("base_region_measurements_ambiguous")
    if not _region_is_consistent(lid, policy):
        reasons.append("lid_region_measurements_ambiguous")
    if not _region_is_consistent(hinge, policy, check_circularity=False):
        reasons.append("hinge_reference_region_ambiguous")
    if any(len(group) < policy.minimum_sections_per_region for group in measured_groups):
        reasons.append("exterior_region_support_sparse")
    if reasons:
        feature = _feature(scan_master)
        return _result(
            FlipTopExteriorStatus.REVIEW_REQUIRED,
            tuple(reasons),
            scan_master,
            feature,
            base,
            lid,
            hinge,
            None,
            None,
            None,
            None,
            None,
            None,
            policy,
            model.coordinate_unit,
        )

    base_diameter = _mean_diameter(base)
    lid_diameter = _mean_diameter(lid)
    base_z = _z_range(base)
    lid_z = _z_range(lid)
    hinge_center = (
        math.fsum(item.center[0] for item in hinge) / len(hinge),
        math.fsum(item.center[1] for item in hinge) / len(hinge),
        math.fsum(item.center[2] for item in hinge) / len(hinge),
    )
    feature = _feature(scan_master)
    parameter_id = (
        "flip_top_exterior_"
        + hashlib.sha256(f"{scan_master.revision_id}:{feature.component_id}".encode()).hexdigest()[
            :24
        ]
    )
    parameter = DesignModelParameter(
        parameter_id,
        {
            "contract": FLIP_TOP_EXTERIOR_CONTRACT,
            "component_id": feature.component_id,
            "feature_id": feature.feature_id,
            "profile_fit_id": profile_fit.fit_id,
            "profile_zone_revision_id": profile_zones.revision_id,
            "base": {
                "diameter": base_diameter,
                "z_range": list(base_z),
                "measurement_ids": [item.measurement_id for item in base],
                "support": _support_evidence(base),
            },
            "lid_envelope": {
                "diameter": lid_diameter,
                "z_range": list(lid_z),
                "measurement_ids": [item.measurement_id for item in lid],
                "support": _support_evidence(lid),
            },
            "hinge_reference_region": {
                "center": list(hinge_center),
                "measurement_ids": [item.measurement_id for item in hinge],
                "support": _support_evidence(hinge),
                "reference_is_observed_section_center": True,
                "hinge_mechanism_confirmed": False,
            },
            "coordinate_unit": model.coordinate_unit,
            "review_required": True,
            "latch_inferred": False,
            "seal_performance_inferred": False,
            "internal_mechanism_inferred": False,
            "wall_thickness_inferred": False,
            "manufacturing_dimensions_inferred": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
        ParameterType.OBJECT,
    )
    features = {item.feature_id: item for item in model.features}
    prior_feature = features.get(feature.feature_id)
    if prior_feature is not None and prior_feature != feature:
        raise FlipTopExteriorError("stable_flip_top_feature_conflict")
    features[feature.feature_id] = feature
    parameters = tuple(item for item in model.parameters if item.parameter_id != parameter_id)
    try:
        updated_model = revise_design_model_revision(
            model,
            parameters=(*parameters, parameter),
            features=tuple(features.values()),
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise FlipTopExteriorError("flip_top_model_revision_invalid") from error
    return _result(
        FlipTopExteriorStatus.FITTED,
        ("parent_bound_base_lid_and_observed_reference_sections_supported",),
        scan_master,
        feature,
        base,
        lid,
        hinge,
        updated_model,
        base_diameter,
        lid_diameter,
        base_z,
        lid_z,
        hinge_center,
        policy,
        model.coordinate_unit,
    )


def _validate_parents(
    scan_master: ScanMasterRevision,
    geometry: NormalizedMeasurementGeometry,
    profile_fit: DesignModelProfileFit,
    profile_zones: DesignProfileZones,
    model: DesignModelRevision,
    expected_scan_master_revision_id: str,
    expected_model_revision_id: str,
) -> None:
    if not isinstance(scan_master, ScanMasterRevision):
        raise FlipTopExteriorError("scan_master_revision_required")
    if not isinstance(geometry, NormalizedMeasurementGeometry):
        raise FlipTopExteriorError("normalized_capture_geometry_required")
    if not isinstance(profile_fit, DesignModelProfileFit):
        raise FlipTopExteriorError("design_model_profile_fit_required")
    if not isinstance(profile_zones, DesignProfileZones):
        raise FlipTopExteriorError("design_profile_zones_required")
    if not isinstance(model, DesignModelRevision):
        raise FlipTopExteriorError("design_model_revision_required")
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
        raise FlipTopExteriorError("selected_scan_master_parent_stale_or_invalid")
    raw_state = manifest.get("scale_state")
    if not isinstance(raw_state, str):
        raise FlipTopExteriorError("scan_master_scale_state_invalid")
    try:
        scale_state = ScaleState(raw_state)
    except ValueError as error:
        raise FlipTopExteriorError("scan_master_scale_state_invalid") from error
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise FlipTopExteriorError("scan_master_scale_state_unauthorized")
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    binding = profile_fit.parent_binding
    if (
        geometry.source_geometry_id != manifest.get("parent_object_geometry_revision_id")
        or geometry.scale_state is not scale_state
        or geometry.scale_provenance_id != manifest.get("scale_provenance_id")
        or geometry.coordinate_unit != unit
        or geometry.generated is not False
        or geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY"
    ):
        raise FlipTopExteriorError("capture_geometry_parent_or_authority_mismatch")
    if (
        profile_fit.status is not ProfileFitStatus.FITTED
        or profile_fit.profile is None
        or profile_fit.scan_master_revision_id != scan_master.revision_id
        or profile_fit.scan_master_geometry_sha256 != digest
        or binding.fitted_to_scan_master_revision_id != scan_master.revision_id
        or binding.scan_master_geometry_sha256 != digest
        or binding.project_id != scan_master.project_id
        or profile_fit.coordinate_unit != unit
        or profile_fit.profile.scale_state is not scale_state
        or profile_fit.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or profile_fit.mold_use_authorized is not False
    ):
        raise FlipTopExteriorError("profile_fit_parent_or_authority_mismatch")
    if (
        profile_zones.status is not ProfileZoneStatus.DETECTED
        or profile_zones.review_required
        or profile_zones.fit_id != profile_fit.fit_id
        or profile_zones.scan_master_revision_id != scan_master.revision_id
        or profile_zones.scan_master_geometry_sha256 != digest
        or profile_zones.parent_binding_revision_id != binding.revision_id
        or profile_zones.coordinate_unit != unit
    ):
        raise FlipTopExteriorError("profile_zones_stale_or_ambiguous")
    try:
        expected_zones = detect_design_profile_zones(
            profile_fit,
            expected_fit_id=profile_fit.fit_id,
            component_id=profile_zones.boundaries[0].component_id,
        )
    except (ProfileZoneError, IndexError) as error:
        raise FlipTopExteriorError("profile_zone_evidence_invalid") from error
    if expected_zones != profile_zones:
        raise FlipTopExteriorError("profile_zone_evidence_identity_invalid")
    if (
        model.revision_id != expected_model_revision_id
        or model.project_id != scan_master.project_id
        or model.parent_binding_revision_id != binding.revision_id
        or model.fitted_to_scan_master_revision_id != scan_master.revision_id
        or model.scan_master_geometry_sha256 != digest
        or model.scale_state is not scale_state
        or model.coordinate_unit != unit
        or model.scale_provenance_id != manifest.get("scale_provenance_id")
        or model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or model.mold_use_authorized is not False
    ):
        raise FlipTopExteriorError("design_model_parent_or_authority_mismatch")


def _measure_group(
    geometry: NormalizedMeasurementGeometry,
    selections: tuple[CrossSectionSelection, ...],
    label: str,
    scan_master: ScanMasterRevision,
    policy: FlipTopExteriorPolicy,
) -> tuple[CrossSectionMeasurement, ...]:
    if len(selections) > 128:
        raise FlipTopExteriorError(f"{label}_section_count_out_of_bounds")
    measured: list[CrossSectionMeasurement] = []
    for selection in selections:
        if (
            selection.source_geometry_id != geometry.source_geometry_id
            or selection.normalized_geometry_revision != geometry.normalized_geometry_revision
            or selection.plane_normal != (0.0, 0.0, 1.0)
            or selection.planarity_tolerance > policy.maximum_radial_residual
        ):
            raise FlipTopExteriorError(f"{label}_section_selection_parent_or_plane_invalid")
        try:
            section = measure_cross_section(
                geometry,
                selection,
                current_geometry_id=geometry.source_geometry_id,
                current_normalized_geometry_revision=geometry.normalized_geometry_revision,
                current_scale_provenance_id=geometry.scale_provenance_id,
            )
        except ValueError as error:
            raise FlipTopExteriorError(f"{label}_cross_section_rejected:{error}") from error
        if (
            section.method_version != CROSS_SECTION_METHOD_VERSION
            or section.sample_count < policy.minimum_points_per_section
            or section.center[2] != selection.plane_origin[2]
            or not math.isfinite(section.maximum_radial_residual)
            or section.maximum_radial_residual > policy.maximum_radial_residual
        ):
            raise FlipTopExteriorError(f"{label}_section_quality_invalid")
        measured.append(section)
    if len({item.center[2] for item in measured}) != len(measured):
        raise FlipTopExteriorError(f"{label}_section_heights_not_unique")
    return tuple(measured)


def _region_is_consistent(
    sections: tuple[CrossSectionMeasurement, ...],
    policy: FlipTopExteriorPolicy,
    *,
    check_circularity: bool = True,
) -> bool:
    if len(sections) < policy.minimum_sections_per_region:
        return False
    center = tuple(
        math.fsum(item.center[axis] for item in sections) / len(sections) for axis in range(2)
    )
    if any(
        math.hypot(item.center[0] - center[0], item.center[1] - center[1])
        > policy.maximum_region_center_spread
        for item in sections
        for item in sections
    ):
        return False
    if check_circularity and any(
        abs(item.major_radius - item.minor_radius) / max(item.major_radius, item.minor_radius)
        > policy.maximum_ellipse_relative_difference
        for item in sections
    ):
        return False
    if check_circularity:
        radii = tuple((item.major_radius + item.minor_radius) / 2.0 for item in sections)
        mean_radius = math.fsum(radii) / len(radii)
        if mean_radius <= 0.0 or any(
            abs(radius - mean_radius) / mean_radius > policy.maximum_region_radius_relative_spread
            for radius in radii
        ):
            return False
    return True


def _mean_diameter(sections: tuple[CrossSectionMeasurement, ...]) -> float:
    return math.fsum(item.major_radius + item.minor_radius for item in sections) / len(sections)


def _support_evidence(sections: tuple[CrossSectionMeasurement, ...]) -> dict[str, object]:
    return {
        "section_count": len(sections),
        "point_count": sum(item.sample_count for item in sections),
        "maximum_radial_residual": max(item.maximum_radial_residual for item in sections),
        "rms_radial_residual": math.sqrt(
            math.fsum(item.rms_radial_residual**2 for item in sections) / len(sections)
        ),
        "coordinate_unit": sections[0].coordinate_unit,
        "scale_uncertainty": sections[0].scale_factor_uncertainty,
        "scale_uncertainty_unit": sections[0].scale_factor_uncertainty_unit,
    }


def _z_range(sections: tuple[CrossSectionMeasurement, ...]) -> tuple[float, float]:
    heights = tuple(item.center[2] for item in sections)
    return min(heights), max(heights)


def _feature(scan_master: ScanMasterRevision) -> DesignModelFeatureReference:
    component_id = (
        "flip_top_"
        + hashlib.sha256(
            f"{scan_master.project_id}:{scan_master.revision_id}:v1".encode()
        ).hexdigest()[:24]
    )
    semantic_key = "flip-top:observed-exterior-component"
    return DesignModelFeatureReference(
        stable_feature_id(component_id, FeatureKind.CAP, semantic_key),
        component_id,
        FeatureKind.CAP,
        semantic_key,
    )


def _result(
    status: FlipTopExteriorStatus,
    reasons: tuple[str, ...],
    scan_master: ScanMasterRevision,
    feature: DesignModelFeatureReference,
    base: tuple[CrossSectionMeasurement, ...],
    lid: tuple[CrossSectionMeasurement, ...],
    hinge: tuple[CrossSectionMeasurement, ...],
    model: DesignModelRevision | None,
    base_diameter: float | None,
    lid_diameter: float | None,
    base_z: tuple[float, float] | None,
    lid_z: tuple[float, float] | None,
    hinge_center: tuple[float, float, float] | None,
    policy: FlipTopExteriorPolicy,
    coordinate_unit: str,
) -> FlipTopExteriorResult:
    return FlipTopExteriorResult(
        status,
        reasons,
        scan_master.revision_id,
        mesh_sha256(scan_master.mesh),
        feature,
        tuple(item.measurement_id for item in base),
        tuple(item.measurement_id for item in lid),
        tuple(item.measurement_id for item in hinge),
        model,
        base_diameter,
        lid_diameter,
        base_z,
        lid_z,
        hinge_center,
        coordinate_unit,
        True,
        policy,
    )


__all__ = [
    "FLIP_TOP_EXTERIOR_CONTRACT",
    "FlipTopExteriorError",
    "FlipTopExteriorPolicy",
    "FlipTopExteriorResult",
    "FlipTopExteriorStatus",
    "fit_flip_top_exterior",
]
