"""Deterministic confidence gates for calibration scale estimates."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .scale_estimation import MAX_RELATIVE_RESIDUAL, ScaleEstimate

CONFIDENCE_VERSION = "scale_confidence_count_residual_spread_v1"
MAX_RELATIVE_EDGE_SPREAD = 0.03
ACCEPTED_MIN_SCORE = 0.80
WARNING_MIN_SCORE = 0.60
COUNT_FULL_CREDIT = 4


@dataclass(frozen=True)
class CalibrationConfidence:
    """Dimensionless confidence result for an already-estimated calibration scale."""

    status: str
    score: float
    usable_for_capture: bool
    factors: dict[str, float]
    thresholds: dict[str, float]
    provenance: dict[str, str]
    reasons: tuple[str, ...]


def score_calibration_confidence(estimate: ScaleEstimate) -> CalibrationConfidence:
    """Score calibration confidence and fail closed when the estimate is not usable."""

    thresholds = _thresholds()
    provenance = {
        "confidence_version": CONFIDENCE_VERSION,
        "score_unit": "dimensionless_0_to_1",
        "residual_unit": "relative_fraction",
        "edge_spread_unit": "relative_fraction",
        "threshold_basis": "provisional_synthetic_consistency_gate_not_physical_accuracy",
    }
    if estimate.status != "estimated" or estimate.mm_per_pixel is None:
        return CalibrationConfidence(
            "rejected",
            0.0,
            False,
            {},
            thresholds,
            provenance,
            ("scale_estimate_not_usable", *estimate.errors),
        )

    marker_count = len(estimate.samples_used)
    if not _has_required_metrics(estimate, marker_count):
        return CalibrationConfidence(
            "rejected",
            0.0,
            False,
            {},
            thresholds,
            provenance,
            ("confidence_metrics_missing_or_malformed",),
        )

    max_relative_residual = _max_metric(estimate, "relative_residual")
    max_relative_edge_spread = _max_metric(estimate, "relative_edge_spread")
    hard_gate_reasons = _hard_gate_reasons(max_relative_residual, max_relative_edge_spread)
    count_factor = min(marker_count / COUNT_FULL_CREDIT, 1.0)
    residual_factor = _inverse_linear(max_relative_residual, MAX_RELATIVE_RESIDUAL)
    spread_factor = _inverse_linear(max_relative_edge_spread, MAX_RELATIVE_EDGE_SPREAD)
    factors = {
        "marker_count": float(marker_count),
        "count_factor": count_factor,
        "max_relative_residual": max_relative_residual,
        "residual_factor": residual_factor,
        "max_relative_edge_spread": max_relative_edge_spread,
        "spread_factor": spread_factor,
    }
    if hard_gate_reasons:
        return CalibrationConfidence(
            "rejected",
            0.0,
            False,
            factors,
            thresholds,
            provenance,
            hard_gate_reasons,
        )
    raw_score = (0.35 * count_factor) + (0.40 * residual_factor) + (0.25 * spread_factor)
    score = _round_score(raw_score)
    if score >= ACCEPTED_MIN_SCORE:
        status = "accepted"
        usable = True
    elif score >= WARNING_MIN_SCORE:
        status = "warning"
        usable = True
    else:
        status = "rejected"
        usable = False
    return CalibrationConfidence(
        status,
        score,
        usable,
        factors,
        thresholds,
        provenance,
        _reasons(status, score),
    )


def _has_required_metrics(estimate: ScaleEstimate, marker_count: int) -> bool:
    if marker_count == 0 or len(estimate.residuals) != marker_count:
        return False
    for item in estimate.residuals:
        for key in ("relative_residual", "relative_edge_spread"):
            if key not in item:
                return False
            value = item[key]
            if not isinstance(value, int | float) or not math.isfinite(float(value)):
                return False
    return True


def _max_metric(estimate: ScaleEstimate, key: str) -> float:
    values = [
        float(item[key])
        for item in estimate.residuals
        if key in item and isinstance(item[key], int | float) and math.isfinite(float(item[key]))
    ]
    return max(values, default=1.0)


def _inverse_linear(value: float, reject_at: float) -> float:
    if not math.isfinite(value) or reject_at <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - (value / reject_at)))


def _hard_gate_reasons(
    max_relative_residual: float, max_relative_edge_spread: float
) -> tuple[str, ...]:
    reasons: list[str] = []
    if max_relative_residual > MAX_RELATIVE_RESIDUAL:
        reasons.append("max_relative_residual_above_hard_gate")
    if max_relative_edge_spread > MAX_RELATIVE_EDGE_SPREAD:
        reasons.append("max_relative_edge_spread_above_hard_gate")
    return tuple(reasons)


def _round_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _thresholds() -> dict[str, float]:
    return {
        "accepted_min_score": ACCEPTED_MIN_SCORE,
        "warning_min_score": WARNING_MIN_SCORE,
        "reject_below_score": WARNING_MIN_SCORE,
        "max_relative_residual": MAX_RELATIVE_RESIDUAL,
        "max_relative_edge_spread": MAX_RELATIVE_EDGE_SPREAD,
        "count_full_credit_markers": float(COUNT_FULL_CREDIT),
    }


def _reasons(status: str, score: float) -> tuple[str, ...]:
    if status == "accepted":
        return ("score_at_or_above_accepted_threshold",)
    if status == "warning":
        return ("score_at_or_above_warning_threshold_below_accepted_threshold",)
    return (f"score_{score}_below_warning_threshold_fail_closed",)
