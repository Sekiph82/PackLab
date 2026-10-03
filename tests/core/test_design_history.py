from __future__ import annotations

import hashlib

import pytest

from packlab_core.design_history import (
    DesignHistoryError,
    DesignModelHistory,
    EditTargetKind,
    create_edit_command,
)
from packlab_core.design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _model():
    scan_id = f"scan-master:{hashlib.sha256(b'history-parent').hexdigest()}"
    binding = bind_design_model_parent(
        ScanMasterRevision(
            scan_id,
            PROJECT,
            MESH,
            {
                "scan_master_revision_id": scan_id,
                "project_id": PROJECT,
                "authority_class": "SCAN_MASTER",
                "output_geometry_sha256": mesh_sha256(MESH),
                "reconstruction_revision_id": "reconstruction-r1",
                "scale_state": ScaleState.METRIC_UNVERIFIED.value,
                "scale_provenance_id": "scale-r1",
                "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
                "mold_use_authorized": False,
            },
        ),
        actor_id="operator-1",
        reason="Initial selection.",
        created_at_utc="2026-10-03T12:00:00Z",
    )
    return create_design_model_revision(
        binding,
        package_family=PackageFamily.BOTTLE,
        parameters=(
            DesignModelParameter("height", 100.0, ParameterType.NUMBER, "mm_unverified"),
            DesignModelParameter("width", 30.0, ParameterType.NUMBER, "mm_unverified"),
        ),
        features=(
            DesignModelFeatureReference(
                stable_feature_id("container", FeatureKind.BODY, "body"),
                "container",
                FeatureKind.BODY,
                "body",
            ),
        ),
        actor_id="operator-1",
        reason="Initial model.",
        created_at_utc="2026-10-03T12:30:00Z",
    )


def _parameter(model, parameter_id: str):
    return next(item for item in model.parameters if item.parameter_id == parameter_id)


def _command(model, parameter_id: str, after_value: float):
    before = _parameter(model, parameter_id)
    after = DesignModelParameter(parameter_id, after_value, ParameterType.NUMBER, before.unit)
    return create_edit_command(
        model.revision_id,
        EditTargetKind.PARAMETER,
        parameter_id,
        before,
        after,
    )


def test_edit_undo_redo_round_trip_uses_new_immutable_revisions() -> None:
    original = _model()
    initial_history = DesignModelHistory(original)
    command = _command(original, "height", 120.0)
    edited = initial_history.apply(
        command,
        actor_id="operator-1",
        reason="Set bottle height.",
        created_at_utc="2026-10-03T13:00:00Z",
    )
    undone = edited.undo(actor_id="operator-1", created_at_utc="2026-10-03T13:01:00Z")
    redone = undone.redo(actor_id="operator-1", created_at_utc="2026-10-03T13:02:00Z")
    assert _parameter(edited.current_revision, "height").value == 120.0
    assert _parameter(undone.current_revision, "height").value == 100.0
    assert _parameter(redone.current_revision, "height").value == 120.0
    assert (
        len(
            {
                original.revision_id,
                edited.current_revision.revision_id,
                undone.current_revision.revision_id,
                redone.current_revision.revision_id,
            }
        )
        == 4
    )
    assert original.parameters[0].value == 100.0
    assert (
        original.fitted_to_scan_master_revision_id
        == redone.current_revision.fitted_to_scan_master_revision_id
    )
    assert original.parent_binding_revision_id == redone.current_revision.parent_binding_revision_id
    assert initial_history.current_revision is original


def test_multi_command_history_and_redo_invalidation_after_branch_edit() -> None:
    model = _model()
    history = DesignModelHistory(model)
    height_edit = _command(history.current_revision, "height", 110.0)
    history = history.apply(
        height_edit,
        actor_id="operator-1",
        reason="Edit height.",
        created_at_utc="2026-10-03T13:00:00Z",
    )
    width_edit = _command(history.current_revision, "width", 35.0)
    history = history.apply(
        width_edit,
        actor_id="operator-1",
        reason="Edit width.",
        created_at_utc="2026-10-03T13:01:00Z",
    )
    history = history.undo(actor_id="operator-1", created_at_utc="2026-10-03T13:02:00Z")
    assert _parameter(history.current_revision, "height").value == 110.0
    assert _parameter(history.current_revision, "width").value == 30.0
    history = history.undo(actor_id="operator-1", created_at_utc="2026-10-03T13:03:00Z")
    assert _parameter(history.current_revision, "height").value == 100.0
    history = history.redo(actor_id="operator-1", created_at_utc="2026-10-03T13:04:00Z")
    assert _parameter(history.current_revision, "height").value == 110.0
    branch = _command(history.current_revision, "width", 40.0)
    history = history.apply(
        branch,
        actor_id="operator-1",
        reason="Branch edit.",
        created_at_utc="2026-10-03T13:05:00Z",
    )
    assert history.can_redo is False
    with pytest.raises(DesignHistoryError, match="redo_history_empty"):
        history.redo(actor_id="operator-1", created_at_utc="2026-10-03T13:06:00Z")


def test_stale_expected_revision_and_deleted_feature_target_fail_closed() -> None:
    model = _model()
    stale = _command(model, "height", 120.0)
    edited = DesignModelHistory(model).apply(
        stale,
        actor_id="operator-1",
        reason="First edit.",
        created_at_utc="2026-10-03T13:00:00Z",
    )
    with pytest.raises(DesignHistoryError, match="edit_command_expected_revision_stale"):
        edited.apply(
            stale,
            actor_id="operator-1",
            reason="Concurrent stale edit.",
            created_at_utc="2026-10-03T13:01:00Z",
        )
    feature = model.features[0]
    delete_feature = create_edit_command(
        model.revision_id,
        EditTargetKind.FEATURE,
        feature.feature_id,
        feature,
        None,
    )
    deleted_history = DesignModelHistory(model).apply(
        delete_feature,
        actor_id="operator-1",
        reason="Delete feature.",
        created_at_utc="2026-10-03T13:01:00Z",
    )
    stale_feature_edit = create_edit_command(
        deleted_history.current_revision.revision_id,
        EditTargetKind.FEATURE,
        feature.feature_id,
        feature,
        None,
    )
    with pytest.raises(DesignHistoryError, match="edit_command_target_missing_or_changed"):
        deleted_history.apply(
            stale_feature_edit,
            actor_id="operator-1",
            reason="Stale feature command.",
            created_at_utc="2026-10-03T13:02:00Z",
        )


def test_command_identity_is_deterministic_and_history_is_bounded() -> None:
    model = _model()
    first = _command(model, "height", 120.0)
    repeat = _command(model, "height", 120.0)
    assert first.command_id == repeat.command_id
    history = DesignModelHistory(model, max_entries=1)
    history = history.apply(
        first,
        actor_id="operator-1",
        reason="First.",
        created_at_utc="2026-10-03T13:00:00Z",
    )
    second = _command(history.current_revision, "width", 35.0)
    history = history.apply(
        second,
        actor_id="operator-1",
        reason="Second.",
        created_at_utc="2026-10-03T13:01:00Z",
    )
    assert len(history.undo_commands) == 1
    assert history.undo_commands[0] == second
