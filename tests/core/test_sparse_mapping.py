from __future__ import annotations

import hashlib
import json
import sys

import pytest

from packlab_core.engine_probe import EngineProbeResult, EngineProbeStatus, EngineVersion
from packlab_core.reconstruction import ReconstructionStageResult, RunStatus, StageStatus
from packlab_core.reconstruction_process import run_reconstruction_stage
from packlab_core.sparse_mapping import (
    COLMAP_ENGINE_VERSION,
    STAGE_SUMMARY_CONTRACT,
    STAGE_SUMMARY_PREFIX,
    InvalidSparseMappingRequest,
    RegisteredImageStatistics,
    SparseMappingConfig,
    SparseMappingError,
    SparseMappingRequest,
    SparseMappingRun,
    SparseMappingSummaryError,
    UnsupportedSparseMappingOption,
    build_colmap_sparse_mapper_command,
    execute_sparse_mapping,
    normalize_sparse_mapping_result,
    parse_registered_image_statistics,
)

_SOURCE_DIGEST = hashlib.sha256(b"packscan").hexdigest()
_MATCHER_DIGEST = hashlib.sha256(b"matcher").hexdigest()


def _request(
    image_asset_ids: tuple[str, ...] = ("working/images/001.jpg", "working/images/002.jpg"),
    *,
    configuration: SparseMappingConfig | None = None,
) -> SparseMappingRequest:
    return SparseMappingRequest(
        image_asset_ids,
        "working-revision-1",
        _SOURCE_DIGEST,
        _MATCHER_DIGEST,
        SparseMappingConfig() if configuration is None else configuration,
    )


def _probe(executable: str = "colmap.exe") -> EngineProbeResult:
    return EngineProbeResult(
        "colmap",
        executable,
        EngineProbeStatus.VALID,
        EngineVersion(3, 12, 6),
        "version matches the selected baseline",
        configured=True,
    )


def _summary(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "contract": STAGE_SUMMARY_CONTRACT,
        "total_images": 3,
        "registered_images": 2,
        "unregistered_images": 1,
        "registration_ratio": 2 / 3,
    }
    value.update(overrides)
    return value


def _summary_with_output(**overrides: object) -> dict[str, object]:
    value = _summary(sparse_model_asset_id="working/reconstruction/sparse")
    value.update(overrides)
    return value


def _stage(
    status: StageStatus = StageStatus.SUCCEEDED,
    *,
    stdout: str = "",
    exit_code: int | None = 0,
    failure_reason: str | None = None,
    stage_id: str = "sparse-mapping",
    cancelled: bool | None = None,
) -> ReconstructionStageResult:
    return ReconstructionStageResult(
        stage_id,
        status,
        exit_code,
        0.01,
        stdout=stdout,
        failure_reason=failure_reason,
        cancelled=status is StageStatus.CANCELLED if cancelled is None else cancelled,
    )


def test_request_is_immutable_order_bound_and_digest_stable() -> None:
    source = ["working/images/001.jpg", "working/images/002.jpg"]
    request = _request(tuple(source))
    source.reverse()
    reversed_order = _request(tuple(source))

    assert request.image_asset_ids == ("working/images/001.jpg", "working/images/002.jpg")
    assert request.request_digest() != reversed_order.request_digest()
    assert "C:" not in request.serialize()
    assert json.loads(request.serialize())["image_asset_ids"] == list(request.image_asset_ids)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"image_asset_ids": ()}, "at least one"),
        ({"image_asset_ids": ("working/images/001.jpg", "working/images/001.jpg")}, "unique"),
        ({"image_asset_ids": ("C:/private/image.jpg",)}, "repository-relative"),
        ({"image_asset_ids": ("working/images/../001.jpg",)}, "unsafe"),
        ({"image_asset_ids": ("/private/image.jpg",)}, "repository-relative"),
        ({"source_digest": "not-a-digest"}, "SHA-256"),
        ({"matcher_selection_digest": "not-a-digest"}, "SHA-256"),
        ({"source_revision": "../revision"}, "safe portable"),
    ],
)
def test_request_rejects_unsafe_or_missing_identity(
    kwargs: dict[str, object], message: str
) -> None:
    base: dict[str, object] = {
        "image_asset_ids": ("working/images/001.jpg",),
        "source_revision": "working-revision-1",
        "source_digest": _SOURCE_DIGEST,
        "matcher_selection_digest": _MATCHER_DIGEST,
    }
    base.update(kwargs)
    with pytest.raises(
        (InvalidSparseMappingRequest, UnsupportedSparseMappingOption), match=message
    ):
        SparseMappingRequest(**base)  # type: ignore[arg-type]


def test_request_rejects_wrong_engine_version_and_config_paths() -> None:
    with pytest.raises(UnsupportedSparseMappingOption, match=COLMAP_ENGINE_VERSION):
        SparseMappingRequest(
            ("working/images/001.jpg",),
            "revision",
            _SOURCE_DIGEST,
            _MATCHER_DIGEST,
            engine_version="3.13.0",
        )
    with pytest.raises(InvalidSparseMappingRequest, match="repository-relative"):
        SparseMappingConfig(image_path_asset_id="C:/private/images")


def test_command_mapping_is_explicit_and_does_not_discover_engine() -> None:
    command = build_colmap_sparse_mapper_command(_request(), "C:/tools/colmap.exe")
    assert command == (
        "C:/tools/colmap.exe",
        "mapper",
        "--database_path",
        "working/reconstruction/database.db",
        "--image_path",
        "working/images",
        "--output_path",
        "working/reconstruction/sparse",
    )


def test_command_adapter_rejects_unprobed_or_mismatched_engine() -> None:
    request = _request()
    with pytest.raises(UnsupportedSparseMappingOption, match="explicitly probed"):
        execute_sparse_mapping(
            request,
            "colmap.exe",
            EngineProbeResult("colmap", "colmap.exe", EngineProbeStatus.MISSING, None, "missing"),
        )
    with pytest.raises(UnsupportedSparseMappingOption, match="does not match"):
        execute_sparse_mapping(request, "other.exe", _probe())


@pytest.mark.parametrize(
    "summary",
    [
        _summary(total_images=0),
        _summary(registered_images=4),
        _summary(unregistered_images=0),
        _summary(unregistered_images=2),
        _summary(registration_ratio=0.5),
        _summary(registration_ratio=float("nan")),
        _summary(total_images=10_000_001, registered_images=10_000_000, unregistered_images=1),
        {"contract": STAGE_SUMMARY_CONTRACT, "total_images": 3, "registered_images": 2},
        _summary(registration_ratio=10**1000),
    ],
)
def test_statistics_reject_malformed_inconsistent_or_overflowed_summaries(
    summary: dict[str, object],
) -> None:
    with pytest.raises(SparseMappingSummaryError):
        parse_registered_image_statistics(summary)


def test_statistics_boundaries_and_alias_are_deterministic() -> None:
    zero_registered = parse_registered_image_statistics(
        _summary(registered_images=0, unregistered_images=3, registration_ratio=0.0)
    )
    all_registered = parse_registered_image_statistics(
        _summary(registered_images=3, unregistered_images=0, registration_ratio=1.0)
    )
    aliased = parse_registered_image_statistics(
        {
            "contract": STAGE_SUMMARY_CONTRACT,
            "total_input_images": 3,
            "registered_images": 2,
            "unregistered_images": 1,
        }
    )
    assert zero_registered.registration_ratio == 0.0
    assert all_registered.registration_ratio == 1.0
    assert aliased == RegisteredImageStatistics(3, 2, 1)
    assert aliased.serialize() == RegisteredImageStatistics(3, 2, 1).serialize()
    with pytest.raises(SparseMappingSummaryError):
        parse_registered_image_statistics("registered 2 of 3 images")


def test_successful_stage_requires_exact_machine_summary_and_exposes_output() -> None:
    request = _request(
        ("working/images/001.jpg", "working/images/002.jpg", "working/images/003.jpg")
    )
    stage = _stage(stdout=STAGE_SUMMARY_PREFIX + json.dumps(_summary_with_output()))
    result = normalize_sparse_mapping_result(request, stage)

    assert result.status is RunStatus.SUCCEEDED
    assert result.statistics == RegisteredImageStatistics(3, 2, 1)
    assert result.sparse_model_asset_id == "working/reconstruction/sparse"
    assert result.stage_result is stage


def test_successful_stage_with_malformed_summary_becomes_failed_without_output() -> None:
    request = _request()
    result = normalize_sparse_mapping_result(request, _stage(stdout="mapper registered 2 images"))

    assert result.status is RunStatus.FAILED
    assert result.stage_result.status is StageStatus.FAILED
    assert result.statistics is None
    assert result.sparse_model_asset_id is None
    assert "output contract invalid" in (result.stage_result.failure_reason or "")


def test_successful_stage_statistics_are_bound_to_request_image_count() -> None:
    result = normalize_sparse_mapping_result(
        _request(),
        _stage(stdout=STAGE_SUMMARY_PREFIX + json.dumps(_summary_with_output(total_images=3))),
    )

    assert result.status is RunStatus.FAILED
    assert "ordered request image count" in (result.stage_result.failure_reason or "")


def test_failed_and_cancelled_processes_never_claim_sparse_output() -> None:
    request = _request()
    failed = normalize_sparse_mapping_result(request, _stage(StageStatus.FAILED, exit_code=7))
    cancelled = normalize_sparse_mapping_result(
        request, _stage(StageStatus.CANCELLED, exit_code=None)
    )

    assert failed.status is RunStatus.FAILED
    assert failed.sparse_model_asset_id is None
    assert cancelled.status is RunStatus.CANCELLED
    assert cancelled.sparse_model_asset_id is None


@pytest.mark.parametrize(
    "stage",
    [
        _stage(stage_id="other", stdout=STAGE_SUMMARY_PREFIX + json.dumps(_summary_with_output())),
        _stage(
            stdout=STAGE_SUMMARY_PREFIX + json.dumps(_summary_with_output()),
            cancelled=True,
        ),
        _stage(stdout=STAGE_SUMMARY_PREFIX + json.dumps(_summary_with_output()), exit_code=7),
        _stage(StageStatus.FAILED, cancelled=True),
        _stage(StageStatus.CANCELLED, exit_code=None, cancelled=False),
    ],
)
def test_inconsistent_stage_results_fail_closed_without_output(
    stage: ReconstructionStageResult,
) -> None:
    result = normalize_sparse_mapping_result(_request(), stage)

    assert result.status is RunStatus.FAILED
    assert result.sparse_model_asset_id is None
    assert result.statistics is None
    assert result.stage_result.status is StageStatus.FAILED
    assert result.stage_result.stage_id == "sparse-mapping"


@pytest.mark.parametrize(
    "output_fields",
    [
        {},
        {"sparse_model_asset_id": None},
        {"sparse_model_asset_id": "working/reconstruction/sparse", "output_asset_id": None},
        {
            "sparse_model_asset_id": "working/reconstruction/sparse",
            "output_asset_id": "working/reconstruction/other",
        },
        {"sparse_model_asset_id": "C:/private/sparse"},
        {"sparse_model_asset_id": "working/reconstruction/../sparse"},
        {"sparse_model_asset_id": "working/reconstruction/other"},
    ],
)
def test_successful_summary_requires_one_matching_safe_output_identity(
    output_fields: dict[str, object],
) -> None:
    summary = _summary(**output_fields)
    result = normalize_sparse_mapping_result(
        _request(),
        _stage(stdout=STAGE_SUMMARY_PREFIX + json.dumps(summary)),
    )

    assert result.status is RunStatus.FAILED
    assert result.sparse_model_asset_id is None
    assert result.statistics is None


def test_equal_output_aliases_are_accepted() -> None:
    summary = _summary_with_output(output_asset_id="working/reconstruction/sparse")
    result = normalize_sparse_mapping_result(
        _request(("working/images/001.jpg", "working/images/002.jpg", "working/images/003.jpg")),
        _stage(stdout=STAGE_SUMMARY_PREFIX + json.dumps(summary)),
    )

    assert result.status is RunStatus.SUCCEEDED
    assert result.sparse_model_asset_id == "working/reconstruction/sparse"


def test_sparse_mapping_run_enforces_direct_success_invariants() -> None:
    request = _request()
    stage = _stage()
    statistics = RegisteredImageStatistics(3, 2, 1)

    with pytest.raises(SparseMappingError, match="image count"):
        SparseMappingRun(
            request,
            RunStatus.SUCCEEDED,
            stage,
            statistics,
            "working/reconstruction/sparse",
        )
    with pytest.raises(SparseMappingError, match="output identity"):
        SparseMappingRun(
            request,
            RunStatus.SUCCEEDED,
            stage,
            RegisteredImageStatistics(2, 1, 1),
            "working/reconstruction/other",
        )
    with pytest.raises(SparseMappingError, match="requires a successful stage"):
        SparseMappingRun(
            request,
            RunStatus.SUCCEEDED,
            _stage(StageStatus.FAILED, exit_code=7),
            RegisteredImageStatistics(2, 1, 1),
            "working/reconstruction/sparse",
        )


def test_sparse_mapping_run_rejects_mismatched_direct_stage_contract() -> None:
    request = _request()
    with pytest.raises(SparseMappingError, match="unexpected stage ID"):
        SparseMappingRun(
            request,
            RunStatus.SUCCEEDED,
            _stage(stage_id="other"),
            RegisteredImageStatistics(2, 1, 1),
            "working/reconstruction/sparse",
        )


def test_sparse_mapping_run_rejects_direct_failure_or_cancellation_output() -> None:
    request = _request()
    statistics = RegisteredImageStatistics(2, 1, 1)

    with pytest.raises(SparseMappingError, match="cannot expose output"):
        SparseMappingRun(
            request,
            RunStatus.FAILED,
            _stage(StageStatus.FAILED, exit_code=7),
            statistics,
            "working/reconstruction/sparse",
        )
    with pytest.raises(SparseMappingError, match="cannot expose output"):
        SparseMappingRun(
            request,
            RunStatus.CANCELLED,
            _stage(StageStatus.CANCELLED, exit_code=None),
            statistics,
            "working/reconstruction/sparse",
        )


def test_execute_uses_injected_runner_through_existing_stage_contract() -> None:
    calls: list[tuple[str, tuple[str, ...]]] = []

    def runner(stage_id: str, args: tuple[str, ...], **_: object) -> ReconstructionStageResult:
        calls.append((stage_id, args))
        return _stage(stdout=STAGE_SUMMARY_PREFIX + json.dumps(_summary_with_output()))

    result = execute_sparse_mapping(
        _request(("working/images/001.jpg", "working/images/002.jpg", "working/images/003.jpg")),
        "colmap.exe",
        _probe(),
        stage_runner=runner,
    )

    assert result.status is RunStatus.SUCCEEDED
    assert calls == [
        (
            "sparse-mapping",
            (
                "colmap.exe",
                "mapper",
                "--database_path",
                "working/reconstruction/database.db",
                "--image_path",
                "working/images",
                "--output_path",
                "working/reconstruction/sparse",
            ),
        )
    ]


def test_sparse_stage_uses_bounded_redacted_process_evidence() -> None:
    result = run_reconstruction_stage(
        "sparse-mapping",
        [
            sys.executable,
            "-c",
            "import sys; print('C:\\\\private\\\\capture\\\\image.jpg token=SECRET'); "
            "print('x' * 1000, file=sys.stderr)",
        ],
        max_output_chars=120,
    )

    assert result.status is StageStatus.SUCCEEDED
    assert len(result.stdout) <= 120
    assert "SECRET" not in result.stdout
    assert "private" not in result.stdout.lower()


def test_source_and_order_inputs_are_not_mutated() -> None:
    image_ids = ["working/images/001.jpg", "working/images/002.jpg"]
    config = SparseMappingConfig()
    request = SparseMappingRequest(image_ids, "revision", _SOURCE_DIGEST, _MATCHER_DIGEST, config)
    image_ids[0] = "working/images/changed.jpg"

    assert request.image_asset_ids == ("working/images/001.jpg", "working/images/002.jpg")
    assert config.as_dict()["image_path_asset_id"] == "working/images"
