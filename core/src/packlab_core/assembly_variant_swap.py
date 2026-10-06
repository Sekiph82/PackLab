"""Explicit trigger/pump variant replacement with immutable assembly snapshot history."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .assembly_graph import (
    AssemblyComponentInput,
    AssemblyComponentRole,
    AssemblyGraphError,
    ParametricAssemblyGraph,
    create_parametric_assembly_graph,
    validate_parametric_assembly_graph,
)
from .design_model import (
    DesignModelError,
    DesignModelRevision,
    FeatureKind,
    resolve_design_model_feature,
)
from .dip_tube import (
    DipTubeComponentRevision,
    DipTubeError,
    edit_dip_tube_component,
)
from .reconstruction import ScaleState

_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class AssemblyVariantSwapError(ValueError):
    """Raised when a variant replacement is stale or attachment-incompatible."""


@dataclass(frozen=True, slots=True)
class AssemblyGraphSnapshot:
    """Immutable exact graph plus the Design Model inputs needed to validate that revision."""

    graph: ParametricAssemblyGraph
    components: tuple[AssemblyComponentInput, ...]

    def __post_init__(self) -> None:
        try:
            validate_parametric_assembly_graph(self.graph, self.components)
        except AssemblyGraphError as error:
            raise AssemblyVariantSwapError("assembly_snapshot_invalid") from error

    @property
    def revision_id(self) -> str:
        return self.graph.revision_id


@dataclass(frozen=True, slots=True)
class AssemblyVariantSwapHistory:
    """Bounded immutable snapshot history compatible with undo, redo and branch invalidation."""

    current: AssemblyGraphSnapshot
    undo_snapshots: tuple[AssemblyGraphSnapshot, ...] = ()
    redo_snapshots: tuple[AssemblyGraphSnapshot, ...] = ()
    maximum_entries: int = 32

    def __post_init__(self) -> None:
        if (
            not isinstance(self.current, AssemblyGraphSnapshot)
            or not isinstance(self.undo_snapshots, tuple)
            or not isinstance(self.redo_snapshots, tuple)
            or any(
                not isinstance(item, AssemblyGraphSnapshot)
                for item in (*self.undo_snapshots, *self.redo_snapshots)
            )
            or isinstance(self.maximum_entries, bool)
            or not isinstance(self.maximum_entries, int)
            or not 1 <= self.maximum_entries <= 128
            or len(self.undo_snapshots) > self.maximum_entries
            or len(self.redo_snapshots) > self.maximum_entries
        ):
            raise AssemblyVariantSwapError("assembly_variant_history_invalid")

    @property
    def can_undo(self) -> bool:
        return bool(self.undo_snapshots)

    @property
    def can_redo(self) -> bool:
        return bool(self.redo_snapshots)

    def apply(self, snapshot: AssemblyGraphSnapshot) -> AssemblyVariantSwapHistory:
        if not isinstance(snapshot, AssemblyGraphSnapshot):
            raise AssemblyVariantSwapError("assembly_snapshot_required")
        return AssemblyVariantSwapHistory(
            snapshot,
            (*self.undo_snapshots, self.current)[-self.maximum_entries :],
            (),
            self.maximum_entries,
        )

    def undo(self) -> AssemblyVariantSwapHistory:
        if not self.undo_snapshots:
            raise AssemblyVariantSwapError("assembly_undo_history_empty")
        return AssemblyVariantSwapHistory(
            self.undo_snapshots[-1],
            self.undo_snapshots[:-1],
            (*self.redo_snapshots, self.current)[-self.maximum_entries :],
            self.maximum_entries,
        )

    def redo(self) -> AssemblyVariantSwapHistory:
        if not self.redo_snapshots:
            raise AssemblyVariantSwapError("assembly_redo_history_empty")
        return AssemblyVariantSwapHistory(
            self.redo_snapshots[-1],
            (*self.undo_snapshots, self.current)[-self.maximum_entries :],
            self.redo_snapshots[:-1],
            self.maximum_entries,
        )


@dataclass(frozen=True, slots=True)
class AssemblyVariantSwapRevision:
    revision_id: str
    previous_assembly_graph_revision_id: str
    assembly_graph_revision_id: str
    body_model_revision_id: str
    closure_model_revision_id: str
    previous_trigger_pump_model_revision_id: str
    trigger_pump_model_revision_id: str
    previous_dip_tube_model_revision_id: str
    dip_tube_model_revision_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    attachment_semantic_key: str
    scale_state: ScaleState
    coordinate_unit: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.assembly-trigger-pump-variant-swap.v1",
            "revision_id": self.revision_id,
            "previous_assembly_graph_revision_id": self.previous_assembly_graph_revision_id,
            "assembly_graph_revision_id": self.assembly_graph_revision_id,
            "body_model_revision_id": self.body_model_revision_id,
            "closure_model_revision_id": self.closure_model_revision_id,
            "previous_trigger_pump_model_revision_id": self.previous_trigger_pump_model_revision_id,
            "trigger_pump_model_revision_id": self.trigger_pump_model_revision_id,
            "previous_dip_tube_model_revision_id": self.previous_dip_tube_model_revision_id,
            "dip_tube_model_revision_id": self.dip_tube_model_revision_id,
            "scan_master_revision_id": self.scan_master_revision_id,
            "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            "attachment_semantic_key": self.attachment_semantic_key,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "authority_class": "PARAMETRIC_ASSEMBLY_METADATA",
            "physical_accuracy_validation_status": _DEFERRED,
            "mold_use_authorized": False,
            "body_geometry_modified": False,
            "scan_master_modified": False,
            "physical_attachment_compatibility_claimed": False,
            "manufacturing_compatibility_claimed": False,
        }


@dataclass(frozen=True, slots=True)
class AssemblyVariantSwapResult:
    revision: AssemblyVariantSwapRevision
    snapshot: AssemblyGraphSnapshot
    history: AssemblyVariantSwapHistory


def swap_trigger_pump_variant(
    current_graph: ParametricAssemblyGraph,
    current_components: tuple[AssemblyComponentInput, ...],
    dip_tube: DipTubeComponentRevision,
    candidate_trigger_pump_model: DesignModelRevision,
    *,
    expected_current_graph_revision_id: str,
    expected_current_dip_tube_revision_id: str,
    expected_candidate_pump_revision_id: str,
    candidate_pump_feature_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    history: AssemblyVariantSwapHistory | None = None,
) -> AssemblyVariantSwapResult:
    """Replace one explicitly compatible pump variant and re-pin its dip-tube attachment."""
    if current_graph.revision_id != expected_current_graph_revision_id:
        raise AssemblyVariantSwapError("assembly_graph_revision_stale")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 700:
        raise AssemblyVariantSwapError("assembly_variant_swap_reason_invalid")
    try:
        validate_parametric_assembly_graph(current_graph, current_components)
    except AssemblyGraphError as error:
        raise AssemblyVariantSwapError(str(error)) from error
    if not isinstance(dip_tube, DipTubeComponentRevision):
        raise AssemblyVariantSwapError("dip_tube_component_required")
    if dip_tube.revision_id != expected_current_dip_tube_revision_id:
        raise AssemblyVariantSwapError("dip_tube_revision_stale")
    if not isinstance(candidate_trigger_pump_model, DesignModelRevision):
        raise AssemblyVariantSwapError("candidate_trigger_pump_model_required")
    if candidate_trigger_pump_model.revision_id != expected_candidate_pump_revision_id:
        raise AssemblyVariantSwapError("candidate_trigger_pump_revision_stale")

    by_role = {item.role: item for item in current_components}
    old_pump = by_role[AssemblyComponentRole.TRIGGER_PUMP]
    old_pump_model = old_pump.model
    tube_input = by_role[AssemblyComponentRole.DIP_TUBE]
    if (
        dip_tube.model.revision_id != tube_input.model.revision_id
        or dip_tube.feature_id != tube_input.feature_id
        or dip_tube.attachment.trigger_pump_model_revision_id != old_pump_model.revision_id
        or dip_tube.attachment.trigger_pump_feature_id != old_pump.feature_id
    ):
        raise AssemblyVariantSwapError("dip_tube_attachment_stale")
    if candidate_trigger_pump_model.revision_id == old_pump_model.revision_id:
        raise AssemblyVariantSwapError("candidate_pump_is_current_variant")
    try:
        old_feature = resolve_design_model_feature(old_pump_model, old_pump.feature_id)
        candidate_feature = resolve_design_model_feature(
            candidate_trigger_pump_model, candidate_pump_feature_id
        )
    except DesignModelError as error:
        raise AssemblyVariantSwapError("trigger_pump_variant_feature_stale") from error
    if (
        old_feature.feature_kind is not FeatureKind.TRIGGER_PUMP
        or candidate_feature.feature_kind is not FeatureKind.TRIGGER_PUMP
        or candidate_feature.semantic_key != old_feature.semantic_key
    ):
        raise AssemblyVariantSwapError("trigger_pump_attachment_semantic_incompatible")
    body = by_role[AssemblyComponentRole.BODY].model
    closure = by_role[AssemblyComponentRole.CLOSURE].model
    body_scan_master_revision_id = body.fitted_to_scan_master_revision_id
    body_scan_master_geometry_sha256 = body.scan_master_geometry_sha256
    if (
        body.parent_binding_revision_id is None
        or body_scan_master_revision_id is None
        or body_scan_master_geometry_sha256 is None
    ):
        raise AssemblyVariantSwapError("assembly_captured_scan_master_parent_required")
    if (
        candidate_trigger_pump_model.project_id != old_pump_model.project_id
        or candidate_trigger_pump_model.fitted_to_scan_master_revision_id
        != old_pump_model.fitted_to_scan_master_revision_id
        or candidate_trigger_pump_model.scan_master_geometry_sha256
        != old_pump_model.scan_master_geometry_sha256
        or candidate_trigger_pump_model.scale_state is not current_graph.scale_state
        or candidate_trigger_pump_model.scale_state is not old_pump_model.scale_state
        or candidate_trigger_pump_model.coordinate_unit != current_graph.coordinate_unit
        or candidate_trigger_pump_model.scale_provenance_id != old_pump_model.scale_provenance_id
        or candidate_trigger_pump_model.physical_accuracy_validation_status != _DEFERRED
        or candidate_trigger_pump_model.mold_use_authorized is not False
    ):
        raise AssemblyVariantSwapError("trigger_pump_variant_parent_or_scale_incompatible")

    if history is not None and history.current.revision_id != current_graph.revision_id:
        raise AssemblyVariantSwapError("assembly_variant_history_stale")
    try:
        revised_tube = edit_dip_tube_component(
            dip_tube,
            candidate_trigger_pump_model,
            expected_current_revision_id=dip_tube.revision_id,
            expected_trigger_pump_revision_id=candidate_trigger_pump_model.revision_id,
            trigger_pump_feature_id=candidate_pump_feature_id,
            path=dip_tube.path,
            length=dip_tube.length,
            diameter=dip_tube.diameter,
            actor_id=actor_id,
            reason=f"Rebind dip tube for explicit pump variant swap: {reason}",
            created_at_utc=created_at_utc,
        )
    except DipTubeError as error:
        raise AssemblyVariantSwapError(f"dip_tube_attachment_rebind_failed:{error}") from error

    updated_components = tuple(
        AssemblyComponentInput(
            item.role,
            candidate_trigger_pump_model,
            candidate_trigger_pump_model.revision_id,
            candidate_pump_feature_id,
        )
        if item.role is AssemblyComponentRole.TRIGGER_PUMP
        else AssemblyComponentInput(
            item.role,
            revised_tube.model,
            revised_tube.revision_id,
            revised_tube.feature_id,
        )
        if item.role is AssemblyComponentRole.DIP_TUBE
        else item
        for item in current_components
    )
    try:
        new_graph = create_parametric_assembly_graph(
            updated_components,
            expected_component_revision_ids={
                item.role: item.model.revision_id for item in updated_components
            },
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
        validate_parametric_assembly_graph(new_graph, updated_components)
    except AssemblyGraphError as error:
        raise AssemblyVariantSwapError(f"replacement_assembly_invalid:{error}") from error
    snapshot = AssemblyGraphSnapshot(new_graph, updated_components)
    current_snapshot = AssemblyGraphSnapshot(current_graph, current_components)
    active_history = history or AssemblyVariantSwapHistory(current_snapshot)
    updated_history = active_history.apply(snapshot)
    identity = {
        "contract": "packlab.assembly-trigger-pump-variant-swap.v1",
        "previous_assembly_graph_revision_id": current_graph.revision_id,
        "assembly_graph_revision_id": new_graph.revision_id,
        "previous_trigger_pump_model_revision_id": old_pump_model.revision_id,
        "trigger_pump_model_revision_id": candidate_trigger_pump_model.revision_id,
        "previous_dip_tube_model_revision_id": dip_tube.revision_id,
        "dip_tube_model_revision_id": revised_tube.revision_id,
        "body_model_revision_id": body.revision_id,
        "closure_model_revision_id": closure.revision_id,
        "scan_master_revision_id": body_scan_master_revision_id,
        "scan_master_geometry_sha256": body_scan_master_geometry_sha256,
        "attachment_semantic_key": candidate_feature.semantic_key,
    }
    revision_id = (
        "assembly-variant-swap:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
    )
    revision = AssemblyVariantSwapRevision(
        revision_id,
        current_graph.revision_id,
        new_graph.revision_id,
        body.revision_id,
        closure.revision_id,
        old_pump_model.revision_id,
        candidate_trigger_pump_model.revision_id,
        dip_tube.revision_id,
        revised_tube.revision_id,
        body_scan_master_revision_id,
        body_scan_master_geometry_sha256,
        candidate_feature.semantic_key,
        current_graph.scale_state,
        current_graph.coordinate_unit,
    )
    return AssemblyVariantSwapResult(revision, snapshot, updated_history)


__all__ = [
    "AssemblyGraphSnapshot",
    "AssemblyVariantSwapError",
    "AssemblyVariantSwapHistory",
    "AssemblyVariantSwapResult",
    "AssemblyVariantSwapRevision",
    "swap_trigger_pump_variant",
]
