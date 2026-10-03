"""Deterministic Scan Master and Design Model plane-section overlays."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum

from .reconstruction import ScaleState
from .repeat_scan_registration import RegistrationError, RegistrationRevision
from .scan_design_heatmap import DesignModelGeometryReference
from .scan_master import ScanMasterRevision, mesh_sha256

MAX_PARENT_TRIANGLES = 100_000
MAX_SECTION_SEGMENTS = 10_000
MAX_DEVIATION_SAMPLES = 1_000
_DEFERRED = "DEFERRED_OWNER_VALIDATION"

Point2 = tuple[float, float]
Segment2 = tuple[Point2, Point2]


class CrossSectionOverlayError(ValueError):
    """Raised when selected parents cannot produce a trustworthy overlay."""


class CanonicalAxis(StrEnum):
    X = "x"
    Y = "y"
    Z = "z"


@dataclass(frozen=True, slots=True)
class CanonicalPlaneSelection:
    axis: CanonicalAxis
    position: float

    def __post_init__(self) -> None:
        if not isinstance(self.axis, CanonicalAxis):
            raise CrossSectionOverlayError("canonical_plane_axis_invalid")
        if (
            isinstance(self.position, bool)
            or not isinstance(self.position, (int, float))
            or not math.isfinite(self.position)
        ):
            raise CrossSectionOverlayError("canonical_plane_position_must_be_finite")
        object.__setattr__(self, "position", float(self.position))

    @property
    def normal_index(self) -> int:
        return {CanonicalAxis.X: 0, CanonicalAxis.Y: 1, CanonicalAxis.Z: 2}[self.axis]

    @property
    def in_plane_axes(self) -> tuple[int, int]:
        # The ordered basis satisfies U x V = the selected positive canonical normal.
        return {
            CanonicalAxis.X: (1, 2),
            CanonicalAxis.Y: (2, 0),
            CanonicalAxis.Z: (0, 1),
        }[self.axis]

    def as_dict(self, units: str) -> dict[str, object]:
        return {
            "kind": "canonical_axis_plane",
            "axis": self.axis.value,
            "position": self.position,
            "u_axis": ("x", "y", "z")[self.in_plane_axes[0]],
            "v_axis": ("x", "y", "z")[self.in_plane_axes[1]],
            "units": units,
        }


@dataclass(frozen=True, slots=True)
class OverlayDeviationSummary:
    direction: str
    sample_count: int
    minimum: float
    mean: float
    maximum: float

    def as_dict(self) -> dict[str, object]:
        return {
            "direction": self.direction,
            "sample_count": self.sample_count,
            "minimum": self.minimum,
            "mean": self.mean,
            "maximum": self.maximum,
        }


@dataclass(frozen=True, slots=True)
class MeshSectionOverlay:
    parent_revision_id: str
    parent_geometry_sha256: str
    segments: tuple[Segment2, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "parent_revision_id": self.parent_revision_id,
            "parent_geometry_sha256": self.parent_geometry_sha256,
            "segments": [[list(start), list(end)] for start, end in self.segments],
            "segment_count": len(self.segments),
            "authority": "DERIVED_OVERLAY_ONLY",
            "closure_invented": False,
        }


@dataclass(frozen=True, slots=True)
class CrossSectionOverlay:
    overlay_id: str
    scan_master_revision_id: str
    design_model_revision_id: str
    scan_master_geometry_sha256: str
    design_model_geometry_sha256: str
    scale_state: ScaleState
    scale_provenance_id: str
    coordinate_frame_id: str
    coordinate_unit: str
    plane: CanonicalPlaneSelection
    scan_master_section: MeshSectionOverlay
    design_model_section: MeshSectionOverlay
    scan_to_design: OverlayDeviationSummary
    design_to_scan: OverlayDeviationSummary
    physical_accuracy_validation_status: str = _DEFERRED
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.cross-section-overlay.v1",
            "overlay_id": self.overlay_id,
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
                "coordinate_unit": self.coordinate_unit,
                "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
                "mold_use_authorized": self.mold_use_authorized,
            },
            "plane": self.plane.as_dict(self.coordinate_unit),
            "sections": {
                "scan_master": self.scan_master_section.as_dict(),
                "design_model": self.design_model_section.as_dict(),
            },
            "deviation_summary": {
                "method": "symmetric_nearest_section_vertex_to_segment_v1",
                "sampling_policy": {
                    "method": "deterministic_even_index_unique_section_vertices",
                    "maximum_samples_per_direction": MAX_DEVIATION_SAMPLES,
                },
                "units": self.coordinate_unit,
                "scan_to_design": self.scan_to_design.as_dict(),
                "design_to_scan": self.design_to_scan.as_dict(),
                "is_manufacturing_tolerance": False,
            },
            "surface_interpolation": "linear_intersection_with_existing_mesh_triangles_only",
            "captured_evidence_interpolated": False,
            "closure_invented": False,
            "authority_class": "DERIVED_OVERLAY_ONLY",
        }


def _scale_unit(scale_state: ScaleState) -> str:
    if scale_state is ScaleState.RELATIVE:
        return "reconstruction_units"
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        return "mm_unverified"
    raise CrossSectionOverlayError(
        "metric_verified_overlay_forbidden_while_physical_validation_deferred"
    )


def _edge_intersection(
    first_index: int,
    second_index: int,
    vertices: tuple[tuple[float, float, float], ...],
    axis: int,
    position: float,
) -> tuple[float, float, float] | None:
    first, second = sorted((first_index, second_index))
    point_a, point_b = vertices[first], vertices[second]
    distance_a = point_a[axis] - position
    distance_b = point_b[axis] - position
    if distance_a == 0.0:
        return point_a
    if distance_b == 0.0:
        return point_b
    if (distance_a < 0.0) == (distance_b < 0.0):
        return None
    ratio = distance_a / (distance_a - distance_b)
    return tuple(point_a[i] + ratio * (point_b[i] - point_a[i]) for i in range(3))  # type: ignore[return-value]


def _section_segments(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
    plane: CanonicalPlaneSelection,
) -> tuple[Segment2, ...]:
    axis = plane.normal_index
    in_plane = plane.in_plane_axes
    segments: set[Segment2] = set()
    for face in triangles:
        if all(vertices[index][axis] == plane.position for index in face):
            raise CrossSectionOverlayError("canonical_plane_coplanar_with_mesh_face")
        points = {
            point
            for first, second in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0]))
            if (point := _edge_intersection(first, second, vertices, axis, plane.position))
            is not None
        }
        if len(points) < 2:
            continue
        projected = sorted((point[in_plane[0]], point[in_plane[1]]) for point in points)
        if len(projected) > 2:
            raise CrossSectionOverlayError("triangle_plane_intersection_ambiguous")
        start, end = projected
        if start != end:
            segments.add((start, end))
            if len(segments) > MAX_SECTION_SEGMENTS:
                raise CrossSectionOverlayError("section_segment_limit_exceeded")
    ordered = tuple(sorted(segments))
    if not ordered:
        raise CrossSectionOverlayError("selected_plane_has_no_mesh_section")
    return ordered


def _segment_distance(point: Point2, segment: Segment2) -> float:
    start, end = segment
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_squared = dx * dx + dy * dy
    if length_squared == 0.0:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    ratio = max(
        0.0,
        min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_squared),
    )
    return math.hypot(point[0] - (start[0] + ratio * dx), point[1] - (start[1] + ratio * dy))


def _unique_vertices(segments: tuple[Segment2, ...]) -> tuple[Point2, ...]:
    return tuple(sorted({point for segment in segments for point in segment}))


def _sample(points: tuple[Point2, ...]) -> tuple[Point2, ...]:
    count = min(len(points), MAX_DEVIATION_SAMPLES)
    if count == 1:
        return points[:1]
    return tuple(points[(index * (len(points) - 1)) // (count - 1)] for index in range(count))


def _deviation(
    source: tuple[Segment2, ...], target: tuple[Segment2, ...], direction: str
) -> OverlayDeviationSummary:
    distances = tuple(
        min(_segment_distance(point, segment) for segment in target)
        for point in _sample(_unique_vertices(source))
    )
    if not distances or any(not math.isfinite(distance) for distance in distances):
        raise CrossSectionOverlayError("section_deviation_summary_invalid")
    return OverlayDeviationSummary(
        direction,
        len(distances),
        min(distances),
        math.fsum(distances) / len(distances),
        max(distances),
    )


def compare_scan_design_cross_sections(
    scan_master: ScanMasterRevision,
    design_model: DesignModelGeometryReference,
    plane: CanonicalPlaneSelection,
) -> CrossSectionOverlay:
    """Intersect existing parent triangles with an explicit canonical plane."""

    if not isinstance(scan_master, ScanMasterRevision):
        raise CrossSectionOverlayError("scan_master_revision_required")
    if not isinstance(design_model, DesignModelGeometryReference):
        raise CrossSectionOverlayError("explicit_design_model_geometry_reference_required")
    if not isinstance(plane, CanonicalPlaneSelection):
        raise CrossSectionOverlayError("explicit_canonical_plane_required")
    if not scan_master.mesh.vertices or not scan_master.mesh.triangles:
        raise CrossSectionOverlayError("scan_master_mesh_evidence_empty")
    if not design_model.mesh.vertices or not design_model.mesh.triangles:
        raise CrossSectionOverlayError("design_model_mesh_evidence_empty")
    try:
        scan_input = RegistrationRevision.from_scan_master(scan_master)
    except RegistrationError as error:
        raise CrossSectionOverlayError("scan_master_parent_manifest_invalid") from error
    if len(scan_master.mesh.triangles) > MAX_PARENT_TRIANGLES:
        raise CrossSectionOverlayError("scan_master_triangle_limit_exceeded")
    if len(design_model.mesh.triangles) > MAX_PARENT_TRIANGLES:
        raise CrossSectionOverlayError("design_model_triangle_limit_exceeded")
    if design_model.project_id != scan_master.project_id:
        raise CrossSectionOverlayError("design_model_project_mismatch")
    if design_model.fitted_to_scan_master_revision_id != scan_master.revision_id:
        raise CrossSectionOverlayError("design_model_parent_stale")
    if (
        design_model.scale_state is not scan_input.scale_state
        or design_model.scale_provenance_id != scan_input.scale_provenance_id
        or design_model.coordinate_frame_id != scan_input.coordinate_frame_id
    ):
        raise CrossSectionOverlayError("design_model_coordinate_or_scale_mismatch")
    try:
        coordinate_unit = _scale_unit(scan_input.scale_state)
        scan_segments = _section_segments(
            scan_master.mesh.vertices, scan_master.mesh.triangles, plane
        )
        design_segments = _section_segments(
            design_model.mesh.vertices, design_model.mesh.triangles, plane
        )
        scan_section = MeshSectionOverlay(
            scan_master.revision_id, mesh_sha256(scan_master.mesh), scan_segments
        )
        design_section = MeshSectionOverlay(
            design_model.revision_id, design_model.geometry_sha256, design_segments
        )
        scan_to_design = _deviation(scan_segments, design_segments, "scan_master_to_design_model")
        design_to_scan = _deviation(design_segments, scan_segments, "design_model_to_scan_master")
    except (ArithmeticError, ValueError) as error:
        if isinstance(error, CrossSectionOverlayError):
            raise
        raise CrossSectionOverlayError("cross_section_geometry_computation_failed") from error
    body: dict[str, object] = {
        "parents": {
            "scan_master_revision_id": scan_master.revision_id,
            "scan_master_geometry_sha256": mesh_sha256(scan_master.mesh),
            "design_model_revision_id": design_model.revision_id,
            "design_model_geometry_sha256": design_model.geometry_sha256,
        },
        "plane": plane.as_dict(coordinate_unit),
        "scan_segments": scan_segments,
        "design_segments": design_segments,
        "scan_to_design": scan_to_design.as_dict(),
        "design_to_scan": design_to_scan.as_dict(),
        "scale_state": scan_input.scale_state.value,
        "scale_provenance_id": scan_input.scale_provenance_id,
        "coordinate_frame_id": scan_input.coordinate_frame_id,
    }
    overlay_id = (
        "cross-section-overlay:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return CrossSectionOverlay(
        overlay_id,
        scan_master.revision_id,
        design_model.revision_id,
        mesh_sha256(scan_master.mesh),
        design_model.geometry_sha256,
        scan_input.scale_state,
        scan_input.scale_provenance_id,
        scan_input.coordinate_frame_id,
        coordinate_unit,
        plane,
        scan_section,
        design_section,
        scan_to_design,
        design_to_scan,
    )


def serialize_cross_section_overlay(overlay: CrossSectionOverlay) -> bytes:
    return json.dumps(
        overlay.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


__all__ = [
    "CanonicalAxis",
    "CanonicalPlaneSelection",
    "CrossSectionOverlay",
    "CrossSectionOverlayError",
    "MeshSectionOverlay",
    "OverlayDeviationSummary",
    "compare_scan_design_cross_sections",
    "serialize_cross_section_overlay",
]
