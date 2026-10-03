"""Exact invariant checks for authored freeform cage edits."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from enum import StrEnum

from .design_dimensions import DIMENSIONS_PARAMETER_ID, DimensionAxis
from .design_freeform import (
    FreeformCageError,
    FreeformCageOperation,
    deform_design_preview,
    edit_freeform_cage,
    resolve_freeform_cage,
)
from .design_model import DesignModelParameter, DesignModelRevision
from .design_preview import DesignPreview

CONSTRAINT_TOLERANCE = 1e-9
_MATING_PARAMETER_PREFIX = "mating_reference_"


class FreeformAxis(StrEnum):
    X = "x"
    Y = "y"
    Z = "z"

    @property
    def coordinate_index(self) -> int:
        return {FreeformAxis.X: 0, FreeformAxis.Y: 1, FreeformAxis.Z: 2}[self]


class FreeformConstraintError(ValueError):
    """Raised when a cage edit violates a selected protected invariant."""


@dataclass(frozen=True, slots=True)
class FreeformConstraintDiagnostics:
    cage_feature_id: str
    operation_id: str
    protected_dimensions: tuple[DimensionAxis, ...]
    dimension_residuals: tuple[tuple[DimensionAxis, float], ...]
    symmetry_axes: tuple[FreeformAxis, ...]
    symmetry_residuals: tuple[tuple[FreeformAxis, float], ...]
    mating_reference_parameter_ids: tuple[str, ...]
    mating_references_preserved: bool
    total_control_scalar_dof: int
    symmetry_constrained_dof: int
    unconstrained_control_scalar_dof: int
    tolerance: float = CONSTRAINT_TOLERANCE

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.freeform-constraint-diagnostics.v1",
            "authority_class": "DESIGN_MODEL_EDIT_DIAGNOSTIC",
            "cage_feature_id": self.cage_feature_id,
            "operation_id": self.operation_id,
            "protected_dimensions": [axis.value for axis in self.protected_dimensions],
            "dimension_residuals": {
                axis.value: residual for axis, residual in self.dimension_residuals
            },
            "symmetry_axes": [axis.value for axis in self.symmetry_axes],
            "symmetry_residuals": {
                axis.value: residual for axis, residual in self.symmetry_residuals
            },
            "mating_reference_parameter_ids": list(self.mating_reference_parameter_ids),
            "mating_references_preserved": self.mating_references_preserved,
            "total_control_scalar_dof": self.total_control_scalar_dof,
            "symmetry_constrained_dof": self.symmetry_constrained_dof,
            "unconstrained_control_scalar_dof": self.unconstrained_control_scalar_dof,
            "constraint_tolerance": self.tolerance,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


def constrain_freeform_cage_preview(
    source_preview: DesignPreview,
    source_model: DesignModelRevision,
    edited_model: DesignModelRevision,
    cage_feature_id: str,
    *,
    protected_dimensions: tuple[DimensionAxis, ...] = (
        DimensionAxis.HEIGHT,
        DimensionAxis.WIDTH,
        DimensionAxis.DEPTH,
    ),
    symmetry_axes: tuple[FreeformAxis, ...] = (),
) -> tuple[DesignPreview, FreeformConstraintDiagnostics]:
    """Apply a cage and fail closed when selected dimension/mating/symmetry rules move."""

    if not isinstance(source_model, DesignModelRevision) or not isinstance(
        edited_model, DesignModelRevision
    ):
        raise FreeformConstraintError("design_model_revision_required")
    if (
        not isinstance(protected_dimensions, tuple)
        or any(not isinstance(axis, DimensionAxis) for axis in protected_dimensions)
        or len(set(protected_dimensions)) != len(protected_dimensions)
    ):
        raise FreeformConstraintError("protected_dimensions_invalid")
    if (
        not isinstance(symmetry_axes, tuple)
        or any(not isinstance(axis, FreeformAxis) for axis in symmetry_axes)
        or len(set(symmetry_axes)) != len(symmetry_axes)
    ):
        raise FreeformConstraintError("freeform_symmetry_axes_invalid")
    try:
        cage = resolve_freeform_cage(edited_model, cage_feature_id)
        preview = deform_design_preview(source_preview, edited_model, cage_feature_id)
    except FreeformCageError as error:
        raise FreeformConstraintError(f"freeform_cage_rejected:{error}") from error
    if (
        not isinstance(source_preview, DesignPreview)
        or source_model.revision_id != cage.source_model_revision_id
        or source_preview.model_revision_id != source_model.revision_id
        or source_model.parent_binding_revision_id != edited_model.parent_binding_revision_id
        or source_model.fitted_to_scan_master_revision_id
        != edited_model.fitted_to_scan_master_revision_id
        or source_model.scan_master_geometry_sha256 != edited_model.scan_master_geometry_sha256
        or source_model.coordinate_unit != edited_model.coordinate_unit
    ):
        raise FreeformConstraintError("freeform_constraint_parent_binding_invalid")

    before_references = _mating_references(source_model)
    after_references = _mating_references(edited_model)
    if before_references != after_references:
        raise FreeformConstraintError("freeform_mating_reference_violation")

    dimensions = _dimension_values(source_model)
    output_extents = _extents(preview)
    input_extents = _extents(source_preview)
    dimension_residuals: list[tuple[DimensionAxis, float]] = []
    for dimension in protected_dimensions:
        axis_index = _dimension_axis_index(dimension)
        expected = dimensions[dimension]
        source_residual = abs(input_extents[axis_index] - expected)
        if source_residual > CONSTRAINT_TOLERANCE:
            raise FreeformConstraintError("freeform_constraint_source_dimension_mismatch")
        residual = abs(output_extents[axis_index] - expected)
        if residual > CONSTRAINT_TOLERANCE:
            raise FreeformConstraintError(f"protected_dimension_violation:{dimension.value}")
        dimension_residuals.append((dimension, residual))

    symmetry_residuals = tuple((axis, _symmetry_residual(cage, axis)) for axis in symmetry_axes)
    violating = tuple(
        axis.value for axis, residual in symmetry_residuals if residual > CONSTRAINT_TOLERANCE
    )
    if violating:
        raise FreeformConstraintError("freeform_symmetry_violation:" + ",".join(violating))
    total_dof = len(cage.control_points) * 4
    constrained_dof = _symmetry_constrained_dof(cage, symmetry_axes)
    diagnostics = FreeformConstraintDiagnostics(
        cage_feature_id,
        cage.operation_id,
        protected_dimensions,
        tuple(dimension_residuals),
        symmetry_axes,
        symmetry_residuals,
        tuple(sorted(before_references)),
        True,
        total_dof,
        constrained_dof,
        total_dof - constrained_dof,
    )
    return preview, diagnostics


def edit_freeform_cage_constrained(
    source_preview: DesignPreview,
    source_model: DesignModelRevision,
    cage_model: DesignModelRevision,
    cage_feature_id: str,
    *,
    control_points: tuple[tuple[float, float, float], ...],
    control_weights: tuple[float, ...],
    actor_id: str,
    reason: str,
    created_at_utc: str,
    protected_dimensions: tuple[DimensionAxis, ...] = (
        DimensionAxis.HEIGHT,
        DimensionAxis.WIDTH,
        DimensionAxis.DEPTH,
    ),
    symmetry_axes: tuple[FreeformAxis, ...] = (),
) -> tuple[
    DesignModelRevision, FreeformCageOperation, DesignPreview, FreeformConstraintDiagnostics
]:
    """Return an edited cage only after all selected invariant checks pass."""

    try:
        candidate_model, candidate_cage = edit_freeform_cage(
            cage_model,
            cage_feature_id,
            control_points=control_points,
            control_weights=control_weights,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except FreeformCageError as error:
        raise FreeformConstraintError(f"freeform_cage_edit_rejected:{error}") from error
    preview, diagnostics = constrain_freeform_cage_preview(
        source_preview,
        source_model,
        candidate_model,
        cage_feature_id,
        protected_dimensions=protected_dimensions,
        symmetry_axes=symmetry_axes,
    )
    return candidate_model, candidate_cage, preview, diagnostics


def _dimension_values(model: DesignModelRevision) -> dict[DimensionAxis, float]:
    matches = tuple(
        item for item in model.parameters if item.parameter_id == DIMENSIONS_PARAMETER_ID
    )
    if len(matches) != 1 or matches[0].unit != model.coordinate_unit:
        raise FreeformConstraintError("protected_dimensions_missing_or_ambiguous")
    value = matches[0].as_dict()["value"]
    if not isinstance(value, dict) or value.get("coordinate_unit") != model.coordinate_unit:
        raise FreeformConstraintError("protected_dimensions_invalid")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, dict):
        raise FreeformConstraintError("protected_dimensions_invalid")
    result: dict[DimensionAxis, float] = {}
    for axis in DimensionAxis:
        number = dimensions.get(axis.value)
        if (
            isinstance(number, bool)
            or not isinstance(number, (int, float))
            or not math.isfinite(number)
        ):
            raise FreeformConstraintError("protected_dimensions_invalid")
        result[axis] = float(number)
    return result


def _mating_references(model: DesignModelRevision) -> dict[str, DesignModelParameter]:
    matches = tuple(
        item for item in model.parameters if item.parameter_id.startswith(_MATING_PARAMETER_PREFIX)
    )
    if len({item.parameter_id for item in matches}) != len(matches):
        raise FreeformConstraintError("freeform_mating_reference_ambiguous")
    return {item.parameter_id: item for item in matches}


def _extents(preview: DesignPreview) -> tuple[float, float, float]:
    vertices = preview.mesh.vertices
    if not vertices:
        raise FreeformConstraintError("freeform_constraint_preview_empty")
    return tuple(
        max(point[axis] for point in vertices) - min(point[axis] for point in vertices)
        for axis in range(3)
    )  # type: ignore[return-value]


def _dimension_axis_index(axis: DimensionAxis) -> int:
    # PackLab preview coordinates use X=width, Y=depth and Z=height.
    return {
        DimensionAxis.WIDTH: 0,
        DimensionAxis.DEPTH: 1,
        DimensionAxis.HEIGHT: 2,
    }[axis]


def _symmetry_residual(cage: FreeformCageOperation, axis: FreeformAxis) -> float:
    dimension = axis.coordinate_index
    maximum = 0.0
    for index, point in enumerate(cage.control_points):
        lattice_index = _unflat_index(index, cage.lattice_shape)
        mirrored_index = list(lattice_index)
        mirrored_index[dimension] = cage.lattice_shape[dimension] - 1 - lattice_index[dimension]
        other_index = _flat_index(
            (mirrored_index[0], mirrored_index[1], mirrored_index[2]), cage.lattice_shape
        )
        if index > other_index:
            continue
        partner = cage.control_points[other_index]
        expected = list(partner)
        plane = (cage.region_bounds[dimension * 2] + cage.region_bounds[dimension * 2 + 1]) / 2
        expected[dimension] = 2 * plane - partner[dimension]
        maximum = max(
            maximum,
            *(abs(point[coordinate] - expected[coordinate]) for coordinate in range(3)),
            abs(cage.control_weights[index] - cage.control_weights[other_index]),
        )
    return maximum


def _symmetry_constrained_dof(cage: FreeformCageOperation, axes: tuple[FreeformAxis, ...]) -> int:
    shape = cage.lattice_shape
    total = len(cage.control_points) * 4
    visited: set[tuple[int, int, int]] = set()
    remaining = 0
    for raw_index in itertools.product(*(range(size) for size in shape)):
        index = (raw_index[0], raw_index[1], raw_index[2])
        if index in visited:
            continue
        orbit = {index}
        for axis in axes:
            for member in tuple(orbit):
                mirrored = list(member)
                mirrored[axis.coordinate_index] = (
                    shape[axis.coordinate_index] - 1 - member[axis.coordinate_index]
                )
                orbit.add((mirrored[0], mirrored[1], mirrored[2]))
        visited.update(orbit)
        fixed_axes = sum(
            shape[axis.coordinate_index] % 2 == 1
            and index[axis.coordinate_index] == shape[axis.coordinate_index] // 2
            for axis in axes
        )
        remaining += 4 - fixed_axes
    return total - remaining


def _unflat_index(index: int, shape: tuple[int, int, int]) -> tuple[int, int, int]:
    x = index % shape[0]
    y = index // shape[0] % shape[1]
    z = index // (shape[0] * shape[1])
    return x, y, z


def _flat_index(index: tuple[int, int, int], shape: tuple[int, int, int]) -> int:
    x, y, z = index
    return (z * shape[1] + y) * shape[0] + x


__all__ = [
    "CONSTRAINT_TOLERANCE",
    "FreeformAxis",
    "FreeformConstraintDiagnostics",
    "FreeformConstraintError",
    "constrain_freeform_cage_preview",
    "edit_freeform_cage_constrained",
]
