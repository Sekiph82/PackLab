"""Immutable overall dimension parameters with explicit proportional relationships."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from .design_history import DesignEditCommand, EditTargetKind, create_edit_command
from .design_model import (
    DesignModelError,
    DesignModelParameter,
    DesignModelRevision,
    ParameterType,
    revise_design_model_revision,
)

DIMENSIONS_PARAMETER_ID = "overall_dimensions"
_CONTRACT = "packlab.overall-dimensions.v1"
_DIMENSION_KEYS = ("height", "width", "depth")


class DesignDimensionsError(ValueError):
    """Raised when dimension inputs or their declared relationships are invalid."""


class DimensionAxis(StrEnum):
    HEIGHT = "height"
    WIDTH = "width"
    DEPTH = "depth"


@dataclass(frozen=True, slots=True)
class DimensionEditRevision:
    model: DesignModelRevision
    parameter: DesignModelParameter
    changed_axes: tuple[DimensionAxis, ...]
    history_command: DesignEditCommand

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.dimension-edit-revision.v1",
            "model_revision_id": self.model.revision_id,
            "previous_model_revision_id": self.model.previous_revision_id,
            "parameter": self.parameter.as_dict(),
            "changed_axes": [axis.value for axis in self.changed_axes],
            "history_command_id": self.history_command.command_id,
            "authority_class": "DESIGN_MODEL_PARAMETRIC_REVISION",
            "physical_accuracy_validation_status": self.model.physical_accuracy_validation_status,
            "mold_use_authorized": self.model.mold_use_authorized,
            "scan_master_changed": False,
        }


def create_overall_dimensions_revision(
    model: DesignModelRevision,
    *,
    height: float,
    width: float,
    depth: float,
    proportional_groups: tuple[tuple[DimensionAxis, ...], ...] = (),
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelRevision:
    """Attach fully specified dimensions and explicit disjoint proportional groups."""
    if not isinstance(model, DesignModelRevision):
        raise DesignDimensionsError("design_model_revision_required")
    if any(item.parameter_id == DIMENSIONS_PARAMETER_ID for item in model.parameters):
        raise DesignDimensionsError("overall_dimensions_already_exist")
    values = {"height": height, "width": width, "depth": depth}
    _validate_dimensions(values)
    groups = _normalize_groups(proportional_groups)
    parameter = _make_parameter(model, values, groups)
    try:
        return revise_design_model_revision(
            model,
            parameters=(*model.parameters, parameter),
            features=model.features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise DesignDimensionsError("overall_dimensions_revision_invalid") from error


def revise_overall_dimension(
    model: DesignModelRevision,
    *,
    expected_model_revision_id: str,
    axis: DimensionAxis,
    value: float,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DimensionEditRevision:
    """Change one dimension and propagate only its explicitly grouped peers."""
    if not isinstance(model, DesignModelRevision):
        raise DesignDimensionsError("design_model_revision_required")
    if model.revision_id != expected_model_revision_id:
        raise DesignDimensionsError("design_model_revision_stale")
    if not isinstance(axis, DimensionAxis):
        raise DesignDimensionsError("dimension_axis_invalid")
    if not _positive_finite(value):
        raise DesignDimensionsError("dimension_value_must_be_positive_finite")
    matches = tuple(
        parameter
        for parameter in model.parameters
        if parameter.parameter_id == DIMENSIONS_PARAMETER_ID
    )
    if len(matches) != 1:
        raise DesignDimensionsError("overall_dimensions_missing_or_ambiguous")
    before = matches[0]
    current_values, groups = _read_parameter(model, before)
    key = axis.value
    current = current_values[key]
    changed_axes = next((group for group in groups if axis in group), (axis,))
    if value == current:
        raise DesignDimensionsError("dimension_edit_noop")
    scale = value / current
    updated = dict(current_values)
    for changed_axis in changed_axes:
        result = value if changed_axis is axis else current_values[changed_axis.value] * scale
        if not _positive_finite(result):
            raise DesignDimensionsError("dimension_relationship_result_invalid")
        updated[changed_axis.value] = result
    after = _make_parameter(model, updated, groups)
    command = create_edit_command(
        model.revision_id,
        EditTargetKind.PARAMETER,
        DIMENSIONS_PARAMETER_ID,
        before,
        after,
    )
    parameters = tuple(
        parameter
        for parameter in model.parameters
        if parameter.parameter_id != DIMENSIONS_PARAMETER_ID
    )
    try:
        revised = revise_design_model_revision(
            model,
            parameters=(*parameters, after),
            features=model.features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise DesignDimensionsError("dimension_edit_revision_invalid") from error
    return DimensionEditRevision(revised, after, changed_axes, command)


def _make_parameter(
    model: DesignModelRevision,
    values: dict[str, float],
    groups: tuple[tuple[DimensionAxis, ...], ...],
) -> DesignModelParameter:
    _validate_dimensions(values)
    value = {
        "contract": _CONTRACT,
        "dimensions": {key: values[key] for key in _DIMENSION_KEYS},
        "proportional_groups": [[axis.value for axis in group] for group in groups],
        "coordinate_unit": model.coordinate_unit,
        "physical_accuracy_validation_status": model.physical_accuracy_validation_status,
        "mold_use_authorized": False,
    }
    return DesignModelParameter(
        DIMENSIONS_PARAMETER_ID,
        value,
        ParameterType.OBJECT,
        model.coordinate_unit,
    )


def _read_parameter(
    model: DesignModelRevision, parameter: DesignModelParameter
) -> tuple[dict[str, float], tuple[tuple[DimensionAxis, ...], ...]]:
    value = parameter.as_dict()["value"]
    if (
        parameter.value_type is not ParameterType.OBJECT
        or parameter.unit != model.coordinate_unit
        or not isinstance(value, dict)
        or value.get("contract") != _CONTRACT
        or value.get("coordinate_unit") != model.coordinate_unit
        or value.get("physical_accuracy_validation_status")
        != model.physical_accuracy_validation_status
        or value.get("mold_use_authorized") is not False
    ):
        raise DesignDimensionsError("overall_dimensions_parameter_invalid")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, dict) or set(dimensions) != set(_DIMENSION_KEYS):
        raise DesignDimensionsError("overall_dimensions_incomplete_or_ambiguous")
    _validate_dimensions(dimensions)
    raw_groups = value.get("proportional_groups")
    if not isinstance(raw_groups, list):
        raise DesignDimensionsError("dimension_relationships_invalid")
    groups: list[tuple[DimensionAxis, ...]] = []
    for raw_group in raw_groups:
        if not isinstance(raw_group, list):
            raise DesignDimensionsError("dimension_relationship_group_invalid")
        try:
            groups.append(tuple(DimensionAxis(item) for item in raw_group))
        except (ValueError, TypeError) as error:
            raise DesignDimensionsError("dimension_relationship_axis_invalid") from error
    normalized_groups = _normalize_groups(tuple(groups))
    values_as_float = {key: float(dimensions[key]) for key in _DIMENSION_KEYS}
    return values_as_float, normalized_groups


def _normalize_groups(
    groups: tuple[tuple[DimensionAxis, ...], ...],
) -> tuple[tuple[DimensionAxis, ...], ...]:
    if not isinstance(groups, tuple):
        raise DesignDimensionsError("dimension_relationships_must_be_tuple")
    normalized: list[tuple[DimensionAxis, ...]] = []
    used: set[DimensionAxis] = set()
    for group in groups:
        if (
            not isinstance(group, tuple)
            or len(group) < 2
            or any(not isinstance(axis, DimensionAxis) for axis in group)
            or len(set(group)) != len(group)
            or used.intersection(group)
        ):
            raise DesignDimensionsError("dimension_relationship_group_invalid")
        ordered = tuple(axis for axis in DimensionAxis if axis in group)
        normalized.append(ordered)
        used.update(ordered)
    return tuple(sorted(normalized, key=lambda group: tuple(axis.value for axis in group)))


def _validate_dimensions(values: object) -> None:
    if not isinstance(values, dict) or set(values) != set(_DIMENSION_KEYS):
        raise DesignDimensionsError("overall_dimensions_incomplete_or_ambiguous")
    if any(not _positive_finite(values[key]) for key in _DIMENSION_KEYS):
        raise DesignDimensionsError("dimension_values_must_be_positive_finite")


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0.0
    )


__all__ = [
    "DIMENSIONS_PARAMETER_ID",
    "DimensionAxis",
    "DimensionEditRevision",
    "DesignDimensionsError",
    "create_overall_dimensions_revision",
    "revise_overall_dimension",
]
