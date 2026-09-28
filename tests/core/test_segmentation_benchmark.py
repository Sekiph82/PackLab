from __future__ import annotations

from pathlib import Path

import pytest

from packlab_core.segmentation import MaskRaster
from packlab_core.segmentation_benchmark import (
    NO_SELECTION_LICENSE_OR_CHECKPOINT_BLOCKER,
    BenchmarkCandidate,
    BenchmarkCase,
    SegmentationBenchmarkError,
    build_default_report,
    build_synthetic_cases,
    mask_quality_metrics,
)


def test_synthetic_dataset_covers_required_packaging_classes_and_is_deterministic() -> None:
    first = build_synthetic_cases()
    second = build_synthetic_cases()
    assert [case.packaging_class for case in first] == [
        "bottle",
        "jerrycan",
        "cap",
        "transparent",
        "glossy-like",
    ]
    assert [case.as_dict() for case in first] == [case.as_dict() for case in second]


def test_metrics_cover_perfect_and_boundary_masks() -> None:
    truth = MaskRaster(2, 2, (True, False, False, False))
    perfect = mask_quality_metrics(truth, truth)
    assert perfect.as_dict() == {
        "intersection_over_union": 1.0,
        "dice": 1.0,
        "precision": 1.0,
        "recall": 1.0,
    }
    empty = MaskRaster(2, 2, (False, False, False, False))
    empty_metrics = mask_quality_metrics(empty, empty)
    assert empty_metrics.dice == 1.0
    assert mask_quality_metrics(truth, empty).recall == 0.0


def test_report_is_reproducible_and_explicitly_does_not_select_a_model() -> None:
    first = build_default_report()
    second = build_default_report()
    assert first.report_digest == second.report_digest
    assert first.as_dict() == second.as_dict()
    assert first.selection_recommendation == "NO_SELECTION"
    assert first.blocker == NO_SELECTION_LICENSE_OR_CHECKPOINT_BLOCKER
    assert {case.packaging_class for case in first.cases} == {
        "bottle",
        "jerrycan",
        "cap",
        "transparent",
        "glossy-like",
    }


def test_predictions_are_immutable_and_report_digest_safe() -> None:
    prediction = MaskRaster(2, 2, (True, False, False, False))
    caller_predictions = {"candidate": prediction}
    case = BenchmarkCase(
        "case",
        "bottle",
        "synthetic",
        prediction,
        caller_predictions,
    )
    before_case = case.as_dict()
    caller_predictions["candidate"] = MaskRaster(2, 2, (False, True, False, False))
    assert case.as_dict() == before_case

    report = build_default_report()
    before_report = report.as_dict()
    with pytest.raises(TypeError):
        report.cases[0].predictions["packlab-synthetic-oracle-v1"] = MaskRaster(8, 8, (False,) * 64)  # type: ignore[index]
    assert report.as_dict() == before_report
    assert report.report_digest == before_report["report_digest"]


def test_unavailable_candidate_records_license_checkpoint_and_runtime_failure_modes() -> None:
    candidate = build_default_report().candidates[-1]
    assert not candidate.available
    assert candidate.license_record == "not-reviewed"
    assert candidate.checkpoint_sha256 == "not-reviewed"
    assert set(candidate.failure_modes) == {
        "model-license-unreviewed",
        "checkpoint-unpinned",
        "runtime-unavailable",
    }


def test_missing_license_or_checkpoint_cannot_be_marked_available() -> None:
    with pytest.raises(SegmentationBenchmarkError, match="unresolved license"):
        BenchmarkCandidate(
            "unsafe",
            ("automatic",),
            "installed",
            "not-reviewed",
            "not-reviewed",
            "not-reviewed",
            True,
        )


def test_mismatched_prediction_dimensions_fail_closed() -> None:
    from packlab_core.segmentation_benchmark import BenchmarkCase

    with pytest.raises(SegmentationBenchmarkError, match="dimensions"):
        BenchmarkCase(
            "case",
            "bottle",
            "synthetic",
            MaskRaster(2, 2, (True, False, False, False)),
            {"candidate": MaskRaster(1, 1, (True,))},
        )


def test_benchmark_does_not_mutate_a_source_sentinel(tmp_path: Path) -> None:
    source = tmp_path / "raw.capture"
    source.write_bytes(b"immutable-raw-capture")
    before = source.read_bytes()
    build_default_report()
    assert source.read_bytes() == before
