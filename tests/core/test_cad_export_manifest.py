from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from tests.core.test_cad_brep import _inputs

from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.cad_mesh_export import export_design_model_obj_glb
from packlab_core.cad_preview import tessellate_brep_preview
from packlab_core.cad_step_export import export_design_model_step
from packlab_core.cad_stl_export import export_design_model_stl
from packlab_core.reconstruction import ScaleState


def _read_manifest(path: Path) -> dict[str, object]:
    return json.loads(Path(str(path) + ".json").read_text(encoding="utf-8"))


def test_step_stl_obj_glb_share_canonical_path_free_manifest_contract(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    private_test_folder = tmp_path / "private-output-path-sentinel"
    private_test_folder.mkdir()
    step_path = private_test_folder / "bottle.step"
    stl_path = private_test_folder / "bottle.stl"
    obj_path = private_test_folder / "bottle.obj"
    glb_path = private_test_folder / "bottle.glb"

    export_design_model_step(model, representation, step_path, part_name="Bottle Body")
    export_design_model_stl(model, representation, stl_path)
    preview = tessellate_brep_preview(model, representation)
    export_design_model_obj_glb(model, representation, preview, obj_path, glb_path)

    manifests = tuple(_read_manifest(path) for path in (step_path, stl_path, obj_path, glb_path))
    assert tuple(item["format"] for item in manifests) == ("step", "stl", "obj", "glb")
    for path, manifest in zip((step_path, stl_path, obj_path, glb_path), manifests):
        assert manifest["contract"] == "packlab.cad-export-manifest.v1"
        assert re.fullmatch(r"cad-export-manifest:[0-9a-f]{64}", manifest["manifest_id"])
        assert manifest["project_id"] == model.project_id
        assert manifest["export_id"]
        assert manifest["source"]["design_model_revision_id"] == model.revision_id
        assert manifest["source"]["cad_representation_revision_id"] == representation.revision_id
        assert manifest["source"]["cad_geometry_sha256"] == representation.geometry_sha256
        assert manifest["source"]["parent_authority"]["kind"] == model.parent_kind.value
        assert manifest["source"]["coordinate_unit"] == "mm_unverified"
        assert manifest["source"]["scale_state"] == ScaleState.METRIC_UNVERIFIED.value
        assert manifest["topology_validation"]["status"] == "VALID"
        assert manifest["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
        assert manifest["mold_use_authorized"] is False
        assert all(value is False for value in manifest["authority_claims"].values())
        assert manifest["software"]["packlab_version"] == "0.1.0"
        assert re.fullmatch(r"[0-9a-f]{40,64}", manifest["software"]["packlab_commit"])
        assert manifest["software"]["python_binding_version"]
        assert manifest["software"]["occt_kernel_version"]
        assert manifest["artifact"]["sha256"] == manifest["artifact_sha256"]
        assert manifest["artifact"]["byte_length"] == manifest["artifact_size_bytes"]
        assert manifest["artifact"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert manifest["part_names"]
        assert manifest["named_feature_mapping"]
        assert "private-output-path-sentinel" not in json.dumps(manifest)
        assert str(path) not in json.dumps(manifest)

    assert manifests[0]["tessellation"] is None
    assert manifests[1]["tessellation"]["linear_deflection"] > 0
    assert manifests[2]["tessellation"]["linear_deflection"] > 0
    assert manifests[3]["coordinate_transform"]["scale"] == [0.001, 0.001, 0.001]
    assert manifests[3]["coordinate_transform"]["inverse_scale"] == [1000.0, 1000.0, 1000.0]
    assert manifests[1]["stl_coordinate_interpretation"] == "millimetres"
    assert manifests[1]["millimetres_numerically_encoded_from_unverified_design_units"] is True


def test_relative_obj_glb_manifests_remain_relative_and_unscaled(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.RELATIVE)
    representation = revolve_design_model_to_brep(model, profile, operation)
    preview = tessellate_brep_preview(model, representation)
    obj_path, glb_path = tmp_path / "relative.obj", tmp_path / "relative.glb"

    export_design_model_obj_glb(model, representation, preview, obj_path, glb_path)
    obj_manifest, glb_manifest = _read_manifest(obj_path), _read_manifest(glb_path)

    for manifest in (obj_manifest, glb_manifest):
        assert manifest["source"]["coordinate_unit"] == "reconstruction_units"
        assert manifest["source"]["scale_state"] == ScaleState.RELATIVE.value
        assert manifest["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
        assert manifest["mold_use_authorized"] is False
    assert obj_manifest["coordinate_transform"]["scale"] == [1.0, 1.0, 1.0]
    assert glb_manifest["coordinate_transform"]["target_unit"] == "relative_viewer_units"
    assert glb_manifest["coordinate_transform"]["scale"] == [1.0, 1.0, 1.0]
    assert glb_manifest["coordinate_transform"]["inverse_scale"] == [1.0, 1.0, 1.0]


def test_captured_parent_manifest_names_exact_scan_master_binding(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED, "captured")
    representation = revolve_design_model_to_brep(model, profile, operation)
    step_path = tmp_path / "captured.step"

    export_design_model_step(model, representation, step_path, part_name="Captured Body")
    parent_authority = _read_manifest(step_path)["source"]["parent_authority"]

    assert parent_authority["kind"] == "CAPTURED_SCAN_MASTER"
    assert parent_authority["scan_master_binding_revision_id"] == model.parent_binding_revision_id
    assert "root_revision_id" not in parent_authority
