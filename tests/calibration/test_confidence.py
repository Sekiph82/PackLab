"""Boundary tests for deterministic calibration confidence gates."""

from __future__ import annotations

from packlab_core.calibration import ScaleEstimate, score_calibration_confidence

EPSILON = 0.000001


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


def test_accepted_score_boundary_immediate_below_exact_above() -> None:
    above = score_calibration_confidence(_estimate(4, residual=0.025 - EPSILON, edge_spread=0.0))
    exact = score_calibration_confidence(_estimate(4, residual=0.025, edge_spread=0.0))
    below = score_calibration_confidence(_estimate(4, residual=0.025 + EPSILON, edge_spread=0.0))

    assert above.score > above.thresholds["accepted_min_score"]
    assert above.status == "accepted"
    assert exact.score == exact.thresholds["accepted_min_score"] == 0.8
    assert exact.status == "accepted"
    assert below.score < below.thresholds["accepted_min_score"]
    assert below.status == "warning"


def test_exact_warning_threshold_warns() -> None:
    result = score_calibration_confidence(_estimate(4, residual=0.05, edge_spread=0.0))
    assert result.status == "warning"
    assert result.score == 0.6
    assert result.usable_for_capture is True
    assert result.thresholds["reject_below_score"] == result.thresholds["warning_min_score"]


def test_warning_score_boundary_immediate_below_exact_above() -> None:
    above = score_calibration_confidence(_estimate(4, residual=0.05 - EPSILON, edge_spread=0.0))
    exact = score_calibration_confidence(_estimate(4, residual=0.05, edge_spread=0.0))
    below = score_calibration_confidence(_estimate(4, residual=0.05, edge_spread=EPSILON))

    assert above.score > above.thresholds["warning_min_score"]
    assert above.status == "warning"
    assert exact.score == exact.thresholds["warning_min_score"] == 0.6
    assert exact.status == "warning"
    assert below.score < below.thresholds["warning_min_score"]
    assert below.status == "rejected"
    assert below.usable_for_capture is False


def test_residual_hard_gate_boundary_immediate_below_exact_above() -> None:
    below = score_calibration_confidence(_estimate(4, residual=0.05 - EPSILON, edge_spread=0.0))
    exact = score_calibration_confidence(_estimate(4, residual=0.05, edge_spread=0.0))
    above = score_calibration_confidence(_estimate(4, residual=0.05 + EPSILON, edge_spread=0.0))

    assert below.status == "warning"
    assert below.factors["max_relative_residual"] < below.thresholds["max_relative_residual"]
    assert exact.status == "warning"
    assert exact.factors["max_relative_residual"] == exact.thresholds["max_relative_residual"]
    assert above.status == "rejected"
    assert above.score == 0.0
    assert above.reasons == ("max_relative_residual_above_hard_gate",)
    assert above.usable_for_capture is False


def test_edge_spread_hard_gate_boundary_immediate_below_exact_above() -> None:
    below = score_calibration_confidence(_estimate(4, residual=0.0, edge_spread=0.03 - EPSILON))
    exact = score_calibration_confidence(_estimate(4, residual=0.0, edge_spread=0.03))
    above = score_calibration_confidence(_estimate(4, residual=0.0, edge_spread=0.03 + EPSILON))

    assert below.status == "warning"
    assert below.factors["max_relative_edge_spread"] < below.thresholds["max_relative_edge_spread"]
    assert exact.status == "warning"
    assert exact.factors["max_relative_edge_spread"] == exact.thresholds["max_relative_edge_spread"]
    assert above.status == "rejected"
    assert above.score == 0.0
    assert above.reasons == ("max_relative_edge_spread_above_hard_gate",)
    assert above.usable_for_capture is False


def test_marker_count_full_credit_boundary_immediate_below_exact_above() -> None:
    below = score_calibration_confidence(_estimate(3, residual=0.0, edge_spread=0.0))
    exact = score_calibration_confidence(_estimate(4, residual=0.0, edge_spread=0.0))
    above = score_calibration_confidence(_estimate(5, residual=0.0, edge_spread=0.0))

    assert below.factors["count_factor"] == 0.75
    assert below.score == 0.9125
    assert exact.factors["count_factor"] == 1.0
    assert exact.score == 1.0
    assert above.factors["count_factor"] == 1.0
    assert above.score == 1.0


def test_adversarial_above_residual_gate_fails_even_with_strong_other_factors() -> None:
    result = score_calibration_confidence(_estimate(8, residual=0.05 + EPSILON, edge_spread=0.0))
    assert result.status == "rejected"
    assert result.score == 0.0
    assert result.usable_for_capture is False
    assert result.reasons == ("max_relative_residual_above_hard_gate",)


def test_adversarial_above_edge_spread_gate_fails_even_with_strong_other_factors() -> None:
    result = score_calibration_confidence(_estimate(8, residual=0.0, edge_spread=0.03 + EPSILON))
    assert result.status == "rejected"
    assert result.score == 0.0
    assert result.usable_for_capture is False
    assert result.reasons == ("max_relative_edge_spread_above_hard_gate",)


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
