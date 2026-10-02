from __future__ import annotations

import math

import pytest

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.reconstruction import ScaleState
from packlab_core.vertical_profile import (
    VerticalProfileError,
    extract_vertical_profile,
    serialize_vertical_profile,
)


def _geometry(points, *, state=ScaleState.RELATIVE):
    metric = state is not ScaleState.RELATIVE
    return NormalizedMeasurementGeometry(
        "normalized-r1",
        "geometry-r1",
        tuple(points),
        state,
        "mm_unverified" if metric else "reconstruction_units",
        "scale-r1" if metric else None,
        0.02 if metric else None,
        "mm_per_reconstruction_unit" if metric else None,
    )


def _extract(
    geometry, direction, *, origin=(0.0, 0.0, 0.0), tolerance=0.0, revision="normalized-r1"
):
    return extract_vertical_profile(
        geometry,
        plane_origin=origin,
        horizontal_direction=direction,
        lateral_tolerance=tolerance,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )


def test_front_and_side_profiles_select_the_explicit_vertical_plane() -> None:
    geometry = _geometry(((-1, 0, 0), (1, 0, 2), (0, 0.01, 1), (0, 0.2, 1), (0, -1, 0), (0, 1, 2)))
    before = geometry.points
    front = _extract(geometry, (1.0, 0.0, 0.0), tolerance=0.02)
    side = _extract(geometry, (0.0, 1.0, 0.0), tolerance=0.0)
    assert len(front.samples) == 3
    assert len(side.samples) == 4
    assert all(sample.captured_point[1] in (0.0, 0.01) for sample in front.samples)
    assert all(sample.captured_point[0] == 0.0 for sample in side.samples)
    assert geometry.points == before


def test_arbitrary_valid_horizontal_direction_is_supported() -> None:
    diagonal = math.sqrt(0.5)
    geometry = _geometry(((0, 0, 0), (1, 1, 1), (2, 2, 2), (1, 0, 1)))
    profile = _extract(geometry, (diagonal, diagonal, 0.0))
    assert len(profile.samples) == 3
    assert profile.plane_normal == pytest.approx((-diagonal, diagonal, 0.0))
    assert [sample.profile_horizontal for sample in profile.samples] == sorted(
        sample.profile_horizontal for sample in profile.samples
    )


@pytest.mark.parametrize(
    "direction",
    [(0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (2.0, 0.0, 0.0)],
)
def test_degenerate_nonhorizontal_or_nonunit_directions_are_rejected(direction) -> None:
    geometry = _geometry(((0, 0, 0), (1, 0, 1)))
    with pytest.raises(VerticalProfileError, match="direction"):
        _extract(geometry, direction)


def test_sparse_and_empty_profile_evidence_is_rejected() -> None:
    sparse = _geometry(((0, 0, 0), (1, 1, 1), (2, 2, 2)))
    with pytest.raises(VerticalProfileError, match="insufficient_samples"):
        _extract(sparse, (1.0, 0.0, 0.0), tolerance=0.0)
    with pytest.raises(VerticalProfileError, match="geometry_empty"):
        _extract(_geometry(()), (1.0, 0.0, 0.0))


def test_sample_order_and_serialization_are_deterministic_and_preserve_source() -> None:
    geometry = _geometry(((2, 0, 2), (-1, 0, 1), (0, 0, 0), (1, 0, 2)))
    before = geometry.points
    first = _extract(geometry, (1.0, 0.0, 0.0))
    second = _extract(geometry, (1.0, 0.0, 0.0))
    assert first.profile_id == second.profile_id
    assert serialize_vertical_profile(first) == serialize_vertical_profile(second)
    assert [sample.profile_horizontal for sample in first.samples] == [-1.0, 0.0, 1.0, 2.0]
    assert first.as_dict()["sampling_policy"]["smoothing"] is False
    assert first.as_dict()["sampling_policy"]["outline_interpolation"] is False
    assert geometry.points == before


@pytest.mark.parametrize(
    ("state", "unit"),
    [
        (ScaleState.RELATIVE, "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ],
)
def test_profile_preserves_scale_state_units(state, unit) -> None:
    profile = _extract(_geometry(((0, 0, 0), (1, 0, 1)), state=state), (1.0, 0.0, 0.0))
    assert profile.coordinate_unit == unit
    assert profile.as_dict()["physical_accuracy_claimed"] is False


def test_stale_source_normalized_or_scale_parent_is_rejected() -> None:
    geometry = _geometry(((0, 0, 0), (1, 0, 1)), state=ScaleState.METRIC_UNVERIFIED)
    with pytest.raises(VerticalProfileError, match="normalized_geometry_parent_stale"):
        _extract(geometry, (1.0, 0.0, 0.0), revision="normalized-r2")
    with pytest.raises(VerticalProfileError, match="scale_provenance_parent_stale"):
        extract_vertical_profile(
            geometry,
            plane_origin=(0.0, 0.0, 0.0),
            horizontal_direction=(1.0, 0.0, 0.0),
            lateral_tolerance=0.0,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id="scale-r2",
        )
