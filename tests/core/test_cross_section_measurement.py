from __future__ import annotations

import math

import pytest

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.cross_section_measurement import (
    CrossSectionMeasurementError,
    CrossSectionSelection,
    measure_cross_section,
    serialize_cross_section_measurement,
)
from packlab_core.reconstruction import ScaleState


def _ellipse_points(major: float, minor: float, count: int = 64, noise: float = 0.0):
    return tuple(
        (
            major * math.cos(2.0 * math.pi * index / count) + noise * math.sin(7.0 * index),
            minor * math.sin(2.0 * math.pi * index / count) + noise * math.cos(11.0 * index),
            0.0,
        )
        for index in range(count)
    )


def _measure(
    points, *, state=ScaleState.RELATIVE, tolerance=1e-8, current_revision="normalized-r1"
):
    metric = state is not ScaleState.RELATIVE
    geometry = NormalizedMeasurementGeometry(
        "normalized-r1",
        "geometry-r1",
        tuple(points),
        state,
        "mm_unverified" if metric else "reconstruction_units",
        "scale-r1" if metric else None,
        0.02 if metric else None,
        "mm_per_reconstruction_unit" if metric else None,
    )
    selection = CrossSectionSelection(
        "section-r1",
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        tuple(range(len(points))),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        tolerance,
    )
    result = measure_cross_section(
        geometry,
        selection,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=current_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )
    return geometry, selection, result


def test_synthetic_circle_reports_equal_radius_and_diameter() -> None:
    _, _, result = _measure(_ellipse_points(3.0, 3.0))
    assert result.major_radius == pytest.approx(3.0)
    assert result.minor_radius == pytest.approx(3.0)
    assert result.major_diameter == pytest.approx(6.0)
    assert result.minor_diameter == pytest.approx(6.0)
    assert result.rms_radial_residual == pytest.approx(0.0, abs=1e-12)


def test_synthetic_ellipse_reports_principal_radii_and_fit_residuals() -> None:
    _, _, result = _measure(_ellipse_points(4.0, 2.0))
    assert result.major_radius == pytest.approx(4.0)
    assert result.minor_radius == pytest.approx(2.0)
    assert result.major_diameter == pytest.approx(8.0)
    assert result.minor_diameter == pytest.approx(4.0)
    assert result.maximum_radial_residual < 1e-12


def test_sparse_noisy_section_reports_residual_quality_and_stable_output() -> None:
    points = _ellipse_points(4.0, 2.0, count=12, noise=0.015)
    geometry, selection, first = _measure(points, tolerance=0.03)
    second = measure_cross_section(
        geometry,
        selection,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )
    assert first.measurement_id == second.measurement_id
    assert serialize_cross_section_measurement(first) == serialize_cross_section_measurement(second)
    assert first.sample_count == 12
    assert first.rms_radial_residual > 0.0
    assert first.maximum_radial_residual >= first.rms_radial_residual
    assert first.as_dict()["uncertainty_inputs"]["fit_uncertainty_status"] == (
        "residuals_reported; statistical confidence interval not estimated"
    )


@pytest.mark.parametrize(
    ("state", "unit"),
    [
        (ScaleState.RELATIVE, "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ],
)
def test_result_preserves_relative_and_unverified_metric_units(state, unit) -> None:
    _, _, result = _measure(_ellipse_points(2.0, 1.0), state=state)
    assert result.coordinate_unit == unit
    assert result.as_dict()["physical_accuracy_claimed"] is False
    assert result.as_dict()["thread_or_finish_standard_inferred"] is False


def test_insufficient_and_collinear_sections_are_rejected() -> None:
    with pytest.raises(CrossSectionMeasurementError, match="insufficient_points"):
        CrossSectionSelection(
            "section", "geometry-r1", "normalized-r1", (0, 1, 2, 3), (0, 0, 0), (0, 0, 1), 0.0
        )
    line = tuple((float(index), 0.0, 0.0) for index in range(6))
    with pytest.raises(CrossSectionMeasurementError, match="degenerate_or_collinear"):
        _measure(line)


def test_nonplanar_or_stale_section_fails_closed() -> None:
    points = list(_ellipse_points(2.0, 1.0))
    points[0] = (points[0][0], points[0][1], 0.1)
    with pytest.raises(CrossSectionMeasurementError, match="not_planar"):
        _measure(tuple(points), tolerance=0.01)
    with pytest.raises(CrossSectionMeasurementError, match="parent_stale"):
        _measure(_ellipse_points(2.0, 1.0), current_revision="normalized-r2")
