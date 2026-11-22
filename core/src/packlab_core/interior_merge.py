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
* Pose: height from the rim (difference within tolerance, kept as ``height_offset_mm``), tilt
  from the two rim planes, xy from the rim centres, yaw sweep on the rim band (flagged
  ``yaw_determined=False`` on a round rim, where yaw is arbitrary), then bounded point-to-plane
  ICP over tilt + yaw + xy (5 DoF) on the rim band (reuses the PL-0483 solver). Refinement past
  ``max_refine_*`` or too little rim overlap is ``insufficient_overlap``; so is an interior scan
  that shows nothing below the rim.
* Wall: the interior scan's wall-like points (horizontal normals) measured inward from the
  Body's outer wall (per 2 mm x 10 degree cell) give the wall thickness; points beyond half of
  it (never below the measured wall noise) are interior, so 0.5-2.5 mm walls separate without a
  fixed margin. Walls far outside the body, too thick or departing from the body outline by depth
  are ``interior_profile_mismatch`` (different jar). Interior points need local surface support
  (floaters are dropped). Only they are added; nothing is filled.
* Coverage per depth band below the rim = share of 10 degree sectors holding a density-aware
  minimum of points. Deepest covered depth = end of the run of covered bands from the rim,
  tolerating gaps up to ``max_gap_mm`` (still listed missing). A scanned inner floor ends the
  run; bands below it are ``base`` (wall under the floor), not missing.

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
    max_gap_mm: float = 2.0  # uncovered depth tolerated inside the covered run (stays missing)
    min_support: int = 4  # neighbours within max(2 mm, 4 spacings) for a surface point
    max_wall_mm: float = 4.0  # thicker "wall" (and > max_wall_ratio x rim radius): foreign
    max_wall_ratio: float = 0.08
    max_floaters: int = 1000  # isolated points below the rim before "too noisy" (and share)
    max_floater_share: float = 0.1
    wall_variation_mm: float = 2.0  # per depth band, around the median wall
    max_outside_share: float = 0.25
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
    coverage: float  # share of azimuth sectors holding enough interior points
    points: int
    kind: str  # covered / missing / base (below the inner floor)


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
    wall_mm: float = float("nan")  # median interior wall inside the body's outer wall
    wall_noise_mm: float = float("nan")  # robust sigma of the body's outer wall radius
    floor_depth_mm: float | None = None  # inner floor depth below the rim, when scanned
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
    centre = np.median(ring[:, :2], axis=0)
    if len(face) >= 30 and len(np.unique(_sector(face[:, :2] - centre))) >= 0.9 * SECTORS:
        ring = face  # thin rims: too few face points all round, keep the whole top band
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


def _outer_radius(
    body: np.ndarray, rim: _Rim, spacing: float, band: float
) -> tuple[np.ndarray, float]:
    """(height band x sector) median radius of the body's outer wall (nan where unseen) and the
    robust sigma of the wall points about it (mm)."""

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
    noise = max(0.05, 1.4826 * float(np.median(np.abs(radius - flat[cell]))))
    table = flat.reshape(rows, SECTORS)
    seen = np.nonzero(~np.isnan(table).all(axis=1))[0]
    if len(seen):  # floor / rim heights the shell band skips: nearest seen height band
        table[: seen[0]] = table[seen[0]]
        table[seen[-1] + 1 :] = table[seen[-1]]
    return table, noise


def _two_walls(
    gap: np.ndarray, body_noise: float, limit: float
) -> tuple[float, float, float] | None:
    """(wall, split, noise) from the gaps of the interior scan's wall points (mm inward from the
    body's outer wall): 1-D two-Gaussian EM, outer wall near 0 and inner wall at the thickness.
    One cluster only: inner wall when clearly off the outer wall, else None (no interior)."""

    g = gap[(gap > -2.0) & (gap < limit)]
    if len(g) < 30:
        return None
    mu = np.array([0.0, max(float(np.percentile(g, 90)), 3 * body_noise)])
    sd = np.full(2, max(body_noise, 0.05))
    weight = np.full(2, 0.5)
    for _ in range(60):
        density = weight * np.exp(-0.5 * ((g[:, None] - mu) / sd) ** 2) / sd + 1e-300
        share = density / density.sum(axis=1, keepdims=True)
        count = share.sum(axis=0) + 1e-9
        weight, mu = count / len(g), (share * g[:, None]).sum(axis=0) / count
        sd = np.sqrt((share * (g[:, None] - mu) ** 2).sum(axis=0) / count).clip(0.05)
    noise = float(sd.max())
    # Ashman's D > 2: two clusters, split where both are equally many sigmas away.
    if count[1] >= 30 and count[0] >= 10 and mu[1] - mu[0] > np.sqrt(2 * (sd**2).sum()):
        return float(mu[1]), float(mu[0] + (mu[1] - mu[0]) * sd[0] / sd.sum()), noise
    middle = float(np.median(g))
    spread = max(1.4826 * float(np.median(np.abs(g - middle))), body_noise, 0.05)
    if middle > 2 * spread and len(g) >= 30:  # only the inner wall was seen
        return middle, middle / 2, spread
    return None


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

    # Initial pose: rim centre onto rim centre, tilt from the levelled mat frames (a large plane
    # beats a narrow rim); height from the rim (difference already within tolerance, kept as
    # height_offset_mm): the rim is what both scans see best, so depth bands start alike.
    start = _about(np.eye(3), i_rim.centre, b_rim.centre - i_rim.centre)
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

    def fit(matrix: np.ndarray) -> tuple[float, float]:
        distance = query(_apply(matrix, source))[1][:, 0]
        near = distance < limits.max_distance_mm
        rmse = float(np.sqrt(np.mean(distance[near] ** 2))) if near.any() else float("inf")
        return float(near.mean()), rmse

    refined = _icp(source, part, query, start, [2, 3, 4], limits, 3 * limits.max_distance_mm, 1e-9)  # fmt: skip
    # Tilt (5 DoF) only within bounds and when it clearly fits the rim better: a narrow rim
    # barely constrains tilt (as in multiscan_alignment).
    tilted = _icp(source, part, query, refined, [0, 1, 2, 3, 4], limits, limits.max_distance_mm, 1e-2)  # fmt: skip
    turn = tilted @ np.linalg.inv(refined)
    if _angle_deg(turn[:3, :3]) <= t.max_refine_deg and fit(tilted)[1] <= 0.9 * fit(refined)[1]:
        refined = tilted
    delta = refined @ np.linalg.inv(start)
    moved_rim = _apply(delta, b_rim.centre[None])[0]
    if (
        _angle_deg(delta[:3, :3]) > t.max_refine_deg + (180 if not determined else 0)
        or np.linalg.norm(moved_rim - b_rim.centre) > t.max_refine_mm
    ):
        raise InteriorMergeError(
            "interior merge refused: rim refinement left its bounds (rim surfaces do not match)",
            ("insufficient_overlap",),
        )
    overlap, rmse = fit(refined)
    if overlap < t.min_rim_overlap:
        raise InteriorMergeError(
            f"interior merge refused: rim overlap {overlap:.0%} < {t.min_rim_overlap:.0%}",
            ("insufficient_overlap",),
        )

    moved = _apply(refined, i_pts)
    rel = moved[:, :2] - b_rim.centre[:2]
    radius = np.linalg.norm(rel, axis=1)
    band = t.band_mm
    table, noise = _outer_radius(b_pts, b_rim, spacing, band)
    level = np.clip((moved[:, 2] / band).astype(int), 0, len(table) - 1)
    gap = table[level, _sector(rel)] - radius  # inward distance from the outer wall, nan unseen
    below = np.nonzero(
        (moved[:, 2] < b_rim.height - b_rim.band) & (moved[:, 2] > 0) & np.isfinite(gap)
    )[0]
    # Surface support first: floaters (isolated points) are never written as interior, and a
    # scan that is mostly floaters is refused as too noisy.
    support = max(2.0, 4.0 * spacing)
    if len(below) > t.min_support:
        kth = _nearest(moved[below])(moved[below], t.min_support + 1)[1][:, -1]
        dropped = int((kth >= support).sum())
        if dropped > max(t.max_floaters, t.max_floater_share * len(below)):
            raise InteriorMergeError(
                f"interior merge refused: {dropped} isolated points (floaters) below the rim - "
                "too noisy; light the inside evenly and rescan",
                ("too_noisy",),
            )
        below = below[kth < support]
    nz = np.ones(len(moved))
    if len(below) >= 10:
        nz[below] = np.abs(_normals(moved[below])[:, 2])
    in_below = np.zeros(len(moved), bool)
    in_below[below] = True
    wallish = in_below & (nz < 0.5)
    # Wall thickness from the data: the interior scan's inner wall sits ``wall`` inside the
    # body's outer wall, any outer wall it also saw sits near 0 (two-cluster fit), so 0.5-2.5 mm
    # walls separate without a fixed margin.
    walls = _two_walls(gap[wallish], noise, 0.5 * b_rim.radius)
    if walls is None:
        raise InteriorMergeError(
            "interior merge refused: the interior scan shows no wall surface below the rim",
            ("insufficient_overlap",),
        )
    wall, split, noise = walls
    inner = wallish & (gap > split)
    outside = wallish & (gap < -max(1.0, 3 * noise, spacing))
    bound = max(t.max_wall_mm, t.max_wall_ratio * b_rim.radius)
    implausible = []
    if wall > bound:
        implausible.append(f"wall {wall:.1f} mm > {bound:.1f} mm")
    if outside.sum() > max(30, t.max_outside_share * inner.sum()):
        implausible.append(f"{int(outside.sum())} wall points outside the body's outer wall")
    if implausible:
        raise InteriorMergeError(
            "interior merge refused: interior_wall_implausible ("
            + "; ".join(implausible)
            + ") - different jar or misaligned scan",
            ("interior_wall_implausible",),
        )
    profile = _profile_failures(moved, gap, inner, wall, noise, b_rim, t)
    if profile:
        raise InteriorMergeError(
            "interior merge refused: " + "; ".join(profile) + " - different jar?",
            ("interior_profile_mismatch",),
        )
    candidate = np.nonzero(in_below & (gap > split))[0]
    depth = b_rim.height - moved[candidate, 2]
    sectors = _sector(rel[candidate])
    floor = (nz[candidate] > 0.8) & (radius[candidate] < 0.8 * (b_rim.radius - wall / 2))
    floor_depth = None
    if floor.sum() >= 30 and len(np.unique(sectors[floor])) / SECTORS >= t.min_band_coverage:
        floor_depth = float(np.median(depth[floor]))
    # Thin shell: only points near the inner wall profile (body outer wall minus the measured
    # wall, within the per-band allowance) or on the scanned floor are interior; blobs inside
    # the cavity are not.
    shell = max(t.wall_variation_mm, 3 * noise, 2 * spacing)
    keep = np.abs(gap[candidate] - wall) < shell
    if floor_depth is not None:
        keep |= (nz[candidate] > 0.8) & (np.abs(depth - floor_depth) < shell)
    candidate, depth, sectors = candidate[keep], depth[keep], sectors[keep]
    if len(candidate) < 30:
        raise InteriorMergeError(
            "interior merge refused: the interior scan shows no surface below the rim",
            ("insufficient_overlap",),
        )
    # Density-aware coverage: a sector counts when it holds a quarter of the points its wall
    # area would give at the measured spacing (random points: density ~0.22 / spacing^2).
    area = band * 2 * np.pi * max(b_rim.radius - wall, 1.0) / SECTORS
    per_sector = max(2.0, 0.25 * 0.22 * area / spacing**2)
    bands: list[DepthBand] = []
    deepest, gap_mm, reached_floor = 0.0, 0.0, False
    top = b_rim.band
    while top < b_rim.height:
        bottom = min(top + band, b_rim.height)
        hit = (depth >= top) & (depth < bottom)
        counts = np.bincount(sectors[hit], minlength=SECTORS)
        coverage = float((counts >= per_sector).mean())
        if floor_depth is not None and top > floor_depth:
            kind = "base"  # wall under the inner floor: no interior to scan
        else:
            kind = "covered" if coverage >= t.min_band_coverage else "missing"
        bands.append(DepthBand(float(top), float(bottom), coverage, int(hit.sum()), kind))
        if kind == "covered" and gap_mm <= t.max_gap_mm:
            gap_mm = 0.0
            # a partly reached band counts as covered, but only down to its deepest point
            deepest = float(min(bottom, depth[hit].max()))
            reached_floor = floor_depth is not None and bottom > floor_depth
        elif kind == "missing":
            gap_mm += bottom - top
        top = bottom
    if reached_floor and floor_depth is not None:
        deepest = floor_depth
    missing = tuple((b.top_mm, b.bottom_mm) for b in bands if b.kind == "missing")
    index = candidate
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
            "height_offset_mm": b_rim.height - i_rim.height,
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
        wall_mm=wall,
        wall_noise_mm=noise,
        floor_depth_mm=floor_depth,
        interior_provenance="SCANNED_TO_FLOOR" if reached_floor else "SCANNED_PARTIAL_DEPTH",
    )


def _profile_failures(
    moved: np.ndarray,
    gap: np.ndarray,
    inner: np.ndarray,
    wall: float,
    noise: float,
    rim: _Rim,
    t: InteriorThresholds,
) -> list[str]:
    """Interior wall vs the body's outer wall minus a plausible wall (different jar check).

    ponytail: one wall thickness per jar with a fixed per-band variation allowance; jars with
    strongly thickened corners need a larger ``wall_variation_mm``."""

    failures = []
    depth = rim.height - moved[:, 2]
    level = (depth / t.band_mm).astype(int)
    allowed = max(t.wall_variation_mm, 4 * noise)
    populated = off = 0
    for key in np.unique(level[inner]):
        here = inner & (level == key)
        if here.sum() < 10:
            continue
        populated += 1
        off += int(abs(float(np.median(gap[here])) - wall) > allowed)
    if populated and off / populated > t.max_outside_share:
        failures.append(
            f"inner wall departs from the body outline by > {allowed:.1f} mm in {off} of "
            f"{populated} depth bands"
        )
    return failures


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
