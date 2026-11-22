"""Merge a body-interior scan into the Body part via the rim / opening (PL-0489).

Inputs are the Body (combined or single scan) and the body-interior scan (lid off, steep 60/70/80
degree rings looking into the opening), each as object points in its own A4-mat frame (mm, +z up
from the mat), e.g. ``part_placement.part_from_scan``. Both stand upright on the mat.

* Reachability first (body only): photos see into the opening down to about
  ``opening x tan(second-steepest ring elevation)`` (a wall point needs two rings to
  triangulate). Too small an opening, too deep a body or a shoulder much wider than the opening
  -> typed refusal ``interior_not_reachable``: use the PL-0488 derived interior instead.
* Rim: top band (thickness from the point spacing) of each cloud, algebraic circle fit; a ring
  with too few azimuth sectors or a poor fit is ``rim_not_found``. Diameter / height differences
  beyond tolerance are ``rim_mismatch`` (wrong body, wrong scale or lid still on).
* Pose (5 DoF, height from the shared mat contact): tilt from the two rim planes, xy from the
  rim centres, yaw sweep on the rim band (flagged ``yaw_determined=False`` on a round rim, where
  yaw is arbitrary), bounded point-to-plane ICP over tilt + yaw + xy on the rim band (reuses the
  PL-0483 solver). Refinement past ``max_refine_*`` or too little rim overlap is
  ``insufficient_overlap``; so is an interior scan that shows nothing below the rim.
* Interior points = aligned interior-scan points below the rim band and inside the Body's outer
  wall (per 2 mm x 10 degree cell, minus a wall tolerance). Only they are added; nothing is
  filled. Coverage per depth band below the rim = share of 10 degree azimuth sectors holding
  interior points; the deepest reliably covered depth is the bottom of the contiguous run of
  covered bands from the rim down; every band below it is reported missing.

Deterministic. Metric values stay METRIC_UNVERIFIED; tests use synthetic proxies only.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .multiscan_alignment import (
    AlignmentThresholds,
    MultiScanAlignmentError,
    _about,
    _adapt,
    _angle_deg,
    _apply,
    _icp,
    _nearest,
    _normals,
    _Part,
    _rodrigues,
    _shell,
    _spacing,
    _top,
    _yaw,
)
from .part_placement import PartInput

METHOD = "rim_circle_tilt_xy_yaw_sweep_bounded_icp_mat_height_v1"
METRIC_STATUS = "METRIC_UNVERIFIED"
SECTORS = 36  # 10 degree azimuth sectors
FALLBACK = "PL-0488 derived interior"


class InteriorMergeError(ValueError):
    """Merge refused; ``codes`` names every failed check (message has the details)."""

    def __init__(self, message: str, codes: tuple[str, ...]) -> None:
        super().__init__(message)
        self.codes = codes


@dataclass(frozen=True)
class InteriorThresholds:
    band_mm: float = 2.0  # depth band height for coverage
    min_band_coverage: float = 0.75  # sector share for a band to count as covered
    rim_band_mm: float = 2.0  # top band holding the rim (at least 2 point spacings)
    min_rim_sectors: float = 0.75
    max_rim_rms_mm: float = 1.5  # circle fit residual (plus half a spacing)
    diameter_tolerance_mm: float = 1.5
    height_tolerance_mm: float = 1.5
    dimension_tolerance_ratio: float = 0.02
    min_rim_overlap: float = 0.6  # interior rim-band points with a body point near
    wall_tolerance_mm: float = 1.0  # interior = inside the outer wall by at least this
    ring_elevation_deg: float = 70.0  # second-steepest capture ring (60/70/80)
    min_opening_mm: float = 25.0  # phone camera cannot look into a smaller opening
    max_shoulder_ratio: float = 1.5  # widest body diameter / opening
    max_refine_deg: float = 5.0
    max_refine_mm: float = 5.0


@dataclass(frozen=True)
class Reachability:
    opening_mm: float  # rim circle diameter (mid wall)
    depth_mm: float  # rim height above the mat (inner floor not known before scanning)
    reachable_depth_mm: float
    widest_mm: float  # widest body diameter below the rim
    reachable: bool
    reason: str


@dataclass(frozen=True)
class DepthBand:
    top_mm: float  # depth below the rim
    bottom_mm: float
    coverage: float  # share of azimuth sectors holding interior points
    points: int


@dataclass(frozen=True)
class InteriorMerge:
    body_id: str
    interior_id: str
    matrix: np.ndarray  # 4x4 rigid: interior scan mat frame mm -> body mat frame mm
    rim: dict[str, float]  # body/interior diameter and height, fit rms, mm
    rim_overlap: float
    rmse_mm: float
    yaw_determined: bool
    reachability: Reachability
    bands: tuple[DepthBand, ...]
    deepest_covered_mm: float  # contiguous covered depth below the rim
    missing: tuple[tuple[float, float], ...]  # (top, bottom) depth of every uncovered band
    points: np.ndarray  # body points then interior points, body mat frame mm
    colors: np.ndarray | None
    source_ids: tuple[str, str]  # (body, interior)
    source_index: np.ndarray  # per point: index into source_ids
    point_index: np.ndarray  # per point: row in that source's input points
    method: str = METHOD
    metric_status: str = METRIC_STATUS
    interior_provenance: str = "SCANNED_PARTIAL_DEPTH"  # never filled below the covered depth


def _checked(item: PartInput | None, role: str) -> np.ndarray:
    if item is None:
        raise InteriorMergeError(f"{role} missing", ("part_missing",))
    points = np.asarray(item.points, dtype=float)
    if points.ndim != 2 or points.shape[1:] != (3,) or len(points) < 100:
        raise InteriorMergeError(f"{role} needs (N>=100, 3) points", ("part_unusable",))
    if not np.isfinite(points).all():
        raise InteriorMergeError(f"{role} has non-finite points", ("part_unusable",))
    return points


def _sector(rel: np.ndarray) -> np.ndarray:
    angle = np.arctan2(rel[:, 1], rel[:, 0]) + np.pi
    return np.asarray((angle / (2 * np.pi) * SECTORS).astype(int) % SECTORS)


@dataclass(frozen=True)
class _Rim:
    centre: np.ndarray  # (3,) circle centre at rim height
    radius: float
    height: float
    normal: np.ndarray
    rms: float
    band: float


def _rim(points: np.ndarray, spacing: float, t: InteriorThresholds, role: str) -> _Rim:
    height = _top(points[:, 2])
    band = max(t.rim_band_mm, 2.0 * spacing)
    ring = points[points[:, 2] > height - band]
    if len(ring) < 30:
        raise InteriorMergeError(f"{role}: rim not found (too few top points)", ("rim_not_found",))
    # The rim's top face only: the outer scan also sees the outer wall top, the interior scan
    # the inner wall top, which would bias the two circle fits apart.
    face = ring[np.abs(_normals(ring)[:, 2]) > 0.7]
    ring = face if len(face) >= 30 else ring
    x, y = ring[:, 0], ring[:, 1]
    # Kasa fit: x^2 + y^2 = 2 a x + 2 b y + c. ponytail: circle only; oval rims get a larger
    # rms (upgrade: direct ellipse fit if oval jars must merge).
    solution = np.linalg.lstsq(np.c_[2 * x, 2 * y, np.ones(len(x))], x * x + y * y, rcond=None)
    a, b, c = solution[0]
    radius = float(np.sqrt(max(c + a * a + b * b, 0.0)))
    rel = ring[:, :2] - [a, b]
    rms = float(np.sqrt(np.mean((np.linalg.norm(rel, axis=1) - radius) ** 2)))
    sectors = len(np.unique(_sector(rel))) / SECTORS
    if radius <= 0 or sectors < t.min_rim_sectors or rms > t.max_rim_rms_mm + 0.5 * spacing:
        raise InteriorMergeError(
            f"{role}: rim not found (ring covers {sectors:.0%} of the azimuth, circle fit rms "
            f"{rms:.1f} mm): is the top an open rim seen all round?",
            ("rim_not_found",),
        )
    centroid = ring.mean(axis=0)
    normal = np.linalg.svd(ring - centroid, full_matrices=False)[2][2]
    normal = normal if normal[2] > 0 else -normal
    return _Rim(np.array([a, b, height]), radius, height, normal, rms, band)


def reachability(body: PartInput, t: InteriorThresholds = InteriorThresholds()) -> Reachability:
    """Can photos from the capture rings reach the body's interior through its opening?"""

    points = _checked(body, "body")
    rim = _rim(points, _spacing(points, 1.0)[0], t, "body")
    opening = 2 * rim.radius
    below = points[points[:, 2] < rim.height - rim.band]
    radial = np.linalg.norm(below[:, :2] - rim.centre[:2], axis=1)
    widest = 2 * float(np.percentile(radial, 98)) if len(below) else opening
    reach = opening * float(np.tan(np.radians(t.ring_elevation_deg)))
    problems = []
    if opening < t.min_opening_mm:
        problems.append(f"opening {opening:.0f} mm < {t.min_opening_mm:.0f} mm")
    if reach < rim.height:
        problems.append(f"photos reach about {reach:.0f} mm of {rim.height:.0f} mm depth")
    if widest > t.max_shoulder_ratio * opening:
        problems.append(f"body {widest:.0f} mm wide behind a {opening:.0f} mm opening")
    reason = ""
    if problems:
        reason = (
            "interior not reachable by photos (" + "; ".join(problems) + f") - use the {FALLBACK}"
        )
    return Reachability(opening, rim.height, reach, widest, not problems, reason)


def _outer_radius(body: np.ndarray, rim: _Rim, spacing: float, band: float) -> np.ndarray:
    """(height band x sector) median radius of the body's outer wall, nan where unseen."""

    limits = replace(AlignmentThresholds(), spacing_mm=spacing)
    try:
        shell = _shell(body, rim.height, spacing, limits)[0]
    except MultiScanAlignmentError as error:
        raise InteriorMergeError(f"body: {error}", ("part_unusable",)) from None
    rel = shell[:, :2] - rim.centre[:2]
    rows = int(np.ceil(rim.height / band)) + 1
    level = np.clip((shell[:, 2] / band).astype(int), 0, rows - 1)
    cell = level * SECTORS + _sector(rel)
    radius = np.linalg.norm(rel, axis=1)
    flat = np.full(rows * SECTORS, np.nan)
    for key in np.unique(cell):
        flat[key] = np.median(radius[cell == key])
    table = flat.reshape(rows, SECTORS)
    seen = np.nonzero(~np.isnan(table).all(axis=1))[0]
    if len(seen):  # floor / rim heights the shell band skips: nearest seen height band
        table[: seen[0]] = table[seen[0]]
        table[seen[-1] + 1 :] = table[seen[-1]]
    return table


def merge_interior(
    body: PartInput | None,
    interior: PartInput | None,
    t: InteriorThresholds = InteriorThresholds(),
) -> InteriorMerge:
    """Align the interior scan to the body by the rim and add its interior points."""

    b_pts, i_pts = _checked(body, "body"), _checked(interior, "body interior")
    assert body is not None and interior is not None
    reach = reachability(body, t)
    if not reach.reachable:
        raise InteriorMergeError(reach.reason, ("interior_not_reachable",))
    spacing = max(_spacing(b_pts, 1.0)[0], _spacing(i_pts, 1.0)[0])
    b_rim, i_rim = _rim(b_pts, spacing, t, "body"), _rim(i_pts, spacing, t, "body interior")
    failures = []
    d_tol = max(t.diameter_tolerance_mm, t.dimension_tolerance_ratio * 2 * b_rim.radius)
    d_tol += 0.5 * spacing
    if abs(b_rim.radius - i_rim.radius) * 2 > d_tol:
        failures.append(
            f"rim diameter {2 * i_rim.radius:.1f} vs body {2 * b_rim.radius:.1f} mm "
            f"(tolerance {d_tol:.1f})"
        )
    h_tol = max(t.height_tolerance_mm, t.dimension_tolerance_ratio * b_rim.height)
    h_tol += 0.5 * spacing
    if abs(b_rim.height - i_rim.height) > h_tol:
        failures.append(
            f"rim height {i_rim.height:.1f} vs body {b_rim.height:.1f} mm (tolerance {h_tol:.1f})"
        )
    if failures:
        raise InteriorMergeError(
            "interior merge refused: " + "; ".join(failures) + " - wrong body, scale or lid on",
            ("rim_mismatch",),
        )

    # Initial pose: tilt interior rim plane onto the body's, then rim centre onto rim centre
    # (height from the mat contact: both stand on the mat).
    axis = np.cross(i_rim.normal, b_rim.normal)
    angle = float(np.arcsin(np.clip(np.linalg.norm(axis), -1, 1)))
    tilt = _rodrigues(axis / np.linalg.norm(axis) * angle) if angle > 1e-9 else np.eye(3)
    start = _about(tilt, i_rim.centre, np.r_[b_rim.centre[:2] - i_rim.centre[:2], 0.0])
    window = 3 * b_rim.band
    target = b_pts[b_pts[:, 2] > b_rim.height - window]
    source = i_pts[i_pts[:, 2] > i_rim.height - window]
    query = _nearest(target)
    pivot = np.r_[b_rim.centre[:2], 0.0]
    scores = []
    for step in range(SECTORS):
        trial = _yaw(2 * np.pi * step / SECTORS, pivot) @ start
        scores.append(float(np.median(query(_apply(trial, source))[1][:, 0])))
    spread = max(scores) - min(scores)
    determined = bool(spread > max(0.5, spacing))
    yaw = int(np.argmin(scores)) if determined else 0
    start = _yaw(2 * np.pi * yaw / SECTORS, pivot) @ start
    limits = _adapt(AlignmentThresholds(), spacing)
    part = _Part("body", np.eye(4), b_pts, np.arange(len(b_pts)), b_rim.height, target,
                 _normals(target), spacing)  # fmt: skip
    refined = _icp(source, part, query, start, [0, 1, 2, 3, 4], limits, 3 * limits.max_distance_mm, 1e-2)  # fmt: skip
    delta = refined @ np.linalg.inv(start)
    moved_rim = _apply(delta, b_rim.centre[None])[0]
    if (
        _angle_deg(delta[:3, :3]) > t.max_refine_deg
        or np.linalg.norm(moved_rim - b_rim.centre) > t.max_refine_mm
    ):
        raise InteriorMergeError(
            "interior merge refused: rim refinement left its bounds (rim surfaces do not match)",
            ("insufficient_overlap",),
        )
    distance = query(_apply(refined, source))[1][:, 0]
    near = distance < limits.max_distance_mm
    overlap = float(near.mean())
    rmse = float(np.sqrt(np.mean(distance[near] ** 2))) if near.any() else float("inf")
    if overlap < t.min_rim_overlap:
        raise InteriorMergeError(
            f"interior merge refused: rim overlap {overlap:.0%} < {t.min_rim_overlap:.0%}",
            ("insufficient_overlap",),
        )

    moved = _apply(refined, i_pts)
    rel = moved[:, :2] - b_rim.centre[:2]
    band = t.band_mm
    table = _outer_radius(b_pts, b_rim, spacing, band)
    level = np.clip((moved[:, 2] / band).astype(int), 0, len(table) - 1)
    outer = table[level, _sector(rel)]
    wall = max(t.wall_tolerance_mm, 1.5 * spacing)
    inside = np.linalg.norm(rel, axis=1) < np.nan_to_num(outer, nan=-np.inf) - wall
    is_interior = inside & (moved[:, 2] < b_rim.height - b_rim.band) & (moved[:, 2] > 0)
    if is_interior.sum() < 30:
        raise InteriorMergeError(
            "interior merge refused: the interior scan shows no surface below the rim",
            ("insufficient_overlap",),
        )
    depth = b_rim.height - moved[is_interior, 2]
    sectors = _sector(rel[is_interior])
    bands, deepest, run = [], 0.0, True
    top = b_rim.band
    while top < b_rim.height:
        bottom = min(top + band, b_rim.height)
        hit = (depth >= top) & (depth < bottom)
        coverage = len(np.unique(sectors[hit])) / SECTORS
        bands.append(DepthBand(float(top), float(bottom), coverage, int(hit.sum())))
        run = run and coverage >= t.min_band_coverage
        # a partly reached band counts as covered, but only down to its deepest point
        deepest = float(min(bottom, depth[hit].max())) if run else deepest
        top = bottom
    missing = tuple(
        (item.top_mm, item.bottom_mm) for item in bands if item.coverage < t.min_band_coverage
    )
    index = np.nonzero(is_interior)[0]
    colors = None
    if body.colors is not None and interior.colors is not None:
        colors = np.r_[np.asarray(body.colors), np.asarray(interior.colors)[index]]
    return InteriorMerge(
        body.part_id,
        interior.part_id,
        refined,
        {
            "body_diameter_mm": 2 * b_rim.radius,
            "interior_diameter_mm": 2 * i_rim.radius,
            "body_height_mm": b_rim.height,
            "interior_height_mm": i_rim.height,
            "body_fit_rms_mm": b_rim.rms,
            "interior_fit_rms_mm": i_rim.rms,
        },
        overlap,
        rmse,
        determined,
        reach,
        tuple(bands),
        deepest,
        missing,
        np.r_[b_pts, moved[index]],
        colors,
        (body.part_id, interior.part_id),
        np.r_[np.zeros(len(b_pts), int), np.ones(len(index), int)],
        np.r_[np.arange(len(b_pts)), index],
    )


__all__ = [
    "METHOD",
    "METRIC_STATUS",
    "DepthBand",
    "InteriorMerge",
    "InteriorMergeError",
    "InteriorThresholds",
    "Reachability",
    "merge_interior",
    "reachability",
]
