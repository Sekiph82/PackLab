from __future__ import annotations

import json
import threading

import pytest
from test_sparse_export import _payload, _run

from packlab_core.dense_reconstruction import (
    DENSE_POINT_CLOUD_STAGE_ID,
    DensePointCloudConfig,
    DensePointCloudRequest,
    DensePointCloudRun,
    DenseReconstructionError,
    InvalidDenseReconstructionRequest,
    UnsupportedDenseReconstructionOption,
    build_openmvs_dense_command,
    execute_openmvs_dense,
    normalize_dense_reconstruction_result,
)
from packlab_core.engine_probe import EngineProbeResult, EngineProbeStatus, EngineVersion
from packlab_core.openmvs_conversion import convert_sparse_export_to_openmvs_scene_plan
from packlab_core.reconstruction import (
    ReconstructionStageResult,
    RunStatus,
    ScaleState,
    StageStatus,
)
from packlab_core.sparse_export import SparseExportBundle, export_sparse_mapping


def _plan():
    bundle: SparseExportBundle = export_sparse_mapping(_run(), _payload())
    return convert_sparse_export_to_openmvs_scene_plan(bundle)


def _request(configuration: DensePointCloudConfig | None = None) -> DensePointCloudRequest:
    return DensePointCloudRequest.from_conversion_plan(_plan(), configuration)


def _probe(executable: str = "DensifyPointCloud.exe") -> EngineProbeResult:
    return EngineProbeResult(
        "openmvs",
        executable,
        EngineProbeStatus.VALID,
        EngineVersion(2, 4, 0),
        "version matches the selected baseline",
        configured=True,
    )


def _stage(
    status: StageStatus = StageStatus.SUCCEEDED,
    *,
    exit_code: int | None = 0,
    cancelled: bool | None = None,
    stage_id: str = DENSE_POINT_CLOUD_STAGE_ID,
    stdout: str = "dense points: 999999",
    stderr: str = "",
) -> ReconstructionStageResult:
    return ReconstructionStageResult(
        stage_id,
        status,
        exit_code,
        0.01,
        stdout=stdout,
        stderr=stderr,
        cancelled=status is StageStatus.CANCELLED if cancelled is None else cancelled,
        failure_reason=None if status is StageStatus.SUCCEEDED else "stage failed",
    )


def test_request_binds_plan_and_configuration_provenance_without_geometry_claims() -> None:
    request = _request()
    payload = json.loads(request.serialize())

    assert request.input_scene_asset_id == "working/reconstruction/openmvs/scene"
    assert request.source_digest == request.conversion_plan.source_digest
    assert request.plan_digest == request.conversion_plan.digest
    assert request.configuration_digest == request.configuration.digest
    assert payload["authority_class"] == "RECONSTRUCTION_OBSERVATION"
    assert payload["scale_state"] == ScaleState.RELATIVE.value
    assert "C:" not in request.serialize()


@pytest.mark.parametrize(
    "configuration",
    [
        {"dense_output_asset_id": "C:/private/dense"},
        {"dense_output_asset_id": "/private/dense"},
        {"dense_output_asset_id": "working/../dense"},
        {"dense_output_asset_id": "working/dense\\file"},
        {"min_resolution": 3000, "max_resolution": 1000},
        {"fusion_depth_diff_threshold": float("nan")},
        {"fusion_reprojection_threshold": float("inf")},
    ],
)
def test_unsafe_or_invalid_configuration_fails_closed(configuration: dict[str, object]) -> None:
    with pytest.raises((InvalidDenseReconstructionRequest, UnsupportedDenseReconstructionOption)):
        DensePointCloudConfig.from_overrides(configuration)


def test_unknown_and_caller_controlled_options_are_rejected() -> None:
    for overrides in (
        {"--input-file": "private"},
        {"openmvs_options": {"--number-views": 2}},
        {"extra_args": ("--help",)},
    ):
        with pytest.raises(UnsupportedDenseReconstructionOption):
            DensePointCloudConfig.from_overrides(overrides)
    with pytest.raises(UnsupportedDenseReconstructionOption, match="METRIC_VERIFIED"):
        DensePointCloudConfig(scale_state=ScaleState.METRIC_VERIFIED)


def test_request_rejects_same_input_and_output_asset() -> None:
    plan = _plan()
    with pytest.raises(InvalidDenseReconstructionRequest, match="differ"):
        DensePointCloudRequest.from_conversion_plan(
            plan,
            DensePointCloudConfig(dense_output_asset_id=plan.output_scene_asset_id),
        )


def test_command_mapping_is_complete_and_matches_pinned_densifier_options() -> None:
    request = _request(
        DensePointCloudConfig(
            dense_output_asset_id="working/reconstruction/openmvs/dense-custom",
            resolution_level=2,
            max_resolution=2048,
            min_resolution=512,
            sub_resolution_levels=3,
            number_views=7,
            number_views_fuse=4,
            iters=5,
            geometric_iters=1,
            estimate_colors=1,
            estimate_normals=0,
            fusion_filter=1,
            fusion_depth_diff_threshold=0.02,
            fusion_reprojection_threshold=1.5,
            postprocess_dmaps=4,
        )
    )
    assert build_openmvs_dense_command(request, "DensifyPointCloud.exe") == (
        "DensifyPointCloud.exe",
        "--input-file",
        "working/reconstruction/openmvs/scene",
        "--output-file",
        "working/reconstruction/openmvs/dense-custom",
        "--resolution-level",
        "2",
        "--max-resolution",
        "2048",
        "--min-resolution",
        "512",
        "--sub-resolution-levels",
        "3",
        "--number-views",
        "7",
        "--number-views-fuse",
        "4",
        "--iters",
        "5",
        "--geometric-iters",
        "1",
        "--estimate-colors",
        "1",
        "--estimate-normals",
        "0",
        "--fusion-filter",
        "1",
        "--fusion-depth-diff-threshold",
        "0.02",
        "--fusion-reprojection-threshold",
        "1.5",
        "--postprocess-dmaps",
        "4",
    )


def test_command_rejects_invalid_executable_without_discovery() -> None:
    with pytest.raises(InvalidDenseReconstructionRequest):
        build_openmvs_dense_command(_request(), "\x00")


@pytest.mark.parametrize(
    "probe",
    [
        EngineProbeResult(
            "colmap",
            "DensifyPointCloud.exe",
            EngineProbeStatus.VALID,
            EngineVersion(3, 12, 6),
            "wrong",
        ),
        EngineProbeResult(
            "openmvs", "DensifyPointCloud.exe", EngineProbeStatus.MISSING, None, "missing"
        ),
        EngineProbeResult(
            "openmvs",
            "DensifyPointCloud.exe",
            EngineProbeStatus.VALID,
            EngineVersion(2, 3, 0),
            "wrong",
        ),
    ],
)
def test_execution_requires_valid_matching_dense_probe(probe: EngineProbeResult) -> None:
    with pytest.raises(UnsupportedDenseReconstructionOption):
        execute_openmvs_dense(_request(), "DensifyPointCloud.exe", probe)
    with pytest.raises(UnsupportedDenseReconstructionOption, match="does not match"):
        execute_openmvs_dense(_request(), "other.exe", _probe())


def test_execution_uses_existing_stage_boundary_and_preserves_timeout_cancellation_inputs() -> None:
    calls: list[tuple[str, tuple[str, ...], object, object]] = []

    def runner(stage_id: str, args: tuple[str, ...], **kwargs: object) -> ReconstructionStageResult:
        calls.append((stage_id, args, kwargs["timeout"], kwargs["cancel_event"]))
        return _stage()

    event = threading.Event()
    result = execute_openmvs_dense(
        _request(),
        "DensifyPointCloud.exe",
        _probe(),
        timeout=12.5,
        cancel_event=event,
        stage_runner=runner,
    )

    assert result.status is RunStatus.SUCCEEDED
    assert result.dense_output_asset_id == "working/reconstruction/openmvs/dense"
    assert calls[0][0] == DENSE_POINT_CLOUD_STAGE_ID
    assert calls[0][2:] == (12.5, event)


def test_success_does_not_infer_point_counts_from_arbitrary_engine_output() -> None:
    result = normalize_dense_reconstruction_result(
        _request(),
        _stage(stdout="points=not-a-contract-and-not-a-count"),
    )
    assert result.status is RunStatus.SUCCEEDED
    assert result.dense_output_asset_id == result.request.configuration.dense_output_asset_id
    assert "point_count" not in result.as_dict()


def test_failed_and_cancelled_runs_never_expose_dense_output() -> None:
    request = _request()
    failed = normalize_dense_reconstruction_result(request, _stage(StageStatus.FAILED, exit_code=7))
    cancelled = normalize_dense_reconstruction_result(
        request,
        _stage(StageStatus.CANCELLED, exit_code=None),
    )
    assert failed.status is RunStatus.FAILED
    assert failed.dense_output_asset_id is None
    assert cancelled.status is RunStatus.CANCELLED
    assert cancelled.dense_output_asset_id is None


@pytest.mark.parametrize(
    "stage",
    [
        _stage(stage_id="other"),
        _stage(stdout="success", cancelled=True),
        _stage(stdout="success", exit_code=7),
        _stage(StageStatus.FAILED, cancelled=True),
        _stage(StageStatus.CANCELLED, exit_code=None, cancelled=False),
    ],
)
def test_inconsistent_stage_results_fail_closed_without_output(
    stage: ReconstructionStageResult,
) -> None:
    result = normalize_dense_reconstruction_result(_request(), stage)
    assert result.status is RunStatus.FAILED
    assert result.dense_output_asset_id is None
    assert result.stage_result.stage_id == DENSE_POINT_CLOUD_STAGE_ID
    assert result.stage_result.status is StageStatus.FAILED


def test_direct_run_rejects_output_on_failure_and_mismatched_output_identity() -> None:
    request = _request()
    with pytest.raises(DenseReconstructionError, match="cannot expose output"):
        DensePointCloudRun(
            request, RunStatus.FAILED, _stage(StageStatus.FAILED, exit_code=7), "working/dense"
        )
    with pytest.raises(DenseReconstructionError, match="does not match"):
        DensePointCloudRun(request, RunStatus.SUCCEEDED, _stage(), "working/other")


def test_result_keeps_authority_scale_and_provenance_immutable() -> None:
    request = _request(DensePointCloudConfig(scale_state=ScaleState.METRIC_UNVERIFIED))
    result = normalize_dense_reconstruction_result(request, _stage())
    data = result.as_dict()

    assert result.authority_class == "RECONSTRUCTION_OBSERVATION"
    assert result.scale_state is ScaleState.METRIC_UNVERIFIED
    assert data["source_digest"] == request.source_digest
    assert data["plan_digest"] == request.plan_digest
    assert data["configuration_digest"] == request.configuration_digest
    assert "Scan Master" in " ".join(result.limitations)


def test_result_rejects_non_stage_runner_output() -> None:
    def runner(*_: object, **__: object) -> object:
        return "not-a-stage-result"

    with pytest.raises(DenseReconstructionError, match="stage runner"):
        execute_openmvs_dense(_request(), "DensifyPointCloud.exe", _probe(), stage_runner=runner)  # type: ignore[arg-type]
