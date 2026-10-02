from __future__ import annotations

import math

import pytest

from packlab_core.component_cleanup import ComponentCleanupPolicy, cleanup_isolated_components
from packlab_core.geometry_adapter import PointCloudData, TriangleMeshData
from packlab_core.geometry_statistics import (
    GeometryStatisticsError,
    GeometryStatisticsPolicy,
    compute_geometry_statistics,
)
from packlab_core.hole_detection import analyze_mesh_holes
from packlab_core.reconstruction import ScaleState


def _tetrahedron() -> TriangleMeshData:
    return TriangleMeshData(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        triangles=((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )


def _grid_with_floater() -> TriangleMeshData:
    side = 5
    vertices = [(float(column), float(row), 0.0) for row in range(side) for column in range(side)]
    triangles: list[tuple[int, int, int]] = []
    for row in range(side - 1):
        for column in range(side - 1):
            top_left = row * side + column
            top_right = top_left + 1
            bottom_left = top_left + side
            bottom_right = bottom_left + 1
            triangles.extend(
                ((top_left, top_right, bottom_right), (top_left, bottom_right, bottom_left))
            )
    base = len(vertices)
    vertices.extend(((10.0, 0.0, 0.0), (11.0, 0.0, 0.0), (10.0, 1.0, 0.0)))
    triangles.append((base, base + 1, base + 2))
    return TriangleMeshData(tuple(vertices), tuple(triangles))


def test_point_cloud_statistics_counts_bounds_density_spacing_and_units() -> None:
    cloud = PointCloudData(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
    stats = compute_geometry_statistics(
        cloud,
        geometry_revision_id="captured-points-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
    )

    assert stats.point_count == 4
    assert stats.vertex_count is None
    assert stats.face_count is None
    assert stats.bounds_minimum == (0.0, 0.0, 0.0)
    assert stats.bounds_maximum == (1.0, 1.0, 1.0)
    assert stats.bounds_diagonal == pytest.approx(math.sqrt(3.0))
    assert stats.bounding_box_sample_density == 4.0
    assert stats.sampled_nearest_vertex_spacing_minimum == 1.0
    assert stats.sampled_nearest_vertex_spacing_mean == 1.0
    assert stats.coordinate_unit == "mm_unverified"
    assert (
        stats.bounding_box_sample_density_unit == "points_or_vertices_per_mm_cubed_unverified_proxy"
    )
    assert stats.connected_component_count is None
    assert stats.connected_component_status.startswith("NOT_APPLICABLE")
    assert stats.interpretation == "DIAGNOSTIC_ONLY_NO_PHYSICAL_ACCURACY_CLAIM"


def test_mesh_statistics_counts_surface_edges_components_and_relative_units() -> None:
    mesh = _tetrahedron()
    stats = compute_geometry_statistics(
        mesh,
        geometry_revision_id="captured-mesh-r1",
        scale_state=ScaleState.RELATIVE,
    )

    assert stats.point_count is None
    assert stats.vertex_count == 4
    assert stats.face_count == 4
    assert stats.surface_area == pytest.approx((3.0 + math.sqrt(3.0)) / 2.0)
    assert stats.edge_length_minimum == 1.0
    assert stats.edge_length_maximum == pytest.approx(math.sqrt(2.0))
    assert stats.connected_component_count == 1
    assert stats.connected_component_face_counts == (4,)
    assert stats.coordinate_unit == "reconstruction_units"
    assert stats.area_unit == "reconstruction_units_squared"
    assert dict(stats.topology_indicators)["unique_edge_count"] == 6


def test_hole_report_and_component_revision_links_require_exact_geometry() -> None:
    mesh = TriangleMeshData(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        triangles=((0, 1, 2),),
    )
    hole_report = analyze_mesh_holes(
        mesh,
        parent_revision_id="captured-mesh-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
    )
    linked = compute_geometry_statistics(
        mesh,
        geometry_revision_id="captured-mesh-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        hole_report=hole_report,
    )
    assert linked.hole_report_linkage == (hole_report.report_id, "ANALYZED", 1, 0)

    cleanup = cleanup_isolated_components(
        _grid_with_floater(),
        parent_revision_id="captured-grid-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        policy=ComponentCleanupPolicy(
            minimum_component_triangles=5, maximum_removable_fraction=0.05
        ),
    )
    component_stats = compute_geometry_statistics(
        cleanup.mesh,
        geometry_revision_id=cleanup.child_revision_id,
        scale_state=cleanup.scale_state,
        scale_provenance_id=cleanup.scale_provenance_id,
        component_revision=cleanup,
    )
    assert component_stats.connected_component_count == 1
    assert component_stats.component_revision_linkage == (
        cleanup.child_revision_id,
        cleanup.parent_revision_id,
        1,
    )

    with pytest.raises(GeometryStatisticsError, match="stale or bound"):
        compute_geometry_statistics(
            _tetrahedron(),
            geometry_revision_id="captured-mesh-r1",
            scale_state=ScaleState.METRIC_UNVERIFIED,
            scale_provenance_id="scale-provenance-r1",
            hole_report=hole_report,
        )


def test_empty_and_degenerate_geometry_are_rejected() -> None:
    with pytest.raises(GeometryStatisticsError, match="must contain points"):
        compute_geometry_statistics(
            PointCloudData(()),
            geometry_revision_id="empty-cloud-r1",
            scale_state=ScaleState.RELATIVE,
        )
    with pytest.raises(GeometryStatisticsError, match="must contain faces"):
        compute_geometry_statistics(
            TriangleMeshData(
                vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
                triangles=(),
            ),
            geometry_revision_id="empty-mesh-r1",
            scale_state=ScaleState.RELATIVE,
        )
    degenerate = TriangleMeshData(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)),
        triangles=((0, 1, 2),),
    )
    with pytest.raises(GeometryStatisticsError, match="degenerate triangle"):
        compute_geometry_statistics(
            degenerate,
            geometry_revision_id="degenerate-mesh-r1",
            scale_state=ScaleState.RELATIVE,
        )


def test_flat_mesh_density_proxy_is_unavailable_and_statistics_are_deterministic() -> None:
    mesh = _tetrahedron()
    policy = GeometryStatisticsPolicy(maximum_spacing_samples=2)
    first = compute_geometry_statistics(
        mesh,
        geometry_revision_id="mesh-r1",
        scale_state=ScaleState.RELATIVE,
        policy=policy,
    )
    second = compute_geometry_statistics(
        mesh,
        geometry_revision_id="mesh-r1",
        scale_state=ScaleState.RELATIVE,
        policy=policy,
    )
    assert first.as_dict() == second.as_dict()
    assert first.geometry_sha256 == second.geometry_sha256
    assert first.spacing_sample_count == 2
    assert first.bounding_box_sample_density == 4.0

    flat = TriangleMeshData(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        triangles=((0, 1, 2),),
    )
    flat_stats = compute_geometry_statistics(
        flat,
        geometry_revision_id="flat-mesh-r1",
        scale_state=ScaleState.RELATIVE,
    )
    assert flat_stats.bounding_box_sample_density is None
    assert flat_stats.density_status == "ZERO_BOUNDS_VOLUME_PROXY_UNAVAILABLE"


def test_metric_verified_and_stale_component_links_are_rejected() -> None:
    mesh = _tetrahedron()
    with pytest.raises(GeometryStatisticsError, match="scale_state"):
        compute_geometry_statistics(
            mesh,
            geometry_revision_id="mesh-r1",
            scale_state=ScaleState.METRIC_VERIFIED,
        )
    cleanup = cleanup_isolated_components(
        _grid_with_floater(),
        parent_revision_id="captured-grid-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        policy=ComponentCleanupPolicy(
            minimum_component_triangles=5, maximum_removable_fraction=0.05
        ),
    )
    with pytest.raises(GeometryStatisticsError, match="component revision linkage"):
        compute_geometry_statistics(
            _tetrahedron(),
            geometry_revision_id=cleanup.child_revision_id,
            scale_state=ScaleState.METRIC_UNVERIFIED,
            scale_provenance_id="scale-provenance-r1",
            component_revision=cleanup,
        )
