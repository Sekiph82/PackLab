"""Deterministic, authority-separated viewport mesh decimation."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass

from .geometry_adapter import (
    CapabilityStatus,
    GeometryCapabilityUnavailable,
    Open3DGeometryAdapter,
    TriangleMeshData,
)
from .reconstruction import ScaleState

PROXY_DECIMATION_CONTRACT = "packlab.preview-proxy-decimation.v1"
PREVIEW_PROXY_AUTHORITY = "PREVIEW_PROXY"
PHYSICAL_VALIDATION_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_TEXTURE_STATUS = "UNAVAILABLE_IN_PACKLAB_GEOMETRY_CONTRACT"


class ProxyDecimationError(ValueError):
    """Raised when proxy generation or authority checks cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class ProxyDecimationPolicy:
    target_triangle_count: int
    maximum_error_ratio: float = 0.001
    boundary_weight: float = 10.0
    maximum_input_triangles: int = 1_000_000
    maximum_target_triangles: int = 20_000
    maximum_quality_samples: int = 16

    def __post_init__(self) -> None:
        if (
            isinstance(self.target_triangle_count, bool)
            or not isinstance(self.target_triangle_count, int)
            or self.target_triangle_count < 1
        ):
            raise ProxyDecimationError("target_triangle_count must be a positive integer")
        if (
            isinstance(self.maximum_error_ratio, bool)
            or not isinstance(self.maximum_error_ratio, (int, float))
            or not math.isfinite(self.maximum_error_ratio)
            or not 0 < self.maximum_error_ratio <= 0.01
        ):
            raise ProxyDecimationError("maximum_error_ratio must be finite and in (0, 0.01]")
        if (
            isinstance(self.boundary_weight, bool)
            or not isinstance(self.boundary_weight, (int, float))
            or not math.isfinite(self.boundary_weight)
            or not 1 <= self.boundary_weight <= 100
        ):
            raise ProxyDecimationError("boundary_weight must be finite and between 1 and 100")
        for name in (
            "maximum_input_triangles",
            "maximum_target_triangles",
            "maximum_quality_samples",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ProxyDecimationError(f"{name} must be a positive integer")
        if self.maximum_input_triangles > 1_000_000:
            raise ProxyDecimationError("maximum_input_triangles exceeds supported work bound")
        if self.maximum_target_triangles > 20_000:
            raise ProxyDecimationError("maximum_target_triangles exceeds supported proxy bound")
        if self.maximum_quality_samples > 64:
            raise ProxyDecimationError("maximum_quality_samples exceeds supported work bound")
        if self.target_triangle_count > self.maximum_target_triangles:
            raise ProxyDecimationError("target_triangle_count exceeds configured proxy bound")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": PROXY_DECIMATION_CONTRACT,
            "algorithm": "open3d_quadric_error_metric_decimation",
            "target_triangle_count": self.target_triangle_count,
            "maximum_error_ratio_of_parent_bbox_diagonal_squared": float(self.maximum_error_ratio),
            "boundary_weight": float(self.boundary_weight),
            "maximum_input_triangles": self.maximum_input_triangles,
            "maximum_target_triangles": self.maximum_target_triangles,
            "maximum_quality_samples_per_direction": self.maximum_quality_samples,
            "authority_class": PREVIEW_PROXY_AUTHORITY,
        }


@dataclass(frozen=True, slots=True)
class ProxyQualityEvidence:
    input_vertex_count: int
    output_vertex_count: int
    input_triangle_count: int
    output_triangle_count: int
    target_triangle_count: int
    target_reached: bool
    vertex_reduction_fraction: float
    triangle_reduction_fraction: float
    sampled_parent_to_proxy_max_distance: float
    sampled_proxy_to_parent_max_distance: float
    sampled_symmetric_rms_nearest_vertex_distance: float
    bounding_extent_delta: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class PreviewProxyRevision:
    contract: str
    authority_class: str
    scan_master_eligible: bool
    full_parent_revision_id: str
    full_parent_geometry_sha256: str
    proxy_revision_id: str
    proxy_geometry_sha256: str
    full_parent_mesh: TriangleMeshData
    proxy_mesh: TriangleMeshData
    policy: ProxyDecimationPolicy
    quality: ProxyQualityEvidence
    texture_uv_status: str
    operation_status: str
    scale_state: ScaleState
    scale_provenance_id: str | None
    physical_accuracy_validation_status: str
    mold_use_authorized: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": self.authority_class,
            "scan_master_eligible": self.scan_master_eligible,
            "full_parent_revision_id": self.full_parent_revision_id,
            "full_parent_geometry_sha256": self.full_parent_geometry_sha256,
            "proxy_revision_id": self.proxy_revision_id,
            "proxy_geometry_sha256": self.proxy_geometry_sha256,
            "policy": self.policy.as_dict(),
            "quality": {
                "input_vertex_count": self.quality.input_vertex_count,
                "output_vertex_count": self.quality.output_vertex_count,
                "input_triangle_count": self.quality.input_triangle_count,
                "output_triangle_count": self.quality.output_triangle_count,
                "target_triangle_count": self.quality.target_triangle_count,
                "target_reached": self.quality.target_reached,
                "vertex_reduction_fraction": self.quality.vertex_reduction_fraction,
                "triangle_reduction_fraction": self.quality.triangle_reduction_fraction,
                "sampled_parent_to_proxy_max_distance": self.quality.sampled_parent_to_proxy_max_distance,
                "sampled_proxy_to_parent_max_distance": self.quality.sampled_proxy_to_parent_max_distance,
                "sampled_symmetric_rms_nearest_vertex_distance": self.quality.sampled_symmetric_rms_nearest_vertex_distance,
                "bounding_extent_delta": self.quality.bounding_extent_delta,
            },
            "texture_uv_status": self.texture_uv_status,
            "operation_status": self.operation_status,
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _geometry_payload(mesh: TriangleMeshData) -> dict[str, object]:
    return {
        "vertices": mesh.vertices,
        "triangles": mesh.triangles,
        "vertex_colors": mesh.vertex_colors,
        "vertex_normals": mesh.vertex_normals,
    }


def _safe_id(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ProxyDecimationError(f"{field} must be a non-empty stable identifier")
    if any(ord(char) < 32 for char in value):
        raise ProxyDecimationError(f"{field} must not contain control characters")
    return value


def _bbox_extents(mesh: TriangleMeshData) -> tuple[float, float, float]:
    if not mesh.vertices:
        return (0.0, 0.0, 0.0)
    return tuple(
        max(vertex[axis] for vertex in mesh.vertices)
        - min(vertex[axis] for vertex in mesh.vertices)
        for axis in range(3)
    )  # type: ignore[return-value]


def _sample_indices(count: int, maximum: int) -> tuple[int, ...]:
    if count <= maximum:
        return tuple(range(count))
    if maximum == 1:
        return (0,)
    return tuple(round(index * (count - 1) / (maximum - 1)) for index in range(maximum))


def _nearest_distances(
    source: TriangleMeshData, target: TriangleMeshData, sample_limit: int
) -> tuple[float, ...]:
    if not source.vertices or not target.vertices:
        return ()
    return tuple(
        math.sqrt(
            min(
                sum((source.vertices[index][axis] - candidate[axis]) ** 2 for axis in range(3))
                for candidate in target.vertices
            )
        )
        for index in _sample_indices(len(source.vertices), sample_limit)
    )


def _quality(
    parent: TriangleMeshData,
    proxy: TriangleMeshData,
    policy: ProxyDecimationPolicy,
) -> ProxyQualityEvidence:
    forward = _nearest_distances(parent, proxy, policy.maximum_quality_samples)
    reverse = _nearest_distances(proxy, parent, policy.maximum_quality_samples)
    distances = forward + reverse
    parent_extent = _bbox_extents(parent)
    proxy_extent = _bbox_extents(proxy)
    return ProxyQualityEvidence(
        input_vertex_count=len(parent.vertices),
        output_vertex_count=len(proxy.vertices),
        input_triangle_count=len(parent.triangles),
        output_triangle_count=len(proxy.triangles),
        target_triangle_count=policy.target_triangle_count,
        target_reached=len(proxy.triangles) <= policy.target_triangle_count,
        vertex_reduction_fraction=(
            1.0 - len(proxy.vertices) / len(parent.vertices) if parent.vertices else 0.0
        ),
        triangle_reduction_fraction=(
            1.0 - len(proxy.triangles) / len(parent.triangles) if parent.triangles else 0.0
        ),
        sampled_parent_to_proxy_max_distance=max(forward, default=0.0),
        sampled_proxy_to_parent_max_distance=max(reverse, default=0.0),
        sampled_symmetric_rms_nearest_vertex_distance=(
            math.sqrt(sum(value * value for value in distances) / len(distances))
            if distances
            else 0.0
        ),
        bounding_extent_delta=tuple(proxy_extent[axis] - parent_extent[axis] for axis in range(3)),  # type: ignore[arg-type]
    )


def decimate_preview_proxy(
    full_mesh: TriangleMeshData,
    *,
    full_parent_revision_id: str,
    scale_state: ScaleState,
    scale_provenance_id: str | None = None,
    policy: ProxyDecimationPolicy,
    adapter: Open3DGeometryAdapter | None = None,
) -> PreviewProxyRevision:
    """Create an Open3D QEM proxy while retaining the exact full parent object."""

    parent_id = _safe_id(full_parent_revision_id, "full_parent_revision_id")
    if not isinstance(scale_state, ScaleState) or scale_state is ScaleState.METRIC_VERIFIED:
        raise ProxyDecimationError("scale_state must preserve relative or metric-unverified state")
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        scale_provenance_id = _safe_id(scale_provenance_id, "scale_provenance_id")
    elif scale_provenance_id is not None:
        scale_provenance_id = _safe_id(scale_provenance_id, "scale_provenance_id")
    if not full_mesh.triangles:
        raise ProxyDecimationError("full parent mesh must contain triangles")
    if len(full_mesh.triangles) > policy.maximum_input_triangles:
        raise ProxyDecimationError("full parent exceeds configured input triangle bound")
    parent_digest = _digest(_geometry_payload(full_mesh))
    adapter = adapter or Open3DGeometryAdapter()
    if policy.target_triangle_count >= len(full_mesh.triangles):
        proxy_mesh = full_mesh
        operation_status = "NO_OP_TARGET_NOT_BELOW_PARENT_TRIANGLE_COUNT"
    else:
        if policy.target_triangle_count < 4:
            raise ProxyDecimationError("decimation target must be at least 4 triangles")
        capability = adapter.probe()
        if capability.status is not CapabilityStatus.AVAILABLE:
            raise ProxyDecimationError(f"Open3D capability unavailable: {capability.detail}")
        if "triangle_mesh_quadric_decimation" not in capability.operations:
            raise ProxyDecimationError("Open3D build lacks quadric mesh decimation capability")
        extents = _bbox_extents(full_mesh)
        diagonal_squared = sum(value * value for value in extents)
        if diagonal_squared <= 1e-24:
            raise ProxyDecimationError("full parent bounding box is degenerate")
        maximum_error = diagonal_squared * policy.maximum_error_ratio
        try:
            proxy_mesh = adapter.simplify_triangle_mesh(
                full_mesh,
                target_triangle_count=policy.target_triangle_count,
                maximum_error=maximum_error,
                boundary_weight=policy.boundary_weight,
            )
        except GeometryCapabilityUnavailable as exc:
            raise ProxyDecimationError(f"Open3D capability unavailable: {exc}") from exc
        operation_status = "DECIMATED_WITH_OPEN3D_QUADRIC_ERROR_METRIC"
        if not proxy_mesh.triangles or not proxy_mesh.vertices:
            raise ProxyDecimationError("Open3D decimation returned empty proxy geometry")
        if len(proxy_mesh.triangles) > len(full_mesh.triangles):
            raise ProxyDecimationError("Open3D decimation increased triangle count")

    quality = _quality(full_mesh, proxy_mesh, policy)
    proxy_digest = _digest(_geometry_payload(proxy_mesh))
    identity = {
        "contract": PROXY_DECIMATION_CONTRACT,
        "authority_class": PREVIEW_PROXY_AUTHORITY,
        "full_parent_revision_id": parent_id,
        "full_parent_geometry_sha256": parent_digest,
        "proxy_geometry_sha256": proxy_digest,
        "policy": policy.as_dict(),
        "quality": asdict(quality),
        "texture_uv_status": _TEXTURE_STATUS,
        "operation_status": operation_status,
        "scale_state": scale_state.value,
        "scale_provenance_id": scale_provenance_id,
    }
    return PreviewProxyRevision(
        contract=PROXY_DECIMATION_CONTRACT,
        authority_class=PREVIEW_PROXY_AUTHORITY,
        scan_master_eligible=False,
        full_parent_revision_id=parent_id,
        full_parent_geometry_sha256=parent_digest,
        proxy_revision_id=f"preview-proxy:{_digest(identity)}",
        proxy_geometry_sha256=proxy_digest,
        full_parent_mesh=full_mesh,
        proxy_mesh=proxy_mesh,
        policy=policy,
        quality=quality,
        texture_uv_status=_TEXTURE_STATUS,
        operation_status=operation_status,
        scale_state=scale_state,
        scale_provenance_id=scale_provenance_id,
        physical_accuracy_validation_status=PHYSICAL_VALIDATION_DEFERRED,
        mold_use_authorized=False,
    )


def reject_proxy_scan_master_promotion(proxy: PreviewProxyRevision) -> None:
    """Explicitly reject this display-only proxy from Scan Master promotion."""
    if proxy.authority_class == PREVIEW_PROXY_AUTHORITY or not proxy.scan_master_eligible:
        raise ProxyDecimationError(
            "PREVIEW_PROXY geometry is never eligible as Scan Master source geometry"
        )


__all__ = [
    "PHYSICAL_VALIDATION_DEFERRED",
    "PREVIEW_PROXY_AUTHORITY",
    "PROXY_DECIMATION_CONTRACT",
    "PreviewProxyRevision",
    "ProxyDecimationError",
    "ProxyDecimationPolicy",
    "ProxyQualityEvidence",
    "decimate_preview_proxy",
    "reject_proxy_scan_master_promotion",
]
