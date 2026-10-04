from __future__ import annotations

import importlib

import pytest
from tests.core.test_cad_brep import _inputs

from packlab_core.cad_adapter import _registered_shape_build, _shape_for_handle
from packlab_core.cad_brep import _representation_from_lineage, revolve_design_model_to_brep
from packlab_core.cad_preview import CadPreviewError, tessellate_brep_preview
from packlab_core.reconstruction import ScaleState


def _representation(scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED):
    model, profile, operation = _inputs(scale_state)
    representation = revolve_design_model_to_brep(model, profile, operation)
    return model, profile, operation, representation


def test_coarse_and_fine_tolerance_are_deterministic_and_fine_is_more_detailed() -> None:
    model, _profile, _operation, representation = _representation()
    coarse = tessellate_brep_preview(
        model,
        representation,
        linear_deflection=0.5,
        angular_deflection=0.8,
    )
    fine = tessellate_brep_preview(
        model,
        representation,
        linear_deflection=0.02,
        angular_deflection=0.15,
    )
    fine_repeat = tessellate_brep_preview(
        model,
        representation,
        linear_deflection=0.02,
        angular_deflection=0.15,
    )

    assert len(fine.mesh.triangles) > len(coarse.mesh.triangles)
    assert fine.mesh.vertices == fine_repeat.mesh.vertices
    assert fine.mesh.triangles == fine_repeat.mesh.triangles
    assert fine.revision_id == fine_repeat.revision_id


def test_preview_bounds_match_brep_within_requested_deflection() -> None:
    model, _profile, _operation, representation = _representation()
    preview = tessellate_brep_preview(model, representation, linear_deflection=0.1)

    assert preview.bounds_consistent
    assert preview.maximum_bounds_delta <= preview.linear_deflection
    expected_bounds = (-5.0, 5.0, -5.0, 5.0, 0.0, 100.0)
    assert all(
        abs(actual - expected) <= preview.linear_deflection
        for actual, expected in zip(preview.preview_bounds, expected_bounds)
    )


def test_preview_work_limits_are_validated_and_enforced() -> None:
    model, _profile, _operation, representation = _representation()

    with pytest.raises(CadPreviewError, match="triangle_work_bound_exceeded"):
        tessellate_brep_preview(model, representation, maximum_triangles=1)
    with pytest.raises(CadPreviewError, match="face_work_bound_exceeded"):
        tessellate_brep_preview(model, representation, maximum_faces=1)
    with pytest.raises(CadPreviewError, match="linear_deflection_out_of_bounds"):
        tessellate_brep_preview(model, representation, linear_deflection=0.0)


def test_supported_feature_mapping_covers_preview_only_at_whole_solid_scope() -> None:
    model, _profile, operation, representation = _representation()
    shape_build = _registered_shape_build(
        model,
        operation.operation_id,
        operation.input_ids,
        _shape_for_handle(representation.shape_handle),
        1,
    )
    mapped_representation = _representation_from_lineage(
        model,
        operation.operation_id,
        operation.input_ids,
        shape_build,
        source_feature_ids=(model.features[0].feature_id,),
    )

    preview = tessellate_brep_preview(model, mapped_representation)
    reference = preview.feature_references[0]

    assert reference.status == "MAPPED"
    assert reference.mapping_scope == "whole_output_solid_preview"
    assert reference.preview_triangle_indices == tuple(range(len(preview.mesh.triangles)))
    ambiguous = tessellate_brep_preview(model, representation).feature_references
    assert all(item.status == "AMBIGUOUS" for item in ambiguous)
    assert all(not item.preview_triangle_indices for item in ambiguous)


def test_invalid_open_shell_brep_is_rejected_before_meshing() -> None:
    model, _profile, operation, representation = _representation()
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

    with pytest.raises(CadPreviewError, match="valid_closed_solid_required"):
        tessellate_brep_preview(model, invalid_representation)


@pytest.mark.parametrize(
    ("scale_state", "expected_unit"),
    (
        (ScaleState.RELATIVE, "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ),
)
def test_preview_preserves_authority_units_and_never_promotes_scan_master(
    scale_state: ScaleState, expected_unit: str
) -> None:
    model, _profile, _operation, representation = _representation(scale_state)
    model_before = model.as_dict()
    brep_digest = representation.geometry_sha256

    preview = tessellate_brep_preview(model, representation)
    record = preview.as_dict()

    assert preview.source_brep_revision_id == representation.revision_id
    assert preview.source_design_model_revision_id == model.revision_id
    assert preview.parent_kind == representation.parent_kind.value
    assert preview.parent_authority_revision_id == representation.parent_authority_revision_id
    assert preview.scale_state == scale_state.value
    assert preview.coordinate_unit == expected_unit
    assert preview.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert preview.mold_use_authorized is False
    assert record["authority_class"] == "PREVIEW_PROXY"
    assert record["disposable"] is True
    assert record["brep_truth_modified"] is False
    assert record["design_model_replaced"] is False
    assert record["scan_master_promoted"] is False
    assert record["physical_accuracy_inferred"] is False
    assert record["manufacturing_suitability_inferred"] is False
    assert record["geometry"] == {
        "vertices": [list(vertex) for vertex in preview.mesh.vertices],
        "triangles": [list(triangle) for triangle in preview.mesh.triangles],
    }
    assert model.as_dict() == model_before
    assert representation.geometry_sha256 == brep_digest
