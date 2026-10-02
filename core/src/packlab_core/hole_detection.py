"""Deterministic mesh boundary-loop reports; this module never repairs geometry."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass

from .geometry_adapter import Point3, PointCloudData, TriangleMeshData
from .reconstruction import ScaleState

HOLE_DETECTION_CONTRACT = "packlab.mesh-boundary-report.v1"
PHYSICAL_VALIDATION_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class HoleDetectionError(ValueError):
    """Raised for malformed provenance or unbounded hole-analysis requests."""


@dataclass(frozen=True, slots=True)
class HoleDetectionPolicy:
    maximum_faces: int = 1_000_000
    maximum_boundary_edges: int = 1_000_000
    maximum_traversal_steps: int = 2_000_000

    def __post_init__(self) -> None:
        for name in ("maximum_faces", "maximum_boundary_edges", "maximum_traversal_steps"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise HoleDetectionError(f"{name} must be a positive integer")
            if value > 2_000_000:
                raise HoleDetectionError(f"{name} exceeds the supported work bound")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": HOLE_DETECTION_CONTRACT,
            "boundary_definition": "undirected_mesh_edge_with_exactly_one_incident_face",
            "maximum_faces": self.maximum_faces,
            "maximum_boundary_edges": self.maximum_boundary_edges,
            "maximum_traversal_steps": self.maximum_traversal_steps,
            "repair_performed": False,
        }


@dataclass(frozen=True, slots=True)
class BoundaryLoopReport:
    loop_id: str
    boundary_vertex_indices: tuple[int, ...]
    perimeter: float
    approximate_area: float
    extent: Point3
    location: Point3
    support_face_indices: tuple[int, ...]
    touches_uncertain_region: bool | None
    touches_coverage_gap: bool | None


@dataclass(frozen=True, slots=True)
class UnresolvedBoundaryComponent:
    vertex_indices: tuple[int, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class MeshHoleReport:
    contract: str
    disposition: str
    parent_revision_id: str
    parent_geometry_sha256: str
    report_id: str
    loops: tuple[BoundaryLoopReport, ...]
    unresolved_components: tuple[UnresolvedBoundaryComponent, ...]
    nonmanifold_edge_indices: tuple[tuple[int, int], ...]
    degenerate_face_indices: tuple[int, ...]
    policy: HoleDetectionPolicy
    scale_state: ScaleState
    scale_provenance_id: str | None
    physical_accuracy_validation_status: str
    mold_use_authorized: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "disposition": self.disposition,
            "parent_revision_id": self.parent_revision_id,
            "parent_geometry_sha256": self.parent_geometry_sha256,
            "report_id": self.report_id,
            "loops": [
                {
                    "loop_id": loop.loop_id,
                    "boundary_vertex_indices": loop.boundary_vertex_indices,
                    "perimeter": loop.perimeter,
                    "approximate_area": loop.approximate_area,
                    "extent": loop.extent,
                    "location": loop.location,
                    "support_face_indices": loop.support_face_indices,
                    "touches_uncertain_region": loop.touches_uncertain_region,
                    "touches_coverage_gap": loop.touches_coverage_gap,
                }
                for loop in self.loops
            ],
            "unresolved_components": [
                {"vertex_indices": item.vertex_indices, "reason": item.reason}
                for item in self.unresolved_components
            ],
            "nonmanifold_edge_indices": self.nonmanifold_edge_indices,
            "degenerate_face_indices": self.degenerate_face_indices,
            "policy": self.policy.as_dict(),
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


def _digest(payload: object) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("ascii")).hexdigest()


def _safe_id(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise HoleDetectionError(f"{field} must be a non-empty stable identifier")
    if any(ord(char) < 32 for char in value):
        raise HoleDetectionError(f"{field} must not contain control characters")
    return value


def _parent_digest(mesh: TriangleMeshData) -> str:
    return _digest(
        {
            "vertices": mesh.vertices,
            "triangles": mesh.triangles,
            "vertex_colors": mesh.vertex_colors,
            "vertex_normals": mesh.vertex_normals,
        }
    )


def _metrics(
    vertices: tuple[Point3, ...], ordered: tuple[int, ...]
) -> tuple[float, float, Point3, Point3]:
    points = tuple(vertices[index] for index in ordered)
    perimeter = sum(
        math.dist(points[index], points[(index + 1) % len(points)]) for index in range(len(points))
    )
    area_vector = [0.0, 0.0, 0.0]
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        area_vector[0] += point[1] * following[2] - point[2] * following[1]
        area_vector[1] += point[2] * following[0] - point[0] * following[2]
        area_vector[2] += point[0] * following[1] - point[1] * following[0]
    area = 0.5 * math.sqrt(sum(component * component for component in area_vector))
    extent: Point3 = tuple(
        max(point[axis] for point in points) - min(point[axis] for point in points)
        for axis in range(3)
    )  # type: ignore[assignment]
    location: Point3 = tuple(
        sum(point[axis] for point in points) / len(points) for axis in range(3)
    )  # type: ignore[assignment]
    return perimeter, area, extent, location


def _point_cloud_report(
    cloud: PointCloudData,
    parent_revision_id: str,
    scale_state: ScaleState,
    scale_provenance_id: str | None,
    policy: HoleDetectionPolicy,
) -> MeshHoleReport:
    digest = _digest({"points": cloud.points, "colors": cloud.colors, "normals": cloud.normals})
    report_id = f"hole-report:{_digest((HOLE_DETECTION_CONTRACT, parent_revision_id, digest, policy.as_dict()))}"
    return MeshHoleReport(
        contract=HOLE_DETECTION_CONTRACT,
        disposition="NOT_APPLICABLE_POINT_CLOUD_BOUNDARY_LOOPS_REQUIRE_TRIANGLE_MESH",
        parent_revision_id=parent_revision_id,
        parent_geometry_sha256=digest,
        report_id=report_id,
        loops=(),
        unresolved_components=(),
        nonmanifold_edge_indices=(),
        degenerate_face_indices=(),
        policy=policy,
        scale_state=scale_state,
        scale_provenance_id=scale_provenance_id,
        physical_accuracy_validation_status=PHYSICAL_VALIDATION_DEFERRED,
        mold_use_authorized=False,
    )


def analyze_mesh_holes(
    geometry: TriangleMeshData | PointCloudData,
    *,
    parent_revision_id: str,
    scale_state: ScaleState,
    scale_provenance_id: str | None = None,
    uncertain_vertex_indices: tuple[int, ...] | None = None,
    coverage_gap_vertex_indices: tuple[int, ...] | None = None,
    policy: HoleDetectionPolicy = HoleDetectionPolicy(),
) -> MeshHoleReport:
    """Report deterministic open boundary loops without filling or altering geometry."""

    parent_revision_id = _safe_id(parent_revision_id, "parent_revision_id")
    if not isinstance(scale_state, ScaleState) or scale_state is ScaleState.METRIC_VERIFIED:
        raise HoleDetectionError("scale_state must preserve relative or metric-unverified state")
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        scale_provenance_id = _safe_id(scale_provenance_id, "scale_provenance_id")
    elif scale_provenance_id is not None:
        scale_provenance_id = _safe_id(scale_provenance_id, "scale_provenance_id")
    if isinstance(geometry, PointCloudData):
        return _point_cloud_report(
            geometry, parent_revision_id, scale_state, scale_provenance_id, policy
        )
    if not isinstance(geometry, TriangleMeshData):
        raise HoleDetectionError("geometry must be PackLab PointCloudData or TriangleMeshData")
    if len(geometry.triangles) > policy.maximum_faces:
        raise HoleDetectionError("face count exceeds configured work bound")

    edge_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    degenerate: list[int] = []
    for face_index, (a, b, c) in enumerate(geometry.triangles):
        ab = (
            geometry.vertices[b][0] - geometry.vertices[a][0],
            geometry.vertices[b][1] - geometry.vertices[a][1],
            geometry.vertices[b][2] - geometry.vertices[a][2],
        )
        ac = (
            geometry.vertices[c][0] - geometry.vertices[a][0],
            geometry.vertices[c][1] - geometry.vertices[a][1],
            geometry.vertices[c][2] - geometry.vertices[a][2],
        )
        cross = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        if math.sqrt(sum(component * component for component in cross)) <= 1e-15:
            degenerate.append(face_index)
        for first, second in ((a, b), (b, c), (c, a)):
            edge_faces[(min(first, second), max(first, second))].append(face_index)

    nonmanifold = tuple(sorted(edge for edge, faces in edge_faces.items() if len(faces) > 2))
    boundary_edges = tuple(sorted(edge for edge, faces in edge_faces.items() if len(faces) == 1))
    if len(boundary_edges) > policy.maximum_boundary_edges:
        raise HoleDetectionError("boundary edge count exceeds configured work bound")

    graph: dict[int, set[int]] = defaultdict(set)
    edge_support: dict[tuple[int, int], int] = {}
    for edge in boundary_edges:
        first, second = edge
        graph[first].add(second)
        graph[second].add(first)
        edge_support[edge] = edge_faces[edge][0]
    uncertain = set(uncertain_vertex_indices) if uncertain_vertex_indices is not None else None
    coverage = set(coverage_gap_vertex_indices) if coverage_gap_vertex_indices is not None else None
    if uncertain is not None and any(
        index < 0 or index >= len(geometry.vertices) for index in uncertain
    ):
        raise HoleDetectionError("uncertain vertex index is out of range")
    if coverage is not None and any(
        index < 0 or index >= len(geometry.vertices) for index in coverage
    ):
        raise HoleDetectionError("coverage-gap vertex index is out of range")

    visited: set[int] = set()
    loops: list[BoundaryLoopReport] = []
    unresolved: list[UnresolvedBoundaryComponent] = []
    traversal_steps = 0
    for start in sorted(graph):
        if start in visited:
            continue
        component: set[int] = set()
        queue = deque([start])
        visited.add(start)
        while queue:
            vertex = queue.popleft()
            component.add(vertex)
            for neighbor in sorted(graph[vertex]):
                traversal_steps += 1
                if traversal_steps > policy.maximum_traversal_steps:
                    raise HoleDetectionError("boundary traversal exceeds configured work bound")
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        if len(component) < 3 or any(len(graph[index]) != 2 for index in component):
            reason = "boundary-network-is-open-or-branched"
            unresolved.append(UnresolvedBoundaryComponent(tuple(sorted(component)), reason))
            continue

        first = min(component)
        first_neighbors = sorted(graph[first])
        ordered = [first, first_neighbors[0]]
        previous, current = first, first_neighbors[0]
        while current != first:
            options = sorted(neighbor for neighbor in graph[current] if neighbor != previous)
            if not options:
                break
            following = options[0]
            if following == first:
                break
            if following in ordered:
                break
            ordered.append(following)
            previous, current = current, following
            traversal_steps += 1
            if traversal_steps > policy.maximum_traversal_steps:
                raise HoleDetectionError("boundary traversal exceeds configured work bound")
        if len(ordered) != len(component):
            unresolved.append(
                UnresolvedBoundaryComponent(
                    tuple(sorted(component)), "boundary-loop-ordering-failed"
                )
            )
            continue
        ordered_tuple = tuple(ordered)
        perimeter, area, extent, location = _metrics(geometry.vertices, ordered_tuple)
        support_faces = tuple(
            sorted(
                edge_support[
                    (
                        min(ordered_tuple[index], ordered_tuple[(index + 1) % len(ordered_tuple)]),
                        max(ordered_tuple[index], ordered_tuple[(index + 1) % len(ordered_tuple)]),
                    )
                ]
                for index in range(len(ordered_tuple))
            )
        )
        loop_identity = {
            "parent_revision_id": parent_revision_id,
            "boundary_vertex_indices": ordered_tuple,
            "support_face_indices": support_faces,
        }
        loops.append(
            BoundaryLoopReport(
                loop_id=f"boundary-loop:{_digest(loop_identity)[:20]}",
                boundary_vertex_indices=ordered_tuple,
                perimeter=perimeter,
                approximate_area=area,
                extent=extent,
                location=location,
                support_face_indices=support_faces,
                touches_uncertain_region=(
                    None if uncertain is None else bool(set(ordered_tuple) & uncertain)
                ),
                touches_coverage_gap=(
                    None if coverage is None else bool(set(ordered_tuple) & coverage)
                ),
            )
        )

    loops.sort(key=lambda loop: (loop.boundary_vertex_indices[0], loop.loop_id))
    unresolved.sort(key=lambda item: item.vertex_indices)
    digest = _parent_digest(geometry)
    disposition = (
        "ANALYZED"
        if not unresolved and not nonmanifold and not degenerate
        else "PARTIAL_AMBIGUOUS_TOPOLOGY"
    )
    report_identity = {
        "contract": HOLE_DETECTION_CONTRACT,
        "parent_revision_id": parent_revision_id,
        "parent_geometry_sha256": digest,
        "policy": policy.as_dict(),
        "loops": [
            (
                loop.loop_id,
                loop.boundary_vertex_indices,
                loop.perimeter,
                loop.approximate_area,
                loop.extent,
                loop.location,
                loop.support_face_indices,
                loop.touches_uncertain_region,
                loop.touches_coverage_gap,
            )
            for loop in loops
        ],
        "unresolved_components": [(item.vertex_indices, item.reason) for item in unresolved],
        "nonmanifold_edge_indices": nonmanifold,
        "degenerate_face_indices": degenerate,
    }
    report_id = f"hole-report:{_digest(report_identity)}"
    return MeshHoleReport(
        contract=HOLE_DETECTION_CONTRACT,
        disposition=disposition,
        parent_revision_id=parent_revision_id,
        parent_geometry_sha256=digest,
        report_id=report_id,
        loops=tuple(loops),
        unresolved_components=tuple(unresolved),
        nonmanifold_edge_indices=nonmanifold,
        degenerate_face_indices=tuple(degenerate),
        policy=policy,
        scale_state=scale_state,
        scale_provenance_id=scale_provenance_id,
        physical_accuracy_validation_status=PHYSICAL_VALIDATION_DEFERRED,
        mold_use_authorized=False,
    )


__all__ = [
    "HOLE_DETECTION_CONTRACT",
    "PHYSICAL_VALIDATION_DEFERRED",
    "BoundaryLoopReport",
    "HoleDetectionError",
    "HoleDetectionPolicy",
    "MeshHoleReport",
    "UnresolvedBoundaryComponent",
    "analyze_mesh_holes",
]
