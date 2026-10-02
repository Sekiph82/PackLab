from __future__ import annotations

import math

import pytest

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.horizontal_section import (
    HorizontalSectionError,
    extract_horizontal_section,
    serialize_horizontal_section,
)
from packlab_core.reconstruction import ScaleState


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


def _extract(geometry, z, half_width=0.0, *, scale_id="from_geometry"):
    return extract_horizontal_section(
        geometry,
        z,
        slab_half_width=half_width,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=(
            geometry.scale_provenance_id if scale_id == "from_geometry" else scale_id
        ),
    )


def _box_points():
    return tuple(
        (float(x), float(y), float(z)) for z in (0, 2) for x, y in ((0, 0), (0, 1), (1, 0), (1, 1))
    )


def _cylinder_points():
    return tuple(
        (math.cos(2.0 * math.pi * index / 16), math.sin(2.0 * math.pi * index / 16), z)
        for z in (0.0, 1.0, 2.0)
        for index in range(16)
    )


def test_box_exact_boundary_z_includes_captured_face_points() -> None:
    section = _extract(_geometry(_box_points()), 0.0)
    assert section.z_range == (0.0, 2.0)
    assert len(section.points) == 4
    assert all(item.point[2] == 0.0 for item in section.points)
    assert [item.point for item in section.points] == sorted(item.point for item in section.points)


def test_cylinder_section_returns_only_captured_ring_without_closure() -> None:
    section = _extract(_geometry(_cylinder_points()), 1.0, 0.05)
    assert len(section.points) == 16
    assert all(item.point[2] == 1.0 for item in section.points)
    assert section.as_dict()["surface_interpolation_performed"] is False
    assert section.as_dict()["surface_closure_invented"] is False


def test_inclusive_bounded_slab_and_outside_slab_point_selection() -> None:
    geometry = _geometry(((0, 0, 0.0), (1, 0, 0.9), (2, 0, 1.1), (4, 0, 1.10001), (3, 0, 2.0)))
    section = _extract(geometry, 1.0, 0.1)
    assert [item.point[0] for item in section.points] == [1.0, 2.0]
    assert section.maximum_allowed_slab_half_width == pytest.approx(0.2)
    with pytest.raises(HorizontalSectionError, match="exceeds_bound"):
        _extract(geometry, 1.0, 0.21)


def test_empty_no_hit_out_of_range_and_nonfinite_requests_fail_closed() -> None:
    geometry = _geometry(((0, 0, 0.0), (0, 0, 1.0)))
    with pytest.raises(HorizontalSectionError, match="no_captured_points"):
        _extract(geometry, 0.5, 0.0)
    with pytest.raises(HorizontalSectionError, match="out_of_range"):
        _extract(geometry, -0.01)
    with pytest.raises(HorizontalSectionError, match="finite"):
        _extract(geometry, math.nan)
    with pytest.raises(HorizontalSectionError, match="geometry_empty"):
        _extract(_geometry(()), 0.0)


def test_ordering_and_serialization_are_deterministic() -> None:
    geometry = _geometry(((2, 0, 1.0), (0, 0, 1.0), (1, 0, 1.0), (0, 0, 0.0), (0, 0, 2.0)))
    first = _extract(geometry, 1.0)
    second = _extract(geometry, 1.0)
    assert first.section_id == second.section_id
    assert [item.point for item in first.points] == [
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 1.0),
        (2.0, 0.0, 1.0),
    ]
    assert serialize_horizontal_section(first) == serialize_horizontal_section(second)
    assert first.as_dict()["points"][0]["source_point_index"] == 1


@pytest.mark.parametrize(
    ("state", "unit"),
    [
        (ScaleState.RELATIVE, "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ],
)
def test_section_preserves_scale_state_units(state, unit) -> None:
    geometry = _geometry(_box_points(), state=state)
    section = _extract(geometry, 0.0)
    assert section.coordinate_unit == unit
    assert section.as_dict()["physical_accuracy_claimed"] is False


def test_stale_geometry_normalization_and_scale_provenance_are_rejected() -> None:
    geometry = _geometry(_box_points(), state=ScaleState.METRIC_UNVERIFIED)
    with pytest.raises(HorizontalSectionError, match="scale_provenance_parent_stale"):
        _extract(geometry, 0.0, scale_id="scale-r2")
    with pytest.raises(HorizontalSectionError, match="normalized_geometry_parent_stale"):
        extract_horizontal_section(
            geometry,
            0.0,
            slab_half_width=0.0,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision="normalized-r2",
            current_scale_provenance_id=geometry.scale_provenance_id,
        )
