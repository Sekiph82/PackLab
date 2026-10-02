from __future__ import annotations

import math

import pytest

from packlab_core.coordinate_frame import (
    PACKLAB_NORMALIZED_FRAME,
    CoordinateFrameError,
    NormalizedFrameTransform,
    coordinate_unit_for_scale_state,
    serialize_frame_transform,
)
from packlab_core.reconstruction import ScaleState

IDENTITY = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)


def _transform(
    matrix: tuple[float, ...] = IDENTITY,
    *,
    transform_id: str = "transform-a",
    source_frame: str = "reconstruction-frame",
    target_frame: str = PACKLAB_NORMALIZED_FRAME,
    state: ScaleState = ScaleState.RELATIVE,
    input_unit: str = "reconstruction_units",
    unit: str | None = None,
    revision: str = "reconstruction-r8",
    provenance: str = "scale-provenance-r2",
) -> NormalizedFrameTransform:
    return NormalizedFrameTransform(
        transform_id,
        source_frame,
        target_frame,
        revision,
        state,
        input_unit,
        coordinate_unit_for_scale_state(state) if unit is None else unit,
        matrix,
        "owner_or_algorithm_selection",
        provenance,
    )


def test_packlab_frame_is_right_handed_z_up_and_front_is_explicit_plus_y() -> None:
    record = _transform().as_dict()
    axes = record["axes"]
    assert axes == {"right": "+X", "front": "+Y", "up": "+Z", "handedness": "right"}
    assert record["target_frame"] == PACKLAB_NORMALIZED_FRAME
    assert record["coordinate_unit"] == "reconstruction_units"


def test_transform_inverse_round_trip_and_composition_order() -> None:
    scale_translate = (
        2.0,
        0.0,
        0.0,
        3.0,
        0.0,
        2.0,
        0.0,
        -4.0,
        0.0,
        0.0,
        2.0,
        5.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )
    first = _transform(scale_translate, target_frame="intermediate-frame")
    second_matrix = (
        0.0,
        -1.0,
        0.0,
        1.0,
        1.0,
        0.0,
        0.0,
        2.0,
        0.0,
        0.0,
        1.0,
        -3.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )
    second = _transform(
        second_matrix,
        transform_id="transform-b",
        source_frame="intermediate-frame",
        target_frame=PACKLAB_NORMALIZED_FRAME,
    )
    point = (1.25, -2.0, 0.5)
    composed = first.then(second)
    expected = second.apply_point(first.apply_point(point))
    actual = composed.apply_point(point)
    assert actual == pytest.approx(expected)
    assert composed.inverse().apply_point(actual) == pytest.approx(point)
    assert composed.parent_transform_ids == ("transform-a", "transform-b")


@pytest.mark.parametrize(
    ("state", "unit"),
    [
        (ScaleState.RELATIVE, "mm"),
        (ScaleState.METRIC_UNVERIFIED, "mm"),
        (ScaleState.METRIC_VERIFIED, "mm_unverified"),
    ],
)
def test_coordinate_units_must_match_metric_scale_state(state: ScaleState, unit: str) -> None:
    with pytest.raises(CoordinateFrameError, match="coordinate_unit_conflicts"):
        _transform(state=state, unit=unit)


def test_unit_semantics_are_explicit_for_all_scale_states() -> None:
    assert coordinate_unit_for_scale_state(ScaleState.RELATIVE) == "reconstruction_units"
    assert coordinate_unit_for_scale_state(ScaleState.METRIC_UNVERIFIED) == "mm_unverified"
    assert coordinate_unit_for_scale_state(ScaleState.METRIC_VERIFIED) == "mm"
    with pytest.raises(CoordinateFrameError, match="coordinate_unit_conflicts"):
        _transform(state=ScaleState.METRIC_UNVERIFIED, input_unit="mm")


@pytest.mark.parametrize(
    "matrix",
    [
        (math.nan,) + IDENTITY[1:],
        (0.0,) * 16,
        (
            -1.0,
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
        ),
        (
            1.0,
            0.2,
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
        ),
    ],
)
def test_invalid_nonfinite_singular_reflected_or_sheared_transforms_fail(matrix) -> None:
    with pytest.raises(CoordinateFrameError):
        _transform(matrix)


def test_transform_serialization_is_deterministic_and_records_provenance() -> None:
    transform = _transform()
    first = serialize_frame_transform(transform)
    second = serialize_frame_transform(transform)
    assert first == second
    assert b'"mutates_source_geometry":false' in first
    assert b'"scale_provenance_id":"scale-provenance-r2"' in first


def test_composition_rejects_frame_revision_state_or_provenance_mismatch() -> None:
    first = _transform(target_frame="intermediate-frame")
    with pytest.raises(CoordinateFrameError, match="frame_chain_mismatch"):
        first.then(_transform(transform_id="transform-b"))
    with pytest.raises(CoordinateFrameError, match="reconstruction_revision_mismatch"):
        first.then(
            _transform(
                transform_id="transform-b",
                source_frame="intermediate-frame",
                revision="reconstruction-r9",
            )
        )
    with pytest.raises(CoordinateFrameError, match="scale_state_mismatch"):
        first.then(
            _transform(
                transform_id="transform-b",
                source_frame="intermediate-frame",
                state=ScaleState.METRIC_UNVERIFIED,
            )
        )


def test_composition_rejects_incompatible_unit_chain() -> None:
    scale_transform = _transform(
        state=ScaleState.METRIC_UNVERIFIED,
        target_frame="metric-intermediate-frame",
    )
    bad_following = _transform(
        transform_id="transform-b",
        source_frame="metric-intermediate-frame",
        target_frame=PACKLAB_NORMALIZED_FRAME,
        state=ScaleState.METRIC_UNVERIFIED,
    )
    with pytest.raises(CoordinateFrameError, match="unit_chain_mismatch"):
        scale_transform.then(bad_following)
