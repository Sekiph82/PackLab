"""Deterministic vector dimension entities derived from exact CAD BREP bounds."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .cad_adapter import (
    cad_shape_precise_bounds,
)
from .cad_brep import CadBrepRepresentationRevision
from .cad_feature_map import map_design_model_features_to_brep
from .cad_validation import validate_cad_brep
from .design_model import (
    DesignModelFeatureReference,
    DesignModelRevision,
    resolve_design_model_feature,
)
from .reconstruction import ScaleState

DIMENSION_ANNOTATION_CONTRACT = "packlab.technical-drawing-dimensions.v1"
_MAX_FEATURE_DIMENSIONS = 16
_ROUND_DIGITS = 12
_IDENTITY_TRANSFORM = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


class DrawingDimensionError(ValueError):
    """Raised when dimensions cannot be derived from exact current CAD geometry."""


@dataclass(frozen=True, slots=True)
class SelectedFeatureDimensionSource:
    """Exact BREP representing one stably mapped feature/component envelope."""

    component_reference_id: str
    placement_revision_id: str
    feature_id: str
    representation: CadBrepRepresentationRevision
    placement_matrix: tuple[float, ...] = _IDENTITY_TRANSFORM


@dataclass(frozen=True, slots=True)
class DimensionAnnotation:
    dimension_id: str
    dimension_kind: str
    measurement_axis: str
    value: float
    coordinate_unit: str
    unit_label: str
    value_status: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    coordinate_frame_id: str
    component_reference_id: str
    feature_id: str | None
    feature_kind: str | None
    feature_mapping_revision_id: str | None
    feature_reference_scope: str | None
    placement_revision_id: str | None
    placement_matrix: tuple[float, ...] | None
    view_id: str
    extension_lines: tuple[tuple[tuple[float, float], tuple[float, float]], ...]
    dimension_line: tuple[tuple[float, float], tuple[float, float]]
    arrow_anchors: tuple[tuple[float, float], tuple[float, float]]
    text_anchor: tuple[float, float]
    collision_group: str
    collision_stack_index: int
    collision_policy: str = "DISTINCT_OUTSIDE_BOUNDARY_STACK"
    typography_baked_into_measurement: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "dimension_id": self.dimension_id,
            "dimension_kind": self.dimension_kind,
            "measurement_axis": self.measurement_axis,
            "value": self.value,
            "coordinate_unit": self.coordinate_unit,
            "unit_label": self.unit_label,
            "value_status": self.value_status,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_brep_geometry_sha256": self.source_brep_geometry_sha256,
            "coordinate_frame_id": self.coordinate_frame_id,
            "component_reference_id": self.component_reference_id,
            "feature_reference": (
                {
                    "feature_id": self.feature_id,
                    "feature_kind": self.feature_kind,
                    "mapping_revision_id": self.feature_mapping_revision_id,
                    "mapping_scope": self.feature_reference_scope,
                }
                if self.feature_id is not None
                else None
            ),
            "placement": (
                {
                    "revision_id": self.placement_revision_id,
                    "matrix_row_major_4x4": list(self.placement_matrix or ()),
                    "authority": "EXPLICIT_INPUT_REFERENCE",
                }
                if self.placement_revision_id is not None
                else None
            ),
            "view_id": self.view_id,
            "extension_lines": [[list(start), list(end)] for start, end in self.extension_lines],
            "dimension_line": [list(point) for point in self.dimension_line],
            "arrow_anchors": [list(point) for point in self.arrow_anchors],
            "text_anchor": list(self.text_anchor),
            "collision_placement": {
                "group": self.collision_group,
                "stack_index": self.collision_stack_index,
                "policy": self.collision_policy,
            },
            "typography_baked_into_measurement": self.typography_baked_into_measurement,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


@dataclass(frozen=True, slots=True)
class TechnicalDrawingDimensions:
    revision_id: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    coordinate_frame_id: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    dimensions: tuple[DimensionAnnotation, ...]
    contract: str = DIMENSION_ANNOTATION_CONTRACT

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "DERIVED_TECHNICAL_DRAWING_DIMENSIONS",
            "revision_id": self.revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_brep_geometry_sha256": self.source_brep_geometry_sha256,
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "coordinate_frame_id": self.coordinate_frame_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "unit_disclaimer": (
                "Numerical millimetres are unverified design geometry; physical accuracy is deferred."
                if self.scale_state == ScaleState.METRIC_UNVERIFIED.value
                else "Dimensions are expressed in reconstruction_units, not millimetres."
            ),
            "source_truth": "EXACT_CAD_BREP_NUMERICAL_BOUNDS",
            "raster_source_of_truth": False,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
            "dimensions": [item.as_dict() for item in self.dimensions],
            "scan_master_promoted": False,
            "design_model_replaced": False,
            "cad_brep_replaced": False,
        }


@dataclass(frozen=True, slots=True)
class _AnnotationGeometry:
    view_id: str
    extension_lines: tuple[tuple[tuple[float, float], tuple[float, float]], ...]
    dimension_line: tuple[tuple[float, float], tuple[float, float]]
    arrow_anchors: tuple[tuple[float, float], tuple[float, float]]
    text_anchor: tuple[float, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "view_id": self.view_id,
            "extension_lines": [[list(start), list(end)] for start, end in self.extension_lines],
            "dimension_line": [list(point) for point in self.dimension_line],
            "arrow_anchors": [list(point) for point in self.arrow_anchors],
            "text_anchor": list(self.text_anchor),
        }


def build_drawing_dimensions(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    *,
    coordinate_frame_id: str,
    selected_features: tuple[SelectedFeatureDimensionSource, ...] = (),
) -> TechnicalDrawingDimensions:
    """Create overall H/W/D and selected whole-solid feature dimensions."""
    if not isinstance(model, DesignModelRevision):
        raise DrawingDimensionError("design_model_revision_required")
    _validate_representation(model, representation)
    if (
        not isinstance(coordinate_frame_id, str)
        or not coordinate_frame_id.strip()
        or len(coordinate_frame_id) > 128
    ):
        raise DrawingDimensionError("drawing_dimension_coordinate_frame_invalid")
    if (
        not isinstance(selected_features, tuple)
        or len(selected_features) > _MAX_FEATURE_DIMENSIONS
        or any(not isinstance(item, SelectedFeatureDimensionSource) for item in selected_features)
    ):
        raise DrawingDimensionError("drawing_dimension_feature_sources_invalid")
    parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if parent_revision is None:
        raise DrawingDimensionError("drawing_dimension_parent_authority_missing")
    if not representation.coordinate_unit == model.coordinate_unit:
        raise DrawingDimensionError("drawing_dimension_source_unit_mismatch")
    try:
        base_validation = validate_cad_brep(representation)
        if not base_validation.valid_closed_solid:
            raise DrawingDimensionError("drawing_dimension_valid_closed_solid_required")
        overall_bounds = cad_shape_precise_bounds(representation.shape_handle)
    except DrawingDimensionError:
        raise
    except Exception as error:
        raise DrawingDimensionError("drawing_dimension_source_processing_failed") from error
    dimensions: list[DimensionAnnotation] = []
    collision_slots: dict[tuple[str, str], int] = {}
    _append_bounds_dimensions(
        dimensions,
        collision_slots,
        model,
        representation,
        overall_bounds,
        coordinate_frame_id,
        component_reference_id="overall",
        feature=None,
        feature_mapping_revision_id=None,
        placement_revision_id=None,
        placement_matrix=None,
        dimension_prefix="OVERALL",
    )

    ordered_sources = tuple(
        sorted(
            selected_features,
            key=lambda item: (item.component_reference_id, item.feature_id),
        )
    )
    seen_components: set[str] = set()
    for source in ordered_sources:
        if (
            not isinstance(source.component_reference_id, str)
            or not source.component_reference_id.strip()
            or len(source.component_reference_id) > 128
            or source.component_reference_id in seen_components
        ):
            raise DrawingDimensionError("drawing_dimension_component_reference_invalid")
        seen_components.add(source.component_reference_id)
        if (
            not isinstance(source.placement_revision_id, str)
            or not source.placement_revision_id.strip()
            or len(source.placement_revision_id) > 128
        ):
            raise DrawingDimensionError("drawing_dimension_placement_reference_invalid")
        if source.representation.source_design_model_revision_id != model.revision_id:
            raise DrawingDimensionError("drawing_dimension_feature_model_revision_mismatch")
        try:
            feature = resolve_design_model_feature(model, source.feature_id)
        except Exception as error:
            raise DrawingDimensionError(
                "drawing_dimension_feature_reference_stale_or_missing"
            ) from error
        _validate_representation(model, source.representation)
        try:
            validation = validate_cad_brep(source.representation)
            if not validation.valid_closed_solid:
                raise DrawingDimensionError("drawing_dimension_feature_brep_invalid")
            mapping = map_design_model_features_to_brep(model, source.representation)
            reference = next(
                item for item in mapping.references if item.feature_id == feature.feature_id
            )
        except DrawingDimensionError:
            raise
        except Exception as error:
            raise DrawingDimensionError("drawing_dimension_feature_mapping_failed") from error
        if (
            reference.status != "MAPPED"
            or reference.target_selector != "whole_output_solid"
            or reference.reference_scope != "whole_component_solid"
        ):
            raise DrawingDimensionError("drawing_dimension_feature_mapping_not_unambiguous")
        try:
            feature_bounds = cad_shape_precise_bounds(
                source.representation.shape_handle,
                placement_matrix=source.placement_matrix,
            )
        except Exception as error:
            raise DrawingDimensionError("drawing_dimension_feature_bounds_failed") from error
        _append_bounds_dimensions(
            dimensions,
            collision_slots,
            model,
            source.representation,
            feature_bounds,
            coordinate_frame_id,
            component_reference_id=source.component_reference_id,
            feature=feature,
            feature_mapping_revision_id=mapping.revision_id,
            placement_revision_id=source.placement_revision_id,
            placement_matrix=source.placement_matrix,
            dimension_prefix="FEATURE",
        )

    canonical_dimensions = tuple(sorted(dimensions, key=lambda item: item.dimension_id))
    identity = {
        "model_revision_id": model.revision_id,
        "brep_revision_id": representation.revision_id,
        "brep_geometry_sha256": representation.geometry_sha256,
        "parent_kind": model.parent_kind.value,
        "parent_revision_id": parent_revision,
        "scale_state": model.scale_state.value,
        "coordinate_unit": model.coordinate_unit,
        "coordinate_frame_id": coordinate_frame_id,
        "dimensions": [item.as_dict() for item in canonical_dimensions],
    }
    revision_id = (
        "technical-drawing-dimensions:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    return TechnicalDrawingDimensions(
        revision_id=revision_id,
        source_design_model_revision_id=model.revision_id,
        source_brep_revision_id=representation.revision_id,
        source_brep_geometry_sha256=representation.geometry_sha256,
        parent_kind=model.parent_kind.value,
        parent_authority_revision_id=parent_revision,
        scale_state=model.scale_state.value,
        coordinate_unit=model.coordinate_unit,
        coordinate_frame_id=coordinate_frame_id,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
        dimensions=canonical_dimensions,
    )


def _validate_representation(
    model: DesignModelRevision, representation: CadBrepRepresentationRevision
) -> None:
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise DrawingDimensionError("cad_brep_representation_required")
    parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if (
        representation.source_design_model_revision_id != model.revision_id
        or representation.parent_kind is not model.parent_kind
        or representation.parent_authority_revision_id != parent_revision
        or representation.scale_state is not model.scale_state
        or representation.coordinate_unit != model.coordinate_unit
        or representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized is not False
        or model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or model.mold_use_authorized is not False
    ):
        raise DrawingDimensionError("drawing_dimension_source_authority_mismatch")


def _append_bounds_dimensions(
    output: list[DimensionAnnotation],
    collision_slots: dict[tuple[str, str], int],
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    bounds: tuple[float, float, float, float, float, float],
    coordinate_frame_id: str,
    *,
    component_reference_id: str,
    feature: DesignModelFeatureReference | None,
    feature_mapping_revision_id: str | None,
    placement_revision_id: str | None,
    placement_matrix: tuple[float, ...] | None,
    dimension_prefix: str,
) -> None:
    spans = _spans(bounds)
    axis_specs: tuple[tuple[str, str, float, str], ...] = (
        ("Z", "HEIGHT", spans[2], "FRONT"),
        ("X", "WIDTH_X", spans[0], "FRONT"),
        ("Y", "DEPTH_Y", spans[1], "TOP"),
    )
    if feature is not None:
        axis_specs = tuple(
            (axis, f"{feature.feature_kind.value.upper().replace('-', '_')}_{name}", value, view)
            for axis, name, value, view in axis_specs
        )
    unit_label = (
        "mm (UNVERIFIED)"
        if model.scale_state is ScaleState.METRIC_UNVERIFIED
        else "reconstruction_units"
    )
    for axis, suffix, value, view_id in axis_specs:
        _positive_finite(value)
        key = (view_id, axis)
        stack_index = collision_slots.get(key, 0)
        collision_slots[key] = stack_index + 1
        geometry = _annotation_geometry(axis, bounds, stack_index)
        document: dict[str, object] = {
            "kind": f"{dimension_prefix}_{suffix}",
            "axis": axis,
            "value": _round(value),
            "unit": model.coordinate_unit,
            "unit_label": unit_label,
            "component_reference_id": component_reference_id,
            "feature_id": feature.feature_id if feature is not None else None,
            "feature_mapping_revision_id": feature_mapping_revision_id,
            "source_brep_revision_id": representation.revision_id,
            "source_brep_geometry_sha256": representation.geometry_sha256,
            "view_id": view_id,
            "geometry": geometry.as_dict(),
            "collision_stack_index": stack_index,
        }
        digest = hashlib.sha256(
            json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
        output.append(
            DimensionAnnotation(
                dimension_id=f"drawing-dimension:{digest}",
                dimension_kind=str(document["kind"]),
                measurement_axis=axis,
                value=_round(value),
                coordinate_unit=model.coordinate_unit,
                unit_label=unit_label,
                value_status=(
                    "MM_UNVERIFIED"
                    if model.scale_state is ScaleState.METRIC_UNVERIFIED
                    else "RELATIVE_RECONSTRUCTION_UNITS"
                ),
                source_design_model_revision_id=model.revision_id,
                source_brep_revision_id=representation.revision_id,
                source_brep_geometry_sha256=representation.geometry_sha256,
                coordinate_frame_id=coordinate_frame_id,
                component_reference_id=component_reference_id,
                feature_id=feature.feature_id if feature is not None else None,
                feature_kind=feature.feature_kind.value if feature is not None else None,
                feature_mapping_revision_id=feature_mapping_revision_id,
                feature_reference_scope=("whole_component_solid" if feature is not None else None),
                placement_revision_id=placement_revision_id,
                placement_matrix=placement_matrix,
                view_id=view_id,
                extension_lines=geometry.extension_lines,
                dimension_line=geometry.dimension_line,
                arrow_anchors=geometry.arrow_anchors,
                text_anchor=geometry.text_anchor,
                collision_group=f"{view_id}:{axis}",
                collision_stack_index=stack_index,
            )
        )


def _spans(bounds: tuple[float, float, float, float, float, float]) -> tuple[float, float, float]:
    if len(bounds) != 6 or any(not math.isfinite(value) for value in bounds):
        raise DrawingDimensionError("drawing_dimension_bounds_invalid")
    minimum = bounds[:3]
    maximum = bounds[3:]
    if any(maximum[index] <= minimum[index] for index in range(3)):
        raise DrawingDimensionError("drawing_dimension_span_must_be_positive")
    return tuple(maximum[index] - minimum[index] for index in range(3))  # type: ignore[return-value]


def _annotation_geometry(
    axis: str, bounds: tuple[float, float, float, float, float, float], stack_index: int
) -> _AnnotationGeometry:
    xmin, ymin, zmin, xmax, ymax, zmax = bounds
    span = max(xmax - xmin, ymax - ymin, zmax - zmin)
    offset = span * 0.06 * (stack_index + 1)
    if axis == "X":
        start = (xmin, zmin)
        end = (xmax, zmin)
        arrows = ((xmin, zmin - offset), (xmax, zmin - offset))
        text = ((xmin + xmax) / 2.0, zmin - offset * 1.25)
        view = "FRONT"
    elif axis == "Y":
        projected_min_x = -xmax
        start = (projected_min_x, ymin)
        end = (projected_min_x, ymax)
        arrows = ((projected_min_x - offset, ymin), (projected_min_x - offset, ymax))
        text = (projected_min_x - offset * 1.25, (ymin + ymax) / 2.0)
        view = "TOP"
    else:
        start = (xmin, zmin)
        end = (xmin, zmax)
        arrows = ((xmin - offset, zmin), (xmin - offset, zmax))
        text = (xmin - offset * 1.25, (zmin + zmax) / 2.0)
        view = "FRONT"
    return _AnnotationGeometry(
        view_id=view,
        extension_lines=((start, arrows[0]), (end, arrows[1])),
        dimension_line=arrows,
        arrow_anchors=arrows,
        text_anchor=text,
    )


def _positive_finite(value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise DrawingDimensionError("drawing_dimension_span_must_be_positive")


def _round(value: float) -> float:
    rounded = round(value, _ROUND_DIGITS)
    return 0.0 if rounded == 0.0 else rounded


__all__ = [
    "DIMENSION_ANNOTATION_CONTRACT",
    "DimensionAnnotation",
    "DrawingDimensionError",
    "SelectedFeatureDimensionSource",
    "TechnicalDrawingDimensions",
    "build_drawing_dimensions",
]
