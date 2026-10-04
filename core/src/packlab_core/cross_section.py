"""Editable backend-neutral cross-sections with explicit symmetry constraints."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from .reconstruction import ScaleState

MAX_SECTION_POINTS = 4096
_EPSILON = 1e-9
_SECTION_PREFIX = "design-section:"


class CrossSectionError(ValueError):
    """Raised when a cross-section or edit violates the parametric contract."""


class CrossSectionSymmetry(StrEnum):
    NONE = "none"
    LEFT_RIGHT = "left-right"
    FRONT_BACK = "front-back"
    BOTH = "both"


@dataclass(frozen=True, slots=True)
class SectionPoint:
    x: float
    y: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.x) or not math.isfinite(self.y):
            raise CrossSectionError("section_coordinates_must_be_finite")


@dataclass(frozen=True, slots=True)
class CrossSection:
    section_id: str
    component_id: str
    points: tuple[SectionPoint, ...]
    symmetry: CrossSectionSymmetry
    center_x: float
    center_y: float
    scale_state: ScaleState
    coordinate_unit: str
    previous_section_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.component_id, str) or not self.component_id.strip():
            raise CrossSectionError("section_component_id_invalid")
        if not isinstance(self.points, tuple) or any(
            not isinstance(point, SectionPoint) for point in self.points
        ):
            raise CrossSectionError("section_points_must_be_immutable_tuple")
        if not 3 <= len(self.points) <= MAX_SECTION_POINTS:
            raise CrossSectionError("section_point_count_out_of_range")
        if not isinstance(self.symmetry, CrossSectionSymmetry):
            raise CrossSectionError("section_symmetry_invalid")
        if not math.isfinite(self.center_x) or not math.isfinite(self.center_y):
            raise CrossSectionError("section_center_must_be_finite")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise CrossSectionError("section_scale_state_unauthorized")
        unit = (
            "reconstruction_units" if self.scale_state is ScaleState.RELATIVE else "mm_unverified"
        )
        if self.coordinate_unit != unit:
            raise CrossSectionError("section_coordinate_unit_mismatch")
        _validate_polygon(self.points)
        _validate_symmetry(self.points, self.symmetry, self.center_x, self.center_y)
        if self.section_id != _section_id(
            self.component_id,
            self.points,
            self.symmetry,
            self.center_x,
            self.center_y,
            self.scale_state,
            self.coordinate_unit,
            self.previous_section_id,
        ):
            raise CrossSectionError("section_id_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.cross-section.v1",
            "section_id": self.section_id,
            "component_id": self.component_id,
            "points": [{"x": point.x, "y": point.y} for point in self.points],
            "symmetry": self.symmetry.value,
            "symmetry_axes": {
                "left_right_axis_x": self.center_x,
                "front_back_axis_y": self.center_y,
            },
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "previous_section_id": self.previous_section_id,
        }


def create_cross_section(
    component_id: str,
    points: tuple[SectionPoint, ...],
    *,
    symmetry: CrossSectionSymmetry = CrossSectionSymmetry.NONE,
    center_x: float = 0.0,
    center_y: float = 0.0,
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED,
    previous_section_id: str | None = None,
) -> CrossSection:
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    section_id = _section_id(
        component_id,
        points,
        symmetry,
        center_x,
        center_y,
        scale_state,
        unit,
        previous_section_id,
    )
    return CrossSection(
        section_id,
        component_id,
        points,
        symmetry,
        center_x,
        center_y,
        scale_state,
        unit,
        previous_section_id,
    )


def circle_section(
    component_id: str,
    radius: float,
    *,
    point_count: int = 32,
    center_x: float = 0.0,
    center_y: float = 0.0,
    symmetry: CrossSectionSymmetry = CrossSectionSymmetry.BOTH,
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED,
) -> CrossSection:
    return _ellipse_section(
        component_id,
        radius,
        radius,
        point_count=point_count,
        center_x=center_x,
        center_y=center_y,
        symmetry=symmetry,
        scale_state=scale_state,
    )


def ellipse_section(
    component_id: str,
    radius_x: float,
    radius_y: float,
    *,
    point_count: int = 32,
    center_x: float = 0.0,
    center_y: float = 0.0,
    symmetry: CrossSectionSymmetry = CrossSectionSymmetry.BOTH,
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED,
) -> CrossSection:
    return _ellipse_section(
        component_id,
        radius_x,
        radius_y,
        point_count=point_count,
        center_x=center_x,
        center_y=center_y,
        symmetry=symmetry,
        scale_state=scale_state,
    )


def edit_control_point(section: CrossSection, index: int, point: SectionPoint) -> CrossSection:
    """Edit one point and propagate its orbit under the declared symmetry constraint."""
    if not isinstance(section, CrossSection):
        raise CrossSectionError("section_required")
    if (
        isinstance(index, bool)
        or not isinstance(index, int)
        or not 0 <= index < len(section.points)
    ):
        raise CrossSectionError("section_point_index_invalid")
    if not isinstance(point, SectionPoint):
        raise CrossSectionError("section_point_invalid")
    old = section.points[index]
    mirrors = _mirrors(section.symmetry, section.center_x, section.center_y)
    replacements: dict[int, SectionPoint] = {index: point}
    for mirror in mirrors:
        expected = mirror(old)
        if _near(expected, old):
            continue
        matches = [
            target_index
            for target_index, candidate in enumerate(section.points)
            if _near(candidate, expected)
        ]
        if len(matches) != 1:
            raise CrossSectionError("section_symmetry_mirror_reference_ambiguous")
        replacements[matches[0]] = mirror(point)
    updated = tuple(replacements.get(i, existing) for i, existing in enumerate(section.points))
    return _rebuild(section, updated, section.symmetry)


def set_symmetry(section: CrossSection, symmetry: CrossSectionSymmetry) -> CrossSection:
    """Set a constraint without inventing coordinates; invalid activation is rejected."""
    if not isinstance(section, CrossSection):
        raise CrossSectionError("section_required")
    return _rebuild(section, section.points, symmetry)


def _ellipse_section(
    component_id: str,
    radius_x: float,
    radius_y: float,
    *,
    point_count: int,
    center_x: float,
    center_y: float,
    symmetry: CrossSectionSymmetry,
    scale_state: ScaleState,
) -> CrossSection:
    if not math.isfinite(radius_x) or not math.isfinite(radius_y) or radius_x <= 0 or radius_y <= 0:
        raise CrossSectionError("section_radii_must_be_positive")
    if isinstance(point_count, bool) or not isinstance(point_count, int):
        raise CrossSectionError("section_point_count_invalid")
    if not 8 <= point_count <= MAX_SECTION_POINTS or point_count % 4:
        raise CrossSectionError("ellipse_point_count_must_be_multiple_of_four")
    points = tuple(
        SectionPoint(
            center_x + radius_x * math.cos(2 * math.pi * index / point_count),
            center_y + radius_y * math.sin(2 * math.pi * index / point_count),
        )
        for index in range(point_count)
    )
    return create_cross_section(
        component_id,
        points,
        symmetry=symmetry,
        center_x=center_x,
        center_y=center_y,
        scale_state=scale_state,
    )


def _rebuild(
    section: CrossSection,
    points: tuple[SectionPoint, ...],
    symmetry: CrossSectionSymmetry,
) -> CrossSection:
    unit = section.coordinate_unit
    section_id = _section_id(
        section.component_id,
        points,
        symmetry,
        section.center_x,
        section.center_y,
        section.scale_state,
        unit,
        section.section_id,
    )
    return CrossSection(
        section_id,
        section.component_id,
        points,
        symmetry,
        section.center_x,
        section.center_y,
        section.scale_state,
        unit,
        section.section_id,
    )


def _section_id(
    component_id: str,
    points: tuple[SectionPoint, ...],
    symmetry: CrossSectionSymmetry,
    center_x: float,
    center_y: float,
    scale_state: ScaleState,
    coordinate_unit: str,
    previous_section_id: str | None,
) -> str:
    payload = {
        "contract": "packlab.cross-section.v1",
        "component_id": component_id,
        "points": [{"x": point.x, "y": point.y} for point in points],
        "symmetry": symmetry.value,
        "center_x": center_x,
        "center_y": center_y,
        "scale_state": scale_state.value,
        "coordinate_unit": coordinate_unit,
        "previous_section_id": previous_section_id,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return _SECTION_PREFIX + digest


def _mirrors(
    symmetry: CrossSectionSymmetry, center_x: float, center_y: float
) -> tuple[Callable[[SectionPoint], SectionPoint], ...]:
    def identity(point: SectionPoint) -> SectionPoint:
        return point

    def reflect_x(point: SectionPoint) -> SectionPoint:
        return SectionPoint(2 * center_x - point.x, point.y)

    def reflect_y(point: SectionPoint) -> SectionPoint:
        return SectionPoint(point.x, 2 * center_y - point.y)

    def reflect_both(point: SectionPoint) -> SectionPoint:
        return reflect_x(reflect_y(point))

    if symmetry is CrossSectionSymmetry.NONE:
        return (identity,)
    if symmetry is CrossSectionSymmetry.LEFT_RIGHT:
        return (identity, reflect_x)
    if symmetry is CrossSectionSymmetry.FRONT_BACK:
        return (identity, reflect_y)
    return (identity, reflect_x, reflect_y, reflect_both)


def _validate_symmetry(
    points: tuple[SectionPoint, ...],
    symmetry: CrossSectionSymmetry,
    center_x: float,
    center_y: float,
) -> None:
    for mirror in _mirrors(symmetry, center_x, center_y)[1:]:
        for point in points:
            if not any(_near(candidate, mirror(point)) for candidate in points):
                raise CrossSectionError("section_symmetry_constraint_not_satisfied")


def _validate_polygon(points: tuple[SectionPoint, ...]) -> None:
    for left, right in zip(points, (*points[1:], points[0])):
        if _near(left, right):
            raise CrossSectionError("section_duplicate_or_degenerate_edge")
    area2 = sum(
        left.x * right.y - right.x * left.y for left, right in zip(points, (*points[1:], points[0]))
    )
    if abs(area2) <= _EPSILON:
        raise CrossSectionError("section_area_degenerate")
    count = len(points)
    for first in range(count):
        a, b = points[first], points[(first + 1) % count]
        for second in range(first + 1, count):
            if second in {first, (first + 1) % count} or (second + 1) % count == first:
                continue
            c, d = points[second], points[(second + 1) % count]
            if _segments_intersect(a, b, c, d):
                raise CrossSectionError("section_self_intersection")


def _segments_intersect(a: SectionPoint, b: SectionPoint, c: SectionPoint, d: SectionPoint) -> bool:
    def orientation(p: SectionPoint, q: SectionPoint, r: SectionPoint) -> float:
        return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)

    def on_segment(p: SectionPoint, q: SectionPoint, r: SectionPoint) -> bool:
        return (
            min(p.x, r.x) - _EPSILON <= q.x <= max(p.x, r.x) + _EPSILON
            and min(p.y, r.y) - _EPSILON <= q.y <= max(p.y, r.y) + _EPSILON
        )

    o1, o2, o3, o4 = (
        orientation(a, b, c),
        orientation(a, b, d),
        orientation(c, d, a),
        orientation(c, d, b),
    )
    if (o1 > _EPSILON and o2 < -_EPSILON or o1 < -_EPSILON and o2 > _EPSILON) and (
        o3 > _EPSILON and o4 < -_EPSILON or o3 < -_EPSILON and o4 > _EPSILON
    ):
        return True
    return (
        abs(o1) <= _EPSILON
        and on_segment(a, c, b)
        or abs(o2) <= _EPSILON
        and on_segment(a, d, b)
        or abs(o3) <= _EPSILON
        and on_segment(c, a, d)
        or abs(o4) <= _EPSILON
        and on_segment(c, b, d)
    )


def _near(left: SectionPoint, right: SectionPoint) -> bool:
    return math.hypot(left.x - right.x, left.y - right.y) <= _EPSILON


__all__ = [
    "CrossSection",
    "CrossSectionError",
    "CrossSectionSymmetry",
    "SectionPoint",
    "circle_section",
    "create_cross_section",
    "edit_control_point",
    "ellipse_section",
    "set_symmetry",
]
