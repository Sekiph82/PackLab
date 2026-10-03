"""Deterministic, Scan Master-bound fitting-strategy recommendations."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .cross_section_measurement import CrossSectionMeasurement
from .design_model_binding import DesignModelParentBindingRevision, bind_design_model_parent
from .geometry_adapter import TriangleMeshData
from .geometry_statistics import (
    GeometryStatistics,
    GeometryStatisticsError,
    GeometryStatisticsPolicy,
    compute_geometry_statistics,
)
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256
from .vertical_profile import VerticalProfile

STRATEGY_CONTRACT = "packlab.fitting-strategy-recommendation.v1"
MAX_STRATEGY_VERTICES = 100_000
MAX_STRATEGY_TRIANGLES = 250_000
MAX_SECTION_SAMPLES = 2_000
MAX_REFLECTION_SAMPLES = 256


class FittingStrategyError(ValueError):
    """Raised when selected Scan Master authority or strategy evidence is invalid."""


class FittingStrategy(StrEnum):
    AXISYMMETRIC_REVOLVE = "axisymmetric_revolve"
    SYMMETRIC_STACKED_SECTION_LOFT = "symmetric_stacked_section_loft"
    REVIEW_REQUIRED = "review_required"


class PrincipalAxis(StrEnum):
    X = "x"
    Y = "y"
    Z = "z"


def _ratio(value: float, field: str, *, lower: float, upper: float = math.inf) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not lower <= value <= upper
    ):
        raise FittingStrategyError(f"{field}_out_of_range")


@dataclass(frozen=True, slots=True)
class FittingStrategyPolicy:
    minimum_sections: int = 3
    minimum_points_per_section: int = 12
    minimum_axis_elongation_ratio: float = 1.15
    minimum_angular_coverage: float = 0.85
    maximum_axisymmetric_radial_cv: float = 0.04
    maximum_bilateral_reflection_error: float = 0.08
    maximum_vertices: int = MAX_STRATEGY_VERTICES
    maximum_triangles: int = MAX_STRATEGY_TRIANGLES

    def __post_init__(self) -> None:
        if (
            isinstance(self.minimum_sections, bool)
            or not isinstance(self.minimum_sections, int)
            or not 3 <= self.minimum_sections <= 9
        ):
            raise FittingStrategyError("minimum_sections_out_of_range")
        if (
            isinstance(self.minimum_points_per_section, bool)
            or not isinstance(self.minimum_points_per_section, int)
            or not 8 <= self.minimum_points_per_section <= MAX_SECTION_SAMPLES
        ):
            raise FittingStrategyError("minimum_section_points_out_of_range")
        _ratio(self.minimum_axis_elongation_ratio, "minimum_axis_elongation_ratio", lower=1.0)
        _ratio(self.minimum_angular_coverage, "minimum_angular_coverage", lower=0.0, upper=1.0)
        _ratio(
            self.maximum_axisymmetric_radial_cv,
            "maximum_axisymmetric_radial_cv",
            lower=0.0,
            upper=1.0,
        )
        _ratio(
            self.maximum_bilateral_reflection_error,
            "maximum_bilateral_reflection_error",
            lower=0.0,
            upper=1.0,
        )
        for name in ("maximum_vertices", "maximum_triangles"):
            value = getattr(self, name)
            cap = MAX_STRATEGY_VERTICES if name == "maximum_vertices" else MAX_STRATEGY_TRIANGLES
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= cap:
                raise FittingStrategyError(f"{name}_out_of_range")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.fitting-strategy-policy.v1",
            "minimum_sections": self.minimum_sections,
            "minimum_points_per_section": self.minimum_points_per_section,
            "minimum_axis_elongation_ratio": self.minimum_axis_elongation_ratio,
            "minimum_angular_coverage": self.minimum_angular_coverage,
            "maximum_axisymmetric_radial_cv": self.maximum_axisymmetric_radial_cv,
            "maximum_bilateral_reflection_error": self.maximum_bilateral_reflection_error,
            "maximum_vertices": self.maximum_vertices,
            "maximum_triangles": self.maximum_triangles,
            "section_sampling_fractions": list(_section_fractions(max(5, self.minimum_sections))),
            "reflection_sampling_policy": "deterministic_even_index_unique_section_samples_v1",
        }


@dataclass(frozen=True, slots=True)
class SectionStrategyEvidence:
    axis_position: float
    point_count: int
    angular_coverage: float
    radial_coefficient_of_variation: float
    left_right_reflection_error: float
    front_back_reflection_error: float

    def as_dict(self) -> dict[str, object]:
        return {
            "axis_position": self.axis_position,
            "point_count": self.point_count,
            "angular_coverage": self.angular_coverage,
            "radial_coefficient_of_variation": self.radial_coefficient_of_variation,
            "left_right_reflection_error": self.left_right_reflection_error,
            "front_back_reflection_error": self.front_back_reflection_error,
        }


@dataclass(frozen=True, slots=True)
class FittingStrategyRecommendation:
    recommendation_id: str
    strategy: FittingStrategy
    principal_axis: PrincipalAxis
    axis_elongation_ratio: float
    section_evidence: tuple[SectionStrategyEvidence, ...]
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    parent_binding: DesignModelParentBindingRevision
    geometry_statistics: GeometryStatistics
    m09_vertical_profile_ids: tuple[str, ...]
    m09_cross_section_measurement_ids: tuple[str, ...]
    uncertainty_codes: tuple[str, ...]
    policy: FittingStrategyPolicy
    coordinate_unit: str
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": STRATEGY_CONTRACT,
            "recommendation_id": self.recommendation_id,
            "strategy": self.strategy.value,
            "principal_axis": self.principal_axis.value,
            "axis_elongation_ratio": self.axis_elongation_ratio,
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "design_model_parent_binding": self.parent_binding.as_dict(),
            },
            "geometry_statistics": self.geometry_statistics.as_dict(),
            "section_evidence": [item.as_dict() for item in self.section_evidence],
            "m09_profile_and_section_evidence": {
                "vertical_profile_ids": list(self.m09_vertical_profile_ids),
                "cross_section_measurement_ids": list(self.m09_cross_section_measurement_ids),
                "authority": "ANCESTOR_CAPTURE_EVIDENCE_ONLY",
            },
            "uncertainty_codes": list(self.uncertainty_codes),
            "policy": self.policy.as_dict(),
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "is_design_model_fit": False,
            "symmetry_is_physical_truth": False,
            "manufacturing_tolerance_claimed": False,
        }


def recommend_fitting_strategy(
    scan_master: ScanMasterRevision,
    *,
    expected_scan_master_revision_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    policy: FittingStrategyPolicy = FittingStrategyPolicy(),
    vertical_profiles: tuple[VerticalProfile, ...] = (),
    cross_section_measurements: tuple[CrossSectionMeasurement, ...] = (),
) -> FittingStrategyRecommendation:
    """Recommend revolve, symmetric loft, or review from exact selected captured geometry."""
    if not isinstance(scan_master, ScanMasterRevision):
        raise FittingStrategyError("scan_master_revision_required")
    if not isinstance(policy, FittingStrategyPolicy):
        raise FittingStrategyError("fitting_strategy_policy_required")
    if scan_master.revision_id != expected_scan_master_revision_id:
        raise FittingStrategyError("selected_scan_master_parent_stale")
    manifest = scan_master.manifest
    digest = mesh_sha256(scan_master.mesh)
    if (
        manifest.get("scan_master_revision_id") != scan_master.revision_id
        or manifest.get("project_id") != scan_master.project_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != digest
        or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or manifest.get("mold_use_authorized") is not False
    ):
        raise FittingStrategyError("scan_master_authority_or_digest_invalid")
    try:
        scale_state = ScaleState(str(manifest.get("scale_state")))
    except ValueError as error:
        raise FittingStrategyError("scan_master_scale_state_invalid") from error
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise FittingStrategyError("scan_master_scale_state_unauthorized")
    scale_provenance_id = manifest.get("scale_provenance_id")
    if not isinstance(scale_provenance_id, str) or not scale_provenance_id:
        raise FittingStrategyError("scan_master_scale_provenance_missing")
    coordinate_unit = (
        "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    )
    binding = bind_design_model_parent(
        scan_master,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    _validate_ancestor_evidence(
        scan_master, scale_state, coordinate_unit, vertical_profiles, cross_section_measurements
    )
    stats = _geometry_statistics(scan_master, scale_state, scale_provenance_id, policy)
    extent = stats.bounds_extent
    axis_index = max(range(3), key=lambda index: (extent[index], index))
    other_extents = tuple(extent[index] for index in range(3) if index != axis_index)
    minor_extent = max(other_extents)
    elongation = extent[axis_index] / minor_extent if minor_extent > 0 else 0.0
    section_evidence = tuple(
        evidence
        for fraction in _section_fractions(max(5, policy.minimum_sections))
        if (
            evidence := _section_evidence(
                scan_master.mesh,
                axis_index,
                stats.bounds_minimum[axis_index] + fraction * extent[axis_index],
                policy.minimum_points_per_section,
            )
        )
        is not None
    )
    strategy, uncertainty = _choose_strategy(
        elongation, section_evidence, policy, axis_index, cross_section_measurements
    )
    body = {
        "contract": STRATEGY_CONTRACT,
        "strategy": strategy.value,
        "axis": axis_index,
        "elongation": elongation,
        "sections": [item.as_dict() for item in section_evidence],
        "scan_master_revision_id": scan_master.revision_id,
        "scan_master_geometry_sha256": digest,
        "parent_binding": binding.as_dict(),
        "geometry_statistics": stats.as_dict(),
        "m09_vertical_profile_ids": [item.profile_id for item in vertical_profiles],
        "m09_cross_section_measurement_ids": [
            item.measurement_id for item in cross_section_measurements
        ],
        "uncertainty_codes": list(uncertainty),
        "policy": policy.as_dict(),
    }
    recommendation_id = (
        "fitting-strategy:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return FittingStrategyRecommendation(
        recommendation_id,
        strategy,
        (PrincipalAxis.X, PrincipalAxis.Y, PrincipalAxis.Z)[axis_index],
        elongation,
        section_evidence,
        scan_master.revision_id,
        digest,
        binding,
        stats,
        tuple(item.profile_id for item in vertical_profiles),
        tuple(item.measurement_id for item in cross_section_measurements),
        uncertainty,
        policy,
        coordinate_unit,
    )


def _geometry_statistics(
    scan_master: ScanMasterRevision,
    scale_state: ScaleState,
    scale_provenance_id: str,
    policy: FittingStrategyPolicy,
) -> GeometryStatistics:
    if (
        len(scan_master.mesh.vertices) > policy.maximum_vertices
        or len(scan_master.mesh.triangles) > policy.maximum_triangles
    ):
        raise FittingStrategyError("scan_master_geometry_work_bound_exceeded")
    try:
        result = compute_geometry_statistics(
            scan_master.mesh,
            geometry_revision_id=scan_master.revision_id,
            scale_state=scale_state,
            scale_provenance_id=scale_provenance_id,
            policy=GeometryStatisticsPolicy(
                maximum_points_or_vertices=policy.maximum_vertices,
                maximum_faces=policy.maximum_triangles,
            ),
        )
    except GeometryStatisticsError as error:
        raise FittingStrategyError("scan_master_geometry_statistics_invalid") from error
    if result.geometry_sha256 != mesh_sha256(scan_master.mesh):
        raise FittingStrategyError("scan_master_geometry_digest_mismatch")
    return result


def _section_fractions(count: int) -> tuple[float, ...]:
    return tuple(0.15 + 0.70 * index / (count - 1) for index in range(count))


def _section_evidence(
    mesh: TriangleMeshData,
    axis: int,
    position: float,
    minimum_points: int,
) -> SectionStrategyEvidence | None:
    remaining_axes = tuple(index for index in range(3) if index != axis)
    points: set[tuple[float, float]] = set()
    for face in mesh.triangles:
        vertices = tuple(mesh.vertices[index] for index in face)
        intersections: set[tuple[float, float]] = set()
        for first, second in (
            (vertices[0], vertices[1]),
            (vertices[1], vertices[2]),
            (vertices[2], vertices[0]),
        ):
            delta_first = first[axis] - position
            delta_second = second[axis] - position
            if delta_first == 0.0:
                intersections.add((first[remaining_axes[0]], first[remaining_axes[1]]))
            if delta_second == 0.0:
                intersections.add((second[remaining_axes[0]], second[remaining_axes[1]]))
            if (delta_first < 0.0) != (delta_second < 0.0):
                ratio = delta_first / (delta_first - delta_second)
                intersections.add(
                    (
                        first[remaining_axes[0]]
                        + ratio * (second[remaining_axes[0]] - first[remaining_axes[0]]),
                        first[remaining_axes[1]]
                        + ratio * (second[remaining_axes[1]] - first[remaining_axes[1]]),
                    )
                )
        points.update(intersections)
    ordered = tuple(sorted(points))
    if len(ordered) < minimum_points:
        return None
    if len(ordered) > MAX_SECTION_SAMPLES:
        ordered = tuple(
            ordered[round(index * (len(ordered) - 1) / (MAX_SECTION_SAMPLES - 1))]
            for index in range(MAX_SECTION_SAMPLES)
        )
    center = (
        math.fsum(point[0] for point in ordered) / len(ordered),
        math.fsum(point[1] for point in ordered) / len(ordered),
    )
    radii = tuple(math.dist(point, center) for point in ordered)
    mean_radius = math.fsum(radii) / len(radii)
    if mean_radius <= 1e-15:
        return None
    radial_cv = (
        math.sqrt(math.fsum((radius - mean_radius) ** 2 for radius in radii) / len(radii))
        / mean_radius
    )
    angles = tuple(
        sorted(
            math.atan2(point[1] - center[1], point[0] - center[0]) % math.tau for point in ordered
        )
    )
    gaps = tuple(right - left for left, right in zip(angles, angles[1:])) + (
        angles[0] + math.tau - angles[-1],
    )
    coverage = 1.0 - max(gaps) / math.tau
    left_right = _reflection_error(ordered, center, reflect_x=True, scale=mean_radius)
    front_back = _reflection_error(ordered, center, reflect_x=False, scale=mean_radius)
    return SectionStrategyEvidence(
        position, len(points), coverage, radial_cv, left_right, front_back
    )


def _reflection_error(
    points: tuple[tuple[float, float], ...],
    center: tuple[float, float],
    *,
    reflect_x: bool,
    scale: float,
) -> float:
    if len(points) > MAX_REFLECTION_SAMPLES:
        selected = tuple(
            points[round(index * (len(points) - 1) / (MAX_REFLECTION_SAMPLES - 1))]
            for index in range(MAX_REFLECTION_SAMPLES)
        )
    else:
        selected = points
    nearest_squared: list[float] = []
    for x, y in selected:
        reflected = (2.0 * center[0] - x, y) if reflect_x else (x, 2.0 * center[1] - y)
        nearest_squared.append(
            min((reflected[0] - px) ** 2 + (reflected[1] - py) ** 2 for px, py in points)
        )
    return math.sqrt(math.fsum(nearest_squared) / len(nearest_squared)) / scale


def _choose_strategy(
    elongation: float,
    sections: tuple[SectionStrategyEvidence, ...],
    policy: FittingStrategyPolicy,
    axis_index: int,
    cross_section_measurements: tuple[CrossSectionMeasurement, ...],
) -> tuple[FittingStrategy, tuple[str, ...]]:
    if len(sections) < policy.minimum_sections:
        return FittingStrategy.REVIEW_REQUIRED, ("insufficient_cross_section_evidence",)
    if elongation < policy.minimum_axis_elongation_ratio:
        return FittingStrategy.REVIEW_REQUIRED, ("principal_axis_not_distinct",)
    if any(item.angular_coverage < policy.minimum_angular_coverage for item in sections):
        return FittingStrategy.REVIEW_REQUIRED, ("cross_section_coverage_insufficient",)
    if all(
        item.radial_coefficient_of_variation <= policy.maximum_axisymmetric_radial_cv
        for item in sections
    ):
        if _measurements_support_revolve(
            cross_section_measurements, axis_index, policy.maximum_axisymmetric_radial_cv
        ):
            return FittingStrategy.AXISYMMETRIC_REVOLVE, ()
        if cross_section_measurements:
            return FittingStrategy.REVIEW_REQUIRED, (
                "m09_cross_section_evidence_conflicts_with_revolve",
            )
    if all(
        item.left_right_reflection_error <= policy.maximum_bilateral_reflection_error
        and item.front_back_reflection_error <= policy.maximum_bilateral_reflection_error
        for item in sections
    ):
        return FittingStrategy.SYMMETRIC_STACKED_SECTION_LOFT, ()
    return FittingStrategy.REVIEW_REQUIRED, ("cross_sections_not_sufficiently_symmetric",)


def _validate_ancestor_evidence(
    scan_master: ScanMasterRevision,
    scale_state: ScaleState,
    coordinate_unit: str,
    vertical_profiles: tuple[VerticalProfile, ...],
    cross_section_measurements: tuple[CrossSectionMeasurement, ...],
) -> None:
    if not isinstance(vertical_profiles, tuple) or any(
        not isinstance(item, VerticalProfile) for item in vertical_profiles
    ):
        raise FittingStrategyError("vertical_profiles_must_be_typed_tuple")
    if not isinstance(cross_section_measurements, tuple) or any(
        not isinstance(item, CrossSectionMeasurement) for item in cross_section_measurements
    ):
        raise FittingStrategyError("cross_section_measurements_must_be_typed_tuple")
    if len(vertical_profiles) > 64 or len(cross_section_measurements) > 64:
        raise FittingStrategyError("ancestor_evidence_count_exceeded")
    manifest = scan_master.manifest
    source_geometry_id = manifest.get("parent_object_geometry_revision_id")
    alignment = manifest.get("alignment_transform")
    transform = alignment.get("transform") if isinstance(alignment, Mapping) else None
    normalized_revision = transform.get("transform_id") if isinstance(transform, Mapping) else None
    scale_provenance_id = manifest.get("scale_provenance_id")
    for profile_evidence in vertical_profiles:
        try:
            matches = _evidence_matches(
                profile_evidence,
                source_geometry_id,
                normalized_revision,
                scale_provenance_id,
                scale_state,
                coordinate_unit,
            )
        except (AttributeError, IndexError, TypeError, ValueError, OverflowError):
            matches = False
        if not matches:
            raise FittingStrategyError("m09_profile_or_section_evidence_stale_or_mismatched")
    for section_evidence in cross_section_measurements:
        try:
            matches = _evidence_matches(
                section_evidence,
                source_geometry_id,
                normalized_revision,
                scale_provenance_id,
                scale_state,
                coordinate_unit,
            )
        except (AttributeError, IndexError, TypeError, ValueError, OverflowError):
            matches = False
        if not matches:
            raise FittingStrategyError("m09_profile_or_section_evidence_stale_or_mismatched")


def _evidence_matches(
    evidence: VerticalProfile | CrossSectionMeasurement,
    source_geometry_id: object,
    normalized_revision: object,
    scale_provenance_id: object,
    scale_state: ScaleState,
    coordinate_unit: str,
) -> bool:
    evidence_id = (
        evidence.profile_id if isinstance(evidence, VerticalProfile) else evidence.measurement_id
    )
    ancestry_matches = (
        isinstance(evidence_id, str)
        and bool(evidence_id)
        and isinstance(evidence.source_geometry_id, str)
        and evidence.source_geometry_id == source_geometry_id
        and evidence.normalized_geometry_revision == normalized_revision
        and evidence.scale_provenance_id == scale_provenance_id
        and evidence.scale_state is scale_state
        and evidence.coordinate_unit == coordinate_unit
    )
    if not ancestry_matches:
        return False
    if isinstance(evidence, VerticalProfile):
        return (
            evidence.method_version == "captured_vertical_plane_samples_v1"
            and isinstance(evidence.samples, tuple)
            and len(evidence.samples) >= 2
            and all(
                math.isfinite(value)
                for value in (
                    *evidence.plane_origin,
                    *evidence.horizontal_direction,
                    *evidence.plane_normal,
                    evidence.lateral_tolerance,
                    *evidence.horizontal_range,
                    *evidence.vertical_range,
                )
            )
        )
    return (
        evidence.method_version == "pca_covariance_ellipse_v1"
        and isinstance(evidence.plane_basis, tuple)
        and len(evidence.plane_basis) == 2
        and all(isinstance(axis, tuple) and len(axis) == 3 for axis in evidence.plane_basis)
        and evidence.sample_count >= 5
        and all(
            math.isfinite(value)
            for value in (
                evidence.major_radius,
                evidence.minor_radius,
                evidence.rms_radial_residual,
                evidence.maximum_radial_residual,
                evidence.maximum_planarity_residual,
                *evidence.center,
                *evidence.plane_basis[0],
                *evidence.plane_basis[1],
            )
        )
        and evidence.major_radius > 0
        and evidence.minor_radius > 0
    )


def _measurements_support_revolve(
    measurements: tuple[CrossSectionMeasurement, ...], axis_index: int, maximum_cv: float
) -> bool:
    for measurement in measurements:
        basis_u, basis_v = measurement.plane_basis
        normal = (
            basis_u[1] * basis_v[2] - basis_u[2] * basis_v[1],
            basis_u[2] * basis_v[0] - basis_u[0] * basis_v[2],
            basis_u[0] * basis_v[1] - basis_u[1] * basis_v[0],
        )
        if abs(abs(normal[axis_index]) - 1.0) <= 1e-3:
            if measurement.major_radius <= 0 or measurement.minor_radius <= 0:
                return False
            axis_ratio_error = 1.0 - measurement.minor_radius / measurement.major_radius
            residual_ratio = measurement.rms_radial_residual / measurement.minor_radius
            if axis_ratio_error > maximum_cv or residual_ratio > maximum_cv:
                return False
    return True


__all__ = [
    "FittingStrategy",
    "FittingStrategyError",
    "FittingStrategyPolicy",
    "FittingStrategyRecommendation",
    "PrincipalAxis",
    "SectionStrategyEvidence",
    "STRATEGY_CONTRACT",
    "recommend_fitting_strategy",
]
