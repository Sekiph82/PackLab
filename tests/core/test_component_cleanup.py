from __future__ import annotations

import pytest

from packlab_core.component_cleanup import (
    PHYSICAL_VALIDATION_DEFERRED,
    ComponentCleanupError,
    ComponentCleanupPolicy,
    cleanup_isolated_components,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState


def _triangle_component(
    count: int, vertex_offset: int
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Build a deterministic edge-connected triangle strip."""
    vertices = [(float(vertex_offset + index), float(index % 2), 0.0) for index in range(count + 2)]
    triangles = [
        (vertex_offset + index, vertex_offset + index + 1, vertex_offset + index + 2)
        for index in range(count)
    ]
    return vertices, triangles


def _mesh(*component_sizes: int) -> TriangleMeshData:
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    offset = 0
    for size in component_sizes:
        component_vertices, component_triangles = _triangle_component(size, offset)
        vertices.extend(component_vertices)
        triangles.extend(component_triangles)
        offset += len(component_vertices)
    colors = tuple((0.2, 0.4, 0.6) for _ in vertices)
    normals = tuple((0.0, 0.0, 1.0) for _ in vertices)
    return TriangleMeshData(tuple(vertices), tuple(triangles), colors, normals)


def _cleanup(mesh: TriangleMeshData, *, policy: ComponentCleanupPolicy):
    return cleanup_isolated_components(
        mesh,
        parent_revision_id="captured-geometry-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        policy=policy,
    )


def test_main_component_is_preserved_and_small_floaters_are_removed_non_destructively() -> None:
    parent = _mesh(30, 2, 1)
    parent_snapshot = (
        parent.vertices,
        parent.triangles,
        parent.vertex_colors,
        parent.vertex_normals,
    )

    result = _cleanup(parent, policy=ComponentCleanupPolicy(30, 0.1))

    assert tuple(item.triangle_count for item in result.components) == (30, 2, 1)
    assert tuple(item.triangle_count for item in result.removed_components) == (2, 1)
    assert len(result.mesh.triangles) == 30
    assert len(result.mesh.vertices) == 32
    assert result.parent_revision_id == "captured-geometry-r1"
    assert (
        parent.vertices,
        parent.triangles,
        parent.vertex_colors,
        parent.vertex_normals,
    ) == parent_snapshot


def test_component_at_support_threshold_is_retained_and_below_threshold_is_removed() -> None:
    result = _cleanup(_mesh(20, 3, 2), policy=ComponentCleanupPolicy(3, 0.1))

    assert tuple(item.triangle_count for item in result.removed_components) == (2,)
    assert len(result.mesh.triangles) == 23


def test_all_small_or_ambiguous_mesh_fails_closed() -> None:
    with pytest.raises(ComponentCleanupError, match="all-small-or-ambiguous"):
        _cleanup(_mesh(2, 1), policy=ComponentCleanupPolicy(3, 0.1))


def test_removal_fraction_boundary_is_inclusive_and_excess_fails_without_partial_result() -> None:
    mesh = _mesh(20, 2)
    exact = _cleanup(mesh, policy=ComponentCleanupPolicy(20, 2 / 22))
    assert len(exact.removed_components) == 1

    with pytest.raises(ComponentCleanupError, match="removal fraction exceeds"):
        _cleanup(mesh, policy=ComponentCleanupPolicy(20, 0.09))


def test_component_order_and_child_identity_are_deterministic() -> None:
    mesh = _mesh(30, 2, 1)
    policy = ComponentCleanupPolicy(30, 0.1)

    first = _cleanup(mesh, policy=policy)
    second = _cleanup(mesh, policy=policy)

    assert first.as_dict() == second.as_dict()
    assert first.child_revision_id == second.child_revision_id
    assert tuple(component.triangle_indices[0] for component in first.components) == (0, 30, 32)


def test_revision_binds_parent_geometry_policy_and_removed_component_evidence() -> None:
    parent = _mesh(20, 2)
    result = _cleanup(parent, policy=ComponentCleanupPolicy(20, 0.1))

    assert len(result.parent_geometry_sha256) == 64
    assert len(result.geometry_sha256) == 64
    assert result.parent_geometry_sha256 != result.geometry_sha256
    assert result.child_revision_id.startswith("mesh-cleanup:")
    serialized = result.as_dict()
    assert serialized["policy"]["connectivity_policy"] == "triangles_share_edge_v1"
    assert serialized["removed_components"][0]["triangle_indices"] == [20, 21]


def test_metric_unverified_provenance_and_deferred_authority_are_preserved() -> None:
    result = _cleanup(_mesh(20, 1), policy=ComponentCleanupPolicy(20, 0.1))

    assert result.scale_state is ScaleState.METRIC_UNVERIFIED
    assert result.scale_provenance_id == "scale-provenance-r1"
    assert result.physical_accuracy_validation_status == PHYSICAL_VALIDATION_DEFERRED
    assert result.mold_use_authorized is False


def test_invalid_or_escalated_scale_state_and_missing_provenance_fail_closed() -> None:
    mesh = _mesh(20)
    with pytest.raises(ComponentCleanupError, match="scale_state"):
        cleanup_isolated_components(
            mesh,
            parent_revision_id="parent-r1",
            scale_state=ScaleState.METRIC_VERIFIED,
        )
    with pytest.raises(ComponentCleanupError, match="scale_provenance_id"):
        cleanup_isolated_components(
            mesh,
            parent_revision_id="parent-r1",
            scale_state=ScaleState.METRIC_UNVERIFIED,
        )


def test_policy_rejects_unsafe_removal_caps_and_mesh_without_triangles() -> None:
    with pytest.raises(ComponentCleanupError, match="between 0 and 0.10"):
        ComponentCleanupPolicy(maximum_removable_fraction=0.11)
    empty = TriangleMeshData(vertices=((0.0, 0.0, 0.0),), triangles=())
    with pytest.raises(ComponentCleanupError, match="no triangles"):
        _cleanup(empty, policy=ComponentCleanupPolicy())
    unreferenced = TriangleMeshData(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (4.0, 4.0, 4.0)),
        triangles=((0, 1, 2),),
    )
    with pytest.raises(ComponentCleanupError, match="unreferenced vertices"):
        _cleanup(unreferenced, policy=ComponentCleanupPolicy())


def test_different_parent_revision_changes_child_revision_identity() -> None:
    mesh = _mesh(20, 1)
    original = _cleanup(mesh, policy=ComponentCleanupPolicy(20, 0.1))
    other_parent = cleanup_isolated_components(
        mesh,
        parent_revision_id="captured-geometry-r2",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        policy=ComponentCleanupPolicy(20, 0.1),
    )
    assert original.child_revision_id != other_parent.child_revision_id
