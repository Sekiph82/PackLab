"""Parametric, bounded jerrycan handle-opening Design Model features."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

from .design_history import DesignEditCommand, EditTargetKind, create_edit_command
from .design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    ParameterType,
    revise_design_model_revision,
    stable_feature_id,
)
from .jerrycan_handle_void_candidates import (
    HandleVoidCandidate,
    HandleVoidDetection,
    HandleVoidStatus,
)

MAX_PROFILE_VERTICES = 64
_DIGEST = re.compile(r"^[0-9a-f]{64}$")

Point2 = tuple[float, float]
Bounds2 = tuple[float, float, float, float]


class JerrycanHandleOpeningError(ValueError):
    """Raised when handle-opening evidence or constrained profile is invalid."""


@dataclass(frozen=True, slots=True)
class JerrycanHandleOpening:
    feature: DesignModelFeatureReference
    candidate_id: str
    candidate_contour_sha256: str
    parent_body_feature_ids: tuple[str, ...]
    plane_axis: str
    plane_position: float
    profile: tuple[Point2, ...]
    clearance: float
    clearance_envelope: Bounds2
    safe_profile_bounds: Bounds2
    coordinate_unit: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.jerrycan-handle-opening.v1",
            "authority_class": "DESIGN_MODEL_FEATURE",
            "feature": self.feature.as_dict(),
            "candidate_id": self.candidate_id,
            "candidate_contour_sha256": self.candidate_contour_sha256,
            "parent_body_feature_ids": list(self.parent_body_feature_ids),
            "plane": {"axis": self.plane_axis, "position": self.plane_position},
            "profile": [list(point) for point in self.profile],
            "profile_source": "explicit_parametric_profile_within_candidate_bounding_envelope",
            "clearance": self.clearance,
            "clearance_envelope": list(self.clearance_envelope),
            "safe_profile_bounds": list(self.safe_profile_bounds),
            "coordinate_unit": self.coordinate_unit,
            "scan_master_mutated": False,
            "hidden_extent_inferred": False,
            "limitations": [
                "candidate_contour_not_embedded; profile_constraints_use_candidate_2d_bounds_only",
                "one_selected_plane_does_not_establish_full_three_dimensional_opening_extent",
            ],
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


def create_jerrycan_handle_opening(
    revision: DesignModelRevision,
    detection: HandleVoidDetection,
    candidate_id: str,
    *,
    profile: Sequence[Sequence[float]],
    clearance: float,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelRevision:
    """Add an explicitly profiled opening inside one accepted 2D void candidate."""

    candidate, body_features = _accepted_candidate(revision, detection, candidate_id)
    bounds = _candidate_bounds(candidate)
    clearance_value = _finite_number(clearance, "clearance_invalid")
    safe_bounds = _safe_bounds(bounds, clearance_value)
    profile_points = _validated_profile(profile, safe_bounds)
    semantic_key = _semantic_key(candidate)
    feature = DesignModelFeatureReference(
        stable_feature_id(body_features[0].component_id, FeatureKind.HANDLE_OPENING, semantic_key),
        body_features[0].component_id,
        FeatureKind.HANDLE_OPENING,
        semantic_key,
    )
    if any(item.feature_id == feature.feature_id for item in revision.features):
        raise JerrycanHandleOpeningError("handle_opening_already_exists")

    parameters = _opening_parameters(
        semantic_key,
        revision,
        candidate,
        detection,
        body_features,
        profile_points,
        bounds,
        safe_bounds,
        clearance_value,
    )
    try:
        return _new_revision(
            revision,
            parameters=(*revision.parameters, *parameters),
            features=(*revision.features, feature),
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise JerrycanHandleOpeningError("handle_opening_design_model_invalid") from error


def resolve_jerrycan_handle_opening(
    revision: DesignModelRevision, feature_id: str
) -> JerrycanHandleOpening:
    """Resolve one opening and verify its persisted parameters remain constrained."""

    if not isinstance(revision, DesignModelRevision):
        raise JerrycanHandleOpeningError("design_model_revision_required")
    if revision.package_family is not PackageFamily.JERRYCAN:
        raise JerrycanHandleOpeningError("jerrycan_design_model_required")
    feature = next(
        (
            item
            for item in revision.features
            if item.feature_id == feature_id and item.feature_kind is FeatureKind.HANDLE_OPENING
        ),
        None,
    )
    if feature is None:
        raise JerrycanHandleOpeningError("handle_opening_feature_missing_or_stale")
    candidate_digest = _semantic_digest(feature.semantic_key)
    prefix = f"handle-opening:{candidate_digest}:"
    parameters = {item.parameter_id.removeprefix(prefix): item for item in revision.parameters}
    required = {
        "candidate",
        "profile",
        "clearance",
        "envelope",
        "safe_bounds",
        "body_features",
        "plane",
    }
    if not required.issubset(parameters):
        raise JerrycanHandleOpeningError("handle_opening_parameters_missing")

    candidate_data = _object_value(parameters["candidate"])
    plane = _object_value(parameters["plane"])
    candidate_id = _string_field(candidate_data, "candidate_id")
    contour_digest = _string_field(candidate_data, "contour_sha256")
    if _DIGEST.fullmatch(contour_digest) is None:
        raise JerrycanHandleOpeningError("candidate_contour_digest_invalid")
    if (
        candidate_id != f"jerrycan-handle-void-candidate:{candidate_digest}"
        or candidate_data.get("scan_master_revision_id")
        != revision.fitted_to_scan_master_revision_id
        or candidate_data.get("scan_master_geometry_sha256") != revision.scan_master_geometry_sha256
    ):
        raise JerrycanHandleOpeningError("handle_opening_candidate_provenance_invalid")
    parent_ids = _string_array(parameters["body_features"])
    profile = _point_array(parameters["profile"])
    clearance = _finite_number(parameters["clearance"].as_dict()["value"], "clearance_invalid")
    envelope = _bounds_array(parameters["envelope"])
    safe_bounds = _bounds_array(parameters["safe_bounds"])
    if any(
        parameters[name].unit != revision.coordinate_unit
        for name in ("profile", "clearance", "envelope", "safe_bounds")
    ):
        raise JerrycanHandleOpeningError("handle_opening_unit_mismatch")
    if safe_bounds != _safe_bounds(envelope, clearance):
        raise JerrycanHandleOpeningError("handle_opening_clearance_constraint_invalid")
    _validated_profile(profile, safe_bounds)
    if not parent_ids or any(
        not any(
            item.feature_id == parent_id
            and item.feature_kind is FeatureKind.BODY
            and item.component_id == feature.component_id
            for item in revision.features
        )
        for parent_id in parent_ids
    ):
        raise JerrycanHandleOpeningError("handle_opening_body_reference_invalid")
    axis = _string_field(plane, "axis")
    position = _finite_number(plane.get("position"), "handle_opening_plane_invalid")
    return JerrycanHandleOpening(
        feature,
        candidate_id,
        contour_digest,
        parent_ids,
        axis,
        position,
        profile,
        clearance,
        envelope,
        safe_bounds,
        revision.coordinate_unit,
    )


def create_handle_opening_profile_edit(
    revision: DesignModelRevision,
    feature_id: str,
    profile: Sequence[Sequence[float]],
) -> DesignEditCommand:
    """Create a history command for a moved/resized profile after validating constraints."""

    opening = resolve_jerrycan_handle_opening(revision, feature_id)
    new_profile = _validated_profile(profile, opening.safe_profile_bounds)
    parameter_id = _parameter_id(opening.feature.semantic_key, "profile")
    current = _parameter(revision, parameter_id)
    updated = DesignModelParameter(
        parameter_id,
        [list(point) for point in new_profile],
        ParameterType.ARRAY,
        opening.coordinate_unit,
    )
    try:
        return create_edit_command(
            revision.revision_id,
            EditTargetKind.PARAMETER,
            parameter_id,
            current,
            updated,
        )
    except DesignModelError as error:
        raise JerrycanHandleOpeningError("handle_opening_profile_edit_invalid") from error


def move_jerrycan_handle_opening(
    revision: DesignModelRevision,
    feature_id: str,
    *,
    offset: Point2,
) -> DesignEditCommand:
    """Return a constrained 2D translation command for an existing opening profile."""

    opening = resolve_jerrycan_handle_opening(revision, feature_id)
    if not isinstance(offset, (tuple, list)) or len(offset) != 2:
        raise JerrycanHandleOpeningError("handle_opening_offset_invalid")
    dx = _finite_number(offset[0], "handle_opening_offset_invalid")
    dy = _finite_number(offset[1], "handle_opening_offset_invalid")
    return create_handle_opening_profile_edit(
        revision,
        feature_id,
        tuple((x + dx, y + dy) for x, y in opening.profile),
    )


def resize_jerrycan_handle_opening(
    revision: DesignModelRevision,
    feature_id: str,
    *,
    width_scale: float,
    height_scale: float,
) -> DesignEditCommand:
    """Return a constrained center-based profile resize command."""

    opening = resolve_jerrycan_handle_opening(revision, feature_id)
    sx = _positive_number(width_scale, "handle_opening_scale_invalid")
    sy = _positive_number(height_scale, "handle_opening_scale_invalid")
    x_values = [point[0] for point in opening.profile]
    y_values = [point[1] for point in opening.profile]
    center_x = (min(x_values) + max(x_values)) / 2
    center_y = (min(y_values) + max(y_values)) / 2
    profile = tuple(
        (center_x + (x - center_x) * sx, center_y + (y - center_y) * sy) for x, y in opening.profile
    )
    return create_handle_opening_profile_edit(revision, feature_id, profile)


def _accepted_candidate(
    revision: DesignModelRevision,
    detection: HandleVoidDetection,
    candidate_id: str,
) -> tuple[HandleVoidCandidate, tuple[DesignModelFeatureReference, ...]]:
    if not isinstance(revision, DesignModelRevision) or not isinstance(
        detection, HandleVoidDetection
    ):
        raise JerrycanHandleOpeningError("accepted_handle_void_detection_required")
    if revision.package_family is not PackageFamily.JERRYCAN:
        raise JerrycanHandleOpeningError("jerrycan_design_model_required")
    if (
        detection.status is not HandleVoidStatus.CANDIDATE
        or not detection.selected_plane_coverage_complete
        or len(detection.candidates) != 1
        or detection.design_model_revision_id != revision.revision_id
        or detection.scan_master_revision_id != revision.fitted_to_scan_master_revision_id
        or detection.scan_master_geometry_sha256 != revision.scan_master_geometry_sha256
        or detection.parent_binding_revision_id != revision.parent_binding_revision_id
        or detection.coordinate_unit != revision.coordinate_unit
    ):
        raise JerrycanHandleOpeningError("handle_void_candidate_stale_ambiguous_or_incomplete")
    candidates = tuple(item for item in detection.candidates if item.candidate_id == candidate_id)
    if len(candidates) != 1:
        raise JerrycanHandleOpeningError("handle_void_candidate_missing_or_ambiguous")
    candidate = candidates[0]
    if (
        candidate.confidence != "HIGH_SECTION_SUPPORT"
        or candidate.ambiguity != "single_enclosed_region_candidate_only"
    ):
        raise JerrycanHandleOpeningError("handle_void_candidate_requires_review")
    bodies = tuple(
        sorted(
            (
                item
                for item in revision.features
                if item.feature_kind is FeatureKind.BODY
                and item.feature_id in candidate.parent_feature_ids
            ),
            key=lambda item: item.feature_id,
        )
    )
    if not bodies or {item.feature_id for item in bodies} != set(candidate.parent_feature_ids):
        raise JerrycanHandleOpeningError("handle_void_body_reference_stale")
    if len({item.component_id for item in bodies}) != 1:
        raise JerrycanHandleOpeningError("handle_void_candidate_body_ambiguous")
    return candidate, bodies


def _opening_parameters(
    semantic_key: str,
    revision: DesignModelRevision,
    candidate: HandleVoidCandidate,
    detection: HandleVoidDetection,
    bodies: tuple[DesignModelFeatureReference, ...],
    profile: tuple[Point2, ...],
    envelope: Bounds2,
    safe_bounds: Bounds2,
    clearance: float,
) -> tuple[DesignModelParameter, ...]:
    candidate_data = {
        "candidate_id": candidate.candidate_id,
        "contour_sha256": candidate.contour_sha256,
        "scan_master_revision_id": detection.scan_master_revision_id,
        "scan_master_geometry_sha256": detection.scan_master_geometry_sha256,
        "source_design_model_revision_id": detection.design_model_revision_id,
        "parent_binding_revision_id": detection.parent_binding_revision_id,
        "plane": detection.plane.as_dict(detection.coordinate_unit),
        "profile_source": "explicit_parametric_profile_within_candidate_bounding_envelope",
        "hidden_extent_inferred": False,
    }
    plane_data = {"axis": detection.plane.axis.value, "position": detection.plane.position}
    return (
        DesignModelParameter(
            _parameter_id(semantic_key, "candidate"),
            candidate_data,
            ParameterType.OBJECT,
        ),
        DesignModelParameter(
            _parameter_id(semantic_key, "profile"),
            [list(point) for point in profile],
            ParameterType.ARRAY,
            revision.coordinate_unit,
        ),
        DesignModelParameter(
            _parameter_id(semantic_key, "clearance"),
            clearance,
            ParameterType.NUMBER,
            revision.coordinate_unit,
        ),
        DesignModelParameter(
            _parameter_id(semantic_key, "envelope"),
            list(envelope),
            ParameterType.ARRAY,
            revision.coordinate_unit,
        ),
        DesignModelParameter(
            _parameter_id(semantic_key, "safe_bounds"),
            list(safe_bounds),
            ParameterType.ARRAY,
            revision.coordinate_unit,
        ),
        DesignModelParameter(
            _parameter_id(semantic_key, "body_features"),
            [item.feature_id for item in bodies],
            ParameterType.ARRAY,
        ),
        DesignModelParameter(
            _parameter_id(semantic_key, "plane"),
            plane_data,
            ParameterType.OBJECT,
        ),
    )


def _new_revision(
    revision: DesignModelRevision,
    *,
    parameters: tuple[DesignModelParameter, ...],
    features: tuple[DesignModelFeatureReference, ...],
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelRevision:
    return revise_design_model_revision(
        revision,
        parameters=parameters,
        features=features,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )


def _semantic_key(candidate: HandleVoidCandidate) -> str:
    if _DIGEST.fullmatch(candidate.candidate_id.rsplit(":", 1)[-1]) is None:
        raise JerrycanHandleOpeningError("handle_void_candidate_identity_invalid")
    if _DIGEST.fullmatch(candidate.contour_sha256) is None:
        raise JerrycanHandleOpeningError("handle_void_candidate_contour_invalid")
    return f"handle-opening:{candidate.candidate_id.rsplit(':', 1)[-1]}"


def _semantic_digest(semantic_key: str) -> str:
    prefix, separator, digest = semantic_key.partition(":")
    if prefix != "handle-opening" or not separator or _DIGEST.fullmatch(digest) is None:
        raise JerrycanHandleOpeningError("handle_opening_semantic_key_invalid")
    return digest


def _parameter_id(semantic_key: str, name: str) -> str:
    return f"handle-opening:{_semantic_digest(semantic_key)}:{name}"


def _parameter(revision: DesignModelRevision, parameter_id: str) -> DesignModelParameter:
    matches = tuple(item for item in revision.parameters if item.parameter_id == parameter_id)
    if len(matches) != 1:
        raise JerrycanHandleOpeningError("handle_opening_parameter_missing_or_ambiguous")
    return matches[0]


def _object_value(parameter: DesignModelParameter) -> dict[str, object]:
    value = parameter.as_dict()["value"]
    if not isinstance(value, dict):
        raise JerrycanHandleOpeningError("handle_opening_object_parameter_invalid")
    return value


def _string_field(value: dict[str, object], name: str) -> str:
    field = value.get(name)
    if not isinstance(field, str) or not field:
        raise JerrycanHandleOpeningError("handle_opening_string_parameter_invalid")
    return field


def _string_array(parameter: DesignModelParameter) -> tuple[str, ...]:
    value = parameter.as_dict()["value"]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise JerrycanHandleOpeningError("handle_opening_body_parameter_invalid")
    return tuple(value)


def _bounds_array(parameter: DesignModelParameter) -> Bounds2:
    value = parameter.as_dict()["value"]
    if not isinstance(value, list) or len(value) != 4:
        raise JerrycanHandleOpeningError("handle_opening_bounds_invalid")
    numbers = tuple(_finite_number(item, "handle_opening_bounds_invalid") for item in value)
    if numbers[0] >= numbers[2] or numbers[1] >= numbers[3]:
        raise JerrycanHandleOpeningError("handle_opening_bounds_invalid")
    return numbers  # type: ignore[return-value]


def _point_array(parameter: DesignModelParameter) -> tuple[Point2, ...]:
    value = parameter.as_dict()["value"]
    if not isinstance(value, list):
        raise JerrycanHandleOpeningError("handle_opening_profile_invalid")
    return _validated_profile(value, (-math.inf, -math.inf, math.inf, math.inf))


def _candidate_bounds(candidate: HandleVoidCandidate) -> Bounds2:
    if len(candidate.region_bounds) != 4:
        raise JerrycanHandleOpeningError("handle_void_candidate_bounds_invalid")
    bounds = tuple(
        _finite_number(item, "handle_void_candidate_bounds_invalid")
        for item in candidate.region_bounds
    )
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise JerrycanHandleOpeningError("handle_void_candidate_bounds_invalid")
    return bounds  # type: ignore[return-value]


def _finite_number(value: object, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise JerrycanHandleOpeningError(code)
    result = float(value)
    if not math.isfinite(result):
        raise JerrycanHandleOpeningError(code)
    return result


def _positive_number(value: object, code: str) -> float:
    result = _finite_number(value, code)
    if result <= 0:
        raise JerrycanHandleOpeningError(code)
    return result


def _safe_bounds(bounds: Bounds2, clearance: float) -> Bounds2:
    margin = _positive_number(clearance, "handle_opening_clearance_invalid")
    safe = (bounds[0] + margin, bounds[1] + margin, bounds[2] - margin, bounds[3] - margin)
    if safe[0] >= safe[2] or safe[1] >= safe[3]:
        raise JerrycanHandleOpeningError("handle_opening_clearance_exceeds_candidate")
    return safe


def _validated_profile(profile: Sequence[Sequence[float]], bounds: Bounds2) -> tuple[Point2, ...]:
    if not isinstance(profile, (tuple, list)) or not 3 <= len(profile) <= MAX_PROFILE_VERTICES:
        raise JerrycanHandleOpeningError("handle_opening_profile_vertex_count_invalid")
    points: list[Point2] = []
    for point in profile:
        if not isinstance(point, (tuple, list)) or len(point) != 2:
            raise JerrycanHandleOpeningError("handle_opening_profile_point_invalid")
        points.append(
            (
                _finite_number(point[0], "handle_opening_profile_point_invalid"),
                _finite_number(point[1], "handle_opening_profile_point_invalid"),
            )
        )
    result = tuple(points)
    if len(set(result)) != len(result):
        raise JerrycanHandleOpeningError("handle_opening_profile_duplicate_point")
    for x, y in result:
        if x < bounds[0] or x > bounds[2] or y < bounds[1] or y > bounds[3]:
            raise JerrycanHandleOpeningError("handle_opening_profile_outside_supported_bounds")
    twice_area = sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(result, (*result[1:], result[0]), strict=True)
    )
    if abs(twice_area) <= 1e-12:
        raise JerrycanHandleOpeningError("handle_opening_profile_area_invalid")
    if _self_intersects(result):
        raise JerrycanHandleOpeningError("handle_opening_profile_self_intersects")
    return result


def _self_intersects(points: tuple[Point2, ...]) -> bool:
    edges = tuple(zip(points, (*points[1:], points[0]), strict=True))
    for first in range(len(edges)):
        for second in range(first + 1, len(edges)):
            if second == first + 1 or (first == 0 and second == len(edges) - 1):
                continue
            if _segments_intersect(*edges[first], *edges[second]):
                return True
    return False


def _segments_intersect(a: Point2, b: Point2, c: Point2, d: Point2) -> bool:
    def orientation(p: Point2, q: Point2, r: Point2) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def on_segment(p: Point2, q: Point2, r: Point2) -> bool:
        return min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= q[1] <= max(
            p[1], r[1]
        )

    ab_c = orientation(a, b, c)
    ab_d = orientation(a, b, d)
    cd_a = orientation(c, d, a)
    cd_b = orientation(c, d, b)
    if ab_c * ab_d < 0 and cd_a * cd_b < 0:
        return True
    epsilon = 1e-12
    return (
        abs(ab_c) <= epsilon
        and on_segment(a, c, b)
        or abs(ab_d) <= epsilon
        and on_segment(a, d, b)
        or abs(cd_a) <= epsilon
        and on_segment(c, a, d)
        or abs(cd_b) <= epsilon
        and on_segment(c, b, d)
    )


__all__ = [
    "JerrycanHandleOpening",
    "JerrycanHandleOpeningError",
    "create_handle_opening_profile_edit",
    "create_jerrycan_handle_opening",
    "move_jerrycan_handle_opening",
    "resize_jerrycan_handle_opening",
    "resolve_jerrycan_handle_opening",
]
