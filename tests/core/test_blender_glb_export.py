from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path

import pytest
from tests.core.test_blender_real_scene_smoke import _hybrid_sources

from packlab_core.blender_glb_export import (
    BlenderGlbExportError,
    BlenderGlbExportRequest,
    build_blender_glb_export_runner,
    run_blender_glb_export,
    validate_glb_bytes,
)
from packlab_core.blender_scene_package import BlenderScenePackage


def _minimal_glb(*, uri: bool = False) -> bytes:
    document = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "PackLabComponent_package-body"}],
        "materials": [{"name": "visual"}],
        "textures": [{"source": 0}],
        "images": [{"bufferView": 0, "mimeType": "image/png"}],
        "bufferViews": [{"buffer": 0, "byteLength": 4}],
        "buffers": [{"byteLength": 4}],
    }
    if uri:
        document["images"][0] = {"uri": "https://example.invalid/label.png"}
    chunk = json.dumps(document, separators=(",", ":")).encode()
    chunk += b" " * ((4 - len(chunk) % 4) % 4)
    binary = b"test"
    total = 12 + 8 + len(chunk) + 8 + len(binary)
    return (
        b"glTF"
        + struct.pack("<II", 2, total)
        + struct.pack("<II", len(chunk), 0x4E4F534A)
        + chunk
        + struct.pack("<II", len(binary), 0x004E4942)
        + binary
    )


def _fixture(tmp_path: Path):
    package = _hybrid_sources(tmp_path)
    return package


def test_glb_validator_checks_container_embedded_media_and_stable_names() -> None:
    facts = validate_glb_bytes(_minimal_glb())
    assert facts["node_names"] == ["PackLabComponent_package-body"]
    assert facts["material_count"] == facts["texture_count"] == facts["image_count"] == 1
    assert facts["all_images_embedded"] is True
    with pytest.raises(BlenderGlbExportError, match="glb_external_uri_forbidden"):
        validate_glb_bytes(_minimal_glb(uri=True))
    with pytest.raises(BlenderGlbExportError, match="glb_header_invalid"):
        validate_glb_bytes(b"not-glb")


def test_export_request_rejects_unsafe_paths_and_invalid_timeout() -> None:
    with pytest.raises(BlenderGlbExportError, match="glb_export_relative_path_invalid"):
        BlenderGlbExportRequest(output_relative_path="../unsafe.glb")
    with pytest.raises(BlenderGlbExportError, match="glb_export_paths_must_differ"):
        BlenderGlbExportRequest(
            output_relative_path="exports/a.glb", sidecar_relative_path="exports/a.glb"
        )
    with pytest.raises(BlenderGlbExportError, match="glb_export_timeout_invalid"):
        BlenderGlbExportRequest(timeout_seconds=float("inf"))


def test_export_runner_refuses_substituted_scene_runner(tmp_path: Path) -> None:
    package = _fixture(tmp_path)
    unsafe_runner = b"print('not the PackLab validator')"
    identity = {
        "contract": package.contract,
        "schema_version": package.schema_version,
        "manifest_sha256": hashlib.sha256(package.manifest_bytes).hexdigest(),
        "runner_sha256": hashlib.sha256(unsafe_runner).hexdigest(),
    }
    unsafe_id = (
        "blender-scene-package:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
                "ascii"
            )
        ).hexdigest()
    )
    forged = BlenderScenePackage(
        revision_id=unsafe_id,
        manifest_bytes=package.manifest_bytes,
        runner_script=unsafe_runner,
    )
    with pytest.raises(BlenderGlbExportError, match="glb_export_runner_untrusted"):
        build_blender_glb_export_runner(forged)


def test_export_invocation_handles_failure_timeout_and_missing_marker(tmp_path: Path) -> None:
    executable = tmp_path / "blender.exe"
    runner_script = tmp_path / "runner.py"
    executable.write_bytes(b"fixture")
    runner_script.write_text("pass", encoding="utf-8")

    def timed_out(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("blender", 1)

    with pytest.raises(BlenderGlbExportError, match="blender_glb_export_timed_out"):
        run_blender_glb_export(
            executable,
            runner_script,
            tmp_path,
            packlab_commit="a" * 40,
            packlab_version="0.1.0",
            timeout_seconds=1,
            runner=timed_out,
        )

    def failed(*_args, **_kwargs):
        return subprocess.CompletedProcess(["blender"], 4, "", "private path")

    with pytest.raises(BlenderGlbExportError, match="blender_glb_export_process_failed") as failure:
        run_blender_glb_export(
            executable,
            runner_script,
            tmp_path,
            packlab_commit="a" * 40,
            packlab_version="0.1.0",
            timeout_seconds=1,
            runner=failed,
        )
    assert "private path" not in str(failure.value)

    def no_marker(*_args, **_kwargs):
        return subprocess.CompletedProcess(["blender"], 0, "completed without export", "")

    with pytest.raises(
        BlenderGlbExportError, match="blender_glb_export_semantic_validation_failed"
    ):
        run_blender_glb_export(
            executable,
            runner_script,
            tmp_path,
            packlab_commit="a" * 40,
            packlab_version="0.1.0",
            timeout_seconds=1,
            runner=no_marker,
        )


@pytest.mark.skipif(
    os.environ.get("PACKLAB_REAL_BLENDER_SMOKE") != "1",
    reason="set PACKLAB_REAL_BLENDER_SMOKE=1 to export a GLB with approved Blender 5.2.2",
)
def test_real_blender_exports_glb_with_embedded_artwork_and_authority_sidecar(
    tmp_path: Path,
) -> None:
    executable = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
    if not executable.is_file():
        pytest.fail("approved_blender_5_2_2_executable_missing")
    package = _fixture(tmp_path)
    request = BlenderGlbExportRequest()
    script = build_blender_glb_export_runner(package, request)
    script_path = tmp_path / "glb_export_runner.py"
    script_path.write_bytes(script)
    assert compile(script, "packlab-glb-export-runner.py", "exec")
    completed = run_blender_glb_export(
        executable,
        script_path,
        tmp_path,
        sidecar_relative_path=request.sidecar_relative_path,
        packlab_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parents[2], text=True
        ).strip(),
        packlab_version="0.1.0",
    )
    assert "PACKLAB_BLENDER_GLB_EXPORT_VALID" in completed.stdout
    output_path = tmp_path / request.output_relative_path
    sidecar_path = tmp_path / request.sidecar_relative_path
    glb = output_path.read_bytes()
    parsed = validate_glb_bytes(glb)
    sidecar_bytes = sidecar_path.read_bytes()
    sidecar = json.loads(sidecar_bytes)
    assert sidecar["output"]["sha256"] == hashlib.sha256(glb).hexdigest()
    assert sidecar["output"]["byte_length"] == len(glb) > 100
    assert sidecar["output"]["media_type"] == "model/gltf-binary"
    assert sidecar["scene_package_revision_id"] == package.revision_id
    assert sidecar["scene_package_sha256"] == package.manifest()["content_sha256"]
    assert sidecar["component_id"] == "package-body"
    assert sidecar["stable_component_name"] == "PackLabComponent_package-body"
    assert sidecar["source_revisions_and_digests"]["coordinate_unit"] == "mm_unverified"
    assert len(sidecar["artwork_source_bindings"]) == 3
    assert all(
        binding["artwork"]["content_sha256"]
        and binding["assignment"]["revision_id"]
        and binding["mapping"]["revision_id"]
        for binding in sidecar["artwork_source_bindings"]
    )
    assert sidecar["output"]["all_images_embedded"] is True
    assert sidecar["output"]["external_uri_count"] == 0
    assert sidecar["output"]["texture_count"] >= 3
    assert sidecar["output"]["image_count"] >= 1
    assert sidecar["output"]["material_count"] >= 4
    provenance = sidecar["m14_render_provenance"]
    assert provenance["contract"] == "packlab.m14-render-provenance.v1"
    assert (
        provenance["identity_payload"]["packlab"]["commit"]
        == subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parents[2], text=True
        ).strip()
    )
    assert provenance["identity_payload"]["render"]["device"] == "NOT_APPLICABLE_EXPORT_ONLY"
    assert provenance["identity_payload"]["outputs"][0]["sha256"] == hashlib.sha256(glb).hexdigest()
    assert provenance["limitations"]["cross_hardware_pixel_identity_guaranteed"] is False
    assert str(tmp_path) not in json.dumps(provenance)
    assert any(name.startswith("PackLabComponent_") for name in parsed["node_names"])
    assert any(name.startswith("PackLabLabelOverlay_") for name in parsed["node_names"])
    assert sidecar["authority_limits"]["derived_presentation_only"] is True
    assert sidecar["authority_limits"]["physical_accuracy_inferred"] is False
    assert sidecar["authority_limits"]["manufacturing_approval_inferred"] is False
    assert sidecar["network_access"] == "NONE"
    assert sidecar["automatic_downloads"] is False
    assert str(tmp_path) not in sidecar_bytes.decode("utf-8")
