"""Extract captured vertical-plane profile samples without closing missing outlines."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .bounding_dimensions import NormalizedMeasurementGeometry
from .reconstruction import ScaleState

VERTICAL_PROFILE_METHOD_VERSION = "captured_vertical_plane_samples_v1"
MAX_PROFILE_INPUT_POINTS = 250_000
MIN_PROFILE_SAMPLES = 2
Point3 = tuple[float, float, float]


class VerticalProfileError(ValueError):
    """Raised when the selected vertical plane or captured evidence is invalid."""


@dataclass(frozen=True, slots=True)
class VerticalProfileSample:
    source_point_index: int
    captured_point: Point3
    profile_horizontal: float
    profile_vertical: float
    lateral_residual: float


@dataclass(frozen=True, slots=True)
class VerticalProfile:
    profile_id: str
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    coordinate_unit: str
    plane_origin: Point3
    horizontal_direction: Point3
    plane_normal: Point3
    lateral_tolerance: float
    horizontal_range: tuple[float, float]
    vertical_range: tuple[float, float]
    samples: tuple[VerticalProfileSample, ...]
    method_version: str = VERTICAL_PROFILE_METHOD_VERSION

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.vertical-profile.v1",
            "profile_id": self.profile_id,
            "method_version": self.method_version,
            "source_geometry_id": self.source_geometry_id,
            "normalized_geometry_revision": self.normalized_geometry_revision,
            "scale_provenance_id": self.scale_provenance_id,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "selected_plane": {
                "origin": list(self.plane_origin),
                "horizontal_direction": list(self.horizontal_direction),
                "normal": list(self.plane_normal),
            },
            "sampling_policy": {
                "type": "captured_point_projection_with_inclusive_lateral_tolerance",
                "lateral_tolerance": self.lateral_tolerance,
                "smoothing": False,
                "outline_interpolation": False,
                "surface_closure_invented": False,
            },
            "horizontal_range": list(self.horizontal_range),
            "vertical_range": list(self.vertical_range),
            "samples": [
                {
                    "source_point_index": item.source_point_index,
                    "captured_point": list(item.captured_point),
                    "profile_horizontal": item.profile_horizontal,
                    "profile_vertical": item.profile_vertical,
                    "lateral_residual": item.lateral_residual,
                }
                for item in self.samples
            ],
            "sample_count": len(self.samples),
            "authority_class": "OBJECT_CAPTURE_GEOMETRY",
            "generated": False,
            "physical_accuracy_claimed": False,
        }


def extract_vertical_profile(
    geometry: NormalizedMeasurementGeometry,
    *,
    plane_origin: Point3,
    horizontal_direction: Point3,
    lateral_tolerance: float,
    current_geometry_id: str,
    current_normalized_geometry_revision: str,
    current_scale_provenance_id: str | None,
) -> VerticalProfile:
    """Project captured points in a selected vertical plane into ordered profile samples."""

    if geometry.source_geometry_id != current_geometry_id:
        raise VerticalProfileError("profile_source_geometry_parent_stale")
    if geometry.normalized_geometry_revision != current_normalized_geometry_revision:
        raise VerticalProfileError("profile_normalized_geometry_parent_stale")
    if geometry.scale_provenance_id != current_scale_provenance_id:
        raise VerticalProfileError("profile_scale_provenance_parent_stale")
    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise VerticalProfileError("profile_requires_captured_geometry_authority")
    if not geometry.points:
        raise VerticalProfileError("profile_geometry_empty")
    if len(geometry.points) > MAX_PROFILE_INPUT_POINTS:
        raise VerticalProfileError("profile_input_point_count_out_of_bounds")
    origin = _point3(plane_origin, "profile_plane_origin_invalid")
    direction = _point3(horizontal_direction, "profile_direction_invalid")
    if not _nonnegative_finite(lateral_tolerance):
        raise VerticalProfileError("profile_lateral_tolerance_invalid")
    direction_norm = math.sqrt(math.fsum(value * value for value in direction))
    if not math.isfinite(direction_norm) or direction_norm <= 0.0:
        raise VerticalProfileError("profile_direction_degenerate")
    if abs(direction_norm - 1.0) > 1e-6:
        raise VerticalProfileError("profile_direction_must_be_unit_length")
    if abs(direction[2]) > 1e-6:
        raise VerticalProfileError("profile_direction_must_be_horizontal")

    normal = (-direction[1], direction[0], 0.0)
    candidates: list[VerticalProfileSample] = []
    for index, point in enumerate(geometry.points):
        delta = tuple(point[axis] - origin[axis] for axis in range(3))
        lateral = math.fsum(delta[axis] * normal[axis] for axis in range(3))
        if _within_tolerance(abs(lateral), lateral_tolerance, point, origin):
            candidates.append(
                VerticalProfileSample(
                    index,
                    point,
                    math.fsum(delta[axis] * direction[axis] for axis in range(3)),
                    delta[2],
                    abs(lateral),
                )
            )
    samples = tuple(
        sorted(
            candidates,
            key=lambda item: (
                item.profile_horizontal,
                item.profile_vertical,
                item.source_point_index,
            ),
        )
    )
    if len(samples) < MIN_PROFILE_SAMPLES:
        raise VerticalProfileError("profile_insufficient_samples")
    if len({(item.profile_horizontal, item.profile_vertical) for item in samples}) < 2:
        raise VerticalProfileError("profile_projected_samples_degenerate")
    horizontal_values = tuple(item.profile_horizontal for item in samples)
    vertical_values = tuple(item.profile_vertical for item in samples)
    horizontal_range = (min(horizontal_values), max(horizontal_values))
    vertical_range = (min(vertical_values), max(vertical_values))
    body: dict[str, object] = {
        "method_version": VERTICAL_PROFILE_METHOD_VERSION,
        "source_geometry_id": geometry.source_geometry_id,
        "normalized_geometry_revision": geometry.normalized_geometry_revision,
        "scale_provenance_id": geometry.scale_provenance_id,
        "scale_state": geometry.scale_state.value,
        "coordinate_unit": geometry.coordinate_unit,
        "plane_origin": list(origin),
        "horizontal_direction": list(direction),
        "plane_normal": list(normal),
        "lateral_tolerance": lateral_tolerance,
        "samples": [
            [
                item.source_point_index,
                list(item.captured_point),
                item.profile_horizontal,
                item.profile_vertical,
                item.lateral_residual,
            ]
            for item in samples
        ],
    }
    profile_id = (
        "vertical-profile:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return VerticalProfile(
        profile_id,
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.scale_state,
        geometry.coordinate_unit,
        origin,
        direction,
        normal,
        lateral_tolerance,
        horizontal_range,
        vertical_range,
        samples,
    )


def serialize_vertical_profile(profile: VerticalProfile) -> bytes:
    return json.dumps(
        profile.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _point3(value: Point3, error: str) -> Point3:
    if len(value) != 3 or any(not _finite(component) for component in value):
        raise VerticalProfileError(error)
    return (float(value[0]), float(value[1]), float(value[2]))


def _within_tolerance(distance: float, tolerance: float, point: Point3, origin: Point3) -> bool:
    ulp = max(*(math.ulp(value) for value in (*point, *origin)), math.ulp(tolerance))
    return distance <= tolerance + 8.0 * ulp


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _nonnegative_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0.0
    )
