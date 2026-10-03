from __future__ import annotations

import pytest
from test_design_history import _model

from packlab_core.design_dimensions import (
    DIMENSIONS_PARAMETER_ID,
    DesignDimensionsError,
    DimensionAxis,
    create_overall_dimensions_revision,
    revise_overall_dimension,
)
from packlab_core.design_history import DesignModelHistory
from packlab_core.design_model import (
    DesignModelParameter,
    ParameterType,
    revise_design_model_revision,
)


def _dimensions_model(*, with_symmetry: bool = False):
    model = _model()
    if with_symmetry:
        symmetry = DesignModelParameter(
            "section_symmetry_fixture",
            {"symmetry": "both", "axes": {"x": 0.0, "y": 0.0}},
            ParameterType.OBJECT,
        )
        model = revise_design_model_revision(
            model,
            parameters=(*model.parameters, symmetry),
            features=model.features,
            actor_id="operator-1",
            reason="Add a constrained section for edit coverage.",
            created_at_utc="2026-10-03T18:00:00Z",
        )
    return create_overall_dimensions_revision(
        model,
        height=100.0,
        width=30.0,
        depth=20.0,
        proportional_groups=((DimensionAxis.WIDTH, DimensionAxis.DEPTH),),
        actor_id="operator-1",
        reason="Initialize explicit overall dimensions.",
        created_at_utc="2026-10-03T18:01:00Z",
    )


def _dimension_value(model):
    parameter = next(
        item for item in model.parameters if item.parameter_id == DIMENSIONS_PARAMETER_ID
    )
    return parameter.as_dict()["value"]


def _edit(model, axis: DimensionAxis, value: float):
    return revise_overall_dimension(
        model,
        expected_model_revision_id=model.revision_id,
        axis=axis,
        value=value,
        actor_id="operator-1",
        reason=f"Set overall {axis.value}.",
        created_at_utc="2026-10-03T18:02:00Z",
    )


def test_height_width_and_depth_edits_update_only_explicitly_related_axes():
    source = _dimensions_model()
    width_edit = _edit(source, DimensionAxis.WIDTH, 45.0)
    assert _dimension_value(width_edit.model)["dimensions"] == {
        "height": 100.0,
        "width": 45.0,
        "depth": 30.0,
    }
    assert width_edit.changed_axes == (DimensionAxis.WIDTH, DimensionAxis.DEPTH)
    assert _dimension_value(width_edit.model)["proportional_groups"] == [["width", "depth"]]

    height_edit = _edit(width_edit.model, DimensionAxis.HEIGHT, 120.0)
    assert _dimension_value(height_edit.model)["dimensions"] == {
        "height": 120.0,
        "width": 45.0,
        "depth": 30.0,
    }
    depth_edit = _edit(height_edit.model, DimensionAxis.DEPTH, 60.0)
    assert _dimension_value(depth_edit.model)["dimensions"] == {
        "height": 120.0,
        "width": 90.0,
        "depth": 60.0,
    }


def test_dimension_edits_preserve_symmetry_features_parent_and_scale_state():
    source = _dimensions_model(with_symmetry=True)
    symmetry_before = next(
        item for item in source.parameters if item.parameter_id == "section_symmetry_fixture"
    )
    edited = _edit(source, DimensionAxis.HEIGHT, 125.0)
    symmetry_after = next(
        item for item in edited.model.parameters if item.parameter_id == "section_symmetry_fixture"
    )

    assert symmetry_after == symmetry_before
    assert edited.model.features == source.features
    assert edited.model.fitted_to_scan_master_revision_id == (
        source.fitted_to_scan_master_revision_id
    )
    assert edited.model.scan_master_geometry_sha256 == source.scan_master_geometry_sha256
    assert edited.model.parent_binding_revision_id == source.parent_binding_revision_id
    assert edited.model.scale_state is source.scale_state
    assert edited.model.coordinate_unit == "mm_unverified"
    assert edited.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert edited.model.mold_use_authorized is False
    assert edited.model.previous_revision_id == source.revision_id


def test_history_undo_redo_replays_dimension_edit_as_new_revisions():
    source = _dimensions_model()
    edited = _edit(source, DimensionAxis.WIDTH, 45.0)
    history = DesignModelHistory(source).apply(
        edited.history_command,
        actor_id="operator-1",
        reason="Set overall width.",
        created_at_utc="2026-10-03T18:02:00Z",
    )
    assert history.current_revision == edited.model

    undone = history.undo(actor_id="operator-1", created_at_utc="2026-10-03T18:03:00Z")
    assert _dimension_value(undone.current_revision)["dimensions"] == {
        "height": 100.0,
        "width": 30.0,
        "depth": 20.0,
    }
    redone = undone.redo(actor_id="operator-1", created_at_utc="2026-10-03T18:04:00Z")
    assert _dimension_value(redone.current_revision) == _dimension_value(edited.model)
    assert (
        len(
            {
                source.revision_id,
                edited.model.revision_id,
                undone.current_revision.revision_id,
                redone.current_revision.revision_id,
            }
        )
        == 4
    )


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf"), True])
def test_impossible_dimension_edits_reject_without_a_revision(value):
    source = _dimensions_model()
    with pytest.raises(DesignDimensionsError, match="dimension_value_must_be_positive_finite"):
        _edit(source, DimensionAxis.DEPTH, value)


def test_underdetermined_relationships_missing_dimensions_and_noops_reject():
    source = _dimensions_model()
    with pytest.raises(DesignDimensionsError, match="dimension_edit_noop"):
        _edit(source, DimensionAxis.WIDTH, 30.0)
    with pytest.raises(DesignDimensionsError, match="overall_dimensions_missing_or_ambiguous"):
        revise_overall_dimension(
            _model(),
            expected_model_revision_id=_model().revision_id,
            axis=DimensionAxis.HEIGHT,
            value=10.0,
            actor_id="operator-1",
            reason="Reject missing dimensions.",
            created_at_utc="2026-10-03T18:02:00Z",
        )
    with pytest.raises(DesignDimensionsError, match="dimension_relationship_group_invalid"):
        create_overall_dimensions_revision(
            _model(),
            height=10.0,
            width=5.0,
            depth=3.0,
            proportional_groups=(
                (DimensionAxis.HEIGHT, DimensionAxis.WIDTH),
                (DimensionAxis.WIDTH, DimensionAxis.DEPTH),
            ),
            actor_id="operator-1",
            reason="Reject overlapping proportional groups.",
            created_at_utc="2026-10-03T18:01:00Z",
        )


def test_overflow_from_proportional_propagation_rejects_atomically():
    model = create_overall_dimensions_revision(
        _model(),
        height=100.0,
        width=5e-324,
        depth=20.0,
        proportional_groups=((DimensionAxis.WIDTH, DimensionAxis.DEPTH),),
        actor_id="operator-1",
        reason="Create bounded proportional dimensions.",
        created_at_utc="2026-10-03T18:01:00Z",
    )
    with pytest.raises(DesignDimensionsError, match="dimension_relationship_result_invalid"):
        _edit(model, DimensionAxis.WIDTH, 1e308)


def test_deterministic_dimension_revisions_and_stale_expected_revision_rejects():
    source = _dimensions_model()
    first = _edit(source, DimensionAxis.HEIGHT, 110.0)
    repeat = _edit(source, DimensionAxis.HEIGHT, 110.0)
    assert first == repeat
    with pytest.raises(DesignDimensionsError, match="design_model_revision_stale"):
        revise_overall_dimension(
            source,
            expected_model_revision_id=first.model.revision_id,
            axis=DimensionAxis.HEIGHT,
            value=120.0,
            actor_id="operator-1",
            reason="Reject stale dimension edit.",
            created_at_utc="2026-10-03T18:02:00Z",
        )
