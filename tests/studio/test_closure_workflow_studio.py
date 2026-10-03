from __future__ import annotations

from unittest.mock import sentinel

import pytest

from packlab_studio import closure_workflow
from packlab_studio.closure_workflow import (
    ClosurePresentationError,
    ClosureWorkflowController,
)
from packlab_studio.viewport import PointCloudGeometry, SceneObjectKind, ViewportService


def test_visibility_toggle_is_presentation_only_and_preserves_geometry() -> None:
    viewport = ViewportService()
    points = PointCloudGeometry(((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)))
    viewport.add_geometry("stable-cap-feature", SceneObjectKind.CAP, points)
    controller = ClosureWorkflowController(viewport)

    controller.set_visible("stable-cap-feature", False)
    assert viewport.scene.get("stable-cap-feature").visible is False
    assert viewport.scene.get("stable-cap-feature").geometry is points
    controller.set_visible("stable-cap-feature", True)
    assert viewport.scene.get("stable-cap-feature").visible is True
    assert viewport.scene.get("stable-cap-feature").geometry is points
    viewport.add_geometry("scan", SceneObjectKind.SCAN_MESH, points)

    with pytest.raises(
        ClosurePresentationError, match="visibility_action_requires_cap_scene_object"
    ):
        controller.set_visible("scan", False)


def test_replacement_action_delegates_to_core_domain_service(monkeypatch) -> None:
    viewport = ViewportService()
    controller = ClosureWorkflowController(viewport)
    observed = {}

    def domain_replacement(*args, **kwargs):
        observed["args"] = args
        observed["kwargs"] = kwargs
        return sentinel.result

    monkeypatch.setattr(closure_workflow, "replace_closure_component", domain_replacement)
    result = controller.replace(
        sentinel.scan_master,
        sentinel.history,
        sentinel.replacement_base,
        sentinel.mating_references,
        current_closure_feature_id="old-feature",
        replacement_closure_feature_id="new-feature",
        current_closure_parameter_ids=(),
        replacement_closure_parameter_ids=(),
        expected_scan_master_revision_id="scan-revision",
        expected_current_model_revision_id="current-revision",
        expected_replacement_base_revision_id="replacement-revision",
        actor_id="test-actor",
        reason="test replacement",
        created_at_utc="2026-10-03T00:00:00Z",
    )
    assert result is sentinel.result
    assert observed["args"] == (
        sentinel.scan_master,
        sentinel.history,
        sentinel.replacement_base,
        sentinel.mating_references,
    )
    assert observed["kwargs"] == {
        "current_closure_feature_id": "old-feature",
        "replacement_closure_feature_id": "new-feature",
        "current_closure_parameter_ids": (),
        "replacement_closure_parameter_ids": (),
        "expected_scan_master_revision_id": "scan-revision",
        "expected_current_model_revision_id": "current-revision",
        "expected_replacement_base_revision_id": "replacement-revision",
        "actor_id": "test-actor",
        "reason": "test replacement",
        "created_at_utc": "2026-10-03T00:00:00Z",
    }
