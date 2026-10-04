from __future__ import annotations

import hashlib
import importlib

import pytest
from tests.core.test_jerrycan_grip_indent import _inputs as _indent_inputs
from tests.core.test_jerrycan_handle_opening import _opening

from packlab_core.cad_adapter import (
    _SHAPE_REGISTRY,
    CadShapeBuild,
    _shape_for_handle,
    shape_handle_for_model,
)
from packlab_core.cad_boolean import CadBooleanError, cut_design_model_feature
from packlab_core.cad_brep import _representation_from_lineage
from packlab_core.design_model import FeatureKind
from packlab_core.jerrycan_grip_indent import (
    GripIndentSide,
    create_jerrycan_grip_indent,
    measure_jerrycan_grip_indent_evidence,
)
from packlab_core.reconstruction import ScaleState


def _box_brep(model, bounds: tuple[float, float, float, float, float, float]):
    primitive = importlib.import_module("OCP.BRepPrimAPI")
    gp = importlib.import_module("OCP.gp")
    shape = primitive.BRepPrimAPI_MakeBox(
        gp.gp_Pnt(bounds[0], bounds[2], bounds[4]),
        bounds[1] - bounds[0],
        bounds[3] - bounds[2],
        bounds[5] - bounds[4],
    ).Shape()
    handle = shape_handle_for_model("cad-shape:test-box", model)
    _SHAPE_REGISTRY[handle.handle_id] = ("test-fixture", shape)
    return _representation_from_lineage(
        model,
        "cad-cut-fixture:box",
        (model.features[0].feature_id,),
        CadShapeBuild(handle, hashlib.sha256(b"fixture-box").hexdigest(), 1),
    )


def test_handle_opening_cut_is_deterministic_and_feature_linked() -> None:
    _scan, base_model, _detection, model, feature = _opening()
    parent = _box_brep(base_model, (0.0, 1.0, 0.0, 4.0, 0.0, 8.0))
    original = _shape_for_handle(parent.shape_handle)
    original_model = model.as_dict()
    first = cut_design_model_feature(model, parent, feature.feature_id)
    second = cut_design_model_feature(model, parent, feature.feature_id)

    assert first.status == "SUCCEEDED"
    assert first.operation_type == "CUT_HANDLE_OPENING_THROUGH_BODY"
    assert first.operation_id == second.operation_id
    assert first.representation == second.representation
    assert first.representation is not None
    assert first.representation.source_design_model_revision_id == model.revision_id
    assert first.representation.source_input_ids == (
        parent.revision_id,
        feature.feature_id,
        base_model.features[0].feature_id,
    )
    assert first.body_feature_ids == (base_model.features[0].feature_id,)
    assert first.as_dict()["cut_extent_policy"] == "through_body_brep_bounds"
    assert first.as_dict()["feature_hidden_extent_inferred"] is False
    assert first.as_dict()["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert _shape_for_handle(parent.shape_handle) is original
    assert model.as_dict() == original_model


def test_grip_indent_cut_uses_explicit_profile_depth_and_side() -> None:
    scan, base_model, body = _indent_inputs()
    evidence = measure_jerrycan_grip_indent_evidence(
        scan,
        base_model,
        body_feature_id=body.feature_id,
        region_id="left-panel-grip",
        region_bounds=(1.0, 1.0, 3.0, 3.0),
        ring_width=0.5,
        side=GripIndentSide.FRONT,
    )
    model = create_jerrycan_grip_indent(
        scan,
        base_model,
        evidence,
        profile=((1.25, 1.25), (2.75, 1.25), (2.75, 2.75), (1.25, 2.75)),
        actor_id="fixture-operator",
        reason="Create synthetic supported indent feature.",
        created_at_utc="2026-10-04T12:02:00Z",
    )
    feature = next(item for item in model.features if item.feature_kind is FeatureKind.GRIP_INDENT)
    parent = _box_brep(base_model, (0.0, 4.0, 0.0, 4.0, 0.0, 4.0))

    result = cut_design_model_feature(model, parent, feature.feature_id)

    assert result.status == "SUCCEEDED"
    assert result.operation_type == "CUT_GRIP_INDENT"
    assert result.representation is not None
    assert result.representation.coordinate_unit == "mm_unverified"
    assert result.representation.scale_state is ScaleState.METRIC_UNVERIFIED


@pytest.mark.parametrize(
    "bounds",
    [
        (0.0, 1.0, 10.0, 14.0, 0.0, 8.0),  # tool lies outside body
        (0.0, 1.0, 0.0, 4.0, 4.5, 8.0),  # separate, nonintersecting volume
    ],
)
def test_outside_or_nonintersecting_tool_is_an_explicit_failure(bounds) -> None:
    _scan, base_model, _detection, model, feature = _opening()
    parent = _box_brep(base_model, bounds)
    before = parent.geometry_sha256
    original_model = model.as_dict()

    result = cut_design_model_feature(model, parent, feature.feature_id)

    assert result.status == "FAILED"
    assert result.representation is None
    assert result.failure_diagnostics == ("cad_boolean_tool_does_not_intersect_body",)
    assert parent.geometry_sha256 == before
    assert model.as_dict() == original_model


def test_invalid_tool_is_reported_without_mutating_parent() -> None:
    _scan, base_model, _detection, model, feature = _opening()
    parent = _box_brep(base_model, (0.0, 1.0, 0.0, 4.0, 0.0, 8.0))
    shape_before = _shape_for_handle(parent.shape_handle)

    from packlab_core.cad_adapter import CadAdapterError, build_polygon_prism_cut

    with pytest.raises(CadAdapterError, match="tool_invalid"):
        build_polygon_prism_cut(
            model,
            parent.shape_handle,
            operation_id="cad-cut:invalid",
            input_ids=(feature.feature_id,),
            profile=((0.5, 0.0, 0.0), (0.5, 1.0, 1.0)),
            extrusion=(1.0, 0.0, 0.0),
        )
    assert _shape_for_handle(parent.shape_handle) is shape_before


def test_raw_scan_mesh_cannot_be_passed_as_boolean_authority() -> None:
    _scan, base_model, _detection, model, feature = _opening()
    with pytest.raises(CadBooleanError, match="cad_brep_representation_required"):
        cut_design_model_feature(model, object(), feature.feature_id)  # type: ignore[arg-type]
