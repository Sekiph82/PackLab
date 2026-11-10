from __future__ import annotations

import pytest

from packlab_core.multi_ring_capture_recipe import (
    MultiRingCaptureRecipe,
    MultiRingCaptureRecipeError,
)


def test_schedule_is_deterministic_ordered_and_marks_angles_as_planned() -> None:
    recipe = MultiRingCaptureRecipe.create((0.1, 0.5, 0.9), 8, starting_angle_degrees=10.0)
    repeated = MultiRingCaptureRecipe.create((0.1, 0.5, 0.9), 8, starting_angle_degrees=370.0)

    assert recipe == repeated
    assert recipe.pose_count == 24
    poses = recipe.schedule()
    assert poses == repeated.schedule()
    assert [pose.ordinal for pose in poses] == list(range(24))
    assert len({pose.pose_id for pose in poses}) == 24
    assert poses[0].object_height_fraction == 0.1
    assert poses[8].object_height_fraction == 0.5
    assert poses[0].planned_azimuth_degrees == 10.0
    assert poses[8].planned_azimuth_degrees == 32.5
    assert all(pose.as_dict()["angle_status"] == "PLANNED_NOT_OBSERVED" for pose in poses)


def test_serialization_never_claims_capture_calibration_or_hardware_control() -> None:
    recipe = MultiRingCaptureRecipe.create((0.2, 0.8), 6)
    payload = recipe.as_dict()
    assert payload["authority_class"] == "PLANNED_CAPTURE_RECIPE"
    assert payload["physical_angles_observed"] is False
    assert payload["capture_performed"] is False
    assert payload["calibration_performed"] is False
    assert payload["hardware_control_performed"] is False
    assert payload["scan_master_replaced"] is False
    assert "path" not in str(payload) and "image_bytes" not in str(payload)


@pytest.mark.parametrize(
    ("fractions", "count", "message"),
    [
        ((0.1, 0.1), 8, "ring_elevations_not_strictly_increasing"),
        ((-0.1, 0.5), 8, "ring_elevation_fraction_invalid"),
        ((0.1, 0.5), 2, "azimuth_count_out_of_bounds"),
        ((0.0,) * 33, 3, "ring_count_out_of_bounds"),
        ((i / 32 for i in range(32)), 17, "total_pose_count_exceeds_limit"),
    ],
)
def test_invalid_or_oversized_recipes_reject(fractions, count, message) -> None:
    if not isinstance(fractions, tuple):
        fractions = tuple(fractions)
    with pytest.raises(MultiRingCaptureRecipeError, match=message):
        MultiRingCaptureRecipe.create(fractions, count)


def test_nonfinite_start_angle_rejects() -> None:
    with pytest.raises((MultiRingCaptureRecipeError, ValueError, OverflowError)):
        MultiRingCaptureRecipe.create((0.5,), 8, starting_angle_degrees=float("nan"))


@pytest.mark.parametrize("angle", [True, "10", None])
def test_start_angle_rejects_bool_and_coercible_non_numeric_values(angle) -> None:
    with pytest.raises(MultiRingCaptureRecipeError, match="starting_angle_invalid"):
        MultiRingCaptureRecipe.create((0.5,), 8, starting_angle_degrees=angle)
