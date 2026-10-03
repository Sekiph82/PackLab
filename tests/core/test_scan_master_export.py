from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import replace

import pytest

from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.scan_master_export import (
    ScanMasterExportError,
    ScanMasterExportRequest,
    ScanMasterTextureAsset,
    export_scan_master,
)

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
MESH = TriangleMeshData(
    ((0.125, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
    ((1.0, 0.5, 0.0), (0.0, 1.0, 0.5), (0.25, 0.5, 1.0)),
    ((0.0, 0.0, 1.0),) * 3,
)


def _revision(
    *, scale_state: str = ScaleState.METRIC_UNVERIFIED.value, authority: str = "SCAN_MASTER"
):
    revision_id = f"scan-master:{hashlib.sha256(b'scan-r1').hexdigest()}"
    manifest = {
        "scan_master_revision_id": revision_id,
        "project_id": PROJECT,
        "authority_class": authority,
        "raw_capture_revision_id": "capture-r1",
        "reconstruction_revision_id": "reconstruction-r1",
        "parent_object_geometry_revision_id": "object-r1",
        "scale_provenance_id": "scale-provenance-r1",
        "scale_state": ScaleState(scale_state).value,
        "output_geometry_sha256": mesh_sha256(MESH),
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "known_limitations": ["physical accuracy remains unverified"],
        "coverage_gaps": ["lower rear surface not observed"],
    }
    return ScanMasterRevision(revision_id, PROJECT, MESH, manifest)


def _request(tmp_path, revision=None, *, formats=("ply", "obj", "glb"), textures=(), **overrides):
    revision = _revision() if revision is None else revision
    values = {
        "scan_master": revision,
        "selected_scan_master_revision_id": revision.revision_id,
        "project_root": tmp_path,
        "destination_relative_dir": "export/scan-master/r1",
        "formats": formats,
        "texture_assets": textures,
    }
    values.update(overrides)
    return ScanMasterExportRequest(**values)


def test_deterministic_ply_obj_glb_exports_and_manifest_are_provenance_bound(tmp_path) -> None:
    revision = _revision()
    first = export_scan_master(_request(tmp_path, revision))
    second = export_scan_master(
        _request(tmp_path, revision, destination_relative_dir="export/scan-master/r2")
    )
    first_manifest = json.loads(first.manifest_path.read_text(encoding="ascii"))
    second_manifest = json.loads(second.manifest_path.read_text(encoding="ascii"))
    assert first_manifest == second_manifest
    assert first_manifest["scan_master_revision_id"] == revision.revision_id
    assert first_manifest["source_geometry_sha256"] == mesh_sha256(MESH)
    assert first_manifest["units"] == "mm_unverified"
    assert first_manifest["scale_state"] == ScaleState.METRIC_UNVERIFIED.value
    assert first_manifest["scale_provenance_id"] == "scale-provenance-r1"
    assert first_manifest["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert first_manifest["mold_use_authorized"] is False
    assert first_manifest["texture_status"] == "NOT_AVAILABLE"
    assert "mm" not in first_manifest["units"] or first_manifest["units"] == "mm_unverified"
    for filename in ("scan-master.ply", "scan-master.obj", "scan-master.glb"):
        first_bytes = (first.output_directory / filename).read_bytes()
        second_bytes = (second.output_directory / filename).read_bytes()
        assert first_bytes == second_bytes
        output = next(row for row in first_manifest["formats"] if row["path"] == filename)
        assert hashlib.sha256(first_bytes).hexdigest() == output["sha256"]
    ply = (first.output_directory / "scan-master.ply").read_text(encoding="ascii")
    assert "element vertex 3" in ply and "element face 1" in ply
    obj = (first.output_directory / "scan-master.obj").read_text(encoding="ascii")
    assert obj.count("\nv ") == 3 and "\nf 1//1 2//2 3//3\n" in obj
    glb = (first.output_directory / "scan-master.glb").read_bytes()
    magic, version, total_length = struct.unpack("<4sII", glb[:12])
    json_length, json_type = struct.unpack("<I4s", glb[12:20])
    glb_json = json.loads(glb[20 : 20 + json_length])
    assert (magic, version, total_length, json_type) == (b"glTF", 2, len(glb), b"JSON")
    extras = glb_json["meshes"][0]["extras"]
    assert extras["coordinateUnit"] == "mm_unverified"
    assert extras["scaleState"] == ScaleState.METRIC_UNVERIFIED.value
    assert glb_json["meshes"][0]["primitives"][0]["attributes"].keys() == {
        "POSITION",
        "NORMAL",
        "COLOR_0",
    }


def test_original_texture_is_digest_checked_preserved_as_unmapped_sidecar(tmp_path) -> None:
    image = b"\x89PNG\r\n\x1a\nfixture"
    texture = ScanMasterTextureAsset(
        "working/reconstruction/r1/texture.png",
        hashlib.sha256(image).hexdigest(),
        image,
        "reconstruction-r1",
    )
    result = export_scan_master(_request(tmp_path, textures=(texture,)))
    manifest = json.loads(result.manifest_path.read_text(encoding="ascii"))
    assert (result.output_directory / "textures" / "texture.png").read_bytes() == image
    assert manifest["texture_status"] == "SIDECARS_WITHOUT_SURFACE_MAPPING"
    assert manifest["textures"][0]["source_sha256"] == hashlib.sha256(image).hexdigest()
    assert manifest["textures"][0]["surface_mapping_status"] == (
        "UNAVAILABLE_NO_UV_COORDINATES_IN_SCAN_MASTER_CONTRACT"
    )


def test_selected_revision_authority_texture_and_publication_boundaries_fail_closed(
    tmp_path,
) -> None:
    revision = _revision()
    with pytest.raises(ScanMasterExportError, match="selected_scan_master_revision_mismatch"):
        _request(tmp_path, revision, selected_scan_master_revision_id="scan-master:other")
    with pytest.raises(ScanMasterExportError, match="scan_master_authority_or_provenance_invalid"):
        _request(tmp_path, _revision(authority="PREVIEW_PROXY"))
    with pytest.raises(ScanMasterExportError, match="scan_master_authority_or_provenance_invalid"):
        _request(tmp_path, _revision(scale_state=ScaleState.METRIC_VERIFIED.value))
    bad_texture = ScanMasterTextureAsset(
        "working/reconstruction/r1/generated.png",
        hashlib.sha256(b"x").hexdigest(),
        b"x",
        "reconstruction-r1",
    )
    with pytest.raises(ScanMasterExportError, match="texture_asset_authority_invalid"):
        replace(bad_texture, generated=True)
    with pytest.raises(ScanMasterExportError, match="texture_asset_digest_mismatch"):
        replace(bad_texture, data=b"different")
    collision_request = _request(tmp_path, revision)
    export_scan_master(collision_request)
    with pytest.raises(ScanMasterExportError, match="already_exists"):
        export_scan_master(collision_request)
    with pytest.raises(ScanMasterExportError, match="must_be_under_export"):
        _request(tmp_path, revision, destination_relative_dir="derived/scan-master/r1")
