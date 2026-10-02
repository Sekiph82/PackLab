from __future__ import annotations

import pytest

from packlab_core.geometry_adapter import PointCloudData, TriangleMeshData
from packlab_core.hole_detection import HoleDetectionError, HoleDetectionPolicy, analyze_mesh_holes
from packlab_core.reconstruction import ScaleState


def _analyze(mesh: TriangleMeshData | PointCloudData, **kwargs):
    return analyze_mesh_holes(
        mesh,
        parent_revision_id="captured-mesh-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        **kwargs,
    )


def _triangle_disk(offset: float = 0.0) -> TriangleMeshData:
    return TriangleMeshData(
        vertices=(
            (offset, 0.0, 0.0),
            (offset + 1.0, 0.0, 0.0),
            (offset, 1.0, 0.0),
        ),
        triangles=((0, 1, 2),),
    )


def _tetrahedron() -> TriangleMeshData:
    return TriangleMeshData(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        triangles=((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )


def test_closed_mesh_reports_no_boundary_loops() -> None:
    result = _analyze(_tetrahedron())

    assert result.disposition == "ANALYZED"
    assert result.loops == ()
    assert result.unresolved_components == ()


def test_one_open_boundary_loop_has_deterministic_order_and_metrics() -> None:
    mesh = _triangle_disk()
    result = _analyze(mesh, uncertain_vertex_indices=(1,), coverage_gap_vertex_indices=())

    assert len(result.loops) == 1
    loop = result.loops[0]
    assert loop.boundary_vertex_indices == (0, 1, 2)
    assert loop.perimeter == pytest.approx(2.0 + 2**0.5)
    assert loop.approximate_area == pytest.approx(0.5)
    assert loop.extent == (1.0, 1.0, 0.0)
    assert loop.location == pytest.approx((1 / 3, 1 / 3, 0.0))
    assert loop.support_face_indices == (0, 0, 0)
    assert loop.touches_uncertain_region is True
    assert loop.touches_coverage_gap is False


def test_multiple_boundary_loops_are_stably_ordered() -> None:
    mesh = TriangleMeshData(
        vertices=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (3.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (3.0, 1.0, 0.0),
        ),
        triangles=((0, 1, 2), (3, 4, 5)),
    )
    result = _analyze(mesh)

    assert tuple(loop.boundary_vertex_indices for loop in result.loops) == ((0, 1, 2), (3, 4, 5))
    assert tuple(loop.location[0] for loop in result.loops) == pytest.approx((1 / 3, 10 / 3))
    assert all(loop.touches_uncertain_region is None for loop in result.loops)
    assert all(loop.touches_coverage_gap is None for loop in result.loops)


def test_open_branched_boundary_and_degenerate_face_are_explicitly_ambiguous() -> None:
    mesh = TriangleMeshData(
        vertices=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (3.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (5.0, 0.0, 0.0),
        ),
        triangles=((0, 1, 2), (0, 3, 4), (5, 6, 7)),
    )
    result = _analyze(mesh)

    assert result.disposition == "PARTIAL_AMBIGUOUS_TOPOLOGY"
    assert result.degenerate_face_indices == (2,)
    assert len(result.loops) == 1
    assert result.loops[0].approximate_area == 0.0
    assert any(
        item.reason == "boundary-network-is-open-or-branched"
        for item in result.unresolved_components
    )


def test_point_cloud_returns_explicit_not_applicable_without_fabricated_holes() -> None:
    result = _analyze(PointCloudData(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))))

    assert result.disposition == "NOT_APPLICABLE_POINT_CLOUD_BOUNDARY_LOOPS_REQUIRE_TRIANGLE_MESH"
    assert result.loops == ()
    assert result.unresolved_components == ()


def test_face_boundary_and_traversal_work_are_bounded() -> None:
    mesh = _triangle_disk()
    with pytest.raises(HoleDetectionError, match="face count"):
        _analyze(_tetrahedron(), policy=HoleDetectionPolicy(maximum_faces=3))
    with pytest.raises(HoleDetectionError, match="boundary edge count"):
        _analyze(mesh, policy=HoleDetectionPolicy(maximum_boundary_edges=2))
    with pytest.raises(HoleDetectionError, match="traversal"):
        _analyze(mesh, policy=HoleDetectionPolicy(maximum_traversal_steps=1))


def test_report_identity_is_deterministic_parent_bound_and_preserves_scale_authority() -> None:
    mesh = _triangle_disk()
    first = _analyze(mesh)
    second = _analyze(mesh)

    assert first.as_dict() == second.as_dict()
    assert first.report_id == second.report_id
    assert first.parent_revision_id == "captured-mesh-r1"
    assert first.scale_state is ScaleState.METRIC_UNVERIFIED
    assert first.scale_provenance_id == "scale-provenance-r1"
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False
    assert len(first.parent_geometry_sha256) == 64


def test_uncertainty_indices_are_validated() -> None:
    with pytest.raises(HoleDetectionError, match="out of range"):
        _analyze(_triangle_disk(), uncertain_vertex_indices=(4,))


def test_unreferenced_vertices_are_reported_as_ambiguous_topology() -> None:
    mesh = TriangleMeshData(vertices=((0.0, 0.0, 0.0),), triangles=())
    result = _analyze(mesh)

    assert result.disposition == "PARTIAL_AMBIGUOUS_TOPOLOGY"
    assert result.unresolved_components[0].vertex_indices == (0,)
    assert (
        result.unresolved_components[0].reason
        == "unreferenced-vertices-not-part-of-boundary-topology"
    )
