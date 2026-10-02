"""Extract ordered horizontal sections from normalized captured point clouds."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .bounding_dimensions import NormalizedMeasurementGeometry
from .reconstruction import ScaleState

HORIZONTAL_SECTION_METHOD_VERSION = "captured_point_z_slab_v1"
MAX_CAPTURED_POINTS = 250_000
MAX_SLAB_FRACTION_OF_Z_EXTENT = 0.1
MAX_SLAB_HALF_WIDTH = 1.0
Point3 = tuple[float, float, float]


class HorizontalSectionError(ValueError):
    """Raised when section inputs, parent revisions, or captured evidence are invalid."""


@dataclass(frozen=True, slots=True)
class HorizontalSectionPoint:
    source_point_index: int
    point: Point3
    z_offset: float


@dataclass(frozen=True, slots=True)
class HorizontalSection:
    section_id: str
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    coordinate_unit: str
    requested_z: float
    z_range: tuple[float, float]
    slab_half_width: float
    maximum_allowed_slab_half_width: float
    points: tuple[HorizontalSectionPoint, ...]
    method_version: str = HORIZONTAL_SECTION_METHOD_VERSION

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.horizontal-section.v1",
            "section_id": self.section_id,
            "method_version": self.method_version,
            "source_geometry_id": self.source_geometry_id,
            "normalized_geometry_revision": self.normalized_geometry_revision,
            "scale_provenance_id": self.scale_provenance_id,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "requested_z": self.requested_z,
            "z_range": list(self.z_range),
            "slab_policy": {
                "type": "inclusive_absolute_distance_from_requested_z",
                "half_width": self.slab_half_width,
                "maximum_allowed_half_width": self.maximum_allowed_slab_half_width,
                "maximum_fraction_of_captured_z_extent": MAX_SLAB_FRACTION_OF_Z_EXTENT,
            },
            "points": [
                {
                    "source_point_index": item.source_point_index,
                    "point": list(item.point),
                    "z_offset": item.z_offset,
                }
                for item in self.points
            ],
            "sample_count": len(self.points),
            "surface_interpolation_performed": False,
            "surface_closure_invented": False,
            "authority_class": "OBJECT_CAPTURE_GEOMETRY",
            "generated": False,
            "physical_accuracy_claimed": False,
        }


def extract_horizontal_section(
    geometry: NormalizedMeasurementGeometry,
    requested_z: float,
    *,
    slab_half_width: float,
    current_geometry_id: str,
    current_normalized_geometry_revision: str,
    current_scale_provenance_id: str | None,
) -> HorizontalSection:
    """Return captured points in an inclusive, bounded slab around canonical Z."""

    if geometry.source_geometry_id != current_geometry_id:
        raise HorizontalSectionError("section_source_geometry_parent_stale")
    if geometry.normalized_geometry_revision != current_normalized_geometry_revision:
        raise HorizontalSectionError("section_normalized_geometry_parent_stale")
    if geometry.scale_provenance_id != current_scale_provenance_id:
        raise HorizontalSectionError("section_scale_provenance_parent_stale")
    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise HorizontalSectionError("section_requires_captured_geometry_authority")
    if not geometry.points:
        raise HorizontalSectionError("section_geometry_empty")
    if len(geometry.points) > MAX_CAPTURED_POINTS:
        raise HorizontalSectionError("section_geometry_point_count_out_of_bounds")
    if not _finite(requested_z):
        raise HorizontalSectionError("section_requested_z_must_be_finite")
    if not _nonnegative_finite(slab_half_width):
        raise HorizontalSectionError("section_slab_half_width_must_be_finite_nonnegative")

    z_values = tuple(point[2] for point in geometry.points)
    z_min, z_max = min(z_values), max(z_values)
    if requested_z < z_min or requested_z > z_max:
        raise HorizontalSectionError("section_requested_z_out_of_range")
    allowed_half_width = min(
        MAX_SLAB_HALF_WIDTH,
        (z_max - z_min) * MAX_SLAB_FRACTION_OF_Z_EXTENT,
    )
    if slab_half_width > allowed_half_width:
        raise HorizontalSectionError("section_slab_half_width_exceeds_bound")

    points = tuple(
        sorted(
            (
                HorizontalSectionPoint(index, point, abs(point[2] - requested_z))
                for index, point in enumerate(geometry.points)
                if _within_slab(point[2], requested_z, slab_half_width)
            ),
            key=lambda item: (item.point[0], item.point[1], item.point[2], item.source_point_index),
        )
    )
    if not points:
        raise HorizontalSectionError("section_no_captured_points_in_slab")

    body: dict[str, object] = {
        "method_version": HORIZONTAL_SECTION_METHOD_VERSION,
        "source_geometry_id": geometry.source_geometry_id,
        "normalized_geometry_revision": geometry.normalized_geometry_revision,
        "scale_provenance_id": geometry.scale_provenance_id,
        "scale_state": geometry.scale_state.value,
        "coordinate_unit": geometry.coordinate_unit,
        "requested_z": requested_z,
        "z_range": [z_min, z_max],
        "slab_half_width": slab_half_width,
        "maximum_allowed_slab_half_width": allowed_half_width,
        "points": [[item.source_point_index, list(item.point), item.z_offset] for item in points],
    }
    section_id = (
        "horizontal-section:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return HorizontalSection(
        section_id,
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.scale_state,
        geometry.coordinate_unit,
        requested_z,
        (z_min, z_max),
        slab_half_width,
        allowed_half_width,
        points,
    )


def serialize_horizontal_section(section: HorizontalSection) -> bytes:
    return json.dumps(
        section.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _nonnegative_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0.0
    )


def _within_slab(point_z: float, requested_z: float, half_width: float) -> bool:
    offset = abs(point_z - requested_z)
    floating_boundary_tolerance = 8.0 * max(
        math.ulp(point_z), math.ulp(requested_z), math.ulp(half_width)
    )
    return offset <= half_width + floating_boundary_tolerance
