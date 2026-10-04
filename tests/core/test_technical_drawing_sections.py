from __future__ import annotations

import pytest
from test_cad_brep import _inputs, _model

from packlab_core.cad_adapter import CadAdapterError, section_cad_shape
from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.design_operations import create_revolve_operation
from packlab_core.design_profile import ProfilePoint, create_design_profile
from packlab_core.reconstruction import ScaleState
from packlab_core.technical_drawing_sections import (
    DrawingSectionError,
    DrawingSectionSource,
    generate_section_view,
)

FRAME = "canonical-section-frame:fixture-v1"
IDENTITY = (
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
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


def _source(
    component_id: str, radius: float, placement_matrix: tuple[float, ...] = IDENTITY
) -> DrawingSectionSource:
    model = _model(
        ScaleState.METRIC_UNVERIFIED,
        "standalone",
        f"section-{component_id}",
    )
    profile = create_design_profile(
        (ProfilePoint(0.0, radius), ProfilePoint(100.0, radius)),
        ScaleState.METRIC_UNVERIFIED,
    )
    operation = create_revolve_operation(
        model,
        profile,
        profile_feature_id=model.features[0].feature_id,
        axis_feature_id=model.features[1].feature_id,
    )
    representation = revolve_design_model_to_brep(model, profile, operation)
    return DrawingSectionSource(
        component_id,
        FRAME,
        f"placement:{component_id}:v1",
        placement_matrix,
        model,
        representation,
    )


def test_horizontal_and_vertical_sections_have_deterministic_curves() -> None:
    source = _source("body", 5.0)
    model_before = source.model.as_dict()
    brep_before = source.representation.as_dict()

    horizontal = generate_section_view((source,), plane_axis="Z", plane_offset=50.0)
    horizontal_repeat = generate_section_view((source,), plane_axis="Z", plane_offset=50.0)
    vertical = generate_section_view((source,), plane_axis="X", plane_offset=0.0)

    assert horizontal.revision_id == horizontal_repeat.revision_id
    assert horizontal.as_dict() == horizontal_repeat.as_dict()
    assert horizontal.plane_origin == (0.0, 0.0, 50.0)
    assert horizontal.plane_normal == (0.0, 0.0, 1.0)
    assert horizontal.screen_right == (1.0, 0.0, 0.0)
    assert horizontal.screen_up == (0.0, 1.0, 0.0)
    assert horizontal.curves
    assert horizontal.bounds is not None
    assert tuple(curve.curve_id for curve in horizontal.curves) == tuple(
        sorted(curve.curve_id for curve in horizontal.curves)
    )
    assert vertical.plane_origin == (0.0, 0.0, 0.0)
    assert vertical.plane_normal == (1.0, 0.0, 0.0)
    assert vertical.curves
    assert source.model.as_dict() == model_before
    assert source.representation.as_dict() == brep_before


def test_empty_section_and_optional_hatching_metadata_are_explicit() -> None:
    source = _source("body", 5.0)
    result = generate_section_view((source,), plane_axis="Z", plane_offset=101.0)
    document = result.as_dict()

    assert document["empty_section"] is True
    assert result.bounds is None
    assert result.curves == ()
    assert result.components[0].intersected is False
    assert document["hatching"] == {
        "status": "NOT_DERIVED_CLOSED_LOOP_CLASSIFICATION_UNAVAILABLE",
        "regions": [],
    }


def test_multiple_explicit_brep_components_keep_independent_provenance() -> None:
    body = _source("body-instance", 5.0)
    closure = _source(
        "closure-instance",
        3.0,
        (
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

    result = generate_section_view((closure, body), plane_axis="Z", plane_offset=50.0)

    assert result.as_dict()["component_count"] == 2
    assert tuple(item.component_reference_id for item in result.components) == (
        "body-instance",
        "closure-instance",
    )
    assert all(item.intersected for item in result.components)
    assert all(item.source_brep_revision_id for item in result.components)
    assert all(item.parent_authority_revision_id for item in result.components)
    assert all(item.feature_mapping_revision_id for item in result.components)
    assert all(
        curve.component_reference_id in {"body-instance", "closure-instance"}
        for curve in result.curves
    )
    assert result.placement_policy == "EXPLICIT_RIGID_COMPONENT_TRANSFORMS"
    assert result.bounds is not None and result.bounds[2] == pytest.approx(23.0, abs=1e-6)
    assert result.components[1].placement_revision_id == "placement:closure-instance:v1"
    assert result.as_dict()["manufacturing_suitability_inferred"] is False


@pytest.mark.parametrize(
    ("axis", "offset", "message"),
    [
        ("Q", 0.0, "drawing_section_plane_axis_invalid"),
        ("Z", float("nan"), "drawing_section_plane_offset_invalid"),
        ("Z", float("inf"), "drawing_section_plane_offset_invalid"),
        ("Z", 1e10, "drawing_section_plane_offset_invalid"),
    ],
)
def test_invalid_planes_fail_closed(axis: str, offset: float, message: str) -> None:
    source = _source("body", 5.0)

    with pytest.raises(DrawingSectionError, match=message):
        generate_section_view((source,), plane_axis=axis, plane_offset=offset)


def test_mixed_units_and_coordinate_frames_fail_closed() -> None:
    relative_model, profile, operation = _inputs(ScaleState.RELATIVE)
    relative_brep = revolve_design_model_to_brep(relative_model, profile, operation)
    metric = _source("metric-body", 5.0)
    relative = DrawingSectionSource(
        "relative-body",
        FRAME,
        "placement:relative-body:v1",
        IDENTITY,
        relative_model,
        relative_brep,
    )

    with pytest.raises(DrawingSectionError, match="drawing_section_component_units_mismatch"):
        generate_section_view((metric, relative), plane_axis="Z", plane_offset=50.0)

    other_frame = DrawingSectionSource(
        "metric-body-other-frame",
        "other-frame",
        "placement:metric-body-other-frame:v1",
        IDENTITY,
        metric.model,
        metric.representation,
    )
    with pytest.raises(
        DrawingSectionError, match="drawing_section_component_coordinate_frame_mismatch"
    ):
        generate_section_view((metric, other_frame), plane_axis="Z", plane_offset=50.0)


def test_section_edge_work_limit_fails_closed() -> None:
    source = _source("body", 5.0)

    with pytest.raises(CadAdapterError, match="cad_section_edge_limit_exceeded"):
        section_cad_shape(
            source.representation.shape_handle,
            plane_origin=(0.0, 0.0, 0.0),
            plane_normal=(1.0, 0.0, 0.0),
            screen_right=(0.0, 1.0, 0.0),
            screen_up=(0.0, 0.0, 1.0),
            maximum_edges=1,
        )
