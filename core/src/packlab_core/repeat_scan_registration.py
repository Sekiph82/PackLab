"""Deterministic, scale-preserving registration for captured scan revisions."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

from .calibration.scale_provenance import ScaleProvenance
from .coordinate_frame import coordinate_unit_for_scale_state
from .geometry_adapter import (
    GeometryAdapterError,
    Open3DGeometryAdapter,
    PointCloudData,
    PointCloudRegistrationOutput,
)
from .normalization_transform import GeometryNormalizationTransform
from .object_mask_lifting import ObjectCaptureGeometry
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_IDENTITY: tuple[float, ...] = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


class RegistrationError(ValueError):
    """Raised when captured registration inputs or the adapter result are invalid."""


def _identifier(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise RegistrationError(f"{field}_invalid")
    if any(ord(character) < 32 for character in value):
        raise RegistrationError(f"{field}_invalid")


def _digest(value: str, field: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise RegistrationError(f"{field}_invalid")


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _point_cloud_digest(cloud: PointCloudData) -> str:
    return _hash({"points": cloud.points, "colors": cloud.colors, "normals": cloud.normals})


def _transform_point(transform: tuple[float, ...], point: tuple[float, float, float]):
    return tuple(
        sum(transform[row * 4 + col] * point[col] for col in range(3)) + transform[row * 4 + 3]
        for row in range(3)
    )


def _validate_rigid_transform(transform: tuple[float, ...], field: str) -> None:
    if len(transform) != 16 or any(not math.isfinite(value) for value in transform):
        raise RegistrationError(f"{field}_invalid")
    if any(
        abs(actual - expected) > 1e-5
        for actual, expected in zip(transform[12:16], (0.0, 0.0, 0.0, 1.0), strict=True)
    ):
        raise RegistrationError(f"{field}_not_affine")
    rotation = tuple(tuple(transform[row * 4 + col] for col in range(3)) for row in range(3))
    for left in range(3):
        for right in range(3):
            dot = sum(rotation[row][left] * rotation[row][right] for row in range(3))
            if abs(dot - (1.0 if left == right else 0.0)) > 1e-4:
                raise RegistrationError(f"{field}_not_rigid")
    determinant = (
        rotation[0][0] * (rotation[1][1] * rotation[2][2] - rotation[1][2] * rotation[2][1])
        - rotation[0][1] * (rotation[1][0] * rotation[2][2] - rotation[1][2] * rotation[2][0])
        + rotation[0][2] * (rotation[1][0] * rotation[2][1] - rotation[1][1] * rotation[2][0])
    )
    if abs(determinant - 1.0) > 1e-4:
        raise RegistrationError(f"{field}_reflection_or_scale_forbidden")


@dataclass(frozen=True, slots=True)
class RegistrationRevision:
    """Captured, coordinate-bound point samples from one immutable parent revision."""

    revision_id: str
    project_id: str
    parent_digest: str
    point_cloud: PointCloudData
    point_samples_sha256: str
    authority_class: str
    generated: bool
    coordinate_frame_id: str
    coordinate_unit: str
    scale_state: ScaleState
    scale_provenance_id: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool

    def __post_init__(self) -> None:
        _identifier(self.revision_id, "registration_revision")
        _identifier(self.project_id, "registration_project")
        _identifier(self.coordinate_frame_id, "coordinate_frame")
        _identifier(self.scale_provenance_id, "scale_provenance")
        _digest(self.parent_digest, "registration_parent_digest")
        _digest(self.point_samples_sha256, "registration_point_samples_digest")
        if not isinstance(self.point_cloud, PointCloudData) or not self.point_cloud.points:
            raise RegistrationError("registration_point_cloud_empty")
        if _point_cloud_digest(self.point_cloud) != self.point_samples_sha256:
            raise RegistrationError("registration_point_samples_digest_mismatch")
        if self.authority_class not in {"OBJECT_CAPTURE_GEOMETRY", "SCAN_MASTER"}:
            raise RegistrationError("generated_or_non_captured_authority_forbidden")
        if self.generated is not False:
            raise RegistrationError("generated_or_non_captured_authority_forbidden")
        if self.scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
            raise RegistrationError("metric_verified_registration_forbidden")
        if self.coordinate_unit != coordinate_unit_for_scale_state(self.scale_state):
            raise RegistrationError("coordinate_unit_scale_state_mismatch")
        if self.physical_accuracy_validation_status != _DEFERRED:
            raise RegistrationError("physical_validation_must_remain_deferred")
        if self.mold_use_authorized is not False:
            raise RegistrationError("mold_use_must_remain_unauthorized")

    @classmethod
    def from_object_capture_geometry(
        cls,
        geometry: ObjectCaptureGeometry,
        alignment: GeometryNormalizationTransform,
        scale_provenance: ScaleProvenance,
    ) -> RegistrationRevision:
        if geometry.generated is not False or geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY":
            raise RegistrationError("generated_or_non_captured_authority_forbidden")
        if alignment.geometry_id != geometry.geometry_id:
            raise RegistrationError("alignment_geometry_parent_mismatch")
        if alignment.original_scale_state is not geometry.scale_state:
            raise RegistrationError("alignment_input_scale_state_mismatch")
        if (
            alignment.transform.reconstruction_revision != geometry.reconstruction_revision
            or scale_provenance.input_reconstruction_revision != geometry.reconstruction_revision
            or alignment.transform.scale_state is not scale_provenance.scale_state
        ):
            raise RegistrationError("alignment_scale_lineage_mismatch")
        points = tuple(alignment.apply_point(point) for point in geometry.filtered_points)
        cloud = PointCloudData(points=points)
        return cls(
            geometry.geometry_id,
            geometry.project_id,
            _hash(
                {
                    "geometry_id": geometry.geometry_id,
                    "source_input_digest": geometry.source_input_digest,
                    "mask_set_revision_id": geometry.mask_set_revision_id,
                    "points": cloud.points,
                }
            ),
            cloud,
            _point_cloud_digest(cloud),
            "OBJECT_CAPTURE_GEOMETRY",
            False,
            alignment.transform.target_frame,
            coordinate_unit_for_scale_state(scale_provenance.scale_state),
            scale_provenance.scale_state,
            scale_provenance.provenance_id,
            _DEFERRED,
            False,
        )

    @classmethod
    def from_scan_master(
        cls,
        revision: ScanMasterRevision,
    ) -> RegistrationRevision:
        manifest = revision.manifest
        alignment = manifest.get("alignment_transform")
        transform = alignment.get("transform") if isinstance(alignment, Mapping) else None
        if not isinstance(transform, Mapping):
            raise RegistrationError("scan_master_alignment_missing")
        revision_id = manifest.get("scan_master_revision_id")
        authority = manifest.get("authority_class")
        scale_state_value = manifest.get("scale_state")
        provenance_id = manifest.get("scale_provenance_id")
        output_digest = manifest.get("output_geometry_sha256")
        raw_digest = manifest.get("raw_capture_sha256")
        provenance = manifest.get("scale_provenance")
        alignment_parents = alignment.get("parents") if isinstance(alignment, Mapping) else None
        object_geometry_id = manifest.get("parent_object_geometry_revision_id")
        if (
            revision_id != revision.revision_id
            or authority != "SCAN_MASTER"
            or manifest.get("project_id") != revision.project_id
            or manifest.get("generated") is True
            or manifest.get("physical_accuracy_validation_status") != _DEFERRED
            or manifest.get("mold_use_authorized") is not False
            or not isinstance(scale_state_value, str)
            or not isinstance(provenance_id, str)
            or not isinstance(raw_digest, str)
            or _SHA256.fullmatch(raw_digest) is None
            or not isinstance(manifest.get("raw_capture_revision_id"), str)
            or not isinstance(manifest.get("reconstruction_revision_id"), str)
            or manifest.get("parent_object_geometry_source_input_digest") != raw_digest
            or not isinstance(object_geometry_id, str)
            or manifest.get("object_geometry_revision_id") != object_geometry_id
            or not isinstance(alignment_parents, Mapping)
            or alignment_parents.get("object_capture_geometry_id") != object_geometry_id
            or not isinstance(provenance, Mapping)
            or provenance.get("provenance_id") != provenance_id
            or provenance.get("scale_state") != scale_state_value
            or transform.get("reconstruction_revision")
            != manifest.get("reconstruction_revision_id")
            or not isinstance(output_digest, str)
            or output_digest != mesh_sha256(revision.mesh)
        ):
            raise RegistrationError("scan_master_manifest_invalid")
        try:
            state = ScaleState(scale_state_value)
        except ValueError as error:
            raise RegistrationError("scan_master_scale_state_invalid") from error
        cloud = PointCloudData(
            points=revision.mesh.vertices,
            colors=revision.mesh.vertex_colors,
            normals=revision.mesh.vertex_normals,
        )
        frame_id = transform.get("target_frame")
        if not isinstance(frame_id, str):
            raise RegistrationError("scan_master_coordinate_frame_missing")
        return cls(
            revision.revision_id,
            revision.project_id,
            output_digest,
            cloud,
            _point_cloud_digest(cloud),
            "SCAN_MASTER",
            False,
            frame_id,
            coordinate_unit_for_scale_state(state),
            state,
            provenance_id,
            _DEFERRED,
            False,
        )


@dataclass(frozen=True, slots=True)
class RegistrationPolicy:
    maximum_correspondence_distance: float
    maximum_iterations: int = 100
    relative_fitness_tolerance: float = 1e-7
    relative_rmse_tolerance: float = 1e-7
    minimum_inlier_count: int = 6
    minimum_fitness: float = 0.25
    maximum_inlier_rmse: float = 0.01
    maximum_points_per_revision: int = 20_000

    def __post_init__(self) -> None:
        if (
            isinstance(self.maximum_correspondence_distance, bool)
            or not isinstance(self.maximum_correspondence_distance, (int, float))
            or not math.isfinite(self.maximum_correspondence_distance)
            or self.maximum_correspondence_distance <= 0
        ):
            raise RegistrationError("maximum_correspondence_distance_invalid")
        for field_name in (
            "relative_fitness_tolerance",
            "relative_rmse_tolerance",
            "minimum_fitness",
            "maximum_inlier_rmse",
        ):
            value = getattr(self, field_name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise RegistrationError(f"{field_name}_invalid")
        if not 0 <= self.relative_fitness_tolerance <= 1:
            raise RegistrationError("relative_fitness_tolerance_invalid")
        if not 0 <= self.relative_rmse_tolerance <= 1:
            raise RegistrationError("relative_rmse_tolerance_invalid")
        if not 0 < self.minimum_fitness <= 1:
            raise RegistrationError("minimum_fitness_invalid")
        if self.maximum_inlier_rmse <= 0:
            raise RegistrationError("maximum_inlier_rmse_invalid")
        for name in ("maximum_iterations", "minimum_inlier_count", "maximum_points_per_revision"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise RegistrationError(f"{name}_invalid")
        if (
            self.maximum_iterations > 250
            or self.maximum_points_per_revision > 50_000
            or self.maximum_iterations * self.maximum_points_per_revision > 2_000_000
        ):
            raise RegistrationError("registration_work_bound_exceeded")

    def as_dict(self) -> dict[str, object]:
        return {
            "algorithm": "open3d_point_to_point_icp_rigid_v1",
            "maximum_correspondence_distance": float(self.maximum_correspondence_distance),
            "maximum_iterations": self.maximum_iterations,
            "relative_fitness_tolerance": float(self.relative_fitness_tolerance),
            "relative_rmse_tolerance": float(self.relative_rmse_tolerance),
            "minimum_inlier_count": self.minimum_inlier_count,
            "minimum_fitness": float(self.minimum_fitness),
            "maximum_inlier_rmse": float(self.maximum_inlier_rmse),
            "maximum_points_per_revision": self.maximum_points_per_revision,
            "scaling_enabled": False,
        }


@dataclass(frozen=True, slots=True)
class RepeatScanRegistration:
    registration_id: str
    project_id: str
    source_revision_id: str
    source_parent_digest: str
    source_authority_class: str
    target_revision_id: str
    target_parent_digest: str
    target_authority_class: str
    source_coordinate_frame_id: str
    target_coordinate_frame_id: str
    scale_state: ScaleState
    source_scale_provenance_id: str
    target_scale_provenance_id: str
    initialization_method: str
    initial_transform: tuple[float, ...]
    transform_source_to_target: tuple[float, ...]
    policy: RegistrationPolicy
    convergence_status: str
    inlier_count: int
    inlier_ratio: float
    inlier_rmse: float | None
    residuals: tuple[float, ...]
    residual_mean: float | None
    residual_maximum: float | None
    physical_repeat_scan_reproducibility_status: str = _DEFERRED
    physical_reproducibility_claim: bool = False
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.repeat-scan-registration.v1",
            "registration_id": self.registration_id,
            "parents": {
                "project_id": self.project_id,
                "source_revision_id": self.source_revision_id,
                "source_parent_digest": self.source_parent_digest,
                "source_authority_class": self.source_authority_class,
                "target_revision_id": self.target_revision_id,
                "target_parent_digest": self.target_parent_digest,
                "target_authority_class": self.target_authority_class,
            },
            "coordinate_frames": {
                "source": self.source_coordinate_frame_id,
                "target": self.target_coordinate_frame_id,
                "transform_direction": "source_to_target",
            },
            "scale": {
                "state": self.scale_state.value,
                "source_provenance_id": self.source_scale_provenance_id,
                "target_provenance_id": self.target_scale_provenance_id,
                "physical_accuracy_validation_status": _DEFERRED,
                "mold_use_authorized": False,
            },
            "initialization": {
                "method": self.initialization_method,
                "transform": list(self.initial_transform),
            },
            "convergence_policy": self.policy.as_dict(),
            "convergence_status": self.convergence_status,
            "termination_reason": (
                "Open3D exposes no stop reason; status applies final quality gates after the "
                "configured relative-delta criteria and maximum-iteration bound."
            ),
            "transform_source_to_target": list(self.transform_source_to_target),
            "inliers": {
                "count": self.inlier_count,
                "ratio_of_source_points": self.inlier_ratio,
                "rmse": self.inlier_rmse,
                "residuals": list(self.residuals),
                "residual_mean": self.residual_mean,
                "residual_maximum": self.residual_maximum,
            },
            "physical_repeat_scan_reproducibility_status": (
                self.physical_repeat_scan_reproducibility_status
            ),
            "physical_reproducibility_claim": self.physical_reproducibility_claim,
            "mold_use_authorized": self.mold_use_authorized,
        }


def register_repeat_scans(
    source: RegistrationRevision,
    target: RegistrationRevision,
    *,
    policy: RegistrationPolicy,
    initial_transform: tuple[float, ...] | None = None,
    adapter: Open3DGeometryAdapter | None = None,
) -> RepeatScanRegistration:
    """Register two captured revisions without changing either parent or scale."""

    if not isinstance(policy, RegistrationPolicy):
        raise RegistrationError("registration_policy_required")
    if not isinstance(source, RegistrationRevision) or not isinstance(target, RegistrationRevision):
        raise RegistrationError("typed_registration_revisions_required")
    if source.revision_id == target.revision_id:
        raise RegistrationError("registration_parents_must_be_distinct")
    if source.project_id != target.project_id:
        raise RegistrationError("registration_project_mismatch")
    if (
        source.generated
        or target.generated
        or any(
            value.authority_class not in {"OBJECT_CAPTURE_GEOMETRY", "SCAN_MASTER"}
            for value in (source, target)
        )
    ):
        raise RegistrationError("generated_or_non_captured_authority_forbidden")
    if (
        source.scale_state is not target.scale_state
        or source.coordinate_unit != target.coordinate_unit
    ):
        raise RegistrationError("registration_scale_or_unit_mismatch")
    for value in (source, target):
        if value.physical_accuracy_validation_status != _DEFERRED or value.mold_use_authorized:
            raise RegistrationError("physical_authority_must_remain_deferred")
        if len(value.point_cloud.points) < 3:
            raise RegistrationError("registration_requires_at_least_three_points")
        if len(value.point_cloud.points) > policy.maximum_points_per_revision:
            raise RegistrationError("registration_point_limit_exceeded")

    initial = _IDENTITY if initial_transform is None else tuple(initial_transform)
    _validate_rigid_transform(initial, "initial_transform")
    initial_method = "identity" if initial_transform is None else "caller_supplied_rigid_transform"
    backend = Open3DGeometryAdapter() if adapter is None else adapter
    try:
        output: PointCloudRegistrationOutput = backend.register_point_clouds(
            source.point_cloud,
            target.point_cloud,
            initial_transform=initial,
            maximum_correspondence_distance=policy.maximum_correspondence_distance,
            relative_fitness=policy.relative_fitness_tolerance,
            relative_rmse=policy.relative_rmse_tolerance,
            maximum_iterations=policy.maximum_iterations,
        )
    except (GeometryAdapterError, RuntimeError, ValueError) as error:
        if isinstance(error, RegistrationError):
            raise
        raise RegistrationError("geometry_adapter_registration_failed") from error
    transform = output.transformation
    _validate_rigid_transform(transform, "registration_transform")
    pairs = output.correspondences
    if (
        len(set(pairs)) != len(pairs)
        or len({source_index for source_index, _target_index in pairs}) != len(pairs)
        or any(
            i < 0
            or i >= len(source.point_cloud.points)
            or j < 0
            or j >= len(target.point_cloud.points)
            for i, j in pairs
        )
    ):
        raise RegistrationError("registration_correspondence_indices_invalid")
    residuals = tuple(
        math.dist(
            _transform_point(transform, source.point_cloud.points[i]),
            target.point_cloud.points[j],
        )
        for i, j in pairs
    )
    if any(
        not math.isfinite(value) or value > policy.maximum_correspondence_distance + 1e-9
        for value in residuals
    ):
        raise RegistrationError("registration_residual_outside_correspondence_gate")
    count = len(residuals)
    ratio = count / len(source.point_cloud.points)
    if not math.isfinite(output.fitness) or not 0.0 <= output.fitness <= 1.0:
        raise RegistrationError("adapter_fitness_invalid")
    if not math.isclose(output.fitness, ratio, rel_tol=1e-5, abs_tol=1e-8):
        raise RegistrationError("adapter_registration_statistics_mismatch")
    rmse = math.sqrt(sum(value * value for value in residuals) / count) if count else None
    residual_mean = sum(residuals) / count if count else None
    residual_max = max(residuals) if count else None
    if count and (
        rmse is None or not math.isclose(output.inlier_rmse, rmse, rel_tol=1e-5, abs_tol=1e-8)
    ):
        raise RegistrationError("adapter_registration_statistics_mismatch")
    if (
        count >= policy.minimum_inlier_count
        and ratio >= policy.minimum_fitness
        and rmse is not None
        and rmse <= policy.maximum_inlier_rmse
    ):
        status = "QUALITY_ACCEPTED_STOP_REASON_UNAVAILABLE"
    elif count < policy.minimum_inlier_count or ratio < policy.minimum_fitness:
        status = "NON_CONVERGED_INSUFFICIENT_OVERLAP"
    else:
        status = "NON_CONVERGED_RESIDUAL_LIMIT"
    body = {
        "algorithm": "open3d_point_to_point_icp_rigid_v1",
        "project_id": source.project_id,
        "source_revision_id": source.revision_id,
        "source_parent_digest": source.parent_digest,
        "source_authority_class": source.authority_class,
        "source_scale_state": source.scale_state.value,
        "source_scale_provenance_id": source.scale_provenance_id,
        "source_coordinate_frame_id": source.coordinate_frame_id,
        "target_revision_id": target.revision_id,
        "target_parent_digest": target.parent_digest,
        "target_authority_class": target.authority_class,
        "target_scale_provenance_id": target.scale_provenance_id,
        "target_coordinate_frame_id": target.coordinate_frame_id,
        "initial_transform": initial,
        "transform_source_to_target": transform,
        "policy": policy.as_dict(),
        "convergence_status": status,
        "termination_reason": "native_stop_reason_unavailable_final_quality_gate_used",
        "residuals": residuals,
    }
    return RepeatScanRegistration(
        "repeat-registration:" + _hash(body),
        source.project_id,
        source.revision_id,
        source.parent_digest,
        source.authority_class,
        target.revision_id,
        target.parent_digest,
        target.authority_class,
        source.coordinate_frame_id,
        target.coordinate_frame_id,
        source.scale_state,
        source.scale_provenance_id,
        target.scale_provenance_id,
        initial_method,
        initial,
        transform,
        policy,
        status,
        count,
        ratio,
        rmse,
        residuals,
        residual_mean,
        residual_max,
    )
