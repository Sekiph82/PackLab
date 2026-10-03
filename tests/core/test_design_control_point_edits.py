from __future__ import annotations

import pytest
from tests.core.test_revolved_design_model import _build as build_revolve
from tests.core.test_symmetric_section_loft import _build as build_loft
from tests.core.test_symmetric_section_loft import _scan_master

from packlab_core.cross_section import SectionPoint
from packlab_core.design_control_point_edits import (
    ControlPointAction,
    ControlPointEditError,
    edit_design_profile_control_point,
    edit_design_section_control_point,
)
from packlab_core.design_history import DesignModelHistory
from packlab_core.design_profile import ProfilePoint


def _edit_profile(model, profile, operation, action, index, point):
    return edit_design_profile_control_point(
        model,
        profile,
        operation,
        expected_model_revision_id=model.revision_id,
        expected_scan_master_revision_id=model.fitted_to_scan_master_revision_id,
        expected_scan_master_geometry_sha256=model.scan_master_geometry_sha256,
        profile_feature_id=next(
            item.feature_id for item in model.features if item.semantic_key == "fitted-profile"
        ),
        action=action,
        point_index=index,
        point=point,
        actor_id="operator-1",
        reason="Edit profile control point.",
        created_at_utc="2026-10-03T16:00:00Z",
        profile_samples=24,
    )


def _edit_section(model, loft, sections, index, point_index, point):
    return edit_design_section_control_point(
        model,
        loft,
        sections,
        expected_model_revision_id=model.revision_id,
        expected_scan_master_revision_id=loft.scan_master_revision_id,
        expected_scan_master_geometry_sha256=loft.scan_master_geometry_sha256,
        section_index=index,
        action=ControlPointAction.MOVE,
        point_index=point_index,
        point=point,
        actor_id="operator-1",
        reason="Edit section control point.",
        created_at_utc="2026-10-03T16:00:00Z",
    )


def test_profile_points_move_add_remove_and_preview_are_revisioned_and_deterministic() -> None:
    _, _, _, _, built = build_revolve()
    point_index = 2
    original_point = built.profile.points[point_index]
    moved_point = ProfilePoint(
        original_point.axial,
        original_point.radius + 0.05,
        original_point.tangent,
    )
    moved = _edit_profile(
        built.model,
        built.profile,
        built.operation,
        ControlPointAction.MOVE,
        point_index,
        moved_point,
    )
    repeated = _edit_profile(
        built.model,
        built.profile,
        built.operation,
        ControlPointAction.MOVE,
        point_index,
        moved_point,
    )
    assert moved == repeated
    assert moved.model.revision_id != built.model.revision_id
    assert moved.profile.points[point_index] == moved_point
    assert moved.preview.authority_class == "PREVIEW_PROXY"
    assert moved.preview.model_revision_id == moved.model.revision_id
    assert moved.operation.parent_feature_ids == built.operation.parent_feature_ids

    left, right = moved.profile.points[1:3]
    inserted = ProfilePoint((left.axial + right.axial) / 2, (left.radius + right.radius) / 2)
    added = _edit_profile(
        moved.model, moved.profile, moved.operation, ControlPointAction.ADD, 2, inserted
    )
    assert added.profile.points[2] == inserted
    removed = _edit_profile(
        added.model, added.profile, added.operation, ControlPointAction.REMOVE, 2, None
    )
    assert removed.profile.points == moved.profile.points


def test_profile_ordering_stale_revision_and_history_undo_redo() -> None:
    _, _, _, _, built = build_revolve()
    feature_id = next(
        item.feature_id for item in built.model.features if item.semantic_key == "fitted-profile"
    )
    moved_point = ProfilePoint(
        built.profile.points[2].axial,
        built.profile.points[2].radius + 0.05,
    )
    moved = _edit_profile(
        built.model, built.profile, built.operation, ControlPointAction.MOVE, 2, moved_point
    )
    history = DesignModelHistory(built.model).apply(
        moved.history_command,
        actor_id="operator-1",
        reason="Edit profile control point.",
        created_at_utc="2026-10-03T16:00:00Z",
    )
    assert history.current_revision == moved.model
    undone = history.undo(actor_id="operator-1", created_at_utc="2026-10-03T16:01:00Z")
    assert undone.current_revision.parameters == built.model.parameters
    redone = undone.redo(actor_id="operator-1", created_at_utc="2026-10-03T16:02:00Z")
    assert redone.current_revision.parameters == moved.model.parameters

    with pytest.raises(ControlPointEditError, match="profile_control_point_edit_rejected"):
        _edit_profile(
            built.model,
            built.profile,
            built.operation,
            ControlPointAction.MOVE,
            2,
            ProfilePoint(built.profile.points[3].axial, 0.5),
        )
    with pytest.raises(ControlPointEditError, match="design_model_revision_stale"):
        edit_design_profile_control_point(
            built.model,
            built.profile,
            built.operation,
            expected_model_revision_id="stale",
            expected_scan_master_revision_id=built.model.fitted_to_scan_master_revision_id,
            expected_scan_master_geometry_sha256=built.model.scan_master_geometry_sha256,
            profile_feature_id=feature_id,
            action=ControlPointAction.MOVE,
            point_index=2,
            point=moved_point,
            actor_id="operator-1",
            reason="Stale edit.",
            created_at_utc="2026-10-03T16:00:00Z",
        )


def test_symmetric_section_move_preserves_mirror_and_rebuilds_loft_preview() -> None:
    scan = _scan_master()
    _, loft = build_loft(scan)
    sections = loft.sections
    target = sections[0]
    selected = target.points[1]
    moved_point = SectionPoint(selected.x + 0.03, selected.y + 0.02)
    moved = _edit_section(loft.model, loft, sections, 0, 1, moved_point)
    repeated = _edit_section(loft.model, loft, sections, 0, 1, moved_point)
    assert moved == repeated
    updated = moved.sections[0]
    assert updated.points[1] == moved_point
    assert any(
        point.x == pytest.approx(-moved_point.x) and point.y == pytest.approx(moved_point.y)
        for point in updated.points
    )
    assert moved.preview.authority_class == "PREVIEW_PROXY"
    assert moved.preview.model_revision_id == moved.model.revision_id
    assert moved.operation.kind.value == "loft"
    assert tuple(item.feature_id for item in moved.model.features) == tuple(
        item.feature_id for item in loft.model.features
    )

    history = DesignModelHistory(loft.model).apply(
        moved.history_command,
        actor_id="operator-1",
        reason="Edit section control point.",
        created_at_utc="2026-10-03T16:00:00Z",
    )
    undone = history.undo(actor_id="operator-1", created_at_utc="2026-10-03T16:01:00Z")
    assert undone.current_revision.parameters == loft.model.parameters
    redone = undone.redo(actor_id="operator-1", created_at_utc="2026-10-03T16:02:00Z")
    assert redone.current_revision.parameters == moved.model.parameters


def test_section_self_intersection_and_malformed_section_sequence_reject() -> None:
    scan = _scan_master()
    _, loft = build_loft(scan)
    target = loft.sections[0]
    with pytest.raises(ControlPointEditError, match="section_control_point_edit_rejected"):
        _edit_section(
            loft.model,
            loft,
            loft.sections,
            0,
            1,
            SectionPoint(100.0, 100.0),
        )
    with pytest.raises(ControlPointEditError, match="section_preview_inputs_invalid"):
        edit_design_section_control_point(
            loft.model,
            loft,
            None,  # type: ignore[arg-type]
            expected_model_revision_id=loft.model.revision_id,
            expected_scan_master_revision_id=loft.scan_master_revision_id,
            expected_scan_master_geometry_sha256=loft.scan_master_geometry_sha256,
            section_index=0,
            action=ControlPointAction.MOVE,
            point_index=1,
            point=target.points[1],
            actor_id="operator-1",
            reason="Malformed edit.",
            created_at_utc="2026-10-03T16:00:00Z",
        )
