from __future__ import annotations

import json

import pytest
from tests.core.test_cross_section_overlay import _scan

from packlab_core.cross_section_overlay import CanonicalAxis, CanonicalPlaneSelection
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.design_preview import DesignPreview
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.jerrycan_handle_void_candidates import (
    HandleVoidDetectionError,
    HandleVoidStatus,
    detect_jerrycan_handle_void_candidates,
)
from packlab_core.scan_master import ScanMasterRevision

PLANE = CanonicalPlaneSelection(CanonicalAxis.X, 0.5)


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> TriangleMeshData:
    vertices = (
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    )
    triangles = (
        (0, 2, 1),
        (0, 3, 2),
        (4, 5, 6),
        (4, 6, 7),
        (0, 1, 5),
        (0, 5, 4),
        (1, 2, 6),
        (1, 6, 5),
        (2, 3, 7),
        (2, 7, 6),
        (3, 0, 4),
        (3, 4, 7),
    )
    return TriangleMeshData(vertices, triangles)


def _combine(*meshes: TriangleMeshData) -> TriangleMeshData:
    vertices = []
    triangles = []
    for mesh in meshes:
        offset = len(vertices)
        vertices.extend(mesh.vertices)
        triangles.extend(tuple(index + offset for index in face) for face in mesh.triangles)
    return TriangleMeshData(tuple(vertices), tuple(triangles))


def _inputs(
    *void_boxes: tuple[float, float, float, float, float, float],
    gaps=(),
    scan_mesh: TriangleMeshData | None = None,
    preview_mesh: TriangleMeshData | None = None,
):
    outer = _box(0.0, 1.0, 0.0, 4.0, 0.0, 8.0)
    parts = [outer]
    parts.extend(_box(*bounds) for bounds in void_boxes)
    scan = _scan(scan_mesh if scan_mesh is not None else _combine(*parts))
    manifest = json.loads(scan.manifest_bytes())
    manifest["coverage_gaps"] = list(gaps)
    scan = ScanMasterRevision(scan.revision_id, scan.project_id, scan.mesh, manifest)
    binding = bind_design_model_parent(
        scan,
        actor_id="fixture-operator",
        reason="Create synthetic jerrycan evidence fixture.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    feature = DesignModelFeatureReference(
        stable_feature_id("jerrycan", FeatureKind.BODY, "body"),
        "jerrycan",
        FeatureKind.BODY,
        "body",
    )
    model = create_design_model_revision(
        binding,
        package_family=PackageFamily.JERRYCAN,
        features=(feature,),
        actor_id="fixture-operator",
        reason="Create synthetic jerrycan Design Model.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    preview = DesignPreview(
        preview_mesh if preview_mesh is not None else outer,
        model.revision_id,
        scan.revision_id,
        model.scan_master_geometry_sha256,
        model.parent_binding_revision_id,
        model.scale_state,
        model.coordinate_unit,
        model.physical_accuracy_validation_status,
        model.mold_use_authorized,
        (
            (
                feature.feature_id,
                tuple(range(len(preview_mesh.vertices if preview_mesh else outer.vertices))),
            ),
        ),
    )
    return scan, model, preview


def _detect(scan, model, preview):
    return detect_jerrycan_handle_void_candidates(
        scan,
        model,
        preview,
        PLANE,
        expected_scan_master_revision_id=scan.revision_id,
        expected_design_model_revision_id=model.revision_id,
    )


def test_single_enclosed_region_is_a_deterministic_candidate_only() -> None:
    scan, model, preview = _inputs((0.25, 0.75, 1.0, 2.0, 2.0, 4.0))
    first = _detect(scan, model, preview)
    second = _detect(scan, model, preview)

    assert first.status is HandleVoidStatus.CANDIDATE
    assert first == second
    assert first.scan_closed_loop_count == 2
    assert first.scan_open_component_count == 0
    assert first.selected_plane_coverage_complete
    assert len(first.candidates) == 1
    candidate = first.as_dict()["candidates"][0]
    assert candidate["parent_feature_ids"] == [model.features[0].feature_id]
    assert candidate["geometry_subtracted"] is False
    assert candidate["handle_opening_created"] is False
    assert candidate["hidden_extent_inferred"] is False
    assert first.as_dict()["hidden_extent_inferred"] is False


def test_no_enclosed_region_reports_no_candidate_for_selected_plane() -> None:
    scan, model, preview = _inputs()
    result = _detect(scan, model, preview)

    assert result.status is HandleVoidStatus.NO_CANDIDATE
    assert result.candidates == ()
    assert "one_selected_plane_does_not_establish_full_three_dimensional_void_extent" in (
        result.limitations
    )


def test_multiple_enclosed_regions_and_incomplete_coverage_require_review() -> None:
    scan, model, preview = _inputs(
        (0.25, 0.75, 0.75, 1.5, 1.5, 2.5),
        (0.25, 0.75, 2.5, 3.25, 4.0, 5.0),
    )
    result = _detect(scan, model, preview)
    assert result.status is HandleVoidStatus.REVIEW_REQUIRED
    assert len(result.candidates) == 2
    assert all(
        candidate.ambiguity == "multiple_enclosed_regions_require_review"
        for candidate in result.candidates
    )

    outer = _box(0.0, 1.0, 0.0, 4.0, 0.0, 8.0)
    incomplete = TriangleMeshData(
        outer.vertices,
        tuple(face for face in outer.triangles if face not in {(0, 1, 5), (0, 5, 4)}),
    )
    partial_scan, partial_model, partial_preview = _inputs(
        gaps=("front-side coverage occluded",),
        scan_mesh=incomplete,
        preview_mesh=outer,
    )
    partial_result = _detect(partial_scan, partial_model, partial_preview)
    assert partial_result.status is HandleVoidStatus.REVIEW_REQUIRED
    assert not partial_result.selected_plane_coverage_complete
    assert partial_result.coverage_gaps == ("front-side coverage occluded",)


def test_stale_parent_and_preview_are_rejected() -> None:
    scan, model, preview = _inputs()
    with pytest.raises(
        HandleVoidDetectionError, match="selected_parent_revision_stale_or_wrong_family"
    ):
        detect_jerrycan_handle_void_candidates(
            scan,
            model,
            preview,
            PLANE,
            expected_scan_master_revision_id=scan.revision_id,
            expected_design_model_revision_id="design-model:stale",
        )
    stale_preview = DesignPreview(
        preview.mesh,
        preview.model_revision_id,
        "older-scan-r0",
        preview.scan_master_geometry_sha256,
        preview.parent_binding_revision_id,
        preview.scale_state,
        preview.coordinate_unit,
        preview.physical_accuracy_validation_status,
        preview.mold_use_authorized,
        preview.feature_vertex_indices,
    )
    with pytest.raises(
        HandleVoidDetectionError, match="jerrycan_design_model_parent_or_authority_mismatch"
    ):
        detect_jerrycan_handle_void_candidates(
            scan,
            model,
            stale_preview,
            PLANE,
            expected_scan_master_revision_id=scan.revision_id,
            expected_design_model_revision_id=model.revision_id,
        )
