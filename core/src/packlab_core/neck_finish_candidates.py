"""Conservative neck/finish narrow-region candidates from captured evidence."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from statistics import median

from .bounding_dimensions import NormalizedMeasurementGeometry
from .cross_section_measurement import CrossSectionMeasurement
from .horizontal_section import HorizontalSection
from .reconstruction import ScaleState
from .vertical_profile import VerticalProfile

NECK_FINISH_METHOD_VERSION = "supported_narrow_region_candidates_v1"
MIN_EVIDENCE_SECTIONS = 3
MAX_EVIDENCE_SECTIONS = 10_000


class NeckFinishCandidateError(ValueError):
    """Raised when candidate evidence is insufficient, stale, or inconsistent."""


@dataclass(frozen=True, slots=True)
class NeckFinishPolicy:
    minimum_relative_radius_reduction: float = 0.2
    maximum_adjacent_radius_change_within_band: float = 0.15
    minimum_support_sections: int = 2
    minimum_points_per_section: int = 8
    z_match_tolerance: float = 1e-6
    method_version: str = NECK_FINISH_METHOD_VERSION

    def __post_init__(self) -> None:
        if not _unit_interval(self.minimum_relative_radius_reduction, allow_zero=False):
            raise NeckFinishCandidateError("candidate_radius_reduction_threshold_invalid")
        if not _unit_interval(self.maximum_adjacent_radius_change_within_band):
            raise NeckFinishCandidateError("candidate_band_change_threshold_invalid")
        if not _positive_integer(self.minimum_support_sections):
            raise NeckFinishCandidateError("candidate_minimum_support_sections_invalid")
        if not _positive_integer(self.minimum_points_per_section):
            raise NeckFinishCandidateError("candidate_minimum_points_invalid")
        if not _nonnegative_finite(self.z_match_tolerance):
            raise NeckFinishCandidateError("candidate_z_match_tolerance_invalid")
        if self.method_version != NECK_FINISH_METHOD_VERSION:
            raise NeckFinishCandidateError("candidate_method_version_unsupported")

    def as_dict(self) -> dict[str, object]:
        return {
            "method_version": self.method_version,
            "minimum_relative_radius_reduction": self.minimum_relative_radius_reduction,
            "maximum_adjacent_radius_change_within_band": self.maximum_adjacent_radius_change_within_band,
            "minimum_support_sections": self.minimum_support_sections,
            "minimum_points_per_section": self.minimum_points_per_section,
            "z_match_tolerance": self.z_match_tolerance,
            "candidate_type": "NARROW_REGION_CANDIDATE",
        }


@dataclass(frozen=True, slots=True)
class NeckSectionEvidence:
    horizontal_section: HorizontalSection
    cross_section_measurement: CrossSectionMeasurement


@dataclass(frozen=True, slots=True)
class NeckFinishCandidate:
    rank: int
    candidate_type: str
    review_required: bool
    ambiguity_review_required: bool
    section_z_range: tuple[float, float]
    section_z_values: tuple[float, ...]
    height: float
    coordinate_unit: str
    major_radius: float
    minor_radius: float
    major_diameter: float
    minor_diameter: float
    relative_radius_reduction: float
    supported_section_count: int
    captured_point_support_count: int
    maximum_fit_residual: float
    maximum_planarity_residual: float
    scale_factor_uncertainty: float | None
    scale_factor_uncertainty_unit: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "candidate_type": self.candidate_type,
            "review_required": self.review_required,
            "ambiguity_review_required": self.ambiguity_review_required,
            "section_z_range": list(self.section_z_range),
            "section_z_values": list(self.section_z_values),
            "height": self.height,
            "coordinate_unit": self.coordinate_unit,
            "radii": {"major": self.major_radius, "minor": self.minor_radius},
            "diameters": {"major": self.major_diameter, "minor": self.minor_diameter},
            "relative_radius_reduction_from_largest_supported_band": self.relative_radius_reduction,
            "support": {
                "section_count": self.supported_section_count,
                "captured_point_count": self.captured_point_support_count,
                "maximum_fit_residual": self.maximum_fit_residual,
                "maximum_planarity_residual": self.maximum_planarity_residual,
            },
            "uncertainty": {
                "scale_factor_uncertainty": self.scale_factor_uncertainty,
                "scale_factor_uncertainty_unit": self.scale_factor_uncertainty_unit,
                "fit_residual_is_confidence_interval": False,
                "combined_statistical_interval_estimated": False,
            },
            "thread_standard_inferred": False,
            "closure_spec_inferred": False,
            "mold_ready_dimensions_claimed": False,
        }


@dataclass(frozen=True, slots=True)
class NeckFinishCandidateSet:
    result_id: str
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    coordinate_unit: str
    vertical_profile_id: str
    policy: NeckFinishPolicy
    baseline_radius: float
    candidates: tuple[NeckFinishCandidate, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.neck-finish-candidates.v1",
            "result_id": self.result_id,
            "method_version": NECK_FINISH_METHOD_VERSION,
            "source_geometry_id": self.source_geometry_id,
            "normalized_geometry_revision": self.normalized_geometry_revision,
            "scale_provenance_id": self.scale_provenance_id,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "vertical_profile_id": self.vertical_profile_id,
            "policy": self.policy.as_dict(),
            "baseline_radius": self.baseline_radius,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "candidate_count": len(self.candidates),
            "authority_class": "OBJECT_CAPTURE_GEOMETRY",
            "generated": False,
            "physical_accuracy_claimed": False,
            "thread_standard_inferred": False,
            "closure_spec_inferred": False,
            "mold_ready_dimensions_claimed": False,
        }


@dataclass(frozen=True, slots=True)
class _SupportedSection:
    z: float
    major_radius: float
    minor_radius: float
    equivalent_radius: float
    horizontal_point_count: int
    measurement_sample_count: int
    radial_residual: float
    planarity_residual: float
    scale_uncertainty: float | None
    scale_uncertainty_unit: str | None


def measure_neck_finish_candidates(
    geometry: NormalizedMeasurementGeometry,
    sections: tuple[NeckSectionEvidence, ...],
    vertical_profile: VerticalProfile,
    *,
    policy: NeckFinishPolicy | None = None,
    current_geometry_id: str,
    current_normalized_geometry_revision: str,
    current_scale_provenance_id: str | None,
) -> NeckFinishCandidateSet:
    """Rank supported narrow section bands as unclassified neck/finish candidates."""

    if policy is None:
        policy = NeckFinishPolicy()
    if geometry.source_geometry_id != current_geometry_id:
        raise NeckFinishCandidateError("candidate_source_geometry_parent_stale")
    if geometry.normalized_geometry_revision != current_normalized_geometry_revision:
        raise NeckFinishCandidateError("candidate_normalized_geometry_parent_stale")
    if geometry.scale_provenance_id != current_scale_provenance_id:
        raise NeckFinishCandidateError("candidate_scale_provenance_parent_stale")
    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise NeckFinishCandidateError("candidate_requires_captured_geometry_authority")
    if not isinstance(sections, tuple) or len(sections) < MIN_EVIDENCE_SECTIONS:
        raise NeckFinishCandidateError("candidate_insufficient_section_evidence")
    if len(sections) > MAX_EVIDENCE_SECTIONS:
        raise NeckFinishCandidateError("candidate_section_evidence_out_of_bounds")
    _validate_profile(geometry, vertical_profile)
    supported = tuple(
        sorted(
            (_validate_section_evidence(geometry, evidence, policy) for evidence in sections),
            key=lambda item: item.z,
        )
    )
    z_values = tuple(item.z for item in supported)
    if len(set(z_values)) != len(z_values):
        raise NeckFinishCandidateError("candidate_duplicate_section_z")
    if (
        min(z_values)
        < vertical_profile.plane_origin[2]
        + vertical_profile.vertical_range[0]
        - policy.z_match_tolerance
        or max(z_values)
        > vertical_profile.plane_origin[2]
        + vertical_profile.vertical_range[1]
        + policy.z_match_tolerance
    ):
        raise NeckFinishCandidateError("candidate_sections_outside_vertical_profile_support")

    baseline = max(item.equivalent_radius for item in supported)
    bands: list[list[_SupportedSection]] = []
    for item in supported:
        if not bands:
            bands.append([item])
            continue
        previous = bands[-1][-1]
        pair_baseline = max(previous.equivalent_radius, item.equivalent_radius)
        relative_change = abs(item.equivalent_radius - previous.equivalent_radius) / pair_baseline
        if relative_change <= policy.maximum_adjacent_radius_change_within_band:
            bands[-1].append(item)
        else:
            bands.append([item])

    ranked_data: list[tuple[float, float, float, list[_SupportedSection]]] = []
    for band in bands:
        if len(band) < policy.minimum_support_sections:
            continue
        band_radius = median(item.equivalent_radius for item in band)
        relative_reduction = (baseline - band_radius) / baseline
        if relative_reduction + 1e-12 < policy.minimum_relative_radius_reduction:
            continue
        ranked_data.append((relative_reduction, band_radius, band[0].z, band))
    ranked_data.sort(key=lambda item: (-item[0], item[1], item[2]))
    ambiguous = len(ranked_data) > 1
    candidates: list[NeckFinishCandidate] = []
    for rank, (relative_reduction, _, _, band) in enumerate(ranked_data, start=1):
        band_z = tuple(item.z for item in band)
        major_radius = median(item.major_radius for item in band)
        minor_radius = median(item.minor_radius for item in band)
        uncertainties = tuple(
            item.scale_uncertainty for item in band if item.scale_uncertainty is not None
        )
        candidates.append(
            NeckFinishCandidate(
                rank,
                "NARROW_REGION_CANDIDATE",
                True,
                ambiguous,
                (min(band_z), max(band_z)),
                band_z,
                max(band_z) - min(band_z),
                geometry.coordinate_unit,
                major_radius,
                minor_radius,
                major_radius * 2.0,
                minor_radius * 2.0,
                relative_reduction,
                len(band),
                sum(item.horizontal_point_count for item in band),
                max(item.radial_residual for item in band),
                max(item.planarity_residual for item in band),
                max(uncertainties) if uncertainties else None,
                next(
                    (
                        item.scale_uncertainty_unit
                        for item in band
                        if item.scale_uncertainty is not None
                    ),
                    None,
                ),
            )
        )

    canonical_sections = [
        {
            "z": item.z,
            "major_radius": item.major_radius,
            "minor_radius": item.minor_radius,
            "equivalent_radius": item.equivalent_radius,
            "horizontal_point_count": item.horizontal_point_count,
            "measurement_sample_count": item.measurement_sample_count,
            "radial_residual": item.radial_residual,
            "planarity_residual": item.planarity_residual,
        }
        for item in supported
    ]
    body: dict[str, object] = {
        "method_version": NECK_FINISH_METHOD_VERSION,
        "source_geometry_id": geometry.source_geometry_id,
        "normalized_geometry_revision": geometry.normalized_geometry_revision,
        "scale_provenance_id": geometry.scale_provenance_id,
        "scale_state": geometry.scale_state.value,
        "coordinate_unit": geometry.coordinate_unit,
        "vertical_profile_id": vertical_profile.profile_id,
        "policy": policy.as_dict(),
        "supported_sections": canonical_sections,
        "baseline_radius": baseline,
        "candidates": [candidate.as_dict() for candidate in candidates],
    }
    result_id = (
        "neck-finish-candidates:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return NeckFinishCandidateSet(
        result_id,
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.scale_state,
        geometry.coordinate_unit,
        vertical_profile.profile_id,
        policy,
        baseline,
        tuple(candidates),
    )


def serialize_neck_finish_candidates(result: NeckFinishCandidateSet) -> bytes:
    return json.dumps(
        result.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _validate_profile(
    geometry: NormalizedMeasurementGeometry,
    profile: VerticalProfile,
) -> None:
    if (
        profile.source_geometry_id != geometry.source_geometry_id
        or profile.normalized_geometry_revision != geometry.normalized_geometry_revision
        or profile.scale_provenance_id != geometry.scale_provenance_id
        or profile.scale_state is not geometry.scale_state
        or profile.coordinate_unit != geometry.coordinate_unit
    ):
        raise NeckFinishCandidateError("candidate_vertical_profile_provenance_mismatch")
    if len(profile.samples) < 2:
        raise NeckFinishCandidateError("candidate_vertical_profile_support_insufficient")


def _validate_section_evidence(
    geometry: NormalizedMeasurementGeometry,
    evidence: NeckSectionEvidence,
    policy: NeckFinishPolicy,
) -> _SupportedSection:
    section = evidence.horizontal_section
    measurement = evidence.cross_section_measurement
    if (
        section.source_geometry_id != geometry.source_geometry_id
        or section.normalized_geometry_revision != geometry.normalized_geometry_revision
        or section.scale_provenance_id != geometry.scale_provenance_id
        or section.scale_state is not geometry.scale_state
        or section.coordinate_unit != geometry.coordinate_unit
    ):
        raise NeckFinishCandidateError("candidate_horizontal_section_provenance_mismatch")
    if (
        measurement.source_geometry_id != geometry.source_geometry_id
        or measurement.normalized_geometry_revision != geometry.normalized_geometry_revision
        or measurement.scale_provenance_id != geometry.scale_provenance_id
        or measurement.scale_state is not geometry.scale_state
        or measurement.coordinate_unit != geometry.coordinate_unit
    ):
        raise NeckFinishCandidateError("candidate_cross_section_provenance_mismatch")
    if abs(measurement.center[2] - section.requested_z) > policy.z_match_tolerance:
        raise NeckFinishCandidateError("candidate_section_measurement_plane_mismatch")
    if (
        len(section.points) < policy.minimum_points_per_section
        or measurement.sample_count < policy.minimum_points_per_section
    ):
        raise NeckFinishCandidateError("candidate_section_support_insufficient")
    numeric = (
        measurement.major_radius,
        measurement.minor_radius,
        measurement.rms_radial_residual,
        measurement.maximum_radial_residual,
        measurement.maximum_planarity_residual,
    )
    if not all(_positive_finite(value) for value in numeric[:2]) or not all(
        _nonnegative_finite(value) for value in numeric[2:]
    ):
        raise NeckFinishCandidateError("candidate_measurement_quality_invalid")
    if measurement.scale_factor_uncertainty is not None and not _nonnegative_finite(
        measurement.scale_factor_uncertainty
    ):
        raise NeckFinishCandidateError("candidate_scale_uncertainty_invalid")
    return _SupportedSection(
        section.requested_z,
        measurement.major_radius,
        measurement.minor_radius,
        math.sqrt(measurement.major_radius * measurement.minor_radius),
        len(section.points),
        measurement.sample_count,
        measurement.maximum_radial_residual,
        measurement.maximum_planarity_residual,
        measurement.scale_factor_uncertainty,
        measurement.scale_factor_uncertainty_unit,
    )


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0.0
    )


def _nonnegative_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0.0
    )


def _unit_interval(value: object, *, allow_zero: bool = True) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and (allow_zero or value > 0.0)
        and 0.0 <= value <= 1.0
    )


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
