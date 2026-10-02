"""Deterministic, revision-bound geometric diagnostics without accuracy claims."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass

from .component_cleanup import ComponentCleanupRevision
from .geometry_adapter import Point3, PointCloudData, TriangleMeshData
from .hole_detection import MeshHoleReport
from .reconstruction import ScaleState

GEOMETRY_STATISTICS_CONTRACT = "packlab.geometry-statistics.v1"
PHYSICAL_VALIDATION_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class GeometryStatisticsError(ValueError):
    """Raised when inputs are empty, degenerate, stale, or exceed a work bound."""


@dataclass(frozen=True, slots=True)
class GeometryStatisticsPolicy:
    maximum_points_or_vertices: int = 100_000
    maximum_faces: int = 1_000_000
    maximum_spacing_samples: int = 64

    def __post_init__(self) -> None:
        for name in (
            "maximum_points_or_vertices",
            "maximum_faces",
            "maximum_spacing_samples",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise GeometryStatisticsError(f"{name} must be a positive integer")
        if self.maximum_points_or_vertices > 100_000:
            raise GeometryStatisticsError("point/vertex bound exceeds 100000")
        if self.maximum_faces > 1_000_000:
            raise GeometryStatisticsError("face bound exceeds 1000000")
        if self.maximum_spacing_samples > 128:
            raise GeometryStatisticsError("spacing sample bound exceeds 128")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": GEOMETRY_STATISTICS_CONTRACT,
            "maximum_points_or_vertices": self.maximum_points_or_vertices,
            "maximum_faces": self.maximum_faces,
            "maximum_spacing_samples": self.maximum_spacing_samples,
            "spacing_estimator": "deterministic_even_index_sample_nearest_vertex_v1",
            "mesh_connectivity": "triangle_components_share_edge_v1",
        }


@dataclass(frozen=True, slots=True)
class GeometryStatistics:
    contract: str
    geometry_revision_id: str
    geometry_sha256: str
    geometry_kind: str
    scale_state: ScaleState
    scale_provenance_id: str | None
    coordinate_unit: str
    length_unit: str
    area_unit: str
    bounding_box_sample_density_unit: str
    point_count: int | None
    vertex_count: int | None
    face_count: int | None
    bounds_minimum: Point3
    bounds_maximum: Point3
    bounds_extent: Point3
    bounds_diagonal: float
    surface_area: float | None
    edge_length_minimum: float | None
    edge_length_mean: float | None
    edge_length_maximum: float | None
    connected_component_count: int | None
    connected_component_face_counts: tuple[int, ...] | None
    connected_component_status: str
    bounding_box_sample_density: float | None
    density_status: str
    sampled_nearest_vertex_spacing_minimum: float | None
    sampled_nearest_vertex_spacing_mean: float | None
    sampled_nearest_vertex_spacing_maximum: float | None
    spacing_sample_count: int
    hole_report_linkage: tuple[str, str, int, int] | None
    component_revision_linkage: tuple[str, str, int] | None
    topology_indicators: tuple[tuple[str, object], ...]
    interpretation: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    policy: GeometryStatisticsPolicy

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "geometry_revision_id": self.geometry_revision_id,
            "geometry_sha256": self.geometry_sha256,
            "geometry_kind": self.geometry_kind,
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "units": {
                "coordinate": self.coordinate_unit,
                "length": self.length_unit,
                "area": self.area_unit,
                "bounding_box_sample_density": self.bounding_box_sample_density_unit,
            },
            "counts": {
                "point_count": self.point_count,
                "vertex_count": self.vertex_count,
                "face_count": self.face_count,
            },
            "bounds": {
                "minimum": self.bounds_minimum,
                "maximum": self.bounds_maximum,
                "extent": self.bounds_extent,
                "diagonal": self.bounds_diagonal,
            },
            "surface_area": self.surface_area,
            "edge_lengths": {
                "minimum": self.edge_length_minimum,
                "mean": self.edge_length_mean,
                "maximum": self.edge_length_maximum,
            },
            "connected_components": {
                "count": self.connected_component_count,
                "face_counts": self.connected_component_face_counts,
                "status": self.connected_component_status,
            },
            "bounding_box_sample_density": self.bounding_box_sample_density,
            "density_status": self.density_status,
            "sampled_nearest_vertex_spacing": {
                "minimum": self.sampled_nearest_vertex_spacing_minimum,
                "mean": self.sampled_nearest_vertex_spacing_mean,
                "maximum": self.sampled_nearest_vertex_spacing_maximum,
                "sample_count": self.spacing_sample_count,
            },
            "hole_report_linkage": self.hole_report_linkage,
            "component_revision_linkage": self.component_revision_linkage,
            "topology_indicators": dict(self.topology_indicators),
            "interpretation": self.interpretation,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "policy": self.policy.as_dict(),
        }


def _digest(payload: object) -> str:
    value = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _safe_id(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise GeometryStatisticsError(f"{field} must be a non-empty stable identifier")
    if any(ord(char) < 32 for char in value):
        raise GeometryStatisticsError(f"{field} must not contain control characters")
    return value


def _mesh_payload(mesh: TriangleMeshData) -> dict[str, object]:
    return {
        "vertices": mesh.vertices,
        "triangles": mesh.triangles,
        "vertex_colors": mesh.vertex_colors,
        "vertex_normals": mesh.vertex_normals,
    }


def _cloud_payload(cloud: PointCloudData) -> dict[str, object]:
    return {"points": cloud.points, "colors": cloud.colors, "normals": cloud.normals}


def _units(state: ScaleState) -> tuple[str, str, str, str]:
    if state is ScaleState.RELATIVE:
        return (
            "reconstruction_units",
            "reconstruction_units",
            "reconstruction_units_squared",
            "points_or_vertices_per_reconstruction_unit_cubed_proxy",
        )
    return (
        "mm_unverified",
        "mm_unverified",
        "mm_unverified_squared",
        "points_or_vertices_per_mm_cubed_unverified_proxy",
    )


def _bounds(points: tuple[Point3, ...]) -> tuple[Point3, Point3, Point3, float]:
    minimum: Point3 = tuple(min(point[axis] for point in points) for axis in range(3))  # type: ignore[assignment]
    maximum: Point3 = tuple(max(point[axis] for point in points) for axis in range(3))  # type: ignore[assignment]
    extent: Point3 = tuple(maximum[axis] - minimum[axis] for axis in range(3))  # type: ignore[assignment]
    diagonal = math.sqrt(sum(value * value for value in extent))
    if diagonal <= 1e-15:
        raise GeometryStatisticsError("geometry bounds are degenerate")
    return minimum, maximum, extent, diagonal


def _component_face_counts(mesh: TriangleMeshData) -> tuple[int, ...]:
    edge_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    for face_index, face in enumerate(mesh.triangles):
        for first, second in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge_faces[(min(first, second), max(first, second))].append(face_index)
    neighbors: list[set[int]] = [set() for _ in mesh.triangles]
    for owners in edge_faces.values():
        for owner in owners:
            neighbors[owner].update(other for other in owners if other != owner)
    visited: set[int] = set()
    counts: list[int] = []
    for start in range(len(mesh.triangles)):
        if start in visited:
            continue
        visited.add(start)
        queue = [start]
        count = 0
        while queue:
            current = queue.pop()
            count += 1
            for neighbor in sorted(neighbors[current], reverse=True):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        counts.append(count)
    return tuple(sorted(counts, reverse=True))


def _mesh_geometry_metrics(
    mesh: TriangleMeshData,
) -> tuple[float, tuple[float, float, float], tuple[int, ...], int]:
    face_area_sum = 0.0
    edge_lengths: dict[tuple[int, int], float] = {}
    for face in mesh.triangles:
        a, b, c = (mesh.vertices[index] for index in face)
        ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        cross = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        double_area = math.sqrt(sum(value * value for value in cross))
        if double_area <= 1e-15:
            raise GeometryStatisticsError("mesh contains a degenerate triangle")
        face_area_sum += double_area * 0.5
        for first, second in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            key = (min(first, second), max(first, second))
            edge_lengths[key] = math.dist(mesh.vertices[first], mesh.vertices[second])
    if not edge_lengths:
        raise GeometryStatisticsError("mesh contains no measurable edges")
    lengths = tuple(edge_lengths.values())
    counts = _component_face_counts(mesh)
    return (
        face_area_sum,
        (min(lengths), sum(lengths) / len(lengths), max(lengths)),
        counts,
        len(edge_lengths),
    )


def _spacing(
    points: tuple[Point3, ...], maximum_samples: int
) -> tuple[float | None, float | None, float | None, int]:
    if len(points) < 2:
        return None, None, None, 0
    if len(points) <= maximum_samples:
        indices = tuple(range(len(points)))
    elif maximum_samples == 1:
        indices = (0,)
    else:
        indices = tuple(
            round(i * (len(points) - 1) / (maximum_samples - 1)) for i in range(maximum_samples)
        )
    distances = tuple(
        min(
            math.dist(points[index], candidate)
            for other_index, candidate in enumerate(points)
            if other_index != index
        )
        for index in indices
    )
    return min(distances), sum(distances) / len(distances), max(distances), len(distances)


def compute_geometry_statistics(
    geometry: TriangleMeshData | PointCloudData,
    *,
    geometry_revision_id: str,
    scale_state: ScaleState,
    scale_provenance_id: str | None = None,
    hole_report: MeshHoleReport | None = None,
    component_revision: ComponentCleanupRevision | None = None,
    policy: GeometryStatisticsPolicy = GeometryStatisticsPolicy(),
) -> GeometryStatistics:
    """Compute deterministic diagnostic counts, bounds, topology, density and spacing."""

    revision_id = _safe_id(geometry_revision_id, "geometry_revision_id")
    if not isinstance(scale_state, ScaleState) or scale_state is ScaleState.METRIC_VERIFIED:
        raise GeometryStatisticsError(
            "scale_state must preserve relative or metric-unverified state"
        )
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        scale_provenance_id = _safe_id(scale_provenance_id, "scale_provenance_id")
    elif scale_provenance_id is not None:
        scale_provenance_id = _safe_id(scale_provenance_id, "scale_provenance_id")

    topology: tuple[tuple[str, object], ...]
    if isinstance(geometry, TriangleMeshData):
        points = geometry.vertices
        if len(points) > policy.maximum_points_or_vertices:
            raise GeometryStatisticsError("vertex count exceeds configured work bound")
        if len(geometry.triangles) > policy.maximum_faces:
            raise GeometryStatisticsError("face count exceeds configured work bound")
        if not geometry.triangles:
            raise GeometryStatisticsError("triangle mesh must contain faces")
        payload = _mesh_payload(geometry)
        digest = _digest(payload)
        minimum, maximum, extent, diagonal = _bounds(points)
        surface_area, edge_stats, component_counts, edge_count = _mesh_geometry_metrics(geometry)
        point_count = None
        vertex_count = len(points)
        face_count = len(geometry.triangles)
        component_status = "EDGE_CONNECTED_TRIANGLE_COMPONENTS"
        topology = (
            ("unique_edge_count", edge_count),
            (
                "boundary_edge_count",
                sum(1 for edges in _mesh_edge_face_counts(geometry).values() if edges == 1),
            ),
            (
                "nonmanifold_edge_count",
                sum(1 for edges in _mesh_edge_face_counts(geometry).values() if edges > 2),
            ),
        )
        hole_linkage = None
        if hole_report is not None:
            if (
                hole_report.parent_revision_id != revision_id
                or hole_report.parent_geometry_sha256 != digest
            ):
                raise GeometryStatisticsError("hole report is stale or bound to different geometry")
            hole_linkage = (
                hole_report.report_id,
                hole_report.disposition,
                len(hole_report.loops),
                len(hole_report.unresolved_components),
            )
        component_linkage = None
        if component_revision is not None:
            if (
                component_revision.child_revision_id != revision_id
                or component_revision.geometry_sha256 != digest
                or component_revision.mesh != geometry
            ):
                raise GeometryStatisticsError("component revision linkage does not match geometry")
            component_linkage = (
                component_revision.child_revision_id,
                component_revision.parent_revision_id,
                len(component_revision.removed_components),
            )
    elif isinstance(geometry, PointCloudData):
        points = geometry.points
        if len(points) > policy.maximum_points_or_vertices:
            raise GeometryStatisticsError("point count exceeds configured work bound")
        if not points:
            raise GeometryStatisticsError("point cloud must contain points")
        payload = _cloud_payload(geometry)
        digest = _digest(payload)
        minimum, maximum, extent, diagonal = _bounds(points)
        surface_area = None
        edge_stats = None
        component_counts = None
        edge_count = 0
        point_count = len(points)
        vertex_count = None
        face_count = None
        component_status = "NOT_APPLICABLE_POINT_CLOUD_NO_CONNECTIVITY_RADIUS_POLICY"
        topology = (("duplicate_point_count", len(points) - len(set(points))),)
        hole_linkage = None
        if hole_report is not None:
            raise GeometryStatisticsError("mesh hole report cannot link to point-cloud geometry")
        if component_revision is not None:
            raise GeometryStatisticsError(
                "mesh component revision cannot link to point-cloud geometry"
            )
        component_linkage = None
    else:
        raise GeometryStatisticsError("geometry must be PackLab PointCloudData or TriangleMeshData")

    density_count = point_count if point_count is not None else vertex_count
    assert density_count is not None
    box_volume = extent[0] * extent[1] * extent[2]
    density = density_count / box_volume if box_volume > 1e-18 else None
    density_status = (
        "BOUNDS_VOLUME_AVAILABLE" if density is not None else "ZERO_BOUNDS_VOLUME_PROXY_UNAVAILABLE"
    )
    spacing_minimum, spacing_mean, spacing_maximum, spacing_count = _spacing(
        points, policy.maximum_spacing_samples
    )
    coordinate_unit, length_unit, area_unit, density_unit = _units(scale_state)
    return GeometryStatistics(
        contract=GEOMETRY_STATISTICS_CONTRACT,
        geometry_revision_id=revision_id,
        geometry_sha256=digest,
        geometry_kind="triangle_mesh" if isinstance(geometry, TriangleMeshData) else "point_cloud",
        scale_state=scale_state,
        scale_provenance_id=scale_provenance_id,
        coordinate_unit=coordinate_unit,
        length_unit=length_unit,
        area_unit=area_unit,
        bounding_box_sample_density_unit=density_unit,
        point_count=point_count,
        vertex_count=vertex_count,
        face_count=face_count,
        bounds_minimum=minimum,
        bounds_maximum=maximum,
        bounds_extent=extent,
        bounds_diagonal=diagonal,
        surface_area=surface_area,
        edge_length_minimum=None if edge_stats is None else edge_stats[0],
        edge_length_mean=None if edge_stats is None else edge_stats[1],
        edge_length_maximum=None if edge_stats is None else edge_stats[2],
        connected_component_count=None if component_counts is None else len(component_counts),
        connected_component_face_counts=component_counts,
        connected_component_status=component_status,
        bounding_box_sample_density=density,
        density_status=density_status,
        sampled_nearest_vertex_spacing_minimum=spacing_minimum,
        sampled_nearest_vertex_spacing_mean=spacing_mean,
        sampled_nearest_vertex_spacing_maximum=spacing_maximum,
        spacing_sample_count=spacing_count,
        hole_report_linkage=hole_linkage,
        component_revision_linkage=component_linkage,
        topology_indicators=topology,
        interpretation="DIAGNOSTIC_ONLY_NO_PHYSICAL_ACCURACY_CLAIM",
        physical_accuracy_validation_status=PHYSICAL_VALIDATION_DEFERRED,
        mold_use_authorized=False,
        policy=policy,
    )


def _mesh_edge_face_counts(mesh: TriangleMeshData) -> dict[tuple[int, int], int]:
    counts: dict[tuple[int, int], int] = defaultdict(int)
    for face in mesh.triangles:
        for first, second in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            counts[(min(first, second), max(first, second))] += 1
    return counts


__all__ = [
    "GEOMETRY_STATISTICS_CONTRACT",
    "PHYSICAL_VALIDATION_DEFERRED",
    "GeometryStatistics",
    "GeometryStatisticsError",
    "GeometryStatisticsPolicy",
    "compute_geometry_statistics",
]
