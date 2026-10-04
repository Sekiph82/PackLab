from __future__ import annotations

from dataclasses import replace

import pytest
from test_cad_brep import _inputs
from test_technical_drawing_dimensions import _brep, _feature_model

from packlab_core.cad_adapter import probe_cad_runtime
from packlab_core.cad_brep import CadBrepRepresentationRevision, revolve_design_model_to_brep
from packlab_core.reconstruction import ScaleState
from packlab_core.technical_drawing import generate_orthographic_views
from packlab_core.technical_drawing_dimensions import (
    SelectedFeatureDimensionSource,
    TechnicalDrawingDimensions,
    build_drawing_dimensions,
)
from packlab_core.technical_drawing_export import (
    TechnicalDrawingVectorExport,
    export_technical_drawing_vectors,
)
from packlab_core.technical_drawing_sections import (
    DrawingSectionSource,
    DrawingSectionViewModel,
    generate_section_view,
)
from packlab_core.technical_drawing_title_block import (
    TechnicalDrawingTitleBlock,
    build_technical_drawing_title_block,
)
from packlab_core.technical_drawing_validation import (
    DrawingValidationError,
    validate_drawing_dimensions,
)

FRAME = "drawing-validation-frame:v1"
IDENTITY = (
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


def _case(
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED,
    *,
    selected_features: tuple[SelectedFeatureDimensionSource, ...] = (),
) -> tuple[
    object,
    CadBrepRepresentationRevision,
    TechnicalDrawingDimensions,
    TechnicalDrawingTitleBlock,
    TechnicalDrawingVectorExport,
    tuple[DrawingSectionViewModel, ...],
]:
    model, profile, operation = _inputs(scale_state)
    representation = revolve_design_model_to_brep(model, profile, operation)
    dimensions = build_drawing_dimensions(
        model,
        representation,
        coordinate_frame_id=FRAME,
        selected_features=selected_features,
    )
    views = generate_orthographic_views(model, representation)
    sections = (
        generate_section_view(
            (
                DrawingSectionSource(
                    "overall",
                    FRAME,
                    "placement:overall:v1",
                    IDENTITY,
                    model,
                    representation,
                ),
            ),
            plane_axis="Z",
            plane_offset=50.0,
        ),
    )
    title = build_technical_drawing_title_block(
        model,
        representation,
        probe_cad_runtime(),
        generated_view_ids=("FRONT", "SIDE", "TOP"),
    )
    vector = export_technical_drawing_vectors(views, sections, dimensions, title)
    return model, representation, dimensions, title, vector, sections


def _validate(case):
    model, representation, dimensions, title, vector, sections = case
    return validate_drawing_dimensions(
        model,
        representation,
        dimensions,
        title,
        vector,
        sections=sections,
    )


def test_known_cad_dimensions_validate_with_explicit_software_tolerance() -> None:
    case = _case()
    report = _validate(case)
    values = {check.dimension_kind: check.expected_value for check in report.checks}

    assert report.passed is True
    assert values["OVERALL_HEIGHT"] == pytest.approx(100.0)
    assert values["OVERALL_WIDTH_X"] == pytest.approx(10.0)
    assert values["OVERALL_DEPTH_Y"] == pytest.approx(10.0)
    assert report.absolute_tolerance == 1e-8
    assert report.relative_tolerance == 1e-10
    assert report.as_dict()["comparison_tolerance"]["is_physical_tolerance"] is False
    assert report.as_dict()["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert report.as_dict()["drawing"]["section_revision_ids"] == [case[5][0].revision_id]
    assert all(check.passed for check in report.checks)


def test_tampered_value_fails_and_unit_label_mismatch_is_reported() -> None:
    model, representation, dimensions, title, vector, sections = _case()
    first = dimensions.dimensions[0]
    tampered = replace(
        dimensions,
        dimensions=(replace(first, value=first.value + 0.25), *dimensions.dimensions[1:]),
    )
    report = validate_drawing_dimensions(
        model, representation, tampered, title, vector, sections=sections
    )
    assert report.passed is False
    assert (
        next(
            check for check in report.checks if check.dimension_id == first.dimension_id
        ).failure_code
        == "drawing_dimension_value_mismatch"
    )

    relabeled = replace(
        dimensions, dimensions=(replace(first, unit_label="mm"), *dimensions.dimensions[1:])
    )
    unit_report = validate_drawing_dimensions(
        model, representation, relabeled, title, vector, sections=sections
    )
    assert unit_report.passed is False
    assert (
        next(
            check for check in unit_report.checks if check.dimension_id == first.dimension_id
        ).failure_code
        == "drawing_dimension_unit_label_mismatch"
    )


@pytest.mark.parametrize("scale_state", [ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED])
def test_relative_and_mm_unverified_unit_labels_are_preserved(scale_state: ScaleState) -> None:
    report = _validate(_case(scale_state))
    assert report.passed is True
    assert report.coordinate_unit == (
        "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    )
    assert all(
        check.expected_unit_label
        == ("reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm (UNVERIFIED)")
        for check in report.checks
    )


def test_stale_model_brep_and_title_block_revision_references_are_rejected() -> None:
    case = _case()
    model, representation, dimensions, title, vector, sections = case
    other_model, other_profile, other_operation = _inputs(ScaleState.RELATIVE)
    other_representation = revolve_design_model_to_brep(other_model, other_profile, other_operation)

    with pytest.raises(DrawingValidationError, match="stale_or_mismatched_source"):
        validate_drawing_dimensions(
            other_model, other_representation, dimensions, title, vector, sections=sections
        )
    with pytest.raises(DrawingValidationError, match="stale_or_mismatched_source"):
        validate_drawing_dimensions(
            model, other_representation, dimensions, title, vector, sections=sections
        )

    stale_manifest = dict(vector.manifest)
    stale_manifest["title_block_revision_id"] = "drawing-title-block:stale"
    stale_vector = replace(vector, manifest=stale_manifest)
    with pytest.raises(DrawingValidationError, match="title_or_export_revision_mismatch"):
        validate_drawing_dimensions(
            model, representation, dimensions, title, stale_vector, sections=sections
        )


def test_selected_whole_solid_feature_dimensions_are_recomputed() -> None:
    model = _feature_model()
    body = _brep(model, radius=7.0, height=30.0)
    neck = _brep(model, radius=3.0, height=15.0)
    selected = (
        SelectedFeatureDimensionSource(
            component_reference_id="neck-instance-2",
            placement_revision_id="placement:neck-instance-2:v1",
            feature_id=model.features[0].feature_id,
            representation=neck,
            placement_matrix=IDENTITY,
        ),
    )
    dimensions = build_drawing_dimensions(
        model, body, coordinate_frame_id=FRAME, selected_features=selected
    )
    views = generate_orthographic_views(model, body)
    title = build_technical_drawing_title_block(
        model,
        body,
        probe_cad_runtime(),
        generated_view_ids=("FRONT", "SIDE", "TOP"),
    )
    vector = export_technical_drawing_vectors(views, (), dimensions, title)
    report = validate_drawing_dimensions(
        model, body, dimensions, title, vector, selected_features=selected
    )
    by_kind = {check.dimension_kind: check.expected_value for check in report.checks}

    assert report.passed is True
    assert by_kind["FEATURE_NECK_HEIGHT"] == pytest.approx(15.0)
    assert by_kind["FEATURE_NECK_WIDTH_X"] == pytest.approx(6.0)
    assert by_kind["FEATURE_NECK_DEPTH_Y"] == pytest.approx(6.0)


def test_validation_report_is_deterministic_and_rejects_zero_tolerance() -> None:
    case = _case(ScaleState.RELATIVE)
    first = _validate(case)
    second = _validate(case)

    assert first.revision_id == second.revision_id
    assert first.as_dict() == second.as_dict()
    with pytest.raises(DrawingValidationError, match="tolerance_invalid"):
        model, representation, dimensions, title, vector, sections = case
        validate_drawing_dimensions(
            model,
            representation,
            dimensions,
            title,
            vector,
            sections=sections,
            absolute_tolerance=0.0,
            relative_tolerance=0.0,
        )
