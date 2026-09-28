from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import cast

import pytest
from test_mesh_reconstruction import _dense_run
from test_mesh_reconstruction import _request as _mesh_request
from test_mesh_reconstruction import _stage as _mesh_stage

from packlab_core.engine_probe import EngineProbeResult, EngineProbeStatus, EngineVersion
from packlab_core.mesh_reconstruction import (
    MeshReconstructionRequest,
    normalize_mesh_reconstruction_result,
)
from packlab_core.mesh_refinement import (
    DEFAULT_REFINED_MESH_OUTPUT_ASSET_ID,
    MESH_REFINEMENT_STAGE_ID,
    InvalidMeshRefinementRequest,
    MeshRefinementConfig,
    MeshRefinementError,
    MeshRefinementRequest,
    MeshRefinementRun,
    UnsupportedMeshRefinementOption,
    build_openmvs_mesh_refinement_command,
    execute_openmvs_mesh_refinement,
    normalize_mesh_refinement_result,
)
from packlab_core.reconstruction import (
    ReconstructionStageResult,
    RunStatus,
    ScaleState,
    StageStatus,
)


def _mesh_run(*, status: StageStatus = StageStatus.SUCCEEDED):
    mesh_request = _mesh_request()
    return normalize_mesh_reconstruction_result(mesh_request, _mesh_stage(status))


def _request(configuration: MeshRefinementConfig | None = None) -> MeshRefinementRequest:
    return MeshRefinementRequest.from_mesh_run(_mesh_run(), configuration)


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
    cancelled: object | None = None,
    stage_id: str = MESH_REFINEMENT_STAGE_ID,
    stdout: str = "mesh cleaned without geometry claims",
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


def test_request_requires_successful_mesh_and_preserves_provenance() -> None:
    request = _request()
    payload = json.loads(request.serialize())

    assert request.input_mesh_asset_id == "working/reconstruction/openmvs/mesh"
    assert request.output_asset_id == DEFAULT_REFINED_MESH_OUTPUT_ASSET_ID
    assert request.output_asset_id != request.input_mesh_asset_id
    assert request.source_revision == request.mesh_run.request.source_revision
    assert request.source_digest == request.mesh_run.source_digest
    assert request.dense_request_digest == request.mesh_run.dense_request_digest
    assert request.mesh_request_digest == request.mesh_run.request_digest
    assert payload["authority_class"] == "RECONSTRUCTION_OBSERVATION"
    assert payload["scale_state"] == ScaleState.RELATIVE.value
    assert "C:" not in request.serialize()

    with pytest.raises(InvalidMeshRefinementRequest, match="successful"):
        MeshRefinementRequest.from_mesh_run(_mesh_run(status=StageStatus.FAILED))
    with pytest.raises(InvalidMeshRefinementRequest, match="differ"):
        MeshRefinementRequest.from_mesh_run(
            _mesh_run(),
            MeshRefinementConfig(
                refined_mesh_output_asset_id="working/reconstruction/openmvs/mesh"
            ),
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"refined_mesh_output_asset_id": "C:/private/mesh"},
        {"refined_mesh_output_asset_id": "/private/mesh"},
        {"refined_mesh_output_asset_id": "working/../mesh"},
        {"refined_mesh_output_asset_id": "working/mesh\\file"},
        {"refined_mesh_output_asset_id": "private/mesh"},
        {"decimate": 0},
        {"decimate": 1.01},
        {"decimate": float("nan")},
        {"decimate": float("inf")},
        {"target_face_num": -1},
        {"target_face_num": True},
        {"close_holes": False},
        {"smooth": -1},
        {"remove_spurious": -0.01},
        {"remove_spurious": 10**400},
        {"edge_length": float("inf")},
        {"remove_spikes": 1},
        {"crop_to_roi": "true"},
        {"roi_border": float("nan")},
    ],
)
def test_invalid_refinement_domains_and_collisions_fail_closed(
    overrides: dict[str, object],
) -> None:
    with pytest.raises((InvalidMeshRefinementRequest, UnsupportedMeshRefinementOption)):
        MeshRefinementConfig.from_overrides(overrides)


def test_valid_clean_domain_edges_are_accepted() -> None:
    config = MeshRefinementConfig.from_overrides(
        {
            "decimate": 0.001,
            "target_face_num": 0,
            "remove_spurious": 0,
            "remove_spikes": False,
            "close_holes": 0,
            "smooth": 0,
            "edge_length": 0,
            "roi_border": -2.5,
            "crop_to_roi": True,
        }
    )
    assert config.decimate == 0.001
    assert config.target_face_num == 0
    assert config.remove_spurious == 0.0
    assert config.remove_spikes is False
    assert config.close_holes == 0
    assert config.smooth == 0
    assert config.edge_length == 0.0
    assert config.roi_border == -2.5


def test_unknown_and_caller_controlled_options_are_rejected() -> None:
    for overrides in (
        {"--mesh-file": "working/input"},
        {"openmvs_options": {"--mesh-export": True}},
        {"extra_args": ("--export-type", "obj")},
    ):
        with pytest.raises(UnsupportedMeshRefinementOption):
            MeshRefinementConfig.from_overrides(overrides)


def test_command_mapping_matches_pinned_clean_option_order() -> None:
    request = _request(
        MeshRefinementConfig(
            refined_mesh_output_asset_id="working/reconstruction/openmvs/mesh-refined-custom",
            decimate=0.5,
            target_face_num=1234,
            remove_spurious=4.5,
            remove_spikes=False,
            close_holes=7,
            smooth=3,
            edge_length=0.25,
            roi_border=-1.5,
            crop_to_roi=False,
        )
    )
    assert build_openmvs_mesh_refinement_command(request, "ReconstructMesh.exe") == (
        "ReconstructMesh.exe",
        "--mesh-file",
        "working/reconstruction/openmvs/mesh",
        "--output-file",
        "working/reconstruction/openmvs/mesh-refined-custom",
        "--decimate",
        "0.5",
        "--target-face-num",
        "1234",
        "--remove-spurious",
        "4.5",
        "--remove-spikes",
        "0",
        "--close-holes",
        "7",
        "--smooth",
        "3",
        "--edge-length",
        "0.25",
        "--roi-border",
        "-1.5",
        "--crop-to-roi",
        "0",
    )


def test_command_rejects_invalid_executable_without_discovery() -> None:
    with pytest.raises(InvalidMeshRefinementRequest):
        build_openmvs_mesh_refinement_command(_request(), "\x00")


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
def test_execution_requires_matching_valid_refinement_probe(probe: EngineProbeResult) -> None:
    with pytest.raises(UnsupportedMeshRefinementOption):
        execute_openmvs_mesh_refinement(_request(), "ReconstructMesh.exe", probe)
    with pytest.raises(UnsupportedMeshRefinementOption, match="does not match"):
        execute_openmvs_mesh_refinement(_request(), "other.exe", _probe())


def test_execution_uses_existing_stage_boundary_and_propagates_controls() -> None:
    calls: list[tuple[str, tuple[str, ...], object, object, object, object]] = []

    def runner(stage_id: str, args: tuple[str, ...], **kwargs: object) -> ReconstructionStageResult:
        calls.append(
            (
                stage_id,
                args,
                kwargs["timeout"],
                kwargs["cancel_event"],
                kwargs["cwd"],
                kwargs["env"],
            )
        )
        return _stage()

    event = threading.Event()
    cwd = Path("working")
    env = {"PACKLAB_TEST_ENV": "1"}
    result = execute_openmvs_mesh_refinement(
        _request(),
        "ReconstructMesh.exe",
        _probe(),
        timeout=12.5,
        cancel_event=event,
        cwd=cwd,
        env=env,
        stage_runner=runner,
    )

    assert result.status is RunStatus.SUCCEEDED
    assert result.output_asset_id == DEFAULT_REFINED_MESH_OUTPUT_ASSET_ID
    assert calls[0][0] == MESH_REFINEMENT_STAGE_ID
    assert calls[0][2:] == (12.5, event, cwd, env)


def test_success_never_parses_mesh_or_infers_quality() -> None:
    result = normalize_mesh_refinement_result(
        _request(), _stage(stdout="faces=999999 quality=perfect vertices=999999")
    )
    data = result.as_dict()
    assert result.status is RunStatus.SUCCEEDED
    assert result.output_asset_id == result.request.output_asset_id
    assert "point_count" not in data
    assert "triangle_count" not in data
    assert "quality" not in data


def test_failed_and_cancelled_runs_never_expose_refined_output() -> None:
    request = _request()
    failed = normalize_mesh_refinement_result(request, _stage(StageStatus.FAILED, exit_code=7))
    cancelled = normalize_mesh_refinement_result(
        request, _stage(StageStatus.CANCELLED, exit_code=None)
    )
    assert failed.status is RunStatus.FAILED
    assert failed.output_asset_id is None
    assert cancelled.status is RunStatus.CANCELLED
    assert cancelled.output_asset_id is None


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
        _stage(stdout=cast(str, 3)),
    ],
)
def test_malformed_stage_results_fail_closed_without_output(
    stage: ReconstructionStageResult,
) -> None:
    result = normalize_mesh_refinement_result(_request(), stage)
    assert result.status is RunStatus.FAILED
    assert result.output_asset_id is None
    assert result.stage_result.stage_id == MESH_REFINEMENT_STAGE_ID
    assert result.stage_result.status is StageStatus.FAILED


@pytest.mark.parametrize("cancelled", [0, 1, "false", "true"])
@pytest.mark.parametrize(
    ("status", "exit_code"),
    [
        (StageStatus.SUCCEEDED, 0),
        (StageStatus.FAILED, 7),
        (StageStatus.CANCELLED, None),
    ],
)
def test_non_boolean_cancellation_fails_closed_on_every_stage_path(
    status: StageStatus, exit_code: int | None, cancelled: object
) -> None:
    result = normalize_mesh_refinement_result(
        _request(), _stage(status, exit_code=exit_code, cancelled=cancelled)
    )
    assert result.status is RunStatus.FAILED
    assert result.output_asset_id is None
    assert result.stage_result.status is StageStatus.FAILED
    assert result.stage_result.cancelled is False


def test_direct_run_rejects_output_on_failure_and_malformed_cancellation() -> None:
    request = _request()
    with pytest.raises(MeshRefinementError, match="cannot expose output"):
        MeshRefinementRun(
            request, RunStatus.FAILED, _stage(StageStatus.FAILED, exit_code=7), "working/mesh"
        )
    with pytest.raises(MeshRefinementError, match="cancellation flag must be a boolean"):
        MeshRefinementRun(
            request,
            RunStatus.SUCCEEDED,
            _stage(cancelled=0),
            DEFAULT_REFINED_MESH_OUTPUT_ASSET_ID,
        )


def test_result_keeps_authority_scale_and_predecessor_digests() -> None:
    request = _request()
    result = normalize_mesh_refinement_result(request, _stage())
    data = result.as_dict()

    assert result.authority_class == "RECONSTRUCTION_OBSERVATION"
    assert result.scale_state is ScaleState.RELATIVE
    assert data["source_revision"] == request.source_revision
    assert data["source_digest"] == request.source_digest
    assert data["dense_request_digest"] == request.dense_request_digest
    assert data["mesh_request_digest"] == request.mesh_request_digest
    assert data["request_digest"] == request.request_digest
    assert "Scan Master" in " ".join(result.limitations)
    assert "METRIC_VERIFIED" not in data["scale_state"]


def test_metric_unverified_scale_is_preserved_without_claiming_verified_scale() -> None:
    mesh_request = MeshReconstructionRequest.from_dense_run(
        _dense_run(scale_state=ScaleState.METRIC_UNVERIFIED)
    )
    mesh_run = normalize_mesh_reconstruction_result(mesh_request, _mesh_stage())
    request = MeshRefinementRequest.from_mesh_run(mesh_run)
    result = normalize_mesh_refinement_result(request, _stage())
    assert result.scale_state is ScaleState.METRIC_UNVERIFIED


def test_result_rejects_non_stage_runner_output() -> None:
    def runner(*_: object, **__: object) -> object:
        return "not-a-stage-result"

    with pytest.raises(MeshRefinementError, match="stage runner"):
        execute_openmvs_mesh_refinement(  # type: ignore[arg-type]
            _request(), "ReconstructMesh.exe", _probe(), stage_runner=runner
        )
