from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import cast

import pytest
from test_mesh_refinement import _mesh_run
from test_mesh_refinement import _stage as _refinement_stage

from packlab_core.engine_probe import EngineProbeResult, EngineProbeStatus, EngineVersion
from packlab_core.mesh_refinement import MeshRefinementRequest, normalize_mesh_refinement_result
from packlab_core.reconstruction import (
    ReconstructionStageResult,
    RunStatus,
    ScaleState,
    StageStatus,
)
from packlab_core.texture_reconstruction import (
    DEFAULT_TEXTURED_MESH_OUTPUT_ASSET_ID,
    TEXTURE_MESH_STAGE_ID,
    InvalidTextureReconstructionRequest,
    TextureReconstructionConfig,
    TextureReconstructionError,
    TextureReconstructionRequest,
    TextureReconstructionRun,
    UnsupportedTextureReconstructionOption,
    build_openmvs_texture_mesh_command,
    execute_openmvs_texture_mesh,
    normalize_texture_mesh_result,
)


def _refinement_run(*, status: StageStatus = StageStatus.SUCCEEDED):
    refinement_request = MeshRefinementRequest.from_mesh_run(_mesh_run())
    return normalize_mesh_refinement_result(refinement_request, _refinement_stage(status))


def _request(
    configuration: TextureReconstructionConfig | None = None,
) -> TextureReconstructionRequest:
    return TextureReconstructionRequest.from_refinement_run(_refinement_run(), configuration)


def _probe(executable: str = "TextureMesh.exe") -> EngineProbeResult:
    return EngineProbeResult(
        "openmvs.TextureMesh",
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
    stage_id: str = TEXTURE_MESH_STAGE_ID,
    duration: object = 0.01,
    stdout: object = "texture stage completed without mesh parsing",
    stderr: object = "",
) -> ReconstructionStageResult:
    return ReconstructionStageResult(
        stage_id,
        status,
        exit_code,
        cast(float, duration),
        stdout=cast(str, stdout),
        stderr=cast(str, stderr),
        cancelled=status is StageStatus.CANCELLED if cancelled is None else cast(bool, cancelled),
        failure_reason=None if status is StageStatus.SUCCEEDED else "stage failed",
    )


def test_request_requires_successful_refinement_and_preserves_provenance() -> None:
    request = _request()
    payload = json.loads(request.serialize())

    assert request.scene_asset_id == "working/reconstruction/openmvs/scene"
    assert request.refined_mesh_asset_id == "working/reconstruction/openmvs/mesh-refined"
    assert request.output_asset_id == DEFAULT_TEXTURED_MESH_OUTPUT_ASSET_ID
    assert request.output_asset_id not in {request.scene_asset_id, request.refined_mesh_asset_id}
    assert request.source_revision == request.refinement_run.source_revision
    assert request.source_digest == request.refinement_run.source_digest
    assert request.plan_digest == request.refinement_run.plan_digest
    assert request.dense_request_digest == request.refinement_run.dense_request_digest
    assert request.mesh_request_digest == request.refinement_run.mesh_request_digest
    assert request.refinement_request_digest == request.refinement_run.request_digest
    assert payload["authority_class"] == "RECONSTRUCTION_OBSERVATION"
    assert payload["scale_state"] == ScaleState.RELATIVE.value
    assert "METRIC_VERIFIED" not in request.serialize()
    assert "C:" not in request.serialize()

    with pytest.raises(InvalidTextureReconstructionRequest, match="successful"):
        TextureReconstructionRequest.from_refinement_run(_refinement_run(status=StageStatus.FAILED))
    with pytest.raises(InvalidTextureReconstructionRequest, match="differ"):
        TextureReconstructionRequest.from_refinement_run(
            _refinement_run(),
            TextureReconstructionConfig(
                textured_mesh_output_asset_id="working/reconstruction/openmvs/mesh-refined"
            ),
        )
    with pytest.raises(InvalidTextureReconstructionRequest, match="differ"):
        TextureReconstructionRequest.from_refinement_run(
            _refinement_run(),
            TextureReconstructionConfig(
                textured_mesh_output_asset_id="working/reconstruction/openmvs/scene"
            ),
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"textured_mesh_output_asset_id": "C:/private/mesh"},
        {"textured_mesh_output_asset_id": "/private/mesh"},
        {"textured_mesh_output_asset_id": "working/../mesh"},
        {"textured_mesh_output_asset_id": "working/mesh\\file"},
        {"textured_mesh_output_asset_id": "private/mesh"},
        {"export_type": "fbx"},
        {"export_type": True},
        {"decimate": -0.01},
        {"decimate": 1.01},
        {"decimate": float("nan")},
        {"decimate": float("inf")},
        {"decimate": True},
        {"close_holes": -1},
        {"close_holes": True},
        {"resolution_level": -1},
        {"min_resolution": False},
        {"virtual_face_images": -1},
        {"texture_size_multiple": True},
        {"outlier_threshold": -0.01},
        {"outlier_threshold": float("nan")},
        {"cost_smoothness_ratio": 1.01},
        {"cost_smoothness_ratio": float("inf")},
        {"global_seam_leveling": 1},
        {"local_seam_leveling": "true"},
        {"patch_packing_heuristic": 101},
        {"patch_packing_heuristic": True},
        {"empty_color": -1},
        {"empty_color": 0x100000000},
        {"empty_color": False},
        {"sharpness_weight": -0.01},
        {"sharpness_weight": 10**400},
        {"ignore_mask_label": -3},
        {"ignore_mask_label": False},
        {"max_texture_size": -1},
        {"max_texture_size": True},
    ],
)
def test_invalid_texture_domains_fail_closed(overrides: dict[str, object]) -> None:
    with pytest.raises(
        (InvalidTextureReconstructionRequest, UnsupportedTextureReconstructionOption)
    ):
        TextureReconstructionConfig.from_overrides(overrides)


def test_valid_texture_domain_edges_are_accepted() -> None:
    config = TextureReconstructionConfig.from_overrides(
        {
            "textured_mesh_output_asset_id": "working/reconstruction/openmvs/custom-textured",
            "export_type": "gltf",
            "decimate": 0,
            "close_holes": 0,
            "resolution_level": 0,
            "min_resolution": 0,
            "virtual_face_images": 0,
            "texture_size_multiple": 0,
            "outlier_threshold": 0,
            "cost_smoothness_ratio": 0,
            "global_seam_leveling": False,
            "local_seam_leveling": False,
            "patch_packing_heuristic": 100,
            "empty_color": 0xFFFFFFFF,
            "sharpness_weight": 0,
            "ignore_mask_label": -2,
            "max_texture_size": 0,
        }
    )
    assert config.decimate == 0.0
    assert config.export_type == "gltf"
    assert config.patch_packing_heuristic == 100
    assert config.empty_color == 0xFFFFFFFF
    assert config.ignore_mask_label == -2


def test_unknown_and_caller_controlled_options_are_rejected() -> None:
    for overrides in (
        {"--input-file": "working/scene"},
        {"openmvs_options": {"--views-file": "private/views"}},
        {"extra_args": ("--cuda-device", "0")},
        {"preserve_output": True},
    ):
        with pytest.raises(UnsupportedTextureReconstructionOption):
            TextureReconstructionConfig.from_overrides(overrides)


def test_command_mapping_matches_pinned_texture_option_order() -> None:
    request = _request(
        TextureReconstructionConfig(
            textured_mesh_output_asset_id="working/reconstruction/openmvs/custom-textured",
            export_type="obj",
            decimate=0.5,
            close_holes=7,
            resolution_level=2,
            min_resolution=320,
            virtual_face_images=3,
            texture_size_multiple=4,
            outlier_threshold=0.25,
            cost_smoothness_ratio=0.75,
            global_seam_leveling=False,
            local_seam_leveling=True,
            patch_packing_heuristic=100,
            empty_color=0x12345678,
            sharpness_weight=1.5,
            ignore_mask_label=-2,
            max_texture_size=4096,
        )
    )
    assert build_openmvs_texture_mesh_command(request, "TextureMesh.exe") == (
        "TextureMesh.exe",
        "--input-file",
        "working/reconstruction/openmvs/scene",
        "--mesh-file",
        "working/reconstruction/openmvs/mesh-refined",
        "--output-file",
        "working/reconstruction/openmvs/custom-textured",
        "--export-type",
        "obj",
        "--decimate",
        "0.5",
        "--close-holes",
        "7",
        "--resolution-level",
        "2",
        "--min-resolution",
        "320",
        "--outlier-threshold",
        "0.25",
        "--cost-smoothness-ratio",
        "0.75",
        "--virtual-face-images",
        "3",
        "--global-seam-leveling",
        "0",
        "--local-seam-leveling",
        "1",
        "--texture-size-multiple",
        "4",
        "--patch-packing-heuristic",
        "100",
        "--empty-color",
        "305419896",
        "--sharpness-weight",
        "1.5",
        "--ignore-mask-label",
        "-2",
        "--max-texture-size",
        "4096",
    )


def test_command_rejects_invalid_executable_without_discovery() -> None:
    with pytest.raises(InvalidTextureReconstructionRequest):
        build_openmvs_texture_mesh_command(_request(), "\x00")


@pytest.mark.parametrize(
    "probe",
    [
        EngineProbeResult(
            "openmvs", "TextureMesh.exe", EngineProbeStatus.VALID, EngineVersion(2, 4, 0), "generic"
        ),
        EngineProbeResult(
            "openmvs.TextureMesh", "TextureMesh.exe", EngineProbeStatus.MISSING, None, "missing"
        ),
        EngineProbeResult(
            "openmvs.TextureMesh",
            "TextureMesh.exe",
            EngineProbeStatus.VALID,
            EngineVersion(2, 3, 0),
            "wrong",
        ),
    ],
)
def test_execution_requires_matching_valid_texture_probe(probe: EngineProbeResult) -> None:
    with pytest.raises(UnsupportedTextureReconstructionOption):
        execute_openmvs_texture_mesh(_request(), "TextureMesh.exe", probe)
    with pytest.raises(UnsupportedTextureReconstructionOption, match="does not match"):
        execute_openmvs_texture_mesh(_request(), "other.exe", _probe())


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
    result = execute_openmvs_texture_mesh(
        _request(),
        "TextureMesh.exe",
        _probe(),
        timeout=12.5,
        cancel_event=event,
        cwd=cwd,
        env=env,
        stage_runner=runner,
    )

    assert result.status is RunStatus.SUCCEEDED
    assert result.output_asset_id == DEFAULT_TEXTURED_MESH_OUTPUT_ASSET_ID
    assert calls[0][0] == TEXTURE_MESH_STAGE_ID
    assert calls[0][2:] == (12.5, event, cwd, env)


def test_success_does_not_parse_mesh_or_infer_texture_quality() -> None:
    result = normalize_texture_mesh_result(
        _request(), _stage(stdout="faces=999 quality=perfect coverage=100% texture=decoded")
    )
    data = result.as_dict()
    assert result.status is RunStatus.SUCCEEDED
    assert result.output_asset_id == result.request.output_asset_id
    assert "point_count" not in data
    assert "triangle_count" not in data
    assert "quality" not in data
    assert "coverage" not in data


def test_failed_and_cancelled_runs_never_expose_textured_output() -> None:
    request = _request()
    failed = normalize_texture_mesh_result(request, _stage(StageStatus.FAILED, exit_code=7))
    cancelled = normalize_texture_mesh_result(
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
        _stage(duration=10**400),
        _stage(stdout=cast(str, 3)),
    ],
)
def test_malformed_stage_results_fail_closed_without_output(
    stage: ReconstructionStageResult,
) -> None:
    result = normalize_texture_mesh_result(_request(), stage)
    assert result.status is RunStatus.FAILED
    assert result.output_asset_id is None
    assert result.stage_result.stage_id == TEXTURE_MESH_STAGE_ID
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
    result = normalize_texture_mesh_result(
        _request(), _stage(status, exit_code=exit_code, cancelled=cancelled)
    )
    assert result.status is RunStatus.FAILED
    assert result.output_asset_id is None
    assert result.stage_result.status is StageStatus.FAILED
    assert result.stage_result.cancelled is False


def test_direct_run_rejects_output_on_failure_and_malformed_cancellation() -> None:
    request = _request()
    with pytest.raises(TextureReconstructionError, match="cannot expose output"):
        TextureReconstructionRun(
            request, RunStatus.FAILED, _stage(StageStatus.FAILED, exit_code=7), "working/textured"
        )
    with pytest.raises(TextureReconstructionError, match="cancellation flag must be a boolean"):
        TextureReconstructionRun(
            request,
            RunStatus.SUCCEEDED,
            _stage(cancelled=0),
            DEFAULT_TEXTURED_MESH_OUTPUT_ASSET_ID,
        )


def test_result_keeps_authority_scale_and_predecessor_digests() -> None:
    request = _request()
    result = normalize_texture_mesh_result(request, _stage())
    data = result.as_dict()

    assert result.authority_class == "RECONSTRUCTION_OBSERVATION"
    assert result.scale_state is ScaleState.RELATIVE
    assert data["source_revision"] == request.source_revision
    assert data["source_digest"] == request.source_digest
    assert data["plan_digest"] == request.plan_digest
    assert data["dense_request_digest"] == request.dense_request_digest
    assert data["mesh_request_digest"] == request.mesh_request_digest
    assert data["refinement_request_digest"] == request.refinement_request_digest
    assert data["configuration_digest"] == request.configuration_digest
