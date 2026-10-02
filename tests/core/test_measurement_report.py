from __future__ import annotations

from dataclasses import replace

import pytest

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
