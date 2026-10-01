"""Deterministic multiview mask lifting into captured object geometry."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime

from .mask_revisions import GeometryMaskRevisionBinding, StaleMaskGeometryError
from .reconstruction import PACKSCAN_CAMERA_CONVENTION, ScaleState
from .segmentation import InvalidMaskArtifact, MaskArtifact, MaskSetRevision

OBJECT_LIFT_PIPELINE = "packlab.object-mask-lift"
OBJECT_LIFT_VERSION = "1.0.0"
PACKLAB_CAMERA_AXES = "packlab-camera-x-right-y-down-z-forward-v1"
PACKSCAN_CAMERA_TO_WORLD = "camera_to_world_row_major_4x4_column_vectors_v1"
WORLD_TO_CAMERA = "world_to_camera_row_major_4x4_column_vectors_v1"
MAX_LIFT_POINTS = 250_000
MAX_LIFT_CAMERAS = 512
MAX_POINT_VIEW_OBSERVATIONS = 5_000_000
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

Point3 = tuple[float, float, float]
Matrix4 = tuple[float, ...]


class ObjectMaskLiftError(ValueError):
    """Raised when object-mask lifting inputs are malformed or unsafe."""


class CameraConventionError(ObjectMaskLiftError):
    """Raised when a camera transform cannot be explicitly normalized."""


@dataclass(frozen=True, slots=True)
class WorldPoint:
    point_id: str
    position: Point3

    def __post_init__(self) -> None:
        if not isinstance(self.point_id, str) or not _IDENTIFIER.fullmatch(self.point_id):
            raise ObjectMaskLiftError("point_id must be an explicit safe identifier")
        if len(self.position) != 3 or not all(
            isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
            for value in self.position
        ):
            raise ObjectMaskLiftError("world point coordinates must be finite 3D values")
        object.__setattr__(self, "position", tuple(float(value) for value in self.position))


@dataclass(frozen=True, slots=True)
class LiftCamera:
    """One source view with an explicitly named rigid pose and axis convention."""

    camera_id: str
    source_image_asset_id: str
    source_digest: str
    image_width: int
    image_height: int
    intrinsics: tuple[float, float, float, float]
    pose_matrix: Matrix4
    pose_convention: str
    camera_axis_convention: str
    mask_artifact_id: str

    def __post_init__(self) -> None:
        for name in ("camera_id", "source_image_asset_id", "mask_artifact_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ObjectMaskLiftError(f"{name} must be non-empty text")
        if (
            not isinstance(self.source_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.source_digest) is None
        ):
            raise ObjectMaskLiftError("source_digest must be lowercase SHA-256")
        for name in ("image_width", "image_height"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ObjectMaskLiftError(f"{name} must be a positive integer")
        if len(self.intrinsics) != 4 or not all(
            isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
            for value in self.intrinsics
        ):
            raise ObjectMaskLiftError("intrinsics must be finite (fx, fy, cx, cy)")
        fx, fy, _cx, _cy = self.intrinsics
        if fx <= 0 or fy <= 0:
            raise ObjectMaskLiftError("camera focal lengths must be positive")
        if len(self.pose_matrix) != 16 or not all(
            isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
            for value in self.pose_matrix
        ):
            raise CameraConventionError("pose_matrix must contain 16 finite row-major values")
        object.__setattr__(self, "pose_matrix", tuple(float(value) for value in self.pose_matrix))
        object.__setattr__(self, "intrinsics", tuple(float(value) for value in self.intrinsics))


@dataclass(frozen=True, slots=True)
class LiftThresholdProfile:
    profile_id: str = "multiview-support-v1"
    minimum_observed_views: int = 2
    minimum_support_views: int = 2
    minimum_support_ratio: float = 0.70

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not _IDENTIFIER.fullmatch(self.profile_id):
            raise ObjectMaskLiftError("threshold profile ID must be a safe identifier")
        for name in ("minimum_observed_views", "minimum_support_views"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ObjectMaskLiftError(f"{name} must be a positive integer")
        if self.minimum_support_views > self.minimum_observed_views:
            raise ObjectMaskLiftError("minimum_support_views cannot exceed minimum_observed_views")
        if (
            not isinstance(self.minimum_support_ratio, (int, float))
            or isinstance(self.minimum_support_ratio, bool)
            or not math.isfinite(self.minimum_support_ratio)
            or not 0.0 <= self.minimum_support_ratio <= 1.0
        ):
            raise ObjectMaskLiftError("minimum_support_ratio must be between 0 and 1")

    def as_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "minimum_observed_views": self.minimum_observed_views,
            "minimum_support_views": self.minimum_support_views,
            "minimum_support_ratio": self.minimum_support_ratio,
        }


@dataclass(frozen=True, slots=True)
class LiftVisibilityPolicy:
    tolerance: float = 1e-4
    raster_scale: int = 1
    policy_id: str = "candidate-zbuffer-v1"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.tolerance, (int, float))
            or isinstance(self.tolerance, bool)
            or not math.isfinite(self.tolerance)
            or self.tolerance < 0.0
        ):
            raise ObjectMaskLiftError("visibility tolerance must be finite and non-negative")
        if not isinstance(self.raster_scale, int) or isinstance(self.raster_scale, bool):
            raise ObjectMaskLiftError("visibility raster_scale must be an integer")
        if not 1 <= self.raster_scale <= 64:
            raise ObjectMaskLiftError("visibility raster_scale must be between 1 and 64")
        if not isinstance(self.policy_id, str) or not _IDENTIFIER.fullmatch(self.policy_id):
            raise ObjectMaskLiftError("visibility policy ID must be a safe identifier")

    def as_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "tolerance": self.tolerance,
            "raster_scale": self.raster_scale,
            "method": "minimum-positive-depth-from-candidate-z-buffer",
        }


@dataclass(frozen=True, slots=True)
class ObjectMaskLiftRequest:
    project_id: str
    source_revision: str
    source_input_digest: str
    reconstruction_revision: str
    camera_solution_revision: str
    mask_set: MaskSetRevision
    cameras: tuple[LiftCamera, ...]
    points: tuple[WorldPoint, ...]
    scale_state: ScaleState
    created_at: str
    thresholds: LiftThresholdProfile = LiftThresholdProfile()
    visibility: LiftVisibilityPolicy = LiftVisibilityPolicy()

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "source_revision",
            "reconstruction_revision",
            "camera_solution_revision",
            "created_at",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ObjectMaskLiftError(f"{name} must be non-empty text")
        if (
            not isinstance(self.source_input_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.source_input_digest) is None
        ):
            raise ObjectMaskLiftError("source_input_digest must be lowercase SHA-256")
        try:
            created = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise ObjectMaskLiftError("created_at must be ISO-8601") from error
        if created.tzinfo is None:
            raise ObjectMaskLiftError("created_at must include a timezone")
        if self.mask_set.source_revision != self.source_revision:
            raise ObjectMaskLiftError("mask-set source revision does not match lift request")
        if not isinstance(self.scale_state, ScaleState):
            raise ObjectMaskLiftError("scale_state must be a ScaleState")
        if self.scale_state is ScaleState.METRIC_VERIFIED:
            raise ObjectMaskLiftError("PL-0190 cannot claim M09 METRIC_VERIFIED authority")
        cameras = tuple(self.cameras)
        points = tuple(self.points)
        if not cameras or len(cameras) > MAX_LIFT_CAMERAS:
            raise ObjectMaskLiftError("camera count must be between 1 and 512")
        if not points or len(points) > MAX_LIFT_POINTS:
            raise ObjectMaskLiftError("candidate count must be between 1 and 250000")
        if len(points) * len(cameras) > MAX_POINT_VIEW_OBSERVATIONS:
            raise ObjectMaskLiftError("candidate-camera observations exceed the bounded work limit")
        if len({camera.camera_id for camera in cameras}) != len(cameras):
            raise ObjectMaskLiftError("camera IDs must be unique")
        if len({camera.source_image_asset_id for camera in cameras}) != len(cameras):
            raise ObjectMaskLiftError("each multiview camera must bind a unique source image")
        if len({point.point_id for point in points}) != len(points):
            raise ObjectMaskLiftError("point IDs must be unique")
        object.__setattr__(self, "cameras", cameras)
        object.__setattr__(self, "points", points)


@dataclass(frozen=True, slots=True)
class PointVoteAggregate:
    point_id: str
    observed_views: int
    support_views: int
    reject_views: int
    not_observed_views: int
    behind_camera_views: int
    out_of_frame_views: int
    occluded_views: int
    support_ratio: float
    selected: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "point_id": self.point_id,
            "observed_views": self.observed_views,
            "support_views": self.support_views,
            "reject_views": self.reject_views,
            "not_observed_views": self.not_observed_views,
            "behind_camera_views": self.behind_camera_views,
            "out_of_frame_views": self.out_of_frame_views,
            "occluded_views": self.occluded_views,
            "support_ratio": self.support_ratio,
            "selected": self.selected,
        }


@dataclass(frozen=True, slots=True)
class CameraProjectionEvidence:
    camera_id: str
    source_image_asset_id: str
    source_digest: str
    image_dimensions: tuple[int, int]
    intrinsics: tuple[float, float, float, float]
    normalized_world_to_camera: Matrix4
    pose_convention: str
    camera_axis_convention: str
    mask_artifact_id: str
    mask_digest: str

    def as_dict(self) -> dict[str, object]:
        return {
            "camera_id": self.camera_id,
            "source_image_asset_id": self.source_image_asset_id,
            "source_digest": self.source_digest,
            "image_dimensions": {
                "width": self.image_dimensions[0],
                "height": self.image_dimensions[1],
            },
            "intrinsics": list(self.intrinsics),
            "normalized_world_to_camera": list(self.normalized_world_to_camera),
            "pose_convention": self.pose_convention,
            "camera_axis_convention": self.camera_axis_convention,
            "mask_artifact_id": self.mask_artifact_id,
            "mask_digest": self.mask_digest,
        }


@dataclass(frozen=True, slots=True)
class PreliminaryOBB:
    center: Point3
    axes: tuple[Point3, Point3, Point3]
    half_extents: Point3
    method: str = "pca-preliminary-qa-only"

    def as_dict(self) -> dict[str, object]:
        return {
            "center": list(self.center),
            "axes": [list(axis) for axis in self.axes],
            "half_extents": list(self.half_extents),
            "method": self.method,
            "metric_authority": False,
        }


@dataclass(frozen=True, slots=True)
class ObjectCaptureGeometry:
    geometry_id: str
    project_id: str
    source_revision: str
    source_input_digest: str
    source_images: tuple[tuple[str, str], ...]
    source_mask_artifacts: tuple[tuple[str, str], ...]
    camera_conventions: tuple[tuple[str, str, str], ...]
    camera_evidence: tuple[CameraProjectionEvidence, ...]
    reconstruction_revision: str
    camera_solution_revision: str
    mask_set_revision_id: str
    mask_set_revision_digest: str
    projection_convention: str
    projection_version: str
    threshold_profile: LiftThresholdProfile
    visibility_policy: LiftVisibilityPolicy
    outlier_policy: str
    candidate_count: int
    point_count: int
    generated: bool
    authority_class: str
    scale_state: ScaleState
    point_votes: tuple[PointVoteAggregate, ...]
    filtered_points: tuple[Point3, ...]
    unfiltered_points: tuple[Point3, ...]
    obb: PreliminaryOBB | None
    created_at: str

    def __post_init__(self) -> None:
        if self.generated is not False:
            raise ObjectMaskLiftError("captured geometry must be explicitly generated=false")
        if self.authority_class != "OBJECT_CAPTURE_GEOMETRY":
            raise ObjectMaskLiftError("mask lift output must remain OBJECT_CAPTURE_GEOMETRY")
        if self.scale_state is ScaleState.METRIC_VERIFIED:
            raise ObjectMaskLiftError("PL-0190 cannot claim M09 METRIC_VERIFIED authority")
        if self.point_count != len(self.filtered_points) or self.point_count != len(
            self.unfiltered_points
        ):
            raise ObjectMaskLiftError(
                "filtered and reproducible unfiltered point counts must agree"
            )

    def invalidation_binding(self) -> GeometryMaskRevisionBinding:
        return GeometryMaskRevisionBinding(
            self.project_id,
            self.source_revision,
            self.mask_set_revision_id,
            self.mask_set_revision_digest,
        )

    def require_current_dependencies(
        self,
        *,
        current_reconstruction_revision: str,
        current_camera_solution_revision: str,
        current_source_revision: str,
        current_source_input_digest: str,
        current_source_images: tuple[tuple[str, str], ...],
        current_source_mask_artifacts: tuple[tuple[str, str], ...],
        current_camera_conventions: tuple[tuple[str, str, str], ...],
        current_camera_evidence: tuple[CameraProjectionEvidence, ...],
        current_mask_set: MaskSetRevision,
        current_projection_convention: str,
        current_projection_version: str,
        current_threshold_profile: LiftThresholdProfile,
        current_visibility_policy: LiftVisibilityPolicy,
    ) -> None:
        if (
            current_reconstruction_revision != self.reconstruction_revision
            or current_camera_solution_revision != self.camera_solution_revision
            or current_source_revision != self.source_revision
            or current_source_input_digest != self.source_input_digest
            or tuple(sorted(current_source_images)) != self.source_images
            or tuple(sorted(current_source_mask_artifacts)) != self.source_mask_artifacts
            or tuple(sorted(current_camera_conventions)) != self.camera_conventions
            or tuple(sorted(current_camera_evidence, key=lambda item: item.camera_id))
            != self.camera_evidence
            or current_projection_convention != self.projection_convention
            or current_projection_version != self.projection_version
            or current_threshold_profile != self.threshold_profile
            or current_visibility_policy != self.visibility_policy
        ):
            raise StaleMaskGeometryError("object geometry is stale and must be regenerated")
        self.invalidation_binding().require_current(current_mask_set)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.object-capture-geometry.v1",
            "geometry_id": self.geometry_id,
            "authority_class": self.authority_class,
            "generated": self.generated,
            "parents": {
                "source_revision": self.source_revision,
                "source_input_digest": self.source_input_digest,
                "reconstruction_revision": self.reconstruction_revision,
                "camera_solution_revision": self.camera_solution_revision,
                "mask_set_revision_id": self.mask_set_revision_id,
                "mask_set_revision_digest": self.mask_set_revision_digest,
            },
            "source_images": [
                {"asset_id": asset_id, "sha256": digest} for asset_id, digest in self.source_images
            ],
            "source_mask_artifacts": [
                {"artifact_id": artifact_id, "sha256": digest}
                for artifact_id, digest in self.source_mask_artifacts
            ],
            "camera_conventions": [
                {
                    "camera_id": camera_id,
                    "pose_convention": pose_convention,
                    "camera_axis_convention": axis_convention,
                }
                for camera_id, pose_convention, axis_convention in self.camera_conventions
            ],
            "camera_projection_evidence": [item.as_dict() for item in self.camera_evidence],
            "projection": {
                "convention": self.projection_convention,
                "version": self.projection_version,
                "pixel_sample": "nearest-pixel-center-floor-coordinate-plus-0.5",
            },
            "object_lift": {"pipeline": OBJECT_LIFT_PIPELINE, "version": OBJECT_LIFT_VERSION},
            "threshold_profile": self.threshold_profile.as_dict(),
            "visibility_policy": self.visibility_policy.as_dict(),
            "outlier_policy": self.outlier_policy,
            "point_count_before_voting": self.candidate_count,
            "point_count_after_voting": self.point_count,
            "point_votes": [item.as_dict() for item in self.point_votes],
            "points": [list(point) for point in self.filtered_points],
            "unfiltered_points": [list(point) for point in self.unfiltered_points],
            "preliminary_obb": None if self.obb is None else self.obb.as_dict(),
            "scale_state": self.scale_state.value,
            "created_at": self.created_at,
        }


def validate_camera_convention(camera_axis_convention: str, pose_convention: str) -> None:
    """Run an explicit optical-axis known-point check before normalizing a camera."""
    supported_axes = {PACKLAB_CAMERA_AXES, PACKSCAN_CAMERA_CONVENTION}
    supported_poses = {WORLD_TO_CAMERA, PACKSCAN_CAMERA_TO_WORLD}
    if camera_axis_convention not in supported_axes or pose_convention not in supported_poses:
        raise CameraConventionError(
            "camera axis or pose convention is unsupported; no guessing is allowed"
        )
    identity: Matrix4 = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
    normalized = _normalized_world_to_camera(identity, pose_convention, camera_axis_convention)
    known_point = (
        (1.0, -0.5, 2.0) if camera_axis_convention == PACKLAB_CAMERA_AXES else (1.0, 0.5, -2.0)
    )
    camera_point = _transform(normalized, known_point)
    projected = (
        2.0 * camera_point[0] / camera_point[2] + 11.0,
        3.0 * camera_point[1] / camera_point[2] + 13.0,
        camera_point[2],
    )
    if not _close_point(projected, (12.0, 12.25, 2.0)):
        raise CameraConventionError("synthetic known-point projection convention gate failed")


def _normalized_world_to_camera(
    matrix: Matrix4, pose_convention: str, camera_axis_convention: str
) -> Matrix4:
    _validate_rigid_matrix(matrix)
    if pose_convention == WORLD_TO_CAMERA:
        world_to_camera = matrix
    elif pose_convention == PACKSCAN_CAMERA_TO_WORLD:
        world_to_camera = _invert_rigid(matrix)
    else:
        raise CameraConventionError("unsupported pose convention")
    if camera_axis_convention == PACKSCAN_CAMERA_CONVENTION:
        values = list(world_to_camera)
        for column in range(4):
            values[4 + column] *= -1.0
            values[8 + column] *= -1.0
        world_to_camera = tuple(values)
    elif camera_axis_convention != PACKLAB_CAMERA_AXES:
        raise CameraConventionError("unsupported camera axis convention")
    return world_to_camera


def _validate_rigid_matrix(matrix: Matrix4) -> None:
    if len(matrix) != 16 or any(
        not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value)
        for value in matrix
    ):
        raise CameraConventionError("camera transform must be a finite row-major 4x4 matrix")
    if any(
        abs(matrix[index] - target) > 1e-8 for index, target in zip((12, 13, 14, 15), (0, 0, 0, 1))
    ):
        raise CameraConventionError("camera transform must be affine with final row (0,0,0,1)")
    rows = tuple(tuple(matrix[row * 4 + col] for col in range(3)) for row in range(3))
    for first in range(3):
        for second in range(3):
            dot = sum(rows[first][axis] * rows[second][axis] for axis in range(3))
            expected = 1.0 if first == second else 0.0
            if abs(dot - expected) > 1e-5:
                raise CameraConventionError("camera transform rotation must be orthonormal")
    determinant = (
        rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
        - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
        + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0])
    )
    if abs(determinant - 1.0) > 1e-5:
        raise CameraConventionError("camera transform rotation must be right-handed")


def _invert_rigid(matrix: Matrix4) -> Matrix4:
    rotation = tuple(tuple(matrix[row * 4 + col] for col in range(3)) for row in range(3))
    translation = tuple(matrix[row * 4 + 3] for row in range(3))
    inverse_rotation = tuple(tuple(rotation[col][row] for col in range(3)) for row in range(3))
    inverse_translation = tuple(
        -sum(inverse_rotation[row][col] * translation[col] for col in range(3)) for row in range(3)
    )
    return tuple(
        inverse_rotation[row][col] if col < 3 else inverse_translation[row]
        for row in range(3)
        for col in range(4)
    ) + (0.0, 0.0, 0.0, 1.0)


def _transform(matrix: Matrix4, point: Point3) -> Point3:
    return tuple(
        sum(matrix[row * 4 + column] * point[column] for column in range(3)) + matrix[row * 4 + 3]
        for row in range(3)
    )  # type: ignore[return-value]


def _close_point(first: Point3, second: Point3) -> bool:
    return all(abs(left - right) <= 1e-9 for left, right in zip(first, second))


@dataclass(frozen=True, slots=True)
class _Projected:
    x: int
    y: int
    depth: float


class ObjectMaskLiftingService:
    """Project reconstruction candidates and vote against verified masks."""

    def lift(self, request: ObjectMaskLiftRequest) -> ObjectCaptureGeometry:
        if request.scale_state is ScaleState.METRIC_VERIFIED:
            raise ObjectMaskLiftError("M09 metric authority cannot be asserted by PL-0190")
        if request.mask_set.project_id != request.project_id:
            raise ObjectMaskLiftError("mask-set project does not match lift request")
        masks = {mask.artifact_id: mask for mask in request.mask_set.masks}
        if len(masks) != len(request.mask_set.masks):
            raise ObjectMaskLiftError("mask set contains ambiguous artifact IDs")
        cameras = tuple(sorted(request.cameras, key=lambda item: item.camera_id))
        points = tuple(sorted(request.points, key=lambda item: item.point_id))
        normalized: dict[str, Matrix4] = {}
        camera_masks: dict[str, MaskArtifact] = {}
        for camera in cameras:
            validate_camera_convention(camera.camera_axis_convention, camera.pose_convention)
            normalized[camera.camera_id] = _normalized_world_to_camera(
                camera.pose_matrix, camera.pose_convention, camera.camera_axis_convention
            )
            mask = masks.get(camera.mask_artifact_id)
            if mask is None:
                raise ObjectMaskLiftError("camera references a mask outside the published mask set")
            if (
                camera.source_image_asset_id != mask.source_image_asset_id
                or camera.source_digest != mask.source_digest
                or (camera.image_width, camera.image_height)
                != (mask.source_width, mask.source_height)
            ):
                raise ObjectMaskLiftError("camera source identity does not match its mask artifact")
            if mask.raster is None:
                raise InvalidMaskArtifact("object lifting requires an in-memory mask raster")
            if mask.raster.digest != mask.mask_digest:
                raise InvalidMaskArtifact("mask raster digest does not match its declared digest")
            camera_masks[camera.camera_id] = mask

        projected: dict[tuple[str, str], _Projected] = {}
        z_buffers: dict[str, dict[tuple[int, int], float]] = {}
        for camera in cameras:
            matrix = normalized[camera.camera_id]
            z_buffer: dict[tuple[int, int], float] = {}
            fx, fy, cx, cy = camera.intrinsics
            for point in points:
                camera_point = _transform(matrix, point.position)
                depth = camera_point[2]
                if depth <= 1e-12:
                    projected[(camera.camera_id, point.point_id)] = _Projected(-1, -1, depth)
                    continue
                pixel_x = fx * camera_point[0] / depth + cx
                pixel_y = fy * camera_point[1] / depth + cy
                if not (math.isfinite(pixel_x) and math.isfinite(pixel_y)):
                    raise ObjectMaskLiftError("camera projection produced a non-finite pixel")
                x, y = math.floor(pixel_x + 0.5), math.floor(pixel_y + 0.5)
                if not (0 <= x < camera.image_width and 0 <= y < camera.image_height):
                    projected[(camera.camera_id, point.point_id)] = _Projected(x, y, depth)
                    continue
                key = (x // request.visibility.raster_scale, y // request.visibility.raster_scale)
                z_buffer[key] = min(z_buffer.get(key, math.inf), depth)
                projected[(camera.camera_id, point.point_id)] = _Projected(x, y, depth)
            z_buffers[camera.camera_id] = z_buffer

        votes: list[PointVoteAggregate] = []
        selected_points: list[Point3] = []
        for point in points:
            support = reject = behind = out_of_frame = occluded = not_observed = 0
            for camera in cameras:
                item = projected[(camera.camera_id, point.point_id)]
                if item.depth <= 1e-12:
                    behind += 1
                    not_observed += 1
                    continue
                if (
                    item.x < 0
                    or item.y < 0
                    or item.x >= camera.image_width
                    or item.y >= camera.image_height
                ):
                    out_of_frame += 1
                    not_observed += 1
                    continue
                key = (
                    item.x // request.visibility.raster_scale,
                    item.y // request.visibility.raster_scale,
                )
                front_depth = z_buffers[camera.camera_id][key]
                if item.depth > front_depth + request.visibility.tolerance:
                    occluded += 1
                    not_observed += 1
                    continue
                mask = camera_masks[camera.camera_id]
                if mask.raster is None:  # narrowed above; retains a clear public failure mode.
                    raise InvalidMaskArtifact("object lifting requires an in-memory mask raster")
                model_x, model_y = mask.transform.source_to_model(item.x, item.y)
                sample_x = math.floor(model_x + 0.5)
                sample_y = math.floor(model_y + 0.5)
                if not (0 <= sample_x < mask.mask_width and 0 <= sample_y < mask.mask_height):
                    not_observed += 1
                    out_of_frame += 1
                    continue
                if mask.raster.sample(sample_x, sample_y):
                    support += 1
                else:
                    reject += 1
            observed = support + reject
            ratio = support / observed if observed else 0.0
            selected = (
                observed >= request.thresholds.minimum_observed_views
                and support >= request.thresholds.minimum_support_views
                and ratio >= request.thresholds.minimum_support_ratio
            )
            vote = PointVoteAggregate(
                point.point_id,
                observed,
                support,
                reject,
                not_observed,
                behind,
                out_of_frame,
                occluded,
                ratio,
                selected,
            )
            votes.append(vote)
            if selected:
                selected_points.append(point.position)

        source_images = tuple(
            sorted({(camera.source_image_asset_id, camera.source_digest) for camera in cameras})
        )
        source_mask_artifacts = tuple(
            sorted(
                {
                    (camera.mask_artifact_id, camera_masks[camera.camera_id].mask_digest)
                    for camera in cameras
                }
            )
        )
        camera_conventions = tuple(
            sorted(
                {
                    (camera.camera_id, camera.pose_convention, camera.camera_axis_convention)
                    for camera in cameras
                }
            )
        )
        camera_evidence = tuple(
            CameraProjectionEvidence(
                camera_id=camera.camera_id,
                source_image_asset_id=camera.source_image_asset_id,
                source_digest=camera.source_digest,
                image_dimensions=(camera.image_width, camera.image_height),
                intrinsics=camera.intrinsics,
                normalized_world_to_camera=normalized[camera.camera_id],
                pose_convention=camera.pose_convention,
                camera_axis_convention=camera.camera_axis_convention,
                mask_artifact_id=camera.mask_artifact_id,
                mask_digest=camera_masks[camera.camera_id].mask_digest,
            )
            for camera in cameras
        )
        selection_digest = _digest(
            {
                "points": [list(point) for point in selected_points],
                "votes": [item.as_dict() for item in votes],
            }
        )
        identity = {
            "pipeline": OBJECT_LIFT_PIPELINE,
            "version": OBJECT_LIFT_VERSION,
            "project_id": request.project_id,
            "source_revision": request.source_revision,
            "source_input_digest": request.source_input_digest,
            "source_images": [list(item) for item in source_images],
            "reconstruction_revision": request.reconstruction_revision,
            "camera_solution_revision": request.camera_solution_revision,
            "mask_set_revision_id": request.mask_set.revision_id,
            "mask_set_revision_digest": request.mask_set.revision_digest,
            "projection_convention": PACKLAB_CAMERA_AXES,
            "outlier_policy": "none; preserve threshold-selected point subset",
            "cameras": [item.as_dict() for item in camera_evidence],
            "points": [
                {"point_id": point.point_id, "position": list(point.position)} for point in points
            ],
            "threshold_profile": request.thresholds.as_dict(),
            "visibility_policy": request.visibility.as_dict(),
            "selection_digest": selection_digest,
        }
        geometry_id = f"object-geometry:{_digest(identity)}"
        return ObjectCaptureGeometry(
            geometry_id=geometry_id,
            project_id=request.project_id,
            source_revision=request.source_revision,
            source_input_digest=request.source_input_digest,
            source_images=source_images,
            source_mask_artifacts=source_mask_artifacts,
            camera_conventions=camera_conventions,
            camera_evidence=camera_evidence,
            reconstruction_revision=request.reconstruction_revision,
            camera_solution_revision=request.camera_solution_revision,
            mask_set_revision_id=request.mask_set.revision_id,
            mask_set_revision_digest=request.mask_set.revision_digest,
            projection_convention=PACKLAB_CAMERA_AXES,
            projection_version=OBJECT_LIFT_VERSION,
            threshold_profile=request.thresholds,
            visibility_policy=request.visibility,
            outlier_policy="none; preserve threshold-selected point subset",
            candidate_count=len(points),
            point_count=len(selected_points),
            generated=False,
            authority_class="OBJECT_CAPTURE_GEOMETRY",
            scale_state=request.scale_state,
            point_votes=tuple(votes),
            filtered_points=tuple(selected_points),
            unfiltered_points=tuple(selected_points),
            obb=_obb(tuple(selected_points)),
            created_at=request.created_at,
        )


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _obb(points: tuple[Point3, ...]) -> PreliminaryOBB | None:
    if not points:
        return None
    center_of_mass = tuple(sum(point[axis] for point in points) / len(points) for axis in range(3))
    covariance = [
        [
            sum(
                (point[row] - center_of_mass[row]) * (point[col] - center_of_mass[col])
                for point in points
            )
            / len(points)
            for col in range(3)
        ]
        for row in range(3)
    ]
    eigenvalues, eigenvectors = _jacobi_eigen(covariance)
    order = sorted(range(3), key=lambda index: (-eigenvalues[index], index))
    axes: list[Point3] = [
        _canonical_axis(
            (
                eigenvectors[0][index],
                eigenvectors[1][index],
                eigenvectors[2][index],
            )
        )
        for index in order
    ]
    if _dot(axes[0], _cross(axes[1], axes[2])) < 0:
        axes[2] = (-axes[2][0], -axes[2][1], -axes[2][2])
    projections = [tuple(_dot(point, axis) for axis in axes) for point in points]
    lows = tuple(min(item[axis] for item in projections) for axis in range(3))
    highs = tuple(max(item[axis] for item in projections) for axis in range(3))
    center = tuple(
        sum(axes[axis][coordinate] * ((lows[axis] + highs[axis]) / 2) for axis in range(3))
        for coordinate in range(3)
    )
    half_extents = tuple((highs[axis] - lows[axis]) / 2 for axis in range(3))
    return PreliminaryOBB(center, tuple(axes), half_extents)  # type: ignore[arg-type]


def _jacobi_eigen(matrix: list[list[float]]) -> tuple[tuple[float, ...], list[list[float]]]:
    values = [row[:] for row in matrix]
    vectors = [[1.0 if row == col else 0.0 for col in range(3)] for row in range(3)]
    for _ in range(32):
        pair = max(((0, 1), (0, 2), (1, 2)), key=lambda item: abs(values[item[0]][item[1]]))
        p, q = pair
        if abs(values[p][q]) < 1e-14:
            break
        angle = 0.5 * math.atan2(2.0 * values[p][q], values[q][q] - values[p][p])
        cosine, sine = math.cos(angle), math.sin(angle)
        for index in range(3):
            if index != p and index != q:
                vp, vq = values[index][p], values[index][q]
                values[index][p] = values[p][index] = cosine * vp - sine * vq
                values[index][q] = values[q][index] = sine * vp + cosine * vq
        app, aqq, apq = values[p][p], values[q][q], values[p][q]
        values[p][p] = cosine * cosine * app - 2 * sine * cosine * apq + sine * sine * aqq
        values[q][q] = sine * sine * app + 2 * sine * cosine * apq + cosine * cosine * aqq
        values[p][q] = values[q][p] = 0.0
        for row in range(3):
            vp, vq = vectors[row][p], vectors[row][q]
            vectors[row][p] = cosine * vp - sine * vq
            vectors[row][q] = sine * vp + cosine * vq
    return tuple(values[index][index] for index in range(3)), vectors


def _canonical_axis(axis: Point3) -> Point3:
    length = math.sqrt(_dot(axis, axis))
    if length <= 1e-12:
        return (1.0, 0.0, 0.0)
    normalized = tuple(value / length for value in axis)
    dominant = max(range(3), key=lambda index: (abs(normalized[index]), -index))
    if normalized[dominant] < 0:
        normalized = tuple(-value for value in normalized)
    return normalized  # type: ignore[return-value]


def _dot(first: Point3, second: Point3) -> float:
    return sum(left * right for left, right in zip(first, second))


def _cross(first: Point3, second: Point3) -> Point3:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )
