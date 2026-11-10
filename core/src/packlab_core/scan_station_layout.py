"""Geometric dry-run of a proposed scan-station layout (PL-0396/PL-0397).

Station frame (PL-0397): origin at the turntable axis on the tabletop, +y toward
the camera's initial front position, +z up, millimetres. Checks are pinhole
geometry only: they do not model flare, bounce light, lens distortion or any
physical station, so a clean result is a planning check, not physical acceptance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Point = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class CameraFov:
    name: str
    horizontal_deg: float
    vertical_deg: float


def fov_from_35mm_equivalent(name: str, focal_mm: float, aspect: tuple[int, int], portrait: bool) -> CameraFov:
    """FOV for a 35 mm-equivalent focal length on a frame of the given aspect."""
    diag = math.hypot(36.0, 24.0)
    long_mm = diag * aspect[0] / math.hypot(*aspect)
    short_mm = diag * aspect[1] / math.hypot(*aspect)
    long_deg = math.degrees(2 * math.atan(long_mm / 2 / focal_mm))
    short_deg = math.degrees(2 * math.atan(short_mm / 2 / focal_mm))
    return CameraFov(name, short_deg, long_deg) if portrait else CameraFov(name, long_deg, short_deg)


@dataclass(frozen=True, slots=True)
class LightFixture:
    name: str
    emitting_points: tuple[Point, ...]
    stand_foot_xy: tuple[float, float]


@dataclass(frozen=True, slots=True)
class StationLayout:
    camera_distance_mm: float
    camera_heights_mm: tuple[float, ...]
    camera_azimuths_deg: tuple[float, ...]
    aim_height_mm: float
    envelope_diagonal_mm: float
    envelope_height_mm: float
    lights: tuple[LightFixture, ...]


def _sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _unit(a: Point) -> Point:
    n = math.sqrt(_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)


def _cross(a: Point, b: Point) -> Point:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def camera_position(layout: StationLayout, azimuth_deg: float, height_mm: float) -> Point:
    a = math.radians(azimuth_deg)
    return (layout.camera_distance_mm * math.sin(a), layout.camera_distance_mm * math.cos(a), height_mm)


def view_angles_deg(camera: Point, target: Point, point: Point) -> tuple[float, float, float]:
    """(horizontal, vertical) angle of `point` from the optical axis, plus forward depth."""
    forward = _unit(_sub(target, camera))
    right = _unit(_cross(forward, (0.0, 0.0, 1.0)))
    up = _cross(right, forward)
    rel = _sub(point, camera)
    depth = _dot(rel, forward)
    return (
        math.degrees(math.atan2(_dot(rel, right), depth)),
        math.degrees(math.atan2(_dot(rel, up), depth)),
        depth,
    )


def _envelope_points(layout: StationLayout) -> list[Point]:
    radius = layout.envelope_diagonal_mm / 2
    return [
        (radius * math.cos(math.radians(k * 15)), radius * math.sin(math.radians(k * 15)), z)
        for k in range(24)
        for z in (0.0, layout.envelope_height_mm)
    ]


def layout_issues(
    layout: StationLayout,
    fov: CameraFov,
    *,
    frame_fill_limit: float = 0.9,
    min_stand_clearance_mm: float = 300.0,
) -> list[str]:
    """Return human-readable violations; an empty list means the dry-run passed."""
    issues: list[str] = []
    half_h, half_v = fov.horizontal_deg / 2, fov.vertical_deg / 2
    target = (0.0, 0.0, layout.aim_height_mm)
    envelope = _envelope_points(layout)
    for height in layout.camera_heights_mm:
        for azimuth in layout.camera_azimuths_deg:
            cam = camera_position(layout, azimuth, height)
            pose = f"camera az={azimuth:g} h={height:g} ({fov.name})"
            worst = max(
                max(abs(h) / half_h, abs(v) / half_v)
                for h, v, _ in (view_angles_deg(cam, target, p) for p in envelope)
            )
            if worst > frame_fill_limit:
                issues.append(f"{pose}: envelope fills {worst:.2f} of half-FOV (> {frame_fill_limit})")
            for light in layout.lights:
                for point in light.emitting_points:
                    h, v, depth = view_angles_deg(cam, target, point)
                    if depth > 0 and abs(h) <= half_h and abs(v) <= half_v:
                        issues.append(f"{pose}: {light.name} emitting surface in frame at ({h:.1f}, {v:.1f}) deg")
                        break
            for light in layout.lights:
                gap = math.dist(cam[:2], light.stand_foot_xy)
                if gap < min_stand_clearance_mm:
                    issues.append(f"{pose}: {light.name} stand foot {gap:.0f} mm from camera (< {min_stand_clearance_mm:g})")
    return issues


def panel(name: str, center: Point, size_mm: float, stand_foot_xy: tuple[float, float]) -> LightFixture:
    """Horizontal square emitting panel (corners and centre) facing down."""
    s = size_mm / 2
    cx, cy, cz = center
    points = ((cx, cy, cz),) + tuple((cx + dx, cy + dy, cz) for dx in (-s, s) for dy in (-s, s))
    return LightFixture(name, points, stand_foot_xy)


def _polar(radius: float, azimuth_deg: float) -> tuple[float, float]:
    a = math.radians(azimuth_deg)
    return (radius * math.sin(a), radius * math.cos(a))


IPHONE_16_MAIN_PORTRAIT = fov_from_35mm_equivalent("iPhone 16 main 26mm-eq portrait", 26.0, (4, 3), True)
IPHONE_16_MAIN_LANDSCAPE = fov_from_35mm_equivalent("iPhone 16 main 26mm-eq landscape", 26.0, (4, 3), False)


def pl0397_v01_layout() -> StationLayout:
    """Original PL-0397 proposal: vertical panels at +/-45 deg, 800 mm radius, 650 mm high."""

    def side_panel(name: str, azimuth: float) -> LightFixture:
        x, y = _polar(800.0, azimuth)
        # Vertical 300 mm panel facing the axis; emitting face sampled at centre/edges.
        tx, ty = _polar(150.0, azimuth + 90.0)
        pts = tuple((x + sx * tx, y + sx * ty, 650.0 + dz) for sx in (-1.0, 0.0, 1.0) for dz in (-150.0, 0.0, 150.0))
        return LightFixture(name, pts, (x, y))

    return StationLayout(800.0, (120.0, 200.0, 320.0), tuple(float(a) for a in range(0, 360, 30)), 200.0,
                         250.0, 400.0, (side_panel("left panel", -45.0), side_panel("right panel", 45.0)))


def pl0397_v02_layout() -> StationLayout:
    """Revised proposal: overhead boom-arm panels, emitting faces above the camera frustum."""
    lights = tuple(
        panel(name, (*_polar(300.0, az), 1300.0), 300.0, _polar(1100.0, az))
        for name, az in (("left overhead panel", -90.0), ("right overhead panel", 90.0))
    )
    return StationLayout(800.0, (120.0, 200.0, 320.0), tuple(float(a) for a in range(0, 360, 30)), 200.0,
                         250.0, 400.0, lights)
