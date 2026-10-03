"""Backend-neutral parametric loft and revolve operation descriptors."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum

from .cross_section import CrossSection
from .design_model import (
    DesignModelError,
    DesignModelRevision,
    resolve_design_model_feature,
)
from .design_profile import DesignProfile
from .reconstruction import ScaleState

_OPERATION_PREFIX = "design-operation:"
MAX_LOFT_SECTIONS = 512


class DesignOperationError(ValueError):
    """Raised when an operation has missing, stale or invalid parametric inputs."""


class OperationKind(StrEnum):
    REVOLVE = "revolve"
    LOFT = "loft"


@dataclass(frozen=True, slots=True)
class LoftSectionInput:
    feature_id: str
    section: CrossSection
    axial_position: float

    def __post_init__(self) -> None:
        if not isinstance(self.feature_id, str) or not self.feature_id:
            raise DesignOperationError("loft_feature_id_invalid")
        if not isinstance(self.section, CrossSection):
            raise DesignOperationError("loft_cross_section_required")
        if not math.isfinite(self.axial_position):
            raise DesignOperationError("loft_axial_position_must_be_finite")


@dataclass(frozen=True, slots=True)
class DesignOperation:
    """Immutable parameter graph operation; it carries no realized geometry."""

    operation_id: str
    kind: OperationKind
    model_revision_id: str
    parent_feature_ids: tuple[str, ...]
    input_ids: tuple[str, ...]
    axis_origin: tuple[float, float, float] | None
    axis_direction: tuple[float, float, float] | None
    angle_degrees: float | None
    section_positions: tuple[float, ...]
    coordinate_unit: str
    scale_state: ScaleState
    physical_accuracy_validation_status: str
    mold_use_authorized: bool

    def __post_init__(self) -> None:
        if not isinstance(self.kind, OperationKind):
            raise DesignOperationError("operation_kind_invalid")
        if not isinstance(self.parent_feature_ids, tuple) or not self.parent_feature_ids:
            raise DesignOperationError("operation_parent_features_required")
        if len(self.parent_feature_ids) != len(set(self.parent_feature_ids)):
            raise DesignOperationError("operation_parent_feature_duplicate")
        if not isinstance(self.input_ids, tuple) or not self.input_ids:
            raise DesignOperationError("operation_inputs_required")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise DesignOperationError("operation_scale_state_unauthorized")
        expected_unit = (
            "reconstruction_units" if self.scale_state is ScaleState.RELATIVE else "mm_unverified"
        )
        if self.coordinate_unit != expected_unit:
            raise DesignOperationError("operation_coordinate_unit_mismatch")
        if self.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION":
            raise DesignOperationError("operation_physical_validation_must_remain_deferred")
        if self.mold_use_authorized is not False:
            raise DesignOperationError("operation_mold_use_forbidden")
        if self.operation_id != _operation_id(self):
            raise DesignOperationError("operation_id_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.design-operation.v1",
            "authority_class": "DESIGN_MODEL_OPERATION",
            "operation_id": self.operation_id,
            "kind": self.kind.value,
            "model_revision_id": self.model_revision_id,
            "parent_feature_ids": list(self.parent_feature_ids),
            "input_ids": list(self.input_ids),
            "axis_origin": list(self.axis_origin) if self.axis_origin is not None else None,
            "axis_direction": (
                list(self.axis_direction) if self.axis_direction is not None else None
            ),
            "angle_degrees": self.angle_degrees,
            "section_positions": list(self.section_positions),
            "coordinate_unit": self.coordinate_unit,
            "scale_state": self.scale_state.value,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "output_geometry": None,
        }


def create_revolve_operation(
    model: DesignModelRevision,
    profile: DesignProfile,
    *,
    profile_feature_id: str,
    axis_feature_id: str,
    axis_origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
    axis_direction: tuple[float, float, float] = (0.0, 0.0, 1.0),
    angle_degrees: float = 360.0,
) -> DesignOperation:
    _validate_model(model)
    if not isinstance(profile, DesignProfile):
        raise DesignOperationError("revolve_profile_required")
    if (
        profile.coordinate_unit != model.coordinate_unit
        or profile.scale_state is not model.scale_state
    ):
        raise DesignOperationError("revolve_profile_unit_mismatch")
    for feature_id in (profile_feature_id, axis_feature_id):
        _resolve_feature(model, feature_id)
    origin = _vector3(axis_origin, "revolve_axis_origin")
    direction = _vector3(axis_direction, "revolve_axis_direction")
    magnitude = math.sqrt(sum(value * value for value in direction))
    if abs(magnitude - 1.0) > 1e-9:
        raise DesignOperationError("revolve_axis_direction_must_be_unit_length")
    if not math.isfinite(angle_degrees) or not 0 < angle_degrees <= 360:
        raise DesignOperationError("revolve_angle_out_of_range")
    return _operation(
        kind=OperationKind.REVOLVE,
        model=model,
        parent_feature_ids=(profile_feature_id, axis_feature_id),
        input_ids=(profile.profile_id,),
        axis_origin=origin,
        axis_direction=direction,
        angle_degrees=angle_degrees,
        section_positions=(),
    )


def create_loft_operation(
    model: DesignModelRevision,
    sections: tuple[LoftSectionInput, ...],
    *,
    path_feature_id: str | None = None,
) -> DesignOperation:
    _validate_model(model)
    if not isinstance(sections, tuple) or not 2 <= len(sections) <= MAX_LOFT_SECTIONS:
        raise DesignOperationError("loft_section_count_out_of_range")
    if any(not isinstance(item, LoftSectionInput) for item in sections):
        raise DesignOperationError("loft_section_input_invalid")
    point_count = len(sections[0].section.points)
    if any(len(item.section.points) != point_count for item in sections[1:]):
        raise DesignOperationError("loft_section_topology_mismatch")
    positions = tuple(item.axial_position for item in sections)
    if any(right <= left for left, right in zip(positions, positions[1:])):
        raise DesignOperationError("loft_sections_must_be_strictly_ordered")
    feature_ids = tuple(item.feature_id for item in sections)
    if len(feature_ids) != len(set(feature_ids)):
        raise DesignOperationError("loft_feature_id_duplicate")
    for feature_id in feature_ids:
        _resolve_feature(model, feature_id)
    if path_feature_id is not None:
        _resolve_feature(model, path_feature_id)
    for item in sections:
        if (
            item.section.coordinate_unit != model.coordinate_unit
            or item.section.scale_state is not model.scale_state
        ):
            raise DesignOperationError("loft_section_unit_mismatch")
    parents = feature_ids + ((path_feature_id,) if path_feature_id is not None else ())
    if len(parents) != len(set(parents)):
        raise DesignOperationError("operation_parent_feature_duplicate")
    return _operation(
        kind=OperationKind.LOFT,
        model=model,
        parent_feature_ids=parents,
        input_ids=tuple(item.section.section_id for item in sections),
        axis_origin=None,
        axis_direction=None,
        angle_degrees=None,
        section_positions=positions,
    )


def _validate_model(model: DesignModelRevision) -> None:
    if not isinstance(model, DesignModelRevision):
        raise DesignOperationError("design_model_revision_required")
    if (
        model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or model.mold_use_authorized is not False
    ):
        raise DesignOperationError("design_model_physical_authority_invalid")


def _resolve_feature(model: DesignModelRevision, feature_id: str) -> None:
    try:
        resolve_design_model_feature(model, feature_id)
    except DesignModelError as error:
        raise DesignOperationError("operation_feature_reference_stale_or_missing") from error


def _vector3(value: tuple[float, float, float], field: str) -> tuple[float, float, float]:
    if (
        not isinstance(value, tuple)
        or len(value) != 3
        or any(not isinstance(item, (int, float)) or isinstance(item, bool) for item in value)
        or any(not math.isfinite(item) for item in value)
    ):
        raise DesignOperationError(f"{field}_invalid")
    return (float(value[0]), float(value[1]), float(value[2]))


def _operation(
    *,
    kind: OperationKind,
    model: DesignModelRevision,
    parent_feature_ids: tuple[str, ...],
    input_ids: tuple[str, ...],
    axis_origin: tuple[float, float, float] | None,
    axis_direction: tuple[float, float, float] | None,
    angle_degrees: float | None,
    section_positions: tuple[float, ...],
) -> DesignOperation:
    provisional = object.__new__(DesignOperation)
    values = (
        ("kind", kind),
        ("model_revision_id", model.revision_id),
        ("parent_feature_ids", parent_feature_ids),
        ("input_ids", input_ids),
        ("axis_origin", axis_origin),
        ("axis_direction", axis_direction),
        ("angle_degrees", angle_degrees),
        ("section_positions", section_positions),
        ("coordinate_unit", model.coordinate_unit),
        ("scale_state", model.scale_state),
        ("physical_accuracy_validation_status", model.physical_accuracy_validation_status),
        ("mold_use_authorized", model.mold_use_authorized),
    )
    for field_name, value in values:
        object.__setattr__(provisional, field_name, value)
    operation_id = _operation_id(provisional)
    return DesignOperation(
        operation_id=operation_id,
        kind=kind,
        model_revision_id=model.revision_id,
        parent_feature_ids=parent_feature_ids,
        input_ids=input_ids,
        axis_origin=axis_origin,
        axis_direction=axis_direction,
        angle_degrees=angle_degrees,
        section_positions=section_positions,
        coordinate_unit=model.coordinate_unit,
        scale_state=model.scale_state,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
    )


def _operation_id(operation: DesignOperation) -> str:
    payload = {
        "contract": "packlab.design-operation.v1",
        "kind": operation.kind.value,
        "model_revision_id": operation.model_revision_id,
        "parent_feature_ids": list(operation.parent_feature_ids),
        "input_ids": list(operation.input_ids),
        "axis_origin": operation.axis_origin,
        "axis_direction": operation.axis_direction,
        "angle_degrees": operation.angle_degrees,
        "section_positions": list(operation.section_positions),
        "coordinate_unit": operation.coordinate_unit,
        "scale_state": operation.scale_state.value,
        "physical_accuracy_validation_status": operation.physical_accuracy_validation_status,
        "mold_use_authorized": operation.mold_use_authorized,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return _OPERATION_PREFIX + digest


__all__ = [
    "DesignOperation",
    "DesignOperationError",
    "LoftSectionInput",
    "OperationKind",
    "create_loft_operation",
    "create_revolve_operation",
]
