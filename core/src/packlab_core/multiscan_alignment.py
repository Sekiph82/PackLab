"""Align scans of one physical part (upright + upside-down pairs, or N scans) in one metric frame.

Per scan (PL-0483): A4-mat frame in mm with +z up from the mat (caller ``to_mat_mm`` from the mat
markers, or a seeded RANSAC plane on a 2 mm voxel subsample plus ``mm_per_unit``), then an
iterative least-squares mat refit on the full cloud (absorbs small tilt / subsampling errors).
Object = points above ``mat_margin_mm``, largest DBSCAN cluster (drops floaters). Outer shell =
near-vertical points at the outer radius of their 5 degree x 5 mm cell (caps and interior surfaces
such as a closure recess are seen by one scan only and are never compared).

Registration to the reference (first) scan: 180 degree flip about a horizontal axis from the
PL-0482 role (both poses when unknown), height fixed by mat contact (flipped: mat side ->
reference top), yaw sweep with yaw + in-plane ICP, then damped tilt + yaw + in-plane
point-to-plane ICP bounded by ``max_refine_deg`` / ``max_refine_mm`` (height stays on the mat
contact, which side walls cannot observe). Poses are ranked by a symmetric score: the worst 5 mm
side-wall slice coverage over both directions (no raw one-way inlier share). With an unknown
role, a pose putting surfaces into space the other scan saw empty (free-space conflict) is
dropped, and if both poses remain within ``ambiguity_margin`` the scan is refused as role
ambiguous. Acceptance also compares both scans' height and diameter profile in their own mat
frames and the free-space conflict, so different objects, scale errors and wrong roles are
refused with the failed check named. Yaw of rotationally symmetric parts is flagged
(``yaw_determined=False``), not guessed silently. Deterministic (seeded RANSAC, exact
KNN, numpy solves). Metric values stay METRIC_UNVERIFIED until owner caliper evidence; tests use
synthetic proxies only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

import numpy as np

METHOD = "mat_frame_flip_yaw_sweep_bounded_tilt_point_to_plane_icp_v2"
METRIC_STATUS = "METRIC_UNVERIFIED"
PLANE_SEED = 7
PLANE_ITERATIONS = 1000
PROFILE_BANDS = 6
Query = Callable[..., tuple[np.ndarray, np.ndarray]]  # (points, k=1) -> (indices, distances)


class MultiScanAlignmentError(ValueError):
    """Raised when scans cannot be aligned reliably; the message names the failed check."""


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
    yaw_probe_deg: float = 5.0  # yaw_determined means pinned to within this
    yaw_symmetric_drop: float = 0.02  # largest slice coverage drop below which yaw is undetermined
    max_refine_deg: float = 5.0
    max_refine_mm: float = 5.0
    mat_margin_mm: float = 1.5
    plane_tolerance_mm: float = 1.0
    cluster_eps_mm: float = 3.0
    voxel_mm: float = 1.0
    slice_mm: float = 5.0
    yaw_steps: int = 12


@dataclass(frozen=True)
class ScanAlignment:
    scan_id: str
    matrix: np.ndarray  # 4x4 raw scan units -> reference mat frame mm
    relative: np.ndarray  # 4x4 rigid, this scan's mat frame mm -> reference mat frame mm
    flipped: bool  # relative to the reference scan (not the scan's own role)
    coverage: float  # worst side-wall slice coverage, both directions
    rmse_mm: float  # point-to-plane, worse direction
    pose_margin: float  # score gap to the other flip (nan: role known or other pose conflicted)
    yaw_determined: bool  # False: rotationally symmetric, yaw (label seam) is arbitrary
    free_space_conflict: float = 0.0  # see _free_space_conflict
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


@dataclass(frozen=True)
class _Pose:
    matrix: np.ndarray
    flipped: bool
    coverage: float
    rmse: float
    alternatives: tuple[np.ndarray, ...] = ()  # locally converged poses at other yaws


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
    return points


def _frame_from_plane(normal: np.ndarray, point: np.ndarray, foot_hint: np.ndarray) -> np.ndarray:
    helper = np.array([1.0, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1.0, 0])
    x_axis = helper - (helper @ normal) * normal
    x_axis /= np.linalg.norm(x_axis)
    rotation = np.stack([x_axis, np.cross(normal, x_axis), normal])
    foot = foot_hint - ((foot_hint - point) @ normal) * normal
    return _about(rotation, np.zeros(3), -rotation @ foot)


def _mat_frame(points_mm: np.ndarray, limits: AlignmentThresholds) -> np.ndarray:
    """Seeded RANSAC on a 2 mm voxel subsample; z up toward the side holding more points."""

    sample = points_mm[_voxel_first(points_mm, 2.0)]
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
    off = np.abs(heights) > 3 * tolerance
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


def _largest_cluster(points: np.ndarray, eps: float, voxel: float) -> np.ndarray:
    import open3d as o3d

    keys = np.floor(points / voxel).astype(np.int64)
    _, first, inverse = np.unique(keys, axis=0, return_index=True, return_inverse=True)
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points[first]))
    labels = np.asarray(cloud.cluster_dbscan(eps=eps, min_points=5))
    if labels.max(initial=-1) < 0:
        raise MultiScanAlignmentError("no connected object above the mat")
    biggest = int(np.argmax(np.bincount(labels[labels >= 0])))
    return np.asarray(labels[inverse.ravel()] == biggest)


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
    )


def _top(z: np.ndarray) -> float:
    """Robust height of the highest face (cluster-cleaned input)."""

    return float(np.median(z[z > np.percentile(z, 99.9) - 1.0]))


def _shell(
    points: np.ndarray, height: float, spacing: float, limits: AlignmentThresholds
) -> tuple[np.ndarray, np.ndarray]:
    """Outer side wall: band points with no other surface further out at the same place on the
    unrolled wall (arc x height window of 2.5 point spacings; removes recesses, inner walls and
    cap remnants). No angular grid, so the set does not depend on the mat frame's x axis.
    """

    band = points[(points[:, 2] > limits.mat_margin_mm + 2) & (points[:, 2] < height - 2)]
    band = band[_voxel_first(band, limits.voxel_mm)]
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
    index = above[_largest_cluster(mm[above], eps, limits.voxel_mm)]
    points = mm[index]
    height = _top(points[:, 2])
    try:
        shell, normals = _shell(points, height, spacing, limits)
    except MultiScanAlignmentError as error:
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: {error}") from None
    return _Part(scan.scan_id, frame, points, index, height, shell, normals, spacing)


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
    found_ab, d_ab = (array[:, 0] for array in query(moved))
    found_ba, d_ba = (array[:, 0] for array in _nearest(moved)(tgt))
    coverage: list[float] = []
    counts: list[int] = []
    for start, stop in zip(edges[:-1], edges[1:], strict=True):
        in_a = (moved[:, 2] >= start) & (moved[:, 2] < stop)
        in_b = (tgt[:, 2] >= start) & (tgt[:, 2] < stop)
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


def _pose_for_flip(
    source: _Part, target: _Part, query: Query, flipped: bool, limits: AlignmentThresholds
) -> _Pose:
    size = float(np.linalg.norm(np.ptp(target.shell, axis=0)))
    base = np.diag([1.0, -1.0, -1.0, 1.0]) if flipped else np.eye(4)  # 180 deg about mat x
    if flipped:
        base[2, 3] = target.height  # flipped scan's mat contact (z = 0) -> reference top face
    best: _Pose | None = None
    candidates = []
    for step in range(limits.yaw_steps):
        start = _yaw(2 * np.pi * step / limits.yaw_steps) @ base
        start[:2, 3] += _centre(target.shell) - _centre(_apply(start, source.shell))
        matrix = _icp(source.shell, target, query, start, [2, 3, 4], limits, 0.08 * size, 1e-9)
        coverage, rmse = _score(source, matrix, target, query, limits)
        candidates.append(matrix)
        if best is None or (coverage, -rmse) > (best.coverage, -best.rmse):
            best = _Pose(matrix, flipped, coverage, rmse)
    assert best is not None
    others = tuple(
        matrix
        for matrix in candidates
        if _angle_deg(matrix[:3, :3] @ best.matrix[:3, :3].T) > 2 * limits.yaw_probe_deg
    )
    best = replace(best, alternatives=others)
    # Fine yaw + in-plane pass, then tilt + yaw + in-plane. Height stays on the mat contact: side
    # walls do not observe it (a closure's short wall let free z slide 1.3 mm in testing). Tilt
    # is kept only within bounds and when it clearly fits better: a short wall (lid) barely
    # constrains tilt, and the levelled mat frames are the better tilt evidence there.
    fine = _icp(
        source.shell, target, query, best.matrix, [2, 3, 4], limits, limits.max_distance_mm, 1e-9
    )
    fine_coverage, fine_rmse = _score(source, fine, target, query, limits)
    if (fine_coverage, -fine_rmse) >= (best.coverage, -best.rmse):
        best = _Pose(fine, flipped, fine_coverage, fine_rmse, others)
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
    if rmse > 0.9 * best.rmse or coverage < best.coverage - 0.01:
        return best
    return _Pose(refined, flipped, coverage, rmse, others)


def _width(points: np.ndarray, z: float, half: float) -> float:
    band = points[np.abs(points[:, 2] - z) < half]
    if len(band) < 15:
        return float("nan")
    angles = np.linspace(0, np.pi, 8, endpoint=False)
    projected = band[:, :2] @ np.c_[np.cos(angles), np.sin(angles)].T
    low, high = np.percentile(projected, [1, 99], axis=0)
    return float(np.mean(high - low))


def _dimension_failures(
    reference: _Part, other: _Part, flipped: bool, limits: AlignmentThresholds
) -> list[str]:
    failures = []
    ratio = limits.dimension_tolerance_ratio
    tolerance = max(limits.height_tolerance_mm, ratio * reference.height)
    if abs(reference.height - other.height) > tolerance:
        failures.append(
            f"height mismatch {other.height:.1f} vs {reference.height:.1f} mm "
            f"(tolerance {tolerance:.1f})"
        )
    valid = seen_mine = seen_theirs = 0
    # Bands stay inside both shells (which span mat margin + 2 .. height - 2 in their own frames).
    half = max(2.0, limits.slice_mm / 2.5)
    lower = limits.mat_margin_mm + 2 + half
    upper = min(reference.height, other.height) - 2 - half
    heights = np.linspace(lower, upper, PROFILE_BANDS) if upper > lower else np.full(1, upper)
    for z in heights:
        mine = _width(reference.shell, z, half)
        theirs = _width(other.shell, other.height - z if flipped else z, half)
        seen_mine += int(not np.isnan(mine))
        seen_theirs += int(not np.isnan(theirs))
        if np.isnan(mine) or np.isnan(theirs):
            continue
        valid += 1
        tolerance = max(limits.width_tolerance_mm, ratio * mine)
        if abs(mine - theirs) > tolerance:
            failures.append(
                f"diameter mismatch at z={z:.0f} mm: {theirs:.1f} vs {mine:.1f} mm "
                f"(tolerance {tolerance:.1f})"
            )
    # Real MVS walls can be patchy: demand overlap in a share of the bands either scan has.
    needed = max(1, int(np.ceil(limits.min_profile_share * max(seen_mine, seen_theirs))))
    if valid < needed:
        failures.append(
            f"too little overlapping side wall ({valid} of {len(heights)} diameter bands, "
            f"need {needed})"
        )
    return failures


def _free_space_conflict(first: _Part, second: _Part, matrix: np.ndarray, cell: float) -> float:
    """Share of ``first`` points (moved by ``matrix`` into ``second``'s mat frame) lying over 2 mm
    above the highest surface ``second`` saw in the same column (``cell`` mm, >= 3). Cameras look down on the mat,
    so the space above a column's top was seen empty; a wrong flip puts e.g. a lid's flat top over
    its own visible recess. ponytail: ignores oblique views; a column the scan saw only partly can
    raise false conflicts, hence the tolerance share.
    """

    own = np.floor(second.points[:, :2] / cell).astype(np.int64)
    keys, inverse = np.unique(own, axis=0, return_inverse=True)
    top = np.full(len(keys), -np.inf)
    np.maximum.at(top, inverse.ravel(), second.points[:, 2])
    moved = _apply(matrix, first.points)
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


def _gate(
    reference: _Part, other: _Part, pose: _Pose, query: Query, limits: AlignmentThresholds
) -> tuple[list[str], bool]:
    failures = _dimension_failures(reference, other, pose.flipped, limits)
    conflict = _conflict(reference, other, pose, limits)
    if conflict > limits.max_free_space_conflict:
        failures.append(
            f"free-space conflict {conflict:.3g} > {limits.max_free_space_conflict} "
            "(surfaces where the other scan saw empty space: wrong role or different part)"
        )
    if pose.coverage < limits.min_slice_coverage:
        failures.append(f"side-wall coverage {pose.coverage:.3g} < {limits.min_slice_coverage}")
    if pose.rmse > limits.max_rmse_mm:
        failures.append(f"rmse_mm {pose.rmse:.3g} > {limits.max_rmse_mm}")
    # Yaw observability: does a small turn about the reference axis, or any locally converged
    # pose at another yaw, cost coverage in some wall slice? Sparse or symmetric parts do not.
    centre = np.r_[_centre(reference.shell), 0.0]
    base, _, fewest = _slices(other, pose.matrix, reference, query, limits)
    # A drop must beat binomial sampling noise of the sparsest slice (about 3 sigma).
    threshold = max(limits.yaw_symmetric_drop, 0.6 / np.sqrt(max(fewest, 1)))
    probes = [
        _yaw(sign * np.radians(limits.yaw_probe_deg), centre) @ pose.matrix for sign in (-1, 1)
    ]
    drops = []
    for matrix in (*probes, *pose.alternatives):
        probe = _slices(other, matrix, reference, query, limits)[0]
        if len(probe) == len(base) and len(base):
            drops.append(float((base - probe).max()))
        else:
            drops.append(float(base.mean() - probe.mean()) if len(probe) and len(base) else 1.0)
    return failures, min(drops) >= threshold


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
    failures, yaw_ok = _gate(reference, other, pose, query, limits)
    conflict = _conflict(reference, other, pose, limits)
    if failures:
        raise MultiScanAlignmentError(
            f"scan {other.scan_id} does not align to {reference.scan_id}: " + "; ".join(failures)
        )
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
    return _checked(ref, part, _Pose(matrix, flipped, coverage, rmse), float("nan"), query, limits)


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
        ScanAlignment(ids[0], reference.frame, np.eye(4), False, 1.0, 0.0, float("nan"), True)
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
    merged = np.concatenate(
        [_apply(a.relative, part.points) for a, part in zip(alignments, parts, strict=True)]
    )
    source = np.concatenate([np.full(len(part.index), i) for i, part in enumerate(parts)])
    rows = np.concatenate([part.index for part in parts])
    colors = None
    if all(scan.colors is not None for scan in scans):
        colors = np.concatenate(
            [np.asarray(s.colors)[part.index] for s, part in zip(scans, parts, strict=True)]
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
) -> MultiScanAlignment:
    """One part (body, closure or assembled): upright + upside-down scan -> one merged outside."""

    return align_scans((replace(upright, flipped=False), replace(flipped, flipped=True)), limits)
