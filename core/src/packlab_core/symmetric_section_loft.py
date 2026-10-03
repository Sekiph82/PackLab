"""Pinned Scan Master section capture into editable cross-sections and loft previews."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum

from .cross_section import (
    CrossSection,
    CrossSectionError,
    CrossSectionSymmetry,
    SectionPoint,
    create_cross_section,
)
from .design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    stable_feature_id,
)
from .design_model_binding import DesignModelParentBindingRevision
from .design_operations import DesignOperation, LoftSectionInput, create_loft_operation
from .design_preview import DesignPreview, tessellate_design_preview
from .fitting_strategy import (
    STRATEGY_CONTRACT,
    FittingStrategy,
    FittingStrategyRecommendation,
    PrincipalAxis,
)
from .geometry_adapter import TriangleMeshData
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

MAX_LOFT_CAPTURE_SECTIONS = 64
MAX_CAPTURE_WORK = 4_000_000


class SectionLoftError(ValueError):
    """Raised when pinned sections, symmetry evidence, or loft construction is invalid."""


class SectionLoftStatus(StrEnum):
    READY = "READY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class SectionSymmetryEvidence:
    requested_height: float
    center_x: float
    center_y: float
    left_right_reflection_error_ratio: float
    front_back_reflection_error_ratio: float
    symmetry_constraint_enabled: bool
    disposition: str

    def as_dict(self) -> dict[str, object]:
        return {
            "requested_height": self.requested_height,
            "center": [self.center_x, self.center_y],
            "left_right_reflection_error_ratio": self.left_right_reflection_error_ratio,
            "front_back_reflection_error_ratio": self.front_back_reflection_error_ratio,
            "symmetry_constraint_enabled": self.symmetry_constraint_enabled,
            "disposition": self.disposition,
        }


@dataclass(frozen=True, slots=True)
class SymmetricSectionLoft:
    status: SectionLoftStatus
    review_required: bool
    model_revision_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    parent_binding_revision_id: str
    strategy_recommendation_id: str
    sections: tuple[CrossSection, ...]
    section_heights: tuple[float, ...]
    symmetry_evidence: tuple[SectionSymmetryEvidence, ...]
    model: DesignModelRevision
    operation: DesignOperation
    preview: DesignPreview
    coordinate_unit: str
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.symmetric-section-loft.v1",
            "status": self.status.value,
            "review_required": self.review_required,
            "authority_class": "DESIGN_MODEL_OPERATION_WITH_PREVIEW_PROXY",
            "model_revision_id": self.model_revision_id,
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "parent_binding_revision_id": self.parent_binding_revision_id,
            },
            "strategy_recommendation_id": self.strategy_recommendation_id,
            "sections": [item.as_dict() for item in self.sections],
            "section_heights": list(self.section_heights),
            "symmetry_evidence": [item.as_dict() for item in self.symmetry_evidence],
            "operation": self.operation.as_dict(),
            "preview": self.preview.as_dict(),
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "scan_master_replaced": False,
            "preview_is_parametric_truth": False,
            "cad_or_brep_generated": False,
        }


def fit_symmetric_section_loft(
    scan_master: ScanMasterRevision,
    strategy: FittingStrategyRecommendation,
    *,
    expected_scan_master_revision_id: str,
    expected_strategy_recommendation_id: str,
    section_heights: tuple[float, ...],
    component_id: str,
    symmetry_constraints_enabled: bool,
    maximum_reflection_error_ratio: float = 0.08,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    package_family: PackageFamily = PackageFamily.BOTTLE,
    chord_tolerance: float = 0.25,
    maximum_preview_angular_segments: int = 256,
) -> SymmetricSectionLoft:
    """Capture ordered section contours, preserve their points, and create a loft proxy."""
    digest, scale_state, unit = _validate_source(scan_master, expected_scan_master_revision_id)
    _validate_strategy(strategy, expected_strategy_recommendation_id, scan_master, digest, unit)
    _validate_text(component_id, "component_id")
    if not isinstance(package_family, PackageFamily):
        raise SectionLoftError("package_family_invalid")
    if not isinstance(symmetry_constraints_enabled, bool):
        raise SectionLoftError("symmetry_constraint_toggle_invalid")
    if (
        isinstance(maximum_reflection_error_ratio, bool)
        or not isinstance(maximum_reflection_error_ratio, (int, float))
        or not math.isfinite(maximum_reflection_error_ratio)
        or not 0.0 <= maximum_reflection_error_ratio <= 0.25
    ):
        raise SectionLoftError("symmetry_reflection_tolerance_out_of_range")
    _validate_heights(scan_master.mesh, section_heights)
    if strategy.strategy not in {
        FittingStrategy.SYMMETRIC_STACKED_SECTION_LOFT,
        FittingStrategy.REVIEW_REQUIRED,
    }:
        raise SectionLoftError("strategy_not_supported_for_section_loft")
    if (
        symmetry_constraints_enabled
        and strategy.strategy is not FittingStrategy.SYMMETRIC_STACKED_SECTION_LOFT
    ):
        raise SectionLoftError("symmetric_loft_strategy_evidence_required")

    policy_payload = {
        "symmetry_constraints_enabled": symmetry_constraints_enabled,
        "maximum_reflection_error_ratio": float(maximum_reflection_error_ratio),
        "section_capture": "pinned_scan_master_triangle_plane_intersections_v1",
        "point_order": "stable_polar_angle_about_arithmetic_centroid_v1",
    }
    estimated_work = len(scan_master.mesh.triangles) * len(section_heights)
    if estimated_work > MAX_CAPTURE_WORK:
        raise SectionLoftError("section_capture_work_bound_exceeded")

    sections: list[CrossSection] = []
    evidence: list[SectionSymmetryEvidence] = []
    unresolved_asymmetry = False
    reflection_work = 0
    for height in section_heights:
        points, center_x, center_y = _intersect_section(scan_master.mesh, height)
        reflection_work += len(points) * min(len(points), 256) * 2
        if reflection_work > MAX_CAPTURE_WORK:
            raise SectionLoftError("section_reflection_work_bound_exceeded")
        left_right_error = _reflection_error(points, center_x, center_y, reflect_x=True)
        front_back_error = _reflection_error(points, center_x, center_y, reflect_x=False)
        supported = (
            left_right_error <= maximum_reflection_error_ratio
            and front_back_error <= maximum_reflection_error_ratio
        )
        if symmetry_constraints_enabled and not supported:
            raise SectionLoftError("section_symmetry_evidence_exceeds_policy")
        unresolved_asymmetry = unresolved_asymmetry or not supported
        constrained_points = (
            _constrain_bilateral_symmetry(
                points,
                center_x,
                center_y,
                max(
                    max(math.hypot(item.x - center_x, item.y - center_y) for item in points) * 1e-6,
                    1e-9,
                ),
            )
            if symmetry_constraints_enabled
            else points
        )
        constraint = (
            CrossSectionSymmetry.BOTH if symmetry_constraints_enabled else CrossSectionSymmetry.NONE
        )
        try:
            section = create_cross_section(
                component_id,
                constrained_points,
                symmetry=constraint,
                center_x=center_x,
                center_y=center_y,
                scale_state=scale_state,
            )
        except CrossSectionError as error:
            raise SectionLoftError("captured_section_not_supported_as_simple_profile") from error
        sections.append(section)
        evidence.append(
            SectionSymmetryEvidence(
                height,
                center_x,
                center_y,
                left_right_error,
                front_back_error,
                symmetry_constraints_enabled,
                "CONSTRAINED_SYMMETRIC"
                if symmetry_constraints_enabled
                else "OBSERVED_POINTS_PRESERVED"
                if supported
                else "OBSERVED_ASYMMETRY_PRESERVED_REVIEW_REQUIRED",
            )
        )

    review_required = strategy.strategy is FittingStrategy.REVIEW_REQUIRED or (
        not symmetry_constraints_enabled and unresolved_asymmetry
    )
    status = SectionLoftStatus.REVIEW_REQUIRED if review_required else SectionLoftStatus.READY
    binding = strategy.parent_binding
    section_features = tuple(
        DesignModelFeatureReference(
            stable_feature_id(component_id, FeatureKind.BODY, f"loft-section:{index:04d}"),
            component_id,
            FeatureKind.BODY,
            f"loft-section:{index:04d}",
        )
        for index in range(len(sections))
    )
    params = (
        DesignModelParameter(
            "stacked_section_strategy_evidence",
            {
                "recommendation_id": strategy.recommendation_id,
                "strategy": strategy.strategy.value,
                "principal_axis": strategy.principal_axis.value,
                "scan_master_geometry_sha256": digest,
                "section_evidence": [item.as_dict() for item in strategy.section_evidence],
            },
            ParameterType.OBJECT,
        ),
        DesignModelParameter(
            "stacked_section_heights",
            list(section_heights),
            ParameterType.ARRAY,
            unit,
        ),
        DesignModelParameter("stacked_section_policy", policy_payload, ParameterType.OBJECT),
        DesignModelParameter(
            "stacked_section_symmetry_evidence",
            [item.as_dict() for item in evidence],
            ParameterType.ARRAY,
        ),
    )
    model = create_design_model_revision(
        binding,
        package_family=package_family,
        parameters=params,
        features=section_features,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    loft_inputs = tuple(
        LoftSectionInput(feature.feature_id, section, height)
        for feature, section, height in zip(
            section_features, sections, section_heights, strict=True
        )
    )
    operation = create_loft_operation(model, loft_inputs)
    previews = tessellate_design_preview(
        model,
        cross_sections=tuple(sections),
        operations=(operation,),
        chord_tolerance=chord_tolerance,
        maximum_angular_segments=maximum_preview_angular_segments,
    )
    if len(previews) != 1:
        raise SectionLoftError("loft_preview_result_invalid")
    return SymmetricSectionLoft(
        status,
        review_required,
        model.revision_id,
        scan_master.revision_id,
        digest,
        binding.revision_id,
        strategy.recommendation_id,
        tuple(sections),
        section_heights,
        tuple(evidence),
        model,
        operation,
        previews[0],
        unit,
    )


def _validate_source(
    scan_master: ScanMasterRevision, expected_revision_id: str
) -> tuple[str, ScaleState, str]:
    if not isinstance(scan_master, ScanMasterRevision):
        raise SectionLoftError("scan_master_revision_required")
    if scan_master.revision_id != expected_revision_id:
        raise SectionLoftError("scan_master_parent_stale")
    mesh = scan_master.mesh
    if len(mesh.vertices) > 100_000 or len(mesh.triangles) > 250_000:
        raise SectionLoftError("scan_master_mesh_work_bound_exceeded")
    if not mesh.vertices or not mesh.triangles:
        raise SectionLoftError("scan_master_mesh_evidence_empty")
    digest = mesh_sha256(mesh)
    manifest = scan_master.manifest
    if (
        manifest.get("scan_master_revision_id") != scan_master.revision_id
        or manifest.get("project_id") != scan_master.project_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != digest
        or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or manifest.get("mold_use_authorized") is not False
    ):
        raise SectionLoftError("scan_master_authority_or_digest_invalid")
    try:
        scale_state = ScaleState(str(manifest.get("scale_state")))
    except ValueError as error:
        raise SectionLoftError("scan_master_scale_state_invalid") from error
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise SectionLoftError("scan_master_scale_state_unauthorized")
    if not isinstance(manifest.get("scale_provenance_id"), str) or not manifest.get(
        "scale_provenance_id"
    ):
        raise SectionLoftError("scan_master_scale_provenance_missing")
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    return digest, scale_state, unit


def _validate_strategy(
    strategy: FittingStrategyRecommendation,
    expected_id: str,
    scan_master: ScanMasterRevision,
    digest: str,
    unit: str,
) -> None:
    if not isinstance(strategy, FittingStrategyRecommendation):
        raise SectionLoftError("fitting_strategy_recommendation_required")
    if strategy.recommendation_id != expected_id:
        raise SectionLoftError("fitting_strategy_recommendation_stale")
    if (
        not isinstance(strategy.parent_binding, DesignModelParentBindingRevision)
        or not isinstance(strategy.strategy, FittingStrategy)
        or not isinstance(strategy.principal_axis, PrincipalAxis)
        or strategy.scan_master_revision_id != scan_master.revision_id
        or strategy.scan_master_geometry_sha256 != digest
        or strategy.parent_binding.project_id != scan_master.project_id
        or strategy.parent_binding.fitted_to_scan_master_revision_id != scan_master.revision_id
        or strategy.parent_binding.scan_master_geometry_sha256 != digest
        or strategy.parent_binding.scale_provenance_id
        != scan_master.manifest.get("scale_provenance_id")
        or strategy.parent_binding.scale_state.value != scan_master.manifest.get("scale_state")
        or strategy.coordinate_unit != unit
        or strategy.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or strategy.mold_use_authorized is not False
        or strategy.principal_axis is not PrincipalAxis.Z
    ):
        raise SectionLoftError("fitting_strategy_parent_or_axis_invalid")
    axis_index = {PrincipalAxis.X: 0, PrincipalAxis.Y: 1, PrincipalAxis.Z: 2}.get(
        strategy.principal_axis
    )
    if axis_index is None:
        raise SectionLoftError("fitting_strategy_axis_invalid")
    body = {
        "contract": STRATEGY_CONTRACT,
        "strategy": strategy.strategy.value,
        "axis": axis_index,
        "elongation": strategy.axis_elongation_ratio,
        "sections": [item.as_dict() for item in strategy.section_evidence],
        "scan_master_revision_id": strategy.scan_master_revision_id,
        "scan_master_geometry_sha256": strategy.scan_master_geometry_sha256,
        "parent_binding": strategy.parent_binding.as_dict(),
        "geometry_statistics": strategy.geometry_statistics.as_dict(),
        "m09_vertical_profile_ids": list(strategy.m09_vertical_profile_ids),
        "m09_cross_section_measurement_ids": list(strategy.m09_cross_section_measurement_ids),
        "uncertainty_codes": list(strategy.uncertainty_codes),
        "policy": strategy.policy.as_dict(),
    }
    identity = (
        "fitting-strategy:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    if identity != strategy.recommendation_id:
        raise SectionLoftError("fitting_strategy_identity_invalid")


def _validate_heights(mesh: TriangleMeshData, heights: tuple[float, ...]) -> None:
    if not isinstance(heights, tuple) or not 3 <= len(heights) <= MAX_LOFT_CAPTURE_SECTIONS:
        raise SectionLoftError("section_height_count_out_of_range")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in heights
    ):
        raise SectionLoftError("section_height_invalid")
    if any(right <= left for left, right in zip(heights, heights[1:])):
        raise SectionLoftError("section_heights_must_be_strictly_ordered")
    z_min = min(point[2] for point in mesh.vertices)
    z_max = max(point[2] for point in mesh.vertices)
    if heights[0] <= z_min or heights[-1] >= z_max:
        raise SectionLoftError("section_heights_outside_supported_mesh_interior")


def _intersect_section(
    mesh: TriangleMeshData, height: float
) -> tuple[tuple[SectionPoint, ...], float, float]:
    intersections: list[tuple[float, float]] = []
    exact_level_points = tuple(point[:2] for point in mesh.vertices if point[2] == height)
    if len(set(exact_level_points)) >= 8:
        intersections.extend(exact_level_points)
    else:
        for triangle in mesh.triangles:
            vertices = tuple(mesh.vertices[index] for index in triangle)
            for index in range(3):
                first = vertices[index]
                second = vertices[(index + 1) % 3]
                low, high = sorted((first[2], second[2]))
                if not low <= height <= high or high == low:
                    continue
                parameter = (height - first[2]) / (second[2] - first[2])
                if not 0.0 <= parameter <= 1.0:
                    continue
                x = first[0] + parameter * (second[0] - first[0])
                y = first[1] + parameter * (second[1] - first[1])
                intersections.append((x, y))
    if len(intersections) < 8:
        raise SectionLoftError("section_intersection_support_out_of_range")
    magnitude = max(max(abs(x), abs(y)) for x, y in intersections)
    tolerance = max(magnitude * 1e-12, 1e-14)
    unique = {(round(x / tolerance), round(y / tolerance)) for x, y in intersections}
    if not 8 <= len(unique) <= 4096:
        raise SectionLoftError("section_intersection_support_out_of_range")
    canonical = tuple((key[0] * tolerance, key[1] * tolerance) for key in sorted(unique))
    center_x = math.fsum(point[0] for point in canonical) / len(canonical)
    center_y = math.fsum(point[1] for point in canonical) / len(canonical)
    ordered = tuple(
        SectionPoint(x, y)
        for x, y in sorted(
            canonical,
            key=lambda point: (
                math.atan2(point[1] - center_y, point[0] - center_x),
                point[0],
                point[1],
            ),
        )
    )
    return ordered, center_x, center_y


def _reflection_error(
    points: tuple[SectionPoint, ...], center_x: float, center_y: float, *, reflect_x: bool
) -> float:
    if len(points) > 256:
        selected = tuple(points[round(index * (len(points) - 1) / 255)] for index in range(256))
    else:
        selected = points
    radius = max(math.hypot(item.x - center_x, item.y - center_y) for item in points)
    if radius <= 0:
        raise SectionLoftError("section_intersection_radius_invalid")
    errors: list[float] = []
    for point in selected:
        target = (
            (2.0 * center_x - point.x, point.y)
            if reflect_x
            else (point.x, 2.0 * center_y - point.y)
        )
        nearest = min(math.hypot(target[0] - item.x, target[1] - item.y) for item in points)
        errors.append(nearest / radius)
    return math.sqrt(math.fsum(value * value for value in errors) / len(errors))


def _constrain_bilateral_symmetry(
    points: tuple[SectionPoint, ...], center_x: float, center_y: float, tolerance: float
) -> tuple[SectionPoint, ...]:
    parent = list(range(len(points)))

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def join(left: int, right: int) -> None:
        root_left, root_right = root(left), root(right)
        if root_left != root_right:
            parent[max(root_left, root_right)] = min(root_left, root_right)

    transforms = (
        lambda point: point,
        lambda point: SectionPoint(2 * center_x - point.x, point.y),
        lambda point: SectionPoint(point.x, 2 * center_y - point.y),
        lambda point: SectionPoint(2 * center_x - point.x, 2 * center_y - point.y),
    )
    for index, point in enumerate(points):
        for transform in transforms[1:]:
            target = transform(point)
            nearest_index = min(
                range(len(points)),
                key=lambda candidate: math.hypot(
                    points[candidate].x - target.x, points[candidate].y - target.y
                ),
            )
            distance = math.hypot(
                points[nearest_index].x - target.x, points[nearest_index].y - target.y
            )
            if distance > tolerance:
                raise SectionLoftError("section_symmetry_constraint_mirror_unmatched")
            join(index, nearest_index)

    groups: dict[int, list[int]] = {}
    for index in range(len(points)):
        groups.setdefault(root(index), []).append(index)
    updated = list(points)
    for indices in groups.values():
        anchor_index = min(indices)
        anchor = points[anchor_index]
        expected_positions: list[SectionPoint] = []
        for transform in transforms:
            candidate = transform(anchor)
            if not any(
                math.hypot(item.x - candidate.x, item.y - candidate.y) <= 1e-9
                for item in expected_positions
            ):
                expected_positions.append(candidate)
        projected: dict[int, list[SectionPoint]] = {}
        for candidate in expected_positions:
            target_index = min(
                indices,
                key=lambda index: math.hypot(
                    points[index].x - candidate.x, points[index].y - candidate.y
                ),
            )
            projected.setdefault(target_index, []).append(candidate)
        for target_index, orbit_positions in projected.items():
            updated[target_index] = SectionPoint(
                math.fsum(item.x for item in orbit_positions) / len(orbit_positions),
                math.fsum(item.y for item in orbit_positions) / len(orbit_positions),
            )
    return tuple(updated)


def _validate_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 1000:
        raise SectionLoftError(f"{field}_invalid")
    if field == "component_id" and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]{0,127}", value):
        raise SectionLoftError("component_id_invalid")


__all__ = [
    "SectionLoftError",
    "SectionLoftStatus",
    "SectionSymmetryEvidence",
    "SymmetricSectionLoft",
    "fit_symmetric_section_loft",
]
