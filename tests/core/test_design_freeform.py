from __future__ import annotations

import pytest
from test_design_operations import _model

import packlab_core.design_freeform as freeform
from packlab_core.design_freeform import (
    FreeformCageError,
    create_freeform_cage,
    deform_design_preview,
    edit_freeform_cage,
    identity_control_points,
    resolve_freeform_cage,
)
from packlab_core.design_preview import DesignPreview
from packlab_core.geometry_adapter import TriangleMeshData


def _preview(model, feature_id: str) -> DesignPreview:
    mesh = TriangleMeshData(
        ((0.25, 0.5, 0.5), (0.75, 0.5, 0.5), (1.1, 0.5, 0.5)),
        ((0, 1, 2),),
    )
    return DesignPreview(
        mesh=mesh,
        model_revision_id=model.revision_id,
        scan_master_revision_id=model.fitted_to_scan_master_revision_id,
        scan_master_geometry_sha256=model.scan_master_geometry_sha256,
        parent_binding_revision_id=model.parent_binding_revision_id,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
        feature_vertex_indices=((feature_id, (0, 1, 2)),),
    )


def _create(model, feature_id: str, points=None, weights=None):
    bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
    shape = (2, 2, 2)
    rest = identity_control_points(bounds, shape)
    return create_freeform_cage(
        model,
        affected_feature_id=feature_id,
        region_bounds=bounds,
        lattice_shape=shape,
        control_points=rest if points is None else points,
        control_weights=(1.0,) * 8 if weights is None else weights,
        actor_id="operator-2",
        reason="Add bounded freeform cage.",
        created_at_utc="2026-10-04T10:00:00Z",
    )


def test_identity_cage_is_deterministic_and_preserves_preview_mapping_and_authority() -> None:
    model, features = _model()
    source = _preview(model, features[0].feature_id)
    revised, cage = _create(model, features[0].feature_id)

    first = deform_design_preview(source, revised, cage.cage_feature_id)
    second = deform_design_preview(source, revised, cage.cage_feature_id)

    assert cage == resolve_freeform_cage(revised, cage.cage_feature_id)
    assert first == second
    assert first.mesh == source.mesh
    assert dict(first.feature_vertex_indices)[features[0].feature_id] == (0, 1, 2)
    assert dict(first.feature_vertex_indices)[cage.cage_feature_id] == (0, 1)
    assert first.model_revision_id == revised.revision_id
    assert first.authority_class == "PREVIEW_PROXY"
    assert first.as_dict()["scan_master_promoted"] is False
    assert revised.previous_revision_id == model.revision_id
    assert all(item.feature_kind.value != "freeform-cage" for item in model.features)
    assert "control_points" not in source.as_dict()


def test_cage_deforms_only_local_preview_vertices_and_maps_deformation() -> None:
    model, features = _model()
    source = _preview(model, features[0].feature_id)
    rest = identity_control_points((0.0, 1.0, 0.0, 1.0, 0.0, 1.0), (2, 2, 2))
    moved = list(rest)
    moved[7] = (1.0, 0.8, 1.0)
    revised, cage = _create(model, features[0].feature_id, tuple(moved))

    output = deform_design_preview(source, revised, cage.cage_feature_id)
    mapping = dict(output.feature_vertex_indices)

    assert output.mesh.vertices[0] != source.mesh.vertices[0]
    assert output.mesh.vertices[1] != source.mesh.vertices[1]
    assert output.mesh.vertices[2] == source.mesh.vertices[2]
    assert mapping[features[0].feature_id] == (0, 1, 2)
    assert mapping[cage.cage_feature_id] == (0, 1)
    assert revised.scan_master_geometry_sha256 == model.scan_master_geometry_sha256
    assert output.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert output.mold_use_authorized is False


def test_cage_bounds_weights_and_control_point_work_are_bounded() -> None:
    model, features = _model()
    rest = identity_control_points((0.0, 1.0, 0.0, 1.0, 0.0, 1.0), (2, 2, 2))
    outside = list(rest)
    outside[0] = (-0.01, 0.0, 0.0)
    with pytest.raises(FreeformCageError, match="control_point_outside_region"):
        _create(model, features[0].feature_id, tuple(outside))
    with pytest.raises(FreeformCageError, match="weight_out_of_range"):
        _create(model, features[0].feature_id, weights=(1.1,) * 8)
    with pytest.raises(FreeformCageError, match="lattice_shape_invalid"):
        create_freeform_cage(
            model,
            affected_feature_id=features[0].feature_id,
            region_bounds=(0, 1, 0, 1, 0, 1),
            lattice_shape=(9, 2, 2),
            control_points=rest,
            control_weights=(1.0,) * 8,
            actor_id="operator-2",
            reason="Reject unbounded cage.",
            created_at_utc="2026-10-04T10:00:00Z",
        )


def test_cage_edits_are_versioned_recoverable_and_reject_stale_previews() -> None:
    model, features = _model()
    source = _preview(model, features[0].feature_id)
    original_model = model
    revised, cage = _create(model, features[0].feature_id)
    rest = list(cage.control_points)
    rest[7] = (1.0, 0.8, 1.0)
    edited, edited_cage = edit_freeform_cage(
        revised,
        cage.cage_feature_id,
        control_points=tuple(rest),
        control_weights=cage.control_weights,
        actor_id="operator-2",
        reason="Move one cage control point.",
        created_at_utc="2026-10-04T10:01:00Z",
    )

    first = deform_design_preview(source, edited, cage.cage_feature_id)
    repeated = deform_design_preview(source, edited, cage.cage_feature_id)
    assert first == repeated
    assert edited_cage == resolve_freeform_cage(edited, cage.cage_feature_id)
    assert edited.previous_revision_id == revised.revision_id
    assert revised.previous_revision_id == original_model.revision_id
    assert deform_design_preview(source, revised, cage.cage_feature_id).mesh == source.mesh
    with pytest.raises(FreeformCageError, match="preview_parent_or_authority_invalid"):
        deform_design_preview(
            _preview(revised, features[0].feature_id), edited, cage.cage_feature_id
        )


def test_cage_rejects_work_outside_its_declared_region() -> None:
    model, features = _model()
    points = TriangleMeshData(
        ((1.01, 0.5, 0.5), (0.5, 0.5, 0.5), (0.75, 0.5, 0.5)),
        ((0, 1, 2),),
    )
    source = _preview(model, features[0].feature_id)
    source = DesignPreview(
        mesh=points,
        model_revision_id=source.model_revision_id,
        scan_master_revision_id=source.scan_master_revision_id,
        scan_master_geometry_sha256=source.scan_master_geometry_sha256,
        parent_binding_revision_id=source.parent_binding_revision_id,
        scale_state=source.scale_state,
        coordinate_unit=source.coordinate_unit,
        physical_accuracy_validation_status=source.physical_accuracy_validation_status,
        mold_use_authorized=source.mold_use_authorized,
        feature_vertex_indices=source.feature_vertex_indices,
    )
    revised, cage = _create(model, features[0].feature_id)
    output = deform_design_preview(source, revised, cage.cage_feature_id)
    assert output.mesh.vertices[0] == source.mesh.vertices[0]


def test_cage_preview_work_bound_rejects_oversized_preview(monkeypatch) -> None:
    model, features = _model()
    source = _preview(model, features[0].feature_id)
    revised, cage = _create(model, features[0].feature_id)
    monkeypatch.setattr(freeform, "MAX_CAGE_PREVIEW_VERTICES", 2)
    with pytest.raises(FreeformCageError, match="preview_work_bound_exceeded"):
        deform_design_preview(source, revised, cage.cage_feature_id)
