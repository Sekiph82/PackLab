"""Evidence-gated parametric fit for a simple cylindrical screw-cap exterior."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import StrEnum

from .closure_separation_candidates import (
    ClosureComponentCandidate,
    ClosureSeparationResult,
    ClosureSeparationStatus,
)
from .cross_section_measurement import CROSS_SECTION_METHOD_VERSION, CrossSectionMeasurement
from .design_model import (
    DesignModelError,
    DesignModelParameter,
    DesignModelRevision,
    ParameterType,
    revise_design_model_revision,
)
from .design_profile_fit import DesignModelProfileFit
from .design_profile_zones import (
    DesignProfileZones,
    ProfileZoneError,
    ProfileZoneStatus,
    detect_design_profile_zones,
)
from .neck_finish_candidates import NeckFinishCandidateSet
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

SCREW_CAP_EXTERIOR_CONTRACT = "packlab.screw-cap-exterior-fit.v1"


class ScrewCapExteriorFitError(ValueError):
    """Raised when inputs are stale or lack the authority required for fitting."""


class ScrewCapExteriorFitStatus(StrEnum):
    FITTED = "FITTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class ScrewCapExteriorFitPolicy:
    minimum_sections: int = 3
    minimum_points_per_section: int = 12
    maximum_radial_residual: float = 0.25
    maximum_ellipse_relative_difference: float = 0.08
    minimum_section_span: float = 0.25

    def __post_init__(self) -> None:
        for name in ("minimum_sections", "minimum_points_per_section"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                raise ScrewCapExteriorFitError(f"{name}_invalid")
        for name in (
            "maximum_radial_residual",
            "maximum_ellipse_relative_difference",
            "minimum_section_span",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0.0
            ):
                raise ScrewCapExteriorFitError(f"{name}_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.screw-cap-exterior-fit-policy.v1",
            "minimum_sections": self.minimum_sections,
            "minimum_points_per_section": self.minimum_points_per_section,
            "maximum_radial_residual": self.maximum_radial_residual,
            "maximum_ellipse_relative_difference": self.maximum_ellipse_relative_difference,
            "minimum_section_span": self.minimum_section_span,
        }


@dataclass(frozen=True, slots=True)
class ScrewCapExteriorFitResult:
    status: ScrewCapExteriorFitStatus
    reasons: tuple[str, ...]
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    closure_candidate_feature_id: str
    section_measurement_ids: tuple[str, ...]
    model: DesignModelRevision | None
    parameters: tuple[tuple[str, float], ...]
    maximum_radial_residual: float | None
    rms_radial_residual: float | None
    support_point_count: int
    review_required: bool
    policy: ScrewCapExteriorFitPolicy

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": SCREW_CAP_EXTERIOR_CONTRACT,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "closure_candidate_feature_id": self.closure_candidate_feature_id,
                "cross_section_measurement_ids": list(self.section_measurement_ids),
            },
            "parameters": {key: value for key, value in self.parameters},
            "residual_support": {
                "maximum_radial_residual": self.maximum_radial_residual,
                "rms_radial_residual": self.rms_radial_residual,
                "support_section_count": len(self.section_measurement_ids),
                "support_point_count": self.support_point_count,
            },
            "model_revision_id": self.model.revision_id if self.model else None,
            "review_required": self.review_required,
            "thread_standard_inferred": False,
            "internal_thread_geometry_inferred": False,
            "seal_performance_inferred": False,
            "manufacturing_dimensions_inferred": False,
            "gross_knurl_envelope_observed": False,
            "scan_master_mutated": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "policy": self.policy.as_dict(),
        }


def fit_screw_cap_exterior(
    scan_master: ScanMasterRevision,
    closure: ClosureSeparationResult,
    neck_finish: NeckFinishCandidateSet,
    profile_fit: DesignModelProfileFit,
    profile_zones: DesignProfileZones,
    section_measurements: tuple[CrossSectionMeasurement, ...],
    *,
    expected_scan_master_revision_id: str,
    expected_model_revision_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    policy: ScrewCapExteriorFitPolicy = ScrewCapExteriorFitPolicy(),
) -> ScrewCapExteriorFitResult:
    """Fit only a supported cylindrical exterior, keeping the Scan Master untouched."""
    model, candidate = _validate_parents(
        scan_master,
        closure,
        neck_finish,
        profile_fit,
        profile_zones,
        expected_scan_master_revision_id,
        expected_model_revision_id,
    )
    if not isinstance(policy, ScrewCapExteriorFitPolicy):
        raise ScrewCapExteriorFitError("screw_cap_fit_policy_invalid")
    if not isinstance(section_measurements, tuple) or any(
        not isinstance(item, CrossSectionMeasurement) for item in section_measurements
    ):
        raise ScrewCapExteriorFitError("cross_section_measurements_must_be_immutable_tuple")

    z_min, z_max = candidate.z_range
    if not math.isfinite(z_min) or not math.isfinite(z_max) or z_max <= z_min or z_min < 0.0:
        raise ScrewCapExteriorFitError("closure_candidate_z_range_invalid")
    sections = tuple(sorted(section_measurements, key=lambda item: item.center[2]))
    _validate_sections(
        scan_master,
        sections,
        candidate,
        neck_finish.normalized_geometry_revision,
        policy,
    )
    if not sections:
        return _result(
            ScrewCapExteriorFitStatus.REVIEW_REQUIRED,
            ("cross_section_support_missing",),
            scan_master,
            candidate,
            sections,
            None,
            (),
            None,
            None,
            0,
            policy,
        )
    z_values = tuple(item.center[2] for item in sections)
    span = z_values[-1] - z_values[0] if len(z_values) > 1 else 0.0
    mean_major = math.fsum(item.major_radius for item in sections) / len(sections)
    mean_minor = math.fsum(item.minor_radius for item in sections) / len(sections)
    relative_ellipse_difference = abs(mean_major - mean_minor) / max(mean_major, mean_minor)
    max_residual = max(item.maximum_radial_residual for item in sections)
    rms_residual = math.sqrt(
        math.fsum(item.rms_radial_residual**2 for item in sections) / len(sections)
    )
    reasons: list[str] = []
    if len(sections) < policy.minimum_sections:
        reasons.append("cross_section_support_sparse")
    if span < policy.minimum_section_span:
        reasons.append("cross_section_axial_span_insufficient")
    if relative_ellipse_difference > policy.maximum_ellipse_relative_difference:
        reasons.append("cross_sections_are_not_cylindrical_enough")
    if max_residual > policy.maximum_radial_residual:
        reasons.append("cross_section_residual_exceeds_policy")
    if reasons:
        return _result(
            ScrewCapExteriorFitStatus.REVIEW_REQUIRED,
            tuple(reasons),
            scan_master,
            candidate,
            sections,
            None,
            (),
            max_residual,
            rms_residual,
            sum(item.sample_count for item in sections),
            policy,
        )

    parameters = (
        ("screw_cap_exterior_diameter", mean_major + mean_minor),
        ("screw_cap_exterior_height", z_max - z_min),
        (
            "screw_cap_exterior_center_x",
            math.fsum(item.center[0] for item in sections) / len(sections),
        ),
        (
            "screw_cap_exterior_center_y",
            math.fsum(item.center[1] for item in sections) / len(sections),
        ),
        ("screw_cap_exterior_base_z", z_min),
    )
    unit = model.coordinate_unit
    parameter_id = (
        "screw_cap_exterior_"
        + hashlib.sha256(
            f"{scan_master.revision_id}:{candidate.component_id}".encode()
        ).hexdigest()[:24]
    )
    parameter = DesignModelParameter(
        parameter_id,
        {
            "contract": SCREW_CAP_EXTERIOR_CONTRACT,
            "component_id": candidate.component_id,
            "feature_id": candidate.feature.feature_id,
            "parameters": {key: value for key, value in parameters},
            "parameter_unit": unit,
            "section_measurement_ids": [item.measurement_id for item in sections],
            "support_point_count": sum(item.sample_count for item in sections),
            "maximum_radial_residual": max_residual,
            "rms_radial_residual": rms_residual,
            "fit_method": "mean principal radii across parent-bound captured horizontal sections",
            "review_required": True,
            "thread_standard_inferred": False,
            "internal_thread_geometry_inferred": False,
            "seal_performance_inferred": False,
            "manufacturing_dimensions_inferred": False,
            "gross_knurl_envelope_observed": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
        ParameterType.OBJECT,
    )
    existing = tuple(item for item in model.parameters if item.parameter_id != parameter_id)
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
        raise ScrewCapExteriorFitError("screw_cap_exterior_model_revision_invalid") from error
    return _result(
        ScrewCapExteriorFitStatus.FITTED,
        ("supported_cylindrical_exterior_fit_created",),
        scan_master,
        candidate,
        sections,
        updated,
        parameters,
        max_residual,
        rms_residual,
        sum(item.sample_count for item in sections),
        policy,
    )


def _validate_parents(
    scan_master: ScanMasterRevision,
    closure: ClosureSeparationResult,
    neck_finish: NeckFinishCandidateSet,
    profile_fit: DesignModelProfileFit,
    profile_zones: DesignProfileZones,
    expected_scan_master_revision_id: str,
    expected_model_revision_id: str,
) -> tuple[DesignModelRevision, ClosureComponentCandidate]:
    if not isinstance(scan_master, ScanMasterRevision):
        raise ScrewCapExteriorFitError("scan_master_revision_required")
    if not isinstance(closure, ClosureSeparationResult):
        raise ScrewCapExteriorFitError("closure_separation_result_required")
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
        raise ScrewCapExteriorFitError("selected_scan_master_parent_stale_or_invalid")
    raw_scale_state = manifest.get("scale_state")
    if not isinstance(raw_scale_state, str):
        raise ScrewCapExteriorFitError("scan_master_scale_state_invalid")
    try:
        scale_state = ScaleState(raw_scale_state)
    except ValueError as error:
        raise ScrewCapExteriorFitError("scan_master_scale_state_invalid") from error
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise ScrewCapExteriorFitError("scan_master_scale_state_unauthorized")
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    model = closure.model
    if (
        closure.status is not ClosureSeparationStatus.CANDIDATE_CREATED
        or closure.scan_master_revision_id != scan_master.revision_id
        or closure.scan_master_geometry_sha256 != digest
        or closure.neck_finish_result_id != neck_finish.result_id
        or closure.profile_fit_id != profile_fit.fit_id
        or closure.profile_zone_revision_id != profile_zones.revision_id
        or not isinstance(model, DesignModelRevision)
        or model.revision_id != expected_model_revision_id
        or model.previous_revision_id != closure.parent_model_revision_id
        or model.fitted_to_scan_master_revision_id != scan_master.revision_id
        or model.scan_master_geometry_sha256 != digest
        or model.scale_state is not scale_state
        or model.coordinate_unit != unit
        or model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or model.mold_use_authorized is not False
    ):
        raise ScrewCapExteriorFitError("closure_candidate_parent_or_authority_mismatch")
    candidates = tuple(item for item in closure.candidates if item.role == "closure-candidate")
    if len(candidates) != 1 or sum(item.role == "body" for item in closure.candidates) != 1:
        raise ScrewCapExteriorFitError("unique_closure_candidate_required")
    candidate = candidates[0]
    if (
        candidate.feature.feature_kind.value != "cap"
        or candidate.feature.component_id != candidate.component_id
        or candidate.feature not in model.features
        or candidate.triangle_count < 1
        or candidate.vertex_count < 5
        or candidate.z_range[1] <= candidate.z_range[0]
    ):
        raise ScrewCapExteriorFitError("closure_candidate_support_invalid")
    binding = profile_fit.parent_binding
    if (
        profile_fit.scan_master_revision_id != scan_master.revision_id
        or profile_fit.scan_master_geometry_sha256 != digest
        or profile_fit.parent_binding is None
        or binding.fitted_to_scan_master_revision_id != scan_master.revision_id
        or binding.scan_master_geometry_sha256 != digest
        or profile_fit.status.value != "FITTED"
        or profile_fit.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or profile_fit.mold_use_authorized is not False
        or profile_zones.review_required
        or profile_zones.status is not ProfileZoneStatus.DETECTED
        or profile_zones.fit_id != profile_fit.fit_id
        or profile_zones.scan_master_revision_id != scan_master.revision_id
        or profile_zones.scan_master_geometry_sha256 != digest
        or profile_zones.parent_binding_revision_id != binding.revision_id
        or neck_finish.source_geometry_id != manifest.get("parent_object_geometry_revision_id")
        or neck_finish.scale_provenance_id != manifest.get("scale_provenance_id")
        or neck_finish.scale_state is not scale_state
        or neck_finish.coordinate_unit != unit
    ):
        raise ScrewCapExteriorFitError("accepted_profile_or_neck_finish_evidence_required")
    try:
        expected_zones = detect_design_profile_zones(
            profile_fit,
            expected_fit_id=profile_fit.fit_id,
            component_id=profile_zones.boundaries[0].component_id,
        )
    except (ProfileZoneError, IndexError) as error:
        raise ScrewCapExteriorFitError("profile_zone_evidence_invalid") from error
    if expected_zones != profile_zones:
        raise ScrewCapExteriorFitError("profile_zone_evidence_identity_invalid")
    supported_neck_bands = tuple(
        item
        for item in neck_finish.candidates
        if item.candidate_type == "NARROW_REGION_CANDIDATE"
        and not item.ambiguity_review_required
        and item.supported_section_count >= 2
        and item.captured_point_support_count >= 16
        and item.section_z_range[0] <= candidate.z_range[1]
        and item.section_z_range[1] >= candidate.z_range[0]
    )
    if len(supported_neck_bands) != 1:
        raise ScrewCapExteriorFitError("unique_supported_neck_finish_band_required")
    return model, candidate


def _validate_sections(
    scan_master: ScanMasterRevision,
    sections: tuple[CrossSectionMeasurement, ...],
    candidate: ClosureComponentCandidate,
    expected_normalized_geometry_revision: str,
    policy: ScrewCapExteriorFitPolicy,
) -> None:
    manifest = scan_master.manifest
    if len({item.measurement_id for item in sections}) != len(sections):
        raise ScrewCapExteriorFitError("duplicate_cross_section_measurement")
    if len({item.center[2] for item in sections}) != len(sections):
        raise ScrewCapExteriorFitError("duplicate_cross_section_height")
    for item in sections:
        numeric = (
            *item.center,
            item.major_radius,
            item.minor_radius,
            item.maximum_radial_residual,
            item.rms_radial_residual,
            item.maximum_planarity_residual,
        )
        if (
            item.source_geometry_id != manifest.get("parent_object_geometry_revision_id")
            or item.normalized_geometry_revision != expected_normalized_geometry_revision
            or item.scale_provenance_id != manifest.get("scale_provenance_id")
            or item.scale_state.value != manifest.get("scale_state")
            or item.coordinate_unit
            != (
                "reconstruction_units"
                if item.scale_state is ScaleState.RELATIVE
                else "mm_unverified"
            )
            or item.method_version != CROSS_SECTION_METHOD_VERSION
            or item.sample_count < policy.minimum_points_per_section
            or not all(math.isfinite(value) for value in numeric)
            or min(item.major_radius, item.minor_radius) <= 0.0
            or min(
                item.maximum_radial_residual,
                item.rms_radial_residual,
                item.maximum_planarity_residual,
            )
            < 0.0
            or not candidate.z_range[0] <= item.center[2] <= candidate.z_range[1]
        ):
            raise ScrewCapExteriorFitError("cross_section_parent_quality_or_range_invalid")


def _result(
    status: ScrewCapExteriorFitStatus,
    reasons: tuple[str, ...],
    scan_master: ScanMasterRevision,
    candidate: ClosureComponentCandidate,
    sections: tuple[CrossSectionMeasurement, ...],
    model: DesignModelRevision | None,
    parameters: tuple[tuple[str, float], ...],
    maximum_residual: float | None,
    rms_residual: float | None,
    support_count: int,
    policy: ScrewCapExteriorFitPolicy,
) -> ScrewCapExteriorFitResult:
    return ScrewCapExteriorFitResult(
        status,
        reasons,
        scan_master.revision_id,
        mesh_sha256(scan_master.mesh),
        candidate.feature.feature_id,
        tuple(item.measurement_id for item in sections),
        model,
        parameters,
        maximum_residual,
        rms_residual,
        support_count,
        True,
        policy,
    )


__all__ = [
    "ScrewCapExteriorFitError",
    "ScrewCapExteriorFitPolicy",
    "ScrewCapExteriorFitResult",
    "ScrewCapExteriorFitStatus",
    "fit_screw_cap_exterior",
]
