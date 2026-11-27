"""Owner build 2026-11-27: OpenMVS TextureMesh crashed (0xC0000005) and failed the build."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tests.studio.test_build_model import PLY, FakeBackend, _import, _pump, _window
from tests.transfer.test_loopback_receiver import _package

from packlab_core.reconstruction import CancelToken, ReconstructionStageResult, StageStatus
from packlab_core.reconstruction_orchestrator import ReconstructionStageExecution
from packlab_studio import build_model, i18n
from packlab_studio.build_model import TEXTURE_OUTCOMES, ColmapOpenMvsBackend
from packlab_studio.jobs import JobState
from packlab_studio.measure_design import companion_mesh_path
from packlab_studio.model_viewer import ModelViewerView
from packlab_studio.navigation import Route

CRASH = 3221225477  # 0xC0000005 access violation, as Windows reports it


def _texture_stage(monkeypatch, tmp_path: Path, outcomes: list[str], cancel: CancelToken):
    """Run only the texture stage against a fake TextureMesh; outcomes per call."""
    mvs = tmp_path / "outputs/mvs"
    mvs.mkdir(parents=True)
    (mvs / "scene_refined.ply").write_text(PLY, encoding="ascii")
    calls: list[tuple[str, ...]] = []

    def fake(stage_id, args, *, cancel_event=None, cwd=None):
        calls.append(tuple(args))
        outcome = outcomes[len(calls) - 1]
        name = args[args.index("-o") + 1].removesuffix(".mvs")
        if outcome == "cancel":
            cancel.cancel()
            return ReconstructionStageResult(
                stage_id,
                StageStatus.CANCELLED,
                None,
                0.5,
                cancelled=True,
                failure_reason="stage cancelled",
            )
        if outcome == "crash":
            (mvs / f"{name}.obj").write_bytes(b"")  # half-written output must not count
            return ReconstructionStageResult(
                stage_id,
                StageStatus.FAILED,
                CRASH,
                2.0,
                "",
                "",
                failure_reason=f"stage exited {CRASH}",
            )
        (mvs / f"{name}.obj").write_text("v 0 0 0\n", encoding="ascii")
        return ReconstructionStageResult(stage_id, StageStatus.SUCCEEDED, 0, 3.0, "ok\n", "")

    monkeypatch.setattr(build_model, "run_reconstruction_stage", fake)
    backend = ColmapOpenMvsBackend(
        tmp_path / "colmap.exe", {"texture_mesh": tmp_path / "TextureMesh.exe"}, quality="high"
    )
    facts: dict[str, object] = {}
    stage = {s.stage_id: s for s in backend.stages(tmp_path, "w/r1", facts)}["texture-mesh"]
    context = type("Context", (), {"cancel": cancel})
    execution: ReconstructionStageExecution = stage.execute(context)  # type: ignore[arg-type]
    return execution, calls, facts


def test_normal_texturing_is_one_unchanged_call(monkeypatch, tmp_path) -> None:
    execution, calls, facts = _texture_stage(monkeypatch, tmp_path, ["ok"], CancelToken())
    assert calls == [
        (
            str(tmp_path / "TextureMesh.exe"),
            "scene_dense.mvs",
            "-m",
            "scene_refined.ply",
            "-o",
            "scene_textured.mvs",
            "--export-type",
            "obj",
        )
    ]
    assert execution.stage_result.status is StageStatus.SUCCEEDED
    assert execution.output_asset_ids == {"textured_mesh": "w/r1/outputs/mvs/scene_textured.obj"}
    assert facts["texture"] == TEXTURE_OUTCOMES[1]
    assert "attempt 1 (scene_textured) produced the model" in execution.stage_result.stdout


def test_crash_then_retry_without_seam_leveling(monkeypatch, tmp_path) -> None:
    execution, calls, facts = _texture_stage(monkeypatch, tmp_path, ["crash", "ok"], CancelToken())
    assert len(calls) == 2
    assert calls[1][-6:] == (
        "--export-type",
        "obj",
        "--global-seam-leveling",
        "0",
        "--local-seam-leveling",
        "0",
    )
    assert "scene_textured_noseam.mvs" in calls[1]
    assert execution.stage_result.status is StageStatus.SUCCEEDED
    assert execution.stage_result.duration_seconds == 5.0
    assert execution.output_asset_ids == {
        "textured_mesh": "w/r1/outputs/mvs/scene_textured_noseam.obj"
    }
    assert facts["texture"] == TEXTURE_OUTCOMES[2]
    stdout = execution.stage_result.stdout
    assert f"attempt 1 (scene_textured) failed: stage exited {CRASH}" in stdout
    assert "attempt 2 (scene_textured_noseam) produced the model" in stdout


def test_two_crashes_finish_with_the_untextured_mesh(monkeypatch, tmp_path) -> None:
    execution, calls, facts = _texture_stage(
        monkeypatch, tmp_path, ["crash", "crash"], CancelToken()
    )
    assert len(calls) == 2
    assert execution.stage_result.status is StageStatus.SUCCEEDED and execution.outputs_verified
    assert execution.output_asset_ids == {"mesh": "w/r1/outputs/mvs/scene_refined.ply"}
    assert facts["texture"] == TEXTURE_OUTCOMES[0]
    assert "texture unavailable" in execution.stage_result.stdout


def test_cancel_during_retry_cancels_the_stage(monkeypatch, tmp_path) -> None:
    execution, calls, facts = _texture_stage(
        monkeypatch, tmp_path, ["crash", "cancel"], CancelToken()
    )
    assert len(calls) == 2
    assert execution.stage_result.status is StageStatus.CANCELLED
    assert not execution.outputs_verified and "texture" not in facts


class UntexturedBackend(FakeBackend):
    """Fake engines whose texture stage ends as the real fallback does after two crashes."""

    def stages(self, workspace_dir, workspace_asset, facts):
        definitions = list(super().stages(workspace_dir, workspace_asset, facts))
        mvs = workspace_dir / "outputs/mvs"

        def texture(context):
            mvs.mkdir(parents=True, exist_ok=True)
            (mvs / "scene_refined.ply").write_text(PLY, encoding="ascii")
            facts["texture"] = TEXTURE_OUTCOMES[0]
            return ReconstructionStageExecution(
                "texture-mesh",
                ReconstructionStageResult("texture-mesh", StageStatus.SUCCEEDED, 0, 0.01),
                {"mesh": f"{workspace_asset}/outputs/mvs/scene_refined.ply"},
                outputs_verified=True,
            )

        definitions[-1] = replace(definitions[-1], execute=texture)
        return tuple(definitions)


def test_untextured_build_succeeds_with_a_plain_limit_message(
    monkeypatch, tmp_path, repo_root
) -> None:
    package = _package(tmp_path / "scan.packscan", repo_root)
    app, window, inbox, builds = _window(monkeypatch, tmp_path, UntexturedBackend())
    monkeypatch.setattr(i18n, "_current", "tr")  # after startup picked the saved language
    try:
        _import(inbox, package)
        _pump(app, lambda: builds.result is not None)
        result = builds.result
        assert window.job_manager.jobs()[0].state is JobState.SUCCEEDED
        assert result is not None and result.status == "succeeded"
        assert result.textured_mesh_path is None and result.model_path is not None
        assert result.facts["texture"] == TEXTURE_OUTCOMES[0]
        assert "Doku yok" in builds.status.text() and builds.open_button.isEnabled()
        viewer = window.route_stack.views[Route.MODEL_VIEWER]
        assert isinstance(viewer, ModelViewerView) and "scene_dense.ply" in viewer.status.text()
        # Measure/parts take the refined mesh as the companion of a real build's dense cloud.
        mvs = result.workspace_dir / "outputs/mvs"
        assert companion_mesh_path(mvs / "scene_dense.ply") == mvs / "scene_refined.ply"
    finally:
        window.close()
        app.processEvents()
