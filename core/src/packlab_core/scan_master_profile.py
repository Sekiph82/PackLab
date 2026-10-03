"""Observed vertical profile evidence extracted from one exact Scan Master mesh."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .cross_section_overlay import CanonicalAxis
from .design_model_binding import DesignModelParentBindingRevision, bind_design_model_parent
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

PROFILE_CONTRACT = "packlab.scan-master-vertical-profile.v1"
MAX_PROFILE_VERTICES = 100_000
MAX_PROFILE_BANDS = 2048
type Point3 = tuple[float, float, float]


class ScanMasterProfileError(ValueError):
    """Raised when profile extraction lacks bounded, current parent evidence."""


@dataclass(frozen=True, slots=True)
class ObservedProfileBand:
    band_index: int
    requested_axis_position: float
    observed_axis_minimum: float | None
    observed_axis_maximum: float | None
    horizontal_minimum: float | None
    horizontal_maximum: float | None
    source_vertex_indices: tuple[int, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "band_index": self.band_index,
            "requested_axis_position": self.requested_axis_position,
            "observed_axis_minimum": self.observed_axis_minimum,
            "observed_axis_maximum": self.observed_axis_maximum,
            "horizontal_minimum": self.horizontal_minimum,
            "horizontal_maximum": self.horizontal_maximum,
            "sample_count": len(self.source_vertex_indices),
            "source_vertex_indices": list(self.source_vertex_indices),
        }


@dataclass(frozen=True, slots=True)
class ProfileOutlier:
    source_vertex_index: int
    captured_point: tuple[float, float, float]
    band_index: int
    horizontal_value: float
    robust_center: float
    absolute_deviation: float
    rejection_threshold: float

    def as_dict(self) -> dict[str, object]:
        return {
            "source_vertex_index": self.source_vertex_index,
            "captured_point": list(self.captured_point),
            "band_index": self.band_index,
            "horizontal_value": self.horizontal_value,
            "robust_center": self.robust_center,
            "absolute_deviation": self.absolute_deviation,
            "rejection_threshold": self.rejection_threshold,
            "disposition": "REJECTED_FROM_PROFILE_SUMMARY_SOURCE_RETAINED",
        }


@dataclass(frozen=True, slots=True)
class ProfileCoverageGap:
    band_index: int
    requested_axis_position: float
    accepted_sample_count: int
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "band_index": self.band_index,
            "requested_axis_position": self.requested_axis_position,
            "accepted_sample_count": self.accepted_sample_count,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ScanMasterVerticalProfile:
    profile_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    parent_binding: DesignModelParentBindingRevision
    axis: CanonicalAxis
    plane_origin: tuple[float, float, float]
    front_direction: tuple[float, float, float]
    plane_normal: tuple[float, float, float]
    lateral_tolerance: float
    outlier_mad_multiplier: float
    minimum_band_samples: int
    scale_state: ScaleState
    coordinate_unit: str
    bands: tuple[ObservedProfileBand, ...]
    outliers: tuple[ProfileOutlier, ...]
    coverage_gaps: tuple[ProfileCoverageGap, ...]
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False
    closure_invented: bool = False
    smoothing_applied: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": PROFILE_CONTRACT,
            "profile_id": self.profile_id,
            "parent": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "design_model_parent_binding": self.parent_binding.as_dict(),
            },
            "context": {
                "axis": self.axis.value,
                "plane_origin": list(self.plane_origin),
                "front_direction": list(self.front_direction),
                "plane_normal": list(self.plane_normal),
                "lateral_tolerance": self.lateral_tolerance,
            },
            "sampling_policy": {
                "type": "bounded_equal_axis_bands_from_scan_master_vertices_v1",
                "band_count": len(self.bands) + len(self.coverage_gaps),
                "minimum_band_samples": self.minimum_band_samples,
                "outlier_method": "per_band_median_absolute_deviation_v1",
                "outlier_mad_multiplier": self.outlier_mad_multiplier,
                "smoothing_applied": False,
                "interpolation_applied": False,
                "closure_invented": False,
            },
            "scale": {
                "state": self.scale_state.value,
                "coordinate_unit": self.coordinate_unit,
                "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
                "mold_use_authorized": self.mold_use_authorized,
            },
            "bands": [item.as_dict() for item in self.bands],
            "outliers": [item.as_dict() for item in self.outliers],
            "coverage_gaps": [item.as_dict() for item in self.coverage_gaps],
            "authority_class": "SCAN_MASTER_DERIVED_PROFILE_EVIDENCE",
            "closure_invented": self.closure_invented,
            "smoothing_applied": self.smoothing_applied,
        }


def extract_scan_master_vertical_profile(
    scan_master: ScanMasterRevision,
    *,
    expected_scan_master_revision_id: str,
    axis: CanonicalAxis,
    plane_origin: tuple[float, float, float],
    front_direction: tuple[float, float, float],
    lateral_tolerance: float,
    band_count: int,
    minimum_band_samples: int,
    outlier_mad_multiplier: float,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> ScanMasterVerticalProfile:
    """Project observed in-plane mesh vertices into bounded ordered height bands."""
    if not isinstance(scan_master, ScanMasterRevision):
        raise ScanMasterProfileError("scan_master_revision_required")
    if scan_master.revision_id != expected_scan_master_revision_id:
        raise ScanMasterProfileError("scan_master_parent_stale")
    if not isinstance(axis, CanonicalAxis):
        raise ScanMasterProfileError("canonical_vertical_axis_required")
    if not isinstance(plane_origin, tuple) or len(plane_origin) != 3:
        raise ScanMasterProfileError("profile_plane_origin_invalid")
    if any(not _finite_number(value) for value in plane_origin):
        raise ScanMasterProfileError("profile_plane_origin_invalid")
    _bounded_int(band_count, 3, MAX_PROFILE_BANDS, "profile_band_count_out_of_range")
    _bounded_int(minimum_band_samples, 2, 1000, "profile_minimum_samples_out_of_range")
    if not _finite_number(lateral_tolerance) or lateral_tolerance <= 0:
        raise ScanMasterProfileError("profile_lateral_tolerance_invalid")
    if not _finite_number(outlier_mad_multiplier) or not 1.0 <= outlier_mad_multiplier <= 20.0:
        raise ScanMasterProfileError("profile_outlier_multiplier_out_of_range")
    if len(scan_master.mesh.vertices) > MAX_PROFILE_VERTICES:
        raise ScanMasterProfileError("profile_source_vertex_limit_exceeded")
    if not scan_master.mesh.vertices or not scan_master.mesh.triangles:
        raise ScanMasterProfileError("scan_master_mesh_evidence_empty")
    extents = tuple(
        max(point[axis_index] for point in scan_master.mesh.vertices)
        - min(point[axis_index] for point in scan_master.mesh.vertices)
        for axis_index in range(3)
    )
    source_diagonal = math.sqrt(math.fsum(value * value for value in extents))
    if source_diagonal <= 0 or lateral_tolerance > source_diagonal:
        raise ScanMasterProfileError("profile_lateral_tolerance_out_of_geometry_bounds")

    manifest = scan_master.manifest
    digest = mesh_sha256(scan_master.mesh)
    if (
        manifest.get("scan_master_revision_id") != scan_master.revision_id
        or manifest.get("project_id") != scan_master.project_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != digest
        or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or manifest.get("mold_use_authorized") is not False
    ):
        raise ScanMasterProfileError("scan_master_authority_or_digest_invalid")
    try:
        scale_state = ScaleState(str(manifest.get("scale_state")))
    except ValueError as error:
        raise ScanMasterProfileError("scan_master_scale_state_invalid") from error
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise ScanMasterProfileError("scan_master_scale_state_unauthorized")
    scale_provenance = manifest.get("scale_provenance_id")
    if not isinstance(scale_provenance, str) or not scale_provenance:
        raise ScanMasterProfileError("scan_master_scale_provenance_missing")
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"

    axis_vector = _axis_vector(axis)
    front = _unit_vector(front_direction, "profile_front_direction_invalid")
    if abs(_dot(axis_vector, front)) > 1e-9:
        raise ScanMasterProfileError("profile_front_direction_must_be_transverse")
    normal = _normalize(_cross(axis_vector, front))
    origin = (float(plane_origin[0]), float(plane_origin[1]), float(plane_origin[2]))
    projected = _project_vertices(
        scan_master.mesh.vertices, origin, axis_vector, front, normal, float(lateral_tolerance)
    )
    if len(projected) < band_count * minimum_band_samples:
        # Sparse sources are represented in the result when there are still enough observations overall.
        if len(projected) < minimum_band_samples:
            raise ScanMasterProfileError("profile_insufficient_in_plane_observations")
    axis_values = tuple(item[3] for item in projected)
    lower, upper = min(axis_values), max(axis_values)
    if upper <= lower:
        raise ScanMasterProfileError("profile_vertical_range_degenerate")
    binding = bind_design_model_parent(
        scan_master,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )

    buckets: list[list[tuple[int, tuple[float, float, float], float, float]]] = [
        [] for _ in range(band_count)
    ]
    for index, point, horizontal, vertical in projected:
        band_index = min(
            band_count - 1,
            max(0, int((vertical - lower) / (upper - lower) * band_count)),
        )
        buckets[band_index].append((index, point, horizontal, vertical))

    bands: list[ObservedProfileBand] = []
    outliers: list[ProfileOutlier] = []
    gaps: list[ProfileCoverageGap] = []
    width = (upper - lower) / band_count
    for index, bucket in enumerate(buckets):
        requested_position = lower + (index + 0.5) * width
        if not bucket:
            gaps.append(
                ProfileCoverageGap(index, requested_position, 0, "no_in_plane_observations")
            )
            continue
        horizontal_values = tuple(item[2] for item in bucket)
        center = _median(horizontal_values)
        side_centers: dict[int, tuple[float, float]] = {}
        for side in (-1, 1):
            side_values = tuple(
                value for value in horizontal_values if (-1 if value < center else 1) == side
            )
            if side_values:
                side_center = _median(side_values)
                side_mad = _median(tuple(abs(value - side_center) for value in side_values))
                side_centers[side] = (
                    side_center,
                    max(lateral_tolerance, outlier_mad_multiplier * 1.4826 * side_mad),
                )
        accepted: list[tuple[int, tuple[float, float, float], float, float]] = []
        for sample in bucket:
            side_center, threshold = side_centers[-1 if sample[2] < center else 1]
            deviation = abs(sample[2] - side_center)
            if deviation > threshold:
                outliers.append(
                    ProfileOutlier(
                        sample[0], sample[1], index, sample[2], side_center, deviation, threshold
                    )
                )
            else:
                accepted.append(sample)
        if len(accepted) < minimum_band_samples:
            gaps.append(
                ProfileCoverageGap(
                    index, requested_position, len(accepted), "below_minimum_samples"
                )
            )
            continue
        horizontal_values = tuple(item[2] for item in accepted)
        vertical_values = tuple(item[3] for item in accepted)
        bands.append(
            ObservedProfileBand(
                index,
                requested_position,
                min(vertical_values),
                max(vertical_values),
                min(horizontal_values),
                max(horizontal_values),
                tuple(item[0] for item in accepted),
            )
        )
    identity = {
        "contract": PROFILE_CONTRACT,
        "scan_master_revision_id": scan_master.revision_id,
        "scan_master_geometry_sha256": digest,
        "parent_binding": binding.as_dict(),
        "axis": axis.value,
        "plane_origin": origin,
        "front_direction": front,
        "plane_normal": normal,
        "lateral_tolerance": lateral_tolerance,
        "band_count": band_count,
        "minimum_band_samples": minimum_band_samples,
        "outlier_mad_multiplier": outlier_mad_multiplier,
        "scale_state": scale_state.value,
        "coordinate_unit": unit,
        "bands": [item.as_dict() for item in bands],
        "outliers": [item.as_dict() for item in outliers],
        "coverage_gaps": [item.as_dict() for item in gaps],
    }
    profile_id = (
        "scan-master-profile:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    return ScanMasterVerticalProfile(
        profile_id,
        scan_master.revision_id,
        digest,
        binding,
        axis,
        origin,
        front,
        normal,
        float(lateral_tolerance),
        float(outlier_mad_multiplier),
        minimum_band_samples,
        scale_state,
        unit,
        tuple(bands),
        tuple(outliers),
        tuple(gaps),
    )


def _project_vertices(
    mesh_vertices: tuple[Point3, ...],
    origin: Point3,
    axis: Point3,
    front: Point3,
    normal: Point3,
    lateral_tolerance: float,
) -> tuple[tuple[int, Point3, float, float], ...]:
    projected: list[tuple[int, Point3, float, float]] = []
    for index, point in enumerate(mesh_vertices):
        delta: Point3 = tuple(point[dimension] - origin[dimension] for dimension in range(3))  # type: ignore[assignment]
        lateral = _dot(delta, normal)
        if abs(lateral) <= lateral_tolerance + _roundoff_tolerance(lateral, *point, *origin):
            projected.append((index, point, _dot(delta, front), _dot(delta, axis)))
    return tuple(projected)


def _median(values: tuple[float, ...]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2.0


def _axis_vector(axis: CanonicalAxis) -> tuple[float, float, float]:
    return {
        CanonicalAxis.X: (1.0, 0.0, 0.0),
        CanonicalAxis.Y: (0.0, 1.0, 0.0),
        CanonicalAxis.Z: (0.0, 0.0, 1.0),
    }[axis]


def _unit_vector(value: tuple[float, float, float], error: str) -> tuple[float, float, float]:
    if (
        not isinstance(value, tuple)
        or len(value) != 3
        or any(not _finite_number(item) for item in value)
    ):
        raise ScanMasterProfileError(error)
    norm = math.sqrt(math.fsum(component * component for component in value))
    if not math.isfinite(norm) or abs(norm - 1.0) > 1e-9:
        raise ScanMasterProfileError(error)
    return (float(value[0]), float(value[1]), float(value[2]))


def _dot(left: Point3, right: Point3) -> float:
    return math.fsum(left[index] * right[index] for index in range(3))


def _cross(left: Point3, right: Point3) -> Point3:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _normalize(value: Point3) -> Point3:
    length = math.sqrt(math.fsum(component * component for component in value))
    if length <= 0 or not math.isfinite(length):
        raise ScanMasterProfileError("profile_plane_normal_invalid")
    return (value[0] / length, value[1] / length, value[2] / length)


def _roundoff_tolerance(*values: float) -> float:
    return max((8.0 * math.ulp(value) for value in values), default=0.0)


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _bounded_int(value: int, minimum: int, maximum: int, error: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ScanMasterProfileError(error)


__all__ = [
    "MAX_PROFILE_BANDS",
    "MAX_PROFILE_VERTICES",
    "PROFILE_CONTRACT",
    "ObservedProfileBand",
    "ProfileCoverageGap",
    "ProfileOutlier",
    "ScanMasterProfileError",
    "ScanMasterVerticalProfile",
    "extract_scan_master_vertical_profile",
]
