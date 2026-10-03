"""Studio actions that delegate closure state changes to owned services."""

from __future__ import annotations

from packlab_core.closure_workflow import (
    ClosureReplacementResult,
    ClosureWorkflowError,
    ClosureWorkflowHistory,
    replace_closure_component,
)
from packlab_core.design_model import DesignModelRevision
from packlab_core.mating_references import MatingReferenceResult
from packlab_core.scan_master import ScanMasterRevision

from .viewport import SceneObjectKind, ViewportService


class ClosurePresentationError(ValueError):
    """Raised when a viewport visibility action does not target a closure scene item."""


class ClosureWorkflowController:
    """Thin Studio controller; model and replacement authority stays in PackLab core."""

    def __init__(self, viewport: ViewportService) -> None:
        if not isinstance(viewport, ViewportService):
            raise ClosurePresentationError("viewport_service_required")
        self.viewport = viewport

    def set_visible(self, closure_feature_id: str, visible: bool) -> None:
        if not isinstance(closure_feature_id, str) or not closure_feature_id.strip():
            raise ClosurePresentationError("closure_feature_id_required")
        if not isinstance(visible, bool):
            raise ClosurePresentationError("visibility_value_must_be_boolean")
        try:
            scene_object = self.viewport.scene.get(closure_feature_id)
        except KeyError as error:
            raise ClosurePresentationError("closure_scene_object_missing") from error
        if scene_object.kind is not SceneObjectKind.CAP:
            raise ClosurePresentationError("visibility_action_requires_cap_scene_object")
        self.viewport.set_visible(closure_feature_id, visible)

    def replace(
        self,
        scan_master: ScanMasterRevision,
        history: ClosureWorkflowHistory,
        replacement_base_model: DesignModelRevision,
        mating_references: MatingReferenceResult,
        *,
        current_closure_feature_id: str,
        replacement_closure_feature_id: str,
        current_closure_parameter_ids: tuple[str, ...],
        replacement_closure_parameter_ids: tuple[str, ...],
        expected_scan_master_revision_id: str,
        expected_current_model_revision_id: str,
        expected_replacement_base_revision_id: str,
        actor_id: str,
        reason: str,
        created_at_utc: str,
    ) -> ClosureReplacementResult:
        """Forward a replacement intent to the PackLab core authority boundary."""
        try:
            return replace_closure_component(
                scan_master,
                history,
                replacement_base_model,
                mating_references,
                current_closure_feature_id=current_closure_feature_id,
                replacement_closure_feature_id=replacement_closure_feature_id,
                current_closure_parameter_ids=current_closure_parameter_ids,
                replacement_closure_parameter_ids=replacement_closure_parameter_ids,
                expected_scan_master_revision_id=expected_scan_master_revision_id,
                expected_current_model_revision_id=expected_current_model_revision_id,
                expected_replacement_base_revision_id=expected_replacement_base_revision_id,
                actor_id=actor_id,
                reason=reason,
                created_at_utc=created_at_utc,
            )
        except ClosureWorkflowError:
            raise

    def undo(
        self, history: ClosureWorkflowHistory, *, actor_id: str, created_at_utc: str
    ) -> ClosureWorkflowHistory:
        return history.undo(actor_id=actor_id, created_at_utc=created_at_utc)

    def redo(
        self, history: ClosureWorkflowHistory, *, actor_id: str, created_at_utc: str
    ) -> ClosureWorkflowHistory:
        return history.redo(actor_id=actor_id, created_at_utc=created_at_utc)


__all__ = ["ClosurePresentationError", "ClosureWorkflowController"]
