"""Immutable, backend-neutral parametric Design Model revisions."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, cast

from .design_model_binding import DesignModelParentBindingRevision
from .reconstruction import ScaleState

_REVISION_PREFIX = "design-model:"
_FEATURE_PREFIX = "packlab-feature:"
_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
type _JSONScalar = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class _FrozenObject:
    items: tuple[tuple[str, Any], ...]


type _JSONValue = _JSONScalar | tuple[_JSONValue, ...] | _FrozenObject


class DesignModelError(ValueError):
    """Raised when a Design Model graph is invalid or lacks required authority."""


class PackageFamily(StrEnum):
    BOTTLE = "bottle"
    JAR = "jar"
    CYLINDRICAL_CONTAINER = "cylindrical-container"
    JERRYCAN = "jerrycan"
    OTHER = "other"


class ParameterType(StrEnum):
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    ARRAY = "array"
    OBJECT = "object"


class FeatureKind(StrEnum):
    BODY = "body"
    BASE = "base"
    SHOULDER = "shoulder"
    NECK = "neck"
    FINISH = "finish"
    CAP = "cap"


def stable_feature_id(component_id: str, feature_kind: FeatureKind, semantic_key: str) -> str:
    """Return a stable semantic ID; parameter values and mesh indices are not inputs."""
    _identifier(component_id, "component_id")
    if not isinstance(feature_kind, FeatureKind):
        raise DesignModelError("feature_kind_invalid")
    _identifier(semantic_key, "feature_semantic_key")
    payload = {
        "contract": "packlab.design-model-feature.v1",
        "component_id": component_id,
        "feature_kind": feature_kind.value,
        "semantic_key": semantic_key,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return _FEATURE_PREFIX + digest


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise DesignModelError(f"{field}_invalid")
    return value


def _timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DesignModelError("created_at_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise DesignModelError("created_at_invalid") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise DesignModelError("created_at_must_be_utc_z")
    return value


def _freeze_json(value: object, field: str, depth: int = 0) -> _JSONValue:
    if depth > 16:
        raise DesignModelError(f"{field}_nesting_too_deep")
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DesignModelError(f"{field}_number_must_be_finite")
        return value
    if isinstance(value, (list, tuple)):
        if len(value) > 4096:
            raise DesignModelError(f"{field}_array_too_large")
        return tuple(_freeze_json(item, field, depth + 1) for item in value)
    if isinstance(value, Mapping):
        if len(value) > 4096 or any(not isinstance(key, str) for key in value):
            raise DesignModelError(f"{field}_object_invalid")
        return _FrozenObject(
            tuple((key, _freeze_json(value[key], field, depth + 1)) for key in sorted(value))
        )
    raise DesignModelError(f"{field}_value_not_json_serializable")


def _thaw_json(value: _JSONValue) -> object:
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    if isinstance(value, _FrozenObject):
        return {key: _thaw_json(item) for key, item in value.items}
    return value


def _inferred_type(value: _JSONValue) -> ParameterType:
    if isinstance(value, bool):
        return ParameterType.BOOLEAN
    if isinstance(value, int):
        return ParameterType.INTEGER
    if isinstance(value, float):
        return ParameterType.NUMBER
    if isinstance(value, str):
        return ParameterType.STRING
    if value is None:
        raise DesignModelError("parameter_null_type_unsupported")
    if isinstance(value, _FrozenObject):
        return ParameterType.OBJECT
    return ParameterType.ARRAY


def _validate_type(value: _JSONValue, value_type: ParameterType) -> None:
    inferred = _inferred_type(value)
    if value_type is ParameterType.NUMBER and inferred in {
        ParameterType.NUMBER,
        ParameterType.INTEGER,
    }:
        return
    if inferred is not value_type:
        raise DesignModelError("parameter_value_type_mismatch")


@dataclass(frozen=True, slots=True)
class DesignModelParameter:
    """A typed, JSON-compatible parameter node; it contains no mesh/backend object."""

    parameter_id: str
    value: object
    value_type: ParameterType
    unit: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.parameter_id, "parameter_id")
        if not isinstance(self.value_type, ParameterType):
            raise DesignModelError("parameter_type_invalid")
        frozen = _freeze_json(self.value, "parameter")
        _validate_type(frozen, self.value_type)
        object.__setattr__(self, "value", frozen)
        if self.unit is not None:
            if not isinstance(self.unit, str) or not self.unit or len(self.unit) > 64:
                raise DesignModelError("parameter_unit_invalid")
            if self.unit not in {"reconstruction_units", "mm_unverified"}:
                raise DesignModelError("parameter_unit_unauthorized")

    def as_dict(self) -> dict[str, object]:
        return {
            "parameter_id": self.parameter_id,
            "value": _thaw_json(cast(_JSONValue, self.value)),
            "value_type": self.value_type.value,
            "unit": self.unit,
        }


@dataclass(frozen=True, slots=True)
class DesignModelFeatureReference:
    """Stable semantic feature/component reference independent of tessellation indices."""

    feature_id: str
    component_id: str
    feature_kind: FeatureKind
    semantic_key: str

    def __post_init__(self) -> None:
        _identifier(self.feature_id, "feature_id")
        _identifier(self.component_id, "component_id")
        _identifier(self.semantic_key, "feature_semantic_key")
        if not isinstance(self.feature_kind, FeatureKind):
            raise DesignModelError("feature_kind_invalid")
        if self.feature_id != stable_feature_id(
            self.component_id, self.feature_kind, self.semantic_key
        ):
            raise DesignModelError("feature_id_semantic_mismatch")

    def as_dict(self) -> dict[str, str]:
        return {
            "feature_id": self.feature_id,
            "component_id": self.component_id,
            "feature_kind": self.feature_kind.value,
            "semantic_key": self.semantic_key,
        }


def resolve_design_model_feature(
    revision: DesignModelRevision, feature_id: str
) -> DesignModelFeatureReference:
    """Resolve only the exact ID; deleted/replaced IDs never retarget implicitly."""
    if not isinstance(revision, DesignModelRevision):
        raise DesignModelError("design_model_revision_required")
    _identifier(feature_id, "feature_id")
    matches = tuple(feature for feature in revision.features if feature.feature_id == feature_id)
    if not matches:
        raise DesignModelError("feature_reference_stale_or_deleted")
    if len(matches) != 1:
        raise DesignModelError("feature_reference_ambiguous")
    return matches[0]


@dataclass(frozen=True, slots=True)
class DesignModelRevision:
    """One immutable parameter-graph revision with an exact captured parent pin."""

    revision_id: str
    project_id: str
    package_family: PackageFamily
    parameters: tuple[DesignModelParameter, ...]
    features: tuple[DesignModelFeatureReference, ...]
    parent_binding_revision_id: str
    fitted_to_scan_master_revision_id: str
    scan_master_geometry_sha256: str
    scale_state: ScaleState
    scale_provenance_id: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    previous_revision_id: str | None
    actor_id: str
    reason: str
    created_at_utc: str

    def __post_init__(self) -> None:
        _identifier(self.project_id, "project_id")
        if not isinstance(self.package_family, PackageFamily):
            raise DesignModelError("package_family_invalid")
        if not isinstance(self.parameters, tuple) or any(
            not isinstance(item, DesignModelParameter) for item in self.parameters
        ):
            raise DesignModelError("parameters_must_be_immutable_tuple")
        parameter_ids = [item.parameter_id for item in self.parameters]
        if len(parameter_ids) != len(set(parameter_ids)):
            raise DesignModelError("parameter_id_duplicate")
        if not isinstance(self.features, tuple) or any(
            not isinstance(item, DesignModelFeatureReference) for item in self.features
        ):
            raise DesignModelError("features_must_be_immutable_tuple")
        feature_ids = [item.feature_id for item in self.features]
        if len(feature_ids) != len(set(feature_ids)):
            raise DesignModelError("feature_id_duplicate")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise DesignModelError("design_model_scale_state_unauthorized")
        expected_unit = (
            "reconstruction_units" if self.scale_state is ScaleState.RELATIVE else "mm_unverified"
        )
        if self.coordinate_unit != expected_unit:
            raise DesignModelError("design_model_coordinate_unit_mismatch")
        if self.physical_accuracy_validation_status != _DEFERRED:
            raise DesignModelError("design_model_physical_validation_must_remain_deferred")
        if self.mold_use_authorized is not False:
            raise DesignModelError("design_model_mold_use_forbidden")
        _identifier(self.parent_binding_revision_id, "parent_binding_revision_id")
        _identifier(self.fitted_to_scan_master_revision_id, "scan_master_revision_id")
        if not re.fullmatch(r"[0-9a-f]{64}", self.scan_master_geometry_sha256):
            raise DesignModelError("scan_master_geometry_digest_invalid")
        _identifier(self.scale_provenance_id, "scale_provenance_id")
        _identifier(self.actor_id, "actor_id")
        if self.previous_revision_id is not None:
            _identifier(self.previous_revision_id, "previous_revision_id")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 1000:
            raise DesignModelError("revision_reason_invalid")
        _timestamp(self.created_at_utc)
        expected_id = _revision_id(self)
        if self.revision_id != expected_id:
            raise DesignModelError("design_model_revision_id_mismatch")

    def as_dict(self) -> dict[str, object]:
        """Return deterministic, human-readable serialization-ready data."""
        return {
            "contract": "packlab.design-model.v1",
            "revision_id": self.revision_id,
            "project_id": self.project_id,
            "package_family": self.package_family.value,
            "parameters": [item.as_dict() for item in self.parameters],
            "features": [item.as_dict() for item in self.features],
            "parent": {
                "binding_revision_id": self.parent_binding_revision_id,
                "scan_master_revision_id": self.fitted_to_scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            },
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "previous_revision_id": self.previous_revision_id,
            "actor_id": self.actor_id,
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
        }


def create_design_model_revision(
    parent_binding: DesignModelParentBindingRevision,
    *,
    package_family: PackageFamily,
    parameters: tuple[DesignModelParameter, ...] = (),
    features: tuple[DesignModelFeatureReference, ...] = (),
    actor_id: str,
    reason: str,
    created_at_utc: str,
    previous_revision_id: str | None = None,
) -> DesignModelRevision:
    """Create an identity from canonical graph data and exact parent provenance."""
    if not isinstance(parent_binding, DesignModelParentBindingRevision):
        raise DesignModelError("design_model_parent_binding_required")
    if not isinstance(parameters, tuple) or not isinstance(features, tuple):
        raise DesignModelError("graph_nodes_must_be_tuples")
    if any(not isinstance(item, DesignModelParameter) for item in parameters):
        raise DesignModelError("parameter_node_invalid")
    if any(not isinstance(item, DesignModelFeatureReference) for item in features):
        raise DesignModelError("feature_reference_invalid")
    ordered_parameters = tuple(sorted(parameters, key=lambda item: item.parameter_id))
    ordered_features = tuple(sorted(features, key=lambda item: item.feature_id))
    scale_state = parent_binding.scale_state
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    provisional = object.__new__(DesignModelRevision)
    provisional_values = (
        ("project_id", parent_binding.project_id),
        ("package_family", package_family),
        ("parameters", ordered_parameters),
        ("features", ordered_features),
        ("parent_binding_revision_id", parent_binding.revision_id),
        ("fitted_to_scan_master_revision_id", parent_binding.fitted_to_scan_master_revision_id),
        ("scan_master_geometry_sha256", parent_binding.scan_master_geometry_sha256),
        ("scale_state", scale_state),
        ("scale_provenance_id", parent_binding.scale_provenance_id),
        ("coordinate_unit", unit),
        ("physical_accuracy_validation_status", _DEFERRED),
        ("mold_use_authorized", False),
        ("previous_revision_id", previous_revision_id),
        ("actor_id", actor_id),
        ("reason", reason),
        ("created_at_utc", created_at_utc),
    )
    for field_name, value in provisional_values:
        object.__setattr__(provisional, field_name, value)
    revision_id = _revision_id(provisional)
    return DesignModelRevision(
        revision_id=revision_id,
        project_id=parent_binding.project_id,
        package_family=package_family,
        parameters=ordered_parameters,
        features=ordered_features,
        parent_binding_revision_id=parent_binding.revision_id,
        fitted_to_scan_master_revision_id=parent_binding.fitted_to_scan_master_revision_id,
        scan_master_geometry_sha256=parent_binding.scan_master_geometry_sha256,
        scale_state=scale_state,
        scale_provenance_id=parent_binding.scale_provenance_id,
        coordinate_unit=unit,
        physical_accuracy_validation_status=_DEFERRED,
        mold_use_authorized=False,
        previous_revision_id=previous_revision_id,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )


def revise_design_model_revision(
    current: DesignModelRevision,
    *,
    parameters: tuple[DesignModelParameter, ...],
    features: tuple[DesignModelFeatureReference, ...],
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelRevision:
    """Create an immutable edit revision while retaining the exact captured parent pin."""
    if not isinstance(current, DesignModelRevision):
        raise DesignModelError("current_design_model_revision_required")
    if not isinstance(parameters, tuple) or not isinstance(features, tuple):
        raise DesignModelError("graph_nodes_must_be_tuples")
    if any(not isinstance(item, DesignModelParameter) for item in parameters):
        raise DesignModelError("parameter_node_invalid")
    if any(not isinstance(item, DesignModelFeatureReference) for item in features):
        raise DesignModelError("feature_reference_invalid")
    ordered_parameters = tuple(sorted(parameters, key=lambda item: item.parameter_id))
    ordered_features = tuple(sorted(features, key=lambda item: item.feature_id))
    provisional = object.__new__(DesignModelRevision)
    values = (
        ("project_id", current.project_id),
        ("package_family", current.package_family),
        ("parameters", ordered_parameters),
        ("features", ordered_features),
        ("parent_binding_revision_id", current.parent_binding_revision_id),
        (
            "fitted_to_scan_master_revision_id",
            current.fitted_to_scan_master_revision_id,
        ),
        ("scan_master_geometry_sha256", current.scan_master_geometry_sha256),
        ("scale_state", current.scale_state),
        ("scale_provenance_id", current.scale_provenance_id),
        ("coordinate_unit", current.coordinate_unit),
        ("physical_accuracy_validation_status", _DEFERRED),
        ("mold_use_authorized", False),
        ("previous_revision_id", current.revision_id),
        ("actor_id", actor_id),
        ("reason", reason),
        ("created_at_utc", created_at_utc),
    )
    for field_name, value in values:
        object.__setattr__(provisional, field_name, value)
    return DesignModelRevision(
        revision_id=_revision_id(provisional),
        project_id=current.project_id,
        package_family=current.package_family,
        parameters=ordered_parameters,
        features=ordered_features,
        parent_binding_revision_id=current.parent_binding_revision_id,
        fitted_to_scan_master_revision_id=current.fitted_to_scan_master_revision_id,
        scan_master_geometry_sha256=current.scan_master_geometry_sha256,
        scale_state=current.scale_state,
        scale_provenance_id=current.scale_provenance_id,
        coordinate_unit=current.coordinate_unit,
        physical_accuracy_validation_status=_DEFERRED,
        mold_use_authorized=False,
        previous_revision_id=current.revision_id,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )


def _revision_id(revision: DesignModelRevision) -> str:
    payload = {
        "contract": "packlab.design-model.v1",
        "project_id": revision.project_id,
        "package_family": revision.package_family.value,
        "parameters": [item.as_dict() for item in revision.parameters],
        "features": [item.as_dict() for item in revision.features],
        "parent_binding_revision_id": revision.parent_binding_revision_id,
        "fitted_to_scan_master_revision_id": revision.fitted_to_scan_master_revision_id,
        "scan_master_geometry_sha256": revision.scan_master_geometry_sha256,
        "scale_state": revision.scale_state.value,
        "scale_provenance_id": revision.scale_provenance_id,
        "coordinate_unit": revision.coordinate_unit,
        "physical_accuracy_validation_status": revision.physical_accuracy_validation_status,
        "mold_use_authorized": revision.mold_use_authorized,
        "previous_revision_id": revision.previous_revision_id,
        "reason": revision.reason,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return _REVISION_PREFIX + digest


__all__ = [
    "DesignModelError",
    "DesignModelFeatureReference",
    "DesignModelParameter",
    "DesignModelRevision",
    "FeatureKind",
    "PackageFamily",
    "ParameterType",
    "create_design_model_revision",
    "revise_design_model_revision",
    "resolve_design_model_feature",
    "stable_feature_id",
]
