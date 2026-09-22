"""Millimetre scale estimation from accepted known-marker observations."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

MIN_ACCEPTED_SAMPLES = 2
MAX_RELATIVE_RESIDUAL = 0.05
MATH_VERSION = "mean_marker_edge_mm_per_pixel_weighted_v1"


@dataclass(frozen=True)
class KnownMarkerObservation:
    """A valid marker observation joined to known millimetre geometry."""

    marker_id: int
    corners_px: tuple[
        tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]
    ]
    side_length_mm: float
    uncertainty_mm: float
    quality_score: float
    accepted: bool = True
    provenance: str = "synthetic_or_operator_geometry_record"


@dataclass(frozen=True)
class ScaleEstimate:
    """Structured scale result; no result is returned as usable after rejection."""

    status: str
    mm_per_pixel: float | None
    pixels_per_mm: float | None
    uncertainty_mm_per_pixel: float | None
    samples_used: tuple[int, ...]
    samples_rejected: tuple[str, ...]
    residuals: tuple[dict[str, float | int], ...]
    provenance: dict[str, str]
    errors: tuple[str, ...]


def estimate_scale(observations: Iterable[KnownMarkerObservation]) -> ScaleEstimate:
    """Estimate mm/pixel using only accepted, valid known-marker observations."""

    candidates = list(observations)
    rejected: list[str] = []
    samples: list[tuple[KnownMarkerObservation, float, float]] = []
    for observation in candidates:
        if not observation.accepted:
            rejected.append(f"{observation.marker_id}:not_accepted")
            continue
        if not _valid_observation(observation):
            rejected.append(f"{observation.marker_id}:invalid_geometry_or_quality")
            continue
        edges = _edge_lengths(observation.corners_px)
        mean_edge = sum(edges) / 4.0
        edge_spread = max(edges) - min(edges)
        sample_scale = observation.side_length_mm / mean_edge
        relative_uncertainty = math.sqrt(
            (observation.uncertainty_mm / observation.side_length_mm) ** 2
            + (edge_spread / mean_edge) ** 2
        )
        sigma = max(
            sample_scale * max(relative_uncertainty, 0.001) / observation.quality_score, 1e-9
        )
        samples.append((observation, sample_scale, sigma))

    if len(samples) < MIN_ACCEPTED_SAMPLES:
        return _rejected(samples, rejected, "insufficient_accepted_observations")
    weights = [1.0 / (sigma * sigma) for _, _, sigma in samples]
    total_weight = sum(weights)
    estimate = (
        sum(weight * sample for weight, (_, sample, _) in zip(weights, samples, strict=True))
        / total_weight
    )
    residuals = tuple(
        {
            "marker_id": observation.marker_id,
            "sample_mm_per_pixel": sample,
            "residual_mm_per_pixel": sample - estimate,
            "relative_residual": abs(sample - estimate) / estimate,
        }
        for observation, sample, _ in samples
    )
    max_residual = max(float(item["relative_residual"]) for item in residuals)
    if max_residual > MAX_RELATIVE_RESIDUAL:
        return _rejected(samples, rejected, "inconsistent_marker_scale", residuals)
    variance = (
        sum(
            weight * (sample - estimate) ** 2
            for weight, (_, sample, _) in zip(weights, samples, strict=True)
        )
        / total_weight
    )
    uncertainty = math.sqrt(variance + 1.0 / total_weight)
    return ScaleEstimate(
        "estimated",
        estimate,
        1.0 / estimate,
        uncertainty,
        tuple(observation.marker_id for observation, _, _ in samples),
        tuple(rejected),
        residuals,
        _provenance(),
        (),
    )


def _valid_observation(observation: KnownMarkerObservation) -> bool:
    if not all(
        math.isfinite(value)
        for value in (
            observation.side_length_mm,
            observation.uncertainty_mm,
            observation.quality_score,
        )
    ):
        return False
    if (
        observation.side_length_mm <= 0
        or observation.uncertainty_mm < 0
        or not 0 < observation.quality_score <= 1
    ):
        return False
    try:
        edges = _edge_lengths(observation.corners_px)
    except (TypeError, ValueError):
        return False
    return all(math.isfinite(edge) and edge > 0 for edge in edges)


def _edge_lengths(corners: tuple[tuple[float, float], ...]) -> tuple[float, float, float, float]:
    if len(corners) != 4:
        raise ValueError("four corners required")
    return tuple(
        math.hypot(
            corners[(index + 1) % 4][0] - corners[index][0],
            corners[(index + 1) % 4][1] - corners[index][1],
        )
        for index in range(4)
    )  # type: ignore[return-value]


def _rejected(
    samples: list[tuple[KnownMarkerObservation, float, float]],
    rejected: list[str],
    error: str,
    residuals: tuple[dict[str, float | int], ...] = (),
) -> ScaleEstimate:
    return ScaleEstimate(
        "rejected",
        None,
        None,
        None,
        tuple(observation.marker_id for observation, _, _ in samples),
        tuple(rejected),
        residuals,
        _provenance(),
        (error,),
    )


def _provenance() -> dict[str, str]:
    return {
        "math_version": MATH_VERSION,
        "real_world_unit": "mm",
        "pixel_unit": "image_pixels",
        "corner_convention": "ordered_clockwise_from_top_left",
    }
