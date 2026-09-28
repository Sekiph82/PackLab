from __future__ import annotations

import hashlib
import json

import pytest
from test_texture_reconstruction import _request, _stage

from packlab_core.reconstruction import StageStatus
from packlab_core.reconstruction_export import (
    ReconstructionExportError,
    TexturedMeshExportRequest,
    export_textured_mesh,
)
from packlab_core.texture_reconstruction import normalize_texture_mesh_result


def _run(*, status: StageStatus = StageStatus.SUCCEEDED):
    request = _request()
    exit_code = 0 if status is StageStatus.SUCCEEDED else 7
    return normalize_texture_mesh_result(request, _stage(status, exit_code=exit_code))


def _export_request(tmp_path, run=None, *, output_name: str = "preview.obj", **overrides):
    source_asset_id = f"{run.output_asset_id}.obj"
    source_path = tmp_path / source_asset_id
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_bytes = b"# PackLab deterministic preview\nv 0 0 0\n"
    source_path.write_bytes(source_bytes)
    values = {
        "run": run,
        "project_root": tmp_path,
        "source_path": source_path,
        "source_asset_id": source_asset_id,
        "source_output_digest": hashlib.sha256(source_bytes).hexdigest(),
        "destination_relative_dir": "derived/previews/r1",
        "output_name": output_name,
        "format": "obj",
    }
    values.update(overrides)
    return TexturedMeshExportRequest(**values)


def test_success_is_byte_preserving_atomic_and_provenance_bound(tmp_path) -> None:
    run = _run()
    request = _export_request(tmp_path, run)
    result = export_textured_mesh(request)

    assert result.output_path.read_bytes() == b"# PackLab deterministic preview\nv 0 0 0\n"
    assert result.manifest_path.is_file()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_revision"] == run.source_revision
    assert manifest["source_request_digest"] == run.request_digest
    assert manifest["source_configuration_digest"] == run.configuration_digest
    assert manifest["conversion_digest"] == result.conversion_digest
    assert manifest["authority_class"] == "RECONSTRUCTION_OBSERVATION"


def test_failed_or_cancelled_inputs_and_aliases_are_rejected(tmp_path) -> None:
    for status in (StageStatus.FAILED, StageStatus.CANCELLED):
        run = _run(status=status)
        with pytest.raises(ReconstructionExportError, match="successful"):
            _export_request(tmp_path / status.value, run)

    run = _run()
    with pytest.raises(ReconstructionExportError, match="source identity"):
        _export_request(tmp_path, run, source_asset_id="raw/capture.obj")


def test_unsupported_private_collision_and_digest_boundaries_fail_closed(tmp_path) -> None:
    run = _run()
    with pytest.raises(ReconstructionExportError, match="format conversion"):
        export_textured_mesh(
            _export_request(tmp_path, run, output_name="preview.ply", format="ply")
        )
    with pytest.raises(ReconstructionExportError, match="private"):
        _export_request(tmp_path, run, destination_relative_dir="derived/private")
    with pytest.raises(ReconstructionExportError, match="overwrite"):
        _export_request(tmp_path, run, overwrite=True)

    request = _export_request(tmp_path, run)
    export_textured_mesh(request)
    with pytest.raises(ReconstructionExportError, match="already exists"):
        export_textured_mesh(request)
    with pytest.raises(ReconstructionExportError, match="digest"):
        export_textured_mesh(
            _export_request(tmp_path / "tampered", run, source_output_digest="0" * 64)
        )


def test_publication_failure_leaves_final_identity_absent(tmp_path, monkeypatch) -> None:
    run = _run()
    request = _export_request(tmp_path, run)
    import packlab_core.reconstruction_export as export_module

    original_replace = export_module.os.replace

    def fail_replace(source, target):
        if target.__str__().replace("\\", "/").endswith("derived/previews/r1"):
            raise OSError("injected publication failure")
        return original_replace(source, target)

    monkeypatch.setattr(export_module.os, "replace", fail_replace)
    with pytest.raises(ReconstructionExportError, match="publication"):
        export_textured_mesh(request)
    assert not (tmp_path / "derived" / "previews" / "r1").exists()
