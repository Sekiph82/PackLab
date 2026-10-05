from __future__ import annotations

import json

import pytest
from tests.core.test_label_metric_surface_binding import _model, _placement, _representation

from packlab_core.cad_label_surface_analysis import (
    CadLabelSurfacePolicy,
    analyze_cad_label_surfaces,
)
from packlab_core.label_metric_surface_binding import (
    LabelMetricSurfaceBindingError,
    create_label_dieline,
    create_label_dieline_print_intent,
    create_label_metric_surface_binding,
)
from packlab_core.label_zone import LabelZoneKind


def _dieline():
    model = _model(label="label-print-intent")
    brep = _representation(model)
    placement = _placement(model, brep, LabelZoneKind.FRONT)
    analysis = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1e6))
    region = next(
        item
        for item in analysis.candidates
        if item.surface_type == "GeomAbs_Plane" and item.center[1] == pytest.approx(60.0)
    )
    binding = create_label_metric_surface_binding(
        model, brep, placement, analysis, region.analysis_region_id
    )
    return model, brep, placement, create_label_dieline(binding, placement)


def test_zero_margin_and_bleed_preserve_source_outline_and_use_explicit_units() -> None:
    model, brep, placement, source = _dieline()
    before_model, before_brep, before_source = model.as_dict(), brep.as_dict(), source.as_dict()

    result = create_label_dieline_print_intent(
        source, safe_margin_mm_unverified=0, bleed_mm_unverified=0
    )
    value = result.as_dict()

    assert result.source_dieline_revision_id == source.revision_id
    assert result.boundary_vertices == source.boundary_vertices
    assert result.safe_boundary_vertices == source.boundary_vertices
    assert result.bleed_boundary_vertices == source.boundary_vertices
    assert value["print_intent"]["safe_margin"]["coordinate_unit"] == "mm_unverified"
    assert value["print_intent"]["bleed"]["coordinate_unit"] == "mm_unverified"
    assert value["print_intent"]["authority"] == "USER_DESIGN_PRINT_INTENT_ONLY"
    assert value["print_intent"]["printer_certified"] is False
    assert value["print_fit_verified"] is False
    assert (
        "Printer requirements, print fit, and printer/manufacturer certification are not verified."
        in result.limitations
    )
    assert source.as_dict() == before_source
    assert model.as_dict() == before_model
    assert brep.as_dict() == before_brep
    assert placement.revision_id == result.placement_revision_id
    json.dumps(value, sort_keys=True, allow_nan=False)


def test_positive_values_create_separate_inner_safe_and_outer_bleed_boundaries() -> None:
    _, _, _, source = _dieline()

    result = create_label_dieline_print_intent(
        source, safe_margin_mm_unverified=2.0, bleed_mm_unverified=1.5
    )

    assert result.width == source.width
    assert result.height == source.height
    assert result.boundary_vertices == source.boundary_vertices
    assert result.safe_margin_mm_unverified == 2.0
    assert result.bleed_mm_unverified == 1.5
    assert result.safe_boundary_vertices == ((12.0, 10.0), (68.0, 10.0), (68.0, 30.0), (12.0, 30.0))
    assert result.bleed_boundary_vertices == (
        (8.5, 6.5),
        (71.5, 6.5),
        (71.5, 33.5),
        (8.5, 33.5),
    )
    assert result.revision_id != source.revision_id
    assert result.source_dieline_revision_id == source.revision_id


@pytest.mark.parametrize("value", [-0.01, float("nan"), float("inf"), True, "1", 1e100])
@pytest.mark.parametrize("field", ["safe_margin_mm_unverified", "bleed_mm_unverified"])
def test_invalid_margin_and_bleed_values_reject(value, field: str) -> None:
    _, _, _, source = _dieline()
    values = {"safe_margin_mm_unverified": 0.0, "bleed_mm_unverified": 0.0}
    values[field] = value

    with pytest.raises(LabelMetricSurfaceBindingError, match="finite_nonnegative_mm"):
        create_label_dieline_print_intent(source, **values)


def test_safe_margin_that_consumes_inner_boundary_rejects() -> None:
    _, _, _, source = _dieline()

    with pytest.raises(LabelMetricSurfaceBindingError, match="consumes_boundary"):
        create_label_dieline_print_intent(
            source,
            safe_margin_mm_unverified=source.height / 2,
            bleed_mm_unverified=0,
        )


def test_print_intent_is_deterministic_and_cannot_be_attached_twice() -> None:
    _, _, _, source = _dieline()
    args = {"safe_margin_mm_unverified": 1.25, "bleed_mm_unverified": 0.75}

    first = create_label_dieline_print_intent(source, **args)
    second = create_label_dieline_print_intent(source, **args)

    assert first == second
    assert first.revision_id == second.revision_id
    with pytest.raises(LabelMetricSurfaceBindingError, match="already_attached"):
        create_label_dieline_print_intent(first, **args)
