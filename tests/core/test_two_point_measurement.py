from __future__ import annotations

import math

import pytest

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.reconstruction import ScaleState
from packlab_core.two_point_measurement import (
    SnapPolicy,
    TwoPointMeasurementError,
    measure_two_point_distance,
    serialize_two_point_measurement,
)


def _geometry(
    *,
    points=((0.0, 0.0, 0.0), (10.0, 0.0, 0.0)),
    state=ScaleState.RELATIVE,
):
    metric = state is not ScaleState.RELATIVE
    return NormalizedMeasurementGeometry(
        "normalized-transform-r1",
        "object-geometry-r1",
        tuple(points),
        state,
        "mm_unverified" if metric else "reconstruction_units",
        "scale-provenance-r1" if metric else None,
        0.01 if metric else None,
        "mm_per_reconstruction_unit" if metric else None,
    )


def _measure(geometry, first, second, *, enabled=False, radius=0.0, tolerance=0.0):
    policy = SnapPolicy(
        enabled,
        radius,
        tolerance,
        geometry.coordinate_unit,
    )
    return measure_two_point_distance(
        geometry,
        first,
        second,
        snap_policy=policy,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )


def test_exact_euclidean_distance_without_snapping() -> None:
    geometry = _geometry()
    result = _measure(geometry, (0.0, 0.0, 0.0), (3.0, 4.0, 0.0))
    assert result.distance == 5.0
    assert result.coordinate_unit == "reconstruction_units"
    assert result.snapped_candidate_indices == (None, None)


def test_snap_radius_boundary_includes_candidate_but_just_outside_does_not() -> None:
    geometry = _geometry()
    boundary = _measure(geometry, (0.5, 0.0, 0.0), (10.0, 0.0, 0.0), enabled=True, radius=0.5)
    outside = _measure(geometry, (0.5001, 0.0, 0.0), (10.0, 0.0, 0.0), enabled=True, radius=0.5)
    assert boundary.snapped_candidate_indices == (0, 1)
    assert boundary.snap_distances[0] == 0.5
    assert boundary.distance == 10.0
    assert outside.snapped_candidate_indices == (None, 1)
    assert outside.requested_points[0] == (0.5001, 0.0, 0.0)
    assert outside.measured_points[0] == outside.requested_points[0]


def test_ambiguous_snap_candidates_fail_closed() -> None:
    geometry = _geometry(points=((-1.0, 0.0, 0.0), (1.0, 0.0, 0.0)))
    with pytest.raises(TwoPointMeasurementError, match="snap_candidate_ambiguous"):
        _measure(
            geometry,
            (0.0, 0.0, 0.0),
            (5.0, 0.0, 0.0),
            enabled=True,
            radius=1.0,
            tolerance=0.001,
        )


@pytest.mark.parametrize(
    ("state", "unit"),
    [
        (ScaleState.RELATIVE, "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ],
)
def test_scale_state_controls_distance_units(state, unit) -> None:
    geometry = _geometry(state=state)
    result = _measure(geometry, (0.0, 0.0, 0.0), (3.0, 4.0, 0.0))
    assert result.coordinate_unit == unit
    assert result.as_dict()["scale_provenance_id"] == geometry.scale_provenance_id
    assert result.as_dict()["physical_accuracy_claimed"] is False


@pytest.mark.parametrize("point", [(1.0, 2.0), (math.nan, 0.0, 0.0), (True, 0.0, 0.0)])
def test_invalid_requested_coordinates_are_rejected(point) -> None:
    geometry = _geometry()
    with pytest.raises(TwoPointMeasurementError, match="finite_3d"):
        _measure(geometry, point, (1.0, 1.0, 1.0))


def test_provenance_is_deterministic_and_source_geometry_is_unchanged() -> None:
    geometry = _geometry()
    before = geometry.points
    first = _measure(geometry, (0.5, 0.0, 0.0), (8.0, 0.0, 0.0), enabled=True, radius=0.5)
    second = _measure(geometry, (0.5, 0.0, 0.0), (8.0, 0.0, 0.0), enabled=True, radius=0.5)
    assert first.measurement_id == second.measurement_id
    assert serialize_two_point_measurement(first) == serialize_two_point_measurement(second)
    assert first.as_dict()["snap_policy"]["radius"] == 0.5
    assert first.as_dict()["normalized_geometry_revision"] == geometry.normalized_geometry_revision
    assert first.as_dict()["uncertainty_inputs"]["propagation_status"] == "preserved_for_PL-0217"
    assert geometry.points == before


def test_stale_geometry_and_scale_provenance_are_rejected() -> None:
    geometry = _geometry(state=ScaleState.METRIC_UNVERIFIED)
    policy = SnapPolicy(False, 0.0, 0.0, geometry.coordinate_unit)
    with pytest.raises(TwoPointMeasurementError, match="geometry_revision_stale"):
        measure_two_point_distance(
            geometry,
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            snap_policy=policy,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision="normalized-transform-r2",
            current_scale_provenance_id=geometry.scale_provenance_id,
        )
    with pytest.raises(TwoPointMeasurementError, match="scale_provenance_stale"):
        measure_two_point_distance(
            geometry,
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            snap_policy=policy,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id="scale-provenance-r2",
        )
