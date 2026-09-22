"""Boundary tests for deterministic calibration confidence gates."""

from __future__ import annotations

from packlab_core.calibration import ScaleEstimate, score_calibration_confidence


def _estimate(
    marker_count: int,
    *,
    residual: float,
    edge_spread: float,
    status: str = "estimated",
) -> ScaleEstimate:
    return ScaleEstimate(
        status=status,
        mm_per_pixel=0.4 if status == "estimated" else None,
        pixels_per_mm=2.5 if status == "estimated" else None,
        uncertainty_mm_per_pixel=0.0 if status == "estimated" else None,
        samples_used=tuple(range(marker_count)),
        samples_rejected=(),
        residuals=tuple(
            {
                "marker_id": marker_id,
                "sample_mm_per_pixel": 0.4,
                "residual_mm_per_pixel": 0.0,
                "relative_residual": residual,
                "relative_edge_spread": edge_spread,
            }
            for marker_id in range(marker_count)
        ),
        provenance={"math_version": "test"},
        errors=() if status == "estimated" else ("inconsistent_marker_scale",),
    )


def test_exact_accepted_threshold_is_accepted() -> None:
    result = score_calibration_confidence(_estimate(4, residual=0.025, edge_spread=0.0))
    assert result.status == "accepted"
    assert result.score == 0.8
    assert result.usable_for_capture is True
    assert result.thresholds["accepted_min_score"] == 0.8


def test_just_below_accepted_threshold_warns() -> None:
    result = score_calibration_confidence(_estimate(4, residual=0.0252, edge_spread=0.0))
    assert result.status == "warning"
    assert result.score < result.thresholds["accepted_min_score"]
    assert result.usable_for_capture is True


def test_exact_warning_threshold_warns() -> None:
    result = score_calibration_confidence(_estimate(4, residual=0.05, edge_spread=0.0))
    assert result.status == "warning"
    assert result.score == 0.6
    assert result.usable_for_capture is True
    assert result.thresholds["reject_below_score"] == result.thresholds["warning_min_score"]


def test_just_below_warning_threshold_fails_closed() -> None:
    result = score_calibration_confidence(_estimate(4, residual=0.05, edge_spread=0.0006))
    assert result.status == "rejected"
    assert result.score < result.thresholds["warning_min_score"]
    assert result.usable_for_capture is False


def test_rejected_scale_estimate_fails_closed_without_capture_use() -> None:
    result = score_calibration_confidence(
        _estimate(2, residual=0.0, edge_spread=0.0, status="rejected")
    )
    assert result.status == "rejected"
    assert result.score == 0.0
    assert result.usable_for_capture is False
    assert "scale_estimate_not_usable" in result.reasons


def test_missing_geometry_spread_is_adversarial_and_rejected() -> None:
    estimate = ScaleEstimate(
        "estimated",
        0.4,
        2.5,
        0.0,
        (0, 1, 2, 3),
        (),
        (
            {
                "marker_id": 0,
                "sample_mm_per_pixel": 0.4,
                "residual_mm_per_pixel": 0.0,
                "relative_residual": 0.0,
            },
        ),
        {"math_version": "test"},
        (),
    )
    result = score_calibration_confidence(estimate)
    assert result.status == "rejected"
    assert result.factors == {}
    assert result.reasons == ("confidence_metrics_missing_or_malformed",)


def test_actual_scale_estimator_emits_confidence_spread_factor() -> None:
    from packlab_core.calibration import KnownMarkerObservation, estimate_scale

    estimate = estimate_scale(
        [
            KnownMarkerObservation(0, ((0, 0), (100, 0), (100, 100), (0, 100)), 40, 0.1, 1.0),
            KnownMarkerObservation(1, ((0, 0), (100, 0), (100, 100), (0, 100)), 40, 0.1, 1.0),
        ]
    )
    result = score_calibration_confidence(estimate)
    assert result.status == "accepted"
    assert result.factors["max_relative_edge_spread"] == 0.0
