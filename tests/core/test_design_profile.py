from __future__ import annotations

import pytest

from packlab_core.design_profile import (
    DesignProfileError,
    ProfilePoint,
    create_design_profile,
)
from packlab_core.reconstruction import ScaleState


def test_linear_profile_interpolates_control_points_and_endpoints() -> None:
    profile = create_design_profile(
        (ProfilePoint(0.0, 2.0), ProfilePoint(10.0, 12.0)),
        ScaleState.METRIC_UNVERIFIED,
    )
    assert profile.evaluate_parameter(0.0).radius == 2.0
    assert profile.evaluate_parameter(1.0).radius == 12.0
    assert profile.evaluate(5.0).radius == 7.0
    assert profile.coordinate_unit == "mm_unverified"


def test_explicit_tangent_curve_is_deterministic_and_bounded() -> None:
    points = (ProfilePoint(0.0, 0.0, 0.0), ProfilePoint(1.0, 1.0, 0.0))
    profile = create_design_profile(points, ScaleState.RELATIVE)
    assert profile.evaluate_parameter(0.5).radius == 0.5
    assert profile.coordinate_unit == "reconstruction_units"
    assert profile.sample(5) == profile.sample(5)
    assert [item.parameter for item in profile.sample(5)] == [0, 0.25, 0.5, 0.75, 1]
    assert [item.radius for item in profile.sample(5)] == sorted(
        item.radius for item in profile.sample(5)
    )
    encoded = profile.as_dict()
    assert encoded["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert encoded["mold_use_authorized"] is False
    assert "verified" not in str(encoded["coordinate_unit"])
    with pytest.raises(DesignProfileError, match="profile_parameter_out_of_range"):
        profile.evaluate_parameter(1.01)
    with pytest.raises(DesignProfileError, match="profile_coordinate_out_of_range"):
        profile.evaluate(1.1)


@pytest.mark.parametrize(
    "points, error",
    [
        ((ProfilePoint(0.0, 1.0),), "profile_requires_two_control_points"),
        (
            (ProfilePoint(0.0, 1.0), ProfilePoint(0.0, 2.0)),
            "profile_axial_points_must_be_strictly_increasing",
        ),
        (
            (ProfilePoint(1.0, 1.0), ProfilePoint(0.0, 2.0)),
            "profile_axial_points_must_be_strictly_increasing",
        ),
    ],
)
def test_degenerate_and_duplicate_control_points_are_rejected(
    points: tuple[ProfilePoint, ...], error: str
) -> None:
    with pytest.raises(DesignProfileError, match=error):
        create_design_profile(points, ScaleState.RELATIVE)


def test_nonfinite_negative_or_unverified_as_verified_values_fail_closed() -> None:
    with pytest.raises(DesignProfileError, match="profile_coordinates_must_be_finite"):
        ProfilePoint(float("nan"), 1.0)
    with pytest.raises(DesignProfileError, match="profile_radius_must_be_nonnegative"):
        ProfilePoint(0.0, -1.0)
    profile = create_design_profile(
        (ProfilePoint(0.0, 1.0), ProfilePoint(1.0, 2.0)),
        ScaleState.METRIC_UNVERIFIED,
    )
    assert profile.as_dict()["coordinate_unit"] == "mm_unverified"
    assert profile.as_dict()["scale_state"] == "metric-unverified"
    with pytest.raises(DesignProfileError, match="profile_sample_count_out_of_range"):
        profile.sample(5000)
    with pytest.raises(DesignProfileError, match="profile_sample_count_invalid"):
        profile.sample(True)
