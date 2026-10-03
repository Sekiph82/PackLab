"""Bounded, backend-neutral cage deformation operations for Design Model previews."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .design_history import DesignEditCommand, EditTargetKind, create_edit_command
from .design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    ParameterType,
    resolve_design_model_feature,
    revise_design_model_revision,
    stable_feature_id,
)
from .geometry_adapter import TriangleMeshData

if TYPE_CHECKING:
    from .design_preview import DesignPreview

Point3 = tuple[float, float, float]
RegionBounds = tuple[float, float, float, float, float, float]
LatticeShape = tuple[int, int, int]

MAX_CAGE_AXIS_POINTS = 8
MAX_CAGE_CONTROL_POINTS = 512
MAX_CAGE_PREVIEW_VERTICES = 250_000
_PARAMETER_PREFIX = "freeform-cage:"


class FreeformCageError(ValueError):
    """Raised when cage parameters, ancestry, or preview bounds are invalid."""


@dataclass(frozen=True, slots=True)
class FreeformCageOperation:
    """Immutable explicit cage operation; realized vertices remain disposable preview data."""

    operation_id: str
    model_revision_id: str
    source_model_revision_id: str
    cage_feature_id: str
    affected_feature_id: str
    region_bounds: RegionBounds
    lattice_shape: LatticeShape
    control_points: tuple[Point3, ...]
    control_weights: tuple[float, ...]
    coordinate_unit: str
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.design-freeform-cage.v1",
            "authority_class": "DESIGN_MODEL_OPERATION",
            "operation_id": self.operation_id,
            "model_revision_id": self.model_revision_id,
            "source_model_revision_id": self.source_model_revision_id,
            "cage_feature_id": self.cage_feature_id,
            "affected_feature_id": self.affected_feature_id,
            "region_bounds_xyz": list(self.region_bounds),
            "lattice_shape": list(self.lattice_shape),
            "control_points": [list(point) for point in self.control_points],
            "control_weights": list(self.control_weights),
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "output_geometry": None,
        }


def create_freeform_cage(
    model: DesignModelRevision,
    *,
    affected_feature_id: str,
    region_bounds: RegionBounds,
    lattice_shape: LatticeShape,
    control_points: tuple[Point3, ...],
    control_weights: tuple[float, ...],
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> tuple[DesignModelRevision, FreeformCageOperation]:
    """Persist an explicit bounded cage as a stable Design Model feature."""

    _validate_model(model)
    parent = _resolve_feature(model, affected_feature_id)
    bounds = _region(region_bounds)
    shape = _shape(lattice_shape)
    points = _points(control_points, shape, bounds)
    weights = _weights(control_weights, shape)
    semantic_key = f"freeform-cage:{parent.feature_id}"
    feature = DesignModelFeatureReference(
        stable_feature_id(parent.component_id, FeatureKind.FREEFORM_CAGE, semantic_key),
        parent.component_id,
        FeatureKind.FREEFORM_CAGE,
        semantic_key,
    )
    if any(item.feature_id == feature.feature_id for item in model.features):
        raise FreeformCageError("freeform_cage_already_exists")
    prefix = _parameter_prefix(feature.feature_id)
    definition = {
        "contract": "packlab.design-freeform-cage-definition.v1",
        "cage_feature_id": feature.feature_id,
        "affected_feature_id": parent.feature_id,
        "source_model_revision_id": model.revision_id,
        "region_bounds_xyz": list(bounds),
        "lattice_shape": list(shape),
        "coordinate_unit": model.coordinate_unit,
        "authority_class": "DESIGN_MODEL_OPERATION",
        "preview_authority_class": "PREVIEW_PROXY",
        "raw_scan_points_retained": False,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
    }
    parameters = _cage_parameters(prefix, definition, points, weights, model.coordinate_unit)
    try:
        revised = revise_design_model_revision(
            model,
            parameters=(*model.parameters, *parameters),
            features=(*model.features, feature),
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise FreeformCageError("freeform_cage_design_model_invalid") from error
    cage = _operation(
        revised, model.revision_id, parent.feature_id, feature, bounds, shape, points, weights
    )
    return revised, cage


def edit_freeform_cage(
    model: DesignModelRevision,
    cage_feature_id: str,
    *,
    control_points: tuple[Point3, ...],
    control_weights: tuple[float, ...],
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> tuple[DesignModelRevision, FreeformCageOperation]:
    """Create an immutable revision with bounded cage control-point/weight edits."""

    cage = resolve_freeform_cage(model, cage_feature_id)
    points = _points(control_points, cage.lattice_shape, cage.region_bounds)
    weights = _weights(control_weights, cage.lattice_shape)
    prefix = _parameter_prefix(cage_feature_id)
    definition = _definition(model, cage_feature_id)
    parameters = _cage_parameters(prefix, definition, points, weights, model.coordinate_unit)
    replacement_ids = {item.parameter_id for item in parameters}
    revised_parameters = (
        tuple(item for item in model.parameters if item.parameter_id not in replacement_ids)
        + parameters
    )
    try:
        revised = revise_design_model_revision(
            model,
            parameters=revised_parameters,
            features=model.features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise FreeformCageError("freeform_cage_design_model_invalid") from error
    edited = _operation(
        revised,
        cage.source_model_revision_id,
        cage.affected_feature_id,
        resolve_design_model_feature(revised, cage_feature_id),
        cage.region_bounds,
        cage.lattice_shape,
        points,
        weights,
    )
    return revised, edited


def create_freeform_cage_edit_command(
    before_model: DesignModelRevision,
    after_model: DesignModelRevision,
    cage_feature_id: str,
) -> DesignEditCommand:
    """Create a normal history command for one cage control/weight parameter edit."""

    before_cage = resolve_freeform_cage(before_model, cage_feature_id)
    after_cage = resolve_freeform_cage(after_model, cage_feature_id)
    if (
        after_model.previous_revision_id != before_model.revision_id
        or before_model.project_id != after_model.project_id
        or before_model.parent_binding_revision_id != after_model.parent_binding_revision_id
        or before_model.fitted_to_scan_master_revision_id
        != after_model.fitted_to_scan_master_revision_id
        or before_model.scan_master_geometry_sha256 != after_model.scan_master_geometry_sha256
        or before_model.features != after_model.features
        or before_cage.source_model_revision_id != after_cage.source_model_revision_id
        or before_cage.affected_feature_id != after_cage.affected_feature_id
        or before_cage.region_bounds != after_cage.region_bounds
        or before_cage.lattice_shape != after_cage.lattice_shape
    ):
        raise FreeformCageError("freeform_cage_history_binding_changed")
    changed = tuple(
        (
            suffix,
            _parameter(before_model, f"{_parameter_prefix(cage_feature_id)}:{suffix}"),
            _parameter(after_model, f"{_parameter_prefix(cage_feature_id)}:{suffix}"),
        )
        for suffix in ("control_points", "control_weights")
        if _parameter(before_model, f"{_parameter_prefix(cage_feature_id)}:{suffix}")
        != _parameter(after_model, f"{_parameter_prefix(cage_feature_id)}:{suffix}")
    )
    if len(changed) != 1:
        raise FreeformCageError("freeform_cage_history_requires_one_parameter_edit")
    _suffix, before, after = changed[0]
    before_parameters = {item.parameter_id: item for item in before_model.parameters}
    after_parameters = {item.parameter_id: item for item in after_model.parameters}
    if set(before_parameters) != set(after_parameters) or tuple(
        parameter_id
        for parameter_id in sorted(before_parameters)
        if before_parameters[parameter_id] != after_parameters[parameter_id]
    ) != (before.parameter_id,):
        raise FreeformCageError("freeform_cage_history_requires_one_parameter_edit")
    return create_edit_command(
        before_model.revision_id,
        EditTargetKind.PARAMETER,
        before.parameter_id,
        before,
        after,
    )


def resolve_freeform_cage(
    model: DesignModelRevision, cage_feature_id: str
) -> FreeformCageOperation:
    """Rebuild the cage operation from its immutable versioned Design Model parameters."""

    _validate_model(model)
    feature = _resolve_feature(model, cage_feature_id)
    if feature.feature_kind is not FeatureKind.FREEFORM_CAGE:
        raise FreeformCageError("freeform_cage_feature_required")
    definition = _definition(model, cage_feature_id)
    affected_id = definition.get("affected_feature_id")
    source_model_id = definition.get("source_model_revision_id")
    if (
        not isinstance(affected_id, str)
        or not isinstance(source_model_id, str)
        or definition.get("cage_feature_id") != cage_feature_id
        or definition.get("coordinate_unit") != model.coordinate_unit
    ):
        raise FreeformCageError("freeform_cage_definition_invalid")
    affected = _resolve_feature(model, affected_id)
    if affected.component_id != feature.component_id:
        raise FreeformCageError("freeform_cage_component_mismatch")
    bounds = _region(definition.get("region_bounds_xyz"))
    shape = _shape(definition.get("lattice_shape"))
    points = _points(_array_parameter(model, cage_feature_id, "control_points"), shape, bounds)
    weights = _weights(_array_parameter(model, cage_feature_id, "control_weights"), shape)
    return _operation(
        model,
        source_model_id,
        affected.feature_id,
        feature,
        bounds,
        shape,
        points,
        weights,
    )


def deform_design_preview(
    preview: DesignPreview,
    model: DesignModelRevision,
    cage_feature_id: str,
) -> DesignPreview:
    """Apply a cage only to an exact parent PREVIEW_PROXY and preserve its feature mapping."""

    from .design_preview import MAX_PREVIEW_VERTICES, DesignPreview

    if not isinstance(preview, DesignPreview):
        raise FreeformCageError("freeform_cage_preview_required")
    cage = resolve_freeform_cage(model, cage_feature_id)
    if (
        preview.model_revision_id != cage.source_model_revision_id
        or preview.scan_master_revision_id != model.fitted_to_scan_master_revision_id
        or preview.scan_master_geometry_sha256 != model.scan_master_geometry_sha256
        or preview.parent_binding_revision_id != model.parent_binding_revision_id
        or preview.scale_state is not model.scale_state
        or preview.coordinate_unit != model.coordinate_unit
        or preview.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or preview.mold_use_authorized is not False
        or preview.authority_class != "PREVIEW_PROXY"
    ):
        raise FreeformCageError("freeform_cage_preview_parent_or_authority_invalid")
    if len(preview.mesh.vertices) > min(MAX_PREVIEW_VERTICES, MAX_CAGE_PREVIEW_VERTICES):
        raise FreeformCageError("freeform_cage_preview_work_bound_exceeded")
    rest_points = identity_control_points(cage.region_bounds, cage.lattice_shape)
    vertices = tuple(_deform_point(point, cage, rest_points) for point in preview.mesh.vertices)
    mesh = TriangleMeshData(vertices, preview.mesh.triangles)
    affected_indices = tuple(
        index
        for index, point in enumerate(preview.mesh.vertices)
        if _inside(point, cage.region_bounds)
    )
    mappings = {feature_id: set(indices) for feature_id, indices in preview.feature_vertex_indices}
    mappings.setdefault(cage.affected_feature_id, set()).update(affected_indices)
    mappings[cage.cage_feature_id] = set(affected_indices)
    ordered_mapping = tuple(
        (feature_id, tuple(sorted(indices))) for feature_id, indices in sorted(mappings.items())
    )
    return DesignPreview(
        mesh=mesh,
        model_revision_id=model.revision_id,
        scan_master_revision_id=model.fitted_to_scan_master_revision_id,
        scan_master_geometry_sha256=model.scan_master_geometry_sha256,
        parent_binding_revision_id=model.parent_binding_revision_id,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
        feature_vertex_indices=ordered_mapping,
    )


def identity_control_points(
    region_bounds: RegionBounds, lattice_shape: LatticeShape
) -> tuple[Point3, ...]:
    """Return the bounded regular rest lattice for a cage."""

    bounds = _region(region_bounds)
    shape = _shape(lattice_shape)
    axes = tuple(
        tuple(
            bounds[axis * 2] + (bounds[axis * 2 + 1] - bounds[axis * 2]) * i / (count - 1)
            for i in range(count)
        )
        for axis, count in enumerate(shape)
    )
    return tuple((x, y, z) for z in axes[2] for y in axes[1] for x in axes[0])


def _deform_point(
    point: Point3, cage: FreeformCageOperation, rest_points: tuple[Point3, ...]
) -> Point3:
    if not _inside(point, cage.region_bounds):
        return point
    shape = cage.lattice_shape
    axes = tuple(
        min(
            shape[axis] - 1.0,
            max(
                0.0,
                (point[axis] - cage.region_bounds[axis * 2])
                / (cage.region_bounds[axis * 2 + 1] - cage.region_bounds[axis * 2])
                * (shape[axis] - 1),
            ),
        )
        for axis in range(3)
    )
    lows = tuple(min(shape[axis] - 2, int(math.floor(axes[axis]))) for axis in range(3))
    fractions = tuple(axes[axis] - lows[axis] for axis in range(3))
    displacement = [0.0, 0.0, 0.0]
    for dz, dy, dx in itertools.product((0, 1), repeat=3):
        indices = (lows[0] + dx, lows[1] + dy, lows[2] + dz)
        index = _flat_index(indices, shape)
        basis = math.prod(
            fractions[axis] if bit else 1.0 - fractions[axis]
            for axis, bit in enumerate((dx, dy, dz))
        )
        rest = rest_points[index]
        weight = basis * cage.control_weights[index]
        for axis in range(3):
            displacement[axis] += weight * (cage.control_points[index][axis] - rest[axis])
    result: Point3 = (
        point[0] + displacement[0],
        point[1] + displacement[1],
        point[2] + displacement[2],
    )
    if not _inside(result, cage.region_bounds):
        raise FreeformCageError("freeform_cage_deformed_point_outside_region")
    return (result[0], result[1], result[2])


def _operation(
    model: DesignModelRevision,
    source_model_id: str,
    affected_feature_id: str,
    cage_feature: DesignModelFeatureReference,
    bounds: RegionBounds,
    shape: LatticeShape,
    points: tuple[Point3, ...],
    weights: tuple[float, ...],
) -> FreeformCageOperation:
    payload = {
        "contract": "packlab.design-freeform-cage.v1",
        "model_revision_id": model.revision_id,
        "source_model_revision_id": source_model_id,
        "cage_feature_id": cage_feature.feature_id,
        "affected_feature_id": affected_feature_id,
        "region_bounds_xyz": bounds,
        "lattice_shape": shape,
        "control_points": points,
        "control_weights": weights,
        "coordinate_unit": model.coordinate_unit,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return FreeformCageOperation(
        "design-freeform-cage:" + digest,
        model.revision_id,
        source_model_id,
        cage_feature.feature_id,
        affected_feature_id,
        bounds,
        shape,
        points,
        weights,
        model.coordinate_unit,
    )


def _cage_parameters(
    prefix: str,
    definition: dict[str, object],
    points: tuple[Point3, ...],
    weights: tuple[float, ...],
    coordinate_unit: str,
) -> tuple[DesignModelParameter, ...]:
    return (
        DesignModelParameter(f"{prefix}:definition", definition, ParameterType.OBJECT),
        DesignModelParameter(
            f"{prefix}:control_points",
            [list(point) for point in points],
            ParameterType.ARRAY,
            coordinate_unit,
        ),
        DesignModelParameter(
            f"{prefix}:control_weights",
            list(weights),
            ParameterType.ARRAY,
        ),
    )


def _definition(model: DesignModelRevision, cage_feature_id: str) -> dict[str, object]:
    parameter = _parameter(model, f"{_parameter_prefix(cage_feature_id)}:definition")
    value = parameter.as_dict()["value"]
    if (
        not isinstance(value, dict)
        or value.get("contract") != "packlab.design-freeform-cage-definition.v1"
    ):
        raise FreeformCageError("freeform_cage_definition_invalid")
    return value


def _array_parameter(
    model: DesignModelRevision, cage_feature_id: str, suffix: str
) -> tuple[object, ...]:
    parameter = _parameter(model, f"{_parameter_prefix(cage_feature_id)}:{suffix}")
    expected_unit = model.coordinate_unit if suffix == "control_points" else None
    if parameter.unit != expected_unit:
        raise FreeformCageError("freeform_cage_parameter_unit_mismatch")
    value = parameter.as_dict()["value"]
    if not isinstance(value, list):
        raise FreeformCageError("freeform_cage_parameter_invalid")
    return tuple(value)


def _parameter(model: DesignModelRevision, parameter_id: str) -> DesignModelParameter:
    matches = tuple(item for item in model.parameters if item.parameter_id == parameter_id)
    if len(matches) != 1:
        raise FreeformCageError("freeform_cage_parameter_missing_or_ambiguous")
    return matches[0]


def _parameter_prefix(feature_id: str) -> str:
    return _PARAMETER_PREFIX + feature_id.rsplit(":", 1)[-1]


def _resolve_feature(model: DesignModelRevision, feature_id: str) -> DesignModelFeatureReference:
    try:
        return resolve_design_model_feature(model, feature_id)
    except DesignModelError as error:
        raise FreeformCageError("freeform_cage_feature_missing_or_stale") from error


def _validate_model(model: DesignModelRevision) -> None:
    if not isinstance(model, DesignModelRevision):
        raise FreeformCageError("design_model_revision_required")
    if (
        model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or model.mold_use_authorized is not False
        or model.coordinate_unit not in {"reconstruction_units", "mm_unverified"}
    ):
        raise FreeformCageError("design_model_authority_invalid")


def _region(value: object) -> RegionBounds:
    if not isinstance(value, (tuple, list)) or len(value) != 6:
        raise FreeformCageError("freeform_cage_region_bounds_invalid")
    numbers = tuple(_finite(item, "freeform_cage_region_bounds_invalid") for item in value)
    if any(numbers[axis * 2] >= numbers[axis * 2 + 1] for axis in range(3)):
        raise FreeformCageError("freeform_cage_region_bounds_invalid")
    return (numbers[0], numbers[1], numbers[2], numbers[3], numbers[4], numbers[5])


def _shape(value: object) -> LatticeShape:
    if (
        not isinstance(value, (tuple, list))
        or len(value) != 3
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
        or any(not 2 <= item <= MAX_CAGE_AXIS_POINTS for item in value)
        or math.prod(value) > MAX_CAGE_CONTROL_POINTS
    ):
        raise FreeformCageError("freeform_cage_lattice_shape_invalid")
    return (value[0], value[1], value[2])


def _points(value: object, shape: LatticeShape, bounds: RegionBounds) -> tuple[Point3, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != math.prod(shape):
        raise FreeformCageError("freeform_cage_control_point_count_invalid")
    points: list[Point3] = []
    for point in value:
        if not isinstance(point, (tuple, list)) or len(point) != 3:
            raise FreeformCageError("freeform_cage_control_point_invalid")
        converted: Point3 = (
            _finite(point[0], "freeform_cage_control_point_invalid"),
            _finite(point[1], "freeform_cage_control_point_invalid"),
            _finite(point[2], "freeform_cage_control_point_invalid"),
        )
        if not _inside(converted, bounds):
            raise FreeformCageError("freeform_cage_control_point_outside_region")
        points.append((converted[0], converted[1], converted[2]))
    return tuple(points)


def _weights(value: object, shape: LatticeShape) -> tuple[float, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != math.prod(shape):
        raise FreeformCageError("freeform_cage_weight_count_invalid")
    weights = tuple(_finite(item, "freeform_cage_weight_invalid") for item in value)
    if any(not 0.0 <= item <= 1.0 for item in weights):
        raise FreeformCageError("freeform_cage_weight_out_of_range")
    return weights


def _inside(point: tuple[float, float, float], bounds: RegionBounds) -> bool:
    return all(bounds[axis * 2] <= point[axis] <= bounds[axis * 2 + 1] for axis in range(3))


def _flat_index(indices: tuple[int, int, int], shape: LatticeShape) -> int:
    x, y, z = indices
    return (z * shape[1] + y) * shape[0] + x


def _finite(value: object, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FreeformCageError(code)
    result = float(value)
    if not math.isfinite(result):
        raise FreeformCageError(code)
    return result


__all__ = [
    "MAX_CAGE_AXIS_POINTS",
    "MAX_CAGE_CONTROL_POINTS",
    "MAX_CAGE_PREVIEW_VERTICES",
    "FreeformCageError",
    "FreeformCageOperation",
    "create_freeform_cage",
    "create_freeform_cage_edit_command",
    "deform_design_preview",
    "edit_freeform_cage",
    "identity_control_points",
    "resolve_freeform_cage",
]
