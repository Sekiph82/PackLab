"""Immutable metadata graph joining exact parametric packaging component revisions."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .design_model import (
    DesignModelError,
    DesignModelRevision,
    FeatureKind,
    resolve_design_model_feature,
)
from .reconstruction import ScaleState

_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_REQUIRED_ROLES = frozenset({"body", "closure", "trigger_pump", "dip_tube"})
_ROLE_FEATURE_KIND = {
    "body": FeatureKind.BODY,
    "closure": FeatureKind.CAP,
    "trigger_pump": FeatureKind.TRIGGER_PUMP,
    "dip_tube": FeatureKind.DIP_TUBE,
}
_RELATIONSHIP_ROLES = {
    "body_to_closure": ("body", "closure"),
    "closure_to_trigger_pump": ("closure", "trigger_pump"),
    "trigger_pump_to_dip_tube": ("trigger_pump", "dip_tube"),
}


class AssemblyGraphError(ValueError):
    """Raised when assembly roles, references, or component ancestry are invalid."""


class AssemblyComponentRole(StrEnum):
    BODY = "body"
    CLOSURE = "closure"
    TRIGGER_PUMP = "trigger_pump"
    DIP_TUBE = "dip_tube"


class AssemblyRelationshipKind(StrEnum):
    BODY_TO_CLOSURE = "body_to_closure"
    CLOSURE_TO_TRIGGER_PUMP = "closure_to_trigger_pump"
    TRIGGER_PUMP_TO_DIP_TUBE = "trigger_pump_to_dip_tube"


@dataclass(frozen=True, slots=True)
class AssemblyComponentInput:
    """A caller-pinned Design Model and stable feature selected for one assembly role."""

    role: AssemblyComponentRole
    model: DesignModelRevision
    expected_model_revision_id: str
    feature_id: str


@dataclass(frozen=True, slots=True)
class AssemblyComponentReference:
    """Serialized exact component and captured-parent ancestry; never a geometry payload."""

    role: AssemblyComponentRole
    model_revision_id: str
    feature_id: str
    component_id: str
    feature_kind: FeatureKind
    project_id: str
    parent_binding_revision_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    previous_model_revision_id: str | None
    scale_state: ScaleState
    scale_provenance_id: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role.value,
            "model_revision_id": self.model_revision_id,
            "feature_id": self.feature_id,
            "component_id": self.component_id,
            "feature_kind": self.feature_kind.value,
            "project_id": self.project_id,
            "parent": {
                "binding_revision_id": self.parent_binding_revision_id,
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            },
            "previous_model_revision_id": self.previous_model_revision_id,
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


@dataclass(frozen=True, slots=True)
class AssemblyFeatureRelationship:
    """Stable role-to-role reference; it does not assert geometric fit or compatibility."""

    relationship_id: str
    kind: AssemblyRelationshipKind
    source_role: AssemblyComponentRole
    source_feature_id: str
    target_role: AssemblyComponentRole
    target_feature_id: str

    def __post_init__(self) -> None:
        _identifier(self.relationship_id, "relationship_id")
        _identifier(self.source_feature_id, "source_feature_id")
        _identifier(self.target_feature_id, "target_feature_id")
        if not isinstance(self.kind, AssemblyRelationshipKind):
            raise AssemblyGraphError("assembly_relationship_kind_invalid")
        if not isinstance(self.source_role, AssemblyComponentRole) or not isinstance(
            self.target_role, AssemblyComponentRole
        ):
            raise AssemblyGraphError("assembly_relationship_role_invalid")
        expected = _RELATIONSHIP_ROLES[self.kind.value]
        if (self.source_role.value, self.target_role.value) != expected:
            raise AssemblyGraphError("assembly_relationship_roles_invalid")

    def as_dict(self) -> dict[str, str]:
        return {
            "relationship_id": self.relationship_id,
            "kind": self.kind.value,
            "source_role": self.source_role.value,
            "source_feature_id": self.source_feature_id,
            "target_role": self.target_role.value,
            "target_feature_id": self.target_feature_id,
        }


@dataclass(frozen=True, slots=True)
class ParametricAssemblyGraph:
    """Versioned immutable role graph; component Design Models remain their own authority."""

    revision_id: str
    project_id: str
    components: tuple[AssemblyComponentReference, ...]
    relationships: tuple[AssemblyFeatureRelationship, ...]
    scale_state: ScaleState
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    actor_id: str
    reason: str
    created_at_utc: str

    def __post_init__(self) -> None:
        _identifier(self.project_id, "project_id")
        _identifier(self.actor_id, "actor_id")
        if not isinstance(self.components, tuple) or any(
            not isinstance(item, AssemblyComponentReference) for item in self.components
        ):
            raise AssemblyGraphError("assembly_components_must_be_immutable_tuple")
        if not isinstance(self.relationships, tuple) or any(
            not isinstance(item, AssemblyFeatureRelationship) for item in self.relationships
        ):
            raise AssemblyGraphError("assembly_relationships_must_be_immutable_tuple")
        if self.physical_accuracy_validation_status != _DEFERRED:
            raise AssemblyGraphError("assembly_physical_validation_must_remain_deferred")
        if self.mold_use_authorized is not False:
            raise AssemblyGraphError("assembly_mold_use_forbidden")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 1000:
            raise AssemblyGraphError("assembly_revision_reason_invalid")
        _timestamp(self.created_at_utc)
        if self.revision_id != _revision_id(self):
            raise AssemblyGraphError("assembly_revision_id_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.parametric-assembly-graph.v1",
            "revision_id": self.revision_id,
            "project_id": self.project_id,
            "components": [item.as_dict() for item in self.components],
            "relationships": [item.as_dict() for item in self.relationships],
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "authority_class": "PARAMETRIC_ASSEMBLY_METADATA",
            "geometry_embedded": False,
            "geometry_exported": False,
            "actor_id": self.actor_id,
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
        }


def create_parametric_assembly_graph(
    components: tuple[AssemblyComponentInput, ...],
    *,
    expected_component_revision_ids: Mapping[AssemblyComponentRole, str],
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> ParametricAssemblyGraph:
    """Pin required roles and explicit stable feature relationships without retargeting."""
    if not isinstance(components, tuple) or any(
        not isinstance(item, AssemblyComponentInput) for item in components
    ):
        raise AssemblyGraphError("assembly_component_inputs_must_be_immutable_tuple")
    role_names = tuple(item.role.value for item in components)
    if len(role_names) != len(set(role_names)):
        raise AssemblyGraphError("assembly_component_role_duplicate")
    if set(role_names) != _REQUIRED_ROLES:
        raise AssemblyGraphError("assembly_required_component_role_missing")
    if not isinstance(expected_component_revision_ids, Mapping):
        raise AssemblyGraphError("assembly_expected_revisions_required")

    references: list[AssemblyComponentReference] = []
    for item in components:
        if not isinstance(item.model, DesignModelRevision):
            raise AssemblyGraphError("assembly_component_model_required")
        if item.expected_model_revision_id != item.model.revision_id or (
            expected_component_revision_ids.get(item.role) != item.model.revision_id
        ):
            raise AssemblyGraphError("assembly_component_revision_stale")
        try:
            feature = resolve_design_model_feature(item.model, item.feature_id)
        except DesignModelError as error:
            raise AssemblyGraphError("assembly_component_feature_stale") from error
        if feature.feature_kind is not _ROLE_FEATURE_KIND[item.role.value]:
            raise AssemblyGraphError("assembly_component_feature_kind_mismatch")
        if (
            item.model.physical_accuracy_validation_status != _DEFERRED
            or item.model.mold_use_authorized is not False
        ):
            raise AssemblyGraphError("assembly_component_physical_authority_invalid")
        references.append(
            AssemblyComponentReference(
                item.role,
                item.model.revision_id,
                feature.feature_id,
                feature.component_id,
                feature.feature_kind,
                item.model.project_id,
                item.model.parent_binding_revision_id,
                item.model.fitted_to_scan_master_revision_id,
                item.model.scan_master_geometry_sha256,
                item.model.previous_revision_id,
                item.model.scale_state,
                item.model.scale_provenance_id,
                item.model.coordinate_unit,
                item.model.physical_accuracy_validation_status,
                item.model.mold_use_authorized,
            )
        )
    by_role = {item.role: item for item in references}
    projects = {item.project_id for item in references}
    scales = {item.scale_state for item in references}
    units = {item.coordinate_unit for item in references}
    if len(projects) != 1:
        raise AssemblyGraphError("assembly_component_project_mismatch")
    if len(scales) != 1 or len(units) != 1:
        raise AssemblyGraphError("assembly_component_unit_or_scale_mismatch")
    scale_state = next(iter(scales))
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise AssemblyGraphError("assembly_component_scale_unauthorized")
    expected_unit = (
        "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    )
    if units != {expected_unit}:
        raise AssemblyGraphError("assembly_component_unit_or_scale_mismatch")

    relationships = tuple(
        AssemblyFeatureRelationship(
            f"assembly-reference:{kind.value}",
            kind,
            source_role,
            by_role[source_role].feature_id,
            target_role,
            by_role[target_role].feature_id,
        )
        for kind, source_role, target_role in (
            (
                AssemblyRelationshipKind.BODY_TO_CLOSURE,
                AssemblyComponentRole.BODY,
                AssemblyComponentRole.CLOSURE,
            ),
            (
                AssemblyRelationshipKind.CLOSURE_TO_TRIGGER_PUMP,
                AssemblyComponentRole.CLOSURE,
                AssemblyComponentRole.TRIGGER_PUMP,
            ),
            (
                AssemblyRelationshipKind.TRIGGER_PUMP_TO_DIP_TUBE,
                AssemblyComponentRole.TRIGGER_PUMP,
                AssemblyComponentRole.DIP_TUBE,
            ),
        )
    )
    ordered = tuple(sorted(references, key=lambda reference: reference.role.value))
    provisional = _provisional(
        project_id=next(iter(projects)),
        components=ordered,
        relationships=relationships,
        scale_state=scale_state,
        coordinate_unit=expected_unit,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    return ParametricAssemblyGraph(
        revision_id=_revision_id(provisional),
        project_id=provisional.project_id,
        components=provisional.components,
        relationships=provisional.relationships,
        scale_state=provisional.scale_state,
        coordinate_unit=provisional.coordinate_unit,
        physical_accuracy_validation_status=_DEFERRED,
        mold_use_authorized=False,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )


def validate_parametric_assembly_graph(
    graph: ParametricAssemblyGraph,
    current_components: tuple[AssemblyComponentInput, ...],
) -> None:
    """Require caller-supplied current models to match every immutable graph pin exactly."""
    if not isinstance(graph, ParametricAssemblyGraph):
        raise AssemblyGraphError("assembly_graph_required")
    if not isinstance(current_components, tuple) or any(
        not isinstance(item, AssemblyComponentInput) for item in current_components
    ):
        raise AssemblyGraphError("assembly_component_inputs_must_be_immutable_tuple")
    if len({item.role for item in current_components}) != len(current_components):
        raise AssemblyGraphError("assembly_component_role_duplicate")
    if {item.role.value for item in current_components} != _REQUIRED_ROLES:
        raise AssemblyGraphError("assembly_required_component_role_missing")
    pinned = {item.role: item for item in graph.components}
    for current in current_components:
        reference = pinned[current.role]
        if (
            not isinstance(current.model, DesignModelRevision)
            or current.expected_model_revision_id != current.model.revision_id
            or current.model.revision_id != reference.model_revision_id
            or current.feature_id != reference.feature_id
        ):
            raise AssemblyGraphError("assembly_component_revision_stale")
        try:
            feature = resolve_design_model_feature(current.model, current.feature_id)
        except DesignModelError as error:
            raise AssemblyGraphError("assembly_component_feature_stale") from error
        if (
            feature.component_id != reference.component_id
            or feature.feature_kind is not reference.feature_kind
            or current.model.parent_binding_revision_id != reference.parent_binding_revision_id
            or current.model.fitted_to_scan_master_revision_id != reference.scan_master_revision_id
            or current.model.scan_master_geometry_sha256 != reference.scan_master_geometry_sha256
            or current.model.scale_state is not reference.scale_state
            or current.model.scale_provenance_id != reference.scale_provenance_id
            or current.model.coordinate_unit != reference.coordinate_unit
        ):
            raise AssemblyGraphError("assembly_component_ancestry_mismatch")


def _provisional(**values: object) -> ParametricAssemblyGraph:
    provisional = object.__new__(ParametricAssemblyGraph)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    object.__setattr__(provisional, "revision_id", "pending")
    object.__setattr__(provisional, "physical_accuracy_validation_status", _DEFERRED)
    object.__setattr__(provisional, "mold_use_authorized", False)
    return provisional


def _revision_id(graph: ParametricAssemblyGraph) -> str:
    identity = {
        "contract": "packlab.parametric-assembly-graph.v1",
        "project_id": graph.project_id,
        "components": [item.as_dict() for item in graph.components],
        "relationships": [item.as_dict() for item in graph.relationships],
        "scale_state": graph.scale_state.value,
        "coordinate_unit": graph.coordinate_unit,
        "physical_accuracy_validation_status": graph.physical_accuracy_validation_status,
        "mold_use_authorized": graph.mold_use_authorized,
        "reason": graph.reason,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return "assembly-graph:" + digest


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise AssemblyGraphError(f"{field}_invalid")
    return value


def _timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise AssemblyGraphError("assembly_created_at_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise AssemblyGraphError("assembly_created_at_invalid") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise AssemblyGraphError("assembly_created_at_must_be_utc_z")
    return value


__all__ = [
    "AssemblyComponentInput",
    "AssemblyComponentReference",
    "AssemblyComponentRole",
    "AssemblyFeatureRelationship",
    "AssemblyGraphError",
    "AssemblyRelationshipKind",
    "ParametricAssemblyGraph",
    "create_parametric_assembly_graph",
    "validate_parametric_assembly_graph",
]
