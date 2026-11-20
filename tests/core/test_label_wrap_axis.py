"""Wrap-label host rules: cylinders along +/-Z bind, other axes are refused; straight runs."""

from __future__ import annotations

import importlib

import pytest
from tests.core.test_label_zone import BODY_ID, COMPONENT_ID, _model

from packlab_core.cad_adapter import _registered_shape_build, _snap_straight_runs
from packlab_core.cad_brep import _representation_from_lineage
from packlab_core.cad_label_surface_analysis import (
    CadLabelSurfacePolicy,
    analyze_cad_label_surfaces,
)
from packlab_core.label_metric_surface_binding import (
    LabelMetricSurfaceBindingError,
    create_label_metric_surface_binding,
)
from packlab_core.label_zone import LabelZoneBoundary, LabelZoneKind, create_label_zone
from packlab_core.label_zone_placement import create_label_zone_placement_revision


def _cylinder_binding(direction: tuple[float, float, float]):
    model = _model(label=f"wrap-axis-{direction}")
    gp = importlib.import_module("OCP.gp")
    primitive = importlib.import_module("OCP.BRepPrimAPI")
    axis = gp.gp_Ax2(gp.gp_Pnt(0.0, 0.0, 0.0), gp.gp_Dir(*direction))
    shape = primitive.BRepPrimAPI_MakeCylinder(axis, 30.0, 60.0).Shape()
    build = _registered_shape_build(model, "wrap-axis-op", (BODY_ID,), shape, 1)
    brep = _representation_from_lineage(
        model, "wrap-axis-op", (BODY_ID,), build, source_feature_ids=(BODY_ID,)
    )
    analysis = analyze_cad_label_surfaces(
        model, brep, CadLabelSurfacePolicy((0.0, 1.0, 0.0), 90.0, 1.0)
    )
    candidate = next(item for item in analysis.candidates if "Cylinder" in item.surface_type)
    boundary = LabelZoneBoundary(0.0, 0.1, 1.0, 0.9)
    zone = create_label_zone(
        model,
        brep,
        zone_kind=LabelZoneKind.WRAP,
        component_id=COMPONENT_ID,
        feature_id=BODY_ID,
        boundary=boundary,
    )
    placement = create_label_zone_placement_revision(
        zone,
        boundary,
        actor_id="operator-1",
        reason="Wrap axis test.",
        created_at_utc="2026-11-21T00:00:00Z",
    )
    return create_label_metric_surface_binding(
        model, brep, placement, analysis, candidate.analysis_region_id
    )


@pytest.mark.parametrize("direction", [(0.0, 0.0, 1.0), (0.0, 0.0, -1.0)])
def test_wrap_binds_on_a_z_axis_cylinder_either_direction(direction) -> None:
    binding = _cylinder_binding(direction)
    assert binding.mapping_mode == "CYLINDRICAL_WRAP"
    assert binding.host_height_mm_unverified == pytest.approx(60.0)
    assert binding.host_width_mm_unverified == pytest.approx(60.0 * 3.141592653589793)


@pytest.mark.parametrize("direction", [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)])
def test_wrap_refuses_a_cylinder_not_on_the_z_axis(direction) -> None:
    with pytest.raises(LabelMetricSurfaceBindingError, match="cylinder_axis_incompatible"):
        _cylinder_binding(direction)


def test_straight_runs_snap_to_one_segment_within_tolerance() -> None:
    noisy = [(0.0, 10.0), (1.0, 10.2), (2.0, 9.9), (3.0, 10.1), (4.0, 12.0), (5.0, 14.0)]
    assert _snap_straight_runs(noisy, 0.15) == [
        (0.0, 10.05),
        (3.0, 10.05),
        (4.0, 12.0),
        (5.0, 14.0),
    ]
    # Spread 0.3 > 2 * 0.1: nothing is moved.
    assert _snap_straight_runs(noisy, 0.1)[:3] == noisy[:3]
    # Two-sample runs stay as they are (already one segment).
    assert _snap_straight_runs([(0.0, 5.0), (1.0, 5.0)], 0.0) == [(0.0, 5.0), (1.0, 5.0)]
