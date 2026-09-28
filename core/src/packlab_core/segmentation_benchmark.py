"""Deterministic, public-safe segmentation benchmark contracts for M08.

The harness evaluates small synthetic masks only.  It records evidence and
cannot select or install a model, runtime, checkpoint, or hosted service.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .segmentation import MaskRaster

BENCHMARK_CONTRACT_VERSION = "packlab.segmentation-benchmark.v1"
NO_SELECTION_LICENSE_OR_CHECKPOINT_BLOCKER = "NO_SELECTION_LICENSE_OR_CHECKPOINT_BLOCKER"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class SegmentationBenchmarkError(ValueError):
    """Raised when benchmark input or provenance is unsafe or incomplete."""


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SegmentationBenchmarkError(f"{field_name} must be non-empty text")
    return value


def _sha_or_state(value: str, field_name: str) -> str:
    _text(value, field_name)
    if value not in {"not-applicable", "not-reviewed"} and not _SHA256.fullmatch(value):
        raise SegmentationBenchmarkError(
            f"{field_name} must be SHA-256 or an explicit unavailable state"
        )
    return value


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class BenchmarkCandidate:
    candidate_id: str
    capabilities: tuple[str, ...]
    runtime: str
    license_record: str
    checkpoint_id: str
    checkpoint_sha256: str
    available: bool
    failure_modes: tuple[str, ...] = ()
    selection_status: str = "not-selected"

    def __post_init__(self) -> None:
        _text(self.candidate_id, "candidate_id")
        if not self.capabilities:
            raise SegmentationBenchmarkError("candidate must record at least one capability")
        _text(self.runtime, "runtime")
        _text(self.license_record, "license_record")
        _text(self.checkpoint_id, "checkpoint_id")
        _sha_or_state(self.checkpoint_sha256, "checkpoint_sha256")
        if not isinstance(self.available, bool):
            raise SegmentationBenchmarkError("available must be boolean")
        if self.available and (
            self.license_record in {"not-reviewed", "unresolved"}
            or self.checkpoint_sha256 == "not-reviewed"
        ):
            raise SegmentationBenchmarkError(
                "available candidate cannot have unresolved license/checkpoint facts"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "capabilities": list(self.capabilities),
            "runtime": self.runtime,
            "license_record": self.license_record,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_sha256": self.checkpoint_sha256,
            "available": self.available,
            "failure_modes": list(self.failure_modes),
            "selection_status": self.selection_status,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    packaging_class: str
    provenance: str
    ground_truth: MaskRaster
    predictions: Mapping[str, MaskRaster]

    def __post_init__(self) -> None:
        _text(self.case_id, "case_id")
        _text(self.packaging_class, "packaging_class")
        _text(self.provenance, "provenance")
        predictions = dict(self.predictions)
        for candidate_id, prediction in predictions.items():
            if (
                prediction.width != self.ground_truth.width
                or prediction.height != self.ground_truth.height
            ):
                raise SegmentationBenchmarkError(
                    f"prediction dimensions do not match case {self.case_id}: {candidate_id}"
                )
        object.__setattr__(self, "predictions", MappingProxyType(predictions))

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "packaging_class": self.packaging_class,
            "provenance": self.provenance,
            "ground_truth_digest": self.ground_truth.digest,
            "predictions": {key: value.digest for key, value in sorted(self.predictions.items())},
        }


@dataclass(frozen=True, slots=True)
class MaskQualityMetrics:
    intersection_over_union: float
    dice: float
    precision: float
    recall: float

    def __post_init__(self) -> None:
        for name in ("intersection_over_union", "dice", "precision", "recall"):
            value = getattr(self, name)
            if not isinstance(value, float) or not 0.0 <= value <= 1.0:
                raise SegmentationBenchmarkError(f"{name} must be a float in [0, 1]")

    def as_dict(self) -> dict[str, float]:
        return {
            "intersection_over_union": self.intersection_over_union,
            "dice": self.dice,
            "precision": self.precision,
            "recall": self.recall,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkScore:
    case_id: str
    candidate_id: str
    metrics: MaskQualityMetrics
    failure_modes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "candidate_id": self.candidate_id,
            "metrics": self.metrics.as_dict(),
            "failure_modes": list(self.failure_modes),
        }


@dataclass(frozen=True, slots=True)
class SegmentationBenchmarkReport:
    dataset_id: str
    dataset_version: str
    generator_seed: int
    candidates: tuple[BenchmarkCandidate, ...]
    cases: tuple[BenchmarkCase, ...]
    scores: tuple[BenchmarkScore, ...]
    minimum_iou: float
    minimum_dice: float
    selection_recommendation: str
    blocker: str | None
    report_digest: str = ""

    def __post_init__(self) -> None:
        _text(self.dataset_id, "dataset_id")
        _text(self.dataset_version, "dataset_version")
        if not isinstance(self.generator_seed, int) or self.generator_seed < 0:
            raise SegmentationBenchmarkError("generator_seed must be a non-negative integer")
        if not self.candidates or not self.cases:
            raise SegmentationBenchmarkError("benchmark report needs candidates and cases")
        if not 0.0 <= self.minimum_iou <= 1.0 or not 0.0 <= self.minimum_dice <= 1.0:
            raise SegmentationBenchmarkError("quality thresholds must be in [0, 1]")
        _text(self.selection_recommendation, "selection_recommendation")
        if self.selection_recommendation == "NO_SELECTION" and not self.blocker:
            raise SegmentationBenchmarkError("NO_SELECTION requires an explicit blocker")
        object.__setattr__(self, "candidates", tuple(self.candidates))
        object.__setattr__(self, "cases", tuple(self.cases))
        object.__setattr__(self, "scores", tuple(self.scores))
        body = self._body()
        expected = _digest(body)
        if self.report_digest and self.report_digest != expected:
            raise SegmentationBenchmarkError("report_digest does not match report content")
        object.__setattr__(self, "report_digest", expected)

    def _body(self) -> dict[str, object]:
        return {
            "contract": BENCHMARK_CONTRACT_VERSION,
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "generator_seed": self.generator_seed,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "cases": [case.as_dict() for case in self.cases],
            "scores": [score.as_dict() for score in self.scores],
            "minimum_iou": self.minimum_iou,
            "minimum_dice": self.minimum_dice,
            "selection_recommendation": self.selection_recommendation,
            "blocker": self.blocker,
        }

    def as_dict(self) -> dict[str, object]:
        return {**self._body(), "report_digest": self.report_digest}


def mask_quality_metrics(ground_truth: MaskRaster, prediction: MaskRaster) -> MaskQualityMetrics:
    """Calculate bounded pixel metrics without treating them as production accuracy."""

    if (ground_truth.width, ground_truth.height) != (prediction.width, prediction.height):
        raise SegmentationBenchmarkError("ground truth and prediction dimensions must match")
    tp = sum(
        actual and predicted for actual, predicted in zip(ground_truth.values, prediction.values)
    )
    fp = sum(
        not actual and predicted
        for actual, predicted in zip(ground_truth.values, prediction.values)
    )
    fn = sum(
        actual and not predicted
        for actual, predicted in zip(ground_truth.values, prediction.values)
    )
    union = tp + fp + fn
    predicted_positive = tp + fp
    actual_positive = tp + fn
    return MaskQualityMetrics(
        float(tp / union) if union else 1.0,
        float((2 * tp) / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else 1.0,
        float(tp / predicted_positive) if predicted_positive else 1.0,
        float(tp / actual_positive) if actual_positive else 1.0,
    )


def _raster(points: set[tuple[int, int]]) -> MaskRaster:
    return MaskRaster(8, 8, tuple((x, y) in points for y in range(8) for x in range(8)))


def build_synthetic_cases() -> tuple[BenchmarkCase, ...]:
    """Return five small deterministic public-safe packaging-shape cases."""

    classes = {
        "bottle": {(3, y) for y in range(1, 7)}
        | {(2, y) for y in range(2, 7)}
        | {(4, y) for y in range(2, 7)},
        "jerrycan": {(x, y) for x in range(1, 6) for y in range(2, 7)}
        | {(6, y) for y in range(3, 6)},
        "cap": {(x, y) for x in range(2, 6) for y in range(3, 5)},
        "transparent": {(x, y) for x in range(2, 6) for y in range(1, 7) if (x + y) % 2 == 0},
        "glossy-like": {
            (x, y) for x in range(1, 7) for y in range(1, 7) if x in {1, 6} or y in {1, 6}
        },
    }
    cases: list[BenchmarkCase] = []
    for index, (packaging_class, points) in enumerate(classes.items(), start=1):
        truth = _raster(points)
        edge_baseline = _raster(points | {(0, index), (7, 7 - index)})
        cases.append(
            BenchmarkCase(
                f"synthetic-{index:02d}",
                packaging_class,
                "PackLab-owned deterministic synthetic raster generator v1; no RAW_CAPTURE",
                truth,
                {
                    "packlab-synthetic-oracle-v1": truth,
                    "packlab-edge-baseline-v1": edge_baseline,
                },
            )
        )
    return tuple(cases)


def build_default_candidates() -> tuple[BenchmarkCandidate, ...]:
    return (
        BenchmarkCandidate(
            "packlab-synthetic-oracle-v1",
            ("deterministic-oracle",),
            "Python standard library",
            "PackLab-owned synthetic test code",
            "not-applicable",
            "not-applicable",
            True,
            selection_status="benchmark-baseline-only",
        ),
        BenchmarkCandidate(
            "packlab-edge-baseline-v1",
            ("deterministic-mask-baseline",),
            "Python standard library",
            "PackLab-owned synthetic test code",
            "not-applicable",
            "not-applicable",
            True,
            ("edge-overcoverage",),
            selection_status="benchmark-baseline-only",
        ),
        BenchmarkCandidate(
            "sam-3-reference-only",
            ("automatic", "prior-mask-refinement"),
            "not-installed",
            "not-reviewed",
            "not-reviewed",
            "not-reviewed",
            False,
            ("model-license-unreviewed", "checkpoint-unpinned", "runtime-unavailable"),
        ),
        BenchmarkCandidate(
            "pytorch-local-candidate-unselected",
            ("automatic", "point-prompt", "box-prompt", "batch"),
            "not-installed",
            "not-reviewed",
            "not-reviewed",
            "not-reviewed",
            False,
            ("model-license-unreviewed", "checkpoint-unpinned", "runtime-unavailable"),
        ),
    )


def build_default_report() -> SegmentationBenchmarkReport:
    candidates = build_default_candidates()
    cases = build_synthetic_cases()
    candidate_ids = {candidate.candidate_id for candidate in candidates}
    scores = tuple(
        BenchmarkScore(
            case.case_id, candidate_id, mask_quality_metrics(case.ground_truth, prediction)
        )
        for case in cases
        for candidate_id, prediction in sorted(case.predictions.items())
        if candidate_id in candidate_ids
    )
    return SegmentationBenchmarkReport(
        "packlab-m08-segmentation-synthetic-v1",
        "1.0.0",
        185,
        candidates,
        cases,
        scores,
        0.80,
        0.88,
        "NO_SELECTION",
        NO_SELECTION_LICENSE_OR_CHECKPOINT_BLOCKER,
    )
