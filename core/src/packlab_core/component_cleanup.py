"""Conservative, revision-bound removal of isolated triangle-mesh components."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass

from .geometry_adapter import TriangleMeshData
from .reconstruction import ScaleState

COMPONENT_CLEANUP_CONTRACT = "packlab.mesh-component-cleanup.v1"
PHYSICAL_VALIDATION_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_MAXIMUM_ALLOWED_REMOVAL_FRACTION = 0.10


class ComponentCleanupError(ValueError):
    """Raised when component cleanup is ambiguous or exceeds its safeguards."""


@dataclass(frozen=True, slots=True)
class ComponentCleanupPolicy:
    """Versioned support and removal limits for edge-connected mesh components."""

    minimum_component_triangles: int = 20
    maximum_removable_fraction: float = 0.05

    def __post_init__(self) -> None:
        if (
            isinstance(self.minimum_component_triangles, bool)
            or not isinstance(self.minimum_component_triangles, int)
            or self.minimum_component_triangles < 1
        ):
            raise ComponentCleanupError("minimum_component_triangles must be a positive integer")
        fraction = self.maximum_removable_fraction
        if (
            isinstance(fraction, bool)
            or not isinstance(fraction, (int, float))
            or not math.isfinite(fraction)
            or not 0.0 <= fraction <= _MAXIMUM_ALLOWED_REMOVAL_FRACTION
        ):
            raise ComponentCleanupError(
                "maximum_removable_fraction must be finite and between 0 and 0.10"
            )
        object.__setattr__(self, "maximum_removable_fraction", float(fraction))

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": COMPONENT_CLEANUP_CONTRACT,
            "connectivity_policy": "triangles_share_edge_v1",
            "minimum_component_triangles": self.minimum_component_triangles,
            "candidate_rule": "component_triangle_count_strictly_less_than_minimum",
            "maximum_removable_fraction": self.maximum_removable_fraction,
            "removal_fraction_basis": "candidate_triangles_over_parent_triangles",
            "largest_component_policy": "always_preserve_largest_tie_break_first_triangle_index",
        }


@dataclass(frozen=True, slots=True)
class MeshComponent:
    component_id: str
    triangle_indices: tuple[int, ...]

    @property
    def triangle_count(self) -> int:
        return len(self.triangle_indices)


@dataclass(frozen=True, slots=True)
class RemovedComponentEvidence:
    component_id: str
    triangle_indices: tuple[int, ...]
    triangle_count: int


@dataclass(frozen=True, slots=True)
class ComponentCleanupRevision:
    contract: str
    parent_revision_id: str
    child_revision_id: str
    parent_geometry_sha256: str
    geometry_sha256: str
    mesh: TriangleMeshData
    policy: ComponentCleanupPolicy
    components: tuple[MeshComponent, ...]
    removed_components: tuple[RemovedComponentEvidence, ...]
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
            "components": [
                {
                    "component_id": item.component_id,
                    "triangle_indices": list(item.triangle_indices),
                    "triangle_count": item.triangle_count,
                }
                for item in self.components
            ],
            "removed_components": [
                {
                    "component_id": item.component_id,
                    "triangle_indices": list(item.triangle_indices),
                    "triangle_count": item.triangle_count,
                }
                for item in self.removed_components
            ],
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _geometry_payload(mesh: TriangleMeshData) -> dict[str, object]:
    return {
        "vertices": mesh.vertices,
        "triangles": mesh.triangles,
        "vertex_colors": mesh.vertex_colors,
        "vertex_normals": mesh.vertex_normals,
    }


def _components(mesh: TriangleMeshData) -> tuple[MeshComponent, ...]:
    if not mesh.triangles:
        raise ComponentCleanupError("mesh has no triangles; component cleanup is ambiguous")
    referenced_vertices = {vertex for triangle in mesh.triangles for vertex in triangle}
    if len(referenced_vertices) != len(mesh.vertices):
        raise ComponentCleanupError("unreferenced vertices make component analysis ambiguous")

    edge_owners: dict[tuple[int, int], list[int]] = defaultdict(list)
    for triangle_index, (a, b, c) in enumerate(mesh.triangles):
        for edge in ((a, b), (b, c), (c, a)):
            edge_key = (min(edge[0], edge[1]), max(edge[0], edge[1]))
            edge_owners[edge_key].append(triangle_index)

    neighbors: list[set[int]] = [set() for _ in mesh.triangles]
    for owners in edge_owners.values():
        for owner in owners:
            neighbors[owner].update(other for other in owners if other != owner)

    visited: set[int] = set()
    groups: list[tuple[int, ...]] = []
    for start in range(len(mesh.triangles)):
        if start in visited:
            continue
        stack = [start]
        visited.add(start)
        members: list[int] = []
        while stack:
            current = stack.pop()
            members.append(current)
            for neighbor in sorted(neighbors[current], reverse=True):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        groups.append(tuple(sorted(members)))

    groups.sort(key=lambda item: item[0])
    return tuple(
        MeshComponent(
            component_id=f"component-{_canonical_digest(list(indices))[:16]}",
            triangle_indices=indices,
        )
        for indices in groups
    )


def _require_safe_id(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ComponentCleanupError(f"{field} must be a non-empty stable identifier")
    if any(ord(character) < 32 for character in value):
        raise ComponentCleanupError(f"{field} must not contain control characters")
    return value


def cleanup_isolated_components(
    mesh: TriangleMeshData,
    *,
    parent_revision_id: str,
    scale_state: ScaleState,
    scale_provenance_id: str | None = None,
    policy: ComponentCleanupPolicy = ComponentCleanupPolicy(),
) -> ComponentCleanupRevision:
    """Return a safe child mesh and deterministic removal evidence without mutating parent."""

    parent_revision_id = _require_safe_id(parent_revision_id, "parent_revision_id")
    if not isinstance(scale_state, ScaleState) or scale_state is ScaleState.METRIC_VERIFIED:
        raise ComponentCleanupError("scale_state must preserve relative or metric-unverified state")
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        scale_provenance_id = _require_safe_id(scale_provenance_id, "scale_provenance_id")
    elif scale_provenance_id is not None:
        scale_provenance_id = _require_safe_id(scale_provenance_id, "scale_provenance_id")

    components = _components(mesh)
    # Largest component wins; ties retain the first component by input triangle index.
    main_component = max(
        components, key=lambda item: (item.triangle_count, -item.triangle_indices[0])
    )
    if main_component.triangle_count < policy.minimum_component_triangles:
        raise ComponentCleanupError(
            "all-small-or-ambiguous: no component meets the support minimum"
        )

    candidates = tuple(
        item
        for item in components
        if item != main_component and item.triangle_count < policy.minimum_component_triangles
    )
    removed_count = sum(item.triangle_count for item in candidates)
    fraction = removed_count / len(mesh.triangles)
    if fraction > policy.maximum_removable_fraction:
        raise ComponentCleanupError("removal fraction exceeds the configured safeguard")

    removed_indices = {index for item in candidates for index in item.triangle_indices}
    kept_triangles = tuple(
        triangle for index, triangle in enumerate(mesh.triangles) if index not in removed_indices
    )
    used_vertices = tuple(sorted({vertex for triangle in kept_triangles for vertex in triangle}))
    remap = {old_index: new_index for new_index, old_index in enumerate(used_vertices)}
    child_mesh = TriangleMeshData(
        vertices=tuple(mesh.vertices[index] for index in used_vertices),
        triangles=tuple(
            (remap[face[0]], remap[face[1]], remap[face[2]]) for face in kept_triangles
        ),
        vertex_colors=(
            tuple(mesh.vertex_colors[index] for index in used_vertices)
            if mesh.vertex_colors is not None
            else None
        ),
        vertex_normals=(
            tuple(mesh.vertex_normals[index] for index in used_vertices)
            if mesh.vertex_normals is not None
            else None
        ),
    )
    parent_digest = _canonical_digest(_geometry_payload(mesh))
    output_digest = _canonical_digest(_geometry_payload(child_mesh))
    removed = tuple(
        RemovedComponentEvidence(item.component_id, item.triangle_indices, item.triangle_count)
        for item in candidates
    )
    revision_inputs = {
        "contract": COMPONENT_CLEANUP_CONTRACT,
        "parent_revision_id": parent_revision_id,
        "parent_geometry_sha256": parent_digest,
        "geometry_sha256": output_digest,
        "policy": policy.as_dict(),
        "removed_components": [
            {"component_id": item.component_id, "triangle_indices": item.triangle_indices}
            for item in removed
        ],
        "scale_state": scale_state.value,
        "scale_provenance_id": scale_provenance_id,
        "physical_accuracy_validation_status": PHYSICAL_VALIDATION_DEFERRED,
        "mold_use_authorized": False,
    }
    child_id = f"mesh-cleanup:{_canonical_digest(revision_inputs)}"
    return ComponentCleanupRevision(
        contract=COMPONENT_CLEANUP_CONTRACT,
        parent_revision_id=parent_revision_id,
        child_revision_id=child_id,
        parent_geometry_sha256=parent_digest,
        geometry_sha256=output_digest,
        mesh=child_mesh,
        policy=policy,
        components=components,
        removed_components=removed,
        scale_state=scale_state,
        scale_provenance_id=scale_provenance_id,
        physical_accuracy_validation_status=PHYSICAL_VALIDATION_DEFERRED,
        mold_use_authorized=False,
    )


__all__ = [
    "COMPONENT_CLEANUP_CONTRACT",
    "PHYSICAL_VALIDATION_DEFERRED",
    "ComponentCleanupError",
    "ComponentCleanupPolicy",
    "ComponentCleanupRevision",
    "MeshComponent",
    "RemovedComponentEvidence",
    "cleanup_isolated_components",
]
