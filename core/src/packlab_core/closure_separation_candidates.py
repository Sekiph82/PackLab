"""Evidence-gated Design Model candidates for already-separated upper components."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import StrEnum

from .component_cleanup import MeshComponent, _components
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
from .neck_finish_candidates import NeckFinishCandidate, NeckFinishCandidateSet
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

CLOSURE_SEPARATION_CONTRACT = "packlab.closure-separation-candidates.v1"
_CANDIDATE_PARAMETER_PREFIX = "closure_separation_candidate_"


class ClosureSeparationError(ValueError):
    """Raised when parent-bound closure separation evidence is stale or invalid."""


class ClosureSeparationStatus(StrEnum):
    CANDIDATE_CREATED = "CANDIDATE_CREATED"
    NO_SEPARATION_EVIDENCE = "NO_SEPARATION_EVIDENCE"
    AMBIGUOUS = "AMBIGUOUS"


def _nonnegative_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0.0
    )


def _unit_interval(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and 0.0 <= value <= 1.0
    )


@dataclass(frozen=True, slots=True)
class ClosureSeparationPolicy:
    minimum_support_sections: int = 2
    minimum_captured_point_support: int = 16
    minimum_component_triangles: int = 20
    minimum_component_triangle_fraction: float = 0.01
    maximum_component_triangle_fraction: float = 0.50
    z_match_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        for name in (
            "minimum_support_sections",
            "minimum_captured_point_support",
            "minimum_component_triangles",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ClosureSeparationError(f"{name}_invalid")
        if not _unit_interval(self.minimum_component_triangle_fraction):
            raise ClosureSeparationError("minimum_component_triangle_fraction_invalid")
        if not _unit_interval(self.maximum_component_triangle_fraction):
            raise ClosureSeparationError("maximum_component_triangle_fraction_invalid")
        if self.maximum_component_triangle_fraction <= self.minimum_component_triangle_fraction:
            raise ClosureSeparationError("component_triangle_fraction_bounds_invalid")
        if not _nonnegative_finite(self.z_match_tolerance):
            raise ClosureSeparationError("z_match_tolerance_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.closure-separation-policy.v1",
            "connectivity_policy": "triangles_share_edge_v1",
            "minimum_support_sections": self.minimum_support_sections,
            "minimum_captured_point_support": self.minimum_captured_point_support,
            "minimum_component_triangles": self.minimum_component_triangles,
            "minimum_component_triangle_fraction": self.minimum_component_triangle_fraction,
            "maximum_component_triangle_fraction": self.maximum_component_triangle_fraction,
            "z_match_tolerance": self.z_match_tolerance,
            "closure_geometry_invented": False,
            "scan_master_split": False,
        }


@dataclass(frozen=True, slots=True)
class ClosureComponentCandidate:
    role: str
    component_id: str
    feature: DesignModelFeatureReference
    source_mesh_component_id: str
    triangle_count: int
    triangle_fraction: float
    vertex_count: int
    z_range: tuple[float, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "component_id": self.component_id,
            "feature": self.feature.as_dict(),
            "review_required": True,
            "source_mesh_component_id": self.source_mesh_component_id,
            "support": {
                "triangle_count": self.triangle_count,
                "triangle_fraction": self.triangle_fraction,
                "vertex_count": self.vertex_count,
            },
            "z_range": list(self.z_range),
            "geometry_copied": False,
            "closure_identity_confirmed": False,
        }


@dataclass(frozen=True, slots=True)
class ClosureSeparationResult:
    status: ClosureSeparationStatus
    reasons: tuple[str, ...]
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    neck_finish_result_id: str
    profile_fit_id: str
    profile_zone_revision_id: str
    parent_model_revision_id: str
    model: DesignModelRevision | None
    candidates: tuple[ClosureComponentCandidate, ...]
    policy: ClosureSeparationPolicy

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": CLOSURE_SEPARATION_CONTRACT,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "neck_finish_result_id": self.neck_finish_result_id,
                "profile_fit_id": self.profile_fit_id,
                "profile_zone_revision_id": self.profile_zone_revision_id,
                "parent_model_revision_id": self.parent_model_revision_id,
            },
            "candidates": [item.as_dict() for item in self.candidates],
            "candidate_count": len(self.candidates),
            "model_revision_id": self.model.revision_id if self.model else None,
            "parent_geometry_preserved": True,
            "scan_master_mutated": False,
            "closure_geometry_invented": False,
            "thread_standard_inferred": False,
            "seal_or_liner_inferred": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "policy": self.policy.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class _ComponentBounds:
    component: MeshComponent
    vertex_indices: tuple[int, ...]
    z_minimum: float
    z_maximum: float
    z_center: float


def create_closure_separation_candidates(
    scan_master: ScanMasterRevision,
    neck_finish: NeckFinishCandidateSet,
    profile_fit: DesignModelProfileFit,
    profile_zones: DesignProfileZones,
    model: DesignModelRevision,
    *,
    expected_scan_master_revision_id: str,
    expected_model_revision_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    policy: ClosureSeparationPolicy = ClosureSeparationPolicy(),
) -> ClosureSeparationResult:
    """Create metadata candidates only for a uniquely supported upper mesh component.

    The source Scan Master is only inspected. No triangles are split, reindexed,
    copied into the model, or promoted as closure geometry.
    """
    _validate_inputs(
        scan_master,
        neck_finish,
        profile_fit,
        profile_zones,
        model,
        expected_scan_master_revision_id,
        expected_model_revision_id,
        policy,
    )
    digest = mesh_sha256(scan_master.mesh)
    try:
        components = _components(scan_master.mesh)
    except (TypeError, ValueError) as error:
        raise ClosureSeparationError(f"scan_component_analysis_rejected:{error}") from error
    if len(components) == 1:
        return _result(
            ClosureSeparationStatus.NO_SEPARATION_EVIDENCE,
            ("scan_has_one_edge_connected_component",),
            scan_master,
            neck_finish,
            profile_fit,
            profile_zones,
            model,
            (),
            policy,
        )
    if len(components) != 2:
        return _result(
            ClosureSeparationStatus.AMBIGUOUS,
            ("scan_has_multiple_possible_upper_components",),
            scan_master,
            neck_finish,
            profile_fit,
            profile_zones,
            model,
            (),
            policy,
        )

    bounds = tuple(_component_bounds(scan_master, item) for item in components)
    upper = max(
        bounds, key=lambda item: (item.z_center, item.z_maximum, item.component.component_id)
    )
    body = next(item for item in bounds if item is not upper)
    if upper.z_maximum <= body.z_maximum or upper.z_center <= body.z_center:
        return _result(
            ClosureSeparationStatus.AMBIGUOUS,
            ("upper_component_ordering_ambiguous",),
            scan_master,
            neck_finish,
            profile_fit,
            profile_zones,
            model,
            (),
            policy,
        )

    total_triangles = len(scan_master.mesh.triangles)
    triangle_fraction = upper.component.triangle_count / total_triangles
    reasons: list[str] = []
    if upper.component.triangle_count < policy.minimum_component_triangles:
        reasons.append("upper_component_triangle_support_insufficient")
    if not (
        policy.minimum_component_triangle_fraction
        <= triangle_fraction
        <= policy.maximum_component_triangle_fraction
    ):
        reasons.append("upper_component_triangle_fraction_out_of_bounds")
    if len(upper.vertex_indices) < policy.minimum_captured_point_support:
        reasons.append("upper_component_captured_point_support_insufficient")

    neck = profile_zones.boundaries[-1]
    if neck.zone_kind != "neck":
        raise ClosureSeparationError("profile_neck_zone_missing")
    if not (
        neck.start_axial - policy.z_match_tolerance
        <= upper.z_minimum
        <= neck.end_axial + policy.z_match_tolerance
    ):
        reasons.append("upper_component_outside_profile_neck_support")

    supporting_bands = tuple(
        candidate
        for candidate in neck_finish.candidates
        if candidate.candidate_type == "NARROW_REGION_CANDIDATE"
        and not candidate.ambiguity_review_required
        and candidate.supported_section_count >= policy.minimum_support_sections
        and candidate.captured_point_support_count >= policy.minimum_captured_point_support
        and candidate.section_z_range[0] <= upper.z_maximum + policy.z_match_tolerance
        and candidate.section_z_range[1] >= upper.z_minimum - policy.z_match_tolerance
    )
    if not supporting_bands:
        reasons.append("unique_neck_finish_support_missing")
    elif len(supporting_bands) != 1:
        return _result(
            ClosureSeparationStatus.AMBIGUOUS,
            ("multiple_neck_finish_bands_support_upper_component",),
            scan_master,
            neck_finish,
            profile_fit,
            profile_zones,
            model,
            (),
            policy,
        )

    if reasons:
        status = (
            ClosureSeparationStatus.AMBIGUOUS
            if any("ambiguous" in item for item in reasons)
            else ClosureSeparationStatus.NO_SEPARATION_EVIDENCE
        )
        return _result(
            status,
            tuple(reasons),
            scan_master,
            neck_finish,
            profile_fit,
            profile_zones,
            model,
            (),
            policy,
        )

    body_candidate = _candidate(scan_master, body, "body", FeatureKind.BODY, total_triangles)
    closure_candidate = _candidate(
        scan_master, upper, "closure-candidate", FeatureKind.CAP, total_triangles
    )
    parameter_id = _parameter_id(scan_master.revision_id, upper.component.component_id)
    parameter = DesignModelParameter(
        parameter_id,
        {
            "contract": CLOSURE_SEPARATION_CONTRACT,
            "scan_master_revision_id": scan_master.revision_id,
            "scan_master_geometry_sha256": digest,
            "neck_finish_result_id": neck_finish.result_id,
            "profile_fit_id": profile_fit.fit_id,
            "profile_zone_revision_id": profile_zones.revision_id,
            "candidate_component_id": closure_candidate.component_id,
            "candidate_feature_id": closure_candidate.feature.feature_id,
            "body_component_id": body_candidate.component_id,
            "body_feature_id": body_candidate.feature.feature_id,
            "supporting_section_count": supporting_bands[0].supported_section_count,
            "supporting_point_count": supporting_bands[0].captured_point_support_count,
            "candidate_triangle_count": upper.component.triangle_count,
            "candidate_triangle_fraction": triangle_fraction,
            "candidate_z_range": list((upper.z_minimum, upper.z_maximum)),
            "candidate_type": "SEPARATE_UPPER_COMPONENT_CANDIDATE",
            "policy": policy.as_dict(),
            "review_required": True,
            "closure_identity_confirmed": False,
            "geometry_embedded": False,
            "scan_master_mutated": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
        ParameterType.OBJECT,
    )
    existing_features = {item.feature_id: item for item in model.features}
    for candidate in (body_candidate, closure_candidate):
        prior = existing_features.get(candidate.feature.feature_id)
        if prior is not None and prior != candidate.feature:
            raise ClosureSeparationError("stable_component_feature_id_conflict")
        existing_features[candidate.feature.feature_id] = candidate.feature
    parameters = tuple(item for item in model.parameters if item.parameter_id != parameter_id)
    try:
        updated_model = revise_design_model_revision(
            model,
            parameters=(*parameters, parameter),
            features=tuple(existing_features.values()),
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise ClosureSeparationError("closure_candidate_model_revision_invalid") from error
    return _result(
        ClosureSeparationStatus.CANDIDATE_CREATED,
        ("two_supported_edge_connected_components_align_with_profile_neck",),
        scan_master,
        neck_finish,
        profile_fit,
        profile_zones,
        model,
        (body_candidate, closure_candidate),
        policy,
        updated_model=updated_model,
    )


def _validate_inputs(
    scan_master: ScanMasterRevision,
    neck_finish: NeckFinishCandidateSet,
    profile_fit: DesignModelProfileFit,
    profile_zones: DesignProfileZones,
    model: DesignModelRevision,
    expected_scan_master_revision_id: str,
    expected_model_revision_id: str,
    policy: ClosureSeparationPolicy,
) -> None:
    if not isinstance(scan_master, ScanMasterRevision):
        raise ClosureSeparationError("scan_master_revision_required")
    if not isinstance(neck_finish, NeckFinishCandidateSet):
        raise ClosureSeparationError("neck_finish_candidates_required")
    if not isinstance(profile_fit, DesignModelProfileFit):
        raise ClosureSeparationError("design_model_profile_fit_required")
    if not isinstance(profile_zones, DesignProfileZones):
        raise ClosureSeparationError("design_profile_zones_required")
    if not isinstance(model, DesignModelRevision):
        raise ClosureSeparationError("design_model_revision_required")
    if not isinstance(policy, ClosureSeparationPolicy):
        raise ClosureSeparationError("closure_separation_policy_invalid")
    if not isinstance(neck_finish.candidates, tuple) or any(
        not isinstance(item, NeckFinishCandidate) for item in neck_finish.candidates
    ):
        raise ClosureSeparationError("neck_finish_candidate_records_invalid")
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
        raise ClosureSeparationError("selected_scan_master_parent_stale_or_invalid")
    scale_state = _manifest_scale_state(manifest.get("scale_state"))
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    scale_id = manifest.get("scale_provenance_id")
    source_geometry_id = manifest.get("parent_object_geometry_revision_id")
    if not isinstance(scale_id, str) or not isinstance(source_geometry_id, str):
        raise ClosureSeparationError("scan_master_capture_parent_provenance_missing")
    binding = profile_fit.parent_binding
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
        raise ClosureSeparationError("profile_fit_parent_or_authority_mismatch")
    if (
        profile_zones.review_required
        or profile_zones.status is not ProfileZoneStatus.DETECTED
        or profile_zones.fit_id != profile_fit.fit_id
        or profile_zones.scan_master_revision_id != scan_master.revision_id
        or profile_zones.scan_master_geometry_sha256 != digest
        or profile_zones.parent_binding_revision_id != binding.revision_id
        or profile_zones.coordinate_unit != unit
    ):
        raise ClosureSeparationError("profile_zones_ambiguous_stale_or_unauthorized")
    if (
        not isinstance(profile_zones.boundaries, tuple)
        or len(profile_zones.boundaries) != 4
        or tuple(item.zone_kind for item in profile_zones.boundaries)
        != ("base", "body", "shoulder", "neck")
        or any(
            item.component_id != profile_zones.boundaries[0].component_id
            for item in profile_zones.boundaries
        )
    ):
        raise ClosureSeparationError("profile_zone_partition_invalid")
    try:
        expected_zones = detect_design_profile_zones(
            profile_fit,
            expected_fit_id=profile_fit.fit_id,
            component_id=profile_zones.boundaries[0].component_id,
        )
    except ProfileZoneError as error:
        raise ClosureSeparationError("profile_zone_fit_evidence_invalid") from error
    if expected_zones != profile_zones:
        raise ClosureSeparationError("profile_zone_revision_identity_invalid")
    if (
        neck_finish.source_geometry_id != source_geometry_id
        or neck_finish.scale_provenance_id != scale_id
        or neck_finish.scale_state is not scale_state
        or neck_finish.coordinate_unit != unit
    ):
        raise ClosureSeparationError("neck_finish_capture_parent_or_scale_mismatch")
    if (
        model.revision_id != expected_model_revision_id
        or model.project_id != scan_master.project_id
        or model.fitted_to_scan_master_revision_id != scan_master.revision_id
        or model.scan_master_geometry_sha256 != digest
        or model.parent_binding_revision_id != binding.revision_id
        or model.scale_state is not scale_state
        or model.coordinate_unit != unit
        or model.scale_provenance_id != scale_id
        or model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or model.mold_use_authorized is not False
    ):
        raise ClosureSeparationError("design_model_parent_or_scale_mismatch")


def _manifest_scale_state(value: object) -> ScaleState:
    if not isinstance(value, str):
        raise ClosureSeparationError("scan_master_scale_state_invalid")
    try:
        state = ScaleState(value)
    except (TypeError, ValueError) as error:
        raise ClosureSeparationError("scan_master_scale_state_invalid") from error
    if state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise ClosureSeparationError("scan_master_scale_state_unauthorized")
    return state


def _component_bounds(scan: ScanMasterRevision, component: MeshComponent) -> _ComponentBounds:
    triangle_vertices = {
        vertex_index
        for triangle_index in component.triangle_indices
        for vertex_index in scan.mesh.triangles[triangle_index]
    }
    if not triangle_vertices:
        raise ClosureSeparationError("empty_scan_component")
    z_values = tuple(scan.mesh.vertices[index][2] for index in triangle_vertices)
    if any(not math.isfinite(value) for value in z_values):
        raise ClosureSeparationError("scan_component_z_invalid")
    return _ComponentBounds(
        component,
        tuple(sorted(triangle_vertices)),
        min(z_values),
        max(z_values),
        sum(z_values) / len(z_values),
    )


def _candidate(
    scan: ScanMasterRevision,
    bounds: _ComponentBounds,
    role: str,
    feature_kind: FeatureKind,
    total_triangles: int,
) -> ClosureComponentCandidate:
    component_id = _component_identity(scan.revision_id, bounds.component.component_id)
    semantic_key = f"closure-separation:{role}:{bounds.component.component_id}"
    feature = DesignModelFeatureReference(
        stable_feature_id(component_id, feature_kind, semantic_key),
        component_id,
        feature_kind,
        semantic_key,
    )
    return ClosureComponentCandidate(
        role,
        component_id,
        feature,
        bounds.component.component_id,
        bounds.component.triangle_count,
        bounds.component.triangle_count / total_triangles,
        len(bounds.vertex_indices),
        (bounds.z_minimum, bounds.z_maximum),
    )


def _component_identity(scan_revision_id: str, mesh_component_id: str) -> str:
    digest = hashlib.sha256(f"{scan_revision_id}:{mesh_component_id}".encode()).hexdigest()
    return f"scan-component:{digest[:32]}"


def _parameter_id(scan_revision_id: str, component_id: str) -> str:
    digest = hashlib.sha256(f"{scan_revision_id}:{component_id}".encode()).hexdigest()
    return _CANDIDATE_PARAMETER_PREFIX + digest


def _result(
    status: ClosureSeparationStatus,
    reasons: tuple[str, ...],
    scan_master: ScanMasterRevision,
    neck_finish: NeckFinishCandidateSet,
    profile_fit: DesignModelProfileFit,
    profile_zones: DesignProfileZones,
    parent_model: DesignModelRevision,
    candidates: tuple[ClosureComponentCandidate, ...],
    policy: ClosureSeparationPolicy,
    *,
    updated_model: DesignModelRevision | None = None,
) -> ClosureSeparationResult:
    return ClosureSeparationResult(
        status,
        reasons,
        scan_master.revision_id,
        mesh_sha256(scan_master.mesh),
        neck_finish.result_id,
        profile_fit.fit_id,
        profile_zones.revision_id,
        parent_model.revision_id,
        updated_model,
        candidates,
        policy,
    )


__all__ = [
    "CLOSURE_SEPARATION_CONTRACT",
    "ClosureComponentCandidate",
    "ClosureSeparationError",
    "ClosureSeparationPolicy",
    "ClosureSeparationResult",
    "ClosureSeparationStatus",
    "create_closure_separation_candidates",
]
