"""Deterministic scan-to-design deviation comparison; this module does no fitting."""

from __future__ import annotations

import bisect
import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum

from .geometry_adapter import (
    GeometryAdapterError,
    MeshSurfaceDistanceOutput,
    Open3DGeometryAdapter,
    PointCloudData,
    TriangleMeshData,
)
from .reconstruction import ScaleState
from .repeat_scan_registration import RegistrationError, RegistrationRevision
from .scan_master import ScanMasterRevision, mesh_sha256

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_PALETTE_UNSIGNED = (
    (0.10, 0.62, 0.35, 1.0),
    (0.88, 0.82, 0.14, 1.0),
    (0.96, 0.55, 0.10, 1.0),
    (0.82, 0.16, 0.15, 1.0),
    (0.42, 0.08, 0.45, 1.0),
)
_PALETTE_NEGATIVE = (
    (0.18, 0.62, 0.88, 1.0),
    (0.16, 0.40, 0.78, 1.0),
    (0.12, 0.25, 0.58, 1.0),
    (0.08, 0.14, 0.38, 1.0),
    (0.04, 0.06, 0.20, 1.0),
)
_PALETTE_POSITIVE = (
    (0.97, 0.75, 0.14, 1.0),
    (0.97, 0.53, 0.10, 1.0),
    (0.91, 0.32, 0.10, 1.0),
    (0.78, 0.14, 0.12, 1.0),
    (0.48, 0.04, 0.08, 1.0),
)
_COLOR_ZERO = (0.10, 0.72, 0.34, 1.0)


class HeatmapError(ValueError):
    """Raised when Scan Master or Design Model comparison inputs are stale or invalid."""


class DistanceSignPolicy(StrEnum):
    UNSIGNED = "unsigned"
    SIGNED_INSIDE_NEGATIVE = "signed_inside_negative"


def _digest(value: str, field: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise HeatmapError(f"{field}_invalid")


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _scale_unit(scale_state: ScaleState) -> str:
    if scale_state is ScaleState.RELATIVE:
        return "reconstruction_units"
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        return "mm_unverified"
    raise HeatmapError("metric_verified_heatmap_forbidden_while_physical_validation_deferred")


@dataclass(frozen=True, slots=True)
class DesignModelGeometryReference:
    """An explicit already-fitted Design Model mesh; no fitting occurs here."""

    revision_id: str
    project_id: str
    fitted_to_scan_master_revision_id: str
    mesh: TriangleMeshData
    geometry_sha256: str
    coordinate_frame_id: str
    scale_state: ScaleState
    scale_provenance_id: str
    authority_class: str = "DESIGN_MODEL"
    physical_accuracy_validation_status: str = _DEFERRED
    mold_use_authorized: bool = False

    def __post_init__(self) -> None:
        if (
            not self.revision_id
            or not self.project_id
            or not self.fitted_to_scan_master_revision_id
        ):
            raise HeatmapError("design_model_reference_identity_invalid")
        if self.authority_class != "DESIGN_MODEL":
            raise HeatmapError("design_model_authority_required")
        _digest(self.geometry_sha256, "design_model_geometry_digest")
        if mesh_sha256(self.mesh) != self.geometry_sha256:
            raise HeatmapError("design_model_geometry_digest_mismatch")
        if not self.mesh.vertices or not self.mesh.triangles:
            raise HeatmapError("design_model_mesh_required")
        _scale_unit(self.scale_state)
        if not self.coordinate_frame_id or not self.scale_provenance_id:
            raise HeatmapError("design_model_coordinate_scale_provenance_required")
        if self.physical_accuracy_validation_status != _DEFERRED:
            raise HeatmapError("physical_validation_must_remain_deferred")
        if self.mold_use_authorized is not False:
            raise HeatmapError("mold_use_must_remain_unauthorized")


@dataclass(frozen=True, slots=True)
class HeatmapPolicy:
    sign_policy: DistanceSignPolicy = DistanceSignPolicy.UNSIGNED
    sample_count: int = 20_000
    magnitude_thresholds: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0)
    maximum_source_vertices: int = 50_000
    maximum_model_triangles: int = 1_000_000

    def __post_init__(self) -> None:
        if not isinstance(self.sign_policy, DistanceSignPolicy):
            raise HeatmapError("distance_sign_policy_invalid")
        for name in ("sample_count", "maximum_source_vertices", "maximum_model_triangles"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise HeatmapError(f"{name}_invalid")
        if (
            self.sample_count > self.maximum_source_vertices
            or self.maximum_source_vertices > 100_000
        ):
            raise HeatmapError("heatmap_sampling_work_bound_exceeded")
        if self.maximum_model_triangles > 1_000_000:
            raise HeatmapError("heatmap_model_triangle_bound_exceeded")
        thresholds = tuple(self.magnitude_thresholds)
        if (
            not thresholds
            or len(thresholds) > 4
            or any(
                isinstance(value, bool)
                or not isinstance(value, (float, int))
                or not math.isfinite(value)
                or value <= 0
                for value in thresholds
            )
            or any(left >= right for left, right in zip(thresholds, thresholds[1:]))
        ):
            raise HeatmapError("magnitude_thresholds_must_be_finite_positive_increasing")
        object.__setattr__(
            self, "magnitude_thresholds", tuple(float(value) for value in thresholds)
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "sign_policy": self.sign_policy.value,
            "sample_count": self.sample_count,
            "sampling_method": "deterministic_even_vertex_index_sampling_v1",
            "magnitude_thresholds": list(self.magnitude_thresholds),
            "maximum_source_vertices": self.maximum_source_vertices,
            "maximum_model_triangles": self.maximum_model_triangles,
        }


@dataclass(frozen=True, slots=True)
class HeatmapColorBin:
    bin_id: str
    sign: str
    minimum_magnitude: float | None
    maximum_magnitude: float | None
    rgba: tuple[float, float, float, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "bin_id": self.bin_id,
            "sign": self.sign,
            "minimum_magnitude": self.minimum_magnitude,
            "maximum_magnitude": self.maximum_magnitude,
            "rgba": list(self.rgba),
        }


def _color_bins(policy: HeatmapPolicy) -> tuple[HeatmapColorBin, ...]:
    bins: list[HeatmapColorBin] = []
    thresholds = policy.magnitude_thresholds
    if policy.sign_policy is DistanceSignPolicy.UNSIGNED:
        for index, color in enumerate(_PALETTE_UNSIGNED[: len(thresholds) + 1]):
            bins.append(
                HeatmapColorBin(
                    f"unsigned_{index}",
                    "unsigned",
                    0.0 if index == 0 else thresholds[index - 1],
                    thresholds[index] if index < len(thresholds) else None,
                    color,
                )
            )
        return tuple(bins)
    bins.append(HeatmapColorBin("zero", "zero", 0.0, 0.0, _COLOR_ZERO))
    for sign, palette in (("negative", _PALETTE_NEGATIVE), ("positive", _PALETTE_POSITIVE)):
        for index, color in enumerate(palette[: len(thresholds) + 1]):
            bins.append(
                HeatmapColorBin(
                    f"{sign}_{index}",
                    sign,
                    0.0 if index == 0 else thresholds[index - 1],
                    thresholds[index] if index < len(thresholds) else None,
                    color,
                )
            )
    return tuple(bins)


def _bin_index(distance: float, policy: HeatmapPolicy) -> int:
    magnitude_index = bisect.bisect_left(policy.magnitude_thresholds, abs(distance))
    if policy.sign_policy is DistanceSignPolicy.UNSIGNED:
        return magnitude_index
    band_count = len(policy.magnitude_thresholds) + 1
    if distance == 0.0:
        return 0
    offset = 1 if distance < 0.0 else 1 + band_count
    return offset + magnitude_index


@dataclass(frozen=True, slots=True)
class ScanDesignHeatmap:
    heatmap_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    design_model_revision_id: str
    design_model_geometry_sha256: str
    scale_state: ScaleState
    scale_provenance_id: str
    coordinate_frame_id: str
    distance_units: str
    policy: HeatmapPolicy
    source_vertex_count: int
    sampled_vertex_indices: tuple[int, ...]
    signed_distances: tuple[float, ...]
    color_bin_indices: tuple[int, ...]
    color_bins: tuple[HeatmapColorBin, ...]
    target_watertight: bool
    physical_accuracy_validation_status: str = _DEFERRED
    tolerance_interpretation: str = "GEOMETRY_DEVIATION_ONLY_NOT_MANUFACTURING_TOLERANCE"
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.scan-design-heatmap.v1",
            "heatmap_id": self.heatmap_id,
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "design_model_revision_id": self.design_model_revision_id,
                "design_model_geometry_sha256": self.design_model_geometry_sha256,
                "design_model_fitted_to_scan_master_revision_id": self.scan_master_revision_id,
            },
            "scale": {
                "state": self.scale_state.value,
                "provenance_id": self.scale_provenance_id,
                "coordinate_frame_id": self.coordinate_frame_id,
                "distance_units": self.distance_units,
                "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
                "mold_use_authorized": self.mold_use_authorized,
            },
            "policy": self.policy.as_dict(),
            "sampling": {
                "source_vertex_count": self.source_vertex_count,
                "sampled_vertex_indices": list(self.sampled_vertex_indices),
                "sample_count": len(self.signed_distances),
            },
            "signed_distances": list(self.signed_distances),
            "color_bin_indices": list(self.color_bin_indices),
            "color_bins": [item.as_dict() for item in self.color_bins],
            "target_watertight": self.target_watertight,
            "tolerance_interpretation": self.tolerance_interpretation,
        }


def compute_scan_design_heatmap(
    scan_master: ScanMasterRevision,
    design_model: DesignModelGeometryReference,
    *,
    policy: HeatmapPolicy = HeatmapPolicy(),
    adapter: Open3DGeometryAdapter | None = None,
) -> ScanDesignHeatmap:
    """Compare sampled Scan Master vertices to a pinned supplied Design Model mesh."""

    if not isinstance(scan_master, ScanMasterRevision):
        raise HeatmapError("scan_master_revision_required")
    if not isinstance(design_model, DesignModelGeometryReference):
        raise HeatmapError("explicit_design_model_geometry_reference_required")
    if not isinstance(policy, HeatmapPolicy):
        raise HeatmapError("heatmap_policy_required")
    try:
        scan_input = RegistrationRevision.from_scan_master(scan_master)
    except RegistrationError as error:
        raise HeatmapError("scan_master_parent_manifest_invalid") from error
    if design_model.project_id != scan_master.project_id:
        raise HeatmapError("design_model_project_mismatch")
    if design_model.fitted_to_scan_master_revision_id != scan_master.revision_id:
        raise HeatmapError("design_model_parent_stale")
    if (
        design_model.scale_state is not scan_input.scale_state
        or design_model.scale_provenance_id != scan_input.scale_provenance_id
        or design_model.coordinate_frame_id != scan_input.coordinate_frame_id
    ):
        raise HeatmapError("design_model_coordinate_or_scale_mismatch")
    if len(design_model.mesh.triangles) > policy.maximum_model_triangles:
        raise HeatmapError("design_model_triangle_limit_exceeded")
    source_vertices = scan_master.mesh.vertices
    if len(source_vertices) > policy.maximum_source_vertices:
        raise HeatmapError("scan_master_vertex_limit_exceeded")
    sample_count = min(len(source_vertices), policy.sample_count)
    if sample_count == 0:
        raise HeatmapError("scan_master_mesh_empty")
    indices: tuple[int, ...]
    if sample_count == 1:
        indices = (0,)
    else:
        indices = tuple(
            (sample * (len(source_vertices) - 1)) // (sample_count - 1)
            for sample in range(sample_count)
        )
    query_points = tuple(source_vertices[index] for index in indices)
    backend = Open3DGeometryAdapter() if adapter is None else adapter
    try:
        distance_output: MeshSurfaceDistanceOutput = backend.compute_mesh_surface_distances(
            design_model.mesh,
            PointCloudData(query_points),
            signed=policy.sign_policy is DistanceSignPolicy.SIGNED_INSIDE_NEGATIVE,
            maximum_query_points=policy.sample_count,
        )
    except (GeometryAdapterError, RuntimeError, ValueError) as error:
        if isinstance(error, HeatmapError):
            raise
        raise HeatmapError("geometry_adapter_surface_distance_failed") from error
    if len(distance_output.distances) != sample_count or distance_output.signed != (
        policy.sign_policy is DistanceSignPolicy.SIGNED_INSIDE_NEGATIVE
    ):
        raise HeatmapError("surface_distance_sample_count_mismatch")
    if policy.sign_policy is DistanceSignPolicy.SIGNED_INSIDE_NEGATIVE and (
        not distance_output.target_watertight or distance_output.target_self_intersecting
    ):
        raise HeatmapError("signed_distance_target_not_closed_or_intersecting")
    bins = _color_bins(policy)
    bin_indices = tuple(_bin_index(value, policy) for value in distance_output.distances)
    scale_unit = _scale_unit(scan_input.scale_state)
    identity = {
        "scan_master_revision_id": scan_master.revision_id,
        "scan_master_geometry_sha256": mesh_sha256(scan_master.mesh),
        "design_model_revision_id": design_model.revision_id,
        "design_model_geometry_sha256": design_model.geometry_sha256,
        "scale_state": scan_input.scale_state.value,
        "scale_provenance_id": scan_input.scale_provenance_id,
        "coordinate_frame_id": scan_input.coordinate_frame_id,
        "policy": policy.as_dict(),
        "sampled_vertex_indices": indices,
        "signed_distances": distance_output.distances,
        "color_bin_indices": bin_indices,
    }
    return ScanDesignHeatmap(
        "scan-design-heatmap:" + _hash(identity),
        scan_master.revision_id,
        mesh_sha256(scan_master.mesh),
        design_model.revision_id,
        design_model.geometry_sha256,
        scan_input.scale_state,
        scan_input.scale_provenance_id,
        scan_input.coordinate_frame_id,
        scale_unit,
        policy,
        len(source_vertices),
        indices,
        distance_output.distances,
        bin_indices,
        bins,
        distance_output.target_watertight,
    )
