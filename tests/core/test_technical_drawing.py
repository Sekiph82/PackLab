from __future__ import annotations

import importlib

import pytest
from test_cad_brep import _inputs, _model

from packlab_core.cad_adapter import (
    _registered_shape_build,
    project_visible_cad_edges,
)
from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.design_operations import create_revolve_operation
from packlab_core.design_profile import ProfilePoint, create_design_profile
from packlab_core.reconstruction import ScaleState
from packlab_core.technical_drawing import generate_orthographic_views


def test_box_hlr_projection_has_expected_front_extents() -> None:
    model = _model(ScaleState.RELATIVE, "standalone", "technical-drawing-box")
    box_builder = importlib.import_module("OCP.BRepPrimAPI").BRepPrimAPI_MakeBox(10.0, 20.0, 30.0)
    shape_build = _registered_shape_build(
        model, "test-box-operation", ("test-box-input",), box_builder.Shape(), 1
    )

    curves = project_visible_cad_edges(
        shape_build.shape_handle,
        screen_right=(1.0, 0.0, 0.0),
        screen_up=(0.0, 0.0, 1.0),
    )
    points = tuple(point for curve in curves for point in curve.points)

    assert points
    assert (min(point[0] for point in points), max(point[0] for point in points)) == (
        0.0,
        10.0,
    )
    assert (min(point[1] for point in points), max(point[1] for point in points)) == (
        0.0,
        30.0,
    )


def test_cylinder_views_are_canonical_vector_outputs_and_repeatable() -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)

    first = generate_orthographic_views(model, representation)
    second = generate_orthographic_views(model, representation)

    assert first.revision_id == second.revision_id
    assert first.as_dict() == second.as_dict()
    assert tuple(view.view_id for view in first.views) == ("FRONT", "SIDE", "TOP")
    assert tuple(view.screen_right for view in first.views) == (
        (1.0, 0.0, 0.0),
        (0.0, -1.0, 0.0),
        (-1.0, 0.0, 0.0),
    )
    assert tuple(view.screen_up for view in first.views) == (
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0),
    )
    assert first.views[0].bounds == pytest.approx((-5.0, 0.0, 5.0, 100.0), abs=1e-6)
    assert first.coordinate_unit == "mm_unverified"
    assert first.scale_state == ScaleState.METRIC_UNVERIFIED.value
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False
    assert first.vector_source_authority == "EXACT_CAD_BREP_HLR"
    assert first.edge_visibility_policy == "OCCT_EXACT_HLR_VISIBLE_EDGES_ONLY"
    assert first.hidden_edges_included is False
    assert len(first.views[0].curves) > 0
    assert first.views[0].curves[0].points
    assert first.views[0].curves[0].feature_lineage_status == (
        "UNRESOLVED_EDGE_TO_FEATURE_ASSOCIATION"
    )
    assert first.feature_references == second.feature_references
    assert first.feature_mapping_revision_id == second.feature_mapping_revision_id
    assert first.as_dict()["raster_source_of_truth"] is False
    assert first.as_dict()["physical_accuracy_inferred"] is False
    assert first.as_dict()["manufacturing_suitability_inferred"] is False


def test_bottle_profile_and_explicit_front_direction() -> None:
    model, _, _ = _inputs(ScaleState.RELATIVE)
    profile = create_design_profile(
        (
            ProfilePoint(0.0, 14.0),
            ProfilePoint(28.0, 14.0),
            ProfilePoint(34.0, 8.0),
            ProfilePoint(78.0, 8.0),
            ProfilePoint(84.0, 12.0),
            ProfilePoint(100.0, 12.0),
        ),
        ScaleState.RELATIVE,
    )
    operation = create_revolve_operation(
        model,
        profile,
        profile_feature_id=model.features[0].feature_id,
        axis_feature_id=model.features[1].feature_id,
    )
    representation = revolve_design_model_to_brep(model, profile, operation)

    drawing = generate_orthographic_views(
        model,
        representation,
        front_direction=(1.0, 0.0, 0.0),
        front_direction_revision_id="front-direction:bottle-fixture-v1",
    )

    assert drawing.front_direction == (1.0, 0.0, 0.0)
    assert drawing.front_direction_source == "EXPLICIT_INPUT"
    assert drawing.front_direction_revision_id == "front-direction:bottle-fixture-v1"
    assert drawing.coordinate_unit == "reconstruction_units"
    assert drawing.scale_state == ScaleState.RELATIVE.value
    assert drawing.views[0].screen_right == (0.0, -1.0, 0.0)
    front_bounds = drawing.views[0].bounds
    assert front_bounds[0] == pytest.approx(-front_bounds[2], abs=1e-6)
    assert (
        14.0 < front_bounds[2] < 15.0
    )  # Smooth profile interpolation slightly rounds the shoulder.
    assert front_bounds[1:] == pytest.approx((0.0, front_bounds[2], 100.0), abs=1e-6)
    assert len(drawing.views[0].curves) > 1
    assert all(curve.points for view in drawing.views for curve in view.curves)


@pytest.mark.parametrize(
    ("parent_mode", "expected_parent"),
    [
        ("captured", "CAPTURED_SCAN_MASTER"),
        ("standalone", "STANDALONE_DESIGN_GEOMETRY"),
    ],
)
def test_drawing_preserves_exact_parent_authority(parent_mode: str, expected_parent: str) -> None:
    model, profile, operation = _inputs(ScaleState.RELATIVE, parent_mode)
    representation = revolve_design_model_to_brep(model, profile, operation)
    drawing = generate_orthographic_views(model, representation)
    parent_revision = (
        model.parent_binding_revision_id
        if model.parent_binding_revision_id is not None
        else model.standalone_root.revision_id
    )

    assert drawing.parent_kind == expected_parent
    assert drawing.parent_authority_revision_id == parent_revision
    assert drawing.source_design_model_revision_id == model.revision_id
    assert drawing.source_brep_revision_id == representation.revision_id
    assert drawing.source_brep_geometry_sha256 == representation.geometry_sha256
    assert drawing.coordinate_unit == "reconstruction_units"
