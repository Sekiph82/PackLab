"""Deterministic synthetic ground-truth coverage for calibration math."""

from __future__ import annotations

import math

from packlab_core.calibration import (
    CalibrationProfile,
    CalibrationProfileKey,
    CalibrationQualityEvidence,
    CaptureProfileRequest,
    KnownMarkerObservation,
    MarkerObservation,
    check_profile_compatibility,
    estimate_scale,
    score_calibration_confidence,
)

GENERATOR_VERSION = "synthetic_ground_truth_v1"
GROUND_TRUTH_SIDE_MM = 40.0
GROUND_TRUTH_MM_PER_PIXEL = 0.4
IDEAL_EDGE_PX = GROUND_TRUTH_SIDE_MM / GROUND_TRUTH_MM_PER_PIXEL


def _detected_marker(
    marker_id: int,
    *,
    pixel_side: float = IDEAL_EDGE_PX,
    x: float = 0.0,
    y: float = 0.0,
    scenario: str = "ideal",
    order: str = "clockwise_top_left",
    quality_score: float = 1.0,
) -> MarkerObservation:
    corners = (
        (x, y),
        (x + pixel_side, y),
        (x + pixel_side, y + pixel_side),
        (x, y + pixel_side),
    )
    if order == "diagonal_perturbed":
        corners = (corners[0], corners[2], corners[1], corners[3])
    return MarkerObservation(
        marker_id,
        corners,
        {
            "quality_score": quality_score,
            "quality_label": "synthetic_geometry",
            "ground_truth_side_mm": GROUND_TRUTH_SIDE_MM,
            "ground_truth_mm_per_pixel": GROUND_TRUTH_MM_PER_PIXEL,
        },
        {
            "generator": GENERATOR_VERSION,
            "scenario": scenario,
            "corner_order": order,
            "coordinate_unit": "image_pixels",
        },
    )


def _known(
    observation: MarkerObservation,
    *,
    side_mm: float = GROUND_TRUTH_SIDE_MM,
    accepted: bool = True,
) -> KnownMarkerObservation:
    quality_score = observation.quality["quality_score"]
    assert isinstance(quality_score, float)
    return KnownMarkerObservation(
        observation.marker_id,
        observation.corners_px,
        side_mm,
        0.1,
        quality_score,
        accepted,
        f"{GENERATOR_VERSION}:{observation.provenance['scenario']}",
    )


def _profile_key() -> CalibrationProfileKey:
    return CalibrationProfileKey(
        "iPhone 16 Standard",
        "main_wide_camera_1x",
        "back",
        4032,
        3024,
        "landscape_right",
        1.0,
        "locked",
        "0.1.0",
        "synthetic-calibration-model-v1",
        "synthetic-calibration-policy-v1",
    )


def test_ideal_synthetic_markers_recover_ground_truth_scale_confidence_and_profile() -> None:
    observations = [
        _known(_detected_marker(0, x=0, y=0)),
        _known(_detected_marker(1, x=150, y=0)),
        _known(_detected_marker(2, x=0, y=150)),
        _known(_detected_marker(3, x=150, y=150)),
    ]
    estimate = estimate_scale(observations)
    assert estimate.status == "estimated"
    assert estimate.mm_per_pixel == GROUND_TRUTH_MM_PER_PIXEL
    assert estimate.provenance["real_world_unit"] == "mm"
    confidence = score_calibration_confidence(estimate)
    assert confidence.status == "accepted"
    assert confidence.usable_for_capture is True

    profile = CalibrationProfile(
        "synthetic-profile-v1",
        "1.0.0",
        _profile_key(),
        "exact_reference_only",
        "2026-09-22T00:00:00Z",
        {"source": "synthetic_public_test"},
        CalibrationQualityEvidence(
            confidence.status, confidence.score, 0.0, 4, "2026-09-22T00:01:00Z"
        ),
        {
            "image_width": "px",
            "image_height": "px",
            "zoom_factor": "unitless",
            "reprojection_rmse": "px",
        },
    )
    compatibility = check_profile_compatibility(profile, CaptureProfileRequest(_profile_key()))
    assert compatibility.status == "compatible"
    assert compatibility.reusable is True


def test_noisy_synthetic_markers_stay_inside_explicit_error_bound() -> None:
    observations = [
        _known(_detected_marker(0, pixel_side=100.0, scenario="noisy")),
        _known(_detected_marker(1, pixel_side=100.4, scenario="noisy")),
        _known(_detected_marker(2, pixel_side=99.7, scenario="noisy")),
        _known(_detected_marker(3, pixel_side=100.2, scenario="noisy")),
    ]
    estimate = estimate_scale(observations)
    assert estimate.status == "estimated"
    assert estimate.mm_per_pixel is not None
    assert math.isclose(estimate.mm_per_pixel, GROUND_TRUTH_MM_PER_PIXEL, abs_tol=0.005)
    assert score_calibration_confidence(estimate).status in {"accepted", "warning"}


def test_partial_synthetic_set_uses_available_markers_and_records_rejection() -> None:
    observations = [
        _known(_detected_marker(0, scenario="partial"), accepted=False),
        _known(_detected_marker(1, scenario="partial")),
        _known(_detected_marker(2, scenario="partial")),
    ]
    estimate = estimate_scale(observations)
    assert estimate.status == "estimated"
    assert estimate.samples_used == (1, 2)
    assert estimate.samples_rejected == ("0:not_accepted",)


def test_degenerate_and_inconsistent_cases_fail_closed() -> None:
    degenerate = estimate_scale(
        [
            _known(_detected_marker(0, pixel_side=0.0, scenario="degenerate")),
            _known(_detected_marker(1, scenario="degenerate")),
        ]
    )
    assert degenerate.status == "rejected"
    assert degenerate.errors == ("insufficient_accepted_observations",)

    inconsistent = estimate_scale(
        [
            _known(_detected_marker(0, scenario="inconsistent")),
            _known(_detected_marker(1, pixel_side=70.0, scenario="inconsistent")),
        ]
    )
    assert inconsistent.status == "rejected"
    assert inconsistent.errors == ("inconsistent_marker_scale",)
    assert score_calibration_confidence(inconsistent).usable_for_capture is False


def test_unit_and_corner_order_sensitivity_are_bounded() -> None:
    wrong_units = estimate_scale(
        [
            _known(_detected_marker(0, scenario="wrong_units"), side_mm=400.0),
            _known(_detected_marker(1, scenario="wrong_units"), side_mm=400.0),
        ]
    )
    assert wrong_units.status == "estimated"
    assert wrong_units.mm_per_pixel is not None
    assert not math.isclose(wrong_units.mm_per_pixel, GROUND_TRUTH_MM_PER_PIXEL, abs_tol=0.005)

    bad_order = estimate_scale(
        [
            _known(_detected_marker(0, scenario="bad_order", order="diagonal_perturbed")),
            _known(_detected_marker(1, scenario="bad_order", order="diagonal_perturbed")),
        ]
    )
    assert bad_order.status == "rejected"
    assert bad_order.errors == ("insufficient_accepted_observations",)
    assert bad_order.samples_rejected == (
        "0:invalid_geometry_or_quality",
        "1:invalid_geometry_or_quality",
    )
    confidence = score_calibration_confidence(bad_order)
    assert confidence.status == "rejected"
    assert confidence.usable_for_capture is False


def test_synthetic_generation_provenance_is_recorded() -> None:
    marker = _detected_marker(7, scenario="provenance")
    assert marker.provenance == {
        "generator": GENERATOR_VERSION,
        "scenario": "provenance",
        "corner_order": "clockwise_top_left",
        "coordinate_unit": "image_pixels",
    }
    assert marker.quality["ground_truth_side_mm"] == GROUND_TRUTH_SIDE_MM
    assert marker.quality["ground_truth_mm_per_pixel"] == GROUND_TRUTH_MM_PER_PIXEL
