from __future__ import annotations

from dataclasses import replace

import pytest
from test_flip_top_exterior import _fit as _fit_flip_top
from test_flip_top_exterior import _fixture as _flip_top_fixture
from test_screw_cap_exterior_fit import _fit as _fit_screw_cap
from test_screw_cap_exterior_fit import _inputs_with_sections as _screw_cap_inputs

from packlab_core.bounding_dimensions import (
    NormalizedMeasurementGeometry,
    measure_bounding_dimensions,
)
from packlab_core.horizontal_section import extract_horizontal_section
from packlab_core.measurement_report import (
    MeasurementReportContext,
    MeasurementReportError,
    build_measurement_report,
    render_measurement_report_markdown,
    serialize_measurement_report,
)
from packlab_core.measurement_uncertainty import (
    MeasurementUncertaintyInput,
    propagate_measurement_uncertainty,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.two_point_measurement import SnapPolicy, measure_two_point_distance


def _fixture():
    geometry = NormalizedMeasurementGeometry(
        "normalized-r1",
        "captured-geometry-r1",
        ((-1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ScaleState.RELATIVE,
        "reconstruction_units",
        None,
        None,
        None,
    )
    dimensions = measure_bounding_dimensions(
        geometry,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )
    section = extract_horizontal_section(
        geometry,
        0.0,
        slab_half_width=0.0,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )
    distance = measure_two_point_distance(
        geometry,
        (-1.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        snap_policy=SnapPolicy(False, 0.0, 0.0, geometry.coordinate_unit),
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )
    uncertainty = propagate_measurement_uncertainty(
        geometry,
        MeasurementUncertaintyInput(
            distance.measurement_id,
            distance.distance,
            distance.coordinate_unit,
            1,
            geometry.source_geometry_id,
            geometry.normalized_geometry_revision,
            geometry.scale_provenance_id,
            geometry.scale_state,
            0.1,
            geometry.coordinate_unit,
        ),
        normalization_scale=None,
    )
    context = MeasurementReportContext(
        "PackLab",
        "project-revision-7",
        "reconstruction-revision-3",
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.scale_state,
        geometry.coordinate_unit,
    )
    return context, (dimensions, section, distance, uncertainty)


def test_mixed_artifacts_are_sorted_and_both_exports_are_deterministic() -> None:
    context, artifacts = _fixture()
    first = build_measurement_report(context, artifacts)
    second = build_measurement_report(context, tuple(reversed(artifacts)))
    assert serialize_measurement_report(first) == serialize_measurement_report(second)
    assert render_measurement_report_markdown(first) == render_measurement_report_markdown(second)
    assert [item["artifact_type"] for item in first.artifacts] == [
        "bounding_dimensions",
        "horizontal_section",
        "measurement_uncertainty",
        "two_point_distance",
    ]


def test_report_carries_units_revisions_and_uncertainty_without_sample_arrays() -> None:
    context, artifacts = _fixture()
    payload = serialize_measurement_report(build_measurement_report(context, artifacts)).decode(
        "utf-8"
    )
    assert '"scale_state":"relative"' in payload
    assert '"coordinate_unit":"reconstruction_units"' in payload
    assert '"source_revision_id":"reconstruction-revision-3"' in payload
    assert '"normalized_geometry_revision":"normalized-r1"' in payload
    assert '"uncertainty_status":"known_relative_coordinate_uncertainty_only"' in payload
    assert '"private_raw_bytes_included":false' in payload
    assert '"ambient_identity_included":false' in payload
    assert '"captured_point":' not in payload
    assert "requested_points" not in payload
    assert "ambient_user" not in payload


def test_stale_mixed_parent_or_duplicate_artifact_ids_are_rejected() -> None:
    context, artifacts = _fixture()
    stale = replace(artifacts[2], normalized_geometry_revision="normalized-r2")
    with pytest.raises(MeasurementReportError, match="mixed_or_stale"):
        build_measurement_report(context, (artifacts[0], stale))
    with pytest.raises(MeasurementReportError, match="duplicate_artifact_id"):
        build_measurement_report(context, (artifacts[2], artifacts[2]))
    with pytest.raises(MeasurementReportError, match="project_id_invalid"):
        replace(context, project_id="owner@example.com")


def test_relative_and_metric_unverified_context_labels_are_checked() -> None:
    context, artifacts = _fixture()
    assert build_measurement_report(context, artifacts).as_dict()["source"]["coordinate_unit"] == (
        "reconstruction_units"
    )
    with pytest.raises(MeasurementReportError, match="relative_scale_mismatch"):
        replace(context, coordinate_unit="mm")

    metric_geometry = NormalizedMeasurementGeometry(
        "normalized-metric-r1",
        "captured-geometry-metric-r1",
        ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
        ScaleState.METRIC_UNVERIFIED,
        "mm_unverified",
        "scale-provenance-r1",
        0.02,
        "mm_per_reconstruction_unit",
    )
    metric_section = extract_horizontal_section(
        metric_geometry,
        0.0,
        slab_half_width=0.0,
        current_geometry_id=metric_geometry.source_geometry_id,
        current_normalized_geometry_revision=metric_geometry.normalized_geometry_revision,
        current_scale_provenance_id=metric_geometry.scale_provenance_id,
    )
    metric_context = MeasurementReportContext(
        "PackLab",
        "project-revision-7",
        "reconstruction-revision-4",
        metric_geometry.source_geometry_id,
        metric_geometry.normalized_geometry_revision,
        metric_geometry.scale_provenance_id,
        metric_geometry.scale_state,
        metric_geometry.coordinate_unit,
    )
    metric_report = build_measurement_report(metric_context, (metric_section,))
    assert metric_report.as_dict()["source"]["scale_state"] == "metric-unverified"
    assert metric_report.as_dict()["source"]["coordinate_unit"] == "mm_unverified"


def test_report_never_claims_certified_or_mold_ready_outputs() -> None:
    context, artifacts = _fixture()
    payload = build_measurement_report(context, artifacts).as_dict()
    limits = payload["authority_and_limitations"]
    assert limits["certified_measurement_claimed"] is False
    assert limits["mold_ready_claimed"] is False
    assert limits["physical_accuracy_claimed"] is False
    assert all(item["certified_claimed"] is False for item in payload["artifacts"])
    markdown = render_measurement_report_markdown(build_measurement_report(context, artifacts))
    assert markdown.endswith("\n")
    assert "(reconstruction_units)" in markdown
    assert "uncertainty:" in markdown


def _modeled_context(scan, model, source_geometry_id, normalized_revision):
    return MeasurementReportContext(
        scan.project_id,
        "project-revision-modeled",
        "reconstruction-revision-modeled",
        source_geometry_id,
        normalized_revision,
        model.scale_provenance_id,
        model.scale_state,
        model.coordinate_unit,
    )


def test_cylindrical_closure_dimensions_are_separate_from_captured_measurements() -> None:
    args = _screw_cap_inputs()
    scan, _, _, _, _, sections = args
    fit = _fit_screw_cap(*args)
    assert fit.model is not None
    context = _modeled_context(
        scan,
        fit.model,
        sections[0].source_geometry_id,
        sections[0].normalized_geometry_revision,
    )

    report = build_measurement_report(
        context,
        sections,
        scan_master=scan,
        design_model=fit.model,
        expected_scan_master_revision_id=scan.revision_id,
        expected_design_model_revision_id=fit.model.revision_id,
    )
    payload = report.as_dict()
    assert len(payload["artifacts"]) == len(sections)
    assert [item["source_kind"] for item in payload["modeled_closure_dimensions"]] == [
        "PARAMETRIC_DESIGN_MODEL"
    ]
    modeled = payload["modeled_closure_dimensions"][0]
    assert modeled["scale_state"] == "metric-unverified"
    assert modeled["coordinate_unit"] == "mm_unverified"
    assert modeled["dimensions"] == [
        {"name": "exterior_diameter", "unit": "mm_unverified", "value": 5.0},
        {"name": "exterior_height", "unit": "mm_unverified", "value": 1.0},
    ]
    assert modeled["captured_fit_support"]["source_kind"] == ("CAPTURED_CROSS_SECTION_MEASUREMENTS")
    assert modeled["captured_fit_support"]["measurement_ids"]["cylindrical_exterior_fit"]
    assert modeled["uncertainty"]["scale_uncertainty_propagated_to_dimensions"] is False
    assert modeled["certified_claimed"] is False
    assert modeled["mold_ready_claimed"] is False
    assert (
        payload["authority_and_limitations"]["modeled_closure_dimensions_are_captured_measurements"]
        is False
    )
    assert serialize_measurement_report(report) == serialize_measurement_report(
        build_measurement_report(
            context,
            tuple(reversed(sections)),
            scan_master=scan,
            design_model=fit.model,
            expected_scan_master_revision_id=scan.revision_id,
            expected_design_model_revision_id=fit.model.revision_id,
        )
    )


def test_flip_top_closure_dimensions_keep_observed_regions_and_deferred_status() -> None:
    args = _flip_top_fixture()
    scan, _, _, _, _, _, _, _, _ = args
    fit = _fit_flip_top(args)
    assert fit.model is not None
    context = _modeled_context(scan, fit.model, "captured-flip-geometry", "normalized-flip-r1")

    report = build_measurement_report(
        context,
        (),
        scan_master=scan,
        design_model=fit.model,
        expected_scan_master_revision_id=scan.revision_id,
        expected_design_model_revision_id=fit.model.revision_id,
    )
    assert report.artifacts == ()
    modeled = report.as_dict()["modeled_closure_dimensions"][0]
    assert modeled["closure_kind"] == "flip_top_exterior"
    assert modeled["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert {item["name"] for item in modeled["dimensions"]} == {
        "base_diameter",
        "base_supported_z_span",
        "lid_envelope_diameter",
        "lid_envelope_supported_z_span",
    }
    assert modeled["captured_fit_support"]["measurement_ids"]["base"]
    assert modeled["captured_fit_support"]["measurement_ids"]["lid_envelope"]
    markdown = render_measurement_report_markdown(report)
    assert "## Parametric closure dimensions" in markdown
    assert "lid_envelope_diameter" in markdown
    assert "mm_unverified" in markdown
    assert report.as_dict()["authority_and_limitations"]["certified_measurement_claimed"] is False


def test_modeled_closure_report_rejects_stale_model_and_scale_parent() -> None:
    args = _screw_cap_inputs()
    scan, _, _, _, _, sections = args
    fit = _fit_screw_cap(*args)
    assert fit.model is not None
    context = _modeled_context(
        scan,
        fit.model,
        sections[0].source_geometry_id,
        sections[0].normalized_geometry_revision,
    )
    with pytest.raises(MeasurementReportError, match="design_model_parent_or_scale_mismatch"):
        build_measurement_report(
            context,
            sections,
            scan_master=scan,
            design_model=fit.model,
            expected_scan_master_revision_id=scan.revision_id,
            expected_design_model_revision_id="stale-design-model",
        )
    with pytest.raises(MeasurementReportError, match="scan_master_stale"):
        build_measurement_report(
            context,
            sections,
            scan_master=scan,
            design_model=fit.model,
            expected_scan_master_revision_id="stale-scan-master",
            expected_design_model_revision_id=fit.model.revision_id,
        )
    wrong_scale_context = replace(
        context,
        scale_state=ScaleState.RELATIVE,
        scale_provenance_id=None,
        coordinate_unit="reconstruction_units",
    )
    with pytest.raises(MeasurementReportError, match="design_model_parent_or_scale_mismatch"):
        build_measurement_report(
            wrong_scale_context,
            (),
            scan_master=scan,
            design_model=fit.model,
            expected_scan_master_revision_id=scan.revision_id,
            expected_design_model_revision_id=fit.model.revision_id,
        )
