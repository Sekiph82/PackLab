from __future__ import annotations

import pytest

from packlab_core.cross_section import (
    CrossSectionError,
    CrossSectionSymmetry,
    SectionPoint,
    circle_section,
    create_cross_section,
    edit_control_point,
    ellipse_section,
    set_symmetry,
)
from packlab_core.reconstruction import ScaleState


def _asymmetric_section():
    return create_cross_section(
        "container",
        (
            SectionPoint(-2.0, -1.0),
            SectionPoint(2.0, -1.0),
            SectionPoint(1.0, 2.0),
            SectionPoint(-2.0, 1.0),
        ),
        symmetry=CrossSectionSymmetry.NONE,
        scale_state=ScaleState.RELATIVE,
    )


def test_circle_ellipse_and_general_section_are_deterministic_and_units_propagate() -> None:
    circle = circle_section("container", 10.0, point_count=32)
    ellipse = ellipse_section("container", 10.0, 5.0, point_count=32)
    general = _asymmetric_section()
    assert circle.section_id == circle_section("container", 10.0, point_count=32).section_id
    assert len(circle.points) == len(ellipse.points) == 32
    assert general.coordinate_unit == "reconstruction_units"
    assert circle.coordinate_unit == ellipse.coordinate_unit == "mm_unverified"
    assert general.as_dict() == _asymmetric_section().as_dict()
    assert general.as_dict()["mold_use_authorized"] is False


@pytest.mark.parametrize(
    "symmetry",
    [
        CrossSectionSymmetry.LEFT_RIGHT,
        CrossSectionSymmetry.FRONT_BACK,
        CrossSectionSymmetry.BOTH,
    ],
)
def test_symmetry_constraint_propagates_mirrored_edits(symmetry: CrossSectionSymmetry) -> None:
    section = set_symmetry(circle_section("container", 5.0), symmetry)
    edited = edit_control_point(section, 1, SectionPoint(3.4, 3.6))
    assert edited.previous_section_id == section.section_id
    assert edited.section_id != section.section_id
    if symmetry in {CrossSectionSymmetry.LEFT_RIGHT, CrossSectionSymmetry.BOTH}:
        assert SectionPoint(-3.4, 3.6) in edited.points
    if symmetry in {CrossSectionSymmetry.FRONT_BACK, CrossSectionSymmetry.BOTH}:
        assert SectionPoint(3.4, -3.6) in edited.points
    assert edited.symmetry is symmetry


def test_asymmetric_mode_preserves_asymmetry_and_rejects_invalid_constraint_activation() -> None:
    section = _asymmetric_section()
    changed = edit_control_point(section, 0, SectionPoint(-3.0, -1.0))
    assert changed.points[0] == SectionPoint(-3.0, -1.0)
    assert changed.points[1:] == section.points[1:]
    with pytest.raises(CrossSectionError, match="section_symmetry_constraint_not_satisfied"):
        set_symmetry(changed, CrossSectionSymmetry.BOTH)


def test_degenerate_duplicate_and_self_intersecting_sections_are_rejected() -> None:
    with pytest.raises(CrossSectionError, match="section_duplicate_or_degenerate_edge"):
        create_cross_section(
            "container",
            (SectionPoint(0, 0), SectionPoint(1, 0), SectionPoint(1, 0)),
        )
    with pytest.raises(CrossSectionError, match="section_area_degenerate"):
        create_cross_section(
            "container",
            (SectionPoint(0, 0), SectionPoint(1, 0), SectionPoint(2, 0)),
        )
    with pytest.raises(CrossSectionError, match="section_self_intersection"):
        create_cross_section(
            "container",
            (
                SectionPoint(0, 0),
                SectionPoint(3, 3),
                SectionPoint(0, 3),
                SectionPoint(2, 0),
            ),
        )


def test_invalid_edit_and_unauthorized_units_fail_closed() -> None:
    with pytest.raises(CrossSectionError, match="section_radii_must_be_positive"):
        circle_section("container", 0.0)
    with pytest.raises(CrossSectionError, match="ellipse_point_count_must_be_multiple_of_four"):
        ellipse_section("container", 3.0, 2.0, point_count=10)
    with pytest.raises(CrossSectionError, match="section_point_index_invalid"):
        edit_control_point(_asymmetric_section(), 99, SectionPoint(0, 0))
    with pytest.raises(CrossSectionError, match="section_scale_state_unauthorized"):
        create_cross_section(
            "container",
            (SectionPoint(0, 0), SectionPoint(1, 0), SectionPoint(0, 1)),
            scale_state=ScaleState.METRIC_VERIFIED,
        )
