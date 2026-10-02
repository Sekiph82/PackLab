from __future__ import annotations

import statistics

import pytest

from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.mesh_smoothing import (
    MeshSmoothingError,
    MeshSmoothingPolicy,
    smooth_triangle_mesh,
)
from packlab_core.reconstruction import ScaleState


def _grid_mesh(side: int = 7, spacing: float = 0.1, noisy: bool = True) -> TriangleMeshData:
    vertices = tuple(
        (
            column * spacing,
            row * spacing,
            ((-1.0) ** (row + column)) * 0.002 if noisy else 0.0,
        )
        for row in range(side)
        for column in range(side)
    )
    triangles = []
    for row in range(side - 1):
        for column in range(side - 1):
            top_left = row * side + column
            top_right = top_left + 1
            bottom_left = top_left + side
            bottom_right = bottom_left + 1
            triangles.extend(
                ((top_left, top_right, bottom_right), (top_left, bottom_right, bottom_left))
            )
    colors = tuple((0.1, 0.3, 0.5) for _ in vertices)
    return TriangleMeshData(vertices, tuple(triangles), colors)


def _smooth(mesh: TriangleMeshData, policy: MeshSmoothingPolicy):
    return smooth_triangle_mesh(
        mesh,
        parent_revision_id="captured-mesh-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        policy=policy,
    )


def test_smoothing_reduces_flat_surface_noise_and_preserves_outer_feature_boundary() -> None:
    base = _grid_mesh()
    mesh = TriangleMeshData(
        base.vertices,
        base.triangles,
        base.vertex_colors,
        tuple((0.0, 0.0, 1.0) for _ in base.vertices),
    )
    policy = MeshSmoothingPolicy(iterations=4, relaxation=0.2, maximum_displacement=0.008)
    result = _smooth(mesh, policy)
    interior = [row * 7 + column for row in range(1, 6) for column in range(1, 6)]

    before = statistics.pvariance(mesh.vertices[index][2] for index in interior)
    after = statistics.pvariance(result.mesh.vertices[index][2] for index in interior)
    assert after < before
    assert set(range(7)) <= set(result.feature_vertex_indices)
    assert all(
        result.mesh.vertices[index] == mesh.vertices[index]
        for index in result.feature_vertex_indices
    )
    assert result.mesh.vertex_colors == mesh.vertex_colors
    assert result.mesh.vertex_normals is not None
    assert result.mesh.vertex_normals != mesh.vertex_normals


def test_sharp_packaging_edge_is_detected_and_frozen() -> None:
    mesh = TriangleMeshData(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        triangles=((0, 1, 2), (1, 0, 3)),
    )
    result = _smooth(mesh, MeshSmoothingPolicy(maximum_displacement=0.01))

    assert {0, 1} <= set(result.feature_vertex_indices)
    assert result.mesh.vertices[0] == mesh.vertices[0]
    assert result.mesh.vertices[1] == mesh.vertices[1]


def test_maximum_displacement_is_reported_and_enforced() -> None:
    mesh = _grid_mesh()
    result = _smooth(
        mesh,
        MeshSmoothingPolicy(iterations=10, relaxation=0.25, maximum_displacement=0.001),
    )

    assert result.maximum_observed_displacement <= 0.001 + 1e-12
    assert max(result.per_vertex_displacement) == result.maximum_observed_displacement
    assert len(result.geometry_sha256) == 64


def test_zero_iterations_produces_no_geometry_delta_but_a_parent_bound_record() -> None:
    base = _grid_mesh()
    mesh = TriangleMeshData(
        base.vertices,
        base.triangles,
        base.vertex_colors,
        tuple((0.0, 0.0, 1.0) for _ in base.vertices),
    )
    result = _smooth(mesh, MeshSmoothingPolicy(iterations=0, maximum_displacement=0.008))

    assert result.mesh == mesh
    assert result.maximum_observed_displacement == 0.0
    assert result.rms_displacement == 0.0
    assert result.child_revision_id.startswith("mesh-smoothing:")
    assert result.parent_geometry_sha256 == result.geometry_sha256


def test_smoothing_is_deterministic_non_mutating_and_preserves_deferred_scale() -> None:
    mesh = _grid_mesh()
    snapshot = (mesh.vertices, mesh.triangles, mesh.vertex_colors, mesh.vertex_normals)
    policy = MeshSmoothingPolicy(iterations=3, relaxation=0.15, maximum_displacement=0.008)
    first = _smooth(mesh, policy)
    second = _smooth(mesh, policy)

    assert first.as_dict() == second.as_dict()
    assert first.child_revision_id == second.child_revision_id
    assert (mesh.vertices, mesh.triangles, mesh.vertex_colors, mesh.vertex_normals) == snapshot
    assert first.parent_revision_id == "captured-mesh-r1"
    assert first.scale_state is ScaleState.METRIC_UNVERIFIED
    assert first.scale_provenance_id == "scale-provenance-r1"
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False


def test_excessive_iterations_relaxation_angle_and_displacement_are_rejected() -> None:
    for kwargs in (
        {"iterations": 11},
        {"relaxation": 0.3},
        {"feature_angle_degrees": 70.0},
    ):
        with pytest.raises(MeshSmoothingError):
            MeshSmoothingPolicy(**kwargs)

    with pytest.raises(MeshSmoothingError, match="1 percent"):
        _smooth(_grid_mesh(), MeshSmoothingPolicy(maximum_displacement=0.1))


def test_degenerate_mesh_and_metric_verified_state_fail_closed() -> None:
    degenerate = TriangleMeshData(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)),
        triangles=((0, 1, 2),),
    )
    with pytest.raises(MeshSmoothingError, match="degenerate triangle"):
        _smooth(degenerate, MeshSmoothingPolicy(maximum_displacement=0.01))
    with pytest.raises(MeshSmoothingError, match="scale_state"):
        smooth_triangle_mesh(
            _grid_mesh(),
            parent_revision_id="parent-r1",
            scale_state=ScaleState.METRIC_VERIFIED,
        )
