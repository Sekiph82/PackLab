from __future__ import annotations

from dataclasses import replace

import pytest
from test_mating_references import _fixture as _mating_fixture

from packlab_core.closure_workflow import (
    ClosureWorkflowHistory,
    replace_closure_component,
)
from packlab_core.design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    FeatureKind,
    ParameterType,
    revise_design_model_revision,
    stable_feature_id,
)
from packlab_core.mating_references import (
    MatingReferenceStatus,
    create_neck_closure_mating_references,
)
from packlab_core.scan_master import mesh_sha256


def _fixture():
    scan, geometry, model, neck, old_cap, neck_sections, closure_sections = _mating_fixture()
    body_component = "bottle-body"
    body_key = "body:container"
    body = DesignModelFeatureReference(
        stable_feature_id(body_component, FeatureKind.BODY, body_key),
        body_component,
        FeatureKind.BODY,
        body_key,
    )
    old_param = DesignModelParameter(
        "old_cap_parameters",
        {"feature_id": old_cap.feature_id, "component_id": old_cap.component_id, "radius": 2.5},
        ParameterType.OBJECT,
    )
    current = revise_design_model_revision(
        model,
        parameters=(*model.parameters, old_param),
        features=(*model.features, body),
        actor_id="operator-1",
        reason="Add existing body and closure parameters.",
        created_at_utc="2026-10-03T18:30:00Z",
    )
    new_component = "replacement-closure"
    new_key = "closure:alternate-exterior"
    new_cap = DesignModelFeatureReference(
        stable_feature_id(new_component, FeatureKind.CAP, new_key),
        new_component,
        FeatureKind.CAP,
        new_key,
    )
    new_param = DesignModelParameter(
        "replacement_cap_parameters",
        {"feature_id": new_cap.feature_id, "component_id": new_component, "radius": 2.75},
        ParameterType.OBJECT,
    )
    replacement_base = revise_design_model_revision(
        current,
        parameters=(*current.parameters, new_param),
        features=(*current.features, new_cap),
        actor_id="operator-1",
        reason="Prepare an alternate closure component candidate.",
        created_at_utc="2026-10-03T18:31:00Z",
    )
    mating = create_neck_closure_mating_references(
        scan,
        geometry,
        replacement_base,
        neck.feature_id,
        new_cap.feature_id,
        neck_sections,
        closure_sections,
        expected_scan_master_revision_id=scan.revision_id,
        expected_model_revision_id=replacement_base.revision_id,
        actor_id="operator-1",
        reason="Bind alternate closure to observed neck reference.",
        created_at_utc="2026-10-03T18:32:00Z",
    )
    assert mating.model is not None
    return scan, current, old_cap, new_cap, replacement_base, mating


def _replace(args, *, mating=None, replacement_base=None):
    scan, current, old_cap, new_cap, original_replacement_base, original_mating = args
    source = original_replacement_base if replacement_base is None else replacement_base
    refs = original_mating if mating is None else mating
    return replace_closure_component(
        scan,
        ClosureWorkflowHistory(current),
        source,
        refs,
        current_closure_feature_id=old_cap.feature_id,
        replacement_closure_feature_id=new_cap.feature_id,
        current_closure_parameter_ids=("old_cap_parameters",),
        replacement_closure_parameter_ids=("replacement_cap_parameters",),
        expected_scan_master_revision_id=scan.revision_id,
        expected_current_model_revision_id=current.revision_id,
        expected_replacement_base_revision_id=source.revision_id,
        actor_id="operator-1",
        reason="Replace the selected closure component.",
        created_at_utc="2026-10-03T18:33:00Z",
    )


def test_replacement_creates_parent_bound_revision_and_preserves_body_feature_ids() -> None:
    args = _fixture()
    scan_digest = mesh_sha256(args[0].mesh)
    first = _replace(args)
    repeated = _replace(args)

    assert first.model == repeated.model
    assert first.model.revision_id == repeated.model.revision_id
    assert first.model.previous_revision_id == args[1].revision_id
    assert first.current_closure_feature_id == args[2].feature_id
    assert first.replacement_closure_feature_id == args[3].feature_id
    assert args[2].feature_id not in {item.feature_id for item in first.model.features}
    assert args[3].feature_id in {item.feature_id for item in first.model.features}
    assert first.body_feature_ids == tuple(
        sorted(
            item.feature_id for item in args[1].features if item.feature_kind is FeatureKind.BODY
        )
    )
    assert "old_cap_parameters" not in {item.parameter_id for item in first.model.parameters}
    assert "replacement_cap_parameters" in {item.parameter_id for item in first.model.parameters}
    assert first.model.fitted_to_scan_master_revision_id == args[0].revision_id
    assert first.model.scan_master_geometry_sha256 == scan_digest
    assert first.model.coordinate_unit == "mm_unverified"
    assert first.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.model.mold_use_authorized is False
    assert first.as_dict()["scan_master_mutated"] is False
    assert first.as_dict()["thread_compatibility_claimed"] is False
    assert first.as_dict()["seal_compatibility_claimed"] is False


def test_replacement_undo_redo_are_atomic_and_keep_body_feature_ids() -> None:
    args = _fixture()
    result = _replace(args)
    assert result.history.can_undo
    undone = result.history.undo(actor_id="operator-1", created_at_utc="2026-10-03T18:34:00Z")
    assert args[2].feature_id in {item.feature_id for item in undone.current_revision.features}
    assert args[3].feature_id not in {item.feature_id for item in undone.current_revision.features}
    assert "old_cap_parameters" in {
        item.parameter_id for item in undone.current_revision.parameters
    }
    assert "replacement_cap_parameters" not in {
        item.parameter_id for item in undone.current_revision.parameters
    }
    assert undone.can_redo

    redone = undone.redo(actor_id="operator-1", created_at_utc="2026-10-03T18:35:00Z")
    assert args[2].feature_id not in {item.feature_id for item in redone.current_revision.features}
    assert args[3].feature_id in {item.feature_id for item in redone.current_revision.features}
    assert "old_cap_parameters" not in {
        item.parameter_id for item in redone.current_revision.parameters
    }
    assert "replacement_cap_parameters" in {
        item.parameter_id for item in redone.current_revision.parameters
    }
    assert (
        tuple(
            sorted(
                item.feature_id
                for item in redone.current_revision.features
                if item.feature_kind is FeatureKind.BODY
            )
        )
        == result.body_feature_ids
    )


def test_incompatible_or_stale_mating_references_and_body_changes_reject() -> None:
    args = _fixture()
    bad_reference = replace(args[5], status=MatingReferenceStatus.AXIS_MISMATCH_REVIEW_REQUIRED)
    with pytest.raises(ValueError, match="replacement_mating_reference_stale_or_incompatible"):
        _replace(args, mating=bad_reference)

    stale_closure = replace(args[5], closure_feature_id="stale-feature")
    with pytest.raises(ValueError, match="replacement_mating_reference_stale_or_incompatible"):
        _replace(args, mating=stale_closure)

    body = next(item for item in args[1].features if item.feature_kind is FeatureKind.BODY)
    changed_body = DesignModelFeatureReference(
        stable_feature_id("different-body", FeatureKind.BODY, "body:container"),
        "different-body",
        FeatureKind.BODY,
        "body:container",
    )
    incompatible_base = revise_design_model_revision(
        args[1],
        parameters=args[4].parameters,
        features=tuple(item for item in args[4].features if item.feature_id != body.feature_id)
        + (changed_body,),
        actor_id="operator-1",
        reason="Create incompatible replacement body evidence.",
        created_at_utc="2026-10-03T18:36:00Z",
    )
    incompatible_mating = create_neck_closure_mating_references(
        args[0],
        _mating_fixture()[1],
        incompatible_base,
        next(item.feature_id for item in args[1].features if item.feature_kind is FeatureKind.NECK),
        args[3].feature_id,
        _mating_fixture()[5],
        _mating_fixture()[6],
        expected_scan_master_revision_id=args[0].revision_id,
        expected_model_revision_id=incompatible_base.revision_id,
        actor_id="operator-1",
        reason="Bind incompatible alternate closure.",
        created_at_utc="2026-10-03T18:37:00Z",
    )
    assert incompatible_mating.model is not None
    with pytest.raises(ValueError, match="replacement_changes_non_closure_features"):
        _replace(args, mating=incompatible_mating, replacement_base=incompatible_base)
