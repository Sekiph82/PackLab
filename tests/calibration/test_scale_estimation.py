"""Synthetic ground-truth tests for scale estimation."""

from __future__ import annotations

from packlab_core.calibration import KnownMarkerObservation, estimate_scale


def _sample(
    marker_id: int,
    side_mm: float,
    pixel_side: float,
    *,
    accepted: bool = True,
    quality: float = 1.0,
) -> KnownMarkerObservation:
    return KnownMarkerObservation(
        marker_id,
        ((0, 0), (pixel_side, 0), (pixel_side, pixel_side), (0, pixel_side)),
        side_mm,
        0.1,
        quality,
        accepted,
    )


def _sample_with_corners(
    marker_id: int,
    corners: tuple[
        tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]
    ],
    *,
    side_mm: float = 40,
) -> KnownMarkerObservation:
    return KnownMarkerObservation(marker_id, corners, side_mm, 0.1, 1.0, True)


def test_exact_two_marker_ground_truth_returns_mm_per_pixel() -> None:
    result = estimate_scale([_sample(0, 40, 100), _sample(1, 80, 200)])
    assert result.status == "estimated"
    assert result.mm_per_pixel == 0.4
    assert result.pixels_per_mm == 2.5
    assert result.samples_used == (0, 1)
    assert result.provenance["real_world_unit"] == "mm"


def test_noisy_samples_report_residuals_and_remain_consistent() -> None:
    result = estimate_scale([_sample(0, 40, 100), _sample(1, 40, 101), _sample(2, 80, 199)])
    assert result.status == "estimated"
    assert result.mm_per_pixel is not None
    assert len(result.residuals) == 3
    assert all("relative_residual" in sample for sample in result.residuals)


def test_inconsistent_marker_size_evidence_is_rejected() -> None:
    result = estimate_scale([_sample(0, 40, 100), _sample(1, 50, 100)])
    assert result.status == "rejected"
    assert result.mm_per_pixel is None
    assert result.errors == ("inconsistent_marker_scale",)
    assert len(result.residuals) == 2


def test_insufficient_and_unaccepted_observations_are_rejected() -> None:
    insufficient = estimate_scale([_sample(0, 40, 100)])
    assert insufficient.errors == ("insufficient_accepted_observations",)
    unaccepted = estimate_scale([_sample(0, 40, 100, accepted=False), _sample(1, 40, 100)])
    assert unaccepted.errors == ("insufficient_accepted_observations",)
    assert unaccepted.samples_rejected == ("0:not_accepted",)


def test_degenerate_geometry_is_rejected_without_scale() -> None:
    result = estimate_scale([_sample(0, 40, 0), _sample(1, 40, 100)])
    assert result.status == "rejected"
    assert result.mm_per_pixel is None
    assert result.samples_rejected == ("0:invalid_geometry_or_quality",)


def test_collinear_four_corner_geometry_is_rejected() -> None:
    result = estimate_scale(
        [
            _sample_with_corners(0, ((0, 0), (50, 0), (100, 0), (150, 0))),
            _sample(1, 40, 100),
        ]
    )
    assert result.status == "rejected"
    assert result.samples_rejected == ("0:invalid_geometry_or_quality",)
    assert result.errors == ("insufficient_accepted_observations",)


def test_bow_tie_corner_order_is_rejected() -> None:
    result = estimate_scale(
        [
            _sample_with_corners(0, ((0, 0), (100, 100), (0, 100), (100, 0))),
            _sample(1, 40, 100),
        ]
    )
    assert result.status == "rejected"
    assert result.samples_rejected == ("0:invalid_geometry_or_quality",)
    assert result.errors == ("insufficient_accepted_observations",)


def test_near_zero_area_quadrilateral_is_rejected() -> None:
    result = estimate_scale(
        [
            _sample_with_corners(0, ((0, 0), (100, 0), (100, 0.000000001), (0, 0.000000001))),
            _sample(1, 40, 100),
        ]
    )
    assert result.status == "rejected"
    assert result.samples_rejected == ("0:invalid_geometry_or_quality",)
    assert result.errors == ("insufficient_accepted_observations",)


def test_valid_perspective_distorted_convex_quadrilateral_is_accepted() -> None:
    corners = ((0, 0), (120, 10), (110, 105), (10, 100))
    result = estimate_scale([_sample_with_corners(0, corners), _sample_with_corners(1, corners)])
    assert result.status == "estimated"
    assert result.mm_per_pixel is not None
    assert result.samples_used == (0, 1)
    assert result.samples_rejected == ()
