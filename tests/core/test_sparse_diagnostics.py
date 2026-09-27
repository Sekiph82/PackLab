from __future__ import annotations

import hashlib
import json

import pytest

from packlab_core.reconstruction import ReconstructionStageResult, RunStatus, StageStatus
from packlab_core.sparse_diagnostics import (
    SPARSE_DIAGNOSTICS_CONTRACT,
    InvalidSparseDiagnosticPolicy,
    SparseDiagnosticCode,
    SparseDiagnosticPolicy,
    SparseDiagnosticSeverity,
    diagnose_sparse_mapping,
)
from packlab_core.sparse_mapping import (
    STAGE_SUMMARY_CONTRACT,
    RegisteredImageStatistics,
    SparseMappingRequest,
    SparseMappingRun,
    normalize_sparse_mapping_result,
)

_SOURCE_DIGEST = hashlib.sha256(b"packscan").hexdigest()
_MATCHER_DIGEST = hashlib.sha256(b"matcher").hexdigest()


def _request(total: int = 10) -> SparseMappingRequest:
    return SparseMappingRequest(
        tuple(f"working/images/{index:03d}.jpg" for index in range(total)),
        "working-revision-1",
        _SOURCE_DIGEST,
        _MATCHER_DIGEST,
    )


def _run(
    registered: int,
    *,
    total: int = 10,
    status: StageStatus = StageStatus.SUCCEEDED,
    cancelled: bool | None = None,
    exit_code: int | None = 0,
) -> SparseMappingRun:
    unregistered = total - registered
    summary = {
        "contract": STAGE_SUMMARY_CONTRACT,
        "total_images": total,
        "registered_images": registered,
        "unregistered_images": unregistered,
        "registration_ratio": registered / total,
        "sparse_model_asset_id": "working/reconstruction/sparse",
    }
    stage = ReconstructionStageResult(
        "sparse-mapping",
        status,
        exit_code,
        0.1,
        stdout="PACKLAB_SPARSE_MAPPING_SUMMARY_V1 " + json.dumps(summary),
        cancelled=status is StageStatus.CANCELLED if cancelled is None else cancelled,
    )
    return normalize_sparse_mapping_result(_request(total), stage)


def _policy(
    *, minimum_registered_images: int = 8, minimum_registration_ratio: float = 0.8
) -> SparseDiagnosticPolicy:
    return SparseDiagnosticPolicy(minimum_registered_images, minimum_registration_ratio)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"minimum_registered_images": 0, "minimum_registration_ratio": 0.8},
        {"minimum_registered_images": 1, "minimum_registration_ratio": 0.0},
        {"minimum_registered_images": 1, "minimum_registration_ratio": 1.1},
        {"minimum_registered_images": 1, "minimum_registration_ratio": float("nan")},
        {"minimum_registered_images": 1, "minimum_registration_ratio": float("inf")},
        {"minimum_registered_images": True, "minimum_registration_ratio": 0.8},
    ],
)
def test_policy_rejects_invalid_thresholds(kwargs: dict[str, object]) -> None:
    with pytest.raises(InvalidSparseDiagnosticPolicy):
        SparseDiagnosticPolicy(**kwargs)  # type: ignore[arg-type]


def test_policy_is_immutable_explicit_and_deterministically_serialized() -> None:
    policy = _policy()
    assert policy.serialize() == policy.serialize()
    assert policy.digest() == SparseDiagnosticPolicy(8, 0.8).digest()
    with pytest.raises((AttributeError, TypeError)):
        policy.minimum_registered_images = 9  # type: ignore[misc]


@pytest.mark.parametrize(
    ("registered", "expected_code", "healthy"),
    [
        (0, SparseDiagnosticCode.REGISTRATION_EMPTY, False),
        (7, SparseDiagnosticCode.REGISTRATION_FRAGMENTED, False),
        (8, SparseDiagnosticCode.REGISTRATION_COMPLETE, True),
        (10, SparseDiagnosticCode.REGISTRATION_COMPLETE, True),
    ],
)
def test_registration_boundaries_are_inclusive_and_deterministic(
    registered: int, expected_code: SparseDiagnosticCode, healthy: bool
) -> None:
    report = diagnose_sparse_mapping(_run(registered), _policy())

    assert report.code is expected_code
    assert report.healthy is healthy
    assert report.severity is (
        SparseDiagnosticSeverity.INFO if healthy else SparseDiagnosticSeverity.ERROR
    )
    assert report.statistics is not None
    assert report.statistics.registered_images == registered
    assert report.serialize() == diagnose_sparse_mapping(_run(registered), _policy()).serialize()


def test_partial_registration_meeting_count_but_not_ratio_is_fragmented() -> None:
    report = diagnose_sparse_mapping(_run(7, total=8), SparseDiagnosticPolicy(6, 0.9))

    assert report.code is SparseDiagnosticCode.REGISTRATION_FRAGMENTED
    assert report.statistics == RegisteredImageStatistics(8, 7, 1)


@pytest.mark.parametrize(
    "run",
    [
        _run(1, status=StageStatus.FAILED, exit_code=7),
        _run(1, status=StageStatus.CANCELLED, cancelled=True, exit_code=None),
    ],
)
def test_failed_and_cancelled_runs_are_never_healthy_or_statistically_claimed(
    run: SparseMappingRun,
) -> None:
    report = diagnose_sparse_mapping(run, _policy())

    assert report.healthy is False
    assert report.statistics is None
    assert report.code in {
        SparseDiagnosticCode.RUN_FAILED,
        SparseDiagnosticCode.RUN_CANCELLED,
    }


def test_invalid_result_fails_closed_without_raw_stage_details_or_output_identity() -> None:
    run = _run(8)
    object.__setattr__(run, "statistics", None)
    object.__setattr__(run.stage_result, "stderr", "C:/private/capture token=SECRET")

    report = diagnose_sparse_mapping(run, _policy())
    serialized = report.serialize()

    assert report.code is SparseDiagnosticCode.RESULT_INVALID
    assert report.healthy is False
    assert report.statistics is None
    assert "SECRET" not in serialized
    assert "private" not in serialized.lower()
    assert "sparse_model_asset_id" not in report.as_dict()


def test_invalid_stage_invariants_fail_closed_even_when_asset_identity_exists() -> None:
    run = _run(8)
    object.__setattr__(run.stage_result, "stage_id", "other-stage")

    report = diagnose_sparse_mapping(run, _policy())

    assert report.code is SparseDiagnosticCode.RESULT_INVALID
    assert report.healthy is False
    assert report.statistics is None


@pytest.mark.parametrize(
    "field_value",
    [
        ("cancelled", True),
        ("exit_code", 7),
        ("status", StageStatus.FAILED),
    ],
)
def test_contradictory_stage_flags_and_exit_status_fail_closed(
    field_value: tuple[str, object],
) -> None:
    run = _run(8)
    object.__setattr__(run.stage_result, field_value[0], field_value[1])

    report = diagnose_sparse_mapping(run, _policy())

    assert report.code is SparseDiagnosticCode.RESULT_INVALID
    assert report.healthy is False
    assert report.statistics is None


def test_non_mutation_and_machine_readable_report_shape() -> None:
    run = _run(8)
    before = run.as_dict()
    report = diagnose_sparse_mapping(run, _policy())
    payload = json.loads(report.serialize())

    assert run.as_dict() == before
    assert payload["contract"] == SPARSE_DIAGNOSTICS_CONTRACT
    assert payload["status"] == RunStatus.SUCCEEDED.value
    assert payload["statistics"]["registered_images"] == 8
    assert payload["policy"]["minimum_registration_ratio"] == 0.8
    assert "stdout" not in payload
    assert "stderr" not in payload
    assert "sparse_model_asset_id" not in payload
