"""Fail-closed, provenance-aware metric comparison for packaging benchmarks.

Ranges attached to generated samples are software scenario bounds only. They
do not establish physical measurement accuracy, verified metric scale, or
manufacturing acceptance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


class MetricOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class MetricBand:
    key: str
    lower: float
    upper: float
    unit: str
    provenance: str
    authority: str

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("metric key must be a non-empty string")
        if type(self.lower) not in (int, float) or not math.isfinite(self.lower):
            raise ValueError("metric lower bound must be finite")
        if type(self.upper) not in (int, float) or not math.isfinite(self.upper):
            raise ValueError("metric upper bound must be finite")
        if self.lower > self.upper:
            raise ValueError("metric lower bound must not exceed upper bound")
        if not isinstance(self.unit, str) or not self.unit:
            raise ValueError("metric unit must be explicit")
        if not isinstance(self.provenance, str) or not self.provenance:
            raise ValueError("metric provenance must be explicit")
        if not isinstance(self.authority, str) or not self.authority:
            raise ValueError("metric authority must be explicit")


@dataclass(frozen=True, slots=True)
class MetricResult:
    key: str
    observed: float
    lower: float
    upper: float
    unit: str
    outcome: MetricOutcome
    provenance: str
    authority: str


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    outcome: MetricOutcome
    results: tuple[MetricResult, ...]


def compare_metric_bands(
    expected: Mapping[str, MetricBand], observed: Mapping[str, object]
) -> BenchmarkComparison:
    """Compare an exact metric set to inclusive finite bands.

    Missing, unexpected, boolean, string, NaN and infinite values fail closed.
    Provenance and measurement authority follow each metric into the result.
    """
    if not isinstance(expected, Mapping) or not expected:
        raise ValueError("expected metrics must be a non-empty mapping")
    if not isinstance(observed, Mapping):
        raise ValueError("observed metrics must be a mapping")
    if set(expected) != set(observed):
        missing = sorted(set(expected) - set(observed))
        extra = sorted(set(observed) - set(expected))
        raise ValueError(f"metric set mismatch (missing={missing}, extra={extra})")

    results = []
    for key in sorted(expected):
        band = expected[key]
        if not isinstance(band, MetricBand) or band.key != key:
            raise ValueError(f"invalid expected metric band: {key}")
        value = observed[key]
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"observed metric must be a finite real number: {key}")
        outcome = MetricOutcome.PASS if band.lower <= value <= band.upper else MetricOutcome.FAIL
        results.append(
            MetricResult(
                key=key,
                observed=float(value),
                lower=float(band.lower),
                upper=float(band.upper),
                unit=band.unit,
                outcome=outcome,
                provenance=band.provenance,
                authority=band.authority,
            )
        )
    final = MetricOutcome.PASS if all(result.outcome is MetricOutcome.PASS for result in results) else MetricOutcome.FAIL
    return BenchmarkComparison(final, tuple(results))


def synthetic_packaging_metric_bands(
    *,
    nominal_dimensions_mm: tuple[float, float, float],
    mesh_extent_mm: tuple[float, float, float],
    scenario_tolerances_mm: tuple[float, float],
) -> dict[str, MetricBand]:
    """Build software-only ranges from generator truth and existing mask gates."""
    if len(nominal_dimensions_mm) != 3 or len(mesh_extent_mm) != 3 or len(scenario_tolerances_mm) != 2:
        raise ValueError("synthetic dimensions require three axes and a two-value scenario tolerance")
    values = (*nominal_dimensions_mm, *mesh_extent_mm, *scenario_tolerances_mm)
    if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("synthetic dimensions and tolerances must be positive finite values")
    if scenario_tolerances_mm[0] > scenario_tolerances_mm[1]:
        raise ValueError("scenario tolerance bounds are reversed")

    common = {
        "provenance": "SYNTHETIC_GENERATOR_SCENARIO",
        "authority": "NONPHYSICAL_SOFTWARE_TEST_ONLY",
    }
    bands: dict[str, MetricBand] = {
        "segmentation_iou": MetricBand(
            "segmentation_iou", 0.80, 1.0, "ratio", **common
        ),
        "segmentation_dice": MetricBand(
            "segmentation_dice", 0.88, 1.0, "ratio", **common
        ),
    }
    tolerance = float(scenario_tolerances_mm[1])
    for axis, extent in zip("xyz", mesh_extent_mm, strict=True):
        for stage in ("reconstruction", "parametric_fit"):
            key = f"{stage}_extent_{axis}_mm"
            center = float(extent)
            bands[key] = MetricBand(
                key=key,
                lower=max(0.0, center - tolerance),
                upper=center + tolerance,
                unit="mm_simulated",
                **common,
            )
    return bands


def compare_synthetic_packaging_sample(
    sample: Mapping[str, object], observed: Mapping[str, object]
) -> BenchmarkComparison:
    """Compare software output with one sample's explicitly synthetic bands.

    Refuse real or authority-ambiguous samples so these scenario bounds cannot
    accidentally be presented as field or physical acceptance evidence.
    """
    if not isinstance(sample, Mapping) or sample.get("synthetic") is not True:
        raise ValueError("only explicitly synthetic benchmark samples are accepted")
    if sample.get("measurement_authority") != "synthetic generator inputs only; no physical or Kenya ground truth":
        raise ValueError("sample does not declare synthetic-only measurement authority")
    raw_bands = sample.get("expected_software_metric_bands")
    if not isinstance(raw_bands, Mapping) or not raw_bands:
        raise ValueError("sample has no expected software metric bands")
    bands: dict[str, MetricBand] = {}
    for key, record in raw_bands.items():
        if not isinstance(key, str) or not isinstance(record, Mapping):
            raise ValueError("invalid expected metric record")
        try:
            bands[key] = MetricBand(
                key=key,
                lower=record["lower"],
                upper=record["upper"],
                unit=record["unit"],
                provenance=record["provenance"],
                authority=record["authority"],
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(f"incomplete expected metric record: {key}") from exc
        if bands[key].provenance != "SYNTHETIC_GENERATOR_SCENARIO" or bands[key].authority != "NONPHYSICAL_SOFTWARE_TEST_ONLY":
            raise ValueError(f"metric authority is not explicitly synthetic: {key}")
    return compare_metric_bands(bands, observed)
