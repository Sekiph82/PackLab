from __future__ import annotations

from dataclasses import replace

import pytest

from packlab_core.geometry_adapter import PointCloudData, TriangleMeshData
from packlab_core.hole_detection import HoleDetectionPolicy, analyze_mesh_holes
from packlab_core.hole_filling import HoleFillingError, HoleFillingPolicy, fill_reported_mesh_holes
from packlab_core.reconstruction import ScaleState


def _two_rings() -> TriangleMeshData:
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for center_x, inner_half in ((0.0, 0.5), (14.0, 1.5)):
        outer = (
            (center_x - 5.0, -5.0, 0.0),
            (center_x + 5.0, -5.0, 0.0),
            (center_x + 5.0, 5.0, 0.0),
            (center_x - 5.0, 5.0, 0.0),
        )
        inner = (
            (center_x - inner_half, -inner_half, 0.0),
            (center_x + inner_half, -inner_half, 0.0),
            (center_x + inner_half, inner_half, 0.0),
            (center_x - inner_half, inner_half, 0.0),
        )
        base = len(vertices)
        vertices.extend((*outer, *inner))
        for index in range(4):
            following = (index + 1) % 4
            triangles.extend(
                (
                    (base + index, base + following, base + 4 + following),
                    (base + index, base + 4 + following, base + 4 + index),
                )
            )
    return TriangleMeshData(tuple(vertices), tuple(triangles))


def _report(mesh: TriangleMeshData):
    return analyze_mesh_holes(
        mesh,
        parent_revision_id="captured-mesh-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        uncertain_vertex_indices=(),
        coverage_gap_vertex_indices=(),
        policy=HoleDetectionPolicy(),
    )


def _policy() -> HoleFillingPolicy:
    return HoleFillingPolicy(
        maximum_perimeter=5.0,
        maximum_area=1.5,
        maximum_boundary_vertices=4,
        maximum_planarity_deviation=0.01,
        maximum_selected_holes=2,
    )


def _fill(mesh: TriangleMeshData, report, selected: tuple[str, ...], policy=None):
    return fill_reported_mesh_holes(
        mesh,
        report,
        parent_revision_id="captured-mesh-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        policy=_policy() if policy is None else policy,
        selected_loop_ids=selected,
    )


def test_explicitly_selected_small_inner_hole_gets_local_derived_fan_faces() -> None:
    mesh = _two_rings()
    report = _report(mesh)
    small_and_large_inner = tuple(loop for loop in report.loops if loop.approximate_area < 20.0)
    small_loop = min(small_and_large_inner, key=lambda loop: loop.approximate_area)
    parent_snapshot = (mesh.vertices, mesh.triangles, mesh.vertex_colors, mesh.vertex_normals)

    result = _fill(mesh, report, (small_loop.loop_id,))

    assert len(result.filled_holes) == 1
    evidence = result.filled_holes[0]
    assert evidence.loop_id == small_loop.loop_id
    assert evidence.center_vertex_index == len(mesh.vertices)
    assert len(evidence.derived_face_indices) == 4
    assert len(result.after_mesh.triangles) == len(mesh.triangles) + 4
    assert evidence.geometry_authority == "REPAIR_DERIVED_NOT_CAPTURED_EVIDENCE"
    assert evidence.repair_method == "local_convex_planar_centroid_fan_v1"
    assert result.before_mesh is mesh
    assert (
        mesh.vertices,
        mesh.triangles,
        mesh.vertex_colors,
        mesh.vertex_normals,
    ) == parent_snapshot
    assert result.before_geometry_sha256 != result.after_geometry_sha256
    assert len(result.before_geometry_sha256) == len(result.after_geometry_sha256) == 64


def test_oversized_hole_and_unselected_loops_remain_as_limitations() -> None:
    mesh = _two_rings()
    report = _report(mesh)
    inner_loops = tuple(loop for loop in report.loops if loop.approximate_area < 20.0)
    selected = tuple(loop.loop_id for loop in inner_loops)
    result = _fill(mesh, report, selected)

    assert len(result.filled_holes) == 1
    oversized = tuple(item for item in result.unfilled_holes if item.loop_id in selected)
    assert len(oversized) == 1
    assert oversized[0].reason in {"perimeter-exceeds-limit", "area-exceeds-limit"}
    assert (
        sum(item.reason == "not-explicitly-selected-for-repair" for item in result.unfilled_holes)
        == 2
    )
    assert len(result.after_mesh.triangles) == len(mesh.triangles) + 4


def test_deterministic_filled_topology_and_repair_provenance() -> None:
    mesh = _two_rings()
    report = _report(mesh)
    small_loop = min(
        (loop for loop in report.loops if loop.approximate_area < 20.0),
        key=lambda loop: loop.approximate_area,
    )
    first = _fill(mesh, report, (small_loop.loop_id,))
    second = _fill(mesh, report, (small_loop.loop_id,))

    assert first.as_dict() == second.as_dict()
    assert first.child_revision_id == second.child_revision_id
    assert first.after_mesh == second.after_mesh
    assert first.hole_report_id == report.report_id
    assert first.scale_state is ScaleState.METRIC_UNVERIFIED
    assert first.scale_provenance_id == "scale-provenance-r1"
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False


def test_empty_selection_is_a_non_destructive_child_with_all_holes_retained() -> None:
    mesh = _two_rings()
    report = _report(mesh)
    result = _fill(mesh, report, ())

    assert result.after_mesh == mesh
    assert result.filled_holes == ()
    assert len(result.unfilled_holes) == len(report.loops)
    assert result.before_geometry_sha256 == result.after_geometry_sha256


def test_stale_or_ambiguous_reports_and_unknown_ids_cannot_authorize_repair() -> None:
    mesh = _two_rings()
    report = _report(mesh)
    with pytest.raises(HoleFillingError, match="digest is stale"):
        _fill(TriangleMeshData(mesh.vertices, mesh.triangles[:-1]), report, ())
    with pytest.raises(HoleFillingError, match="selected_loop_ids must come"):
        _fill(mesh, report, ("invented-loop",))
    with pytest.raises(HoleFillingError, match="parent revision"):
        fill_reported_mesh_holes(
            mesh,
            report,
            parent_revision_id="other-parent",
            scale_state=ScaleState.METRIC_UNVERIFIED,
            scale_provenance_id="scale-provenance-r1",
            selected_loop_ids=(),
        )
    point_cloud_report = analyze_mesh_holes(
        PointCloudData(((0.0, 0.0, 0.0),)),
        parent_revision_id="captured-mesh-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
    )
    with pytest.raises(HoleFillingError, match="unsupported hole reports"):
        _fill(mesh, point_cloud_report, ())


def test_forged_report_metrics_cannot_bypass_fill_thresholds() -> None:
    mesh = _two_rings()
    report = _report(mesh)
    small_loop = min(
        (loop for loop in report.loops if loop.approximate_area < 20.0),
        key=lambda loop: loop.approximate_area,
    )
    forged_loop = replace(small_loop, perimeter=0.01, approximate_area=0.001)
    forged_report = replace(
        report,
        loops=tuple(
            forged_loop if loop.loop_id == small_loop.loop_id else loop for loop in report.loops
        ),
    )

    result = _fill(mesh, forged_report, (small_loop.loop_id,))
    rejected = next(item for item in result.unfilled_holes if item.loop_id == small_loop.loop_id)
    assert result.filled_holes == ()
    assert rejected.reason == "reported-perimeter-does-not-match-parent-geometry"


def test_threshold_and_selection_bounds_are_explicit() -> None:
    mesh = _two_rings()
    report = _report(mesh)
    small_loop = min(
        (loop for loop in report.loops if loop.approximate_area < 20.0),
        key=lambda loop: loop.approximate_area,
    )
    too_strict = HoleFillingPolicy(
        maximum_perimeter=3.0,
        maximum_area=0.5,
        maximum_boundary_vertices=3,
        maximum_planarity_deviation=0.001,
    )
    result = _fill(mesh, report, (small_loop.loop_id,), too_strict)
    assert result.filled_holes == ()
    selected_unfilled = next(
        item for item in result.unfilled_holes if item.loop_id == small_loop.loop_id
    )
    assert selected_unfilled.reason == "perimeter-exceeds-limit"
    with pytest.raises(HoleFillingError, match="parent-relative safety bounds"):
        _fill(mesh, report, (), HoleFillingPolicy(maximum_perimeter=100.0))


def test_nonplanar_reported_loop_is_not_repaired() -> None:
    mesh = _two_rings()
    original_report = _report(mesh)
    small_loop = min(
        (loop for loop in original_report.loops if loop.approximate_area < 20.0),
        key=lambda loop: loop.approximate_area,
    )
    altered_vertices = list(mesh.vertices)
    altered_vertices[small_loop.boundary_vertex_indices[0]] = (0.0, 0.0, 0.1)
    altered = TriangleMeshData(tuple(altered_vertices), mesh.triangles)
    altered_report = _report(altered)
    altered_small_loop = min(
        (loop for loop in altered_report.loops if loop.approximate_area < 20.0),
        key=lambda loop: loop.approximate_area,
    )
    result = _fill(altered, altered_report, (altered_small_loop.loop_id,))
    selected_unfilled = next(
        item for item in result.unfilled_holes if item.loop_id == altered_small_loop.loop_id
    )
    assert selected_unfilled.reason == "planarity-exceeds-limit"


def test_loop_touching_known_uncertainty_is_retained() -> None:
    mesh = _two_rings()
    base_report = _report(mesh)
    small_loop = min(
        (loop for loop in base_report.loops if loop.approximate_area < 20.0),
        key=lambda loop: loop.approximate_area,
    )
    report = analyze_mesh_holes(
        mesh,
        parent_revision_id="captured-mesh-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        uncertain_vertex_indices=(small_loop.boundary_vertex_indices[0],),
        coverage_gap_vertex_indices=(),
    )
    reported_loop = next(loop for loop in report.loops if loop.approximate_area < 20.0)

    result = _fill(mesh, report, (reported_loop.loop_id,))
    unfilled = next(item for item in result.unfilled_holes if item.loop_id == reported_loop.loop_id)
    assert unfilled.reason == "touches-uncertain-region"
    assert result.filled_holes == ()
