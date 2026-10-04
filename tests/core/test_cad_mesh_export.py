from __future__ import annotations

import json
import struct
from dataclasses import replace

import pytest
from tests.core.test_cad_brep import _inputs, _model

from packlab_core.assembly_hierarchy_export import AssemblyHierarchyExportHandoff
from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.cad_mesh_export import CadMeshExportError, export_design_model_obj_glb
from packlab_core.cad_preview import tessellate_brep_preview
from packlab_core.reconstruction import ScaleState


def _export_inputs(scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED):
    model, profile, operation = _inputs(scale_state)
    representation = revolve_design_model_to_brep(model, profile, operation)
    preview = tessellate_brep_preview(model, representation)
    return model, representation, preview


def _parse_glb(path):
    data = path.read_bytes()
    magic, version, total_length = struct.unpack_from("<4sII", data)
    assert (magic, version, total_length) == (b"glTF", 2, len(data))
    json_length, json_kind = struct.unpack_from("<I4s", data, 12)
    assert json_kind == b"JSON"
    document = json.loads(data[20 : 20 + json_length].decode("ascii"))
    binary_header = 20 + json_length
    binary_length, binary_kind = struct.unpack_from("<I4s", data, binary_header)
    assert binary_kind == b"BIN\x00"
    assert binary_header + 8 + binary_length == len(data)
    return document, data[binary_header + 8 :]


def test_obj_and_glb_are_deterministic_named_and_provenance_bound(tmp_path) -> None:
    model, representation, preview = _export_inputs()
    obj_a, glb_a = tmp_path / "a.obj", tmp_path / "a.glb"
    obj_b, glb_b = tmp_path / "b.obj", tmp_path / "b.glb"

    first = export_design_model_obj_glb(model, representation, preview, obj_a, glb_a)
    second = export_design_model_obj_glb(model, representation, preview, obj_b, glb_b)

    assert obj_a.read_bytes() == obj_b.read_bytes()
    assert glb_a.read_bytes() == glb_b.read_bytes()
    assert first.export_id == second.export_id
    assert first.obj_sha256 == second.obj_sha256
    assert first.glb_sha256 == second.glb_sha256
    lines = obj_a.read_text(encoding="ascii").splitlines()
    metadata = json.loads(lines[1].removeprefix("# source_metadata="))
    assert lines[2] == f"o {first.semantic_part_name}"
    assert lines[3] == f"g {first.semantic_part_name}"
    assert sum(line.startswith("v ") for line in lines) == len(preview.mesh.vertices)
    faces = [line for line in lines if line.startswith("f ")]
    assert len(faces) == len(preview.mesh.triangles)
    assert all(
        1 <= int(index) <= len(preview.mesh.vertices)
        for line in faces
        for index in line[2:].split()
    )
    assert metadata["sourceDesignModelRevisionId"] == model.revision_id
    assert metadata["sourceCadBrepRevisionId"] == representation.revision_id
    assert metadata["sourceCadBrepGeometrySha256"] == representation.geometry_sha256
    assert metadata["sourceCadPreviewRevisionId"] == preview.revision_id
    assert metadata["parentAuthority"]["revisionId"] == representation.parent_authority_revision_id
    assert metadata["physicalAccuracyValidationStatus"] == "DEFERRED_OWNER_VALIDATION"
    assert metadata["moldUseAuthorized"] is False
    assert metadata["featureMapping"]
    assert first.semantic_part_name == "bottle-body-profile"


@pytest.mark.parametrize(
    ("scale_state", "coordinate_unit", "viewer_scale", "viewer_unit"),
    (
        (ScaleState.RELATIVE, "reconstruction_units", 1.0, "relative_viewer_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified", 0.001, "meters"),
    ),
)
def test_units_and_glb_transform_are_explicit_and_reversible(
    tmp_path, scale_state, coordinate_unit, viewer_scale, viewer_unit
) -> None:
    model, representation, preview = _export_inputs(scale_state)
    result = export_design_model_obj_glb(
        model, representation, preview, tmp_path / "unit.obj", tmp_path / "unit.glb"
    )
    document, binary = _parse_glb(tmp_path / "unit.glb")
    node = document["nodes"][0]
    metadata = node["extras"]
    transform = metadata["sourceToViewerTransform"]

    assert result.scale_state == scale_state.value
    assert result.coordinate_unit == coordinate_unit
    assert metadata["scaleState"] == scale_state.value
    assert metadata["coordinateUnit"] == coordinate_unit
    assert metadata["physicalAccuracyValidationStatus"] == "DEFERRED_OWNER_VALIDATION"
    assert metadata["moldUseAuthorized"] is False
    assert metadata["physicalAccuracyInferred"] is False
    assert transform["reversible"] is True
    assert transform["sourceCoordinatesPreservedInBuffer"] is True
    assert transform["viewerUnit"] == viewer_unit
    assert transform["scale"] == [viewer_scale] * 3
    assert transform["inverseScale"] == [1.0 / viewer_scale] * 3
    assert all(
        pytest.approx(scale * inverse) == 1.0
        for scale, inverse in zip(transform["scale"], transform["inverseScale"])
    )
    assert node.get("scale", [1.0, 1.0, 1.0]) == [viewer_scale] * 3
    assert len(binary) >= document["bufferViews"][1]["byteOffset"]
    assert metadata["sourceCadPreviewRevisionId"] == preview.revision_id


def test_glb_has_valid_accessors_and_triangle_indices(tmp_path) -> None:
    model, representation, preview = _export_inputs()
    export_design_model_obj_glb(
        model, representation, preview, tmp_path / "mesh.obj", tmp_path / "mesh.glb"
    )
    document, binary = _parse_glb(tmp_path / "mesh.glb")
    position_view, index_view = document["bufferViews"]
    position_accessor, index_accessor = document["accessors"]
    assert position_accessor["count"] == len(preview.mesh.vertices)
    assert index_accessor["count"] == len(preview.mesh.triangles) * 3
    assert len(binary) >= position_view["byteLength"] + index_view["byteLength"]
    index_format = "<H" if index_accessor["componentType"] == 5123 else "<I"
    index_size = struct.calcsize(index_format)
    flat_indices = tuple(
        struct.unpack_from(index_format, binary, index_view["byteOffset"] + offset)[0]
        for offset in range(0, index_view["byteLength"], index_size)
    )
    assert len(flat_indices) == index_accessor["count"]
    assert all(index < len(preview.mesh.vertices) for index in flat_indices)
    position_data = binary[
        position_view["byteOffset"] : position_view["byteOffset"] + position_view["byteLength"]
    ]
    parsed_positions = tuple(
        struct.unpack_from("<3f", position_data, offset)
        for offset in range(0, len(position_data), 12)
    )
    assert parsed_positions == tuple(
        tuple(struct.unpack("<3f", struct.pack("<3f", *vertex))) for vertex in preview.mesh.vertices
    )
    primitive = document["meshes"][0]["primitives"][0]
    assert primitive["mode"] == 4
    assert primitive["attributes"]["POSITION"] == 0
    assert primitive["indices"] == 1
    assert document["nodes"][0]["name"] == document["meshes"][0]["name"]


def test_stale_preview_and_mismatched_model_reject_before_publication(tmp_path) -> None:
    model, representation, preview = _export_inputs()
    stale_preview = replace(preview, source_brep_revision_id="cad-brep:stale")
    with pytest.raises(CadMeshExportError, match="cad_mesh_preview_provenance_mismatch"):
        export_design_model_obj_glb(
            model, representation, stale_preview, tmp_path / "stale.obj", tmp_path / "stale.glb"
        )
    other_model = _model(ScaleState.METRIC_UNVERIFIED, "standalone", "distinct-export-model")
    with pytest.raises(CadMeshExportError, match="cad_mesh_model_revision_mismatch"):
        export_design_model_obj_glb(
            other_model, representation, preview, tmp_path / "other.obj", tmp_path / "other.glb"
        )
    assert not (tmp_path / "stale.obj").exists()
    assert not (tmp_path / "stale.glb").exists()


def test_metadata_only_assembly_handoff_is_not_a_geometry_source(tmp_path) -> None:
    model, representation, _preview = _export_inputs()
    handoff = AssemblyHierarchyExportHandoff("assembly-hierarchy-handoff:test", "{}")
    with pytest.raises(CadMeshExportError, match="assembly_geometry_source_not_available"):
        export_design_model_obj_glb(
            model, representation, handoff, tmp_path / "assembly.obj", tmp_path / "assembly.glb"
        )
    assert not (tmp_path / "assembly.obj").exists()
    assert not (tmp_path / "assembly.glb").exists()


def test_existing_output_is_not_overwritten(tmp_path) -> None:
    model, representation, preview = _export_inputs()
    obj_path, glb_path = tmp_path / "exists.obj", tmp_path / "exists.glb"
    obj_path.write_bytes(b"owner")
    with pytest.raises(CadMeshExportError, match="cad_mesh_export_destination_exists"):
        export_design_model_obj_glb(model, representation, preview, obj_path, glb_path)
    assert obj_path.read_bytes() == b"owner"
    assert not glb_path.exists()
