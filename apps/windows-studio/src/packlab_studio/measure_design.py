"""Measure & Design glue: built model -> object-only -> scale/upright -> mm -> Scan Master -> Design Model.

Geometry primitives come from already-installed libraries (seeded numpy plane RANSAC, open3d DBSCAN,
OpenCV through ``calibration.marker_detection``). Every authority decision stays in core:
marker scale (``estimate_reconstruction_scale`` + ``create_scale_provenance``), dimensions
(``measure_bounding_dimensions``), uncertainty (``propagate_measurement_uncertainty``), the
report (``build_measurement_report``), cleanup (``cleanup_isolated_components``), Scan Master
promotion (``promote_scan_master``) and the revolved Design Model chain. Results stay
METRIC_UNVERIFIED with DEFERRED_OWNER_VALIDATION; nothing here claims physical accuracy.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from packlab_core.bounding_dimensions import (
    BoundingDimensions,
    NormalizedMeasurementGeometry,
    measure_bounding_dimensions,
)
from packlab_core.calibration.marker_association import (
    CameraImageBinding,
    associate_marker_detections,
)
from packlab_core.calibration.marker_detection import detect_markers
from packlab_core.calibration.reconstruction_scale import (
    PhysicalMarkerReference,
    ReconstructedMarkerGeometry,
    ReconstructionScaleObservation,
    estimate_reconstruction_scale,
)
from packlab_core.calibration.scale_provenance import (
    ScaleProvenance,
    create_scale_provenance,
)
from packlab_core.calibration.scale_provenance import _digest as _provenance_digest
from packlab_core.component_cleanup import ComponentCleanupError, cleanup_isolated_components
from packlab_core.coordinate_frame import NormalizedFrameTransform
from packlab_core.cross_section_overlay import CanonicalAxis
from packlab_core.design_dimensions import (
    DimensionAxis,
    create_overall_dimensions_revision,
    revise_overall_dimension,
)
from packlab_core.design_model import DesignModelRevision, PackageFamily
from packlab_core.design_profile_fit import (
    ProfileTransitionAnchor,
    ProfileTransitionKind,
    fit_design_profile,
)
from packlab_core.design_profile_zones import (
    detect_design_profile_zones,
    override_design_profile_zones,
)
from packlab_core.fitting_strategy import (
    FittingStrategy,
    FittingStrategyPolicy,
    PrincipalAxis,
    recommend_fitting_strategy,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.hole_detection import analyze_mesh_holes
from packlab_core.measurement_report import (
    MeasurementReport,
    MeasurementReportContext,
    build_measurement_report,
    render_measurement_report_markdown,
    serialize_measurement_report,
)
from packlab_core.measurement_uncertainty import (
    MeasurementUncertaintyInput,
    MeasurementUncertaintyReport,
    NormalizationScaleEvidence,
    propagate_measurement_uncertainty,
)
from packlab_core.normalization_transform import GeometryNormalizationTransform
from packlab_core.object_mask_lifting import (
    LiftThresholdProfile,
    LiftVisibilityPolicy,
    ObjectCaptureGeometry,
)
from packlab_core.reconstruction import (
    ReconstructionBackendId,
    ReconstructionOutputManifest,
    ScaleState,
)
from packlab_core.revolved_design_model import (
    RevolvedDesignModel,
    build_axisymmetric_revolved_design_model,
)
from packlab_core.scan_master import (
    CapturedScanLineage,
    CleanupOperationEvidence,
    CleanupOperationKind,
    ScanMasterRevision,
    mesh_sha256,
)
from packlab_core.scan_master_profile import extract_scan_master_vertical_profile

from .scan_master_promotion import ScanMasterPromotionRequest

ISOLATION_METHOD = "camera_lookat_base_plane_seeded_ransac_dbscan_cylinder_v2"
TARGET_FRAME = "packlab_right_handed_x_right_y_front_z_up_v1"
# A4 PackLab mat (assets/calibration/a4-packlab-calibration-mat.svg v1.0.1): AprilTag 36h11
# IDs 0-3, nominal outer black square 40 mm, 100 mm reference bar for print checks.
MAT_REFERENCE_ID = "packlab-a4-calibration-mat-v1.0.1"
MAT_MARKER_IDS = frozenset({0, 1, 2, 3})
MAT_MARKER_SIDE_MM = 40.0
MAT_REFERENCE_BAR_MM = 100.0
# Ruler reading of the printed side/bar; carried into the core reference uncertainty.
MAT_PRINT_UNCERTAINTY_MM = 0.25
CORNER_PIXEL_SIGMA = 0.5
MAX_MESH_TRIANGLES = 60_000
_COLMAP_PARAMS = {0: 3, 1: 4, 2: 4, 3: 5, 4: 8, 5: 8, 6: 12, 7: 5, 8: 4, 9: 5, 10: 12}


class MeasureDesignError(ValueError):
    """A pipeline step cannot run on the current inputs (message is owner-facing)."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_json(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _points3(points: np.ndarray) -> tuple[tuple[float, float, float], ...]:
    return tuple((float(x), float(y), float(z)) for x, y, z in points.tolist())


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------- loading


@dataclass(frozen=True)
class LoadedModel:
    path: Path
    sha256: str
    points: np.ndarray  # (N, 3) reconstruction units
    colors: np.ndarray | None  # (N, 3) in [0, 1]
    triangles: np.ndarray | None  # (M, 3) when the file is a mesh

    @property
    def reconstruction_revision(self) -> str:
        return f"reconstruction-{self.sha256[:40]}"


def load_model(path: Path) -> LoadedModel:
    import open3d as o3d

    path = Path(path)
    if not path.is_file():
        raise MeasureDesignError(f"{path.name} does not exist")
    is_mesh_format = path.suffix.lower() in {".obj", ".ply"}
    mesh = o3d.io.read_triangle_mesh(path) if is_mesh_format else None
    if mesh is not None and len(mesh.triangles) > 0:
        points = np.asarray(mesh.vertices, dtype=np.float64)
        colors = np.asarray(mesh.vertex_colors) if mesh.has_vertex_colors() else None
        triangles: np.ndarray | None = np.asarray(mesh.triangles, dtype=np.int64)
    else:
        cloud = o3d.io.read_point_cloud(path)
        points = np.asarray(cloud.points, dtype=np.float64)
        colors = np.asarray(cloud.colors) if cloud.has_colors() else None
        triangles = None
    if len(points) < 50 or not np.isfinite(points).all():
        raise MeasureDesignError(f"{path.name} has no usable geometry")
    return LoadedModel(path, _sha256_file(path), points, colors, triangles)


def companion_mesh_path(model_path: Path) -> Path | None:
    """OpenMVS writes the mesh beside the dense cloud; promotion needs triangles."""

    for name in (
        "scene_dense_mesh.ply",
        "scene_refined.ply",
        "scene_textured.obj",
        "scene_mesh.ply",
    ):
        candidate = Path(model_path).with_name(name)
        if candidate.is_file() and candidate != Path(model_path):
            return candidate
    return None


def latest_built_model(project_root: Path) -> Path | None:
    """Newest Build-model output in a project (dense cloud, else textured mesh)."""

    builds = Path(project_root) / "working" / "reconstruction"
    if not builds.is_dir():
        return None
    candidates = [
        path
        for pattern in ("*/outputs/mvs/scene_dense.ply", "*/outputs/mvs/scene_textured.obj")
        for path in builds.glob(pattern)
        if path.is_file()
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


# ---------------------------------------------------------------- COLMAP cameras


@dataclass(frozen=True)
class CameraPose:
    name: str
    rotation: np.ndarray  # world -> camera
    translation: np.ndarray
    fx: float
    fy: float
    cx: float
    cy: float
    width: int
    height: int

    @property
    def center(self) -> np.ndarray:
        return -self.rotation.T @ self.translation

    def ray(self, u: float, v: float) -> np.ndarray:
        direction = self.rotation.T @ np.array(
            [(u - self.cx) / self.fx, (v - self.cy) / self.fy, 1]
        )
        return direction / np.linalg.norm(direction)


def _quaternion_matrix(w: float, x: float, y: float, z: float) -> np.ndarray:
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
        ]
    )


def read_colmap_cameras(sparse_dir: Path) -> tuple[CameraPose, ...]:
    """Read binary COLMAP ``cameras.bin``/``images.bin``; only undistorted pinhole cameras."""

    intrinsics: dict[int, tuple[int, int, int, tuple[float, ...]]] = {}
    with (Path(sparse_dir) / "cameras.bin").open("rb") as handle:
        (count,) = struct.unpack("<Q", handle.read(8))
        for _ in range(count):
            camera_id, model_id, width, height = struct.unpack("<iiQQ", handle.read(24))
            size = _COLMAP_PARAMS.get(model_id)
            if size is None:
                raise MeasureDesignError(f"unsupported COLMAP camera model {model_id}")
            params = struct.unpack(f"<{size}d", handle.read(8 * size))
            intrinsics[camera_id] = (model_id, width, height, params)
    poses: list[CameraPose] = []
    with (Path(sparse_dir) / "images.bin").open("rb") as handle:
        (count,) = struct.unpack("<Q", handle.read(8))
        for _ in range(count):
            (_image_id,) = struct.unpack("<I", handle.read(4))
            quaternion = struct.unpack("<4d", handle.read(32))
            translation = struct.unpack("<3d", handle.read(24))
            (camera_id,) = struct.unpack("<I", handle.read(4))
            name = bytearray()
            while (byte := handle.read(1)) not in (b"\0", b""):
                name += byte
            (point_count,) = struct.unpack("<Q", handle.read(8))
            handle.seek(24 * point_count, 1)
            model_id, width, height, params = intrinsics[camera_id]
            if model_id == 0:
                fx = fy = params[0]
                cx, cy = params[1], params[2]
            elif model_id == 1:
                fx, fy, cx, cy = params[:4]
            else:
                continue  # distorted models: marker rays would be wrong without undistortion
            poses.append(
                CameraPose(
                    name.decode("utf-8"),
                    _quaternion_matrix(*quaternion),
                    np.array(translation),
                    fx,
                    fy,
                    cx,
                    cy,
                    int(width),
                    int(height),
                )
            )
    return tuple(poses)


def find_colmap_workspace(model_path: Path) -> tuple[Path, Path] | None:
    """Locate (undistorted images dir, pinhole sparse dir) of an OpenMVS/COLMAP build."""

    model_path = Path(model_path)
    for root in (model_path.parent, model_path.parent.parent):
        for images, sparse in (
            (root / "dense" / "images", root / "dense" / "sparse"),
            (root / "images", root / "sparse"),
        ):
            if images.is_dir() and (sparse / "images.bin").is_file():
                return images, sparse
    return None


def camera_look_at(cameras: tuple[CameraPose, ...]) -> np.ndarray | None:
    """Least-squares point closest to every optical axis (where the photographer aimed)."""

    if len(cameras) < 3:
        return None
    system = np.zeros((3, 3))
    rhs = np.zeros(3)
    for camera in cameras:
        axis = camera.rotation[2]
        projector = np.eye(3) - np.outer(axis, axis)
        system += projector
        rhs += projector @ camera.center
    if np.linalg.cond(system) > 1e8:
        return None
    return np.asarray(np.linalg.solve(system, rhs))


# ---------------------------------------------------------------- 1. object only


@dataclass(frozen=True)
class Isolation:
    normal: np.ndarray  # unit, pointing from the support plane toward the object
    offset: float  # plane: dot(normal, p) + offset == 0
    center: np.ndarray  # object axis foot point on the plane
    radius: float  # object footprint radius (reconstruction units)
    top: float  # object top height above the plane
    tolerance: float  # plane inlier tolerance
    plane_rms: float
    object_indices: np.ndarray
    method: str
    notes: tuple[str, ...]

    def heights(self, points: np.ndarray) -> np.ndarray:
        return np.asarray(points @ self.normal + self.offset)

    def region_mask(self, points: np.ndarray) -> np.ndarray:
        heights = self.heights(points)
        relative = points - self.center
        horizontal = relative - np.outer(relative @ self.normal, self.normal)
        radial = np.linalg.norm(horizontal, axis=1)
        return np.asarray(
            (heights > 0.5 * self.tolerance)
            & (heights < self.top + 2 * self.tolerance)
            & (radial < self.radius * 1.06)
        )


PLANE_RANSAC_SEED = 7
PLANE_RANSAC_ITERATIONS = 2000


def _fit_plane(points: np.ndarray, tolerance: float) -> tuple[np.ndarray, float, np.ndarray]:
    """Seeded 3-point RANSAC plane + least-squares refit on its inliers.

    Replaces open3d ``segment_plane``, whose multi-threaded sampling gave a different plane on
    each run of the same file (PL-0462). Same input -> same plane, bit for bit.
    """

    rng = np.random.default_rng(PLANE_RANSAC_SEED)
    samples = points[rng.integers(0, len(points), (PLANE_RANSAC_ITERATIONS, 3))]
    normals = np.cross(samples[:, 1] - samples[:, 0], samples[:, 2] - samples[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    valid = lengths > 1e-12
    normals, samples = normals[valid] / lengths[valid, None], samples[valid]
    offsets = -np.einsum("ij,ij->i", normals, samples[:, 0])
    best_count, best = -1, 0
    for start in range(0, len(normals), 100):  # 100 planes x N points per batch
        counts = (
            np.abs(points @ normals[start : start + 100].T + offsets[start : start + 100])
            < tolerance
        ).sum(axis=0)
        index = int(np.argmax(counts))
        if counts[index] > best_count:
            best_count, best = int(counts[index]), start + index
    inliers = np.nonzero(np.abs(points @ normals[best] + offsets[best]) < tolerance)[0]
    if len(inliers) < 3:
        return normals[best], float(offsets[best]), inliers
    centroid = points[inliers].mean(axis=0)
    normal = np.linalg.svd(points[inliers] - centroid, full_matrices=False)[2][2]
    return normal, float(-normal @ centroid), inliers


def isolate_object(model: LoadedModel, cameras: tuple[CameraPose, ...] = ()) -> Isolation:
    """Base plane + cluster above the plane nearest the object centre.

    Without camera poses the object centre falls back to the point-cloud median and "up" to
    the plane side holding more off-plane points.
    """

    import open3d as o3d

    points = model.points
    look_at = camera_look_at(cameras)
    notes: list[str] = []
    if look_at is not None:
        scale = float(np.median([np.linalg.norm(c.center - look_at) for c in cameras]))
        anchor = look_at
        notes.append(f"object centre from {len(cameras)} camera optical axes")
    else:
        extent = np.ptp(points, axis=0)
        scale = float(np.linalg.norm(extent)) * 0.5
        anchor = np.median(points, axis=0)
        notes.append("no camera poses: object centre = cloud median")
    near = np.nonzero(np.linalg.norm(points - anchor, axis=1) < 0.6 * scale)[0]
    if len(near) < 50:
        near = np.arange(len(points))
    tolerance = 0.005 * scale
    normal, offset, inliers = _fit_plane(points[near], tolerance)
    if len(inliers) < 30:
        raise MeasureDesignError("no support plane (table/mat) found under the object")
    heights = points[near] @ normal + offset
    if cameras:
        up_vote = float(np.median([c.center @ normal + offset for c in cameras]))
    else:
        band = (np.abs(heights) > 3 * tolerance) & (np.abs(heights) < 0.5 * scale)
        up_vote = float(np.sum(heights[band] > 0) - np.sum(heights[band] < 0))
    if up_vote < 0:
        normal, offset, heights = -normal, -offset, -heights
    plane_rms = float(np.sqrt(np.mean(heights[np.asarray(inliers)] ** 2)))
    foot = anchor - (anchor @ normal + offset) * normal

    def radial(values: np.ndarray, centre: np.ndarray) -> np.ndarray:
        relative = values - centre
        return np.asarray(np.linalg.norm(relative - np.outer(relative @ normal, normal), axis=1))

    candidate = near[
        (heights > 2 * tolerance)
        & (heights < 0.6 * scale)
        & (radial(points[near], foot) < 0.4 * scale)
    ]
    if len(candidate) < 30:
        raise MeasureDesignError("nothing stands on the support plane near the object centre")
    sub = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points[candidate]))
    labels = np.asarray(sub.cluster_dbscan(eps=0.02 * scale, min_points=10))
    best: np.ndarray | None = None
    best_score = -1.0
    for label in range(int(labels.max()) + 1 if len(labels) else 0):
        members = candidate[labels == label]
        if len(members) < 30:
            continue
        distance = float(np.median(radial(points[members], foot)))
        score = len(members) / (1.0 + (distance / (0.1 * scale)) ** 2)
        if score > best_score:
            best, best_score = members, score
    if best is None:
        raise MeasureDesignError("no object cluster above the support plane")
    notes.append(f"support plane {len(inliers):,} inliers, rms {plane_rms:.4g} units")
    return _axis_isolation(points, best, normal, offset, foot, tolerance, plane_rms, notes)


def _axis_isolation(
    points: np.ndarray,
    best: np.ndarray,
    normal: np.ndarray,
    offset: float,
    foot: np.ndarray,
    tolerance: float,
    plane_rms: float,
    notes: list[str],
    method: str = ISOLATION_METHOD,
) -> Isolation:
    """Axis, footprint radius and top of the object cluster ``best`` standing on the plane."""

    def radial(values: np.ndarray, centre: np.ndarray) -> np.ndarray:
        relative = values - centre
        return np.asarray(np.linalg.norm(relative - np.outer(relative @ normal, normal), axis=1))

    # Axis centre: middle of the robust footprint extent along two in-plane directions.
    helper = np.array([1.0, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1.0, 0])
    x_axis = np.cross(normal, helper)
    x_axis /= np.linalg.norm(x_axis)
    y_axis = np.cross(normal, x_axis)
    cluster = points[best]
    u, v = (cluster - foot) @ x_axis, (cluster - foot) @ y_axis
    center = (
        foot
        + x_axis * (np.percentile(u, 1) + np.percentile(u, 99)) / 2
        + y_axis * (np.percentile(v, 1) + np.percentile(v, 99)) / 2
    )
    top = float(np.percentile(cluster @ normal + offset, 99.5))
    # A partly observed side wall biases that midpoint toward the seen side (2-3 mm on
    # test-333), so prefer a robust circle through the side band when the wall is round.
    side = (cluster @ normal + offset >= 0.15 * top) & (cluster @ normal + offset < 0.85 * top)
    if side.sum() >= 30:
        uv = np.c_[(cluster[side] - foot) @ x_axis, (cluster[side] - foot) @ y_axis]
        circle, circle_radius, fraction = _robust_circle(uv)
        fitted = foot + x_axis * circle[0] + y_axis * circle[1]
        footprint = float(np.percentile(radial(cluster, center), 99))
        shift = float(np.linalg.norm(fitted - center))
        if fraction >= 0.6 and shift <= 0.15 * footprint and circle_radius <= 1.2 * footprint:
            center = fitted
            notes.append(f"axis from a robust side-wall circle ({fraction:.0%} inliers)")
        else:
            notes.append("axis from the footprint extent (side wall not a clear circle)")
    radius = float(np.percentile(radial(cluster, center), 99))
    isolation = Isolation(
        normal,
        offset,
        center,
        radius,
        top,
        tolerance,
        plane_rms,
        np.array([]),
        method,
        (),
    )
    indices = np.nonzero(isolation.region_mask(points))[0]
    notes.append(f"object cluster {len(best):,} points, kept {len(indices):,} in its footprint")
    return Isolation(
        normal,
        offset,
        center,
        radius,
        top,
        tolerance,
        plane_rms,
        indices,
        method,
        tuple(notes),
    )


# ---------------------------------------------------------------- 2. scale


@dataclass(frozen=True)
class ScaleResult:
    mm_per_unit: float
    uncertainty: float  # standard uncertainty, mm per reconstruction unit
    source: str  # "mat_markers" | "manual_reference"
    provenance: ScaleProvenance
    details: str


def mat_reference(
    print_correction: float, evidence_class: str
) -> dict[int, PhysicalMarkerReference]:
    side = MAT_MARKER_SIDE_MM * print_correction
    digest = _sha256_json(
        {
            "reference_id": MAT_REFERENCE_ID,
            "nominal_side_mm": MAT_MARKER_SIDE_MM,
            "print_correction": print_correction,
        }
    )
    return {
        marker_id: PhysicalMarkerReference(
            marker_id,
            MAT_REFERENCE_ID,
            digest,
            side,
            "mm",
            MAT_PRINT_UNCERTAINTY_MM * MAT_MARKER_SIDE_MM / MAT_REFERENCE_BAR_MM + 0.05,
            evidence_class,
        )
        for marker_id in MAT_MARKER_IDS
    }


def _read_image(path: Path) -> np.ndarray | None:
    import cv2

    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return image if image is not None else None


def estimate_marker_scale(
    model: LoadedModel,
    isolation: Isolation,
    cameras: tuple[CameraPose, ...],
    images_dir: Path,
    camera_solution_revision: str,
    *,
    print_correction: float = 1.0,
    # The owner's print is not caliper-verified; only an explicit owner-verified print
    # record may pass accepted_owner_physical (the class METRIC_VERIFIED promotion needs).
    evidence_class: str = "owner_unverified_print",
) -> ScaleResult:
    """Detect mat markers per photo, cast corners onto the base plane, let core fit scale."""

    if not 0.8 <= print_correction <= 1.2:
        raise MeasureDesignError("print correction must be between 0.8 and 1.2")
    references = mat_reference(print_correction, evidence_class)
    observations: list[ReconstructionScaleObservation] = []
    images_seen = 0
    detection_errors: set[str] = set()
    for camera in cameras:
        path = Path(images_dir) / camera.name
        if not path.is_file():
            continue
        image = _read_image(path)
        if image is None:
            continue
        images_seen += 1
        batch = detect_markers(image)
        if batch.status not in {"detected", "no_markers"}:
            detection_errors.update(batch.errors or (batch.status,))
            continue
        digest = _sha256_file(path)
        binding = CameraImageBinding(
            camera.name, camera.name, digest, camera.width, camera.height, camera_solution_revision
        )
        associated = associate_marker_detections(
            batch,
            source_image_asset_id=camera.name,
            source_digest=digest,
            image_width=int(image.shape[1]),
            image_height=int(image.shape[0]),
            camera_solution_revision=camera_solution_revision,
            cameras=(binding,),
        )
        center = camera.center
        for item in associated:
            if item.marker_id not in references:
                continue
            corners = []
            for u, v in item.corners_px:
                direction = camera.ray(u, v)
                denominator = float(direction @ isolation.normal)
                if abs(denominator) < 0.15:  # grazing view: plane hit is unstable
                    break
                distance = -(float(center @ isolation.normal) + isolation.offset) / denominator
                if distance <= 0:
                    break
                corners.append(tuple(float(value) for value in center + distance * direction))
            if len(corners) != 4:
                continue
            depth = float(np.linalg.norm(np.asarray(corners[0]) - center))
            observations.append(
                ReconstructionScaleObservation(
                    references[item.marker_id],
                    ReconstructedMarkerGeometry(
                        item,
                        model.reconstruction_revision,
                        "reconstruction_units",
                        tuple(corners),  # type: ignore[arg-type]
                        max(depth * CORNER_PIXEL_SIGMA / camera.fx, 1e-9),
                    ),
                )
            )
    if detection_errors:
        raise MeasureDesignError(
            "marker detection unavailable: " + ", ".join(sorted(detection_errors))
        )
    estimate = estimate_reconstruction_scale(
        tuple(observations),
        reconstruction_revision=model.reconstruction_revision,
        camera_solution_revision=camera_solution_revision,
    )
    if estimate.status != "estimated" or estimate.reconstruction_units_to_mm is None:
        raise MeasureDesignError(
            f"mat markers not usable ({len(observations)} marker views in {images_seen} photos; "
            f"{', '.join(estimate.errors)}). Use a manual reference length."
        )
    provenance = create_scale_provenance(
        estimate,
        tuple(observations),
        reconstruction_revision=model.reconstruction_revision,
        camera_solution_revision=camera_solution_revision,
        created_at_utc=_now(),
        actor_id="packlab-studio",
        process_id="measure-design-marker-scale",
    )
    assert estimate.uncertainty_mm_per_reconstruction_unit is not None
    return ScaleResult(
        estimate.reconstruction_units_to_mm,
        estimate.uncertainty_mm_per_reconstruction_unit,
        "mat_markers",
        provenance,
        f"{len(estimate.observations_used)} of {len(observations)} marker views agree "
        f"({images_seen} photos, print correction {print_correction:.4f})",
    )


def manual_scale(
    model: LoadedModel,
    point_a: tuple[float, float, float],
    point_b: tuple[float, float, float],
    known_mm: float,
    *,
    known_mm_uncertainty: float = 0.5,
) -> ScaleResult:
    """Owner-entered reference: two model points and their real distance in mm."""

    length = float(np.linalg.norm(np.subtract(point_b, point_a)))
    if not math.isfinite(known_mm) or known_mm <= 0 or not math.isfinite(length) or length <= 0:
        raise MeasureDesignError(
            "manual reference needs two distinct points and a positive mm length"
        )
    factor = known_mm / length
    uncertainty = factor * known_mm_uncertainty / known_mm
    identity: dict[str, object] = {
        "contract": "packlab.scale-provenance.v1",
        "version": "scale_provenance_v1",
        "source_method": "manual_two_point_reference",
        "calibration_observation_ids": [],
        "physical_references": [
            {
                "reference_id": "owner-entered-two-point-length",
                "point_a": list(point_a),
                "point_b": list(point_b),
                "value": known_mm,
                "unit": "mm",
                "uncertainty_mm": known_mm_uncertainty,
                "evidence_class": "owner_entered_unverified",
            }
        ],
        "estimated_scale_factor": factor,
        "scale_factor_unit": "mm_per_reconstruction_unit",
        "residuals": [],
        "rejected_observations": [],
        "algorithm_version": "manual_two_point_reference_v1",
        "outlier_policy_version": "none_single_reference_v1",
        "input_reconstruction_revision": model.reconstruction_revision,
        "camera_solution_revision": "manual-reference",
        "uncertainty": {
            "representation": "standard_uncertainty_mm_per_reconstruction_unit",
            "value": uncertainty,
        },
        "created_at_utc": _now(),
        "actor_process_provenance": {"actor_id": "packlab-studio", "process_id": "manual-scale"},
        "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        "promotion_evidence": None,
        "ai_visual_reference_measurement_authority": False,
    }
    provenance = ScaleProvenance(
        "scale-provenance:" + _provenance_digest(identity),
        "manual_two_point_reference",
        (),
        tuple(identity["physical_references"]),  # type: ignore[arg-type]
        factor,
        (),
        (),
        "manual_two_point_reference_v1",
        "none_single_reference_v1",
        model.reconstruction_revision,
        "manual-reference",
        dict(identity["uncertainty"]),  # type: ignore[call-overload]
        str(identity["created_at_utc"]),
        "packlab-studio",
        "manual-scale",
        ScaleState.METRIC_UNVERIFIED,
    )
    return ScaleResult(
        factor,
        uncertainty,
        "manual_reference",
        provenance,
        f"{known_mm:g} mm over {length:.5g} units",
    )


# ---------------------------------------------------------------- combined parts (PL-0485)

PART_FRAME_METHOD = "part_combine_mat_frame_z_up_axis_v1"
PART_FRAME_TOLERANCE_MM = 0.5


def isolate_in_mat_frame(model: LoadedModel) -> Isolation:
    """A combined part cloud is already levelled in the mat frame (mm, mat at z = 0).

    The merge holds only the object (PL-0483 drops the mat and clutter), so the support
    plane is known: no plane search, the object is every point above z = 0.
    """

    normal = np.array([0.0, 0.0, 1.0])
    points = model.points
    best = np.nonzero(points[:, 2] > PART_FRAME_TOLERANCE_MM)[0]
    if len(best) < 30:
        raise MeasureDesignError("the combined part cloud has nothing above the mat plane")
    foot = np.r_[np.median(points[best, :2], axis=0), 0.0]
    notes = ["combined part: mat frame known from the combine (z up, mat at z = 0)"]
    return _axis_isolation(
        points, best, normal, 0.0, foot, PART_FRAME_TOLERANCE_MM, 0.0, notes, PART_FRAME_METHOD
    )


def part_combine_scale(model: LoadedModel, record: dict[str, Any]) -> ScaleResult:
    """Scale of a combined part: already mm; provenance = each source build's own scale."""

    sources = record.get("sources")
    if record.get("status") != "combined" or not isinstance(sources, list) or len(sources) < 2:
        raise MeasureDesignError("not a combined part record")
    relative = []
    for source in sources:
        factor, uncertainty = source.get("mm_per_unit"), source.get("scale_uncertainty")
        if not isinstance(factor, float | int) or not isinstance(uncertainty, float | int):
            raise MeasureDesignError(
                "the combine did not record each scan's scale uncertainty; combine the part again"
            )
        relative.append(float(uncertainty) / float(factor))
    uncertainty = max(relative)  # mm per mm: the worse source scale bounds the merge
    references = tuple(
        {
            "reference_id": f"part-combine-{source.get('view')}",
            "package_sha256": source.get("package_sha256"),
            "model_sha256": source.get("model_sha256"),
            "mm_per_unit": source.get("mm_per_unit"),
            "scale_source": source.get("scale_source"),
            "uncertainty_mm_per_unit": source.get("scale_uncertainty"),
            "evidence_class": "source_build_scale_unverified",
        }
        for source in sources
    )
    identity: dict[str, Any] = {
        "contract": "packlab.scale-provenance.v1",
        "version": "scale_provenance_v1",
        "source_method": "part_combine",
        "calibration_observation_ids": [],
        "physical_references": list(references),
        "estimated_scale_factor": 1.0,
        "scale_factor_unit": "mm_per_reconstruction_unit",
        "residuals": [],
        "rejected_observations": [],
        "algorithm_version": str(record.get("method")),
        "outlier_policy_version": "multiscan_alignment_gate_v1",
        "input_reconstruction_revision": model.reconstruction_revision,
        "camera_solution_revision": f"part-combine-{str(record.get('file_sha256'))[:40]}",
        "uncertainty": {
            "representation": "standard_uncertainty_mm_per_reconstruction_unit",
            "value": uncertainty,
        },
        "created_at_utc": _now(),
        "actor_process_provenance": {"actor_id": "packlab-studio", "process_id": "part-combine"},
        "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        "promotion_evidence": None,
        "ai_visual_reference_measurement_authority": False,
    }
    provenance = ScaleProvenance(
        "scale-provenance:" + _provenance_digest(identity),
        "part_combine",
        (),
        references,
        1.0,
        (),
        (),
        identity["algorithm_version"],
        identity["outlier_policy_version"],
        model.reconstruction_revision,
        identity["camera_solution_revision"],
        dict(identity["uncertainty"]),
        str(identity["created_at_utc"]),
        "packlab-studio",
        "part-combine",
        ScaleState.METRIC_UNVERIFIED,
    )
    return ScaleResult(
        1.0,
        uncertainty,
        "part_combine",
        provenance,
        "combined part in mat-frame mm; scale from "
        + ", ".join(f"{s.get('view')} {s.get('scale_source')}" for s in sources),
    )


# ---------------------------------------------------------------- upright frame


@dataclass(frozen=True)
class Frame:
    """Reconstruction units -> PackLab normalized mm frame (z up from the base plane)."""

    matrix: np.ndarray  # 4x4, p_mm = M @ [p, 1]
    transform: GeometryNormalizationTransform
    geometry: ObjectCaptureGeometry
    scale: ScaleResult

    def apply(self, points: np.ndarray) -> np.ndarray:
        return np.asarray(points @ self.matrix[:3, :3].T + self.matrix[:3, 3])


def upright_matrix(isolation: Isolation, factor: float = 1.0) -> np.ndarray:
    """4x4 rigid+uniform-scale map: axis foot -> origin, plane normal -> +z (right-handed)."""

    up = isolation.normal
    helper = np.array([1.0, 0, 0]) if abs(up[0]) < 0.9 else np.array([0, 1.0, 0])
    x_axis = helper - (helper @ up) * up
    x_axis /= np.linalg.norm(x_axis)
    rotation = np.stack([x_axis, np.cross(up, x_axis), up])
    matrix = np.eye(4)
    matrix[:3, :3] = factor * rotation
    matrix[:3, 3] = -factor * rotation @ isolation.center
    return matrix


def build_frame(
    model: LoadedModel, isolation: Isolation, scale: ScaleResult, *, project_id: str
) -> Frame:
    matrix = upright_matrix(isolation, scale.mm_per_unit)
    object_points = _points3(model.points[isolation.object_indices])
    geometry_digest = _sha256_json(
        {
            "model": model.sha256,
            "method": isolation.method,
            "normal": isolation.normal.tolist(),
            "offset": isolation.offset,
            "center": isolation.center.tolist(),
            "radius": isolation.radius,
            "top": isolation.top,
        }
    )
    geometry = ObjectCaptureGeometry(
        geometry_id=f"object-geometry-{geometry_digest[:40]}",
        project_id=project_id,
        source_revision=f"built-model-{model.sha256[:40]}",
        source_input_digest=model.sha256,
        source_images=(),
        source_mask_artifacts=(),
        camera_conventions=(),
        camera_evidence=(),
        reconstruction_revision=model.reconstruction_revision,
        camera_solution_revision=scale.provenance.camera_solution_revision,
        mask_set_revision_id=f"geometric-isolation-{geometry_digest[:32]}",
        mask_set_revision_digest=geometry_digest,
        projection_convention=isolation.method,
        projection_version="v1",
        threshold_profile=LiftThresholdProfile(),
        visibility_policy=LiftVisibilityPolicy(),
        outlier_policy="dbscan_cluster_plus_footprint_cylinder_v1",
        candidate_count=len(model.points),
        point_count=len(object_points),
        generated=False,
        authority_class="OBJECT_CAPTURE_GEOMETRY",
        scale_state=ScaleState.RELATIVE,
        point_votes=(),
        filtered_points=object_points,
        unfiltered_points=object_points,
        obb=None,
        created_at=_now(),
    )
    flat = tuple(float(value) for value in matrix.reshape(-1))
    frame_id = f"normalization-{_sha256_json([flat, scale.provenance.provenance_id])[:40]}"
    transform = GeometryNormalizationTransform(
        NormalizedFrameTransform(
            transform_id=frame_id,
            source_frame="captured-object-reconstruction-v1",
            target_frame=TARGET_FRAME,
            reconstruction_revision=model.reconstruction_revision,
            scale_state=ScaleState.METRIC_UNVERIFIED,
            input_unit="reconstruction_units",
            coordinate_unit="mm_unverified",
            matrix=flat,
            method=f"{isolation.method}+{scale.source}",
            scale_provenance_id=scale.provenance.provenance_id,
        ),
        geometry.geometry_id,
        _sha256_json(scale.provenance.as_dict()),
        scale.mm_per_unit,
        scale.uncertainty,
        f"base-plane-{geometry_digest[:24]}",
        f"upright-plane-normal-{geometry_digest[:24]}",
        "front-arbitrary-x",
        ScaleState.RELATIVE,
    )
    return Frame(matrix, transform, geometry, scale)


# ---------------------------------------------------------------- 3. measurements


@dataclass(frozen=True)
class Dimension:
    name: str
    value_mm: float
    report: MeasurementUncertaintyReport

    @property
    def display(self) -> str:
        return f"{self.report.estimate_display} ({self.report.uncertainty_display})"


@dataclass(frozen=True)
class Measurements:
    points_mm: np.ndarray
    bounding: BoundingDimensions
    dimensions: tuple[Dimension, ...]
    profile: tuple[tuple[float, float], ...]  # (z mm, diameter mm)
    geometry: NormalizedMeasurementGeometry
    notes: tuple[str, ...] = field(default=())

    def get(self, name: str) -> Dimension | None:
        return next((item for item in self.dimensions if item.name == name), None)


def _slice_diameters(points: np.ndarray, height: float) -> list[tuple[float, float, float]]:
    """(z centre, diameter, spread) per horizontal slice, from wall points only."""

    slices = max(8, min(60, int(height / 1.0)))
    edges = np.linspace(0.0, height, slices + 1)
    radial = np.linalg.norm(points[:, :2], axis=1)
    result: list[tuple[float, float, float]] = []
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        inside = radial[(points[:, 2] >= low) & (points[:, 2] < high)]
        if len(inside) < 12:
            continue
        outer = np.percentile(inside, 95)
        wall = inside[inside > 0.85 * outer]
        if len(wall) < 8:
            continue
        result.append(((low + high) / 2, 2 * float(np.median(wall)), 2 * float(np.std(wall))))
    return result


def measure(frame: Frame, model: LoadedModel, isolation: Isolation) -> Measurements:
    points = frame.apply(model.points[isolation.object_indices])
    keep = points[:, 2] <= np.percentile(points[:, 2], 99.7)
    points = points[keep]
    scale = frame.scale
    geometry = NormalizedMeasurementGeometry(
        normalized_geometry_revision=frame.transform.transform_id,
        source_geometry_id=frame.geometry.geometry_id,
        points=_points3(points),
        scale_state=ScaleState.METRIC_UNVERIFIED,
        coordinate_unit="mm_unverified",
        scale_provenance_id=scale.provenance.provenance_id,
        scale_factor_uncertainty=scale.uncertainty,
        scale_factor_uncertainty_unit="mm_per_reconstruction_unit",
        scale_provenance_record=scale.provenance,
    )
    bounding = measure_bounding_dimensions(
        geometry,
        current_geometry_id=frame.geometry.geometry_id,
        current_normalized_geometry_revision=frame.transform.transform_id,
        current_scale_provenance_id=scale.provenance.provenance_id,
    )
    evidence = NormalizationScaleEvidence(
        frame.geometry.geometry_id,
        frame.transform.transform_id,
        scale.provenance.provenance_id,
        ScaleState.METRIC_UNVERIFIED,
        scale.mm_per_unit,
        scale.uncertainty,
        "mm_per_reconstruction_unit",
    )
    plane_noise_mm = isolation.plane_rms * scale.mm_per_unit
    height = float(bounding.axis_bounds["z"][1])  # top above the base plane (z = 0)
    slices = _slice_diameters(points, height)
    if not slices:
        raise MeasureDesignError("too few wall points to measure diameters")
    body_index = max(
        range(len(slices)), key=lambda i: slices[i][1] if slices[i][0] < 0.8 * height else -1
    )
    top_band = [s for s in slices if 0.82 * height <= s[0] < 0.97 * height]
    values: list[tuple[str, float, float]] = [
        ("height", height, plane_noise_mm),
        ("max_body_diameter", slices[body_index][1], slices[body_index][2]),
    ]
    notes: list[str] = []
    if top_band:
        lid = float(np.median([s[1] for s in top_band]))
        values.append(("lid_diameter", lid, float(np.median([s[2] for s in top_band]))))
        between = [s for s in slices if slices[body_index][0] < s[0] < top_band[0][0]]
        if between:
            neck = min(between, key=lambda s: s[1])
            if neck[1] < 0.92 * min(lid, slices[body_index][1]):
                values.append(("neck_diameter", neck[1], neck[2]))
            else:
                notes.append("no neck: no slice narrower than 92% of body and lid")
    dimensions = tuple(
        Dimension(
            name,
            value,
            propagate_measurement_uncertainty(
                geometry,
                MeasurementUncertaintyInput(
                    f"{name}-{frame.transform.transform_id}",
                    value,
                    "mm_unverified",
                    1,
                    frame.geometry.geometry_id,
                    frame.transform.transform_id,
                    scale.provenance.provenance_id,
                    ScaleState.METRIC_UNVERIFIED,
                    spread,
                    "mm_unverified",
                ),
                normalization_scale=evidence,
            ),
        )
        for name, value, spread in values
    )
    return Measurements(
        points,
        bounding,
        dimensions,
        tuple((s[0], s[1]) for s in slices),
        geometry,
        tuple(notes),
    )


def dimension_report(
    measurements: Measurements, frame: Frame, *, project_id: str, project_revision: str
) -> MeasurementReport:
    context = MeasurementReportContext(
        project_id,
        project_revision,
        frame.geometry.source_revision,
        frame.geometry.geometry_id,
        frame.transform.transform_id,
        frame.scale.provenance.provenance_id,
        ScaleState.METRIC_UNVERIFIED,
        "mm_unverified",
    )
    return build_measurement_report(
        context, (measurements.bounding, *(item.report for item in measurements.dimensions))
    )


def write_dimension_report(report: MeasurementReport, destination: Path) -> tuple[Path, Path]:
    destination = Path(destination)
    json_path = destination.with_suffix(".json")
    markdown_path = destination.with_suffix(".md")
    json_path.write_bytes(serialize_measurement_report(report) + b"\n")
    markdown_path.write_text(render_measurement_report_markdown(report), encoding="utf-8")
    return json_path, markdown_path


# ---------------------------------------------------------------- 4. Scan Master + Design Model


def object_mesh(mesh_model: LoadedModel, isolation: Isolation, frame: Frame) -> TriangleMeshData:
    """Triangles fully inside the object footprint, in normalized mm (the cleaned selection)."""

    if mesh_model.triangles is None:
        raise MeasureDesignError("promotion needs a mesh; open the built mesh (OBJ/PLY)")
    inside = isolation.region_mask(mesh_model.points)
    triangles = mesh_model.triangles[inside[mesh_model.triangles].all(axis=1)]
    if len(triangles) < 20:
        raise MeasureDesignError("the built mesh has no triangles on the isolated object")
    if len(triangles) > MAX_MESH_TRIANGLES:
        # ponytail: stride decimation keeps the Scan Master JSON tractable; use
        # proxy_decimation/a quadric decimator when full-resolution masters matter.
        triangles = triangles[:: math.ceil(len(triangles) / MAX_MESH_TRIANGLES)]
    used, remapped = np.unique(triangles, return_inverse=True)
    vertices = frame.apply(mesh_model.points[used])
    return TriangleMeshData(
        _points3(np.round(vertices, 6)),
        tuple((int(a), int(b), int(c)) for a, b, c in remapped.reshape(-1, 3)),
    )


PART_GAP_MIN_MM = 2.0
PART_GAP_SPACING_FACTOR = 3.0


def derived_surface_gaps(
    mesh: TriangleMeshData, scanned_mm: np.ndarray
) -> tuple[tuple[int, ...], float]:
    """Vertices of a derived (Poisson) surface with no scanned point nearby: filled, not seen.

    Threshold: max(2 mm, 3 x the median scanned point spacing).
    """
    import open3d as o3d

    scanned = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(scanned_mm))
    spacing = float(np.median(np.asarray(scanned.compute_nearest_neighbor_distance())))
    limit = max(PART_GAP_MIN_MM, PART_GAP_SPACING_FACTOR * spacing)
    vertices = o3d.geometry.PointCloud(
        o3d.utility.Vector3dVector(np.asarray(mesh.vertices, dtype=float))
    )
    distance = np.asarray(vertices.compute_point_cloud_distance(scanned))
    return tuple(int(i) for i in np.nonzero(distance > limit)[0]), limit


def promotion_request(
    *,
    project_id: str,
    model: LoadedModel,
    mesh_model: LoadedModel,
    isolation: Isolation,
    frame: Frame,
    actor_id: str,
    reason: str,
    part_record: dict[str, Any] | None = None,
) -> ScanMasterPromotionRequest:
    # A companion mesh comes from the same OpenMVS scene, so it shares the model's frame.
    aligned = object_mesh(mesh_model, isolation, frame)
    aligned_id = f"aligned-object-mesh-{mesh_sha256(aligned)[:40]}"
    derived = frame.scale.source == "part_combine"
    surface_note = ""
    if derived:
        if part_record is None:
            raise MeasureDesignError("a combined part needs its combine record to be promoted")
        mesh_method = str(part_record.get("mesh_method"))
        surface_note = (
            f"surface DERIVED, not scanned: Open3D Poisson ({mesh_method}) closed from the "
            f"merged part cloud sha256 {model.sha256}; filled areas are coverage gaps"
        )
        reconstruction = ReconstructionOutputManifest(
            project_id=project_id,
            reconstruction_revision=model.reconstruction_revision,
            # Source clouds are COLMAP/OpenMVS builds; the surface itself is derived.
            backend_id=ReconstructionBackendId.COLMAP_OPENMVS,
            backend_version=f"derived:open3d-poisson:{mesh_method}",
            backend_build=f"part-combine:{part_record.get('part')}",
            backend_license=(
                "source clouds: COLMAP BSD-3-Clause, OpenMVS AGPL-3.0 (external process); "
                "derived surface: Open3D MIT"
            ),
            configuration_digest=_sha256_json(
                {
                    "part_cloud": model.sha256,
                    "mesh": mesh_model.sha256,
                    "mesh_method": mesh_method,
                    "combine_method": part_record.get("method"),
                    "sources": [s.get("model_sha256") for s in part_record.get("sources", [])],
                }
            ),
            source_input_digest=model.sha256,
            camera_convention="world-to-camera",
            asset_paths={
                "part_cloud": str(part_record.get("artifact_path")),
                "derived_surface": str(part_record.get("mesh_artifact_path")),
            },
            point_count=len(model.points),
            triangle_count=0 if mesh_model.triangles is None else len(mesh_model.triangles),
            limitations=(
                surface_note,
                "source digest is the merged part cloud, not the raw PackScans",
            ),
        )
    else:
        reconstruction = ReconstructionOutputManifest(
            project_id=project_id,
            reconstruction_revision=model.reconstruction_revision,
            backend_id=ReconstructionBackendId.COLMAP_OPENMVS,
            backend_version="external-build",
            backend_build=model.path.name,
            backend_license="COLMAP BSD-3-Clause; OpenMVS AGPL-3.0 (external process)",
            configuration_digest=_sha256_json({"model": model.sha256, "mesh": mesh_model.sha256}),
            source_input_digest=model.sha256,
            camera_convention="world-to-camera",
            point_count=len(model.points),
            triangle_count=0 if mesh_model.triangles is None else len(mesh_model.triangles),
            limitations=("source digest is the built model file, not the raw PackScan",),
        )
    scale_id = frame.scale.provenance.provenance_id
    lineage = CapturedScanLineage(
        project_id,
        frame.geometry.source_revision,
        model.sha256,
        reconstruction,
        frame.geometry,
        frame.scale.provenance,
        frame.transform,
        aligned_id,
        aligned,
    )
    try:
        cleaned = cleanup_isolated_components(
            aligned,
            parent_revision_id=aligned_id,
            scale_state=ScaleState.METRIC_UNVERIFIED,
            scale_provenance_id=scale_id,
        )
        operation = CleanupOperationEvidence(
            "component-cleanup",
            CleanupOperationKind.COMPONENT_CLEANUP,
            aligned_id,
            mesh_sha256(aligned),
            aligned,
            cleaned.child_revision_id,
            mesh_sha256(cleaned.mesh),
            cleaned.mesh,
            {
                "policy": cleaned.policy.as_dict(),
                "removed_components": len(cleaned.removed_components),
            },
        )
        final, final_id = cleaned.mesh, cleaned.child_revision_id
    except ComponentCleanupError as error:
        digest = mesh_sha256(aligned)
        final_id = f"{aligned_id}-reviewed"
        operation = CleanupOperationEvidence(
            "cleanup-review",
            CleanupOperationKind.NO_OP,
            aligned_id,
            digest,
            aligned,
            final_id,
            digest,
            aligned,
            {"disposition": "component_cleanup_refused", "reason": str(error)},
        )
        final = aligned
    gaps: tuple[int, ...] = ()
    gap_mm = 0.0
    if derived:
        gaps, gap_mm = derived_surface_gaps(final, frame.apply(model.points))
    holes = analyze_mesh_holes(
        final,
        parent_revision_id=final_id,
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id=scale_id,
        uncertain_vertex_indices=(),
        coverage_gap_vertex_indices=gaps,
    )
    return ScanMasterPromotionRequest(
        lineage=lineage,
        parent_revision_id=aligned_id,
        parent_mesh=aligned,
        cleanup_operations=(operation,),
        final_mesh=final,
        hole_report=holes,
        promoted_at_utc=_now(),
        actor_id=actor_id,
        reason=reason,
        known_limitations=(
            "object isolated geometrically (base plane + cluster), not by SAM masks",
            f"scale source {frame.scale.source}; METRIC_UNVERIFIED",
            "no physical validation against the real package",
            *((surface_note,) if derived else ()),
        ),
        coverage_gaps=(
            (
                "merged upright + upside-down scans; a closed, hole-free surface is not proven",
                f"{len(gaps)} of {len(final.vertices)} surface vertices are DERIVED fill "
                f"(farther than {gap_mm:.2f} mm from any scanned point)",
            )
            if derived
            else ("underside against the support plane is not observed",)
        ),
    )


@dataclass(frozen=True)
class DesignState:
    revolved: RevolvedDesignModel
    model: DesignModelRevision  # latest revision (with overall dimensions)
    fitted_height: float
    fitted_diameter: float
    height: float
    diameter: float
    history: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def preview_mesh(self) -> TriangleMeshData:
        """Fitted revolve preview scaled to the edited overall dimensions."""

        mesh = self.revolved.preview.mesh
        radial = self.diameter / self.fitted_diameter
        axial = self.height / self.fitted_height
        return TriangleMeshData(
            tuple((x * radial, y * radial, z * axial) for x, y, z in mesh.vertices),
            mesh.triangles,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.studio-design-model-revision.v1",
            "design_model_revision_id": self.model.revision_id,
            "revision_history": list(self.history),
            "overall_dimensions_mm_unverified": {
                "height": self.height,
                "diameter": self.diameter,
            },
            "fitted_from_scan": {"height": self.fitted_height, "diameter": self.fitted_diameter},
            "model": self.model.as_dict(),
            "revolved_fit": self.revolved.as_dict(),
            "notes": list(self.notes),
            "scan_master_replaced": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


# Owner review may relax the core revolve policy only to these fixed bounds; the policy
# is hashed into the recommendation id. A scan must still be round about its axis
# (radial CV <= 5 %); partial rings drag core's centroid-based CV up.
OWNER_REVIEW_MAX_AXIS_CV = 0.05
OWNER_REVIEW_MIN_ANGULAR_COVERAGE = 0.60
OWNER_REVIEW_MAX_SECTION_CV = 0.45
# PL-0462 roundness evidence. The vertical axis is a seeded least-median-of-squares circle
# fit to the side band (15-85 % of height: no base contact band, no lid face), so a
# footprint-centre bias of ~2 mm no longer decides the gate; the fit is bounded (below).
# The CV is then measured per 10 % slice over ALL slice points about that axis, untrimmed
# (as on origin/main, so the gate is never weaker than the axis-centred one when the axis is
# unchanged); a slice counts only with >= 25 % of the circumference (9 of 36 bins of 10
# degrees) observed. A bin is evidence only with >= 2 vertices: a single
# vertex per bin on a barely photographed wall is reconstruction noise, and judging it made
# rebuilds of one capture pass or fail at random. At least 4 of the 5 body slices (15-75 %
# of height) must be judged: with 3, the verdict hinged on whether one marginal slice reached
# 9 bins (8 real test-333 builds: 2-3 judged slices, never the upper body).
ROUNDNESS_METHOD = (
    "lmeds_bounded_vertical_axis_side_band_15_85_all_points_untrimmed_min2_cov025_slices4_v3"
)
ROUNDNESS_SEED = 0
ROUNDNESS_MIN_SLICE_COVERAGE = 0.25
ROUNDNESS_MIN_SLICES = 4
ROUNDNESS_MIN_BIN_VERTICES = 2
# The fitted axis may only correct the measured-axis bias (2-3 mm on test-333). A circle
# further off, of a different size, or not backed by most side points means the wall is not
# one circle (e.g. a 40-60 % arc of an oval fits a circle 12-15 mm off-axis): then the CV is
# measured about the measured axis itself, as before PL-0462.
ROUNDNESS_MAX_AXIS_SHIFT = 0.10  # of the measured side radius
ROUNDNESS_MAX_RADIUS_CHANGE = 0.10  # relative to the measured side radius
ROUNDNESS_MIN_AXIS_INLIERS = 0.60
SIDE_RECAPTURE_ADVICE = (
    "The side of the package is not covered well enough — take more photos from the side "
    "at middle height, all the way around, then rebuild."
)


@dataclass(frozen=True)
class AxisRoundness:
    method: str
    axis_xy_mm: tuple[float, float]  # fitted axis relative to the Scan Master z axis
    radius_mm: float
    radial_cv: float  # worst slice CV about the (bounded) axis, all points, untrimmed
    slices_used: int
    slices_total: int
    axis_inlier_fraction: float  # side-band points within 3 robust sigma of the circle
    axis_source: str = "fitted_circle"  # or "measured_axis" when the fit is out of bounds

    def as_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "seed": ROUNDNESS_SEED,
            "min_slice_coverage": ROUNDNESS_MIN_SLICE_COVERAGE,
            "min_bin_vertices": ROUNDNESS_MIN_BIN_VERTICES,
            "min_slices": ROUNDNESS_MIN_SLICES,
            "axis_xy_mm": [round(value, 4) for value in self.axis_xy_mm],
            "radius_mm": round(self.radius_mm, 4),
            "radial_cv": round(self.radial_cv, 5),
            "slices_used": self.slices_used,
            "slices_total": self.slices_total,
            "axis_inlier_fraction": round(self.axis_inlier_fraction, 4),
            "axis_source": self.axis_source,
            "max_axis_shift": ROUNDNESS_MAX_AXIS_SHIFT,
            "max_radius_change": ROUNDNESS_MAX_RADIUS_CHANGE,
            "min_axis_inliers": ROUNDNESS_MIN_AXIS_INLIERS,
        }


def _circle_through(points: np.ndarray) -> np.ndarray | None:
    (ax, ay), (bx, by), (cx, cy) = points
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return None
    a, b, c = ax * ax + ay * ay, bx * bx + by * by, cx * cx + cy * cy
    return np.array(
        [
            (a * (by - cy) + b * (cy - ay) + c * (ay - by)) / d,
            (a * (cx - bx) + b * (ax - cx) + c * (bx - ax)) / d,
        ]
    )


def _robust_circle(band: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Seeded least-median-of-squares circle + Kasa refit: (centre, radius, inlier fraction)."""

    rng = np.random.default_rng(ROUNDNESS_SEED)
    search = band[rng.choice(len(band), min(len(band), 5000), replace=False)]
    centre, best = np.zeros(2), math.inf
    for _ in range(500):  # least median of squares over 3-point circles
        candidate = _circle_through(search[rng.choice(len(search), 3, replace=False)])
        if candidate is None:
            continue
        radii = np.linalg.norm(search - candidate, axis=1)
        median = float(np.median(np.abs(radii - np.median(radii))))
        if median < best:
            centre, best = candidate, median
    radii = np.linalg.norm(band - centre, axis=1)
    inliers = np.abs(radii - np.median(radii)) <= max(
        3 * 1.4826 * best, 0.002 * float(np.median(radii))
    )
    # Least-squares (Kasa) refit on the inliers.
    solution = np.linalg.lstsq(
        np.c_[2 * band[inliers], np.ones(int(inliers.sum()))],
        (band[inliers] ** 2).sum(axis=1),
        rcond=None,
    )[0]
    centre = solution[:2]
    return centre, math.sqrt(max(float(solution[2] + centre @ centre), 0.0)), float(inliers.mean())


def robust_axis_roundness(mesh: TriangleMeshData) -> AxisRoundness:
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    top = float(vertices[:, 2].max())
    band = vertices[(vertices[:, 2] >= 0.15 * top) & (vertices[:, 2] < 0.85 * top), :2]
    if len(band) < 8:
        return AxisRoundness(ROUNDNESS_METHOD, (0.0, 0.0), 0.0, math.inf, 0, 5, 0.0)
    centre, radius, inlier_fraction = _robust_circle(band)
    measured = float(np.median(np.linalg.norm(band, axis=1)))
    source = "fitted_circle"
    if (
        float(np.linalg.norm(centre)) > ROUNDNESS_MAX_AXIS_SHIFT * measured
        or abs(radius - measured) > ROUNDNESS_MAX_RADIUS_CHANGE * measured
        or inlier_fraction < ROUNDNESS_MIN_AXIS_INLIERS
    ):
        centre, radius, source = np.zeros(2), measured, "measured_axis"
    worst, used = 0.0, 0
    for low in np.linspace(0.15, 0.75, 5) * top:
        ring = vertices[(vertices[:, 2] >= low) & (vertices[:, 2] < low + 0.1 * top), :2] - centre
        if len(ring) < 8:
            continue
        bins = np.floor((np.arctan2(ring[:, 1], ring[:, 0]) + math.pi) / math.tau * 36) % 36
        occupied, counts = np.unique(bins, return_counts=True)
        occupied = occupied[counts >= ROUNDNESS_MIN_BIN_VERTICES]
        if len(occupied) / 36 < ROUNDNESS_MIN_SLICE_COVERAGE:
            continue
        radial = np.linalg.norm(ring, axis=1)
        worst = max(worst, float(np.std(radial) / np.mean(radial)))
        used += 1
    return AxisRoundness(
        ROUNDNESS_METHOD,
        (float(centre[0]), float(centre[1])),
        radius,
        worst if used else math.inf,
        used,
        5,
        inlier_fraction,
        source,
    )


def fit_design_model(
    scan_master: ScanMasterRevision, *, actor_id: str, owner_review: bool = False
) -> DesignState:
    """Core M11 chain: Scan Master profile -> fit -> zones -> strategy -> revolve + dimensions."""

    created = _now()
    vertices = np.asarray(scan_master.mesh.vertices)
    radial = np.linalg.norm(vertices[:, :2], axis=1)
    diameter_hint = 2 * float(np.percentile(radial, 95))
    profile = extract_scan_master_vertical_profile(
        scan_master,
        expected_scan_master_revision_id=scan_master.revision_id,
        axis=CanonicalAxis.Z,
        plane_origin=(0.0, 0.0, 0.0),
        front_direction=(1.0, 0.0, 0.0),
        # Axisymmetric: accept every vertex around the circumference (|lateral| <= radius).
        lateral_tolerance=0.6 * diameter_hint,
        band_count=16,
        minimum_band_samples=3,
        outlier_mad_multiplier=4.5,
        actor_id=actor_id,
        reason="Profile evidence for the Studio Design Model fit.",
        created_at_utc=created,
    )
    bands = sorted(item.band_index for item in profile.bands if item.source_vertex_indices)
    if len(bands) < 4:
        raise MeasureDesignError("Scan Master profile has too few observed bands for a fit")
    fit = fit_design_profile(
        profile,
        transition_anchors=(
            ProfileTransitionAnchor(ProfileTransitionKind.BASE, bands[0]),
            ProfileTransitionAnchor(ProfileTransitionKind.SHOULDER, bands[-2]),
        ),
        smoothing_strength=0.2,
        window_radius=2,
        maximum_relative_adjustment=0.25,
    )
    if fit.profile is None:
        raise MeasureDesignError(
            "core profile fit needs review: " + ", ".join(fit.uncertainty_codes)
        )
    zones = detect_design_profile_zones(fit, expected_fit_id=fit.fit_id, component_id="container")
    notes: list[str] = []
    if zones.review_required and owner_review:
        # Core zone rules expect a bottle (base flare, shoulder, neck); a straight jar has
        # none. Record an attributed jar partition: base 8%, body to 85%, lid step, lid top.
        start, end = fit.profile.domain
        cuts = [start, *(start + f * (end - start) for f in (0.08, 0.85, 0.93)), end]
        zones = override_design_profile_zones(
            zones,
            fit,
            expected_zone_revision_id=zones.revision_id,
            expected_fit_id=fit.fit_id,
            boundaries=tuple(
                replace(
                    item,
                    start_axial=cuts[index],
                    end_axial=cuts[index + 1],
                    evidence_codes=("owner_reviewed_jar_partition",),
                )
                for index, item in enumerate(zones.boundaries)
            ),
            actor_id=actor_id,
            reason="Owner review: straight jar partition ("
            + ", ".join(zones.uncertainty_codes)
            + ")",
            created_at_utc=created,
        )
        notes.append("owner-reviewed jar zone partition (core bottle zone rules were ambiguous)")
    elif zones.review_required:
        raise MeasureDesignError(
            "core profile zones need review (" + ", ".join(zones.uncertainty_codes) + "). "
            "Tick owner review to accept a jar partition."
        )
    strategy = recommend_fitting_strategy(
        scan_master,
        expected_scan_master_revision_id=scan_master.revision_id,
        actor_id=actor_id,
        reason="Assess axisymmetric revolve suitability.",
        created_at_utc=created,
        upright_axis=PrincipalAxis.Z,  # the Scan Master frame is base-plane upright
    )
    if strategy.strategy is not FittingStrategy.AXISYMMETRIC_REVOLVE and owner_review:
        # Core section CV is centred on each section's centroid, which a partial ring drags
        # off-axis. Allow an owner-reviewed, recorded policy only when the scan really is round
        # about the measured axis.
        roundness = robust_axis_roundness(scan_master.mesh)
        if roundness.slices_used < ROUNDNESS_MIN_SLICES:
            raise MeasureDesignError(
                f"cannot judge roundness — only {roundness.slices_used} of "
                f"{roundness.slices_total} side slices show at least a quarter of the "
                f"circumference with >= {ROUNDNESS_MIN_BIN_VERTICES} points per 10° step. "
                f"{SIDE_RECAPTURE_ADVICE}"
            )
        if roundness.radial_cv > OWNER_REVIEW_MAX_AXIS_CV or len(strategy.section_evidence) < 3:
            raise MeasureDesignError(
                f"not round about the measured axis (radial CV {roundness.radial_cv:.3f} > "
                f"{OWNER_REVIEW_MAX_AXIS_CV} on the side wall, "
                f"{roundness.axis_inlier_fraction:.0%} of side points on one circle). "
                "Either the package is not round, or "
                + SIDE_RECAPTURE_ADVICE[0].lower()
                + SIDE_RECAPTURE_ADVICE[1:]
            )
        policy = FittingStrategyPolicy(
            minimum_angular_coverage=OWNER_REVIEW_MIN_ANGULAR_COVERAGE,
            maximum_axisymmetric_radial_cv=OWNER_REVIEW_MAX_SECTION_CV,
        )
        evidence = json.dumps(roundness.as_dict(), sort_keys=True, separators=(",", ":"))
        strategy = recommend_fitting_strategy(
            scan_master,
            expected_scan_master_revision_id=scan_master.revision_id,
            actor_id=actor_id,
            reason=f"Owner-reviewed revolve policy; roundness {evidence}.",
            created_at_utc=created,
            policy=policy,
            upright_axis=PrincipalAxis.Z,
        )
        notes.append(
            f"owner-reviewed strategy policy: angular coverage >= "
            f"{policy.minimum_angular_coverage}, section CV <= "
            f"{policy.maximum_axisymmetric_radial_cv} (radial CV {roundness.radial_cv:.3f} "
            f"about a robust axis {math.hypot(*roundness.axis_xy_mm):.1f} mm from the "
            f"measured centre, {roundness.slices_used}/{roundness.slices_total} side slices, "
            f"{roundness.axis_inlier_fraction:.0%} axis inliers; {roundness.method})"
        )
    if strategy.strategy is not FittingStrategy.AXISYMMETRIC_REVOLVE:
        sections = strategy.section_evidence
        worst = (
            f" Worst side section: {min(s.angular_coverage for s in sections):.0%} of the "
            f"circumference seen, section CV "
            f"{max(s.radial_coefficient_of_variation for s in sections):.2f}."
            if sections
            else ""
        )
        raise MeasureDesignError(
            f"core fitting strategy is {strategy.strategy.value} "
            f"({', '.join(strategy.uncertainty_codes)}). "
            + (
                f"Exceeds the owner-review bounds (coverage >= {OWNER_REVIEW_MIN_ANGULAR_COVERAGE},"
                f" section CV <= {OWNER_REVIEW_MAX_SECTION_CV}).{worst} {SIDE_RECAPTURE_ADVICE}"
                if owner_review
                else "Tick owner review to accept a partial scan as round, or recapture."
            )
        )
    revolved = build_axisymmetric_revolved_design_model(
        strategy,
        fit,
        zones,
        expected_strategy_recommendation_id=strategy.recommendation_id,
        expected_profile_fit_id=fit.fit_id,
        expected_feature_zone_revision_id=zones.revision_id,
        component_id="container",
        package_family=PackageFamily.JAR,
        actor_id=actor_id,
        reason="Fit editable axisymmetric jar to the measured Scan Master.",
        created_at_utc=created,
        chord_tolerance=0.25,
        profile_samples=48,
        maximum_angular_segments=96,
    )
    preview = np.asarray(revolved.preview.mesh.vertices)
    fitted_height = float(np.ptp(preview[:, 2]))
    fitted_diameter = 2 * float(np.linalg.norm(preview[:, :2], axis=1).max())
    model = create_overall_dimensions_revision(
        revolved.model,
        height=fitted_height,
        width=fitted_diameter,
        depth=fitted_diameter,
        proportional_groups=((DimensionAxis.WIDTH, DimensionAxis.DEPTH),),
        actor_id=actor_id,
        reason="Overall dimensions from the fitted revolve.",
        created_at_utc=created,
    )
    return DesignState(
        revolved,
        model,
        fitted_height,
        fitted_diameter,
        fitted_height,
        fitted_diameter,
        (revolved.model.revision_id, model.revision_id),
        tuple(notes),
    )


def edit_dimensions(
    state: DesignState, *, height: float, diameter: float, actor_id: str
) -> DesignState:
    model = state.model
    history = list(state.history)
    for axis, value, current in (
        (DimensionAxis.HEIGHT, height, state.height),
        (DimensionAxis.WIDTH, diameter, state.diameter),
    ):
        if abs(value - current) < 1e-9:
            continue
        edit = revise_overall_dimension(
            model,
            expected_model_revision_id=model.revision_id,
            axis=axis,
            value=value,
            actor_id=actor_id,
            reason=f"Studio edit: {axis.value} -> {value:.3f} mm_unverified",
            created_at_utc=_now(),
        )
        model = edit.model
        history.append(model.revision_id)
    return DesignState(
        state.revolved,
        model,
        state.fitted_height,
        state.fitted_diameter,
        height,
        diameter,
        tuple(history),
        state.notes,
    )
