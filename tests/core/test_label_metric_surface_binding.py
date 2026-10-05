from __future__ import annotations

import importlib
import json
from dataclasses import replace

import pytest
from tests.core.test_label_zone import BODY_ID, COMPONENT_ID, NOW, _model, _representation

import packlab_core.label_metric_surface_binding as metric_binding
from packlab_core.cad_adapter import _registered_shape_build
from packlab_core.cad_brep import _representation_from_lineage
from packlab_core.cad_label_surface_analysis import (
    CadLabelSurfacePolicy,
    analyze_cad_label_surfaces,
)
from packlab_core.label_metric_surface_binding import (
    LabelMetricSurfaceBindingError,
    create_label_dieline,
    create_label_metric_surface_binding,
)
from packlab_core.label_zone import LabelZoneBoundary, LabelZoneKind, create_label_zone
from packlab_core.label_zone_placement import create_label_zone_placement_revision
from packlab_core.reconstruction import ScaleState


def _placement(
    model,
    brep,
    kind: LabelZoneKind,
    boundary: LabelZoneBoundary = LabelZoneBoundary(0.1, 0.2, 0.7, 0.8),
):
    zone = create_label_zone(
        model,
        brep,
        zone_kind=kind,
        component_id=COMPONENT_ID,
        feature_id=BODY_ID,
        boundary=boundary,
    )
    return create_label_zone_placement_revision(
        zone,
        zone.boundary,
        actor_id="operator-1",
        reason="Create metric binding fixture.",
        created_at_utc=NOW,
    )


def _cylinder():
    model = _model(label="metric-cylinder")
    shape = importlib.import_module("OCP.BRepPrimAPI").BRepPrimAPI_MakeCylinder(5.0, 20.0).Shape()
    feature_ids = (BODY_ID,)
    build = _registered_shape_build(model, "metric-cylinder-op", feature_ids, shape, 1)
    brep = _representation_from_lineage(
        model,
        "metric-cylinder-op",
        feature_ids,
        build,
        source_feature_ids=feature_ids,
    )
    return model, brep


def _trapezoid_prism():
    model = _model(label="metric-trapezoid")
    api = importlib.import_module("OCP.BRepBuilderAPI")
    gp = importlib.import_module("OCP.gp")
    polygon = api.BRepBuilderAPI_MakePolygon()
    for x, z in ((0.0, 0.0), (100.0, 0.0), (80.0, 40.0), (0.0, 40.0)):
        polygon.Add(gp.gp_Pnt(x, 0.0, z))
    polygon.Close()
    face = api.BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
    prism_api = importlib.import_module("OCP.BRepPrimAPI")
    shape = prism_api.BRepPrimAPI_MakePrism(face, gp.gp_Vec(0.0, 60.0, 0.0)).Shape()
    feature_ids = (BODY_ID,)
    build = _registered_shape_build(model, "metric-trapezoid-op", feature_ids, shape, 1)
    brep = _representation_from_lineage(
        model,
        "metric-trapezoid-op",
        feature_ids,
        build,
        source_feature_ids=feature_ids,
    )
    return model, brep


@pytest.mark.parametrize(
    ("kind", "host_y", "expected_sign"),
    [(LabelZoneKind.FRONT, 60.0, 1.0), (LabelZoneKind.BACK, 0.0, -1.0)],
)
def test_planar_front_back_bind_exact_rectangle_and_map_normalized_subrectangle(
    kind: LabelZoneKind, host_y: float, expected_sign: float
) -> None:
    model = _model(label=f"metric-{kind.value}")
    brep = _representation(model)
    placement = _placement(model, brep, kind)
    analysis = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1e6))
    region = next(
        candidate
        for candidate in analysis.candidates
        if candidate.surface_type == "GeomAbs_Plane"
        and candidate.center[1] == pytest.approx(host_y)
    )

    binding = create_label_metric_surface_binding(
        model, brep, placement, analysis, region.analysis_region_id
    )
    dieline = create_label_dieline(binding, placement)

    assert binding.mapping_mode == "PLANAR_RECTANGULAR"
    assert (binding.host_width_mm_unverified, binding.host_height_mm_unverified) == pytest.approx(
        (100.0, 40.0)
    )
    assert dieline.coordinate_unit == "mm_unverified"
    assert dieline.width == pytest.approx(60.0)
    assert dieline.height == pytest.approx(24.0)
    assert dieline.boundary_vertices[0][0] == pytest.approx(expected_sign * 10.0)
    assert dieline.winding in {"CLOCKWISE", "COUNTERCLOCKWISE"}
    serialized = dieline.as_dict()
    assert serialized["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert serialized["parent_authority"]["revision_id"] == brep.parent_authority_revision_id
    assert serialized["source_to_dieline_mapping"] == dict(binding.mapping_parameters)
    assert serialized["print_fit_verified"] is False
    assert json.dumps(serialized, sort_keys=True, allow_nan=False)


def test_cylindrical_wrap_uses_exact_circumference_and_partial_arc_length() -> None:
    model, brep = _cylinder()
    placement = _placement(model, brep, LabelZoneKind.WRAP)
    analysis = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1.0))
    region = next(item for item in analysis.candidates if item.surface_type == "GeomAbs_Cylinder")

    binding = create_label_metric_surface_binding(
        model, brep, placement, analysis, region.analysis_region_id
    )
    dieline = create_label_dieline(binding, placement)

    assert binding.mapping_mode == "CYLINDRICAL_WRAP"
    assert binding.host_width_mm_unverified == pytest.approx(10.0 * 3.141592653589793)
    assert binding.host_height_mm_unverified == pytest.approx(20.0)
    assert dieline.width == pytest.approx(6.0 * 3.141592653589793)
    assert dieline.height == pytest.approx(12.0)
    assert dieline.as_dict()["mapping_mode"] == "CYLINDRICAL_WRAP"


def test_full_wrap_emits_exact_circumference_and_reordered_runtime_faces_are_stable(
    monkeypatch,
) -> None:
    model, brep = _cylinder()
    placement = _placement(
        model,
        brep,
        LabelZoneKind.WRAP,
        LabelZoneBoundary(0.0, 0.0, 1.0, 1.0),
    )
    analysis = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1.0))
    region = next(item for item in analysis.candidates if item.surface_type == "GeomAbs_Cylinder")
    baseline = create_label_metric_surface_binding(
        model, brep, placement, analysis, region.analysis_region_id
    )
    original = metric_binding.sample_cad_surface_regions
    monkeypatch.setattr(
        metric_binding,
        "sample_cad_surface_regions",
        lambda *args, **kwargs: tuple(reversed(original(*args, **kwargs))),
    )
    reordered = create_label_metric_surface_binding(
        model, brep, placement, analysis, region.analysis_region_id
    )

    assert reordered == baseline
    assert create_label_dieline(baseline, placement).width == pytest.approx(
        10.0 * 3.141592653589793
    )


def test_relative_and_stale_analysis_candidates_fail_closed() -> None:
    model = _model(ScaleState.RELATIVE, label="metric-relative")
    brep = _representation(model)
    placement = _placement(model, brep, LabelZoneKind.FRONT)
    analysis = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1e6))
    candidate = analysis.candidates[0]
    with pytest.raises(LabelMetricSurfaceBindingError, match="mm_unverified"):
        create_label_metric_surface_binding(
            model, brep, placement, analysis, candidate.analysis_region_id
        )
    metric_model = _model(label="metric-stale")
    metric_brep = _representation(metric_model)
    metric_placement = _placement(metric_model, metric_brep, LabelZoneKind.FRONT)
    metric_analysis = analyze_cad_label_surfaces(
        metric_model, metric_brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1e6)
    )
    with pytest.raises(LabelMetricSurfaceBindingError, match="region_not_found"):
        create_label_metric_surface_binding(
            metric_model, metric_brep, metric_placement, metric_analysis, "stale"
        )


def test_deterministic_binding_and_dieline_ids_and_source_immutability() -> None:
    model = _model(label="metric-deterministic")
    brep = _representation(model)
    placement = _placement(model, brep, LabelZoneKind.FRONT)
    analysis = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1e6))
    region = next(
        item
        for item in analysis.candidates
        if item.surface_type == "GeomAbs_Plane" and item.center[1] == pytest.approx(60.0)
    )
    before_model, before_brep = model.as_dict(), brep.as_dict()

    first = create_label_metric_surface_binding(
        model, brep, placement, analysis, region.analysis_region_id
    )
    second = create_label_metric_surface_binding(
        model, brep, placement, analysis, region.analysis_region_id
    )
    dieline_a, dieline_b = (
        create_label_dieline(first, placement),
        create_label_dieline(second, placement),
    )

    assert first == second
    assert dieline_a == dieline_b
    assert model.as_dict() == before_model
    assert brep.as_dict() == before_brep
    assert "runtime_face" not in json.dumps(first.as_dict())
    assert "face_index" not in json.dumps(first.as_dict())


def test_non_planar_surface_cannot_be_substituted_with_whole_solid_bounds() -> None:
    model, brep = _cylinder()
    placement = _placement(model, brep, LabelZoneKind.FRONT)
    analysis = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1.0))
    candidate = next(
        item for item in analysis.candidates if item.surface_type == "GeomAbs_Cylinder"
    )

    with pytest.raises(LabelMetricSurfaceBindingError, match="planar_host_required"):
        create_label_metric_surface_binding(
            model, brep, placement, analysis, candidate.analysis_region_id
        )


def test_nonrectangular_planar_trim_rejects() -> None:
    model, brep = _trapezoid_prism()
    placement = _placement(model, brep, LabelZoneKind.FRONT)
    analysis = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1e6))
    candidate = next(
        item
        for item in analysis.candidates
        if item.surface_type == "GeomAbs_Plane" and item.center[1] == pytest.approx(60.0)
    )

    with pytest.raises(LabelMetricSurfaceBindingError, match="planar_"):
        create_label_metric_surface_binding(
            model, brep, placement, analysis, candidate.analysis_region_id
        )


def test_multiple_exact_host_matches_fail_closed(monkeypatch) -> None:
    model = _model(label="metric-ambiguous")
    brep = _representation(model)
    placement = _placement(model, brep, LabelZoneKind.FRONT)
    analysis = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1e6))
    candidate = next(
        item
        for item in analysis.candidates
        if item.surface_type == "GeomAbs_Plane" and item.center[1] == pytest.approx(60.0)
    )
    original = metric_binding.sample_cad_surface_regions

    def ambiguous(*args, **kwargs):
        regions = original(*args, **kwargs)
        expected = tuple(
            sorted(set(tuple(round(value, 9) for value in p) for p in candidate.support_points))
        )
        selected = next(
            item
            for item in regions
            if tuple(
                sorted({tuple(round(value, 9) for value in p.point) for p in item.support_points})
            )
            == expected
        )
        other_face = next(
            item._runtime_face
            for item in regions
            if not item._runtime_face.IsSame(selected._runtime_face)
        )
        return (*regions, replace(selected, _runtime_face=other_face))

    monkeypatch.setattr(metric_binding, "sample_cad_surface_regions", ambiguous)
    with pytest.raises(LabelMetricSurfaceBindingError, match="resolution_ambiguous"):
        create_label_metric_surface_binding(
            model, brep, placement, analysis, candidate.analysis_region_id
        )
