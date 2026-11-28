"""Align scans of one physical part (upright + upside-down pairs, or N scans) in one metric frame.

Per scan (PL-0483): A4-mat frame in mm with +z up from the mat (caller ``to_mat_mm`` from the mat
markers, or a seeded RANSAC plane on a 2 mm voxel subsample plus ``mm_per_unit``), then an
iterative least-squares mat refit on the full cloud (absorbs small tilt / subsampling errors).
Object = the DBSCAN cluster standing on the mat footprint plus clusters above it (drops floaters
and off-mat clutter; refuses when nothing stands on the mat), minus a flat white glare halo
on the mat around its foot. Outer shell =
near-vertical points at the outer radius of their 5 degree x 5 mm cell (caps and interior surfaces
such as a closure recess are seen by one scan only and are never compared), after sparse MVS
strays (glare fans, tip spikes, curtains: ``_dense``) are dropped. A connected wall patch
without counterpart (``_miss_patch``, true area) is refused however small its slice share; the
merge leaves out points outside the other scan's footprint (PL-0483, see
coordination/sessions/M18-C001/PL-0483_REAL_PAIR_ROOT_CAUSE_V01.md).

Registration to the reference (first) scan: 180 degree flip about a horizontal axis from the
PL-0482 role (both poses when unknown), height fixed by mat contact (flipped: mat side ->
the taller scan's top), yaw sweep with yaw + in-plane ICP (the printed label's
lighting-normalised texture decides, only when significant, between yaws the wall fits
equally, e.g. a flat oval turned 180 degrees), then damped tilt + yaw + in-plane
point-to-plane ICP bounded by ``max_refine_deg`` / ``max_refine_mm`` (height stays on the mat
contact, which side walls cannot observe). Poses are ranked by a symmetric score: the worst 5 mm
side-wall slice coverage over both directions (no raw one-way inlier share). With an unknown
role, a pose putting surfaces into space the other scan saw empty (free-space conflict) is
dropped, and if both poses remain within ``ambiguity_margin`` the scan is refused as role
ambiguous. Acceptance also compares both scans' heights (own mat frames), their aligned
section walls bin by bin around the axis (shape-aware for oval parts) and the free-space
conflict, so different objects, scale errors and wrong roles are
refused with the failed check named. One exception: a scan whose free end MVS missed (its top
open, no closing face seen, walls agreeing elsewhere, gap <= ``max_missing_end_ratio``) is
accepted with the end completed from the other scan, recorded in ``limitations``. Yaw of rotationally symmetric parts is flagged
(``yaw_determined=False``), not guessed silently. Deterministic (seeded RANSAC, exact
KNN, numpy solves). Metric values stay METRIC_UNVERIFIED until owner caliper evidence; tests use
synthetic proxies only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

import numpy as np

METHOD = "mat_frame_flip_yaw_sweep_bounded_tilt_point_to_plane_icp_v3"
METRIC_STATUS = "METRIC_UNVERIFIED"
GATE_PASSED = "GATE_PASSED"
OWNER_CONFIRMED_UNVERIFIED = "OWNER_CONFIRMED_UNVERIFIED"
# Refusal kinds an owner may override (same part, scans disagree), and the most scale
# difference such an override may carry.
OVERRIDABLE = frozenset({"coverage", "patch", "section", "scale"})
OVERRIDE_MAX_SCALE = 0.02
PLANE_SEED = 7
PLANE_ITERATIONS = 1000
PROFILE_BANDS = 6
Query = Callable[..., tuple[np.ndarray, np.ndarray]]  # (points, k=1) -> (indices, distances)


class MultiScanAlignmentError(ValueError):
    """Raised when scans cannot be aligned reliably; the message names the failed check.

    ``heights_mm``: each prepared scan's own mat-frame height, when known (diagnostics).
    ``override_disagreements``: set by ``align_part_pair`` only when the refusal is one the
    owner may override (agreement gates on a determined pose, see ``_override_offer``): the
    measured disagreements, each a dict with a ``kind`` (``disagreement_text`` words it)."""

    heights_mm: dict[str, float] | None = None
    override_disagreements: tuple[dict[str, Any], ...] | None = None


@dataclass(frozen=True)
class ScanInput:
    scan_id: str
    points: np.ndarray  # (N, 3) reconstruction units
    colors: np.ndarray | None = None  # (N, 3) in [0, 1]
    to_mat_mm: np.ndarray | None = None  # 4x4 similarity raw units -> mat frame mm (z up)
    mm_per_unit: float = 1.0  # used only when to_mat_mm is None
    # Captured upside-down (PL-0482 scan role). None = unknown: both poses are tried and the
    # alignment is refused as "role ambiguous" unless one pose is clearly better.
    flipped: bool | None = None
    # Relative standard uncertainty of mm_per_unit (mat markers of this build), e.g. 0.007.
    scale_uncertainty: float | None = None


@dataclass(frozen=True)
class AlignmentThresholds:
    max_distance_mm: float = 2.0  # correspondence / coverage distance
    min_slice_coverage: float = 0.9  # worst side-wall slice, both directions
    max_rmse_mm: float = 1.0  # point-to-plane, worse direction
    height_tolerance_mm: float = 1.0
    width_tolerance_mm: float = 1.0
    dimension_tolerance_ratio: float = 0.015  # of height / diameter, whichever is larger
    min_profile_share: float = 0.5  # of the diameter bands either scan has, seen by both
    ambiguity_margin: float = 0.03  # score gap needed between flip / no-flip when role unknown
    max_free_space_conflict: float = 0.05  # share of points above the other scan's seen top
    max_missing_end_ratio: float = 0.15  # longest open end completed from the other scan
    closed_top_share: float = 0.08  # top band points inside half its radius: a seen top face
    max_scale_error: float = 0.01  # least shared-wall scale difference refused (see _gate)
    max_scale_cap: float = 0.012  # most the scale uncertainty may widen that bound to
    yaw_probe_deg: float = 5.0  # max yaw uncertainty for yaw_determined
    max_refine_deg: float = 5.0
    max_refine_mm: float = 5.0
    mat_margin_mm: float = 1.5
    plane_tolerance_mm: float = 1.0
    cluster_eps_mm: float = 3.0
    voxel_mm: float = 1.0
    slice_mm: float = 5.0
    yaw_steps: int = 12
    spacing_mm: float = 0.0  # measured point spacing; set by the aligner, not by callers


@dataclass(frozen=True)
class ScanAlignment:
    scan_id: str
    matrix: np.ndarray  # 4x4 raw scan units -> reference mat frame mm
    relative: np.ndarray  # 4x4 rigid, this scan's mat frame mm -> reference mat frame mm
    flipped: bool  # relative to the reference scan (not the scan's own role)
    coverage: float  # worst side-wall slice coverage, both directions
    rmse_mm: float  # point-to-plane, worse direction
    pose_margin: float  # score gap to the other flip (nan: role known or other pose conflicted)
    yaw_determined: bool  # False only for parts shown round: yaw (label seam) is arbitrary
    free_space_conflict: float = 0.0  # see _free_space_conflict
    yaw_uncertainty_deg: float = 0.0  # half width of the fine yaw coverage plateau
    height_mm: float = float("nan")  # this scan's own mat-frame height
    limitations: tuple[str, ...] = ()  # accepted with these (e.g. an end completed from a scan)
    dof: str = "tilt_yaw_xy_bounded_refine_height_from_mat_contact"


@dataclass(frozen=True)
class MultiScanAlignment:
    reference_id: str
    alignments: tuple[ScanAlignment, ...]  # reference first (identity relative)
    points: np.ndarray  # merged, voxel-downsampled, reference mat frame mm
    colors: np.ndarray | None
    source_index: np.ndarray  # per merged point: index into alignments
    point_index: np.ndarray  # per merged point: row in that scan's input points
    surface_coverage: dict[str, float]  # occupied share of side / top / bottom grid cells
    method: str = METHOD
    metric_status: str = METRIC_STATUS
    verification: str = GATE_PASSED  # or OWNER_CONFIRMED_UNVERIFIED (see align_part_pair)
    disagreements: tuple[dict[str, Any], ...] = ()  # measured, for an owner-confirmed merge


@dataclass(frozen=True)
class _Part:
    scan_id: str
    frame: np.ndarray  # raw -> mat mm
    points: np.ndarray  # cleaned object, mat mm
    index: np.ndarray  # rows into the input points
    height: float
    shell: np.ndarray  # outer side-wall points, mat mm
    normals: np.ndarray  # shell normals
    spacing: float  # median nearest-neighbour distance on the working voxel grid, mm
    colors: np.ndarray | None = None  # per ``points`` row, [0, 1]
    scale_uncertainty: float = 0.0  # relative, from ScanInput
    upside_down: bool | None = None  # ScanInput.flipped (capture role)


@dataclass(frozen=True)
class _Pose:
    matrix: np.ndarray
    flipped: bool
    coverage: float
    rmse: float
    yaw_uncertainty: float = float("inf")  # degrees, from the fine coverage scan
    colour_resolved: bool = False  # label texture picked this yaw over a geometric twin


def _apply(matrix: np.ndarray, points: np.ndarray) -> np.ndarray:
    return np.asarray(points @ matrix[:3, :3].T + matrix[:3, 3])


def _voxel_first(points: np.ndarray, voxel: float) -> np.ndarray:
    """Indices of the first point in each voxel, in input order (deterministic)."""

    _, first = np.unique(np.floor(points / voxel).astype(np.int64), axis=0, return_index=True)
    return np.sort(first)


def _nearest(target: np.ndarray) -> Query:
    import open3d.core as o3c

    index = o3c.nns.NearestNeighborSearch(o3c.Tensor.from_numpy(np.ascontiguousarray(target)))
    index.knn_index()

    def query(points: np.ndarray, k: int = 1) -> tuple[np.ndarray, np.ndarray]:
        found, d2 = index.knn_search(o3c.Tensor.from_numpy(np.ascontiguousarray(points)), k)
        return found.numpy().astype(np.int64), np.sqrt(d2.numpy())

    return query


def _normals(points: np.ndarray) -> np.ndarray:
    neighbours = points[_nearest(points)(points, min(10, len(points)))[0]]
    centred = neighbours - neighbours.mean(axis=1, keepdims=True)
    return np.asarray(np.linalg.eigh(np.einsum("nki,nkj->nij", centred, centred))[1][:, :, 0])


def _rodrigues(vector: np.ndarray) -> np.ndarray:
    angle = float(np.linalg.norm(vector))
    if angle < 1e-15:
        return np.eye(3)
    x, y, z = vector / angle
    k = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.asarray(np.eye(3) + np.sin(angle) * k + (1 - np.cos(angle)) * k @ k)


def _about(rotation: np.ndarray, centre: np.ndarray, shift: np.ndarray) -> np.ndarray:
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = centre - rotation @ centre + shift
    return matrix


def _yaw(angle: float, centre: np.ndarray | None = None) -> np.ndarray:
    pivot = np.zeros(3) if centre is None else centre
    return _about(_rodrigues(np.array([0.0, 0.0, angle])), pivot, np.zeros(3))


def _angle_deg(rotation: np.ndarray) -> float:
    return float(np.degrees(np.arccos(np.clip((np.trace(rotation) - 1) / 2, -1, 1))))


def _centre(points: np.ndarray) -> np.ndarray:
    """Footprint centre: least-squares fit to extent midpoints along 18 directions (near
    rotation-invariant, unlike per-axis extents)."""

    angles = np.linspace(0, np.pi, 18, endpoint=False)
    directions = np.c_[np.cos(angles), np.sin(angles)]
    low, high = np.percentile(points[:, :2] @ directions.T, [1, 99], axis=0)
    return np.asarray(np.linalg.lstsq(directions, (low + high) / 2, rcond=None)[0])


# ---------------------------------------------------------------- per-scan preparation


def _validate(scan: ScanInput) -> np.ndarray:
    points = np.asarray(scan.points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 100:
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: needs an (N>=100, 3) point array")
    if not np.isfinite(points).all():
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: non-finite points")
    if scan.colors is not None and np.shape(scan.colors) != points.shape:
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: colors must match points (N, 3)")
    if scan.to_mat_mm is not None:
        matrix = np.asarray(scan.to_mat_mm, dtype=float)
        if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
            raise MultiScanAlignmentError(f"scan {scan.scan_id}: to_mat_mm must be a finite 4x4")
        linear = matrix[:3, :3]
        det = float(np.linalg.det(linear))
        scale = det ** (1 / 3) if det > 0 else 0.0
        if (
            scale <= 0
            or not np.allclose(matrix[3], [0, 0, 0, 1])
            or not np.allclose(linear @ linear.T, scale**2 * np.eye(3), rtol=1e-6, atol=1e-9)
        ):
            raise MultiScanAlignmentError(
                f"scan {scan.scan_id}: to_mat_mm must be a proper similarity (rotation x scale)"
            )
    elif not (np.isfinite(scan.mm_per_unit) and scan.mm_per_unit > 0):
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: mm_per_unit must be positive")
    u = scan.scale_uncertainty
    if u is not None and not (np.isfinite(u) and 0 <= u < 0.1):
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: scale_uncertainty must be in [0, 0.1)")
    return points


def _frame_from_plane(normal: np.ndarray, point: np.ndarray, foot_hint: np.ndarray) -> np.ndarray:
    helper = np.array([1.0, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1.0, 0])
    x_axis = helper - (helper @ normal) * normal
    x_axis /= np.linalg.norm(x_axis)
    rotation = np.stack([x_axis, np.cross(normal, x_axis), normal])
    foot = foot_hint - ((foot_hint - point) @ normal) * normal
    return _about(rotation, np.zeros(3), -rotation @ foot)


def _mat_frame(points_mm: np.ndarray, limits: AlignmentThresholds) -> np.ndarray:
    """Seeded RANSAC on an even-stride subsample (keeps density, so the photographed mat beats a
    sparse floor or table). Up = the side holding more points over the mat's own footprint:
    cameras above the mat see the part on it, never what lies under it."""

    sample = points_mm[:: max(1, len(points_mm) // 20000)]  # density-weighted: the mat is dense
    rng = np.random.default_rng(PLANE_SEED)
    triples = sample[rng.integers(0, len(sample), (PLANE_ITERATIONS, 3))]
    normals = np.cross(triples[:, 1] - triples[:, 0], triples[:, 2] - triples[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    keep = lengths > 1e-9
    normals, triples = normals[keep] / lengths[keep, None], triples[keep]
    offsets = -np.einsum("ij,ij->i", normals, triples[:, 0])
    tolerance = limits.plane_tolerance_mm
    best = int(np.argmax((np.abs(sample @ normals.T + offsets) < tolerance).sum(axis=0)))
    normal, offset = normals[best], float(offsets[best])
    heights = sample @ normal + offset
    on_mat = np.abs(heights) < tolerance
    helper = np.array([1.0, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1.0, 0])
    u_axis = np.cross(normal, helper)
    u_axis /= np.linalg.norm(u_axis)
    in_plane = sample @ np.c_[u_axis, np.cross(normal, u_axis)]
    low, high = np.percentile(in_plane[on_mat], [5, 95], axis=0)
    over = np.all((in_plane > low) & (in_plane < high), axis=1)
    off = over & (np.abs(heights) > 3 * tolerance)
    if (heights[off] > 0).sum() < (heights[off] < 0).sum():
        normal, offset, heights = -normal, -offset, -heights
    above = sample[heights > 3 * tolerance]
    if len(above) < 30:
        raise MultiScanAlignmentError("nothing stands on the mat plane")
    return _frame_from_plane(normal, -offset * normal, above.mean(axis=0))


def _refine_mat(mat_mm: np.ndarray, tolerance: float) -> np.ndarray:
    """Least-squares mat refit around z = 0 in bands of 3, 2, 1 x tolerance; returns a 4x4."""

    frame = np.eye(4)
    for factor in (3.0, 2.0, 1.0):
        mat = _apply(frame, mat_mm)
        near = mat[np.abs(mat[:, 2]) < factor * tolerance]
        if len(near) < 30:
            raise MultiScanAlignmentError("no mat plane found in scan")
        centroid = near.mean(axis=0)
        normal = np.linalg.svd(near - centroid, full_matrices=False)[2][2]
        normal = normal if normal[2] > 0 else -normal
        above = mat[mat[:, 2] > 3 * tolerance]
        foot = above.mean(axis=0) if len(above) else centroid
        frame = _frame_from_plane(normal, centroid, foot) @ frame
    return frame


def _mat_box(mat_xy: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
    """Inside-test for the mat's footprint: principal-axis box of its points (p2..p98)."""

    centre = mat_xy.mean(axis=0)
    axes = np.linalg.svd(mat_xy - centre, full_matrices=False)[2]
    low, high = np.percentile((mat_xy - centre) @ axes.T, [2, 98], axis=0)

    def inside(xy: np.ndarray) -> np.ndarray:
        local = (xy - centre) @ axes.T
        return np.asarray(np.all((local > low) & (local < high), axis=1))

    return inside


def _object_on_mat(
    points: np.ndarray,
    mat_xy: np.ndarray,
    eps: float,
    spacing: float,
    limits: AlignmentThresholds,
) -> np.ndarray:
    """Mask of the part standing on the mat.

    DBSCAN clusters (eps from point spacing). Seeds: clusters whose base touches the mat (within
    ``mat_margin_mm`` + max(3 mm, 3 spacings)) and whose footprint centre lies over the mat; the
    largest seed wins. Clusters above that footprint (e.g. a lid top cut off by a thin MVS side
    wall) join it. No seed -> "object not found on the mat".
    """

    import open3d as o3d

    keys = np.floor(points / limits.voxel_mm).astype(np.int64)
    _, first, inverse = np.unique(keys, axis=0, return_index=True, return_inverse=True)
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points[first]))
    labels = np.asarray(cloud.cluster_dbscan(eps=eps, min_points=5))[inverse.ravel()]
    over_mat = _mat_box(mat_xy)
    touch = limits.mat_margin_mm + max(3.0, 3.0 * spacing)
    best, best_count = -1, 0
    for label in range(int(labels.max(initial=-1)) + 1):
        member = points[labels == label]
        footprint = np.median(member[:, :2], axis=0, keepdims=True)
        if member[:, 2].min() <= touch and over_mat(footprint)[0] and len(member) > best_count:
            best, best_count = label, len(member)
    if best < 0:
        raise MultiScanAlignmentError("object not found on the mat (no cluster stands on it)")
    seed = points[labels == best]
    centre = np.median(seed[:, :2], axis=0)
    reach = float(np.percentile(np.linalg.norm(seed[:, :2] - centre, axis=1), 95)) + eps
    mask = labels == best
    for label in range(int(labels.max()) + 1):
        member = points[labels == label]
        if label == best or len(member) < 0.05 * best_count:
            continue
        if np.linalg.norm(np.median(member[:, :2], axis=0) - centre) < reach:
            mask |= labels == label
    return mask


GLARE_HEIGHT_MM = 6.0  # mat glare / shadow halos MVS lifts off the mat stay below this
FOOT_FLARE_MM = 10.0  # widest foot flare (beyond the wall above) kept under GLARE_HEIGHT_MM


def _mat_halo(points: np.ndarray, colors: np.ndarray | None, spacing: float) -> np.ndarray:
    """Mask of a flat halo on the mat around the part's foot (specular glare on the white mat
    that MVS lifts a few mm and DBSCAN joins to the part: a 97 mm skirt under a 57 mm bottle in
    real scans). Halo = below ``GLARE_HEIGHT_MM``, over max(3 mm, 3 spacings) beyond the outline
    of the part's own section just above (per 10 degree azimuth; a floor or recess inside the
    outline stays), glare-white (every channel >= 0.6, grey within 0.15) when colours are
    given (the printed mat itself is darker: median ~0.56 on the owner's scans), and lying as a
    low layer not rising to the section above (a flared foot's wall does, so it stays).

    ponytail: a foot under 4 mm tall, flaring over FOOT_FLARE_MM, or sampled under 4 points
    per 10 degrees at its top, is cut like glare; the section check then refuses (fail-safe, never a wrong accept).
    """

    low = points[:, 2] < GLARE_HEIGHT_MM
    above = points[(points[:, 2] >= GLARE_HEIGHT_MM) & (points[:, 2] < GLARE_HEIGHT_MM + 10)]
    if not low.any() or len(above) < 30:
        return np.zeros(len(points), dtype=bool)
    centre = _centre(above)

    def polar(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        rel = xy - centre
        azimuth = ((np.arctan2(rel[:, 1], rel[:, 0]) + np.pi) / (2 * np.pi) * 36).astype(int)
        return azimuth % 36, np.linalg.norm(rel, axis=1)

    bins, radius = polar(above[:, :2])
    outline = np.full(36, np.inf)  # unseen azimuth: nothing is called halo there
    for k in np.unique(bins):
        outline[k] = np.percentile(radius[bins == k], 98)
    bins, radius = polar(points[low, :2])
    beyond = radius - outline[bins]
    halo = beyond > max(3.0, 3.0 * spacing)
    # A foot wall rises to the section above; glare thins out with height (owner's scans:
    # 84 of ~600 glare points above 4 mm, scattered or in blobs 26-37 mm out). Per bin, a
    # coherent wall top = 4+ points above GLARE_HEIGHT_MM - 2 within 1.5 mm of their median
    # outward reach, at most FOOT_FLARE_MM out; within it stays (foot wall and ledge), beyond
    # it is halo.
    top = points[low, 2] >= GLARE_HEIGHT_MM - 2
    for k in np.unique(bins[halo]):
        member = halo & (bins == k)
        upper = beyond[member & top]
        if len(upper) < 4:
            continue
        reach = float(np.median(upper))
        if reach <= FOOT_FLARE_MM and (np.abs(upper - reach) <= 1.5).sum() >= 4:
            halo[member & (beyond <= reach + 1.5)] = False
    if colors is not None:
        tone = colors[low]
        halo &= (tone.min(axis=1) >= 0.6) & (np.ptp(tone, axis=1) <= 0.15)
    mask = np.zeros(len(points), dtype=bool)
    mask[np.nonzero(low)[0][halo]] = True
    return mask


def _spacing(points: np.ndarray, voxel: float) -> tuple[float, float]:
    """(median, 95th percentile) nearest-neighbour distance after the working voxel grid."""

    sample = points[_voxel_first(points, voxel)]
    distance = _nearest(sample)(sample, 2)[1][:, 1]
    return float(np.median(distance)), float(np.percentile(distance, 95))


def _adapt(limits: AlignmentThresholds, spacing: float) -> AlignmentThresholds:
    """Scale lengths that must hold several samples to the measured point spacing (mm)."""

    return replace(
        limits,
        max_distance_mm=max(limits.max_distance_mm, 2.5 * spacing),
        slice_mm=max(limits.slice_mm, 6.0 * spacing),
        max_rmse_mm=max(limits.max_rmse_mm, 0.6 * spacing),  # sparse normals are noisier
        spacing_mm=spacing,
    )


def _top(z: np.ndarray) -> float:
    """Robust height of the highest face (cluster-cleaned input)."""

    return float(np.median(z[z > np.percentile(z, 99.9) - 1.0]))


def _part_top(points: np.ndarray) -> float:
    """Robust height of the highest face (cluster-cleaned input, ``points`` N x 3 mm).

    Blob-resistant: in the upper 20 mm (1 mm levels) the top is the highest kept level. Kept:
    a level at least half as wide as the typical level there; a ring (a neck or spout wall,
    on or off the part axis: points reach round the level's own centre, 10 of 12 sectors, and
    sit at its rim, median radius >= 0.85 of the 95th percentile); and the level just above a
    ring with about its width and centre (the neck's cap). A blob fused on a cap is a filled,
    narrow lump, no ring, and is skipped. ponytail: a blob on a neck cap, as wide as the neck,
    is not told apart."""

    z = points[:, 2]
    edges = np.arange(z.max() - 20.0, z.max() + 1.0, 1.0)
    level = np.searchsorted(edges, z) - 1
    count = len(edges) - 1
    widths, centres = np.zeros(count), np.zeros((count, 2))
    ring = np.zeros(count, dtype=bool)
    for k in np.unique(level[level >= 0]):
        xy = points[level == k, :2]
        if len(xy) >= 10:
            low, high = np.percentile(xy, [5, 95], axis=0)
            widths[k], centres[k] = float((high - low).max()), (low + high) / 2
            rel = xy - centres[k]
            radius = np.linalg.norm(rel, axis=1)
            sectors = np.unique(
                ((np.arctan2(rel[:, 1], rel[:, 0]) + np.pi) / (np.pi / 6)).astype(int)
            )
            ring[k] = len(sectors) >= 10 and np.median(radius) >= 0.85 * np.percentile(radius, 95)
    if (widths > 0).sum() >= 3:
        kept = (widths >= 0.5 * np.median(widths[widths > 0])) | ring
        for k in range(1, count):  # the cap closing a ring (one level, not chained)
            if ring[k - 1] and widths[k] > 0:
                near = np.linalg.norm(centres[k] - centres[k - 1]) < 0.25 * widths[k - 1]
                kept[k] |= near and 0.5 * widths[k - 1] <= widths[k] <= 1.2 * widths[k - 1]
        z = z[z < edges[np.nonzero(kept)[0][-1] + 1]] if kept.any() else z
    return _top(z)


SPARSE_SHARE = 0.25  # of the wall's median neighbour count; less is an MVS stray
# Largest wall patch (true area, mm^2) one scan may have without counterpart (and at least
# 40 spacings^2): synthetic genuine pairs read <= 14 (dense), <= 53 (d 0.2, spacing 1.2).
MISS_PATCH_MM2 = 40.0


def _dense(points: np.ndarray, spacing: float, voxel: float) -> np.ndarray:
    """Mask of points on a surface: within r = max(2.5 mm, 3 spacings) at least
    ``SPARSE_SHARE`` of the median neighbour count there (relative, so sparse scans and short
    bands keep their walls). The owner's real scans carry glare fans, tip spikes and curtains
    at a few points per 3 mm; their walls hold ~28."""

    radius = max(2.5, 3.0 * max(spacing, voxel))
    distance = _nearest(points)(points, min(48, len(points)))[1]
    count = (distance < radius).sum(axis=1)
    if np.median(count) < 12:  # too few neighbours to tell a stray from sampling noise
        return np.ones(len(points), dtype=bool)
    return np.asarray(count >= SPARSE_SHARE * np.median(count))


def _shell(
    points: np.ndarray, height: float, spacing: float, limits: AlignmentThresholds
) -> tuple[np.ndarray, np.ndarray]:
    """Outer side wall: band points with no other surface further out at the same place on the
    unrolled wall (arc x height window of 2.5 point spacings; removes recesses, inner walls and
    cap remnants). No angular grid, so the set does not depend on the mat frame's x axis.

    Sparse points are dropped first (``_dense``): "outermost" otherwise lets MVS glare fans,
    tip spikes and curtains outside the part replace its real wall.
    """

    band = points[(points[:, 2] > limits.mat_margin_mm + 2) & (points[:, 2] < height - 2)]
    band = band[_voxel_first(band, limits.voxel_mm)]
    band = band[_dense(band, spacing, limits.voxel_mm)] if len(band) >= 30 else band
    if len(band) < 30:
        raise MultiScanAlignmentError("too little side wall above the mat")
    rel = band[:, :2] - _centre(band)
    radius = np.linalg.norm(rel, axis=1)
    period = 2 * np.pi * float(np.median(radius))
    unrolled = np.c_[np.arctan2(rel[:, 1], rel[:, 0]) / (2 * np.pi) * period, band[:, 2]]
    unrolled = np.c_[unrolled, np.zeros(len(band))]
    wrapped = np.r_[unrolled, unrolled + [period, 0, 0], unrolled - [period, 0, 0]]
    found, distance = _nearest(wrapped)(unrolled, min(24, len(band)))
    window = max(2.0, 2.5 * spacing)
    outward = np.where(distance < window, np.tile(radius, 3)[found], -np.inf).max(axis=1)
    keep = outward <= radius + 2.5  # 2.5 mm: thinner than any wall gap we must tell apart
    shell = band[keep]
    if len(shell) < 30:
        raise MultiScanAlignmentError("too little side wall above the mat")
    return shell, _normals(shell)


def _prepare(scan: ScanInput, limits: AlignmentThresholds) -> _Part:
    raw = _validate(scan)
    if scan.to_mat_mm is not None:
        frame = np.asarray(scan.to_mat_mm, dtype=float)
    else:
        scale = np.diag([scan.mm_per_unit] * 3 + [1.0])
        frame = _mat_frame(raw * scan.mm_per_unit, limits) @ scale
    frame = _refine_mat(_apply(frame, raw), limits.plane_tolerance_mm) @ frame
    mm = _apply(frame, raw)
    above = np.nonzero(mm[:, 2] > limits.mat_margin_mm)[0]
    if len(above) < 100:
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: under 100 points above the mat")
    spacing, gap = _spacing(mm[above], limits.voxel_mm)
    # eps bridges the sparse 5 % of the surface (e.g. thin MVS side walls), still far below
    # the spacing of isolated floaters.
    eps = max(limits.cluster_eps_mm, 2.5 * gap)
    mat_xy = mm[np.abs(mm[:, 2]) < limits.plane_tolerance_mm, :2]
    try:
        chosen = _object_on_mat(mm[above], mat_xy, eps, spacing, limits)
    except MultiScanAlignmentError as error:
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: {error}") from None
    index = above[chosen]
    tone = None if scan.colors is None else np.asarray(scan.colors, dtype=float)[index]
    index = index[~_mat_halo(mm[index], tone, spacing)]
    points = mm[index]
    spacing = _spacing(points, limits.voxel_mm)[0]  # of the part itself, not the clutter
    height = _part_top(points)
    try:
        shell, normals = _shell(points, height, spacing, limits)
    except MultiScanAlignmentError as error:
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: {error}") from None
    colors = None if scan.colors is None else np.asarray(scan.colors, dtype=float)[index]
    return _Part(
        scan.scan_id,
        frame,
        points,
        index,
        height,
        shell,
        normals,
        spacing,
        colors,
        float(scan.scale_uncertainty or 0.0),
        scan.flipped,
    )


# ---------------------------------------------------------------- pose search and scoring


def _icp(
    src: np.ndarray,
    target: _Part,
    query: Query,
    matrix: np.ndarray,
    columns: list[int],
    limits: AlignmentThresholds,
    coarse_distance: float,
    damping: float,
    iterations: int = 40,
) -> np.ndarray:
    """Point-to-plane ICP over a subset of (wx, wy, wz, tx, ty, tz); damped normal equations."""

    tgt, normals = target.shell, target.normals
    for iteration in range(iterations):
        moved = _apply(matrix, src)
        found, distance = query(moved)
        cut = coarse_distance if iteration < iterations // 3 else limits.max_distance_mm
        use = distance[:, 0] < cut
        if use.sum() < 10:
            break
        p, n, q = moved[use], normals[found[use, 0]], tgt[found[use, 0]]
        centre = p.mean(axis=0)
        residual = np.einsum("ij,ij->i", n, p - q)
        jacobian = np.c_[np.cross(p - centre, n), n][:, columns]
        system = jacobian.T @ jacobian + damping * len(p) * np.eye(len(columns))
        step = np.linalg.solve(system, -jacobian.T @ residual)
        full = np.zeros(6)
        full[columns] = step
        matrix = _about(_rodrigues(full[:3]), centre, full[3:]) @ matrix
        if iteration >= iterations // 3 and np.abs(step).max() < 1e-8:
            break
    return matrix


def _score(
    source: _Part, matrix: np.ndarray, target: _Part, query: Query, limits: AlignmentThresholds
) -> tuple[float, float]:
    """(worst slice coverage over both directions, worse point-to-plane RMSE) on outer shells."""

    slices, rmse, _ = _slices(source, matrix, target, query, limits)
    return (float(slices.min()) if len(slices) else 0.0), rmse


def _slices(
    source: _Part, matrix: np.ndarray, target: _Part, query: Query, limits: AlignmentThresholds
) -> tuple[np.ndarray, float, int]:
    """Per wall slice: min of both coverage directions; worse RMSE; fewest points in a slice."""

    moved = _apply(matrix, source.shell)
    moved_normals = source.normals @ matrix[:3, :3].T
    tgt = target.shell
    # Shared height range, inset so slice edges never hold one cloud only.
    lo = max(np.percentile(moved[:, 2], 1), np.percentile(tgt[:, 2], 1)) + 1.0
    hi = min(np.percentile(moved[:, 2], 99), np.percentile(tgt[:, 2], 99)) - 1.0
    if hi - lo < 1.0:
        return np.zeros(0), float("inf"), 0
    edges = np.linspace(lo, hi, max(1, round((hi - lo) / limits.slice_mm)) + 1)  # equal slices
    found_ab, dist_ab = query(moved, 3)
    found_ba, dist_ba = _nearest(moved)(tgt, 3)
    found_ab, d_ab, found_ba, d_ba = found_ab[:, 0], dist_ab[:, 0], found_ba[:, 0], dist_ba[:, 0]
    # The other scan "has data here" when 3 of its points are near (one stray point is not).
    near_ab, near_ba = dist_ab[:, 2], dist_ba[:, 2]
    coverage: list[float] = []
    counts: list[int] = []
    for start, stop in zip(edges[:-1], edges[1:], strict=True):
        # Only where the other scan has data nearby: a hole in one scan (glossy band MVS missed)
        # is not a misfit; a feature a few mm off still is.
        seen = 3 * limits.max_distance_mm
        in_a = (moved[:, 2] >= start) & (moved[:, 2] < stop) & (near_ab < seen)
        in_b = (tgt[:, 2] >= start) & (tgt[:, 2] < stop) & (near_ba < seen)
        if in_a.sum() < 15 or in_b.sum() < 15:
            coverage.append(np.nan)  # keeps slice positions comparable between poses
            continue
        counts.append(int(min(in_a.sum(), in_b.sum())))
        coverage.append(
            min(
                float((d_ab[in_a] < limits.max_distance_mm).mean()),
                float((d_ba[in_b] < limits.max_distance_mm).mean()),
            )
        )
    slices = np.array(coverage)
    if np.isnan(slices).all():
        return np.zeros(0), float("inf"), 0
    hit_a = (moved[:, 2] >= lo) & (moved[:, 2] <= hi) & (d_ab < limits.max_distance_mm)
    hit_b = (tgt[:, 2] >= lo) & (tgt[:, 2] <= hi) & (d_ba < limits.max_distance_mm)
    if not hit_a.any() or not hit_b.any():
        return slices[~np.isnan(slices)], float("inf"), min(counts)
    near_b, near_a = found_ab[hit_a], found_ba[hit_b]
    r_ab = np.einsum("ij,ij->i", target.normals[near_b], moved[hit_a] - tgt[near_b])
    r_ba = np.einsum("ij,ij->i", moved_normals[near_a], tgt[hit_b] - moved[near_a])
    rmse = float(max(np.sqrt(np.mean(r_ab**2)), np.sqrt(np.mean(r_ba**2))))
    return slices[~np.isnan(slices)], rmse, min(counts)


def _point_area(points: np.ndarray, spacing: float) -> np.ndarray:
    """Surface area each point stands for (mm^2): pi r^2 over its neighbour count within r =
    max(3 mm, 2.5 spacings), from the local density (a 200 mm^2 face sums to ~200)."""

    radius = max(3.0, 2.5 * spacing)
    distance = _nearest(points)(points, min(64, len(points)))[1]
    return np.asarray(np.pi * radius**2 / np.maximum((distance < radius).sum(axis=1), 1))


def _miss_patch(
    source: _Part,
    matrix: np.ndarray,
    target: _Part,
    query: Query,
    limits: AlignmentThresholds,
    where: bool = False,
) -> Any:
    """Largest connected patch (true area, mm^2) of either scan's wall that has the other
    scan's wall nearby (3 x the coverage distance) but not within the coverage distance. Noise
    misses scatter; a feature one scan lacks (lug, rim, bump) misses as a patch, which the slice
    share hides when it fills under 10 % of every slice."""

    import open3d as o3d

    moved, tgt = _apply(matrix, source.shell), target.shell
    _, dist_ab = query(moved, 3)
    _, dist_ba = _nearest(moved)(tgt, 3)
    lo = max(np.percentile(moved[:, 2], 1), np.percentile(tgt[:, 2], 1)) + 1.0
    hi = min(np.percentile(moved[:, 2], 99), np.percentile(tgt[:, 2], 99)) - 1.0
    step = max(limits.spacing_mm, limits.voxel_mm)
    largest, at = 0.0, [float("nan"), float("nan")]
    for points, distance in ((moved, dist_ab), (tgt, dist_ba)):
        miss = (
            (distance[:, 2] < 3 * limits.max_distance_mm)
            & (distance[:, 0] >= limits.max_distance_mm)
            & (points[:, 2] >= lo)
            & (points[:, 2] <= hi)
        )
        if miss.sum() < 2:
            continue
        area = _point_area(points, step)[miss]
        cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points[miss]))
        labels = np.asarray(cloud.cluster_dbscan(eps=max(3.0, 2.5 * step), min_points=1))
        sums = np.bincount(labels, weights=area)
        if sums.max() > largest:
            largest = float(sums.max())
            z = points[miss][labels == int(np.argmax(sums)), 2]
            at = [float(z.min()), float(z.max())]
    return (largest, at) if where else largest


def _slice_profile(
    source: _Part, matrix: np.ndarray, target: _Part, query: Query, limits: AlignmentThresholds
) -> list[tuple[float, float, float]]:
    """(z low, z high, coverage) per wall slice, as ``_slices`` measures it (min of both
    directions, only where the other scan has data nearby)."""

    moved, tgt = _apply(matrix, source.shell), target.shell
    lo = max(np.percentile(moved[:, 2], 1), np.percentile(tgt[:, 2], 1)) + 1.0
    hi = min(np.percentile(moved[:, 2], 99), np.percentile(tgt[:, 2], 99)) - 1.0
    if hi - lo < 1.0:
        return []
    edges = np.linspace(lo, hi, max(1, round((hi - lo) / limits.slice_mm)) + 1)
    d_ab = query(moved, 3)[1]
    d_ba = _nearest(moved)(tgt, 3)[1]
    seen = 3 * limits.max_distance_mm
    out = []
    for start, stop in zip(edges[:-1], edges[1:], strict=True):
        in_a = (moved[:, 2] >= start) & (moved[:, 2] < stop) & (d_ab[:, 2] < seen)
        in_b = (tgt[:, 2] >= start) & (tgt[:, 2] < stop) & (d_ba[:, 2] < seen)
        if in_a.sum() >= 15 and in_b.sum() >= 15:
            coverage = min(
                float((d_ab[in_a, 0] < limits.max_distance_mm).mean()),
                float((d_ba[in_b, 0] < limits.max_distance_mm).mean()),
            )
            out.append((float(start), float(stop), coverage))
    return out


def _pose_for_flip(
    source: _Part, target: _Part, query: Query, flipped: bool, limits: AlignmentThresholds
) -> _Pose:
    size = float(np.linalg.norm(np.ptp(target.shell, axis=0)))
    coarse: list[_Pose] = []
    # Flipped: its mat contact (z = 0) is the reference top face, at the full part height. A
    # scan can miss its free end (real upright: 153 of 173 mm; flipped Fast: 165 of 173 mm)
    # but not extend past the part, so that is the taller scan's height. (The walls are no
    # judge: two real builds' walls differ by a +-1 mm height-dependent flare, which picked
    # the short contact.) The gate checks the height difference.
    for contact in {max(target.height, source.height)} if flipped else {0.0}:
        base = np.diag([1.0, -1.0, -1.0, 1.0]) if flipped else np.eye(4)  # 180 deg about mat x
        base[2, 3] = contact
        for step in range(limits.yaw_steps):
            start = _yaw(2 * np.pi * step / limits.yaw_steps) @ base
            start[:2, 3] += _centre(target.shell) - _centre(_apply(start, source.shell))
            matrix = _icp(source.shell, target, query, start, [2, 3, 4], limits, 0.08 * size, 1e-9)
            coverage, rmse = _score(source, matrix, target, query, limits)
            coarse.append(_Pose(matrix, flipped, coverage, rmse))
    best = _colour_yaw(source, target, coarse, limits)
    # Fine yaw + in-plane pass, then tilt + yaw + in-plane. Height stays on the mat contact: side
    # walls do not observe it (a closure's short wall let free z slide 1.3 mm in testing). Tilt
    # is kept only within bounds and when it clearly fits better: a short wall (lid) barely
    # constrains tilt, and the levelled mat frames are the better tilt evidence there.
    fine = _icp(
        source.shell, target, query, best.matrix, [2, 3, 4], limits, limits.max_distance_mm, 1e-9
    )
    fine_coverage, fine_rmse = _score(source, fine, target, query, limits)
    if (fine_coverage, -fine_rmse) >= (best.coverage, -best.rmse):
        best = replace(best, matrix=fine, coverage=fine_coverage, rmse=fine_rmse)
    tilt_dof = [0, 1, 2, 3, 4]
    refined = _icp(
        source.shell, target, query, best.matrix, tilt_dof, limits, limits.max_distance_mm, 1e-2
    )
    delta = refined @ np.linalg.inv(best.matrix)
    centre = _apply(best.matrix, source.shell.mean(axis=0, keepdims=True))
    moved_by = float(np.linalg.norm(_apply(delta, centre) - centre))
    if _angle_deg(delta[:3, :3]) > limits.max_refine_deg or moved_by > limits.max_refine_mm:
        return best  # refinement left its bounds: keep the mat-constrained pose
    coverage, rmse = _score(source, refined, target, query, limits)
    if rmse <= 0.9 * best.rmse and coverage >= best.coverage - 0.01:
        best = replace(best, matrix=refined, coverage=coverage, rmse=rmse)
    return _yaw_sweep_fine(source, target, query, best, limits)


TEXTURE_AZIMUTH_BINS = 180  # 2 degree columns of the unrolled side wall
TEXTURE_Z_MM = 2.0
TEXTURE_MIN_ENERGY = 0.05  # std of high-passed log luminance: about 5 % print contrast
TEXTURE_PEAK_SIGMA = 6.0  # chosen yaw above the shift-search sidelobes, in their std
TEXTURE_MARGIN_SIGMA = 4.0  # chosen yaw above every geometric twin, in sidelobe std
TEXTURE_MIN_MARGIN = 0.1  # ... and at least this much correlation


def _box(values: np.ndarray, reach_az: int, reach_z: int) -> np.ndarray:
    """Box sum over +-reach cells; azimuth (axis 0) wraps, height (axis 1) is cut at the ends."""

    wrapped = np.concatenate([values[-reach_az:], values, values[:reach_az]], axis=0)
    total = np.cumsum(np.pad(wrapped, ((1, 0), (0, 0))), axis=0)
    rows = total[2 * reach_az + 1 :] - total[: -2 * reach_az - 1]
    total = np.cumsum(np.pad(rows, ((0, 0), (1, 0))), axis=1)
    upper = np.minimum(np.arange(rows.shape[1]) + reach_z + 1, rows.shape[1])
    lower = np.maximum(np.arange(rows.shape[1]) - reach_z, 0)
    return np.asarray(total[:, upper] - total[:, lower])


def _texture_map(
    points: np.ndarray, colors: np.ndarray, centre: np.ndarray, edges: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """High-passed log luminance on the unrolled side wall (azimuth x height cells) and its
    mask. The log turns lighting (gain over the wall: one side lit) into an offset; the
    10 degree x 6 mm high-pass and removing column and row means take it out, leaving the
    print; the correlation's normalisation removes exposure. ponytail: assumes shading varies slower than the print; glossy highlights that
    move with the camera are not modelled."""

    rel = points[:, :2] - centre
    column = (np.arctan2(rel[:, 1], rel[:, 0]) + np.pi) / (2 * np.pi) * TEXTURE_AZIMUTH_BINS
    column = column.astype(int) % TEXTURE_AZIMUTH_BINS
    row = np.searchsorted(edges, points[:, 2]) - 1
    use = (row >= 0) & (row < len(edges) - 1)
    shape = (TEXTURE_AZIMUTH_BINS, len(edges) - 1)
    total, count = np.zeros(shape), np.zeros(shape)
    np.add.at(total, (column[use], row[use]), np.log(colors[use].mean(axis=1) + 0.02))
    np.add.at(count, (column[use], row[use]), 1.0)
    mask = count > 0
    mean = np.where(mask, total / np.maximum(count, 1), 0.0)
    smooth = _box(mean, 5, 3) / np.maximum(_box(mask.astype(float), 5, 3), 1)
    texture = np.where(mask, mean - smooth, 0.0)
    # Remove what varies along one axis only: directional light on a wall shades whole columns
    # (azimuth) and a light above shades whole rows; print changes along both.
    for axis in (1, 0):
        held = np.maximum(mask.sum(axis=axis, keepdims=True), 1)
        texture = np.where(mask, texture - texture.sum(axis=axis, keepdims=True) / held, 0.0)
    return texture, mask


def _texture_curve(
    source: _Part, matrix: np.ndarray, target: _Part, limits: AlignmentThresholds
) -> np.ndarray | None:
    """Normalised cross-correlation of the two walls' print textures for every 2 degree yaw
    shift of ``source`` (moved by ``matrix``) about the reference axis; None without colour or
    without print (texture energy under ``TEXTURE_MIN_ENERGY``: plain or only shaded walls)."""

    if source.colors is None or target.colors is None:
        return None
    centre = _centre(target.shell)
    moved = _apply(matrix, source.points)
    lo = max(np.percentile(moved[:, 2], 1), np.percentile(target.points[:, 2], 1)) + 2
    hi = min(np.percentile(moved[:, 2], 99), np.percentile(target.points[:, 2], 99)) - 2
    if hi - lo < 6 * TEXTURE_Z_MM:
        return None
    edges = np.arange(lo, hi, TEXTURE_Z_MM)
    radius = float(np.median(np.linalg.norm(target.shell[:, :2] - centre, axis=1)))

    def wall(points: np.ndarray, colors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        outer = np.linalg.norm(points[:, :2] - centre, axis=1) > 0.6 * radius
        return _texture_map(points[outer], colors[outer], centre, edges)

    mine, seen = wall(target.points, target.colors)
    theirs, held = wall(moved, source.colors)
    for texture, mask in ((mine, seen), (theirs, held)):
        if mask.sum() < 100 or texture[mask].std() < TEXTURE_MIN_ENERGY:
            return None
    curve = np.full(TEXTURE_AZIMUTH_BINS, np.nan)
    for shift in range(TEXTURE_AZIMUTH_BINS):
        both = seen & np.roll(held, shift, axis=0)
        if both.sum() < 100:
            continue
        a, b = mine[both], np.roll(theirs, shift, axis=0)[both]
        a, b = a - a.mean(), b - b.mean()
        curve[shift] = float(a @ b / max(np.sqrt((a @ a) * (b @ b)), 1e-12))
    return curve


def _colour_yaw(
    source: _Part, target: _Part, coarse: list[_Pose], limits: AlignmentThresholds
) -> _Pose:
    """Best coarse pose; the printed label decides between yaws the wall fits about equally
    well (a flat-oval bottle fits its own shape turned 180 degrees: front and back swap).

    Texture shift search (``_texture_curve``) from the geometric best: the twin a label picks
    must stand ``TEXTURE_PEAK_SIGMA`` sidelobe std above the shifts no twin explains and beat
    every other twin over 20 degrees away by max(``TEXTURE_MIN_MARGIN``,
    ``TEXTURE_MARGIN_SIGMA`` sidelobe std). Anything less (plain, shaded only, upside-down
    label from a wrong role) leaves the geometric best, and the gate refuses its yaw.
    """

    best = max(coarse, key=lambda pose: (pose.coverage, -pose.rmse))
    twins = [pose for pose in coarse if pose.coverage >= best.coverage - 0.05]
    turns = [
        float(np.degrees(np.arctan2(*(pose.matrix[:3, :3] @ best.matrix[:3, :3].T)[[1, 0], 0])))
        for pose in twins
    ]
    if all(min(abs(t), 360 - abs(t)) <= 20 for t in turns):
        return best  # no geometric twin: the gate judges the yaw from the wall alone
    curve = _texture_curve(source, best.matrix, target, limits)
    if curve is None:
        return best
    step = 360 / TEXTURE_AZIMUTH_BINS
    shifts = np.array([round(t / step) % TEXTURE_AZIMUTH_BINS for t in turns])
    index = np.arange(TEXTURE_AZIMUTH_BINS)
    near = np.zeros(TEXTURE_AZIMUTH_BINS, dtype=bool)
    scores = []
    for shift in shifts:
        gap = np.minimum(abs(index - shift), TEXTURE_AZIMUTH_BINS - abs(index - shift))
        near |= gap <= 10 / step
        window = curve[gap <= 1]
        scores.append(float(np.nanmax(window)) if np.isfinite(window).any() else -1.0)
    side = curve[~near & np.isfinite(curve)]
    if len(side) < 20:
        return best
    sigma, centre = float(side.std()), float(side.mean())
    pick = int(np.argmax(scores))
    rivals = [
        score
        for turn, score in zip(turns, scores, strict=True)
        if min(abs(turn - turns[pick]) % 360, 360 - abs(turn - turns[pick]) % 360) > 20
    ]
    margin = max(TEXTURE_MIN_MARGIN, TEXTURE_MARGIN_SIGMA * sigma)
    if (
        rivals
        and scores[pick] >= centre + TEXTURE_PEAK_SIGMA * sigma
        and scores[pick] - max(rivals) >= margin
    ):
        return replace(twins[pick], colour_resolved=True)
    return best


def _yaw_sweep_fine(
    source: _Part,
    target: _Part,
    query: Query,
    pose: _Pose,
    limits: AlignmentThresholds,
    mean: bool = False,
) -> _Pose:
    """+-10 degree, 1 degree yaw scan on wall coverage. Turns within the coverage noise of the
    best (2 binomial sigma of the sparsest slice, at least 0.01) form a plateau; its centre is
    the yaw (ICP can settle off-centre on sparse walls) and its half width (+0.5 degree) the yaw
    uncertainty, so sparse data cannot claim a precision its noise does not support.
    ``mean`` (owner-confirmed path only): score each turn by the mean slice coverage (noise over
    all slices) instead of the worst slice, so slices the scans disagree on at every yaw (a
    curtain, a shrunken closure) do not flatten the plateau."""

    centre = np.r_[_centre(target.shell), 0.0]
    turns = np.arange(-10, 11)
    scores = []
    fewest = 1
    for t in turns:
        slices, rmse, count = _slices(
            source, _yaw(np.radians(float(t)), centre) @ pose.matrix, target, query, limits
        )
        worst = 0.0 if not len(slices) else float(slices.mean() if mean else slices.min())
        scores.append((worst, rmse))
        if t == 0:
            fewest = max(fewest, count * (len(slices) if mean else 1))
    coverage = np.array([c for c, _ in scores])
    best = float(coverage.max())
    noise = 2 * np.sqrt(max(best * (1 - best), 0.01 * 0.99) / fewest)
    plateau = turns[coverage >= best - max(0.01, noise)]
    uncertainty = (plateau.max() - plateau.min()) / 2 + 0.5
    middle = int(round((plateau.max() + plateau.min()) / 2))
    if middle == 0:
        return replace(pose, yaw_uncertainty=float(uncertainty))
    matrix = _yaw(np.radians(middle), centre) @ pose.matrix
    c, r = scores[middle + 10]
    return replace(pose, matrix=matrix, coverage=c, rmse=r, yaw_uncertainty=float(uncertainty))


def _width(points: np.ndarray, z: float, half: float) -> float:
    band = points[np.abs(points[:, 2] - z) < half]
    if len(band) < 15:
        return float("nan")
    angles = np.linspace(0, np.pi, 8, endpoint=False)
    projected = band[:, :2] @ np.c_[np.cos(angles), np.sin(angles)].T
    low, high = np.percentile(projected, [1, 99], axis=0)
    return float(np.mean(high - low))


def _section(points: np.ndarray, z: float, half: float) -> np.ndarray:
    """(narrowest, widest) caliper width of the band at ``z`` over 36 directions, mm; NaN when
    sparse. Reported so a refusal names the section sizes of a non-round part."""

    band = points[np.abs(points[:, 2] - z) < half]
    if len(band) < 15:
        return np.full(2, np.nan)
    angles = np.linspace(0, np.pi, 36, endpoint=False)
    low, high = np.percentile(band[:, :2] @ np.c_[np.cos(angles), np.sin(angles)].T, [1, 99], 0)
    return np.array([(high - low).min(), (high - low).max()])


def _radial_offset(mine: np.ndarray, theirs: np.ndarray) -> tuple[float, float]:
    """(median radial offset of ``theirs`` from ``mine``, typical radius), mm: per 10 degree
    azimuth bin both bands fill, the median radius about ``mine``'s centre. Shape-aware: an oval
    is compared bin by bin, not as one circle; medians shrug off fuzzy MVS tips. NaN when the
    bands share under 9 bins."""

    centre = _centre(mine)

    def radii(band: np.ndarray) -> np.ndarray:
        rel = band[:, :2] - centre
        radius = np.linalg.norm(rel, axis=1)
        azimuth = ((np.arctan2(rel[:, 1], rel[:, 0]) + np.pi) / (2 * np.pi) * 36).astype(int) % 36
        out = np.full(36, np.nan)
        for k in range(36):
            if (azimuth == k).sum() >= 3:
                out[k] = np.median(radius[azimuth == k])
        return out

    a, b = radii(mine), radii(theirs)
    both = ~np.isnan(a) & ~np.isnan(b)
    if both.sum() < 9:
        return float("nan"), float("nan")
    return float(np.median(b[both] - a[both])), float(np.median(a[both]))


def _closed_top(part: _Part, limits: AlignmentThresholds) -> bool:
    """Did the scan see a face closing its top (cap, base, lid)? Share of the top 3 mm band
    inside half the band's radius: a disc puts ~20 % there, a wall that just ends (MVS lost the
    rest) ~0. An open-mouthed part (body rim) reads open too; ``_missing_end_problems`` only
    completes upside-down scans for that reason."""

    band = part.points[part.points[:, 2] > part.height - 3]
    if len(band) < 15:
        return False
    radius = np.linalg.norm(band[:, :2] - _centre(band), axis=1)
    return bool((radius < 0.5 * np.percentile(radius, 95)).mean() >= limits.closed_top_share)


def _scale_ratio(
    reference: _Part, other: _Part, matrix: np.ndarray, limits: AlignmentThresholds
) -> float:
    """Median radius ratio other / reference of the shared walls (3 mm bands, bin by bin around
    the axis); NaN with under 3 bands. Many bands pin a 1-2 % scale error the per-band section
    tolerance and the height tolerance let through."""

    moved = _apply(matrix, other.shell)
    ratios = []
    top = min(reference.height, other.height) - 2
    for z in np.arange(limits.mat_margin_mm + 4, top - 1.5, 3.0):
        mine = reference.shell[np.abs(reference.shell[:, 2] - z) < 1.5]
        theirs = moved[np.abs(moved[:, 2] - z) < 1.5]
        if len(mine) >= 15 and len(theirs) >= 15:
            offset, radius = _radial_offset(mine, theirs)
            if np.isfinite(offset) and radius > 0:
                ratios.append(1 + offset / radius)
    return float(np.median(ratios)) if len(ratios) >= 3 else float("nan")


def _missing_end_problems(
    short: _Part,
    long: _Part,
    reference: _Part,
    other: _Part,
    matrix: np.ndarray,
    limits: AlignmentThresholds,
) -> list[str]:
    """Why the height gap cannot be a missing end of ``short`` (empty list: it can be).

    - scale: enough shared wall to measure it (``_scale_ratio``, gated for every pair).
    - role: only an upside-down scan's free end (the part's base: closed on packaging parts)
      is completed. An upright scan's free end is the part's top, which could be a real open
      mouth or rim; the upside-down scan stands on it and never sees it, so it is refused.
      (A visible-inside test was tried: on the owner's real clouds the base push-up dome and
      tapering caps read as "inside" too, so it would refuse the genuine case.) ponytail: an
      upside-down part with a genuinely open free end (a closure's recess) and the same walls
      but up to 15 % taller passes as a lost end; the limitation names it.
    - contact: the flipped scan's mat contact (the taller top) must be where the walls put it,
      a z shift of 2-3 mm may not fit the shared walls clearly better.
    """

    problems: list[str] = []
    if not np.isfinite(_scale_ratio(reference, other, matrix, limits)):
        problems.append("too few shared wall bands to check the scales")
    flipped = bool(matrix[2, 2] < 0)
    if short.upside_down is not True:
        problems.append(
            f"scan {short.scan_id} is not an upside-down scan: its free end is the part's top, "
            "which no other scan sees (the upside-down scan stands on it), so a lost top cannot "
            "be told from a different, taller part"
        )
    if flipped:
        query = _nearest(reference.shell)
        base = _score(other, matrix, reference, query, limits)[0]
        for shift in (-3.0, -2.0, 2.0, 3.0):
            moved_z = np.eye(4)
            moved_z[2, 3] = shift
            if _score(other, moved_z @ matrix, reference, query, limits)[0] > base + 0.03:
                problems.append(
                    f"the walls fit {shift:+.0f} mm off the mat contact: top height unreliable"
                )
                break
    return problems


def _dimension_failures(
    reference: _Part,
    other: _Part,
    matrix: np.ndarray,
    limits: AlignmentThresholds,
    limitations: list[str] | None = None,
    details: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Height (each scan's own mat frame) and section size after alignment. The rigid pose
    cannot absorb a scale error or a different part: their walls sit consistently in or out.

    A height difference passes (noted in ``limitations``) only as a missing end: the shorter
    scan's top is open (no closing face seen), every section both scans have agrees, and the
    gap is at most ``max_missing_end_ratio`` of the taller scan. ``details`` receives one
    structured entry per failure (kind, measured values) for the owner-confirmed path."""

    failures = []
    notes: list[dict[str, Any]] = [] if details is None else details
    ratio = limits.dimension_tolerance_ratio
    tolerance = max(limits.height_tolerance_mm, ratio * reference.height)
    moved = _apply(matrix, other.shell)
    valid = seen_mine = seen_theirs = 0
    half = max(2.0, limits.slice_mm / 2.5)
    # Bands span both walls' real overlap: a flipped scan that lost its free end lacks the
    # reference's bottom, not its top (min height would leave its top band unchecked).
    lower = max(np.percentile(reference.shell[:, 2], 1), np.percentile(moved[:, 2], 1)) + half
    upper = min(np.percentile(reference.shell[:, 2], 99), np.percentile(moved[:, 2], 99)) - half
    heights = np.linspace(lower, upper, PROFILE_BANDS) if upper > lower else np.full(1, upper)
    sections: list[tuple[float, str]] = []
    for z in heights:
        mine = reference.shell[np.abs(reference.shell[:, 2] - z) < half]
        theirs = moved[np.abs(moved[:, 2] - z) < half]
        seen_mine += int(len(mine) >= 15)
        seen_theirs += int(len(theirs) >= 15)
        if len(mine) < 15 or len(theirs) < 15:
            continue
        offset, radius = _radial_offset(mine, theirs)
        if np.isnan(offset):
            continue
        valid += 1
        # radius tolerance: half the diameter one, + half a spacing for patchy sampled walls
        allowed = max(limits.width_tolerance_mm, ratio * 2 * radius) / 2 + 0.5 * limits.spacing_mm
        if abs(offset) > allowed:
            a, b = _section(mine, z, half), _section(theirs, z, half)
            notes.append(
                {
                    "kind": "section",
                    "z_mm": float(z),
                    "offset_mm": float(offset),
                    "tolerance_mm": float(allowed),
                    "reference_caliper_mm": [float(a[0]), float(a[1])],
                    "other_caliper_mm": [float(b[0]), float(b[1])],
                }
            )
            sections.append(
                (
                    float(z),
                    f"section mismatch at z={z:.0f} mm: wall {offset:+.1f} mm off "
                    f"(tolerance {allowed:.1f}; {b[0]:.1f} x {b[1]:.1f} vs {a[0]:.1f} x {a[1]:.1f} mm)",
                )
            )
    if abs(reference.height - other.height) > tolerance:
        message = (
            f"height mismatch {other.height:.1f} vs {reference.height:.1f} mm "
            f"(tolerance {tolerance:.1f})"
        )
        short, long = (reference, other) if reference.height < other.height else (other, reference)
        missing = long.height - short.height
        closed = _closed_top(short, limits)
        # Same walls up to near the shorter top, different height: that scan lost its top.
        if valid and all(z > short.height - 10 for z, _ in sections):
            candidate = (
                limitations is not None
                and not sections
                and not closed
                and missing <= limits.max_missing_end_ratio * long.height
            )
            problems = (
                _missing_end_problems(short, long, reference, other, matrix, limits)
                if candidate
                else []
            )
            if limitations is not None and candidate and not problems:
                limitations.append(
                    f"end completed from scan {long.scan_id}: scan {short.scan_id} misses its "
                    f"free end ({missing:.0f} mm; its cloud ends open there)"
                )
                message = ""
            else:
                message += (
                    f" - the sections agree, so scan {short.scan_id} most likely misses the top "
                    f"{missing:.0f} mm of the part"
                    + (" (yet it saw a face closing its top)" if closed else "")
                    + "".join(f"; {p}" for p in problems)
                    + ": rebuild or rescan it"
                )
        if message:
            failures.append(message)
            notes.append(
                {"kind": "height", "reference_mm": reference.height, "other_mm": other.height}
            )
    failures += [message for _, message in sections]
    scale = _scale_ratio(reference, other, matrix, limits)
    # Bound: the two builds' combined mat-marker scale uncertainty, at least max_scale_error.
    # Capped at max_scale_cap: the owner's real builds give u = 0.007-0.008 each (combined
    # 1.04 %), so an uncertainty claim far above that must not let 1.5-2 % scale errors pass.
    bound = min(
        limits.max_scale_cap,
        max(
            limits.max_scale_error,
            float(np.hypot(reference.scale_uncertainty, other.scale_uncertainty)),
        ),
    )
    if abs(scale - 1) > bound:  # NaN compares False
        notes.append({"kind": "scale", "ratio": float(scale), "limit": float(bound)})
        failures.append(
            f"the shared walls differ in scale by {100 * (scale - 1):+.2f} % "
            f"(limit {100 * bound:.2f} %, the scans' scale uncertainty): check both mat-marker "
            "scales"
        )
    # Real MVS walls can be patchy: demand overlap in a share of the bands either scan has.
    needed = max(1, int(np.ceil(limits.min_profile_share * max(seen_mine, seen_theirs))))
    if valid < needed:
        notes.append({"kind": "overlap", "bands": valid, "needed": needed})
        failures.append(
            f"too little overlapping side wall ({valid} of {len(heights)} section bands, "
            f"need {needed})"
        )
    return failures


def _free_space_conflict(first: _Part, second: _Part, matrix: np.ndarray, cell: float) -> float:
    """Share of ``first`` points (moved by ``matrix`` into ``second``'s mat frame) lying over 2 mm
    above the face ``second`` saw closing the same column (``cell`` mm, >= 3) from above.
    Cameras look down on the mat, so the space above a seen top face was seen empty; a wrong
    flip puts e.g. a lid's flat top over its own visible recess. A column whose top is only
    where a wall ends (most of its points well below: a missing end, an open rim) proves
    nothing about the space above and never conflicts. ponytail: ignores oblique views; a
    column the scan saw only partly can raise false conflicts, hence the tolerance share.
    ``first`` points under ``GLARE_HEIGHT_MM`` (its own mat glare and foot halo) are not
    tested: on the owner's real pair they were 97 % of a 0.054 false conflict.
    """

    own = np.floor(second.points[:, :2] / cell).astype(np.int64)
    keys, inverse = np.unique(own, axis=0, return_inverse=True)
    inverse = inverse.ravel()
    top = np.full(len(keys), -np.inf)
    np.maximum.at(top, inverse, second.points[:, 2])
    # Seen from above: at least half the column's points lie within 1.5 mm of its top.
    near_top = np.bincount(inverse, weights=(second.points[:, 2] > top[inverse] - 1.5) * 1.0)
    top[near_top < 0.5 * np.bincount(inverse)] = np.inf
    moved = _apply(matrix, first.points[first.points[:, 2] >= GLARE_HEIGHT_MM])
    cells = np.floor(moved[:, :2] / cell).astype(np.int64)
    flat_keys = keys[:, 0] * 2_000_003 + keys[:, 1]
    flat = cells[:, 0] * 2_000_003 + cells[:, 1]
    order = np.argsort(flat_keys)
    slot = np.clip(np.searchsorted(flat_keys[order], flat), 0, len(keys) - 1)
    hit = flat_keys[order][slot] == flat
    if not hit.any():
        return 0.0
    above = moved[hit, 2] > top[order][slot[hit]] + cell / 1.5
    return float(above.mean())


def _conflict(reference: _Part, other: _Part, pose: _Pose, limits: AlignmentThresholds) -> float:
    cell = max(3.0, 1.5 * limits.max_distance_mm)
    return max(
        _free_space_conflict(reference, other, np.linalg.inv(pose.matrix), cell),
        _free_space_conflict(other, reference, pose.matrix, cell),
    )


SIGNATURE_BINS = 36  # 10 degree azimuth bins of the radial wall profile


def _signature(points: np.ndarray, centre: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """Radial wall profile per (height band, 10 degree azimuth bin): median radius minus the
    band's median; NaN where fewer than 2 points. Works at sparse densities (cells hold a few
    points, not point-to-point matches)."""

    rel = points[:, :2] - centre
    radius = np.linalg.norm(rel, axis=1)
    azimuth = ((np.arctan2(rel[:, 1], rel[:, 0]) + np.pi) / (2 * np.pi) * SIGNATURE_BINS).astype(
        int
    ) % SIGNATURE_BINS
    band = np.searchsorted(edges, points[:, 2]) - 1
    result = np.full((len(edges) - 1, SIGNATURE_BINS), np.nan)
    for b in range(len(edges) - 1):
        in_band = band == b
        if in_band.sum() < 2:
            continue
        typical = np.median(radius[in_band])
        for k in np.unique(azimuth[in_band]):
            cell = in_band & (azimuth == k)
            if cell.sum() >= 2:
                result[b, k] = np.median(radius[cell]) - typical
    return result


def _bands(points: np.ndarray, limits: AlignmentThresholds) -> np.ndarray:
    lo, hi = np.percentile(points[:, 2], [1, 99])
    return np.linspace(lo, hi, max(1, round((hi - lo) / limits.slice_mm)) + 1)


def _profile_tolerance(part: _Part, limits: AlignmentThresholds) -> float:
    radius = float(np.median(np.linalg.norm(part.shell[:, :2] - _centre(part.shell), axis=1)))
    return max(limits.width_tolerance_mm, limits.dimension_tolerance_ratio * radius)


def _is_round(part: _Part, limits: AlignmentThresholds) -> bool:
    """Positive symmetry test: every observed azimuth cell sits on the band's typical radius."""

    signature = _signature(part.shell, _centre(part.shell), _bands(part.shell, limits))
    observed = signature[~np.isnan(signature)]
    return bool(len(observed) and np.abs(observed).max() <= _profile_tolerance(part, limits))


def _yaw_unique(
    reference: _Part,
    other: _Part,
    matrix: np.ndarray,
    limits: AlignmentThresholds,
    colour_resolved: bool = False,
) -> bool:
    """Is the chosen yaw the only one that fits the radial wall profile?"""

    return not _yaw_rivals(reference, other, matrix, limits, colour_resolved)


def _yaw_rivals(
    reference: _Part,
    other: _Part,
    matrix: np.ndarray,
    limits: AlignmentThresholds,
    colour_resolved: bool = False,
) -> list[float]:
    """Turns (degrees, 20-340) the radial wall profile cannot tell from ``matrix``'s yaw.

    Mismatch = summed |radius difference| over signature cells both scans observe (clipped at 3
    tolerances). Every yaw at least 20 degrees away must cost more than both two full-tolerance
    cells and four noise sigmas of that sum; symmetric or under-sampled walls fail this.
    ``colour_resolved``: the label texture already beat the half turn (an oval's geometric twin),
    so yaws within 20 degrees of 180 are not rivals.
    """

    centre = _centre(reference.shell)
    edges = _bands(reference.shell, limits)
    mine = _signature(reference.shell, centre, edges)
    moved = _apply(matrix, other.shell)
    tolerance = _profile_tolerance(reference, limits)

    def difference(turn_deg: float) -> np.ndarray:
        turned = _apply(_yaw(np.radians(turn_deg), np.r_[centre, 0.0]), moved)
        theirs = _signature(turned, centre, edges)
        both = ~np.isnan(mine) & ~np.isnan(theirs)
        return np.asarray(np.minimum(np.abs(mine[both] - theirs[both]), 3 * tolerance))

    at_pose = difference(0.0)
    if not len(at_pose):
        return [float("nan")]
    noise = float(np.median(at_pose)) * np.sqrt(len(at_pose))
    steps = [
        step
        for step in range(2, SIGNATURE_BINS - 1)
        if not (colour_resolved and abs(step * 10 - 180) <= 20)
    ]
    margin = max(2 * tolerance, 4 * noise)
    return [
        step * 10.0
        for step in steps
        if float(difference(step * 10.0).sum()) - float(at_pose.sum()) < margin
    ]


def _gate(
    reference: _Part,
    other: _Part,
    pose: _Pose,
    query: Query,
    limits: AlignmentThresholds,
    limitations: list[str] | None = None,
    details: list[dict[str, Any]] | None = None,
) -> tuple[list[str], bool]:
    notes: list[dict[str, Any]] = [] if details is None else details
    failures = _dimension_failures(reference, other, pose.matrix, limits, limitations, notes)
    conflict = _conflict(reference, other, pose, limits)
    if conflict > limits.max_free_space_conflict:
        notes.append({"kind": "conflict", "share": conflict})
        failures.append(
            f"free-space conflict {conflict:.3g} > {limits.max_free_space_conflict} "
            "(surfaces where the other scan saw empty space: wrong role or different part)"
        )
    if pose.coverage < limits.min_slice_coverage:
        notes.append(
            {
                "kind": "coverage",
                "worst": pose.coverage,
                "limit": limits.min_slice_coverage,
                "slices": [
                    [float(lo), float(hi), float(c)]
                    for lo, hi, c in _slice_profile(other, pose.matrix, reference, query, limits)
                    if c < limits.min_slice_coverage
                ],
            }
        )
        failures.append(f"side-wall coverage {pose.coverage:.3g} < {limits.min_slice_coverage}")
    if pose.rmse > limits.max_rmse_mm:
        notes.append({"kind": "rmse", "rmse_mm": pose.rmse})
        failures.append(f"rmse_mm {pose.rmse:.3g} > {limits.max_rmse_mm}")
    step = max(limits.spacing_mm, limits.voxel_mm)
    patch, patch_z = _miss_patch(other, pose.matrix, reference, query, limits, where=True)
    if patch > max(MISS_PATCH_MM2, 40 * step * step):
        notes.append({"kind": "patch", "area_mm2": patch, "z_mm": patch_z})
        failures.append(
            f"a {patch:.0f} mm^2 patch of side wall has no counterpart within "
            f"{limits.max_distance_mm:.1f} mm in the other scan (a local feature differs)"
        )
    # Yaw: accept only a yaw the wall profile pins, or a part shown to be round (any yaw fits).
    determined = pose.yaw_uncertainty <= limits.yaw_probe_deg and _yaw_unique(
        reference, other, pose.matrix, limits, pose.colour_resolved
    )
    if not determined and not (_is_round(reference, limits) and _is_round(other, limits)):
        rivals = _yaw_rivals(reference, other, pose.matrix, limits, pose.colour_resolved)
        turns = ", ".join(f"{t:.0f}" for t in rivals[:4] if np.isfinite(t))
        why = (
            f"the side wall fits turns of {turns} deg about as well"
            if turns
            else f"the wall fits within +-{pose.yaw_uncertainty:.1f} deg of yaw "
            f"(limit {limits.yaw_probe_deg:g})"
        )
        notes.append({"kind": "yaw", "rivals_deg": [t for t in rivals if np.isfinite(t)]})
        failures.append(
            f"yaw undetermined: {why} and the label print did not decide - rescan with the "
            "printed label or an asymmetric feature fully in view in both scans"
        )
    return failures, determined


FOOTPRINT_CELL_MM = 3.0


def _in_footprint(points: np.ndarray, cell: float) -> Callable[[np.ndarray], np.ndarray]:
    """Inside-test for the mat-frame xy footprint of ``points`` (``cell`` mm grid, grown by one
    cell). Cameras above the mat see the whole column outside a part's footprint as empty."""

    occupied = np.unique(np.floor(points[:, :2] / cell).astype(np.int64), axis=0)
    shifts = np.array([[dx, dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1)])
    grown = np.unique((occupied[:, None, :] + shifts).reshape(-1, 2), axis=0)
    keys = np.sort(grown[:, 0] * 2_000_003 + grown[:, 1])

    def inside(query: np.ndarray) -> np.ndarray:
        cells = np.floor(query[:, :2] / cell).astype(np.int64)
        flat = cells[:, 0] * 2_000_003 + cells[:, 1]
        slot = np.clip(np.searchsorted(keys, flat), 0, len(keys) - 1)
        return np.asarray(keys[slot] == flat)

    return inside


def _surface_coverage(points: np.ndarray, reference: _Part) -> dict[str, float]:
    """Occupied share of grid cells. side: 10 deg x 5 mm wall cells. top: footprint columns
    (30 deg x 5 mm rings) holding any point. bottom: columns also holding a second surface layer
    at least 2 mm below their highest point (an underside, flat or recessed).

    ponytail: assumes a roughly round footprint about the reference axis; a hole check on the
    reconstructed mesh replaces this once parts are meshed (PL-0484).
    """

    centre = _centre(reference.shell)
    rel = points[:, :2] - centre
    radius = np.linalg.norm(rel, axis=1)
    angle = ((np.arctan2(rel[:, 1], rel[:, 0]) + np.pi) / (2 * np.pi) * 36).astype(int) % 36
    outer = float(np.median(np.linalg.norm(reference.shell[:, :2] - centre, axis=1)))
    height = reference.height
    side = (radius > 0.8 * outer) & (points[:, 2] > 2) & (points[:, 2] < height - 2)
    side_cells = {(a, int(z // 5)) for a, z in zip(angle[side], points[side, 2], strict=True)}
    result = {"side": min(1.0, len(side_cells) / (36 * max(1, int((height - 4) // 5))))}
    rings = max(1, int((outer - 3) // 5))
    cap = radius < outer - 3
    column = (angle[cap] // 3) * 1000 + (radius[cap] // 5).astype(int)
    keys, inverse = np.unique(column, return_inverse=True)
    top, bottom = np.full(len(keys), -np.inf), np.full(len(keys), np.inf)
    np.maximum.at(top, inverse, points[cap, 2])
    np.minimum.at(bottom, inverse, points[cap, 2])
    span = top - bottom
    result["top"] = min(1.0, len(keys) / (12 * rings))
    result["bottom"] = min(1.0, int((span > 2.0).sum()) / (12 * rings))
    return result


# ---------------------------------------------------------------- public API


def _checked(
    reference: _Part,
    other: _Part,
    pose: _Pose,
    margin: float,
    query: Query,
    limits: AlignmentThresholds,
) -> ScanAlignment:
    limitations: list[str] = []
    failures, yaw_ok = _gate(reference, other, pose, query, limits, limitations)
    conflict = _conflict(reference, other, pose, limits)
    if failures:
        error = MultiScanAlignmentError(
            f"scan {other.scan_id} does not align to {reference.scan_id}: " + "; ".join(failures)
        )
        error.heights_mm = {reference.scan_id: reference.height, other.scan_id: other.height}
        error._context = (reference, other, pose, query, limits)  # type: ignore[attr-defined]
        raise error
    return ScanAlignment(
        other.scan_id,
        pose.matrix @ other.frame,
        pose.matrix,
        pose.flipped,
        pose.coverage,
        pose.rmse,
        margin,
        yaw_ok,
        conflict,
        pose.yaw_uncertainty,
        other.height,
        tuple(limitations),
    )


def check_alignment(
    reference: ScanInput,
    other: ScanInput,
    relative: np.ndarray,
    flipped: bool,
    limits: AlignmentThresholds = AlignmentThresholds(),
) -> ScanAlignment:
    """Run the acceptance gate on a given relative pose (e.g. a manual or stored alignment)."""

    ref, part = _prepare(reference, limits), _prepare(other, limits)
    limits = _adapt(limits, max(ref.spacing, part.spacing))
    query = _nearest(ref.shell)
    matrix = np.asarray(relative, dtype=float)
    coverage, rmse = _score(part, matrix, ref, query, limits)
    pose = _Pose(matrix, flipped, coverage, rmse)
    uncertainty = _yaw_sweep_fine(part, ref, query, pose, limits).yaw_uncertainty
    pose = replace(pose, yaw_uncertainty=uncertainty)
    return _checked(ref, part, pose, float("nan"), query, limits)


def align_scans(
    scans: list[ScanInput] | tuple[ScanInput, ...],
    limits: AlignmentThresholds = AlignmentThresholds(),
) -> MultiScanAlignment:
    """Register every scan to ``scans[0]`` in its mat frame (mm) and merge with scan ids.

    Check ``surface_coverage`` before treating the merge as closed; it is not hole-checked.
    """

    if len(scans) < 2:
        raise MultiScanAlignmentError("need at least two scans")
    ids = [scan.scan_id for scan in scans]
    if len(set(ids)) != len(ids):
        raise MultiScanAlignmentError("scan ids must be unique")
    parts = [_prepare(scan, limits) for scan in scans]
    limits = _adapt(limits, max(part.spacing for part in parts))
    reference = parts[0]
    query = _nearest(reference.shell)
    alignments = [
        ScanAlignment(
            ids[0],
            reference.frame,
            np.eye(4),
            False,
            1.0,
            0.0,
            float("nan"),
            True,
            height_mm=reference.height,
        )
    ]
    for index in range(1, len(scans)):
        roles = (scans[0].flipped, scans[index].flipped)
        flips = (False, True) if None in roles else (roles[0] != roles[1],)
        poses = sorted(
            (_pose_for_flip(parts[index], reference, query, f, limits) for f in flips),
            key=lambda pose: (pose.coverage, -pose.rmse),
            reverse=True,
        )
        if len(poses) == 2:  # a pose that puts surfaces into seen-empty space is no candidate
            free = [
                p
                for p in poses
                if _conflict(reference, parts[index], p, limits) <= limits.max_free_space_conflict
            ]
            poses = free or poses
        margin = float("nan")
        if len(poses) == 2:
            margin = poses[0].coverage - poses[1].coverage
            if margin < limits.ambiguity_margin:
                raise MultiScanAlignmentError(
                    f"scan {ids[index]}: role ambiguous (flip / no-flip score gap {margin:.3g} "
                    f"< {limits.ambiguity_margin}); set the scan role (PL-0482)"
                )
        alignments.append(_checked(reference, parts[index], poses[0], margin, query, limits))
    # Merge: first point per voxel wins (deterministic), keeping colour, scan and input row.
    # Left out: points outside another scan's footprint, where that scan saw only the mat (glare
    # blobs, fans). Surfaces one scan alone saw inside the footprint stay.
    moved = [_apply(a.relative, part.points) for a, part in zip(alignments, parts, strict=True)]
    keep = [np.ones(len(points), dtype=bool) for points in moved]
    for j, (a, part) in enumerate(zip(alignments, parts, strict=True)):
        inside = _in_footprint(part.points, FOOTPRINT_CELL_MM)
        for i, points in enumerate(moved):
            if i != j:
                keep[i] &= inside(_apply(np.linalg.inv(a.relative), points))
    merged = np.concatenate([points[k] for points, k in zip(moved, keep, strict=True)])
    source = np.concatenate([np.full(int(k.sum()), i) for i, k in enumerate(keep)])
    rows = np.concatenate([part.index[k] for part, k in zip(parts, keep, strict=True)])
    colors = None
    if all(scan.colors is not None for scan in scans):
        colors = np.concatenate(
            [
                np.asarray(s.colors)[part.index[k]]
                for s, part, k in zip(scans, parts, keep, strict=True)
            ]
        )
    first = _voxel_first(merged, limits.voxel_mm)
    return MultiScanAlignment(
        ids[0],
        tuple(alignments),
        merged[first],
        None if colors is None else colors[first],
        source[first],
        rows[first],
        _surface_coverage(merged[first], reference),
    )


def align_part_pair(
    upright: ScanInput,
    flipped: ScanInput,
    limits: AlignmentThresholds = AlignmentThresholds(),
    *,
    owner_confirmed: bool = False,
) -> MultiScanAlignment:
    """One part (body, closure or assembled): upright + upside-down scan -> one merged outside.

    A refusal on agreement gates only (``OVERRIDABLE``; scale within ``OVERRIDE_MAX_SCALE``)
    with a determined pose (RMSE within its limit, yaw pinned by the wall or the label) carries
    ``override_disagreements``. With ``owner_confirmed`` such a pair is merged anyway, each scan
    taken away from its own mat contact (``_owner_confirmed_merge``), and the result is marked
    ``OWNER_CONFIRMED_UNVERIFIED`` with the disagreements. Any other refusal stays a refusal.
    """

    scans = (replace(upright, flipped=False), replace(flipped, flipped=True))
    try:
        return align_scans(scans, limits)
    except MultiScanAlignmentError as error:
        context = getattr(error, "_context", None)
        if context is None:
            raise
        offer = _override_offer(*context)
        if offer is None:
            raise
        pose, details = offer
        if not owner_confirmed:
            error.override_disagreements = tuple(details)
            raise
        reference, other, _, query, adapted = context
        return _owner_confirmed_merge(reference, other, pose, query, adapted, tuple(details))


def disagreement_text(item: dict[str, Any]) -> str:
    """One measured disagreement in plain words (mm, mm^2)."""

    kind = item.get("kind")
    if kind == "section":
        a, b = item["reference_caliper_mm"], item["other_caliper_mm"]
        side = "inside" if item["offset_mm"] < 0 else "outside"
        return (
            f"section at {item['z_mm']:.0f} mm height: the upside-down scan's wall lies "
            f"{abs(item['offset_mm']):.1f} mm {side} the upright scan's ({b[0]:.1f} x {b[1]:.1f} "
            f"vs {a[0]:.1f} x {a[1]:.1f} mm; tolerance {item['tolerance_mm']:.1f} mm)"
        )
    if kind == "coverage":
        runs: list[list[float]] = []
        for lo, hi, _ in item.get("slices", []):
            if runs and lo - runs[-1][1] < 0.5:
                runs[-1][1] = hi
            else:
                runs.append([lo, hi])
        spans = ", ".join(f"{lo:.0f}-{hi:.0f} mm" for lo, hi in runs)
        return (
            f"the walls differ by more than 2 mm on a share of the wall at heights {spans} "
            f"(worst {100 * item['worst']:.0f} % within 2 mm, {100 * item['limit']:.0f} % needed)"
        )
    if kind == "patch":
        z = item.get("z_mm") or [float("nan")] * 2
        return (
            f"a {item['area_mm2']:.0f} mm^2 patch of wall at {z[0]:.0f}-{z[1]:.0f} mm height has "
            "no counterpart in the other scan"
        )
    if kind == "scale":
        return (
            f"the shared walls differ in size by {100 * (item['ratio'] - 1):+.2f} % "
            f"(limit {100 * item['limit']:.2f} %)"
        )
    return str(kind)


def _label_pose(
    reference: _Part, other: _Part, pose: _Pose, query: Query, limits: AlignmentThresholds
) -> _Pose | None:
    """Owner-confirmed path only. With wall-profile rivals: the yaw the printed label picks
    among them (same significance rules as ``_colour_yaw``), refined; None when the label does
    not decide. Without rivals: the pose with its yaw plateau re-measured on the mean slice
    coverage, so slices the scans disagree on at every yaw do not flatten it."""

    rivals = _yaw_rivals(reference, other, pose.matrix, limits)
    if not all(np.isfinite(rivals)):
        return None
    if not rivals:  # the wall profile pins the turn; only the coverage plateau was too wide
        swept = _yaw_sweep_fine(other, reference, query, pose, limits, mean=True)
        coverage, rmse = _score(other, swept.matrix, reference, query, limits)
        return replace(swept, coverage=coverage, rmse=rmse)
    curve = _texture_curve(other, pose.matrix, reference, limits)
    if curve is None:
        return None
    step = 360 / TEXTURE_AZIMUTH_BINS
    turns = [0.0, *rivals]
    index = np.arange(TEXTURE_AZIMUTH_BINS)
    near = np.zeros(TEXTURE_AZIMUTH_BINS, dtype=bool)
    scores = []
    for turn in turns:
        shift = round(turn / step) % TEXTURE_AZIMUTH_BINS
        gap = np.minimum(abs(index - shift), TEXTURE_AZIMUTH_BINS - abs(index - shift))
        near |= gap <= 10 / step
        window = curve[gap <= 1]
        scores.append(float(np.nanmax(window)) if np.isfinite(window).any() else -1.0)
    side = curve[~near & np.isfinite(curve)]
    if len(side) < 20:
        return None
    sigma, mean = float(side.std()), float(side.mean())
    pick = int(np.argmax(scores))
    others = [
        score
        for turn, score in zip(turns, scores, strict=True)
        if min(abs(turn - turns[pick]) % 360, 360 - abs(turn - turns[pick]) % 360) > 20
    ]
    margin = max(TEXTURE_MIN_MARGIN, TEXTURE_MARGIN_SIGMA * sigma)
    if scores[pick] < mean + TEXTURE_PEAK_SIGMA * sigma or (
        others and scores[pick] - max(others) < margin
    ):
        return None
    centre = np.r_[_centre(reference.shell), 0.0]
    matrix = _yaw(np.radians(turns[pick]), centre) @ pose.matrix
    matrix = _icp(
        other.shell, reference, query, matrix, [2, 3, 4], limits, limits.max_distance_mm, 1e-9
    )
    coverage, rmse = _score(other, matrix, reference, query, limits)
    picked = _Pose(matrix, pose.flipped, coverage, rmse, colour_resolved=True)
    swept = _yaw_sweep_fine(other, reference, query, picked, limits, mean=True)
    coverage, rmse = _score(other, swept.matrix, reference, query, limits)
    return replace(swept, coverage=coverage, rmse=rmse, colour_resolved=True)


def _override_offer(
    reference: _Part, other: _Part, pose: _Pose, query: Query, limits: AlignmentThresholds
) -> tuple[_Pose, list[dict[str, Any]]] | None:
    """(pose, measured disagreements) when only agreement gates refused a determined pose."""

    details: list[dict[str, Any]] = []
    _gate(reference, other, pose, query, limits, [], details)
    if any(item["kind"] == "yaw" for item in details):
        picked = _label_pose(reference, other, pose, query, limits)
        if picked is None:
            return None
        pose, details = picked, []
        _gate(reference, other, pose, query, limits, [], details)
    kinds = {item["kind"] for item in details}
    if not kinds or not kinds <= OVERRIDABLE:
        return None
    if any(
        item["kind"] == "scale" and abs(item["ratio"] - 1) > OVERRIDE_MAX_SCALE for item in details
    ):
        return None
    return pose, details


def _owner_confirmed_merge(
    reference: _Part,
    other: _Part,
    pose: _Pose,
    query: Query,
    limits: AlignmentThresholds,
    details: tuple[dict[str, Any], ...],
) -> MultiScanAlignment:
    """Merge for an owner-confirmed pair: each scan only away from its own mat contact. The
    upright ``reference`` gives everything above the band where the walls agree best (three
    5 mm slices around the highest smoothed slice coverage), the upside-down ``other``
    everything below it; both overlap in the band. So the upright closure and shoulder replace
    the upside-down scan's, and the upright foot gives way to the upside-down base."""

    profile = _slice_profile(other, pose.matrix, reference, query, limits)
    if not profile:
        raise MultiScanAlignmentError("no shared wall slices to blend the scans in")
    coverage = np.array([c for _, _, c in profile])
    smooth = np.convolve(coverage, np.ones(3), "same") / np.convolve(
        np.ones(len(coverage)), np.ones(3), "same"
    )
    middle = (len(coverage) - 1) / 2
    best = int(min(np.flatnonzero(smooth >= smooth.max() - 1e-9), key=lambda i: abs(i - middle)))
    z0, z1 = profile[max(best - 1, 0)][0], profile[min(best + 1, len(profile) - 1)][1]
    moved = _apply(pose.matrix, other.points)
    keep_ref = reference.points[:, 2] >= z0
    keep_other = moved[:, 2] <= z1
    inside_ref = _in_footprint(reference.points, FOOTPRINT_CELL_MM)
    inside_other = _in_footprint(other.points, FOOTPRINT_CELL_MM)
    keep_ref &= inside_other(_apply(np.linalg.inv(pose.matrix), reference.points))
    keep_other &= inside_ref(moved)
    merged = np.concatenate([reference.points[keep_ref], moved[keep_other]])
    source = np.r_[np.zeros(int(keep_ref.sum()), int), np.ones(int(keep_other.sum()), int)]
    rows = np.r_[reference.index[keep_ref], other.index[keep_other]]
    colors = None
    if reference.colors is not None and other.colors is not None:
        colors = np.concatenate([reference.colors[keep_ref], other.colors[keep_other]])
    first = _voxel_first(merged, limits.voxel_mm)
    limitations = (
        f"{OWNER_CONFIRMED_UNVERIFIED}: the owner confirmed both scans are the same part; "
        "the scans disagree (" + "; ".join(disagreement_text(d) for d in details) + ")",
        f"above {z0:.0f} mm from upright scan {reference.scan_id}, below {z1:.0f} mm from "
        f"upside-down scan {other.scan_id} (blended where the walls agree best, "
        f"{100 * smooth[best]:.0f} % within {limits.max_distance_mm:.1f} mm)",
    )
    alignments = (
        ScanAlignment(
            reference.scan_id,
            reference.frame,
            np.eye(4),
            False,
            1.0,
            0.0,
            float("nan"),
            True,
            height_mm=reference.height,
        ),
        ScanAlignment(
            other.scan_id,
            pose.matrix @ other.frame,
            pose.matrix,
            pose.flipped,
            pose.coverage,
            pose.rmse,
            float("nan"),
            True,
            _conflict(reference, other, pose, limits),
            pose.yaw_uncertainty,
            other.height,
            limitations,
        ),
    )
    return MultiScanAlignment(
        reference.scan_id,
        alignments,
        merged[first],
        None if colors is None else colors[first],
        source[first],
        rows[first],
        _surface_coverage(merged[first], reference),
        verification=OWNER_CONFIRMED_UNVERIFIED,
        disagreements=details,
    )
