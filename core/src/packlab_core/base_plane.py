"""Bounded, non-mutating captured-geometry base-plane candidates."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass

from .coordinate_frame import coordinate_unit_for_scale_state
from .object_mask_lifting import ObjectCaptureGeometry

BASE_PLANE_METHOD_VERSION = "bounded_seeded_ransac_base_plane_v1"
BASE_PLANE_OVERRIDE_VERSION = "captured_geometry_base_plane_override_v1"
MAX_BASE_PLANE_POINTS = 50_000
MAX_PLANE_HYPOTHESES = 512
MAX_PLANE_CANDIDATES = 8
Point3 = tuple[float, float, float]


class BasePlaneError(ValueError):
    """Raised when captured geometry cannot safely produce a plane result."""


class BasePlaneOverrideError(BasePlaneError):
    """Raised when a manual plane override is stale or unsupported by geometry."""


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0.0
    )


@dataclass(frozen=True, slots=True)
class BasePlaneProfile:
    profile_id: str = "base-plane-support-v1"
    distance_tolerance: float = 0.01
    minimum_inliers: int = 6
    minimum_inlier_ratio: float = 0.10
    maximum_hypotheses: int = 512
    ambiguity_ratio_delta: float = 0.02

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not self.profile_id.strip():
            raise BasePlaneError("profile_id_required")
        if not _positive_finite(self.distance_tolerance):
            raise BasePlaneError("distance_tolerance_must_be_positive_finite")
        if (
            not isinstance(self.minimum_inliers, int)
            or isinstance(self.minimum_inliers, bool)
            or self.minimum_inliers < 3
        ):
            raise BasePlaneError("minimum_inliers_must_be_integer_at_least_three")
        if not _finite(self.minimum_inlier_ratio) or not 0.0 < self.minimum_inlier_ratio <= 1.0:
            raise BasePlaneError("minimum_inlier_ratio_must_be_in_(0,1]")
        if (
            not isinstance(self.maximum_hypotheses, int)
            or isinstance(self.maximum_hypotheses, bool)
            or not 1 <= self.maximum_hypotheses <= MAX_PLANE_HYPOTHESES
        ):
            raise BasePlaneError("maximum_hypotheses_out_of_bounds")
        if not _finite(self.ambiguity_ratio_delta) or not 0.0 <= self.ambiguity_ratio_delta <= 1.0:
            raise BasePlaneError("ambiguity_ratio_delta_must_be_in_[0,1]")

    def as_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "distance_tolerance": self.distance_tolerance,
            "minimum_inliers": self.minimum_inliers,
            "minimum_inlier_ratio": self.minimum_inlier_ratio,
            "maximum_hypotheses": self.maximum_hypotheses,
            "ambiguity_ratio_delta": self.ambiguity_ratio_delta,
            "inlier_boundary": "absolute_signed_distance_lte_tolerance",
        }


@dataclass(frozen=True, slots=True)
class BasePlaneCandidate:
    candidate_id: str
    normal: Point3
    offset: float
    inlier_indices: tuple[int, ...]
    inlier_ratio: float
    rms_residual: float
    confidence_score: float
    confidence_semantics: str

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "plane_equation": {
                "normal": list(self.normal),
                "offset": self.offset,
                "signed_distance": "dot(normal,point)+offset",
            },
            "inlier_indices": list(self.inlier_indices),
            "inlier_ratio": self.inlier_ratio,
            "rms_residual": self.rms_residual,
            "confidence_score": self.confidence_score,
            "confidence_semantics": self.confidence_semantics,
            "authority": "candidate_only_requires_explicit_selection",
        }


@dataclass(frozen=True, slots=True)
class BasePlaneDetectionResult:
    status: str
    geometry_id: str
    reconstruction_revision: str
    camera_solution_revision: str
    coordinate_unit: str
    source_points_digest: str
    profile: BasePlaneProfile
    hypotheses_evaluated: int
    candidates: tuple[BasePlaneCandidate, ...]
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.base-plane-detection.v1",
            "status": self.status,
            "geometry_id": self.geometry_id,
            "reconstruction_revision": self.reconstruction_revision,
            "camera_solution_revision": self.camera_solution_revision,
            "coordinate_unit": self.coordinate_unit,
            "source_points_digest": self.source_points_digest,
            "method_version": BASE_PLANE_METHOD_VERSION,
            "profile": self.profile.as_dict(),
            "hypotheses_evaluated": self.hypotheses_evaluated,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "errors": list(self.errors),
            "mutates_source_geometry": False,
        }


@dataclass(frozen=True, slots=True)
class BasePlaneOverride:
    override_id: str
    actor_id: str
    reason: str
    geometry_id: str
    reconstruction_revision: str
    camera_solution_revision: str
    normal: Point3
    offset: float
    evidence_point_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class BasePlaneSelection:
    selection_id: str
    selection_method: str
    override_version: str | None
    actor_id: str | None
    reason: str | None
    geometry_id: str
    reconstruction_revision: str
    camera_solution_revision: str
    coordinate_unit: str
    source_points_digest: str
    candidate: BasePlaneCandidate

    def require_current_geometry(self, geometry: ObjectCaptureGeometry) -> None:
        if (
            geometry.geometry_id != self.geometry_id
            or geometry.reconstruction_revision != self.reconstruction_revision
            or geometry.camera_solution_revision != self.camera_solution_revision
            or _points_digest(geometry.filtered_points) != self.source_points_digest
        ):
            raise BasePlaneError("base_plane_selection_stale_parent_geometry")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.base-plane-selection.v1",
            "selection_id": self.selection_id,
            "selection_method": self.selection_method,
            "override_version": self.override_version,
            "actor_id": self.actor_id,
            "reason": self.reason,
            "geometry_id": self.geometry_id,
            "reconstruction_revision": self.reconstruction_revision,
            "camera_solution_revision": self.camera_solution_revision,
            "coordinate_unit": self.coordinate_unit,
            "source_points_digest": self.source_points_digest,
            "candidate": self.candidate.as_dict(),
            "mutates_source_geometry": False,
        }


def detect_base_plane_candidates(
    geometry: ObjectCaptureGeometry,
    profile: BasePlaneProfile = BasePlaneProfile(),
) -> BasePlaneDetectionResult:
    """Find bounded, deterministic planar patches in captured object geometry."""

    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise BasePlaneError("base_plane_requires_non_generated_object_capture_geometry")
    points = geometry.filtered_points
    coordinate_unit = coordinate_unit_for_scale_state(geometry.scale_state)
    if not points or len(points) > MAX_BASE_PLANE_POINTS:
        points_digest = _digest({"geometry_id": geometry.geometry_id, "point_count": len(points)})
        return _result(
            geometry,
            points_digest,
            coordinate_unit,
            profile,
            "no_plane",
            0,
            (),
            ("captured_geometry_point_count_out_of_bounds",),
        )
    if any(len(point) != 3 or not all(_finite(value) for value in point) for point in points):
        points_digest = _digest(
            {"geometry_id": geometry.geometry_id, "invalid_points": len(points)}
        )
        return _result(
            geometry,
            points_digest,
            coordinate_unit,
            profile,
            "invalid_geometry",
            0,
            (),
            ("captured_geometry_contains_non_finite_or_non_3d_point",),
        )
    points_digest = _points_digest(points)
    hypotheses = _triplets(points, profile.maximum_hypotheses, points_digest)
    candidates: list[BasePlaneCandidate] = []
    for first, second, third in hypotheses:
        plane = _plane_from_triplet(points[first], points[second], points[third])
        if plane is None:
            continue
        normal, offset = plane
        inliers = tuple(
            index
            for index, point in enumerate(points)
            if abs(_signed_distance(normal, offset, point)) <= profile.distance_tolerance
        )
        if len(inliers) < profile.minimum_inliers:
            continue
        ratio = len(inliers) / len(points)
        if ratio < profile.minimum_inlier_ratio:
            continue
        residuals = tuple(abs(_signed_distance(normal, offset, points[index])) for index in inliers)
        rms = math.sqrt(sum(value * value for value in residuals) / len(residuals))
        candidate = _candidate(
            normal, offset, inliers, ratio, rms, points_digest, profile.distance_tolerance
        )
        same_index = next(
            (
                index
                for index, old in enumerate(candidates)
                if _same_plane(candidate, old, profile.distance_tolerance)
            ),
            None,
        )
        if same_index is None:
            candidates.append(candidate)
        elif _candidate_rank(candidate) < _candidate_rank(candidates[same_index]):
            candidates[same_index] = candidate
    candidates.sort(
        key=lambda item: (-len(item.inlier_indices), item.rms_residual, item.candidate_id)
    )
    candidates = candidates[:MAX_PLANE_CANDIDATES]
    if not candidates:
        return _result(
            geometry,
            points_digest,
            coordinate_unit,
            profile,
            "no_plane",
            len(hypotheses),
            (),
            ("no_plane_met_minimum_support",),
        )
    ambiguous = len(candidates) > 1 and (
        candidates[0].inlier_ratio - candidates[1].inlier_ratio <= profile.ambiguity_ratio_delta
    )
    return _result(
        geometry,
        points_digest,
        coordinate_unit,
        profile,
        "ambiguous" if ambiguous else "candidate",
        len(hypotheses),
        tuple(candidates),
        ("multiple_similarly_supported_planes_require_user_selection",) if ambiguous else (),
    )


def apply_base_plane_override(
    geometry: ObjectCaptureGeometry,
    override: BasePlaneOverride,
    profile: BasePlaneProfile = BasePlaneProfile(),
) -> BasePlaneSelection:
    """Validate and bind an explicit user plane override to exact geometry."""

    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise BasePlaneOverrideError("override_requires_non_generated_object_capture_geometry")
    for name in ("override_id", "actor_id", "reason"):
        value = getattr(override, name)
        if not isinstance(value, str) or not value.strip():
            raise BasePlaneOverrideError(f"override_{name}_required")
    if (
        override.geometry_id != geometry.geometry_id
        or override.reconstruction_revision != geometry.reconstruction_revision
        or override.camera_solution_revision != geometry.camera_solution_revision
    ):
        raise BasePlaneOverrideError("override_parent_revision_mismatch")
    if len(geometry.filtered_points) > MAX_BASE_PLANE_POINTS:
        raise BasePlaneOverrideError("captured_geometry_point_count_out_of_bounds")
    if any(
        len(point) != 3 or not all(_finite(value) for value in point)
        for point in geometry.filtered_points
    ):
        raise BasePlaneOverrideError("captured_geometry_contains_non_finite_or_non_3d_point")
    if len(override.normal) != 3 or not all(_finite(value) for value in override.normal):
        raise BasePlaneOverrideError("override_normal_must_be_finite_3d")
    magnitude = math.sqrt(sum(value * value for value in override.normal))
    if magnitude <= 1e-12 or not _finite(override.offset):
        raise BasePlaneOverrideError("override_plane_invalid")
    normal: Point3 = (
        override.normal[0] / magnitude,
        override.normal[1] / magnitude,
        override.normal[2] / magnitude,
    )
    offset = override.offset / magnitude
    indices = override.evidence_point_indices
    if (
        len(indices) < 3
        or len(indices) > 64
        or len(set(indices)) != len(indices)
        or any(not isinstance(index, int) or isinstance(index, bool) for index in indices)
        or any(index < 0 or index >= len(geometry.filtered_points) for index in indices)
    ):
        raise BasePlaneOverrideError("override_evidence_point_indices_invalid")
    evidence = tuple(geometry.filtered_points[index] for index in indices)
    if any(not all(_finite(value) for value in point) for point in evidence):
        raise BasePlaneOverrideError("override_geometry_point_invalid")
    if any(
        abs(_signed_distance(normal, offset, point)) > profile.distance_tolerance
        for point in evidence
    ):
        raise BasePlaneOverrideError("override_plane_not_supported_by_selected_geometry_points")
    if not _has_non_collinear_evidence(evidence):
        raise BasePlaneOverrideError("override_evidence_points_are_collinear")
    inliers = tuple(
        index
        for index, point in enumerate(geometry.filtered_points)
        if abs(_signed_distance(normal, offset, point)) <= profile.distance_tolerance
    )
    ratio = len(inliers) / len(geometry.filtered_points) if geometry.filtered_points else 0.0
    if len(inliers) < profile.minimum_inliers or ratio < profile.minimum_inlier_ratio:
        raise BasePlaneOverrideError("override_plane_support_below_profile_threshold")
    residuals = tuple(
        abs(_signed_distance(normal, offset, geometry.filtered_points[i])) for i in inliers
    )
    rms = math.sqrt(sum(value * value for value in residuals) / len(residuals))
    points_digest = _points_digest(geometry.filtered_points)
    candidate = _candidate(
        normal, offset, inliers, ratio, rms, points_digest, profile.distance_tolerance
    )
    selection_id = _digest(
        {
            "override_id": override.override_id,
            "geometry_id": geometry.geometry_id,
            "reconstruction_revision": geometry.reconstruction_revision,
            "camera_solution_revision": geometry.camera_solution_revision,
            "actor_id": override.actor_id,
            "reason": override.reason,
            "evidence_point_indices": list(indices),
            "candidate": candidate.as_dict(),
            "version": BASE_PLANE_OVERRIDE_VERSION,
        }
    )
    return BasePlaneSelection(
        selection_id,
        "manual_override",
        BASE_PLANE_OVERRIDE_VERSION,
        override.actor_id,
        override.reason,
        geometry.geometry_id,
        geometry.reconstruction_revision,
        geometry.camera_solution_revision,
        coordinate_unit_for_scale_state(geometry.scale_state),
        points_digest,
        candidate,
    )


def _triplets(
    points: tuple[Point3, ...], maximum: int, seed_digest: str
) -> tuple[tuple[int, int, int], ...]:
    total = len(points) * (len(points) - 1) * (len(points) - 2) // 6
    if total <= maximum:
        return tuple(itertools.combinations(range(len(points)), 3))
    triplets: set[tuple[int, int, int]] = set()
    counter = 0
    while len(triplets) < maximum:
        block = hashlib.sha256(f"{seed_digest}:{counter}".encode()).digest()
        counter += 1
        values = [
            int.from_bytes(block[start : start + 4], "big") % len(points) for start in (0, 4, 8)
        ]
        if len(set(values)) == 3:
            first, second, third = sorted(values)
            triplets.add((first, second, third))
    return tuple(sorted(triplets))


def _plane_from_triplet(
    first: Point3, second: Point3, third: Point3
) -> tuple[Point3, float] | None:
    normal = _cross(_subtract(second, first), _subtract(third, first))
    magnitude = math.sqrt(_dot(normal, normal))
    if magnitude <= 1e-12:
        return None
    unit: Point3 = (
        normal[0] / magnitude,
        normal[1] / magnitude,
        normal[2] / magnitude,
    )
    dominant = max(range(3), key=lambda axis: (abs(unit[axis]), -axis))
    if unit[dominant] < 0:
        unit = (-unit[0], -unit[1], -unit[2])
    offset = -_dot(unit, first)
    return unit, offset


def _candidate(
    normal: Point3,
    offset: float,
    inliers: tuple[int, ...],
    ratio: float,
    rms: float,
    points_digest: str,
    distance_tolerance: float,
) -> BasePlaneCandidate:
    identity = {
        "normal": list(normal),
        "offset": offset,
        "inlier_indices": list(inliers),
        "points_digest": points_digest,
        "method_version": BASE_PLANE_METHOD_VERSION,
    }
    candidate_id = f"base-plane:{_digest(identity)}"
    confidence = min(1.0, max(0.0, ratio * math.exp(-rms / distance_tolerance)))
    return BasePlaneCandidate(
        candidate_id,
        normal,
        offset,
        inliers,
        ratio,
        rms,
        confidence,
        "support_residual_heuristic_not_probability_or_accuracy",
    )


def _same_plane(candidate: BasePlaneCandidate, other: BasePlaneCandidate, tolerance: float) -> bool:
    return (
        _dot(candidate.normal, other.normal) >= 0.999
        and abs(candidate.offset - other.offset) <= tolerance
    )


def _candidate_rank(candidate: BasePlaneCandidate) -> tuple[int, float, str]:
    return (-len(candidate.inlier_indices), candidate.rms_residual, candidate.candidate_id)


def _result(
    geometry: ObjectCaptureGeometry,
    points_digest: str,
    coordinate_unit: str,
    profile: BasePlaneProfile,
    status: str,
    hypotheses: int,
    candidates: tuple[BasePlaneCandidate, ...],
    errors: tuple[str, ...],
) -> BasePlaneDetectionResult:
    return BasePlaneDetectionResult(
        status,
        geometry.geometry_id,
        geometry.reconstruction_revision,
        geometry.camera_solution_revision,
        coordinate_unit,
        points_digest,
        profile,
        hypotheses,
        candidates,
        errors,
    )


def _points_digest(points: tuple[Point3, ...]) -> str:
    return _digest([list(point) for point in points])


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    ).hexdigest()


def _signed_distance(normal: Point3, offset: float, point: Point3) -> float:
    return _dot(normal, point) + offset


def _has_non_collinear_evidence(points: tuple[Point3, ...]) -> bool:
    first = points[0]
    for second_index in range(1, len(points) - 1):
        second = points[second_index]
        for third in points[second_index + 1 :]:
            cross = _cross(_subtract(second, first), _subtract(third, first))
            if _dot(cross, cross) > 1e-24:
                return True
    return False


def _subtract(first: Point3, second: Point3) -> Point3:
    return (first[0] - second[0], first[1] - second[1], first[2] - second[2])


def _cross(first: Point3, second: Point3) -> Point3:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _dot(first: Point3, second: Point3) -> float:
    return sum(left * right for left, right in zip(first, second, strict=True))
