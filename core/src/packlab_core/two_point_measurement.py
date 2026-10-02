"""Versioned two-point distance measurement on normalized captured geometry."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .bounding_dimensions import NormalizedMeasurementGeometry
from .reconstruction import ScaleState

TWO_POINT_METHOD_VERSION = "normalized_two_point_distance_v1"
SNAP_POLICY_VERSION = "captured_point_nearest_v1"
MAX_SNAP_CANDIDATES = 250_000
Point3 = tuple[float, float, float]


class TwoPointMeasurementError(ValueError):
    """Raised when point input, snapping, or measurement provenance is invalid."""


@dataclass(frozen=True, slots=True)
class SnapPolicy:
    enabled: bool
    radius: float
    ambiguity_tolerance: float
    coordinate_unit: str
    version: str = SNAP_POLICY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TwoPointMeasurementError("snap_enabled_must_be_boolean")
        if not _nonnegative_finite(self.radius):
            raise TwoPointMeasurementError("snap_radius_must_be_finite_nonnegative")
        if not _nonnegative_finite(self.ambiguity_tolerance):
            raise TwoPointMeasurementError("snap_ambiguity_tolerance_must_be_finite_nonnegative")
        if not isinstance(self.coordinate_unit, str) or not self.coordinate_unit.strip():
            raise TwoPointMeasurementError("snap_coordinate_unit_required")
        if self.version != SNAP_POLICY_VERSION:
            raise TwoPointMeasurementError("snap_policy_version_unsupported")

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "enabled": self.enabled,
            "radius": self.radius,
            "ambiguity_tolerance": self.ambiguity_tolerance,
            "coordinate_unit": self.coordinate_unit,
            "candidate_source": "normalized_object_capture_points",
        }


@dataclass(frozen=True, slots=True)
class TwoPointDistanceMeasurement:
    measurement_id: str
    normalized_geometry_revision: str
    source_geometry_id: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    coordinate_unit: str
    requested_points: tuple[Point3, Point3]
    measured_points: tuple[Point3, Point3]
    snapped_candidate_indices: tuple[int | None, int | None]
    snap_distances: tuple[float | None, float | None]
    snap_policy: SnapPolicy
    distance: float
    scale_factor_uncertainty: float | None
    scale_factor_uncertainty_unit: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.two-point-distance.v1",
            "method_version": TWO_POINT_METHOD_VERSION,
            "measurement_id": self.measurement_id,
            "normalized_geometry_revision": self.normalized_geometry_revision,
            "source_geometry_id": self.source_geometry_id,
            "scale_provenance_id": self.scale_provenance_id,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "requested_points": [list(point) for point in self.requested_points],
            "measured_points": [list(point) for point in self.measured_points],
            "snapped_candidate_indices": list(self.snapped_candidate_indices),
            "snap_distances": list(self.snap_distances),
            "snap_policy": self.snap_policy.as_dict(),
            "distance": self.distance,
            "uncertainty_inputs": {
                "scale_factor_uncertainty": self.scale_factor_uncertainty,
                "scale_factor_uncertainty_unit": self.scale_factor_uncertainty_unit,
                "propagation_status": "preserved_for_PL-0217",
            },
            "authority_class": "OBJECT_CAPTURE_GEOMETRY",
            "generated": False,
            "distance_uncertainty_propagated": False,
            "physical_accuracy_claimed": False,
        }


def measure_two_point_distance(
    geometry: NormalizedMeasurementGeometry,
    first: Point3,
    second: Point3,
    *,
    snap_policy: SnapPolicy,
    current_geometry_id: str,
    current_normalized_geometry_revision: str,
    current_scale_provenance_id: str | None,
) -> TwoPointDistanceMeasurement:
    """Measure the Euclidean distance, optionally snapping to captured points."""

    if geometry.source_geometry_id != current_geometry_id:
        raise TwoPointMeasurementError("measurement_source_geometry_parent_stale")
    if geometry.normalized_geometry_revision != current_normalized_geometry_revision:
        raise TwoPointMeasurementError("measurement_normalized_geometry_revision_stale")
    if geometry.scale_provenance_id != current_scale_provenance_id:
        raise TwoPointMeasurementError("measurement_scale_provenance_stale")
    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise TwoPointMeasurementError("measurement_requires_captured_geometry_authority")
    if snap_policy.coordinate_unit != geometry.coordinate_unit:
        raise TwoPointMeasurementError("snap_policy_unit_mismatch")
    if len(geometry.points) > MAX_SNAP_CANDIDATES:
        raise TwoPointMeasurementError("snap_candidate_count_out_of_bounds")
    requested = (_validate_point(first), _validate_point(second))
    measured: list[Point3] = []
    snapped_indices: list[int | None] = []
    snap_distances: list[float | None] = []
    for point in requested:
        snapped, candidate_index, snap_distance = _snap(point, geometry.points, snap_policy)
        measured.append(snapped)
        snapped_indices.append(candidate_index)
        snap_distances.append(snap_distance)
    distance = math.dist(measured[0], measured[1])
    if not math.isfinite(distance):
        raise TwoPointMeasurementError("measured_distance_non_finite")
    body: dict[str, object] = {
        "method_version": TWO_POINT_METHOD_VERSION,
        "normalized_geometry_revision": geometry.normalized_geometry_revision,
        "source_geometry_id": geometry.source_geometry_id,
        "scale_provenance_id": geometry.scale_provenance_id,
        "scale_state": geometry.scale_state.value,
        "coordinate_unit": geometry.coordinate_unit,
        "requested_points": [list(point) for point in requested],
        "measured_points": [list(point) for point in measured],
        "snapped_candidate_indices": snapped_indices,
        "snap_distances": snap_distances,
        "snap_policy": snap_policy.as_dict(),
        "distance": distance,
        "scale_factor_uncertainty": geometry.scale_factor_uncertainty,
        "scale_factor_uncertainty_unit": geometry.scale_factor_uncertainty_unit,
    }
    measurement_id = (
        "two-point-distance:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return TwoPointDistanceMeasurement(
        measurement_id,
        geometry.normalized_geometry_revision,
        geometry.source_geometry_id,
        geometry.scale_provenance_id,
        geometry.scale_state,
        geometry.coordinate_unit,
        requested,
        (measured[0], measured[1]),
        (snapped_indices[0], snapped_indices[1]),
        (snap_distances[0], snap_distances[1]),
        snap_policy,
        distance,
        geometry.scale_factor_uncertainty,
        geometry.scale_factor_uncertainty_unit,
    )


def serialize_two_point_measurement(result: TwoPointDistanceMeasurement) -> bytes:
    return json.dumps(
        result.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _snap(
    requested: Point3,
    candidates: tuple[Point3, ...],
    policy: SnapPolicy,
) -> tuple[Point3, int | None, float | None]:
    if not policy.enabled or not candidates:
        return requested, None, None
    ranked = sorted(
        (math.dist(requested, candidate), index, candidate)
        for index, candidate in enumerate(candidates)
    )
    if any(not math.isfinite(item[0]) for item in ranked):
        raise TwoPointMeasurementError("snap_distance_non_finite")
    if ranked[0][0] > policy.radius:
        return requested, None, None
    if (
        len(ranked) > 1
        and ranked[1][0] <= policy.radius
        and ranked[1][0] - ranked[0][0] <= policy.ambiguity_tolerance
    ):
        raise TwoPointMeasurementError("snap_candidate_ambiguous")
    return ranked[0][2], ranked[0][1], ranked[0][0]


def _validate_point(point: Point3) -> Point3:
    if len(point) != 3 or any(
        not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value)
        for value in point
    ):
        raise TwoPointMeasurementError("measurement_point_must_be_finite_3d")
    return (float(point[0]), float(point[1]), float(point[2]))


def _nonnegative_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0.0
    )
