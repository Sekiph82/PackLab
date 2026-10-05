from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from tests.core.test_blender_real_scene_smoke import _hybrid_sources

from packlab_core.blender_render import (
    BlenderRenderError,
    BlenderRenderRequest,
    build_blender_render_runner,
    run_blender_render,
)
from packlab_core.blender_render_preset import create_blender_render_preset


def _package_and_render_job(tmp_path: Path):
    package = _hybrid_sources(tmp_path)
    (tmp_path / "blender_scene_manifest.json").write_bytes(package.manifest_bytes)
    source = package.manifest()["body"]["source"]
    revisions = tuple(
        sorted(
            (key.removesuffix("_revision_id"), value)
            for key, value in source.items()
            if key.endswith("_revision_id")
        )
    )
    preset = create_blender_render_preset(
        (0.0, -0.06, 0.0), (0.1, 0.0, 0.06), "THREE_QUARTER", revisions
    )
    request = BlenderRenderRequest(width=256, height=256, samples=8)
    script = build_blender_render_runner(package, preset, request)
    script_path = tmp_path / "blender_render_runner.py"
    script_path.write_bytes(script)
    return package, preset, request, script_path


def test_render_job_is_static_deterministic_and_contains_no_machine_paths(tmp_path: Path) -> None:
    package = _hybrid_sources(tmp_path)
    source = package.manifest()["body"]["source"]
    revisions = tuple(
        sorted(
            (key.removesuffix("_revision_id"), value)
            for key, value in source.items()
            if key.endswith("_revision_id")
        )
    )
    preset = create_blender_render_preset((0.0, 0.0, 0.0), (0.1, 0.06, 0.06), "FRONT", revisions)
    first = build_blender_render_runner(package, preset, BlenderRenderRequest())
    second = build_blender_render_runner(package, preset, BlenderRenderRequest())
    compile(first, "packlab-render-runner.py", "exec")
    assert first == second
    assert str(tmp_path).encode() not in first
    assert b"PACKLAB_BLENDER_RENDER_VALID" in first
    assert b"subprocess" not in first
    assert b"requests" not in first


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width": 0},
        {"height": 100_000},
        {"samples": 0},
        {"timeout_seconds": float("inf")},
        {"output_relative_path": "../outside.png"},
        {"evidence_relative_path": "C:/private/evidence.json"},
    ],
)
def test_render_request_rejects_unbounded_or_unsafe_settings(kwargs) -> None:
    with pytest.raises(BlenderRenderError):
        BlenderRenderRequest(**kwargs)


def test_process_failure_and_timeout_are_path_free_and_bounded(tmp_path: Path) -> None:
    executable = tmp_path / "blender.exe"
    script = tmp_path / "runner.py"
    executable.write_bytes(b"fake")
    script.write_text("pass", encoding="utf-8")

    def timed_out(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("blender", 1)

    with pytest.raises(BlenderRenderError, match="blender_render_timed_out") as timeout_error:
        run_blender_render(executable, script, tmp_path, runner=timed_out, timeout_seconds=1)
    assert str(tmp_path) not in str(timeout_error.value)

    def failed(*_args, **_kwargs):
        return subprocess.CompletedProcess(["blender"], 2, "", "private path")

    with pytest.raises(BlenderRenderError, match="blender_render_process_failed") as failure:
        run_blender_render(executable, script, tmp_path, runner=failed, timeout_seconds=1)
    assert "private path" not in str(failure.value)

    def no_semantic_result(*_args, **_kwargs):
        return subprocess.CompletedProcess(["blender"], 0, "finished without result", "")

    with pytest.raises(BlenderRenderError, match="blender_render_semantic_validation_failed"):
        run_blender_render(
            executable, script, tmp_path, runner=no_semantic_result, timeout_seconds=1
        )


@pytest.mark.skipif(
    os.environ.get("PACKLAB_REAL_BLENDER_SMOKE") != "1",
    reason="set PACKLAB_REAL_BLENDER_SMOKE=1 to render through approved Blender 5.2.2",
)
def test_real_blender_renders_transparent_product_png_with_semantic_evidence(
    tmp_path: Path,
) -> None:
    executable = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
    if not executable.is_file():
        pytest.fail("approved_blender_5_2_2_executable_missing")
    package, preset, request, script_path = _package_and_render_job(tmp_path)
    completed = run_blender_render(executable, script_path, tmp_path)
    assert "PACKLAB_BLENDER_RENDER_VALID" in completed.stdout, completed.stderr[-2000:]
    output_path = tmp_path / request.output_relative_path
    evidence_path = tmp_path / request.evidence_relative_path
    evidence_bytes = evidence_path.read_bytes()
    evidence = json.loads(evidence_bytes)
    output = evidence["output"]
    image_bytes = output_path.read_bytes()
    assert image_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    assert output["sha256"] == hashlib.sha256(image_bytes).hexdigest()
    assert output["byte_length"] == len(image_bytes) > 64
    assert [output["width"], output["height"]] == [256, 256]
    assert output["alpha_channel"] is True
    assert output["transparent_pixel_count"] > 0
    assert output["visible_pixel_count"] > 0
    assert output["all_mesh_bounds_inside_camera"] is True
    assert evidence["scene_package_revision_id"] == package.revision_id
    assert evidence["scene_package_sha256"] == package.manifest()["content_sha256"]
    assert evidence["render_preset_revision_id"] == preset.revision_id
    assert evidence["settings"]["engine"] == "BLENDER_EEVEE"
    assert evidence["settings"]["transparent_background"] is True
    assert evidence["settings"]["color_mode"] == "RGBA"
    assert evidence["determinism_claim"] == "REPRODUCIBLE_SETTINGS_AND_PROVENANCE_ONLY"
    assert evidence["authority_limits"]["physical_accuracy_inferred"] is False
    assert evidence["authority_limits"]["material_certified"] is False
    assert evidence["network_access"] == "NONE"
    assert evidence["automatic_downloads"] is False
    assert str(tmp_path) not in evidence_bytes.decode("utf-8")
