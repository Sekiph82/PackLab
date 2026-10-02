from __future__ import annotations

from dataclasses import replace

import pytest

from packlab_core.bounding_dimensions import (
    BoundingDimensionError,
    NormalizedMeasurementGeometry,
    measure_bounding_dimensions,
    measurement_geometry_from_normalized_view,
    serialize_bounding_dimensions,
)
from packlab_core.coordinate_frame import PACKLAB_NORMALIZED_FRAME, NormalizedFrameTransform
from packlab_core.normalization_transform import (
    GeometryNormalizationTransform,
    NormalizedGeometryView,
)
from packlab_core.reconstruction import ScaleState


def _box(
    *,
    state: ScaleState = ScaleState.RELATIVE,
    points=((0.0, 0.0, 0.0), (2.0, 3.0, 5.0)),
) -> NormalizedMeasurementGeometry:
    unit = {
        ScaleState.RELATIVE: "reconstruction_units",
        ScaleState.METRIC_UNVERIFIED: "mm_unverified",
        ScaleState.METRIC_VERIFIED: "mm",
    }[state]
    metric = state is not ScaleState.RELATIVE
    return NormalizedMeasurementGeometry(
        "normalized-transform-r1",
        "object-geometry-r1",
        tuple(points),
        state,
        unit,
        "scale-provenance-r1" if metric else None,
        0.01 if metric else None,
        "mm_per_reconstruction_unit" if metric else None,
    )


def _measure(geometry):
    return measure_bounding_dimensions(
        geometry,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )


def test_axis_aligned_box_maps_x_to_width_y_to_depth_and_z_to_height() -> None:
    geometry = _box(points=((-1.0, 2.0, 4.0), (3.0, 8.0, 13.0)))
    before = geometry.points
    result = _measure(geometry)
    assert (result.width, result.depth, result.height) == (4.0, 6.0, 9.0)
    assert result.axis_bounds == {"x": (-1.0, 3.0), "y": (2.0, 8.0), "z": (4.0, 13.0)}
    assert geometry.points == before


@pytest.mark.parametrize(
    ("state", "unit", "scale_id"),
    [
        (ScaleState.RELATIVE, "reconstruction_units", None),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified", "scale-provenance-r1"),
    ],
)
def test_scale_state_controls_dimension_units(state, unit, scale_id) -> None:
    result = _measure(_box(state=state))
    record = result.as_dict()
    assert result.coordinate_unit == unit
    assert result.scale_provenance_id == scale_id
    assert record["physical_accuracy_claimed"] is False


def test_empty_and_non_finite_geometry_fail_closed() -> None:
    with pytest.raises(BoundingDimensionError, match="empty"):
        _measure(_box(points=()))
    with pytest.raises(BoundingDimensionError, match="non_finite"):
        _box(points=((0.0, 0.0, float("nan")),))


def test_stale_geometry_revision_or_scale_provenance_is_rejected() -> None:
    geometry = _box(state=ScaleState.METRIC_UNVERIFIED)
    with pytest.raises(BoundingDimensionError, match="revision_stale"):
        measure_bounding_dimensions(
            geometry,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision="normalized-transform-r2",
            current_scale_provenance_id=geometry.scale_provenance_id,
        )
    with pytest.raises(BoundingDimensionError, match="scale_provenance_stale"):
        measure_bounding_dimensions(
            geometry,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id="scale-provenance-r2",
        )
    with pytest.raises(BoundingDimensionError, match="source_parent_stale"):
        measure_bounding_dimensions(
            geometry,
            current_geometry_id="object-geometry-r2",
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id=geometry.scale_provenance_id,
        )


def test_deterministic_dimensions_bind_transform_and_preserve_scale_uncertainty() -> None:
    geometry = _box(state=ScaleState.METRIC_UNVERIFIED)
    first = _measure(geometry)
    second = _measure(geometry)
    assert first.measurement_id == second.measurement_id
    assert serialize_bounding_dimensions(first) == serialize_bounding_dimensions(second)
    record = first.as_dict()
    assert record["normalized_geometry_revision"] == geometry.normalized_geometry_revision
    assert record["scale_provenance_id"] == geometry.scale_provenance_id
    assert record["uncertainty_inputs"]["scale_factor_uncertainty"] == 0.01
    assert record["uncertainty_inputs"]["propagation_status"] == "preserved_for_PL-0217"
    assert record["dimension_uncertainty_propagated"] is False


def test_normalized_view_binds_exact_transform_and_scale_provenance() -> None:
    frame = NormalizedFrameTransform(
        "frame-transform-r1",
        "object-capture-source",
        PACKLAB_NORMALIZED_FRAME,
        "reconstruction-r1",
        ScaleState.METRIC_UNVERIFIED,
        "reconstruction_units",
        "mm_unverified",
        (
            0.4,
            0.0,
            0.0,
            0.0,
            0.0,
            0.4,
            0.0,
            0.0,
            0.0,
            0.0,
            0.4,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ),
        "synthetic test transform",
        "scale-estimate-r1",
    )
    transform = GeometryNormalizationTransform(
        frame,
        "object-geometry-r1",
        "a" * 64,
        0.4,
        0.01,
        "plane-r1",
        "upright-r1",
        "front-r1",
        ScaleState.RELATIVE,
    )
    view = NormalizedGeometryView(
        "object-geometry-r1",
        frame.transform_id,
        ((0.0, 0.0, 0.0), (0.8, 1.2, 2.0)),
        ((0.0, 0.0, 0.0), (0.8, 1.2, 2.0)),
    )
    measurement_geometry = measurement_geometry_from_normalized_view(view, transform)
    result = measure_bounding_dimensions(
        measurement_geometry,
        current_geometry_id="object-geometry-r1",
        current_normalized_geometry_revision=frame.transform_id,
        current_scale_provenance_id="scale-estimate-r1",
    )
    assert (result.width, result.depth, result.height) == (0.8, 1.2, 2.0)
    assert result.scale_provenance_id == "scale-estimate-r1"
    with pytest.raises(BoundingDimensionError, match="parent_stale"):
        measurement_geometry_from_normalized_view(
            replace(view, transform_id="frame-transform-old"), transform
        )


def test_invalid_scale_unit_or_generated_authority_is_rejected() -> None:
    with pytest.raises(BoundingDimensionError, match="coordinate_unit_conflicts"):
        replace(_box(), coordinate_unit="mm")
    with pytest.raises(BoundingDimensionError, match="captured_geometry_authority"):
        replace(_box(), generated=True)
    with pytest.raises(BoundingDimensionError, match="verified_scale_provenance_record_required"):
        replace(
            _box(state=ScaleState.METRIC_UNVERIFIED),
            scale_state=ScaleState.METRIC_VERIFIED,
            coordinate_unit="mm",
        )
    with pytest.raises(BoundingDimensionError, match="frame_not_canonical"):
        replace(_box(), coordinate_frame_id="unknown-frame")
