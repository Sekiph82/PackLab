from __future__ import annotations

import importlib
import json
import math
import struct
from pathlib import Path

import pytest
from tests.core.test_cad_brep import _inputs

from packlab_core.cad_adapter import _registered_shape_build, _shape_for_handle
from packlab_core.cad_brep import _representation_from_lineage, revolve_design_model_to_brep
from packlab_core.cad_stl_export import (
    CadStlExportError,
    CadStlMeshQuality,
    export_design_model_stl,
)
from packlab_core.reconstruction import ScaleState


def _inputs_with_brep(scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED):
    model, profile, operation = _inputs(scale_state)
    representation = revolve_design_model_to_brep(model, profile, operation)
    return model, profile, operation, representation


def test_binary_stl_and_sidecar_are_deterministic_and_provenance_bound(tmp_path) -> None:
    model, _profile, _operation, representation = _inputs_with_brep()
    first_path = tmp_path / "first.stl"
    second_path = tmp_path / "second.stl"

    first = export_design_model_stl(model, representation, first_path)
    second = export_design_model_stl(model, representation, second_path)
    first_sidecar = Path(str(first_path) + ".json")
    second_sidecar = Path(str(second_path) + ".json")
    first_data = first_path.read_bytes()
    sidecar = json.loads(first_sidecar.read_text(encoding="utf-8"))

    assert first.artifact_mode == "BINARY_STL"
    assert first_data == second_path.read_bytes()
    assert first_sidecar.read_bytes() == second_sidecar.read_bytes()
    assert first.artifact_sha256 == second.artifact_sha256
    assert first.sidecar_sha256 == second.sidecar_sha256
    assert first.export_id == second.export_id == sidecar["export_id"]
    assert len(first_data) == 84 + first.triangle_count * 50
    assert int.from_bytes(first_data[80:84], "little") == first.triangle_count
    assert b"mm_unverified" in first_data[:80]
    assert sidecar["source_design_model_revision_id"] == model.revision_id
    assert sidecar["source_brep_revision_id"] == representation.revision_id
    assert sidecar["source_brep_geometry_sha256"] == representation.geometry_sha256
    assert sidecar["parent_authority_revision_id"] == representation.parent_authority_revision_id
    assert sidecar["coordinate_unit"] == "mm_unverified"
    assert sidecar["stl_coordinate_interpretation"] == "millimetres"
    assert sidecar["millimetres_numerically_encoded_from_unverified_design_units"] is True
    assert sidecar["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert sidecar["topology_validation_status"] == first.topology_validation_status
    assert sidecar["artifact_mode"] == "BINARY_STL"
    assert sidecar["feature_mapping"]


def test_mesh_quality_presets_map_to_bounded_deterministic_triangle_counts(tmp_path) -> None:
    model, _profile, _operation, representation = _inputs_with_brep()
    coarse = export_design_model_stl(
        model, representation, tmp_path / "coarse.stl", quality=CadStlMeshQuality.COARSE
    )
    fine = export_design_model_stl(
        model, representation, tmp_path / "fine.stl", quality=CadStlMeshQuality.FINE
    )
    fine_repeat = export_design_model_stl(
        model, representation, tmp_path / "fine-repeat.stl", quality="FINE"
    )

    assert coarse.linear_deflection == 0.5
    assert coarse.angular_deflection == 0.8
    assert fine.linear_deflection == 0.02
    assert fine.angular_deflection == 0.15
    assert fine.triangle_count > coarse.triangle_count
    assert fine_path_bytes(tmp_path / "fine.stl") == fine_path_bytes(tmp_path / "fine-repeat.stl")
    assert fine.artifact_sha256 == fine_repeat.artifact_sha256
    assert fine.quality_preset == "FINE"
    assert fine.maximum_vertices == 250_000
    assert fine.maximum_triangles == 500_000


def test_binary_stl_triangle_coordinates_and_normals_are_sane(tmp_path) -> None:
    model, _profile, _operation, representation = _inputs_with_brep()
    exported = export_design_model_stl(model, representation, tmp_path / "bottle.stl")
    data = (tmp_path / "bottle.stl").read_bytes()
    triangle_count = struct.unpack_from("<I", data, 80)[0]

    assert triangle_count == exported.triangle_count
    for index in range(triangle_count):
        normal_x, normal_y, normal_z, *tail = struct.unpack_from("<12fH", data, 84 + index * 50)
        points = (tail[0:3], tail[3:6], tail[6:9])
        assert all(math.isfinite(value) for value in (normal_x, normal_y, normal_z, *tail[:9]))
        assert math.isclose(math.sqrt(normal_x**2 + normal_y**2 + normal_z**2), 1.0, rel_tol=1e-5)
        assert tail[9] == 0
        edge_a = tuple(points[1][axis] - points[0][axis] for axis in range(3))
        edge_b = tuple(points[2][axis] - points[0][axis] for axis in range(3))
        cross = (
            edge_a[1] * edge_b[2] - edge_a[2] * edge_b[1],
            edge_a[2] * edge_b[0] - edge_a[0] * edge_b[2],
            edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0],
        )
        assert sum(a * b for a, b in zip((normal_x, normal_y, normal_z), cross)) > 0.0


def test_relative_input_fails_closed_without_stl_or_sidecar(tmp_path) -> None:
    model, _profile, _operation, representation = _inputs_with_brep(ScaleState.RELATIVE)
    output = tmp_path / "relative.stl"

    with pytest.raises(CadStlExportError, match="mm_unverified_source_required"):
        export_design_model_stl(model, representation, output)

    assert not output.exists()
    assert not Path(str(output) + ".json").exists()


def test_invalid_shell_brep_is_rejected_before_stl_publication(tmp_path) -> None:
    model, _profile, operation, representation = _inputs_with_brep()
    shape = _shape_for_handle(representation.shape_handle)
    top_exp = importlib.import_module("OCP.TopExp")
    top_abs = importlib.import_module("OCP.TopAbs")
    topods = importlib.import_module("OCP.TopoDS")
    explorer = top_exp.TopExp_Explorer(shape, top_abs.TopAbs_SHELL)
    shell = topods.TopoDS.Shell_s(explorer.Current())
    shape_build = _registered_shape_build(
        model, operation.operation_id, operation.input_ids, shell, 1
    )
    invalid_representation = _representation_from_lineage(
        model,
        operation.operation_id,
        operation.input_ids,
        shape_build,
        source_feature_ids=representation.source_feature_ids,
    )
    output = tmp_path / "invalid.stl"

    with pytest.raises(CadStlExportError, match="valid_closed_solid_required"):
        export_design_model_stl(model, invalid_representation, output)

    assert not output.exists()
    assert not Path(str(output) + ".json").exists()


def test_bounded_work_and_nonproduction_authority_are_explicit(tmp_path) -> None:
    model, _profile, _operation, representation = _inputs_with_brep()

    with pytest.raises(CadStlExportError, match="triangle_work_bound_exceeded"):
        export_design_model_stl(
            model, representation, tmp_path / "bounded.stl", maximum_triangles=1
        )
    exported = export_design_model_stl(model, representation, tmp_path / "normal.stl")
    metadata = exported.as_dict()

    assert metadata["physical_accuracy_inferred"] is False
    assert metadata["print_fit_inferred"] is False
    assert metadata["production_ready_claimed"] is False
    assert metadata["manufacturing_suitability_inferred"] is False
    assert metadata["scan_master_promoted"] is False
    assert metadata["design_model_replaced"] is False
    assert metadata["cad_brep_replaced"] is False
    assert exported.mold_use_authorized is False
    assert exported.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"


def fine_path_bytes(path):
    return path.read_bytes()
