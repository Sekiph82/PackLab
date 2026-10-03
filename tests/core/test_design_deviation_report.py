from __future__ import annotations

from dataclasses import replace

import pytest
from test_cross_section_overlay import FRAME, _cube, _scan

from packlab_core.design_deviation_report import (
    DeviationReportError,
    SectionDeviationTarget,
    calculate_design_deviation_report,
)
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.scan_design_heatmap import (
    DesignModelGeometryReference,
    DistanceSignPolicy,
    HeatmapPolicy,
)
from packlab_core.scan_master import mesh_sha256


def _open_triangle() -> TriangleMeshData:
    return TriangleMeshData(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )


def _context(scan_mesh: TriangleMeshData, model_mesh: TriangleMeshData):
    scan = _scan(scan_mesh)
    binding = bind_design_model_parent(
        scan,
        actor_id="operator-1",
        reason="Pin deviation report fixture.",
        created_at_utc="2026-10-03T17:00:00Z",
    )
    semantics = ("loft-section:0000", "loft-section:0001")
    features = tuple(
        DesignModelFeatureReference(
            stable_feature_id("container", FeatureKind.BODY, semantic),
            "container",
            FeatureKind.BODY,
            semantic,
        )
        for semantic in semantics
    )
    model = create_design_model_revision(
        binding,
        package_family=PackageFamily.BOTTLE,
        features=features,
        actor_id="operator-1",
        reason="Create deviation report fixture model.",
        created_at_utc="2026-10-03T17:01:00Z",
    )
    geometry = _geometry(model, model_mesh)
    targets = (
        SectionDeviationTarget(features[0].feature_id, "section-upper", 0.75, geometry),
        SectionDeviationTarget(features[1].feature_id, "section-lower", 0.25, geometry),
    )
    return scan, model, geometry, targets


def _geometry(model, mesh: TriangleMeshData) -> DesignModelGeometryReference:
    return DesignModelGeometryReference(
        model.revision_id,
        model.project_id,
        model.fitted_to_scan_master_revision_id,
        mesh,
        mesh_sha256(mesh),
        FRAME,
        model.scale_state,
        model.scale_provenance_id,
    )


def _report(scan, model, geometry, regions):
    return calculate_design_deviation_report(
        scan,
        model,
        geometry,
        regions,
        expected_scan_master_revision_id=scan.revision_id,
        expected_scan_master_geometry_sha256=mesh_sha256(scan.mesh),
    )


def test_zero_and_known_deviation_are_deterministic_and_ranked_by_region():
    scan, model, geometry, targets = _context(_cube(), _cube())
    zero = _report(scan, model, geometry, targets)
    repeated = _report(scan, model, geometry, targets)
    assert zero == repeated
    assert zero.report_id == repeated.report_id
    assert all(region.peak_deviation == pytest.approx(0.0) for region in zero.regions)
    assert all(not region.deviation_present for region in zero.regions)

    scan, model, geometry, targets = _context(_cube(), _cube(0.2))
    feature_targets = (
        replace(targets[0], geometry=_geometry(model, _cube(0.3))),
        replace(targets[1], geometry=_geometry(model, _cube(0.1))),
    )
    report = _report(scan, model, geometry, tuple(reversed(feature_targets)))
    assert len(report.regions) == 2
    assert {region.feature_id for region in report.regions} == {item.feature_id for item in targets}
    assert {region.feature_semantic_key for region in report.regions} == {
        "loft-section:0000",
        "loft-section:0001",
    }
    assert [region.height for region in report.regions] == [0.75, 0.25]
    assert [region.peak_deviation for region in report.regions] == pytest.approx([0.3, 0.1])
    assert all(region.deviation_present for region in report.regions)
    assert [region.feature_geometry_sha256 for region in report.regions] == [
        mesh_sha256(_cube(0.3)),
        mesh_sha256(_cube(0.1)),
    ]
    assert report.heatmap.design_model_geometry_sha256 == geometry.geometry_sha256
    assert [region.feature_geometry_sha256 for region in report.regions] == [
        mesh_sha256(_cube(0.3)),
        mesh_sha256(_cube(0.1)),
    ]
    assert report.heatmap.design_model_geometry_sha256 == geometry.geometry_sha256


def test_exact_parents_unverified_units_and_no_tolerance_claim():
    scan, model, geometry, targets = _context(_cube(), _cube(0.1))
    report = _report(scan, model, geometry, targets)
    data = report.as_dict()
    assert report.scan_master_geometry_sha256 == mesh_sha256(scan.mesh)
    assert report.design_model_revision_id == model.revision_id
    assert report.units == "mm_unverified"
    assert data["scale"]["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert data["scale"]["mold_use_authorized"] is False
    assert data["tolerance_interpretation"] == "GEOMETRY_DEVIATION_ONLY_NOT_MANUFACTURING_TOLERANCE"
    assert data["is_manufacturing_tolerance"] is False
    assert data["authority_class"] == "DERIVED_SCAN_DESIGN_DEVIATION_DIAGNOSTIC"
    assert data["scan_master_changed"] is False


def test_open_surfaces_are_unsigned_and_do_not_claim_inside_outside_direction():
    mesh = _open_triangle()
    scan, model, geometry, targets = _context(mesh, mesh)
    target = (replace(targets[0], height=0.5),)
    report = _report(scan, model, geometry, target)
    surface = report.as_dict()["surface_comparison"]
    assert surface["distance_sign_policy"] == DistanceSignPolicy.UNSIGNED.value
    assert surface["signed_distance_available"] is False
    assert surface["inside_outside_direction_available"] is False
    assert surface["design_surface_watertight"] is False
    assert surface["open_surface_direction_limited"] is True
    assert report.regions[0].peak_deviation == pytest.approx(0.0)

    with pytest.raises(DeviationReportError, match="signed_deviation_report_not_supported"):
        calculate_design_deviation_report(
            scan,
            model,
            geometry,
            target,
            expected_scan_master_revision_id=scan.revision_id,
            expected_scan_master_geometry_sha256=mesh_sha256(scan.mesh),
            heatmap_policy=HeatmapPolicy(sign_policy=DistanceSignPolicy.SIGNED_INSIDE_NEGATIVE),
        )


def test_stale_model_parent_and_missing_feature_reject():
    scan, model, geometry, targets = _context(_cube(), _cube())
    stale_scan = _scan(_cube(0.1))
    stale_binding = bind_design_model_parent(
        stale_scan,
        actor_id="operator-1",
        reason="Create stale model parent.",
        created_at_utc="2026-10-03T17:02:00Z",
    )
    stale_model = create_design_model_revision(
        stale_binding,
        package_family=PackageFamily.BOTTLE,
        features=model.features,
        actor_id="operator-1",
        reason="Create stale child model.",
        created_at_utc="2026-10-03T17:03:00Z",
    )
    stale_geometry = replace(
        geometry,
        revision_id=stale_model.revision_id,
        fitted_to_scan_master_revision_id=stale_model.fitted_to_scan_master_revision_id,
    )
    with pytest.raises(DeviationReportError, match="scan_master_parent_binding_mismatch"):
        _report(scan, stale_model, stale_geometry, targets)

    missing_feature = replace(targets[0], feature_id="deleted-feature")
    with pytest.raises(DeviationReportError, match="deviation_region_feature_stale_or_missing"):
        _report(scan, model, geometry, (missing_feature,))


def test_invalid_region_targets_and_scale_units_fail_closed():
    scan, model, geometry, targets = _context(_cube(), _cube())
    with pytest.raises(DeviationReportError, match="deviation_regions_invalid_or_unbounded"):
        _report(scan, model, geometry, ())
    with pytest.raises(DeviationReportError, match="deviation_region_duplicate"):
        _report(scan, model, geometry, (targets[0], targets[0]))
    with pytest.raises(DeviationReportError, match="section_height_invalid"):
        SectionDeviationTarget(
            targets[0].feature_id,
            "section-bad",
            float("nan"),
            targets[0].geometry,
        )
    stale_feature_geometry = replace(
        targets[0].geometry,
        fitted_to_scan_master_revision_id="older-scan-master",
    )
    with pytest.raises(DeviationReportError, match="feature_geometry_binding_mismatch"):
        _report(
            scan,
            model,
            geometry,
            (replace(targets[0], geometry=stale_feature_geometry),),
        )
    stale_feature_geometry = replace(
        targets[0].geometry,
        fitted_to_scan_master_revision_id="older-scan-master",
    )
    with pytest.raises(DeviationReportError, match="feature_geometry_binding_mismatch"):
        _report(
            scan,
            model,
            geometry,
            (replace(targets[0], geometry=stale_feature_geometry),),
        )
