from __future__ import annotations

import pytest
from tests.core.test_jerrycan_handle_void_candidates import _detect, _inputs

from packlab_core.design_history import DesignModelHistory
from packlab_core.design_model import FeatureKind
from packlab_core.jerrycan_handle_opening import (
    JerrycanHandleOpeningError,
    create_handle_opening_profile_edit,
    create_jerrycan_handle_opening,
    move_jerrycan_handle_opening,
    resize_jerrycan_handle_opening,
    resolve_jerrycan_handle_opening,
)
from packlab_core.scan_master import mesh_sha256


def _opening(*, gaps=()):
    scan, model, preview = _inputs((0.25, 0.75, 1.0, 2.0, 2.0, 4.0), gaps=gaps)
    detection = _detect(scan, model, preview)
    candidate = detection.candidates[0]
    result = create_jerrycan_handle_opening(
        model,
        detection,
        candidate.candidate_id,
        profile=((1.2, 2.3), (1.8, 2.3), (1.8, 3.7), (1.2, 3.7)),
        clearance=0.1,
        actor_id="fixture-operator",
        reason="Create constrained synthetic handle-opening design feature.",
        created_at_utc="2026-10-04T12:00:00Z",
    )
    feature = next(
        item for item in result.features if item.feature_kind is FeatureKind.HANDLE_OPENING
    )
    return scan, model, detection, result, feature


def test_accepted_candidate_creates_parametric_bounded_opening() -> None:
    scan, original, preview = _inputs((0.25, 0.75, 1.0, 2.0, 2.0, 4.0))
    original_manifest = scan.manifest_bytes()
    original_scan_digest = mesh_sha256(scan.mesh)
    detection = _detect(scan, original, preview)
    candidate = detection.candidates[0]
    model = create_jerrycan_handle_opening(
        original,
        detection,
        candidate.candidate_id,
        profile=((1.2, 2.3), (1.8, 2.3), (1.8, 3.7), (1.2, 3.7)),
        clearance=0.1,
        actor_id="fixture-operator",
        reason="Create constrained synthetic handle-opening design feature.",
        created_at_utc="2026-10-04T12:00:00Z",
    )
    feature = next(
        item for item in model.features if item.feature_kind is FeatureKind.HANDLE_OPENING
    )
    opening = resolve_jerrycan_handle_opening(model, feature.feature_id)

    assert feature.feature_kind is FeatureKind.HANDLE_OPENING
    assert feature.component_id == original.features[0].component_id
    assert opening.candidate_id == detection.candidates[0].candidate_id
    assert opening.parent_body_feature_ids == (original.features[0].feature_id,)
    assert opening.profile == (
        (1.2, 2.3),
        (1.8, 2.3),
        (1.8, 3.7),
        (1.2, 3.7),
    )
    assert opening.clearance_envelope == pytest.approx((1.0, 2.0, 2.0, 4.0))
    assert opening.safe_profile_bounds == pytest.approx((1.1, 2.1, 1.9, 3.9))
    assert opening.coordinate_unit == original.coordinate_unit
    metadata = opening.as_dict()
    assert metadata["authority_class"] == "DESIGN_MODEL_FEATURE"
    assert metadata["scan_master_mutated"] is False
    assert metadata["hidden_extent_inferred"] is False
    assert any("candidate_contour_not_embedded" in item for item in metadata["limitations"])
    assert model.fitted_to_scan_master_revision_id == original.fitted_to_scan_master_revision_id
    assert model.scan_master_geometry_sha256 == original.scan_master_geometry_sha256
    assert scan.manifest_bytes() == original_manifest
    assert mesh_sha256(scan.mesh) == original_scan_digest


def test_move_resize_and_undo_redo_preserve_feature_identity() -> None:
    _, original, _, model, feature = _opening()
    initial = resolve_jerrycan_handle_opening(model, feature.feature_id)
    history = DesignModelHistory(model)

    move = move_jerrycan_handle_opening(model, feature.feature_id, offset=(0.02, 0.03))
    history = history.apply(
        move,
        actor_id="fixture-operator",
        reason="Move handle-opening profile within supported bounds.",
        created_at_utc="2026-10-04T12:01:00Z",
    )
    moved = resolve_jerrycan_handle_opening(history.current_revision, feature.feature_id)
    assert moved.profile[0] == pytest.approx((1.22, 2.33))
    assert moved.feature.feature_id == initial.feature.feature_id

    resize = resize_jerrycan_handle_opening(
        history.current_revision,
        feature.feature_id,
        width_scale=0.9,
        height_scale=0.9,
    )
    history = history.apply(
        resize,
        actor_id="fixture-operator",
        reason="Resize handle-opening profile within supported bounds.",
        created_at_utc="2026-10-04T12:02:00Z",
    )
    resized = resolve_jerrycan_handle_opening(history.current_revision, feature.feature_id)
    assert resized.profile != moved.profile
    assert resized.feature.feature_id == initial.feature.feature_id

    history = history.undo(actor_id="fixture-operator", created_at_utc="2026-10-04T12:03:00Z")
    assert (
        resolve_jerrycan_handle_opening(history.current_revision, feature.feature_id).profile
        == moved.profile
    )
    history = history.undo(actor_id="fixture-operator", created_at_utc="2026-10-04T12:04:00Z")
    assert (
        resolve_jerrycan_handle_opening(history.current_revision, feature.feature_id).profile
        == initial.profile
    )
    history = history.redo(actor_id="fixture-operator", created_at_utc="2026-10-04T12:05:00Z")
    assert (
        resolve_jerrycan_handle_opening(history.current_revision, feature.feature_id).profile
        == moved.profile
    )
    assert (
        history.current_revision.fitted_to_scan_master_revision_id
        == original.fitted_to_scan_master_revision_id
    )


def test_body_bounds_and_self_intersection_reject_invalid_edits() -> None:
    _, _, _, model, feature = _opening()

    with pytest.raises(JerrycanHandleOpeningError, match="outside_supported_bounds"):
        move_jerrycan_handle_opening(model, feature.feature_id, offset=(1.0, 0.0))
    with pytest.raises(JerrycanHandleOpeningError, match="outside_supported_bounds"):
        resize_jerrycan_handle_opening(
            model,
            feature.feature_id,
            width_scale=2.0,
            height_scale=1.0,
        )
    with pytest.raises(JerrycanHandleOpeningError, match="self_intersects"):
        create_handle_opening_profile_edit(
            model,
            feature.feature_id,
            ((1.1, 2.1), (1.9, 3.9), (1.1, 3.9), (1.9, 2.1), (1.3, 2.7)),
        )


def test_opening_requires_unambiguous_complete_current_candidate() -> None:
    scan, model, preview = _inputs((0.25, 0.75, 1.0, 2.0, 2.0, 4.0), gaps=("unobserved rear area",))
    incomplete = _detect(scan, model, preview)
    with pytest.raises(JerrycanHandleOpeningError, match="stale_ambiguous_or_incomplete"):
        create_jerrycan_handle_opening(
            model,
            incomplete,
            incomplete.candidates[0].candidate_id,
            profile=((1.2, 2.3), (1.8, 2.3), (1.8, 3.7), (1.2, 3.7)),
            clearance=0.1,
            actor_id="fixture-operator",
            reason="Reject incomplete handle-opening evidence.",
            created_at_utc="2026-10-04T12:00:00Z",
        )

    ambiguous_scan, ambiguous_model, ambiguous_preview = _inputs(
        (0.25, 0.75, 1.0, 2.0, 2.0, 4.0),
        (0.25, 0.75, 2.5, 3.0, 2.0, 4.0),
    )
    ambiguous = _detect(ambiguous_scan, ambiguous_model, ambiguous_preview)
    with pytest.raises(JerrycanHandleOpeningError, match="stale_ambiguous_or_incomplete"):
        create_jerrycan_handle_opening(
            ambiguous_model,
            ambiguous,
            ambiguous.candidates[0].candidate_id,
            profile=((1.2, 2.3), (1.8, 2.3), (1.8, 3.7), (1.2, 3.7)),
            clearance=0.1,
            actor_id="fixture-operator",
            reason="Reject ambiguous handle-opening evidence.",
            created_at_utc="2026-10-04T12:00:00Z",
        )

    _, _, detection, updated, feature = _opening()
    with pytest.raises(JerrycanHandleOpeningError, match="stale_ambiguous_or_incomplete"):
        create_jerrycan_handle_opening(
            updated,
            detection,
            detection.candidates[0].candidate_id,
            profile=((1.2, 2.3), (1.8, 2.3), (1.8, 3.7), (1.2, 3.7)),
            clearance=0.1,
            actor_id="fixture-operator",
            reason="Reject stale handle-opening evidence.",
            created_at_utc="2026-10-04T12:00:00Z",
        )


def test_opening_feature_identity_is_candidate_stable() -> None:
    _, _, _, first_model, first_feature = _opening()
    _, _, _, second_model, second_feature = _opening()

    assert first_feature.feature_id == second_feature.feature_id
    assert first_model.revision_id == second_model.revision_id
