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
)
from packlab_core.engine_probe import EngineProbeResult, EngineProbeStatus, EngineVersion
from packlab_core.mesh_reconstruction import (
    DEFAULT_MESH_OUTPUT_ASSET_ID,
    MESH_RECONSTRUCTION_STAGE_ID,
    InvalidMeshReconstructionRequest,
    MeshReconstructionConfig,
    MeshReconstructionError,
    MeshReconstructionRequest,
    MeshReconstructionRun,
    UnsupportedMeshReconstructionOption,
    build_openmvs_mesh_command,
    execute_openmvs_mesh,
    normalize_mesh_reconstruction_result,
)
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


def _dense_run(
    *,
    status: StageStatus = StageStatus.SUCCEEDED,
    scale_state: ScaleState = ScaleState.RELATIVE,
    output_asset_id: str = "working/reconstruction/openmvs/dense",
) -> DensePointCloudRun:
    dense_request = DensePointCloudRequest.from_conversion_plan(
        _plan(),
        DensePointCloudConfig(dense_output_asset_id=output_asset_id, scale_state=scale_state),
    )
    stage = ReconstructionStageResult(
        DENSE_POINT_CLOUD_STAGE_ID,
        status,
        0 if status is StageStatus.SUCCEEDED else 8,
        0.01,
        stdout="dense points: 999999",
        cancelled=False,
        failure_reason=None if status is StageStatus.SUCCEEDED else "dense failed",
    )
    return DensePointCloudRun(
        dense_request,
        RunStatus.SUCCEEDED if status is StageStatus.SUCCEEDED else RunStatus.FAILED,
        stage,
        output_asset_id if status is StageStatus.SUCCEEDED else None,
    )


def _request(configuration: MeshReconstructionConfig | None = None) -> MeshReconstructionRequest:
    return MeshReconstructionRequest.from_dense_run(_dense_run(), configuration)


def _probe(executable: str = "ReconstructMesh.exe") -> EngineProbeResult:
    return EngineProbeResult(
        "openmvs.ReconstructMesh",
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
    stage_id: str = MESH_RECONSTRUCTION_STAGE_ID,
    stdout: str = "vertices=not-a-contract-and-not-a-count",
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


def test_request_binds_successful_dense_provenance_without_geometry_claims() -> None:
    request = _request(MeshReconstructionConfig(mesh_output_asset_id=DEFAULT_MESH_OUTPUT_ASSET_ID))
    payload = json.loads(request.serialize())

    assert request.input_scene_asset_id == "working/reconstruction/openmvs/scene"
    assert request.dense_point_cloud_asset_id == "working/reconstruction/openmvs/dense"
    assert request.source_digest == request.dense_run.source_digest
    assert request.plan_digest == request.dense_run.plan_digest
    assert request.dense_configuration_digest == request.dense_run.configuration_digest
    assert request.dense_request_digest == request.dense_run.request.request_digest
    assert payload["authority_class"] == "RECONSTRUCTION_OBSERVATION"
    assert payload["scale_state"] == ScaleState.RELATIVE.value
    assert "C:" not in request.serialize()


@pytest.mark.parametrize(
    "overrides",
    [
        {"mesh_output_asset_id": "C:/private/mesh"},
        {"mesh_output_asset_id": "/private/mesh"},
        {"mesh_output_asset_id": "working/../mesh"},
        {"mesh_output_asset_id": "working/mesh\\file"},
        {"mesh_output_asset_id": "private/mesh"},
        {"min_point_distance": -0.01},
        {"min_point_distance": float("nan")},
        {"thickness_factor": float("inf")},
        {"quality_factor": True},
        {"integrate_only_roi": 1},
        {"constant_weight": "true"},
        {"free_space_support": 0},
    ],
)
def test_invalid_semantic_values_and_asset_ids_fail_closed(
    overrides: dict[str, object],
) -> None:
    with pytest.raises((InvalidMeshReconstructionRequest, UnsupportedMeshReconstructionOption)):
        MeshReconstructionConfig.from_overrides(overrides)


def test_defaults_and_valid_edge_values_are_accepted() -> None:
    config = MeshReconstructionConfig.from_overrides(
        {
            "min_point_distance": 0,
            "integrate_only_roi": True,
            "constant_weight": False,
            "free_space_support": True,
            "thickness_factor": 0,
            "quality_factor": 0,
        }
    )
    assert config.min_point_distance == 0.0
    assert config.integrate_only_roi is True
    assert config.constant_weight is False
    assert config.free_space_support is True
    assert config.thickness_factor == 0.0
    assert config.quality_factor == 0.0
    assert MeshReconstructionConfig().mesh_output_asset_id == DEFAULT_MESH_OUTPUT_ASSET_ID


def test_unknown_and_caller_controlled_options_are_rejected() -> None:
    for overrides in (
        {"--input-file": "private"},
        {"openmvs_options": {"--close-holes": 30}},
        {"extra_args": ("--mesh-export",)},
    ):
        with pytest.raises(UnsupportedMeshReconstructionOption):
            MeshReconstructionConfig.from_overrides(overrides)


def test_request_requires_one_successful_dense_run_and_distinct_output() -> None:
    with pytest.raises(InvalidMeshReconstructionRequest):
        MeshReconstructionRequest("not-a-dense-run")  # type: ignore[arg-type]
    with pytest.raises(InvalidMeshReconstructionRequest, match="successful"):
        MeshReconstructionRequest.from_dense_run(_dense_run(status=StageStatus.FAILED))
    with pytest.raises(InvalidMeshReconstructionRequest, match="differ"):
        MeshReconstructionRequest.from_dense_run(
            _dense_run(),
            MeshReconstructionConfig(mesh_output_asset_id="working/reconstruction/openmvs/dense"),
        )


def test_command_mapping_is_complete_and_matches_pinned_reconstruct_mesh_options() -> None:
    request = _request(
        MeshReconstructionConfig(
            mesh_output_asset_id="working/reconstruction/openmvs/mesh-custom",
            min_point_distance=0.25,
            integrate_only_roi=True,
            constant_weight=False,
            free_space_support=True,
            thickness_factor=1.5,
            quality_factor=0.75,
        )
    )
    assert build_openmvs_mesh_command(request, "ReconstructMesh.exe") == (
        "ReconstructMesh.exe",
        "--input-file",
        "working/reconstruction/openmvs/scene",
        "--pointcloud-file",
        "working/reconstruction/openmvs/dense",
        "--output-file",
        "working/reconstruction/openmvs/mesh-custom",
        "--min-point-distance",
        "0.25",
        "--integrate-only-roi",
        "1",
        "--constant-weight",
        "0",
        "--free-space-support",
        "1",
        "--thickness-factor",
        "1.5",
        "--quality-factor",
        "0.75",
    )


def test_command_rejects_invalid_executable_without_discovery() -> None:
    with pytest.raises(InvalidMeshReconstructionRequest):
        build_openmvs_mesh_command(_request(), "\x00")


@pytest.mark.parametrize(
    "probe",
    [
        EngineProbeResult(
            "openmvs",
            "ReconstructMesh.exe",
            EngineProbeStatus.VALID,
            EngineVersion(2, 4, 0),
            "generic probe",
        ),
        EngineProbeResult(
            "openmvs.ReconstructMesh",
            "ReconstructMesh.exe",
            EngineProbeStatus.MISSING,
            None,
            "missing",
        ),
        EngineProbeResult(
            "openmvs.ReconstructMesh",
            "ReconstructMesh.exe",
            EngineProbeStatus.VALID,
            EngineVersion(2, 3, 0),
            "wrong",
        ),
    ],
)
def test_execution_requires_valid_matching_mesh_probe(probe: EngineProbeResult) -> None:
    with pytest.raises(UnsupportedMeshReconstructionOption):
        execute_openmvs_mesh(_request(), "ReconstructMesh.exe", probe)
    with pytest.raises(UnsupportedMeshReconstructionOption, match="does not match"):
        execute_openmvs_mesh(_request(), "other.exe", _probe())


def test_execution_uses_existing_stage_boundary_and_propagates_controls() -> None:
    calls: list[tuple[str, tuple[str, ...], object, object]] = []

    def runner(stage_id: str, args: tuple[str, ...], **kwargs: object) -> ReconstructionStageResult:
        calls.append((stage_id, args, kwargs["timeout"], kwargs["cancel_event"]))
        return _stage()

    event = threading.Event()
    result = execute_openmvs_mesh(
        _request(),
        "ReconstructMesh.exe",
        _probe(),
        timeout=12.5,
        cancel_event=event,
        stage_runner=runner,
    )

    assert result.status is RunStatus.SUCCEEDED
    assert result.mesh_output_asset_id == DEFAULT_MESH_OUTPUT_ASSET_ID
    assert calls[0][0] == MESH_RECONSTRUCTION_STAGE_ID
    assert calls[0][2:] == (12.5, event)


def test_success_does_not_infer_mesh_counts_or_quality_from_engine_output() -> None:
    result = normalize_mesh_reconstruction_result(
        _request(), _stage(stdout="faces=999999 quality=perfect")
    )
    assert result.status is RunStatus.SUCCEEDED
    assert result.mesh_output_asset_id == result.request.configuration.mesh_output_asset_id
    data = result.as_dict()
    assert "point_count" not in data
    assert "triangle_count" not in data
    assert "quality" not in data


def test_failed_and_cancelled_runs_never_expose_mesh_output() -> None:
    request = _request()
    failed = normalize_mesh_reconstruction_result(request, _stage(StageStatus.FAILED, exit_code=7))
    cancelled = normalize_mesh_reconstruction_result(
        request, _stage(StageStatus.CANCELLED, exit_code=None)
    )
    assert failed.status is RunStatus.FAILED
    assert failed.mesh_output_asset_id is None
    assert cancelled.status is RunStatus.CANCELLED
    assert cancelled.mesh_output_asset_id is None


@pytest.mark.parametrize(
    "stage",
    [
        _stage(stage_id="other"),
        _stage(stdout="success", cancelled=True),
        _stage(stdout="success", exit_code=7),
        _stage(StageStatus.FAILED, cancelled=True),
        _stage(StageStatus.FAILED, exit_code=0),
        _stage(StageStatus.CANCELLED, exit_code=None, cancelled=False),
        _stage(StageStatus.CANCELLED, exit_code=0),
    ],
)
def test_malformed_stage_results_fail_closed_without_output(
    stage: ReconstructionStageResult,
) -> None:
    result = normalize_mesh_reconstruction_result(_request(), stage)
    assert result.status is RunStatus.FAILED
    assert result.mesh_output_asset_id is None
    assert result.stage_result.stage_id == MESH_RECONSTRUCTION_STAGE_ID
    assert result.stage_result.status is StageStatus.FAILED


def test_direct_run_rejects_output_on_failure_and_mismatched_output_identity() -> None:
    request = _request()
    with pytest.raises(MeshReconstructionError, match="cannot expose output"):
        MeshReconstructionRun(
            request, RunStatus.FAILED, _stage(StageStatus.FAILED, exit_code=7), "working/mesh"
        )
    with pytest.raises(MeshReconstructionError, match="does not match"):
        MeshReconstructionRun(request, RunStatus.SUCCEEDED, _stage(), "working/other")


def test_result_keeps_authority_scale_and_all_provenance_immutable() -> None:
    request = _request()
    result = normalize_mesh_reconstruction_result(request, _stage())
    data = result.as_dict()

    assert result.authority_class == "RECONSTRUCTION_OBSERVATION"
    assert result.scale_state is ScaleState.RELATIVE
    assert data["source_digest"] == request.source_digest
    assert data["plan_digest"] == request.plan_digest
    assert data["dense_configuration_digest"] == request.dense_configuration_digest
    assert data["dense_request_digest"] == request.dense_request_digest
    assert data["configuration_digest"] == request.configuration_digest
    assert data["request_digest"] == request.request_digest
    assert "Scan Master" in " ".join(result.limitations)


def test_metric_unverified_scale_is_preserved_but_verified_scale_is_not_claimed() -> None:
    request = MeshReconstructionRequest.from_dense_run(
        _dense_run(scale_state=ScaleState.METRIC_UNVERIFIED)
    )
    result = normalize_mesh_reconstruction_result(request, _stage())
    assert result.scale_state is ScaleState.METRIC_UNVERIFIED


def test_result_rejects_non_stage_runner_output() -> None:
    def runner(*_: object, **__: object) -> object:
        return "not-a-stage-result"

    with pytest.raises(MeshReconstructionError, match="stage runner"):
        execute_openmvs_mesh(_request(), "ReconstructMesh.exe", _probe(), stage_runner=runner)  # type: ignore[arg-type]
