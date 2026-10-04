"""Bounded advisory label-surface analysis over exact CAD BREP differentials."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass

from .cad_adapter import (
    CadAdapterError,
    CadSurfaceRegionSample,
    cad_shape_geometry_digest,
    inspect_shape_topology,
    sample_cad_surface_regions,
)
from .cad_brep import CadBrepRepresentationRevision
from .cad_feature_map import map_design_model_features_to_brep
from .design_model import DesignModelRevision

CAD_LABEL_SURFACE_ANALYSIS_CONTRACT = "packlab.cad-label-surface-analysis.v1"
_MAX_FACES = 512
_MAX_REGIONS = 8_192
_MAX_DIFFERENTIAL_SAMPLES = 40_960
_MAX_SAMPLES_PER_AXIS = 16
_SUPPORTED_ATTRIBUTION = {"MAPPED", "MAPPED_COARSE", "AMBIGUOUS", "UNRESOLVED"}


class CadLabelSurfaceAnalysisError(ValueError):
    """Raised when exact BREP provenance or deterministic analysis is unavailable."""


@dataclass(frozen=True, slots=True)
class CadLabelSurfacePolicy:
    """Explicit finite analysis thresholds and bounded CAD parameter-cell density."""

    target_normal: tuple[float, float, float]
    maximum_slope_degrees: float
    maximum_absolute_curvature: float
    samples_per_axis: int = 4
    maximum_faces: int = _MAX_FACES
    maximum_regions: int = _MAX_REGIONS
    maximum_differential_samples: int = _MAX_DIFFERENTIAL_SAMPLES

    def __post_init__(self) -> None:
        if not isinstance(self.target_normal, tuple) or len(self.target_normal) != 3:
            raise CadLabelSurfaceAnalysisError("cad_label_target_normal_invalid")
        normalized_input = tuple(
            _finite_float(value, "cad_label_target_normal_invalid") for value in self.target_normal
        )
        length = math.sqrt(sum(value**2 for value in normalized_input))
        if not math.isfinite(length) or length <= 1e-12:
            raise CadLabelSurfaceAnalysisError("cad_label_target_normal_invalid")
        object.__setattr__(
            self,
            "target_normal",
            tuple(value / length for value in normalized_input),
        )
        for name, value, maximum, code in (
            (
                "maximum_slope_degrees",
                self.maximum_slope_degrees,
                90.0,
                "cad_label_slope_threshold_invalid",
            ),
            (
                "maximum_absolute_curvature",
                self.maximum_absolute_curvature,
                1e9,
                "cad_label_curvature_threshold_invalid",
            ),
        ):
            normalized = _finite_float(value, code)
            if not 0.0 <= normalized <= maximum:
                raise CadLabelSurfaceAnalysisError(code)
            object.__setattr__(self, name, normalized)
        for name, value, maximum, minimum, code in (
            (
                "samples_per_axis",
                self.samples_per_axis,
                _MAX_SAMPLES_PER_AXIS,
                2,
                "cad_label_samples_per_axis_invalid",
            ),
            ("maximum_faces", self.maximum_faces, _MAX_FACES, 1, "cad_label_maximum_faces_invalid"),
            (
                "maximum_regions",
                self.maximum_regions,
                _MAX_REGIONS,
                1,
                "cad_label_maximum_regions_invalid",
            ),
            (
                "maximum_differential_samples",
                self.maximum_differential_samples,
                _MAX_DIFFERENTIAL_SAMPLES,
                1,
                "cad_label_maximum_samples_invalid",
            ),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not minimum <= value <= maximum
            ):
                raise CadLabelSurfaceAnalysisError(code)
        maximum_work_regions = self.maximum_faces * (self.samples_per_axis - 1) ** 2
        if maximum_work_regions > self.maximum_regions:
            raise CadLabelSurfaceAnalysisError("cad_label_region_work_bound_exceeded")
        if maximum_work_regions * 5 > self.maximum_differential_samples:
            raise CadLabelSurfaceAnalysisError("cad_label_differential_work_bound_exceeded")

    def as_dict(self) -> dict[str, object]:
        return {
            "target_normal": list(self.target_normal),
            "maximum_slope_degrees": self.maximum_slope_degrees,
            "maximum_absolute_curvature": self.maximum_absolute_curvature,
            "samples_per_axis": self.samples_per_axis,
            "maximum_faces": self.maximum_faces,
            "maximum_regions": self.maximum_regions,
            "maximum_differential_samples": self.maximum_differential_samples,
        }


@dataclass(frozen=True, slots=True)
class CadLabelFeatureEvidence:
    feature_id: str
    feature_kind: str
    component_id: str
    status: str
    reference_scope: str
    target_subshape_type: str | None
    evidence_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "feature_id": self.feature_id,
            "feature_kind": self.feature_kind,
            "component_id": self.component_id,
            "mapping_status": self.status,
            "reference_scope": self.reference_scope,
            "target_subshape_type": self.target_subshape_type,
            "evidence_codes": list(self.evidence_codes),
        }


@dataclass(frozen=True, slots=True)
class CadLabelSurfaceCandidate:
    analysis_region_id: str
    component_id: str
    feature_attribution_status: str
    resolved_feature_id: None
    contributing_features: tuple[CadLabelFeatureEvidence, ...]
    center: tuple[float, float, float]
    support_points: tuple[tuple[float, float, float], ...]
    maximum_slope_degrees: float
    maximum_absolute_curvature: float
    coordinate_unit_for_curvature: str
    surface_type: str
    sampled_boundary: bool
    periodic_seam_boundary: bool
    supported_surface_type: bool
    advisory_classification: str
    rejection_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "analysis_region_id": self.analysis_region_id,
            "analysis_region_identity_scope": "EXACT_SOURCE_BREP_REVISION_AND_DIGEST",
            "component_id": self.component_id,
            "feature_attribution_status": self.feature_attribution_status,
            "resolved_feature_id": self.resolved_feature_id,
            "contributing_features": [item.as_dict() for item in self.contributing_features],
            "center": list(self.center),
            "support_points": [list(point) for point in self.support_points],
            "maximum_slope_degrees": self.maximum_slope_degrees,
            "maximum_absolute_curvature": self.maximum_absolute_curvature,
            "curvature_unit": self.coordinate_unit_for_curvature,
            "surface_type": self.surface_type,
            "sampled_boundary": self.sampled_boundary,
            "periodic_seam_boundary": self.periodic_seam_boundary,
            "supported_surface_type": self.supported_surface_type,
            "advisory_classification": self.advisory_classification,
            "rejection_reasons": list(self.rejection_reasons),
            "automatic_label_zone_created": False,
            "physical_fit_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


@dataclass(frozen=True, slots=True)
class CadLabelSurfaceAnalysis:
    revision_id: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    component_id: str
    source_feature_mapping_revision_id: str
    feature_attribution_status: str
    contributing_features: tuple[CadLabelFeatureEvidence, ...]
    policy: CadLabelSurfacePolicy
    analyzed_region_count: int
    candidates: tuple[CadLabelSurfaceCandidate, ...]
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": CAD_LABEL_SURFACE_ANALYSIS_CONTRACT,
            "authority_class": "ADVISORY_CAD_LABEL_SURFACE_ANALYSIS",
            "revision_id": self.revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_cad_brep": {
                "revision_id": self.source_brep_revision_id,
                "geometry_sha256": self.source_brep_geometry_sha256,
            },
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "component_id": self.component_id,
            "source_feature_mapping_revision_id": self.source_feature_mapping_revision_id,
            "feature_attribution_status": self.feature_attribution_status,
            "resolved_feature_id": None,
            "contributing_features": [item.as_dict() for item in self.contributing_features],
            "analysis_policy": self.policy.as_dict(),
            "sampling": {
                "source": "EXACT_OCCT_BREP_SURFACE_DIFFERENTIALS",
                "regions_analyzed": self.analyzed_region_count,
                "face_limit": self.policy.maximum_faces,
                "region_limit": self.policy.maximum_regions,
                "differential_sample_limit": self.policy.maximum_differential_samples,
                "face_traversal_index_used_as_identity": False,
                "mesh_or_preview_used_as_authority": False,
                "candidate_order": "analysis_region_id_ascending",
            },
            "candidates": [item.as_dict() for item in self.candidates],
            "limitations": list(self.limitations),
            "advisory_only": True,
            "automatic_production_approval": False,
            "print_fit_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


def analyze_cad_label_surfaces(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    policy: CadLabelSurfacePolicy,
) -> CadLabelSurfaceAnalysis:
    """Classify exact CAD surface sample patches without inventing feature ownership."""
    if not isinstance(model, DesignModelRevision):
        raise CadLabelSurfaceAnalysisError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise CadLabelSurfaceAnalysisError("cad_brep_representation_required")
    if not isinstance(policy, CadLabelSurfacePolicy):
        raise CadLabelSurfaceAnalysisError("cad_label_surface_policy_required")
    try:
        mapping = map_design_model_features_to_brep(model, representation)
    except (TypeError, ValueError) as error:
        raise CadLabelSurfaceAnalysisError("cad_label_surface_provenance_mismatch") from error
    _validate_representation_provenance(model, representation, mapping)
    try:
        registered_digest = cad_shape_geometry_digest(representation.shape_handle)
        topology = inspect_shape_topology(representation.shape_handle)
    except CadAdapterError as error:
        raise CadLabelSurfaceAnalysisError(str(error)) from error
    if registered_digest != representation.geometry_sha256:
        raise CadLabelSurfaceAnalysisError("cad_label_surface_brep_digest_mismatch")
    if not topology.kernel_valid or topology.solid_count != 1:
        raise CadLabelSurfaceAnalysisError("cad_label_surface_brep_not_valid_single_solid")
    feature_by_id = {feature.feature_id: feature for feature in model.features}
    evidence: list[CadLabelFeatureEvidence] = []
    component_ids: set[str] = set()
    for feature_id in representation.source_feature_ids:
        feature = feature_by_id.get(feature_id)
        reference = next(
            (item for item in mapping.references if item.feature_id == feature_id), None
        )
        if feature is None or reference is None or reference.status not in _SUPPORTED_ATTRIBUTION:
            raise CadLabelSurfaceAnalysisError("cad_label_surface_lineage_evidence_invalid")
        component_id = feature.component_id
        if not isinstance(component_id, str) or not component_id.strip():
            raise CadLabelSurfaceAnalysisError("cad_label_surface_component_provenance_missing")
        component_ids.add(component_id)
        evidence.append(
            CadLabelFeatureEvidence(
                feature_id,
                feature.feature_kind.value,
                component_id,
                reference.status,
                reference.reference_scope,
                reference.target_subshape_type,
                reference.evidence_codes,
            )
        )
    if len(component_ids) != 1:
        raise CadLabelSurfaceAnalysisError("cad_label_surface_component_provenance_ambiguous")
    component_id = next(iter(component_ids))
    feature_evidence = tuple(sorted(evidence, key=lambda item: item.feature_id))
    if any(item.status == "AMBIGUOUS" for item in feature_evidence):
        attribution = "AMBIGUOUS"
    elif any(item.status in {"UNRESOLVED", "MAPPED_COARSE"} for item in feature_evidence):
        attribution = "UNRESOLVED"
    else:
        # Existing M13 selectors target whole solids, not these specific regions.
        attribution = "UNRESOLVED"
    try:
        regions = sample_cad_surface_regions(
            representation.shape_handle,
            samples_per_axis=policy.samples_per_axis,
            maximum_faces=policy.maximum_faces,
            maximum_regions=policy.maximum_regions,
            maximum_differential_samples=policy.maximum_differential_samples,
        )
    except CadAdapterError as error:
        raise CadLabelSurfaceAnalysisError(str(error)) from error
    candidates: list[CadLabelSurfaceCandidate] = []
    seen_signatures: set[str] = set()
    for region in regions:
        geometric_evidence = _canonical_region_evidence(region)
        signature = json.dumps(
            geometric_evidence, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        if signature in seen_signatures:
            raise CadLabelSurfaceAnalysisError("cad_label_analysis_region_signature_collision")
        seen_signatures.add(signature)
        slopes = tuple(
            _angle_degrees(sample.normal, policy.target_normal) for sample in region.support_points
        )
        maximum_slope = max(slopes)
        maximum_curvature = max(
            max(abs(sample.minimum_curvature), abs(sample.maximum_curvature))
            for sample in region.support_points
        )
        unsafe_reasons = []
        if maximum_slope > policy.maximum_slope_degrees:
            unsafe_reasons.append("slope_threshold_exceeded")
        if maximum_curvature > policy.maximum_absolute_curvature:
            unsafe_reasons.append("curvature_threshold_exceeded")
        if region.trimmed_or_boundary:
            unsafe_reasons.append("trimmed_or_face_boundary_sampled")
        if region.periodic_seam_boundary:
            unsafe_reasons.append("periodic_seam_boundary_sampled")
        if not region.supported_surface_type:
            unsafe_reasons.append("unsupported_surface_class")
        identity = {
            "contract": CAD_LABEL_SURFACE_ANALYSIS_CONTRACT,
            "source_design_model_revision_id": model.revision_id,
            "source_brep_revision_id": representation.revision_id,
            "source_brep_geometry_sha256": representation.geometry_sha256,
            "component_id": component_id,
            "feature_mapping_revision_id": mapping.revision_id,
            "feature_attribution_status": attribution,
            "contributing_features": [item.as_dict() for item in feature_evidence],
            "policy": policy.as_dict(),
            "geometric_evidence": geometric_evidence,
        }
        analysis_region_id = "cad-analysis-region:" + _digest(identity)
        center = region.center.point
        ordered_points: tuple[tuple[float, float, float], ...] = tuple(
            sorted(
                {
                    (
                        round(sample.point[0], 9),
                        round(sample.point[1], 9),
                        round(sample.point[2], 9),
                    )
                    for sample in region.support_points
                }
            )
        )
        classification = "LABEL_SAFE_CANDIDATE" if not unsafe_reasons else "NOT_SAFE_UNDER_POLICY"
        candidates.append(
            CadLabelSurfaceCandidate(
                analysis_region_id,
                component_id,
                attribution,
                None,
                feature_evidence,
                center,
                ordered_points,
                maximum_slope,
                maximum_curvature,
                _curvature_unit(representation.coordinate_unit),
                region.surface_type,
                region.trimmed_or_boundary,
                region.periodic_seam_boundary,
                region.supported_surface_type,
                classification,
                tuple(unsafe_reasons),
            )
        )
    candidates.sort(key=lambda item: item.analysis_region_id)
    limitations = (
        "Finite parameter-cell samples do not mathematically bound unsampled geometry between support points.",
        "Trimmed and sampled face-boundary regions are classified not-safe; narrow trim features may be missed by the finite grid.",
        "Periodic parameter seams are marked not-safe where sampled; other surface discontinuities may require finer analysis.",
        "Unsupported surface classes are classified not-safe.",
        "A candidate is BREP-scoped advisory evidence, not a stable CAD face ID, label-footprint fit, printability, or manufacturing decision.",
    )
    result_identity = {
        "contract": CAD_LABEL_SURFACE_ANALYSIS_CONTRACT,
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "source_brep_geometry_sha256": representation.geometry_sha256,
        "parent_kind": representation.parent_kind.value,
        "parent_authority_revision_id": representation.parent_authority_revision_id,
        "scale_state": representation.scale_state.value,
        "coordinate_unit": representation.coordinate_unit,
        "feature_mapping_revision_id": mapping.revision_id,
        "component_id": component_id,
        "feature_attribution_status": attribution,
        "contributing_features": [item.as_dict() for item in feature_evidence],
        "policy": policy.as_dict(),
        "candidate_ids": [item.analysis_region_id for item in candidates],
        "limitations": list(limitations),
    }
    return CadLabelSurfaceAnalysis(
        "cad-label-surface-analysis:" + _digest(result_identity),
        model.revision_id,
        representation.revision_id,
        representation.geometry_sha256,
        representation.parent_kind.value,
        representation.parent_authority_revision_id,
        representation.scale_state.value,
        representation.coordinate_unit,
        representation.physical_accuracy_validation_status,
        representation.mold_use_authorized,
        component_id,
        mapping.revision_id,
        attribution,
        feature_evidence,
        policy,
        len(regions),
        tuple(candidates),
        limitations,
    )


def _validate_representation_provenance(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    mapping,
) -> None:
    expected_parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if (
        representation.source_design_model_revision_id != model.revision_id
        or representation.parent_kind is not model.parent_kind
        or representation.parent_authority_revision_id != expected_parent_revision
        or representation.scale_state is not model.scale_state
        or representation.coordinate_unit != model.coordinate_unit
        or representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized
        or mapping.source_design_model_revision_id != model.revision_id
        or mapping.source_brep_revision_id != representation.revision_id
        or mapping.source_feature_ids != representation.source_feature_ids
        or not representation.source_feature_ids
    ):
        raise CadLabelSurfaceAnalysisError("cad_label_surface_provenance_mismatch")


def _canonical_region_evidence(region: CadSurfaceRegionSample) -> dict[str, object]:
    samples = sorted(
        (
            tuple(round(value, 9) for value in sample.point),
            tuple(round(value, 9) for value in sample.normal),
            round(sample.minimum_curvature, 12),
            round(sample.maximum_curvature, 12),
        )
        for sample in region.support_points
    )
    return {
        "surface_type": region.surface_type,
        "support_samples": [
            {
                "point": list(point),
                "normal": list(normal),
                "minimum_curvature": minimum,
                "maximum_curvature": maximum,
            }
            for point, normal, minimum, maximum in samples
        ],
        "trimmed_or_boundary": region.trimmed_or_boundary,
        "periodic_seam_boundary": region.periodic_seam_boundary,
        "supported_surface_type": region.supported_surface_type,
    }


def _angle_degrees(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    cosine = max(-1.0, min(1.0, sum(a * b for a, b in zip(left, right, strict=True))))
    return math.degrees(math.acos(cosine))


def _curvature_unit(coordinate_unit: str) -> str:
    return {
        "reconstruction_units": "inverse_reconstruction_units",
        "mm_unverified": "inverse_mm_unverified",
    }.get(coordinate_unit, "unknown_inverse_unit")


def _digest(value: Mapping[str, object]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _finite_float(value: object, error_code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CadLabelSurfaceAnalysisError(error_code)
    try:
        converted = float(value)
    except OverflowError as error:
        raise CadLabelSurfaceAnalysisError(error_code) from error
    if not math.isfinite(converted):
        raise CadLabelSurfaceAnalysisError(error_code)
    return converted


__all__ = [
    "CAD_LABEL_SURFACE_ANALYSIS_CONTRACT",
    "CadLabelFeatureEvidence",
    "CadLabelSurfaceAnalysis",
    "CadLabelSurfaceAnalysisError",
    "CadLabelSurfaceCandidate",
    "CadLabelSurfacePolicy",
    "analyze_cad_label_surfaces",
]
