"""Conservative edge-preserving smoothing as an immutable mesh child revision."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass

from .geometry_adapter import Point3, TriangleMeshData
from .reconstruction import ScaleState

MESH_SMOOTHING_CONTRACT = "packlab.mesh-smoothing.v1"
PHYSICAL_VALIDATION_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class MeshSmoothingError(ValueError):
    """Raised when smoothing is invalid, unbounded, or topologically ambiguous."""


@dataclass(frozen=True, slots=True)
class MeshSmoothingPolicy:
    iterations: int = 2
    relaxation: float = 0.1
    feature_angle_degrees: float = 35.0
    maximum_displacement: float = 0.001

    def __post_init__(self) -> None:
        if (
            isinstance(self.iterations, bool)
            or not isinstance(self.iterations, int)
            or not 0 <= self.iterations <= 10
        ):
            raise MeshSmoothingError("iterations must be an integer between 0 and 10")
        if (
            isinstance(self.relaxation, bool)
            or not isinstance(self.relaxation, (int, float))
            or not math.isfinite(self.relaxation)
            or not 0 < self.relaxation <= 0.25
        ):
            raise MeshSmoothingError("relaxation must be finite and in (0, 0.25]")
        if (
            isinstance(self.feature_angle_degrees, bool)
            or not isinstance(self.feature_angle_degrees, (int, float))
            or not math.isfinite(self.feature_angle_degrees)
            or not 20 <= self.feature_angle_degrees <= 60
        ):
            raise MeshSmoothingError("feature_angle_degrees must be between 20 and 60")
        if (
            isinstance(self.maximum_displacement, bool)
            or not isinstance(self.maximum_displacement, (int, float))
            or not math.isfinite(self.maximum_displacement)
            or self.maximum_displacement <= 0
        ):
            raise MeshSmoothingError("maximum_displacement must be finite and positive")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": MESH_SMOOTHING_CONTRACT,
            "iterations": self.iterations,
            "relaxation": float(self.relaxation),
            "feature_angle_degrees": float(self.feature_angle_degrees),
            "feature_rule": "freeze_vertices_on_boundary_nonmanifold_or_sharp_edges_v1",
            "maximum_displacement": float(self.maximum_displacement),
            "maximum_displacement_safety_rule": "at_most_1_percent_of_parent_bbox_diagonal",
            "coordinate_units": "inherited_parent_units_no_physical_accuracy_claim",
        }


@dataclass(frozen=True, slots=True)
class MeshSmoothingRevision:
    contract: str
    parent_revision_id: str
    child_revision_id: str
    parent_geometry_sha256: str
    geometry_sha256: str
    mesh: TriangleMeshData
    policy: MeshSmoothingPolicy
    feature_vertex_indices: tuple[int, ...]
    per_vertex_displacement: tuple[float, ...]
    maximum_observed_displacement: float
    rms_displacement: float
    scale_state: ScaleState
    scale_provenance_id: str | None
    physical_accuracy_validation_status: str
    mold_use_authorized: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "parent_revision_id": self.parent_revision_id,
            "child_revision_id": self.child_revision_id,
            "parent_geometry_sha256": self.parent_geometry_sha256,
            "geometry_sha256": self.geometry_sha256,
            "policy": self.policy.as_dict(),
            "feature_vertex_indices": self.feature_vertex_indices,
            "per_vertex_displacement": self.per_vertex_displacement,
            "maximum_observed_displacement": self.maximum_observed_displacement,
            "rms_displacement": self.rms_displacement,
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


def _safe_identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise MeshSmoothingError(f"{field} must be a non-empty stable identifier")
    if any(ord(char) < 32 for char in value):
        raise MeshSmoothingError(f"{field} must not contain control characters")
    return value


def _subtract(a: Point3, b: Point3) -> Point3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Point3, b: Point3) -> Point3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(vector: Point3) -> Point3 | None:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude <= 1e-15 or not math.isfinite(magnitude):
        return None
    return (vector[0] / magnitude, vector[1] / magnitude, vector[2] / magnitude)


def _dot(a: Point3, b: Point3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _feature_vertices(mesh: TriangleMeshData, threshold_degrees: float) -> tuple[int, ...]:
    edge_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    face_normals: list[Point3] = []
    for face_index, (a, b, c) in enumerate(mesh.triangles):
        normal = _unit(
            _cross(
                _subtract(mesh.vertices[b], mesh.vertices[a]),
                _subtract(mesh.vertices[c], mesh.vertices[a]),
            )
        )
        if normal is None:
            raise MeshSmoothingError("degenerate triangle prevents safe feature analysis")
        face_normals.append(normal)
        for first, second in ((a, b), (b, c), (c, a)):
            key = (min(first, second), max(first, second))
            edge_faces[key].append(face_index)

    threshold = math.cos(math.radians(threshold_degrees))
    features: set[int] = set()
    for edge, faces in edge_faces.items():
        if len(faces) != 2:
            features.update(edge)
            continue
        if _dot(face_normals[faces[0]], face_normals[faces[1]]) < threshold:
            features.update(edge)
    return tuple(sorted(features))


def _recomputed_vertex_normals(
    mesh: TriangleMeshData, vertices: tuple[Point3, ...]
) -> tuple[Point3, ...]:
    accumulated = [[0.0, 0.0, 0.0] for _ in vertices]
    for a, b, c in mesh.triangles:
        face_vector = _cross(
            _subtract(vertices[b], vertices[a]), _subtract(vertices[c], vertices[a])
        )
        for index in (a, b, c):
            for axis in range(3):
                accumulated[index][axis] += face_vector[axis]
    result: list[Point3] = []
    for vector in accumulated:
        normal = _unit((vector[0], vector[1], vector[2]))
        result.append((0.0, 0.0, 0.0) if normal is None else normal)
    return tuple(result)


def smooth_triangle_mesh(
    mesh: TriangleMeshData,
    *,
    parent_revision_id: str,
    scale_state: ScaleState,
    scale_provenance_id: str | None = None,
    policy: MeshSmoothingPolicy = MeshSmoothingPolicy(),
) -> MeshSmoothingRevision:
    """Apply capped Laplacian steps while freezing packaging edges and boundaries."""

    parent_revision_id = _safe_identifier(parent_revision_id, "parent_revision_id")
    if not isinstance(scale_state, ScaleState) or scale_state is ScaleState.METRIC_VERIFIED:
        raise MeshSmoothingError("scale_state must preserve relative or metric-unverified state")
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        scale_provenance_id = _safe_identifier(scale_provenance_id, "scale_provenance_id")
    elif scale_provenance_id is not None:
        scale_provenance_id = _safe_identifier(scale_provenance_id, "scale_provenance_id")
    if not mesh.triangles:
        raise MeshSmoothingError("mesh must contain triangles")

    bbox_diagonal = math.sqrt(
        sum(
            (
                max(vertex[axis] for vertex in mesh.vertices)
                - min(vertex[axis] for vertex in mesh.vertices)
            )
            ** 2
            for axis in range(3)
        )
    )
    if bbox_diagonal <= 1e-15:
        raise MeshSmoothingError("mesh bounds are degenerate")
    safety_bound = bbox_diagonal * 0.01
    if policy.maximum_displacement > safety_bound:
        raise MeshSmoothingError("maximum_displacement exceeds 1 percent of parent bounds")

    adjacency: list[set[int]] = [set() for _ in mesh.vertices]
    for a, b, c in mesh.triangles:
        for first, second in ((a, b), (b, c), (c, a)):
            adjacency[first].add(second)
            adjacency[second].add(first)
    if any(not neighbors for neighbors in adjacency):
        raise MeshSmoothingError("unreferenced vertices prevent safe smoothing")

    features = _feature_vertices(mesh, policy.feature_angle_degrees)
    frozen = set(features)
    original = mesh.vertices
    current: tuple[Point3, ...] = original
    for _ in range(policy.iterations):
        updated: list[Point3] = []
        for index, point in enumerate(current):
            if index in frozen:
                updated.append(point)
                continue
            neighbors = sorted(adjacency[index])
            average = tuple(
                sum(current[neighbor][axis] for neighbor in neighbors) / len(neighbors)
                for axis in range(3)
            )
            proposed: Point3 = (
                point[0] + policy.relaxation * (average[0] - point[0]),
                point[1] + policy.relaxation * (average[1] - point[1]),
                point[2] + policy.relaxation * (average[2] - point[2]),
            )
            total_delta = _subtract(proposed, original[index])
            magnitude = math.sqrt(_dot(total_delta, total_delta))
            if magnitude > policy.maximum_displacement:
                ratio = policy.maximum_displacement / magnitude
                proposed = (
                    original[index][0] + total_delta[0] * ratio,
                    original[index][1] + total_delta[1] * ratio,
                    original[index][2] + total_delta[2] * ratio,
                )
            updated.append((proposed[0], proposed[1], proposed[2]))
        current = tuple(updated)

    displacements = tuple(
        math.sqrt(
            _dot(
                _subtract(current[index], original[index]),
                _subtract(current[index], original[index]),
            )
        )
        for index in range(len(original))
    )
    maximum_observed = max(displacements, default=0.0)
    rms = (
        math.sqrt(sum(value * value for value in displacements) / len(displacements))
        if displacements
        else 0.0
    )
    if maximum_observed > policy.maximum_displacement + 1e-12:
        raise MeshSmoothingError("observed displacement exceeded the configured cap")

    output_mesh = TriangleMeshData(
        vertices=current,
        triangles=mesh.triangles,
        vertex_colors=mesh.vertex_colors,
        vertex_normals=(
            _recomputed_vertex_normals(mesh, current)
            if mesh.vertex_normals is not None and current != original
            else mesh.vertex_normals
        ),
    )
    parent_digest = _digest(_geometry_payload(mesh))
    output_digest = _digest(_geometry_payload(output_mesh))
    revision_inputs = {
        "contract": MESH_SMOOTHING_CONTRACT,
        "parent_revision_id": parent_revision_id,
        "parent_geometry_sha256": parent_digest,
        "geometry_sha256": output_digest,
        "policy": policy.as_dict(),
        "feature_vertex_indices": features,
        "per_vertex_displacement": displacements,
        "scale_state": scale_state.value,
        "scale_provenance_id": scale_provenance_id,
        "physical_accuracy_validation_status": PHYSICAL_VALIDATION_DEFERRED,
        "mold_use_authorized": False,
    }
    child_id = f"mesh-smoothing:{_digest(revision_inputs)}"
    return MeshSmoothingRevision(
        contract=MESH_SMOOTHING_CONTRACT,
        parent_revision_id=parent_revision_id,
        child_revision_id=child_id,
        parent_geometry_sha256=parent_digest,
        geometry_sha256=output_digest,
        mesh=output_mesh,
        policy=policy,
        feature_vertex_indices=features,
        per_vertex_displacement=displacements,
        maximum_observed_displacement=maximum_observed,
        rms_displacement=rms,
        scale_state=scale_state,
        scale_provenance_id=scale_provenance_id,
        physical_accuracy_validation_status=PHYSICAL_VALIDATION_DEFERRED,
        mold_use_authorized=False,
    )


__all__ = [
    "MESH_SMOOTHING_CONTRACT",
    "PHYSICAL_VALIDATION_DEFERRED",
    "MeshSmoothingError",
    "MeshSmoothingPolicy",
    "MeshSmoothingRevision",
    "smooth_triangle_mesh",
]
