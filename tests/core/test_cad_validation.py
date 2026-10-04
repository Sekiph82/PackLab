from __future__ import annotations

import importlib

from tests.core.test_cad_brep import _inputs as _revolve_inputs
from tests.core.test_cad_loft import _loft_inputs

from packlab_core.cad_adapter import (
    _SHAPE_REGISTRY,
    _registered_shape_build,
    _shape_for_handle,
)
from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.cad_validation import CadValidationError, validate_cad_brep
from packlab_core.reconstruction import ScaleState


def _open_shell_representation():
    model, _profile, _operation = _revolve_inputs(ScaleState.METRIC_UNVERIFIED)
    primitive = importlib.import_module("OCP.BRepPrimAPI")
    top_abs = importlib.import_module("OCP.TopAbs")
    top_exp = importlib.import_module("OCP.TopExp")
    builder_module = importlib.import_module("OCP.BRep")
    topo_ds = importlib.import_module("OCP.TopoDS")
    solid = primitive.BRepPrimAPI_MakeBox(1.0, 2.0, 3.0).Shape()
    explorer = top_exp.TopExp_Explorer(solid, top_abs.TopAbs_FACE)
    faces = []
    while explorer.More():
        faces.append(explorer.Current())
        explorer.Next()
    shell = topo_ds.TopoDS_Shell()
    builder = builder_module.BRep_Builder()
    builder.MakeShell(shell)
    for face in faces[:-1]:
        builder.Add(shell, face)
    shape_build = _registered_shape_build(
        model,
        "cad-shape-test:open-shell",
        (model.features[0].feature_id,),
        shell,
        1,
    )
    from packlab_core.cad_brep import _representation_from_lineage

    return _representation_from_lineage(
        model,
        "cad-operation-test:open-shell",
        (model.features[0].feature_id,),
        shape_build,
    )


def test_valid_revolve_report_is_deterministic_and_preserves_authority() -> None:
    model, profile, operation = _revolve_inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    before_shape = _shape_for_handle(representation.shape_handle)

    first = validate_cad_brep(representation)
    second = validate_cad_brep(representation)

    assert first == second
    assert first.status == "VALID"
    assert first.kernel_valid
    assert first.valid_closed_solid
    assert first.solid_count == 1
    assert first.source_brep_revision_id == representation.revision_id
    assert first.source_design_model_revision_id == model.revision_id
    assert first.source_operation_id == operation.operation_id
    assert first.parent_kind == "STANDALONE_DESIGN_GEOMETRY"
    assert first.coordinate_unit == "mm_unverified"
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False
    assert first.repair_performed is False
    assert _shape_for_handle(representation.shape_handle) is before_shape
    assert first.as_dict()["physical_accuracy_inferred"] is False
    assert first.as_dict()["manufacturing_suitability_inferred"] is False


def test_valid_loft_report_has_closed_single_solid_topology() -> None:
    from packlab_core.cad_brep import loft_design_model_to_brep

    model, sections, operation = _loft_inputs()
    representation = loft_design_model_to_brep(model, sections, operation)

    report = validate_cad_brep(representation)

    assert report.status == "VALID"
    assert report.valid_closed_solid
    assert report.solid_count == 1
    assert report.shell_count >= 1
    assert report.open_edge_count == 0
    assert report.nonmanifold_edge_count == 0


def test_open_shell_reports_open_edges_without_silent_repair() -> None:
    representation = _open_shell_representation()
    shape = _shape_for_handle(representation.shape_handle)
    original_digest = representation.geometry_sha256

    report = validate_cad_brep(representation)

    assert report.status == "INVALID"
    assert not report.valid_closed_solid
    assert report.solid_count == 0
    assert report.shell_count == 1
    assert report.closed_shell_count == 0
    assert report.open_edge_count > 0
    assert "open_shell_detected" in report.failure_diagnostics
    assert "open_or_free_edge_detected" in report.failure_diagnostics
    assert report.repair_performed is False
    assert representation.geometry_sha256 == original_digest
    assert _shape_for_handle(representation.shape_handle) is shape


def test_unavailable_shape_is_reported_as_failure_and_not_repaired() -> None:
    model, profile, operation = _revolve_inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    registered = _SHAPE_REGISTRY.pop(representation.shape_handle.handle_id)
    try:
        first = validate_cad_brep(representation)
        second = validate_cad_brep(representation)
    finally:
        _SHAPE_REGISTRY[representation.shape_handle.handle_id] = registered

    assert first == second
    assert first.status == "FAILED"
    assert first.failure_diagnostics == ("cad_shape_handle_unavailable_in_runtime",)
    assert first.repair_performed is False


def test_wrong_representation_type_is_rejected() -> None:
    try:
        validate_cad_brep(object())  # type: ignore[arg-type]
    except CadValidationError as error:
        assert str(error) == "cad_brep_representation_required"
    else:
        raise AssertionError("non-BREP input was accepted")
