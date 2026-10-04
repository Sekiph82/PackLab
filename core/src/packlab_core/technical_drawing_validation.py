"""Independent numerical checks for drawing annotations and exact CAD sources."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .cad_adapter import cad_shape_precise_bounds
from .cad_brep import CadBrepRepresentationRevision
from .cad_feature_map import map_design_model_features_to_brep
from .cad_validation import validate_cad_brep
from .design_model import DesignModelRevision, resolve_design_model_feature
from .reconstruction import ScaleState
from .technical_drawing_dimensions import (
    DimensionAnnotation,
    SelectedFeatureDimensionSource,
    TechnicalDrawingDimensions,
)
from .technical_drawing_export import TechnicalDrawingVectorExport
from .technical_drawing_sections import DrawingSectionViewModel
from .technical_drawing_title_block import TechnicalDrawingTitleBlock

DRAWING_VALIDATION_CONTRACT = "packlab.technical-drawing-consistency-report.v1"
DEFAULT_ABSOLUTE_TOLERANCE = 1e-8
DEFAULT_RELATIVE_TOLERANCE = 1e-10


class DrawingValidationError(ValueError):
    """Raised when source revisions or authority cannot support a comparison."""


@dataclass(frozen=True, slots=True)
class DrawingDimensionCheck:
    dimension_id: str
    dimension_kind: str
    source_component_reference_id: str
    expected_value: float
    drawing_value: float
    coordinate_unit: str
    expected_unit_label: str
    drawing_unit_label: str
    absolute_error: float
    allowed_error: float
    passed: bool
    failure_code: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "dimension_id": self.dimension_id,
            "dimension_kind": self.dimension_kind,
            "source_component_reference_id": self.source_component_reference_id,
            "expected_value": self.expected_value,
            "drawing_value": self.drawing_value,
            "coordinate_unit": self.coordinate_unit,
            "expected_unit_label": self.expected_unit_label,
            "drawing_unit_label": self.drawing_unit_label,
            "absolute_error": self.absolute_error,
            "allowed_error": self.allowed_error,
            "status": "PASS" if self.passed else "FAIL",
            "failure_code": self.failure_code,
            "source_truth": "EXACT_CAD_BREP_NUMERICAL_BOUNDS",
            "pixel_measurement_used": False,
        }


@dataclass(frozen=True, slots=True)
class DrawingConsistencyReport:
    revision_id: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    parent_kind: str
    parent_authority_revision_id: str
    dimensions_revision_id: str
    title_block_revision_id: str
    drawing_revision_id: str
    scale_state: str
    coordinate_unit: str
    absolute_tolerance: float
    relative_tolerance: float
    checks: tuple[DrawingDimensionCheck, ...]
    section_revision_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": DRAWING_VALIDATION_CONTRACT,
            "revision_id": self.revision_id,
            "status": "PASS" if self.passed else "FAIL",
            "source": {
                "design_model_revision_id": self.source_design_model_revision_id,
                "cad_representation_revision_id": self.source_brep_revision_id,
                "cad_geometry_sha256": self.source_brep_geometry_sha256,
                "parent_authority": {
                    "kind": self.parent_kind,
                    "revision_id": self.parent_authority_revision_id,
                },
            },
            "drawing": {
                "dimensions_revision_id": self.dimensions_revision_id,
                "title_block_revision_id": self.title_block_revision_id,
                "drawing_revision_id": self.drawing_revision_id,
                "section_revision_ids": list(self.section_revision_ids),
            },
            "units": {"scale_state": self.scale_state, "coordinate_unit": self.coordinate_unit},
            "comparison_tolerance": {
                "absolute_source_units": self.absolute_tolerance,
                "relative_fraction": self.relative_tolerance,
                "is_physical_tolerance": False,
            },
            "checks": [check.as_dict() for check in self.checks],
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
            "pixel_measurement_used": False,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class _ExpectedDimension:
    kind: str
    component_reference_id: str
    feature_id: str | None
    source_brep_revision_id: str
    source_geometry_sha256: str
    feature_kind: str | None
    feature_mapping_revision_id: str | None
    feature_reference_scope: str | None
    placement_revision_id: str | None
    measurement_axis: str
    value: float
    unit_label: str
    value_status: str


def validate_drawing_dimensions(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    dimensions: TechnicalDrawingDimensions,
    title_block: TechnicalDrawingTitleBlock,
    vector_export: TechnicalDrawingVectorExport,
    *,
    selected_features: tuple[SelectedFeatureDimensionSource, ...] = (),
    sections: tuple[DrawingSectionViewModel, ...] = (),
    absolute_tolerance: float = DEFAULT_ABSOLUTE_TOLERANCE,
    relative_tolerance: float = DEFAULT_RELATIVE_TOLERANCE,
) -> DrawingConsistencyReport:
    """Recompute drawing extents from exact CAD shapes, then compare annotations."""
    _validate_sources(
        model,
        representation,
        dimensions,
        title_block,
        vector_export,
        selected_features,
        sections,
    )
    _validate_tolerances(absolute_tolerance, relative_tolerance)
    unit_label, value_status = _unit_presentation(model.scale_state)

    try:
        validation = validate_cad_brep(representation)
        if not validation.valid_closed_solid:
            raise DrawingValidationError("drawing_validation_valid_source_brep_required")
        overall_bounds = cad_shape_precise_bounds(representation.shape_handle)
    except DrawingValidationError:
        raise
    except Exception as error:
        raise DrawingValidationError("drawing_validation_source_geometry_failed") from error
    dimensions_document = dimensions.as_dict()
    export_document = vector_export.as_dict()
    if (
        dimensions_document.get("source_truth") != "EXACT_CAD_BREP_NUMERICAL_BOUNDS"
        or dimensions_document.get("raster_source_of_truth") is not False
        or export_document.get("raster_source_of_truth") is not False
        or vector_export.manifest.get("raster_entities") != 0
    ):
        raise DrawingValidationError("drawing_validation_pixel_authority_rejected")
    expected: dict[tuple[str, str, str | None], _ExpectedDimension] = {}
    _add_expected_dimensions(
        expected,
        overall_bounds,
        component_reference_id="overall",
        feature_id=None,
        representation=representation,
        feature_kind=None,
        unit_label=unit_label,
        value_status=value_status,
    )

    for source in selected_features:
        try:
            parent_revision = _parent_revision(model)
            if (
                source.representation.source_design_model_revision_id != model.revision_id
                or source.representation.parent_kind is not model.parent_kind
                or source.representation.parent_authority_revision_id != parent_revision
                or source.representation.scale_state is not model.scale_state
                or source.representation.coordinate_unit != model.coordinate_unit
                or source.representation.physical_accuracy_validation_status
                != "DEFERRED_OWNER_VALIDATION"
                or source.representation.mold_use_authorized is not False
            ):
                raise DrawingValidationError("drawing_validation_feature_source_mismatch")
            if (
                not isinstance(source.placement_revision_id, str)
                or not source.placement_revision_id.strip()
                or len(source.placement_revision_id) > 128
            ):
                raise DrawingValidationError("drawing_validation_feature_placement_invalid")
            feature = resolve_design_model_feature(model, source.feature_id)
            feature_validation = validate_cad_brep(source.representation)
            if not feature_validation.valid_closed_solid:
                raise DrawingValidationError("drawing_validation_feature_brep_invalid")
            mapping = map_design_model_features_to_brep(model, source.representation)
            mapped = tuple(
                item for item in mapping.references if item.feature_id == feature.feature_id
            )
            if (
                len(mapped) != 1
                or mapped[0].status != "MAPPED"
                or mapped[0].target_selector != "whole_output_solid"
                or mapped[0].reference_scope != "whole_component_solid"
            ):
                raise DrawingValidationError("drawing_validation_feature_mapping_ambiguous")
            bounds = cad_shape_precise_bounds(
                source.representation.shape_handle,
                placement_matrix=source.placement_matrix,
            )
        except DrawingValidationError:
            raise
        except Exception as error:
            raise DrawingValidationError("drawing_validation_feature_source_invalid") from error
        _add_expected_dimensions(
            expected,
            bounds,
            component_reference_id=source.component_reference_id,
            feature_id=feature.feature_id,
            representation=source.representation,
            feature_kind=feature.feature_kind.value,
            feature_mapping_revision_id=mapping.revision_id,
            placement_revision_id=source.placement_revision_id,
            unit_label=unit_label,
            value_status=value_status,
        )

    actual: dict[tuple[str, str, str | None], DimensionAnnotation] = {}
    for dimension in dimensions.dimensions:
        if not isinstance(dimension, DimensionAnnotation):
            raise DrawingValidationError("drawing_validation_dimension_entity_invalid")
        key = (dimension.component_reference_id, dimension.dimension_kind, dimension.feature_id)
        if key in actual:
            raise DrawingValidationError("drawing_validation_duplicate_dimension_entity")
        actual[key] = dimension
    if set(actual) != set(expected):
        raise DrawingValidationError("drawing_validation_dimension_set_mismatch")

    checks: list[DrawingDimensionCheck] = []
    for key in sorted(expected, key=lambda item: (item[0], item[1], item[2] or "")):
        source_item = expected[key]
        dimension = actual[key]
        _validate_dimension_provenance(
            dimension,
            dimensions,
            source_item,
            value_status,
        )
        source_value = source_item.value
        if (
            isinstance(dimension.value, bool)
            or not isinstance(dimension.value, (int, float))
            or not math.isfinite(dimension.value)
        ):
            raise DrawingValidationError("drawing_validation_dimension_value_invalid")
        drawing_value = float(dimension.value)
        absolute_error = abs(drawing_value - source_value)
        allowed = absolute_tolerance + relative_tolerance * abs(source_value)
        passed = absolute_error <= allowed
        failure = None
        if dimension.unit_label != source_item.unit_label:
            passed = False
            failure = "drawing_dimension_unit_label_mismatch"
        elif absolute_error > allowed:
            passed = False
            failure = "drawing_dimension_value_mismatch"
        checks.append(
            DrawingDimensionCheck(
                dimension_id=dimension.dimension_id,
                dimension_kind=dimension.dimension_kind,
                source_component_reference_id=dimension.component_reference_id,
                expected_value=source_value,
                drawing_value=drawing_value,
                coordinate_unit=dimension.coordinate_unit,
                expected_unit_label=source_item.unit_label,
                drawing_unit_label=dimension.unit_label,
                absolute_error=absolute_error,
                allowed_error=allowed,
                passed=passed,
                failure_code=failure,
            )
        )

    section_ids = tuple(sorted(section.revision_id for section in sections))
    report_identity = {
        "source_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "source_brep_geometry_sha256": representation.geometry_sha256,
        "parent_kind": model.parent_kind.value,
        "parent_authority_revision_id": _parent_revision(model),
        "dimensions_revision_id": dimensions.revision_id,
        "title_block_revision_id": title_block.revision_id,
        "drawing_revision_id": title_block.drawing_revision_id,
        "scale_state": model.scale_state.value,
        "coordinate_unit": model.coordinate_unit,
        "absolute_tolerance": absolute_tolerance,
        "relative_tolerance": relative_tolerance,
        "checks": [item.as_dict() for item in checks],
        "section_revision_ids": section_ids,
    }
    digest = hashlib.sha256(
        json.dumps(report_identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
            "ascii"
        )
    ).hexdigest()
    return DrawingConsistencyReport(
        revision_id=f"drawing-consistency-report:{digest}",
        source_design_model_revision_id=model.revision_id,
        source_brep_revision_id=representation.revision_id,
        source_brep_geometry_sha256=representation.geometry_sha256,
        parent_kind=model.parent_kind.value,
        parent_authority_revision_id=_parent_revision(model),
        dimensions_revision_id=dimensions.revision_id,
        title_block_revision_id=title_block.revision_id,
        drawing_revision_id=title_block.drawing_revision_id,
        scale_state=model.scale_state.value,
        coordinate_unit=model.coordinate_unit,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        checks=tuple(checks),
        section_revision_ids=section_ids,
        limitations=(
            "numerical CAD consistency is software evidence, not physical metrology",
            "comparison tolerance is numeric serialization tolerance, not physical acceptance tolerance",
            "mm_unverified remains unverified against the physical benchmark",
        ),
    )


def _validate_sources(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    dimensions: TechnicalDrawingDimensions,
    title_block: TechnicalDrawingTitleBlock,
    vector_export: TechnicalDrawingVectorExport,
    selected_features: tuple[SelectedFeatureDimensionSource, ...],
    sections: tuple[DrawingSectionViewModel, ...],
) -> None:
    if not isinstance(model, DesignModelRevision):
        raise DrawingValidationError("drawing_validation_design_model_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise DrawingValidationError("drawing_validation_cad_representation_required")
    if not isinstance(dimensions, TechnicalDrawingDimensions):
        raise DrawingValidationError("drawing_validation_dimensions_required")
    if not isinstance(title_block, TechnicalDrawingTitleBlock):
        raise DrawingValidationError("drawing_validation_title_block_required")
    if not isinstance(vector_export, TechnicalDrawingVectorExport):
        raise DrawingValidationError("drawing_validation_vector_export_required")
    if not isinstance(selected_features, tuple) or any(
        not isinstance(source, SelectedFeatureDimensionSource) for source in selected_features
    ):
        raise DrawingValidationError("drawing_validation_feature_sources_invalid")
    if not isinstance(sections, tuple) or any(
        not isinstance(section, DrawingSectionViewModel) for section in sections
    ):
        raise DrawingValidationError("drawing_validation_sections_invalid")
    parent_revision = _parent_revision(model)
    source_tuple = (
        dimensions.source_design_model_revision_id,
        dimensions.source_brep_revision_id,
        dimensions.source_brep_geometry_sha256,
        dimensions.parent_kind,
        dimensions.parent_authority_revision_id,
        dimensions.scale_state,
        dimensions.coordinate_unit,
    )
    expected_tuple = (
        model.revision_id,
        representation.revision_id,
        representation.geometry_sha256,
        model.parent_kind.value,
        parent_revision,
        model.scale_state.value,
        model.coordinate_unit,
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
        or source_tuple != expected_tuple
    ):
        raise DrawingValidationError("drawing_validation_stale_or_mismatched_source")
    if (
        title_block.design_model_revision_id != model.revision_id
        or title_block.cad_representation_revision_id != representation.revision_id
        or title_block.cad_geometry_sha256 != representation.geometry_sha256
        or title_block.parent_kind != model.parent_kind.value
        or title_block.parent_authority_revision_id != parent_revision
        or title_block.scale_state != model.scale_state.value
        or title_block.coordinate_unit != model.coordinate_unit
        or title_block.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or title_block.mold_use_authorized is not False
        or vector_export.source_design_model_revision_id != model.revision_id
        or vector_export.source_brep_revision_id != representation.revision_id
        or vector_export.parent_kind != model.parent_kind.value
        or vector_export.parent_authority_revision_id != parent_revision
        or vector_export.scale_state != model.scale_state.value
        or vector_export.coordinate_unit != model.coordinate_unit
        or vector_export.manifest.get("source_brep_geometry_sha256")
        != representation.geometry_sha256
        or vector_export.manifest.get("dimension_revision_id") != dimensions.revision_id
        or vector_export.manifest.get("title_block_revision_id") != title_block.revision_id
        or vector_export.manifest.get("drawing_revision_id") != title_block.drawing_revision_id
    ):
        raise DrawingValidationError("drawing_validation_title_or_export_revision_mismatch")
    if (
        model.scale_state is ScaleState.RELATIVE and model.coordinate_unit != "reconstruction_units"
    ) or (
        model.scale_state is ScaleState.METRIC_UNVERIFIED
        and model.coordinate_unit != "mm_unverified"
    ):
        raise DrawingValidationError("drawing_validation_source_unit_invalid")
    raw_section_ids = vector_export.manifest.get("section_revision_ids")
    if not isinstance(raw_section_ids, list) or any(
        not isinstance(revision_id, str) for revision_id in raw_section_ids
    ):
        raise DrawingValidationError("drawing_validation_section_manifest_invalid")
    for section in sections:
        if (
            section.scale_state != model.scale_state.value
            or section.coordinate_unit != model.coordinate_unit
            or section.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
            or section.mold_use_authorized is not False
            or section.revision_id not in raw_section_ids
            or any(
                component.source_design_model_revision_id != model.revision_id
                or component.source_brep_revision_id != representation.revision_id
                or component.source_brep_geometry_sha256 != representation.geometry_sha256
                or component.parent_kind != model.parent_kind.value
                or component.parent_authority_revision_id != parent_revision
                for component in section.components
            )
        ):
            raise DrawingValidationError("drawing_validation_section_source_mismatch")
    if sorted(section.revision_id for section in sections) != sorted(raw_section_ids):
        raise DrawingValidationError("drawing_validation_section_manifest_mismatch")


def _validate_dimension_provenance(
    dimension: DimensionAnnotation,
    dimensions: TechnicalDrawingDimensions,
    source: _ExpectedDimension,
    value_status: str,
) -> None:
    if (
        dimension.source_design_model_revision_id != dimensions.source_design_model_revision_id
        or dimension.source_brep_revision_id != source.source_brep_revision_id
        or dimension.source_brep_geometry_sha256 != source.source_geometry_sha256
        or dimension.coordinate_unit != dimensions.coordinate_unit
        or dimension.value_status != value_status
        or dimension.coordinate_frame_id != dimensions.coordinate_frame_id
        or dimension.measurement_axis != source.measurement_axis
        or dimension.typography_baked_into_measurement
        or dimension.feature_kind != source.feature_kind
        or dimension.feature_mapping_revision_id != source.feature_mapping_revision_id
        or dimension.feature_reference_scope != source.feature_reference_scope
        or dimension.placement_revision_id != source.placement_revision_id
    ):
        raise DrawingValidationError("drawing_validation_dimension_source_or_unit_mismatch")


def _add_expected_dimensions(
    output: dict[tuple[str, str, str | None], _ExpectedDimension],
    bounds: tuple[float, float, float, float, float, float],
    *,
    component_reference_id: str,
    feature_id: str | None,
    representation: CadBrepRepresentationRevision,
    feature_kind: str | None,
    feature_mapping_revision_id: str | None = None,
    placement_revision_id: str | None = None,
    unit_label: str,
    value_status: str,
) -> None:
    if len(bounds) != 6 or any(not math.isfinite(value) for value in bounds):
        raise DrawingValidationError("drawing_validation_source_bounds_invalid")
    spans = (bounds[3] - bounds[0], bounds[4] - bounds[1], bounds[5] - bounds[2])
    if any(value <= 0.0 for value in spans):
        raise DrawingValidationError("drawing_validation_source_span_invalid")
    prefix = "OVERALL" if feature_id is None else "FEATURE"
    feature_prefix = (
        f"{feature_kind.upper().replace('-', '_')}_" if feature_kind is not None else ""
    )
    for axis, suffix, value in (
        ("Z", "HEIGHT", spans[2]),
        ("X", "WIDTH_X", spans[0]),
        ("Y", "DEPTH_Y", spans[1]),
    ):
        kind = f"{prefix}_{feature_prefix}{suffix}"
        key = (component_reference_id, kind, feature_id)
        if key in output:
            raise DrawingValidationError("drawing_validation_expected_dimension_duplicate")
        output[key] = _ExpectedDimension(
            kind,
            component_reference_id,
            feature_id,
            representation.revision_id,
            representation.geometry_sha256,
            feature_kind,
            feature_mapping_revision_id,
            "whole_component_solid" if feature_id is not None else None,
            placement_revision_id,
            axis,
            value,
            unit_label,
            value_status,
        )


def _validate_tolerances(absolute: float, relative: float) -> None:
    if (
        not isinstance(absolute, (int, float))
        or isinstance(absolute, bool)
        or not math.isfinite(absolute)
        or absolute < 0.0
        or not isinstance(relative, (int, float))
        or isinstance(relative, bool)
        or not math.isfinite(relative)
        or relative < 0.0
        or absolute + relative == 0.0
    ):
        raise DrawingValidationError("drawing_validation_tolerance_invalid")


def _unit_presentation(scale_state: ScaleState) -> tuple[str, str]:
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        return "mm (UNVERIFIED)", "MM_UNVERIFIED"
    if scale_state is ScaleState.RELATIVE:
        return "reconstruction_units", "RELATIVE_RECONSTRUCTION_UNITS"
    raise DrawingValidationError("drawing_validation_scale_state_invalid")


def _parent_revision(model: DesignModelRevision) -> str:
    revision_id = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if not revision_id:
        raise DrawingValidationError("drawing_validation_parent_authority_missing")
    return revision_id


__all__ = [
    "DEFAULT_ABSOLUTE_TOLERANCE",
    "DEFAULT_RELATIVE_TOLERANCE",
    "DRAWING_VALIDATION_CONTRACT",
    "DrawingConsistencyReport",
    "DrawingDimensionCheck",
    "DrawingValidationError",
    "validate_drawing_dimensions",
]
