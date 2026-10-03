"""Non-destructive closure visibility and Design Model replacement workflow."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    ParameterType,
    revise_design_model_revision,
)
from .mating_references import MatingReferenceResult, MatingReferenceStatus
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_CAP_PREFIX = "closure_replacement_state_"


class ClosureWorkflowError(ValueError):
    """Raised when a closure visibility/replacement action lacks exact authority."""


@dataclass(frozen=True, slots=True)
class ClosureWorkflowHistory:
    """Bounded snapshot history for atomic closure component replacement undo/redo."""

    current_revision: DesignModelRevision
    undo_revisions: tuple[DesignModelRevision, ...] = ()
    redo_revisions: tuple[DesignModelRevision, ...] = ()
    maximum_entries: int = 32

    def __post_init__(self) -> None:
        if not isinstance(self.current_revision, DesignModelRevision):
            raise ClosureWorkflowError("design_model_revision_required")
        if not isinstance(self.undo_revisions, tuple) or not isinstance(self.redo_revisions, tuple):
            raise ClosureWorkflowError("closure_history_snapshots_must_be_tuples")
        if any(
            not isinstance(item, DesignModelRevision)
            for item in (*self.undo_revisions, *self.redo_revisions)
        ):
            raise ClosureWorkflowError("closure_history_snapshot_invalid")
        if (
            isinstance(self.maximum_entries, bool)
            or not isinstance(self.maximum_entries, int)
            or not 1 <= self.maximum_entries <= 128
            or len(self.undo_revisions) > self.maximum_entries
            or len(self.redo_revisions) > self.maximum_entries
        ):
            raise ClosureWorkflowError("closure_history_limit_invalid")

    @property
    def can_undo(self) -> bool:
        return bool(self.undo_revisions)

    @property
    def can_redo(self) -> bool:
        return bool(self.redo_revisions)

    def undo(self, *, actor_id: str, created_at_utc: str) -> ClosureWorkflowHistory:
        if not self.undo_revisions:
            raise ClosureWorkflowError("closure_undo_history_empty")
        target = self.undo_revisions[-1]
        restored = _restore_graph(
            self.current_revision,
            target,
            actor_id=actor_id,
            reason=f"Undo closure replacement from {self.current_revision.revision_id}",
            created_at_utc=created_at_utc,
        )
        return ClosureWorkflowHistory(
            restored,
            self.undo_revisions[:-1],
            (*self.redo_revisions, self.current_revision)[-self.maximum_entries :],
            self.maximum_entries,
        )

    def redo(self, *, actor_id: str, created_at_utc: str) -> ClosureWorkflowHistory:
        if not self.redo_revisions:
            raise ClosureWorkflowError("closure_redo_history_empty")
        target = self.redo_revisions[-1]
        reapplied = _restore_graph(
            self.current_revision,
            target,
            actor_id=actor_id,
            reason=f"Redo closure replacement toward {target.revision_id}",
            created_at_utc=created_at_utc,
        )
        return ClosureWorkflowHistory(
            reapplied,
            (*self.undo_revisions, self.current_revision)[-self.maximum_entries :],
            self.redo_revisions[:-1],
            self.maximum_entries,
        )


@dataclass(frozen=True, slots=True)
class ClosureReplacementResult:
    previous_model_revision_id: str
    replacement_source_revision_id: str
    current_closure_feature_id: str
    replacement_closure_feature_id: str
    mating_reference_set_id: str
    model: DesignModelRevision
    history: ClosureWorkflowHistory
    body_feature_ids: tuple[str, ...]
    scan_master_geometry_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.closure-replacement.v1",
            "previous_model_revision_id": self.previous_model_revision_id,
            "replacement_source_revision_id": self.replacement_source_revision_id,
            "model_revision_id": self.model.revision_id,
            "current_closure_feature_id": self.current_closure_feature_id,
            "replacement_closure_feature_id": self.replacement_closure_feature_id,
            "mating_reference_set_id": self.mating_reference_set_id,
            "body_feature_ids": list(self.body_feature_ids),
            "scan_master_revision_id": self.model.fitted_to_scan_master_revision_id,
            "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            "coordinate_unit": self.model.coordinate_unit,
            "physical_accuracy_validation_status": _DEFERRED,
            "mold_use_authorized": False,
            "thread_compatibility_claimed": False,
            "seal_compatibility_claimed": False,
            "scan_master_mutated": False,
        }


def replace_closure_component(
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
    """Replace only a CAP feature after exact parent/body/mating-reference checks."""
    if not isinstance(scan_master, ScanMasterRevision):
        raise ClosureWorkflowError("scan_master_revision_required")
    if not isinstance(history, ClosureWorkflowHistory):
        raise ClosureWorkflowError("closure_workflow_history_required")
    current = history.current_revision
    if current.revision_id != expected_current_model_revision_id:
        raise ClosureWorkflowError("current_design_model_revision_stale")
    if not isinstance(replacement_base_model, DesignModelRevision):
        raise ClosureWorkflowError("replacement_design_model_revision_required")
    if replacement_base_model.revision_id != expected_replacement_base_revision_id:
        raise ClosureWorkflowError("replacement_design_model_revision_stale")
    if not isinstance(mating_references, MatingReferenceResult):
        raise ClosureWorkflowError("replacement_mating_reference_required")
    replacement_model = mating_references.model
    if not isinstance(replacement_model, DesignModelRevision):
        raise ClosureWorkflowError("replacement_mating_reference_model_required")
    _validate_common_parent(
        scan_master,
        current,
        replacement_base_model,
        replacement_model,
        expected_scan_master_revision_id,
    )

    if replacement_base_model.previous_revision_id != current.revision_id:
        raise ClosureWorkflowError("replacement_model_not_derived_from_current_revision")
    if (
        mating_references.status is not MatingReferenceStatus.ALIGNED
        or mating_references.review_required
        or mating_references.source_model_revision_id != replacement_base_model.revision_id
        or replacement_model.previous_revision_id != replacement_base_model.revision_id
        or mating_references.scan_master_revision_id != scan_master.revision_id
        or mating_references.scan_master_geometry_sha256 != mesh_sha256(scan_master.mesh)
        or mating_references.closure_feature_id != replacement_closure_feature_id
    ):
        raise ClosureWorkflowError("replacement_mating_reference_stale_or_incompatible")

    current_cap = _cap_feature(current, current_closure_feature_id, "current")
    replacement_cap = _cap_feature(
        replacement_base_model, replacement_closure_feature_id, "replacement"
    )
    if current_cap.feature_id == replacement_cap.feature_id:
        raise ClosureWorkflowError("replacement_closure_feature_must_differ")
    current_non_cap = tuple(
        item for item in current.features if item.feature_kind is not FeatureKind.CAP
    )
    replacement_non_cap = tuple(
        item for item in replacement_base_model.features if item.feature_kind is not FeatureKind.CAP
    )
    if current_non_cap != replacement_non_cap:
        raise ClosureWorkflowError("replacement_changes_non_closure_features")
    body_feature_ids = tuple(
        sorted(
            item.feature_id for item in current.features if item.feature_kind is FeatureKind.BODY
        )
    )
    replacement_body_ids = tuple(
        sorted(
            item.feature_id
            for item in replacement_base_model.features
            if item.feature_kind is FeatureKind.BODY
        )
    )
    if body_feature_ids != replacement_body_ids:
        raise ClosureWorkflowError("replacement_body_feature_identity_changed")
    if mating_references.neck_feature_id not in {item.feature_id for item in current_non_cap}:
        raise ClosureWorkflowError("replacement_neck_mating_feature_missing")
    if mating_references.neck_feature_id not in {item.feature_id for item in replacement_non_cap}:
        raise ClosureWorkflowError("replacement_neck_mating_feature_changed")

    _validate_parameter_ids(current, current_closure_parameter_ids, "current")
    _validate_parameter_ids(
        replacement_base_model, replacement_closure_parameter_ids, "replacement"
    )
    _validate_parameters_reference_feature(
        current, current_closure_parameter_ids, current_cap, "current"
    )
    _validate_parameters_reference_feature(
        replacement_base_model,
        replacement_closure_parameter_ids,
        replacement_cap,
        "replacement",
    )
    reference_parameters = tuple(
        item
        for item in replacement_model.parameters
        if _parameter_reference_set_id(item) == mating_references.reference_set_id
    )
    if len(reference_parameters) != 1:
        raise ClosureWorkflowError("replacement_mating_reference_parameter_missing_or_ambiguous")

    current_parameter_ids = set(current_closure_parameter_ids)
    replacement_parameter_ids = set(replacement_closure_parameter_ids)
    retained = tuple(
        item for item in current.parameters if item.parameter_id not in current_parameter_ids
    )
    replaced_features = tuple(
        item for item in current.features if item.feature_id != current_closure_feature_id
    )
    if any(item.feature_id == replacement_cap.feature_id for item in replaced_features):
        raise ClosureWorkflowError("replacement_feature_id_already_present")
    final_features = (*replaced_features, replacement_cap)
    replacement_parameters = tuple(
        item
        for item in replacement_base_model.parameters
        if item.parameter_id in replacement_parameter_ids
    )
    all_replacement_parameters = (*replacement_parameters, reference_parameters[0])
    retained_ids = {item.parameter_id for item in retained}
    if any(item.parameter_id in retained_ids for item in all_replacement_parameters):
        raise ClosureWorkflowError("replacement_parameter_id_conflicts_with_retained_state")

    state_id = _replacement_state_parameter_id(
        current_closure_feature_id, replacement_closure_feature_id
    )
    state_parameter = DesignModelParameter(
        state_id,
        {
            "contract": "packlab.active-closure-component.v1",
            "active_closure_feature_id": replacement_cap.feature_id,
            "replaced_closure_feature_id": current_cap.feature_id,
            "mating_reference_set_id": mating_references.reference_set_id,
            "reference_source_model_revision_id": mating_references.source_model_revision_id,
            "replacement_source_model_revision_id": replacement_base_model.revision_id,
            "body_feature_ids": list(body_feature_ids),
            "thread_compatibility_claimed": False,
            "seal_compatibility_claimed": False,
            "manufacturing_alignment_claimed": False,
            "physical_accuracy_validation_status": _DEFERRED,
            "mold_use_authorized": False,
        },
        ParameterType.OBJECT,
    )
    if state_id in retained_ids or state_id in {
        item.parameter_id for item in all_replacement_parameters
    }:
        raise ClosureWorkflowError("closure_replacement_state_parameter_conflict")
    try:
        updated = revise_design_model_revision(
            current,
            parameters=(*retained, *all_replacement_parameters, state_parameter),
            features=final_features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise ClosureWorkflowError("closure_replacement_revision_invalid") from error
    updated_history = ClosureWorkflowHistory(
        updated,
        (*history.undo_revisions, current)[-history.maximum_entries :],
        (),
        history.maximum_entries,
    )
    return ClosureReplacementResult(
        current.revision_id,
        replacement_base_model.revision_id,
        current_cap.feature_id,
        replacement_cap.feature_id,
        mating_references.reference_set_id,
        updated,
        updated_history,
        body_feature_ids,
        mesh_sha256(scan_master.mesh),
    )


def _validate_common_parent(
    scan_master: ScanMasterRevision,
    current: DesignModelRevision,
    replacement: DesignModelRevision,
    replacement_with_references: DesignModelRevision,
    expected_scan_master_revision_id: str,
) -> None:
    digest = mesh_sha256(scan_master.mesh)
    manifest = scan_master.manifest
    raw_scale = manifest.get("scale_state")
    if not isinstance(raw_scale, str):
        raise ClosureWorkflowError("scan_master_scale_state_invalid")
    try:
        scale_state = ScaleState(raw_scale)
    except ValueError as error:
        raise ClosureWorkflowError("scan_master_scale_state_invalid") from error
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise ClosureWorkflowError("closure_replacement_metric_state_not_authorized")
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    if (
        scan_master.revision_id != expected_scan_master_revision_id
        or manifest.get("scan_master_revision_id") != scan_master.revision_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != digest
        or manifest.get("physical_accuracy_validation_status") != _DEFERRED
        or manifest.get("mold_use_authorized") is not False
    ):
        raise ClosureWorkflowError("selected_scan_master_parent_stale_or_invalid")
    for model in (current, replacement, replacement_with_references):
        if (
            model.project_id != scan_master.project_id
            or model.fitted_to_scan_master_revision_id != scan_master.revision_id
            or model.scan_master_geometry_sha256 != digest
            or model.parent_binding_revision_id != current.parent_binding_revision_id
            or model.scale_state is not scale_state
            or model.coordinate_unit != unit
            or model.scale_provenance_id != manifest.get("scale_provenance_id")
            or model.physical_accuracy_validation_status != _DEFERRED
            or model.mold_use_authorized is not False
        ):
            raise ClosureWorkflowError("closure_replacement_parent_or_authority_mismatch")


def _cap_feature(
    model: DesignModelRevision, feature_id: str, role: str
) -> DesignModelFeatureReference:
    matches = tuple(item for item in model.features if item.feature_id == feature_id)
    if len(matches) != 1:
        raise ClosureWorkflowError(f"{role}_closure_feature_stale_or_ambiguous")
    if matches[0].feature_kind is not FeatureKind.CAP:
        raise ClosureWorkflowError(f"{role}_closure_feature_kind_invalid")
    return matches[0]


def _validate_parameter_ids(
    model: DesignModelRevision, parameter_ids: tuple[str, ...], role: str
) -> None:
    if not isinstance(parameter_ids, tuple) or any(
        not isinstance(item, str) or not item.strip() for item in parameter_ids
    ):
        raise ClosureWorkflowError(f"{role}_closure_parameter_ids_must_be_tuple")
    if len(set(parameter_ids)) != len(parameter_ids):
        raise ClosureWorkflowError(f"{role}_closure_parameter_ids_not_unique")
    model_ids = {item.parameter_id for item in model.parameters}
    if any(item not in model_ids for item in parameter_ids):
        raise ClosureWorkflowError(f"{role}_closure_parameter_id_stale")


def _validate_parameters_reference_feature(
    model: DesignModelRevision,
    parameter_ids: tuple[str, ...],
    feature: DesignModelFeatureReference,
    role: str,
) -> None:
    parameters = {item.parameter_id: item for item in model.parameters}
    for parameter_id in parameter_ids:
        parameter = parameters[parameter_id]
        if parameter.value_type is not ParameterType.OBJECT:
            raise ClosureWorkflowError(f"{role}_closure_parameter_not_object")
        values = _string_values(parameter.as_dict()["value"])
        if feature.feature_id not in values and feature.component_id not in values:
            raise ClosureWorkflowError(f"{role}_closure_parameter_feature_binding_missing")


def _string_values(value: object) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return set().union(*(_string_values(item) for item in value)) if value else set()
    if isinstance(value, dict):
        return set().union(*(_string_values(item) for item in value.values())) if value else set()
    return set()


def _parameter_reference_set_id(parameter: DesignModelParameter) -> str | None:
    value = parameter.as_dict()["value"]
    if isinstance(value, dict):
        reference_set_id = value.get("reference_set_id")
        if isinstance(reference_set_id, str):
            return reference_set_id
    return None


def _replacement_state_parameter_id(current_feature_id: str, replacement_feature_id: str) -> str:
    digest = hashlib.sha256(f"{current_feature_id}:{replacement_feature_id}".encode()).hexdigest()
    return _CAP_PREFIX + digest[:32]


def _restore_graph(
    current: DesignModelRevision,
    target: DesignModelRevision,
    *,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelRevision:
    if (
        target.project_id != current.project_id
        or target.parent_binding_revision_id != current.parent_binding_revision_id
        or target.fitted_to_scan_master_revision_id != current.fitted_to_scan_master_revision_id
        or target.scan_master_geometry_sha256 != current.scan_master_geometry_sha256
        or target.scale_state is not current.scale_state
        or target.scale_provenance_id != current.scale_provenance_id
    ):
        raise ClosureWorkflowError("closure_history_parent_mismatch")
    try:
        return revise_design_model_revision(
            current,
            parameters=target.parameters,
            features=target.features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise ClosureWorkflowError("closure_history_revision_invalid") from error


__all__ = [
    "ClosureReplacementResult",
    "ClosureWorkflowError",
    "ClosureWorkflowHistory",
    "replace_closure_component",
]
