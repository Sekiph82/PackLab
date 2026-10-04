from __future__ import annotations

import pytest
from test_cad_brep import _inputs, _model

import packlab_core.technical_drawing_dimensions as drawing_dimensions
from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_standalone_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_operations import create_revolve_operation
from packlab_core.design_profile import ProfilePoint, create_design_profile
from packlab_core.reconstruction import ScaleState
from packlab_core.technical_drawing_dimensions import (
    DrawingDimensionError,
    SelectedFeatureDimensionSource,
    build_drawing_dimensions,
)

FRAME = "dimension-assembly-frame:fixture-v1"


def _feature_model(scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED):
    base = _model(scale_state, "standalone", f"dimension-feature-{scale_state.value}")
    features = (
        DesignModelFeatureReference(
            stable_feature_id("bottle", FeatureKind.NECK, "neck-solid"),
            "bottle",
            FeatureKind.NECK,
            "neck-solid",
        ),
        DesignModelFeatureReference(
            stable_feature_id("bottle", FeatureKind.SHOULDER, "revolve-axis"),
            "bottle",
            FeatureKind.SHOULDER,
            "revolve-axis",
        ),
    )
    return create_standalone_design_model_revision(
        base.standalone_root,
        package_family=PackageFamily.BOTTLE,
        features=features,
        actor_id="operator-1",
        reason="Create a neck-only CAD dimension fixture.",
        created_at_utc="2026-10-04T12:00:00Z",
    )


def _brep(model, radius: float, height: float):
    profile = create_design_profile(
        (ProfilePoint(0.0, radius), ProfilePoint(height, radius)), model.scale_state
    )
    operation = create_revolve_operation(
        model,
        profile,
        profile_feature_id=model.features[0].feature_id,
        axis_feature_id=model.features[1].feature_id,
    )
    return revolve_design_model_to_brep(model, profile, operation)


def test_overall_dimensions_are_exact_and_stably_anchored() -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)

    first = build_drawing_dimensions(model, representation, coordinate_frame_id=FRAME)
    second = build_drawing_dimensions(model, representation, coordinate_frame_id=FRAME)
    by_kind = {item.dimension_kind: item for item in first.dimensions}

    assert first.revision_id == second.revision_id
    assert first.as_dict() == second.as_dict()
    assert by_kind["OVERALL_HEIGHT"].value == pytest.approx(100.0)
    assert by_kind["OVERALL_WIDTH_X"].value == pytest.approx(10.0)
    assert by_kind["OVERALL_DEPTH_Y"].value == pytest.approx(10.0)
    assert all(item.coordinate_unit == "mm_unverified" for item in first.dimensions)
    assert all(item.unit_label == "mm (UNVERIFIED)" for item in first.dimensions)
    assert all(item.value_status == "MM_UNVERIFIED" for item in first.dimensions)
    assert all(item.arrow_anchors and item.text_anchor for item in first.dimensions)
    assert all(not item.typography_baked_into_measurement for item in first.dimensions)
    assert first.as_dict()["physical_accuracy_inferred"] is False


def test_relative_units_neck_feature_and_assembly_component_dimensions() -> None:
    relative_model, relative_profile, relative_operation = _inputs(ScaleState.RELATIVE)
    relative_brep = revolve_design_model_to_brep(
        relative_model, relative_profile, relative_operation
    )
    relative_drawing = build_drawing_dimensions(
        relative_model, relative_brep, coordinate_frame_id=FRAME
    )
    assert all(item.unit_label == "reconstruction_units" for item in relative_drawing.dimensions)
    assert all("mm" not in item.unit_label.casefold() for item in relative_drawing.dimensions)

    model = _feature_model()
    body_brep = _brep(model, radius=7.0, height=30.0)
    placed_neck_brep = _brep(model, radius=3.0, height=15.0)
    source = SelectedFeatureDimensionSource(
        component_reference_id="neck-instance-2",
        placement_revision_id="placement:neck-instance-2:v1",
        feature_id=model.features[0].feature_id,
        representation=placed_neck_brep,
        placement_matrix=(
            1.0,
            0.0,
            0.0,
            20.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ),
    )

    drawing = build_drawing_dimensions(
        model, body_brep, coordinate_frame_id=FRAME, selected_features=(source,)
    )
    feature_dimensions = tuple(
        item for item in drawing.dimensions if item.feature_id == model.features[0].feature_id
    )
    assert len(feature_dimensions) == 3
    by_axis = {item.measurement_axis: item for item in feature_dimensions}
    assert by_axis["X"].value == pytest.approx(6.0)
    assert by_axis["Y"].value == pytest.approx(6.0)
    assert by_axis["Z"].value == pytest.approx(15.0)
    assert by_axis["X"].component_reference_id == "neck-instance-2"
    assert by_axis["X"].placement_revision_id == "placement:neck-instance-2:v1"
    assert by_axis["X"].feature_reference_scope == "whole_component_solid"
    assert all(item.collision_stack_index == 1 for item in feature_dimensions)
    assert drawing.as_dict()["coordinate_unit"] == "mm_unverified"


def test_stale_or_unmapped_feature_references_reject() -> None:
    model = _feature_model()
    representation = _brep(model, radius=7.0, height=30.0)
    stale = SelectedFeatureDimensionSource(
        "stale-feature-instance",
        "placement:stale-feature:v1",
        "feature:deleted",
        representation,
    )
    with pytest.raises(DrawingDimensionError, match="feature_reference_stale_or_missing"):
        build_drawing_dimensions(
            model, representation, coordinate_frame_id=FRAME, selected_features=(stale,)
        )

    unresolved = SelectedFeatureDimensionSource(
        "unmapped-feature-instance",
        "placement:unmapped-feature:v1",
        model.features[1].feature_id,
        representation,
    )
    with pytest.raises(DrawingDimensionError, match="feature_mapping_not_unambiguous"):
        build_drawing_dimensions(
            model, representation, coordinate_frame_id=FRAME, selected_features=(unresolved,)
        )


@pytest.mark.parametrize(
    "bounds",
    [
        (0.0, 0.0, 0.0, 0.0, 10.0, 20.0),
        (5.0, 0.0, 0.0, 0.0, 10.0, 20.0),
    ],
)
def test_zero_or_negative_spans_reject(
    monkeypatch: pytest.MonkeyPatch, bounds: tuple[float, ...]
) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    monkeypatch.setattr(
        drawing_dimensions, "cad_shape_precise_bounds", lambda *_args, **_kwargs: bounds
    )

    with pytest.raises(DrawingDimensionError, match="span_must_be_positive"):
        build_drawing_dimensions(model, representation, coordinate_frame_id=FRAME)


def test_changed_coordinate_frame_invalidates_document() -> None:
    model, profile, operation = _inputs(ScaleState.RELATIVE)
    representation = revolve_design_model_to_brep(model, profile, operation)

    with pytest.raises(DrawingDimensionError, match="coordinate_frame_invalid"):
        build_drawing_dimensions(model, representation, coordinate_frame_id=" ")
