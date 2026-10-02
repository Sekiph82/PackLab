from __future__ import annotations

import math

import pytest

from packlab_core.geometry_adapter import PointCloudData
from packlab_core.normal_estimation import (
    PHYSICAL_VALIDATION_DEFERRED,
    NormalEstimationError,
    NormalEstimationPolicy,
    estimate_point_cloud_normals,
)
from packlab_core.reconstruction import ScaleState


def _estimate(cloud: PointCloudData, policy: NormalEstimationPolicy):
    return estimate_point_cloud_normals(
        cloud,
        parent_revision_id="captured-points-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        policy=policy,
    )


def _plane(side: int = 7, spacing: float = 0.1) -> PointCloudData:
    return PointCloudData(
        tuple(
            ((column - (side - 1) / 2) * spacing, (row - (side - 1) / 2) * spacing, 2.0)
            for row in range(side)
            for column in range(side)
        )
    )


def _fibonacci_sphere(count: int = 120) -> PointCloudData:
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    points = []
    for index in range(count):
        z = 1.0 - 2.0 * (index + 0.5) / count
        radius = math.sqrt(1.0 - z * z)
        angle = golden_angle * index
        points.append((radius * math.cos(angle), radius * math.sin(angle), z))
    return PointCloudData(tuple(points))


def test_plane_normals_are_estimated_and_orientation_is_consistent() -> None:
    cloud = _plane()
    result = _estimate(
        cloud, NormalEstimationPolicy(radius=0.16, minimum_neighbors=3, maximum_neighbors=12)
    )

    resolved = [normal for normal in result.normal_estimates if normal is not None]
    assert len(resolved) == len(cloud.points)
    assert all(abs(normal[2]) > 0.999 for normal in resolved)
    assert not result.unresolved_point_indices
    assert not result.ambiguous_orientation_edges
    assert all(_dot(resolved[0], normal) > 0.99 for normal in resolved)


def test_sphere_normals_match_local_surface_without_claiming_outward_orientation() -> None:
    cloud = _fibonacci_sphere()
    result = _estimate(
        cloud, NormalEstimationPolicy(radius=0.48, minimum_neighbors=5, maximum_neighbors=20)
    )

    resolved = [normal for normal in result.normal_estimates if normal is not None]
    assert len(resolved) >= 110
    assert all(
        abs(_dot(normal, cloud.points[index])) > 0.85
        for index, normal in enumerate(result.normal_estimates)
        if normal
    )
    assert not result.ambiguous_orientation_edges
    assert result.policy.as_dict()["physical_orientation_inference"] is False


def test_radius_boundary_is_inclusive_and_outside_points_are_unresolved() -> None:
    points = tuple((column * 0.125, row * 0.125, 0.0) for row in range(5) for column in range(5))
    boundary = _estimate(
        PointCloudData(points),
        NormalEstimationPolicy(radius=0.125, minimum_neighbors=3, maximum_neighbors=8),
    )
    center_index = 2 * 5 + 2
    assert boundary.neighborhood_counts[center_index] == 4

    outside = _estimate(
        PointCloudData(points),
        NormalEstimationPolicy(radius=0.124, minimum_neighbors=3, maximum_neighbors=8),
    )
    assert center_index in outside.unresolved_point_indices
    assert outside.normal_estimates[center_index] is None


def test_sparse_and_collinear_neighborhoods_are_reported_unresolved() -> None:
    sparse = PointCloudData(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)))
    sparse_result = _estimate(
        sparse,
        NormalEstimationPolicy(radius=0.01, minimum_neighbors=3, maximum_neighbors=4),
    )
    assert sparse_result.unresolved_point_indices == (0, 1, 2)
    assert sparse_result.normal_estimates == (None, None, None)

    line = PointCloudData(tuple((index * 0.1, 0.0, 0.0) for index in range(9)))
    line_result = _estimate(
        line,
        NormalEstimationPolicy(radius=0.31, minimum_neighbors=3, maximum_neighbors=8),
    )
    assert len(line_result.unresolved_point_indices) == len(line.points)


def test_output_is_deterministic_parent_immutable_and_provenance_bound() -> None:
    cloud = _plane()
    original_points = cloud.points
    policy = NormalEstimationPolicy(radius=0.16, minimum_neighbors=3, maximum_neighbors=12)

    first = _estimate(cloud, policy)
    second = _estimate(cloud, policy)

    assert first.as_dict() == second.as_dict()
    assert first.child_revision_id == second.child_revision_id
    assert first.source_point_cloud is cloud
    assert cloud.points == original_points
    assert first.parent_revision_id == "captured-points-r1"
    assert first.scale_state is ScaleState.METRIC_UNVERIFIED
    assert first.scale_provenance_id == "scale-provenance-r1"
    assert first.physical_accuracy_validation_status == PHYSICAL_VALIDATION_DEFERRED
    assert first.mold_use_authorized is False
    assert len(first.parent_geometry_sha256) == 64
    assert len(first.geometry_sha256) == 64


def test_orientation_ambiguity_is_reported_for_near_orthogonal_normals() -> None:
    cloud = PointCloudData(
        (
            (0.0, 0.0, 0.0),
            (0.0, 0.1, 0.0),
            (0.1, 0.0, 0.0),
            (0.0, 0.0, 0.1),
            (0.0, 0.1, 0.1),
            (0.1, 0.0, 0.1),
        )
    )
    result = _estimate(
        cloud,
        NormalEstimationPolicy(
            radius=0.15,
            minimum_neighbors=3,
            maximum_neighbors=5,
            orientation_ambiguity_cosine=0.99,
        ),
    )
    assert result.ambiguous_orientation_edges
    assert any(
        edge.reason == "near-orthogonal-normal-pair" for edge in result.ambiguous_orientation_edges
    )


def test_resource_and_scale_authority_bounds_fail_closed() -> None:
    cloud = _plane()
    with pytest.raises(NormalEstimationError, match="point count exceeds"):
        _estimate(
            cloud,
            NormalEstimationPolicy(
                radius=0.16, minimum_neighbors=3, maximum_neighbors=12, maximum_points=20
            ),
        )
    with pytest.raises(NormalEstimationError, match="neighbor-search work"):
        _estimate(
            _plane(5, 0.001),
            NormalEstimationPolicy(
                radius=1.0,
                minimum_neighbors=3,
                maximum_neighbors=20,
                maximum_neighbor_candidates=10,
            ),
        )
    with pytest.raises(NormalEstimationError, match="scale_state"):
        estimate_point_cloud_normals(
            cloud,
            parent_revision_id="parent-r1",
            scale_state=ScaleState.METRIC_VERIFIED,
        )


def test_policy_rejects_invalid_neighborhood_and_ambiguity_values() -> None:
    with pytest.raises(NormalEstimationError, match="neighbor limits"):
        NormalEstimationPolicy(minimum_neighbors=2)
    with pytest.raises(NormalEstimationError, match="orientation_ambiguity_cosine"):
        NormalEstimationPolicy(orientation_ambiguity_cosine=1.0)


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(a[index] * b[index] for index in range(3))
