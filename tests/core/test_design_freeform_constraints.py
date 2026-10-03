from __future__ import annotations

import pytest
from test_design_operations import _model

from packlab_core.design_dimensions import (
    DimensionAxis,
    create_overall_dimensions_revision,
)
from packlab_core.design_freeform import (
    create_freeform_cage,
    create_freeform_cage_edit_command,
    edit_freeform_cage,
    identity_control_points,
)
from packlab_core.design_freeform_constraints import (
    FreeformAxis,
    FreeformConstraintError,
    constrain_freeform_cage_preview,
    edit_freeform_cage_constrained,
)
from packlab_core.design_history import DesignModelHistory
from packlab_core.design_model import (
    DesignModelParameter,
    ParameterType,
    revise_design_model_revision,
)
from packlab_core.design_preview import DesignPreview
from packlab_core.geometry_adapter import TriangleMeshData

BOUNDS = (0.0, 2.0, 0.0, 0.6, 0.0, 1.2)
SHAPE = (4, 3, 3)


def _fixture():
    model, features = _model()
    mating = DesignModelParameter(
        "mating_reference_fixture",
        {"reference_id": "neck-axis-r1", "offset": 0.0},
        ParameterType.OBJECT,
    )
    model = revise_design_model_revision(
        model,
        parameters=(*model.parameters, mating),
        features=model.features,
        actor_id="operator-1",
        reason="Pin mating reference fixture.",
        created_at_utc="2026-10-04T11:00:00Z",
    )
    model = create_overall_dimensions_revision(
        model,
        height=1.2,
        width=2.0,
        depth=0.6,
        actor_id="operator-1",
        reason="Pin protected overall dimensions.",
        created_at_utc="2026-10-04T11:01:00Z",
    )
    vertices = (
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (2.0, 0.6, 0.0),
        (0.0, 0.6, 0.0),
        (0.0, 0.0, 1.2),
        (2.0, 0.0, 1.2),
        (2.0, 0.6, 1.2),
        (0.0, 0.6, 1.2),
        (2.0 / 3.0, 0.3, 0.6),
        (4.0 / 3.0, 0.3, 0.6),
    )
    mesh = TriangleMeshData(
        vertices,
        (
            (0, 1, 2),
            (0, 2, 3),
            (4, 6, 5),
            (4, 7, 6),
            (0, 4, 5),
            (0, 5, 1),
            (1, 5, 6),
            (1, 6, 2),
            (2, 6, 7),
            (2, 7, 3),
            (3, 7, 4),
            (3, 4, 0),
        ),
    )
    source_preview = DesignPreview(
        mesh,
        model.revision_id,
        model.fitted_to_scan_master_revision_id,
        model.scan_master_geometry_sha256,
        model.parent_binding_revision_id,
        model.scale_state,
        model.coordinate_unit,
        model.physical_accuracy_validation_status,
        model.mold_use_authorized,
        ((features[0].feature_id, tuple(range(len(vertices)))),),
    )
    return model, features[0].feature_id, source_preview


def _create(model, feature_id, points=None):
    rest = identity_control_points(BOUNDS, SHAPE)
    return create_freeform_cage(
        model,
        affected_feature_id=feature_id,
        region_bounds=BOUNDS,
        lattice_shape=SHAPE,
        control_points=rest if points is None else points,
        control_weights=(1.0,) * len(rest),
        actor_id="operator-2",
        reason="Add bounded constrained cage.",
        created_at_utc="2026-10-04T11:02:00Z",
    )


def _index(x: int, y: int, z: int) -> int:
    return (z * SHAPE[1] + y) * SHAPE[0] + x


def _asymmetric_points():
    points = list(identity_control_points(BOUNDS, SHAPE))
    x, y, z = points[_index(1, 1, 1)]
    points[_index(1, 1, 1)] = (x, y + 0.05, z)
    return tuple(points)


def test_protected_height_width_and_depth_reject_boundary_shrink() -> None:
    axis_to_coordinate = {
        DimensionAxis.WIDTH: 0,
        DimensionAxis.DEPTH: 1,
        DimensionAxis.HEIGHT: 2,
    }
    for axis, coordinate in axis_to_coordinate.items():
        source, feature_id, preview = _fixture()
        points = list(identity_control_points(BOUNDS, SHAPE))
        minimum = BOUNDS[coordinate * 2]
        for index, point in enumerate(points):
            if point[coordinate] == minimum:
                moved = list(point)
                moved[coordinate] += 0.05
                points[index] = (moved[0], moved[1], moved[2])
        revised, cage = _create(source, feature_id, tuple(points))
        with pytest.raises(
            FreeformConstraintError,
            match=f"protected_dimension_violation:{axis.value}",
        ):
            constrain_freeform_cage_preview(preview, source, revised, cage.cage_feature_id)


def test_symmetric_and_unconstrained_local_deformations_have_exact_diagnostics() -> None:
    source, feature_id, preview = _fixture()
    revised, cage = _create(source, feature_id, _asymmetric_points())
    first_preview, unconstrained = constrain_freeform_cage_preview(
        preview, source, revised, cage.cage_feature_id, symmetry_axes=()
    )
    repeat_preview, repeat = constrain_freeform_cage_preview(
        preview, source, revised, cage.cage_feature_id, symmetry_axes=()
    )
    assert first_preview == repeat_preview
    assert unconstrained == repeat
    assert unconstrained.dimension_residuals == tuple((axis, 0.0) for axis in DimensionAxis)
    assert first_preview.mesh.vertices[8] != preview.mesh.vertices[8]
    assert unconstrained.total_control_scalar_dof == 144
    assert unconstrained.symmetry_constrained_dof == 0
    assert unconstrained.unconstrained_control_scalar_dof == 144

    symmetric_points = list(identity_control_points(BOUNDS, SHAPE))
    for x in (1, 2):
        px, py, pz = symmetric_points[_index(x, 1, 1)]
        symmetric_points[_index(x, 1, 1)] = (px, py + 0.05, pz)
    symmetric_model, symmetric_cage = _create(source, feature_id, tuple(symmetric_points))
    _, diagnostics = constrain_freeform_cage_preview(
        preview,
        source,
        symmetric_model,
        symmetric_cage.cage_feature_id,
        symmetry_axes=(FreeformAxis.X,),
    )
    assert diagnostics.symmetry_residuals[0][0] is FreeformAxis.X
    assert diagnostics.symmetry_residuals[0][1] <= diagnostics.tolerance
    assert diagnostics.symmetry_constrained_dof > 0
    assert diagnostics.unconstrained_control_scalar_dof < diagnostics.total_control_scalar_dof


def test_constrained_edit_api_does_not_return_a_protected_dimension_violation() -> None:
    source, feature_id, preview = _fixture()
    cage_model, cage = _create(source, feature_id)
    points = list(cage.control_points)
    for index, point in enumerate(points):
        if point[0] == BOUNDS[0]:
            points[index] = (point[0] + 0.05, point[1], point[2])
    with pytest.raises(FreeformConstraintError, match="protected_dimension_violation:width"):
        edit_freeform_cage_constrained(
            preview,
            source,
            cage_model,
            cage.cage_feature_id,
            control_points=tuple(points),
            control_weights=cage.control_weights,
            actor_id="operator-2",
            reason="Attempt to shrink protected width.",
            created_at_utc="2026-10-04T11:03:00Z",
        )


def test_enabled_symmetry_rejects_asymmetric_control_edits_and_disabled_symmetry_allows_them() -> (
    None
):
    source, feature_id, preview = _fixture()
    revised, cage = _create(source, feature_id, _asymmetric_points())
    with pytest.raises(FreeformConstraintError, match="freeform_symmetry_violation:x"):
        constrain_freeform_cage_preview(
            preview,
            source,
            revised,
            cage.cage_feature_id,
            symmetry_axes=(FreeformAxis.X,),
        )
    _, diagnostics = constrain_freeform_cage_preview(
        preview, source, revised, cage.cage_feature_id, symmetry_axes=()
    )
    assert diagnostics.symmetry_axes == ()


def test_mating_references_are_pinned_and_changed_values_reject() -> None:
    source, feature_id, preview = _fixture()
    revised, cage = _create(source, feature_id, _asymmetric_points())
    _, diagnostics = constrain_freeform_cage_preview(preview, source, revised, cage.cage_feature_id)
    assert diagnostics.mating_references_preserved is True
    assert diagnostics.mating_reference_parameter_ids == ("mating_reference_fixture",)

    changed = DesignModelParameter(
        "mating_reference_fixture",
        {"reference_id": "neck-axis-r2", "offset": 0.0},
        ParameterType.OBJECT,
    )
    tampered = revise_design_model_revision(
        revised,
        parameters=tuple(
            changed if item.parameter_id == changed.parameter_id else item
            for item in revised.parameters
        ),
        features=revised.features,
        actor_id="operator-2",
        reason="Attempt to move the pinned mating reference.",
        created_at_utc="2026-10-04T11:03:00Z",
    )
    with pytest.raises(FreeformConstraintError, match="freeform_mating_reference_violation"):
        constrain_freeform_cage_preview(preview, source, tampered, cage.cage_feature_id)


def test_cage_control_edit_history_undo_redo_is_compatible() -> None:
    source, feature_id, _preview_value = _fixture()
    cage_model, cage = _create(source, feature_id)
    points = list(cage.control_points)
    px, py, pz = points[_index(1, 1, 1)]
    points[_index(1, 1, 1)] = (px, py + 0.05, pz)
    edited_model, _ = edit_freeform_cage(
        cage_model,
        cage.cage_feature_id,
        control_points=tuple(points),
        control_weights=cage.control_weights,
        actor_id="operator-2",
        reason="Move one cage control point.",
        created_at_utc="2026-10-04T11:04:00Z",
    )
    command = create_freeform_cage_edit_command(cage_model, edited_model, cage.cage_feature_id)
    history = DesignModelHistory(cage_model).apply(
        command,
        actor_id="operator-2",
        reason="Move one cage control point.",
        created_at_utc="2026-10-04T11:04:00Z",
    )
    assert history.current_revision == edited_model
    undone = history.undo(actor_id="operator-2", created_at_utc="2026-10-04T11:05:00Z")
    assert (
        undone.current_revision == cage_model
        or undone.current_revision.parameters == cage_model.parameters
    )
    redone = undone.redo(actor_id="operator-2", created_at_utc="2026-10-04T11:06:00Z")
    assert redone.current_revision.parameters == edited_model.parameters
    assert redone.current_revision.scan_master_geometry_sha256 == source.scan_master_geometry_sha256
