"""Align scans of one physical part (upright + upside-down pairs, or N scans) in one metric frame.

Each scan is first brought into its own A4-mat frame (mm, +z up from the mat, PL-0483): either a
caller-supplied ``to_mat_mm`` 4x4 (Studio's ``upright_matrix(isolation, mm_per_unit)`` from the
mat markers) or a seeded RANSAC mat-plane fit plus ``mm_per_unit``. Points within
``mat_margin_mm`` of the mat are dropped (object isolation). Every other scan is then registered
to the first (reference) scan: the 180 degree flip about a horizontal axis (from the PL-0482 role,
or both poses when unknown) with the mat contact fixing height, a yaw sweep, then point-to-plane
ICP over yaw + in-plane shift (numpy solve, Open3D exact KNN; deterministic). Poor results raise
``MultiScanAlignmentError`` with the failed metric. Metric values stay METRIC_UNVERIFIED until
owner caliper evidence; tests use synthetic proxies only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

import numpy as np

METHOD = "mat_frame_flip_yaw_sweep_planar_point_to_plane_icp_v1"
METRIC_STATUS = "METRIC_UNVERIFIED"
PLANE_SEED = 7
PLANE_ITERATIONS = 1000
Query = Callable[..., tuple[np.ndarray, np.ndarray]]  # (points, k=1) -> (indices, distances)


class MultiScanAlignmentError(ValueError):
    """Raised when scans cannot be aligned reliably; the message names the failed check."""


@dataclass(frozen=True)
class ScanInput:
    scan_id: str
    points: np.ndarray  # (N, 3) reconstruction units
    colors: np.ndarray | None = None  # (N, 3) in [0, 1]
    to_mat_mm: np.ndarray | None = None  # 4x4 raw units -> mat frame mm (z up), if known
    mm_per_unit: float = 1.0  # used only when to_mat_mm is None
    # Captured upside-down (PL-0482 scan role). None = unknown: try both poses and keep the
    # better fit, which is ambiguous for top/bottom-symmetric parts - pass the role when known.
    flipped: bool | None = None


@dataclass(frozen=True)
class AlignmentThresholds:
    min_fitness: float = 0.2  # share of source points with a target point within max_distance
    min_overlap: float = 0.2  # min of source->target and target->source shares
    max_rmse_mm: float = 1.5
    max_distance_mm: float = 2.0  # ICP correspondence / inlier distance
    mat_margin_mm: float = 1.5
    plane_tolerance_mm: float = 1.0
    voxel_mm: float = 1.0
    yaw_steps: int = 12


@dataclass(frozen=True)
class ScanAlignment:
    scan_id: str
    matrix: np.ndarray  # 4x4 raw scan units -> reference mat frame mm
    relative: np.ndarray  # 4x4 rigid, this scan's mat frame mm -> reference mat frame mm
    flipped: bool
    fitness: float
    rmse_mm: float
    overlap: float


@dataclass(frozen=True)
class MultiScanAlignment:
    reference_id: str
    alignments: tuple[ScanAlignment, ...]  # reference first (identity relative)
    points: np.ndarray  # merged, voxel-downsampled, reference mat frame mm
    colors: np.ndarray | None
    source_index: np.ndarray  # per merged point: index into alignments
    method: str = METHOD
    metric_status: str = METRIC_STATUS


def _apply(matrix: np.ndarray, points: np.ndarray) -> np.ndarray:
    return np.asarray(points @ matrix[:3, :3].T + matrix[:3, 3])


def _mat_frame(points_mm: np.ndarray, tolerance: float) -> np.ndarray:
    """Seeded RANSAC on the dominant plane; returns 4x4 mm -> mat frame (z up toward object)."""

    rng = np.random.default_rng(PLANE_SEED)
    samples = points_mm[rng.integers(0, len(points_mm), (PLANE_ITERATIONS, 3))]
    normals = np.cross(samples[:, 1] - samples[:, 0], samples[:, 2] - samples[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    keep = lengths > 1e-9
    normals, samples = normals[keep] / lengths[keep, None], samples[keep]
    offsets = -np.einsum("ij,ij->i", normals, samples[:, 0])
    counts = [
        int((np.abs(points_mm @ n + d) < tolerance).sum())
        for n, d in zip(normals, offsets, strict=True)
    ]
    best = int(np.argmax(counts))
    inliers = points_mm[np.abs(points_mm @ normals[best] + offsets[best]) < tolerance]
    if len(inliers) < 30:
        raise MultiScanAlignmentError("no mat plane found in scan")
    centroid = inliers.mean(axis=0)
    normal = np.linalg.svd(inliers - centroid, full_matrices=False)[2][2]
    heights = (points_mm - centroid) @ normal
    off = np.abs(heights) > 3 * tolerance
    if (heights[off] > 0).sum() < (heights[off] < 0).sum():
        normal, heights = -normal, -heights
    above = points_mm[heights > 3 * tolerance]
    if len(above) < 30:
        raise MultiScanAlignmentError("nothing stands on the mat plane")
    helper = np.array([1.0, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1.0, 0])
    x_axis = helper - (helper @ normal) * normal
    x_axis /= np.linalg.norm(x_axis)
    rotation = np.stack([x_axis, np.cross(normal, x_axis), normal])
    foot = above.mean(axis=0)
    foot = foot - ((foot - centroid) @ normal) * normal
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = -rotation @ foot
    return matrix


def _to_mat_mm(scan: ScanInput, limits: AlignmentThresholds) -> np.ndarray:
    points = np.asarray(scan.points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 100:
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: needs an (N>=100, 3) point array")
    if not np.isfinite(points).all():
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: non-finite points")
    if scan.to_mat_mm is not None:
        return np.asarray(scan.to_mat_mm, dtype=float)
    if not (np.isfinite(scan.mm_per_unit) and scan.mm_per_unit > 0):
        raise MultiScanAlignmentError(f"scan {scan.scan_id}: mm_per_unit must be positive")
    scale = np.diag([scan.mm_per_unit] * 3 + [1.0])
    return _mat_frame(points * scan.mm_per_unit, limits.plane_tolerance_mm) @ scale


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


def _normals(points: np.ndarray, query: Query) -> np.ndarray:
    neighbours = points[query(points, 16)[0]]
    centred = neighbours - neighbours.mean(axis=1, keepdims=True)
    return np.asarray(np.linalg.eigh(np.einsum("nki,nkj->nij", centred, centred))[1][:, :, 0])


def _planar(params: np.ndarray, base: np.ndarray) -> np.ndarray:  # (yaw, tx, ty) after base
    yaw, tx, ty = params
    c, s = np.cos(yaw), np.sin(yaw)
    matrix = np.eye(4)
    matrix[:2, :2] = [[c, -s], [s, c]]
    matrix[:2, 3] = tx, ty
    return matrix @ base


def _register(
    source: np.ndarray,
    target: np.ndarray,
    limits: AlignmentThresholds,
    flips: tuple[bool, ...] = (False, True),
) -> tuple[np.ndarray, bool, float, float, float]:
    """Mat-constrained point-to-plane ICP: both clouds share the mat's +z, so only yaw and the
    in-plane shift are free; height is fixed by mat contact (flipped: mat side -> reference top).
    ponytail: tilt comes from the mat-plane fit only; add a tilt DOF if mat poses prove noisy.
    """

    src = source[_voxel_first(source, limits.voxel_mm)]
    tgt = target[_voxel_first(target, limits.voxel_mm)]
    query = _nearest(tgt)
    normals = _normals(tgt, query)
    size = float(np.linalg.norm(np.ptp(tgt, axis=0)))

    def top(z: np.ndarray) -> float:  # robust height of the highest face
        return float(np.median(z[z > np.percentile(z, 99.9) - 1.0]))

    best: tuple[float, float, np.ndarray, bool] | None = None
    for flipped in flips:
        base = np.diag([1.0, -1.0, -1.0, 1.0]) if flipped else np.eye(4)  # 180 deg about x
        if flipped:
            base[2, 3] = top(tgt[:, 2])  # flipped mat contact (z = 0) -> reference top face
        for step in range(limits.yaw_steps):
            yaw = 2 * np.pi * step / limits.yaw_steps
            shift = tgt[:, :2].mean(axis=0) - _apply(_planar(np.array([yaw, 0.0, 0.0]), base), src)[
                :, :2
            ].mean(0)
            params = np.array([yaw, *shift])
            for iteration in range(40):
                moved = _apply(_planar(params, base), src)
                found, distance = query(moved)
                limit = 0.08 * size if iteration < 15 else limits.max_distance_mm
                use = distance[:, 0] < limit
                if use.sum() < 10:
                    break
                p, n = moved[use], normals[found[use, 0]]
                residual = np.einsum("ij,ij->i", n, p - tgt[found[use, 0]])
                arm = p[:, :2] - params[1:]  # yaw acts about the current translation
                jacobian = np.c_[n[:, 1] * arm[:, 0] - n[:, 0] * arm[:, 1], n[:, 0], n[:, 1]]
                step_params = np.linalg.lstsq(jacobian, -residual, rcond=None)[0]
                params = params + step_params
                if iteration >= 15 and np.abs(step_params).max() < 1e-7:
                    break
            matrix = _planar(params, base)
            moved = _apply(matrix, src)
            found, distance = query(moved)
            inlier = distance[:, 0] < limits.max_distance_mm
            fitness = float(inlier.mean())
            hit = found[inlier, 0]  # point-to-plane residual: independent of sample spacing
            residual = np.einsum("ij,ij->i", normals[hit], moved[inlier] - tgt[hit])
            rmse = float(np.sqrt(np.mean(residual**2))) if inlier.any() else np.inf
            if best is None or (fitness, -rmse) > best[:2]:
                best = (fitness, -rmse, matrix, flipped)
    assert best is not None
    fitness, neg_rmse, matrix, flipped = best
    back = _nearest(_apply(matrix, src))(tgt)[1][:, 0] < limits.max_distance_mm
    return matrix, flipped, fitness, -neg_rmse, min(fitness, float(back.mean()))


def align_scans(
    scans: list[ScanInput] | tuple[ScanInput, ...],
    limits: AlignmentThresholds = AlignmentThresholds(),
) -> MultiScanAlignment:
    """Register every scan to ``scans[0]`` in its mat frame (mm) and merge with scan ids."""

    if len(scans) < 2:
        raise MultiScanAlignmentError("need at least two scans")
    ids = [scan.scan_id for scan in scans]
    if len(set(ids)) != len(ids):
        raise MultiScanAlignmentError("scan ids must be unique")
    frames = [_to_mat_mm(scan, limits) for scan in scans]
    objects = []
    for scan, frame in zip(scans, frames, strict=True):
        mm = _apply(frame, np.asarray(scan.points, dtype=float))
        keep = mm[:, 2] > limits.mat_margin_mm
        if keep.sum() < 100:
            raise MultiScanAlignmentError(f"scan {scan.scan_id}: under 100 points above the mat")
        objects.append((mm[keep], keep))
    alignments = [ScanAlignment(ids[0], frames[0], np.eye(4), False, 1.0, 0.0, 1.0)]
    for index in range(1, len(scans)):
        pair = (scans[0].flipped, scans[index].flipped)
        flips = (False, True) if None in pair else (pair[0] != pair[1],)
        relative, flipped, fitness, rmse, overlap = _register(
            objects[index][0], objects[0][0], limits, flips
        )
        failed = [
            f"{name} {value:.3g} {op} {bound:.3g}"
            for name, value, op, bound, bad in (
                ("fitness", fitness, "<", limits.min_fitness, fitness < limits.min_fitness),
                ("overlap", overlap, "<", limits.min_overlap, overlap < limits.min_overlap),
                ("rmse_mm", rmse, ">", limits.max_rmse_mm, rmse > limits.max_rmse_mm),
            )
            if bad
        ]
        if failed:
            raise MultiScanAlignmentError(
                f"scan {ids[index]} does not align to {ids[0]}: " + "; ".join(failed)
            )
        alignments.append(
            ScanAlignment(
                ids[index], relative @ frames[index], relative, flipped, fitness, rmse, overlap
            )
        )
    # Merge: first point per voxel wins (deterministic), keeping its colour and source scan.
    merged = np.concatenate(
        [_apply(a.relative, obj) for a, (obj, _) in zip(alignments, objects, strict=True)]
    )
    source = np.concatenate([np.full(len(obj), i) for i, (obj, _) in enumerate(objects)])
    colors = None
    if all(scan.colors is not None for scan in scans):
        colors = np.concatenate(
            [np.asarray(s.colors)[keep] for s, (_, keep) in zip(scans, objects, strict=True)]
        )
    first = _voxel_first(merged, limits.voxel_mm)
    return MultiScanAlignment(
        ids[0],
        tuple(alignments),
        merged[first],
        None if colors is None else colors[first],
        source[first],
    )


def align_part_pair(
    upright: ScanInput,
    flipped: ScanInput,
    limits: AlignmentThresholds = AlignmentThresholds(),
) -> MultiScanAlignment:
    """One part (body, closure or assembled): upright + upside-down scan -> one closed surface."""

    return align_scans((replace(upright, flipped=False), replace(flipped, flipped=True)), limits)
