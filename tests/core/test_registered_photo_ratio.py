from __future__ import annotations

import hashlib
import json

import pytest

from packlab_core.reconstruction import ReconstructionStageResult, RunStatus, StageStatus
from packlab_core.registered_photo_ratio import (
    REGISTERED_PHOTO_RATIO_CONTRACT,
    build_registered_photo_ratio_report,
)
from packlab_core.sparse_mapping import (
    STAGE_SUMMARY_CONTRACT,
    SparseMappingRequest,
    SparseMappingRun,
    normalize_sparse_mapping_result,
)

_SOURCE_DIGEST = hashlib.sha256(b"synthetic packscan source").hexdigest()
_MATCHER_DIGEST = hashlib.sha256(b"synthetic matcher selection").hexdigest()


def _request(
    image_ids: tuple[str, ...] = (
        "working/images/001.jpg",
        "working/images/002.jpg",
        "working/images/003.jpg",
    ),
) -> SparseMappingRequest:
    return SparseMappingRequest(image_ids, "revision-1", _SOURCE_DIGEST, _MATCHER_DIGEST)


def _summary(total: int, registered: int) -> dict[str, object]:
    return {
        "contract": STAGE_SUMMARY_CONTRACT,
        "total_images": total,
        "registered_images": registered,
        "unregistered_images": total - registered,
        "registration_ratio": registered / total,
        "sparse_model_asset_id": "working/reconstruction/sparse",
    }


def _run(registered: int, *, request: SparseMappingRequest | None = None) -> SparseMappingRun:
    use_request = request or _request()
    summary = _summary(len(use_request.image_asset_ids), registered)
    stage = ReconstructionStageResult(
        "sparse-mapping",
        StageStatus.SUCCEEDED,
        0,
        0.125,
        stdout="PACKLAB_SPARSE_MAPPING_SUMMARY_V1 " + json.dumps(summary, sort_keys=True),
    )
    return normalize_sparse_mapping_result(use_request, stage)


@pytest.mark.parametrize(
    ("registered", "expected_ratio", "expected_code"),
    [
        (0, 0.0, "registered_photo_ratio_zero"),
        (1, 1 / 3, "registered_photo_ratio_observed"),
        (2, 2 / 3, "registered_photo_ratio_observed"),
        (3, 1.0, "registered_photo_ratio_observed"),
    ],
)
def test_zero_one_partial_and_all_registration_are_observations(
    registered: int, expected_ratio: float, expected_code: str
) -> None:
    report = build_registered_photo_ratio_report(_run(registered))
    payload = report.as_dict()

    assert payload["contract"] == REGISTERED_PHOTO_RATIO_CONTRACT
    assert payload["observation_status"] == "observed"
    assert payload["acceptance_status"] == "not_evaluated"
    assert payload["statistics"]["total_input_photos"] == 3  # type: ignore[index]
    assert payload["statistics"]["registered_photos"] == registered  # type: ignore[index]
    assert payload["statistics"]["registration_ratio"] == pytest.approx(expected_ratio)  # type: ignore[index]
    assert payload["diagnostics"][0]["code"] == expected_code  # type: ignore[index]


def test_denominator_is_bound_to_exact_ordered_input_identities() -> None:
    first = build_registered_photo_ratio_report(_run(2, request=_request()))
    reordered = build_registered_photo_ratio_report(
        _run(
            2,
            request=_request(
                ("working/images/002.jpg", "working/images/001.jpg", "working/images/003.jpg")
            ),
        )
    )

    first_evidence = first.as_dict()["source_evidence"]
    reordered_evidence = reordered.as_dict()["source_evidence"]
    assert first_evidence["ordered_input_photo_count"] == 3  # type: ignore[index]
    assert (
        first_evidence["ordered_input_photo_ids_sha256"]
        != reordered_evidence[  # type: ignore[index]
            "ordered_input_photo_ids_sha256"
        ]
    )
    assert first_evidence["request_sha256"] != reordered_evidence["request_sha256"]  # type: ignore[index]


@pytest.mark.parametrize("bad_ids", [(), ("working/images/001.jpg", "working/images/001.jpg")])
def test_zero_or_duplicate_input_identity_fails_closed(bad_ids: tuple[str, ...]) -> None:
    run = _run(2)
    object.__setattr__(run.request, "image_asset_ids", bad_ids)

    payload = build_registered_photo_ratio_report(run).as_dict()
    assert payload["observation_status"] == "invalid"
    assert payload["acceptance_status"] == "not_evaluated"
    assert payload["statistics"] is None
    assert payload["diagnostics"][0]["code"] == "sparse_mapping_run_invalid"  # type: ignore[index]


def test_missing_and_malformed_stage_counts_fail_closed() -> None:
    request = _request()
    for malformed in (
        {"contract": STAGE_SUMMARY_CONTRACT, "total_images": 3, "registered_images": 2},
        {
            "contract": STAGE_SUMMARY_CONTRACT,
            "total_images": 3,
            "registered_images": 2.0,
            "unregistered_images": 1,
            "sparse_model_asset_id": "working/reconstruction/sparse",
        },
    ):
        stage = ReconstructionStageResult(
            "sparse-mapping",
            StageStatus.SUCCEEDED,
            0,
            0.1,
            stdout="PACKLAB_SPARSE_MAPPING_SUMMARY_V1 " + json.dumps(malformed),
        )
        failed = normalize_sparse_mapping_result(request, stage)
        payload = build_registered_photo_ratio_report(failed).as_dict()
        assert failed.status is RunStatus.FAILED
        assert payload["observation_status"] == "unavailable"
        assert payload["acceptance_status"] == "not_evaluated"
        assert payload["statistics"] is None
        assert payload["diagnostics"][0]["code"] == "colmap_stage_not_successful"  # type: ignore[index]


def test_successful_run_with_mutated_counts_or_stage_summary_is_invalid() -> None:
    run = _run(2)
    assert run.statistics is not None
    object.__setattr__(run.statistics, "registered_images", 1)
    payload = build_registered_photo_ratio_report(run).as_dict()
    assert payload["observation_status"] == "invalid"
    assert payload["statistics"] is None

    changed_stage = _run(2)
    object.__setattr__(
        changed_stage.stage_result,
        "stdout",
        "PACKLAB_SPARSE_MAPPING_SUMMARY_V1 " + json.dumps(_summary(3, 1)),
    )
    assert (
        build_registered_photo_ratio_report(changed_stage).as_dict()["observation_status"]
        == "invalid"
    )


def test_failed_and_cancelled_stage_have_no_ratio() -> None:
    request = _request()
    failed_stage = ReconstructionStageResult("sparse-mapping", StageStatus.FAILED, 7, 0.1)
    cancelled_stage = ReconstructionStageResult(
        "sparse-mapping", StageStatus.CANCELLED, None, 0.1, cancelled=True
    )
    for run in (
        SparseMappingRun(request, RunStatus.FAILED, failed_stage),
        SparseMappingRun(request, RunStatus.CANCELLED, cancelled_stage),
    ):
        payload = build_registered_photo_ratio_report(run).as_dict()
        assert payload["observation_status"] == "unavailable"
        assert payload["statistics"] is None
        assert payload["acceptance_status"] == "not_evaluated"


def test_report_is_deterministic_redacted_and_does_not_mutate_run() -> None:
    run = _run(2)
    before = run.as_dict()
    first = build_registered_photo_ratio_report(run)
    second = build_registered_photo_ratio_report(run)
    payload = first.as_dict()
    serialized = first.serialize()

    assert first.serialize() == second.serialize()
    assert first.digest() == second.digest()
    assert run.as_dict() == before
    assert payload["source_evidence"]["stage"]["stage_id"] == "sparse-mapping"  # type: ignore[index]
    assert '"stdout":' not in serialized and '"stderr":' not in serialized
    assert "sparse_model_asset_id" not in serialized


def test_wrong_public_input_fails_closed() -> None:
    payload = build_registered_photo_ratio_report(None).as_dict()
    assert payload["observation_status"] == "invalid"
    assert payload["statistics"] is None
