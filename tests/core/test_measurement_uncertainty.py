from __future__ import annotations

import math
from dataclasses import replace

import pytest

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.measurement_uncertainty import (
    MeasurementUncertaintyError,
    MeasurementUncertaintyInput,
    NormalizationScaleEvidence,
    propagate_measurement_uncertainty,
    serialize_measurement_uncertainty,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.two_point_measurement import SnapPolicy, measure_two_point_distance


def _relative_geometry():
    return NormalizedMeasurementGeometry(
        "normalized-relative-r1",
        "geometry-r1",
        ((0.0, 0.0, 0.0), (3.0, 4.0, 0.0)),
        ScaleState.RELATIVE,
        "reconstruction_units",
        None,
        None,
        None,
    )


def _unverified_geometry():
    return NormalizedMeasurementGeometry(
        "normalized-metric-r1",
        "geometry-metric-r1",
        ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0)),
        ScaleState.METRIC_UNVERIFIED,
        "mm_unverified",
        "scale-r1",
        0.1,
        "mm_per_reconstruction_unit",
    )


def _scale_evidence(geometry, *, factor=2.0, sigma=0.1, unit="mm_per_reconstruction_unit"):
    return NormalizationScaleEvidence(
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.scale_state,
        factor,
        sigma,
        unit,
    )


def _measurement(
    geometry, measurement_id, value, unit, power=1, *, standard=None, standard_unit=None
):
    return MeasurementUncertaintyInput(
        measurement_id,
        value,
        unit,
        power,
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.scale_state,
        standard,
        standard_unit,
    )


def test_known_scale_and_measurement_uncertainties_combine_by_rss() -> None:
    geometry = _unverified_geometry()
    measurement = _measurement(
        geometry,
        "two-point-distance:test-r1",
        10.0,
        "mm_unverified",
        standard=0.3,
        standard_unit="mm_unverified",
    )
    report = propagate_measurement_uncertainty(
        geometry,
        measurement,
        normalization_scale=_scale_evidence(geometry),
    )
    assert report.components[0]["value"] == pytest.approx(0.5)
    assert report.propagated_standard_uncertainty == pytest.approx(math.sqrt(0.5**2 + 0.3**2))
    assert report.uncertainty_status == "known_propagated_components_only"
    assert report.estimate_display == "10.00 mm_unverified"
    assert report.uncertainty_display == "± 0.58 mm_unverified"


def test_uncertainty_power_propagation_links_volume_measurement() -> None:
    geometry = _unverified_geometry()
    measurement = _measurement(
        geometry,
        "capacity-estimate:test-r1",
        24.0,
        "mm_unverified^3",
        power=3,
    )
    report = propagate_measurement_uncertainty(
        geometry,
        measurement,
        normalization_scale=_scale_evidence(geometry),
    )
    assert report.propagated_standard_uncertainty == pytest.approx(3.6)
    assert report.measurement_id == measurement.measurement_id
    assert report.as_dict()["measurement_link"]["normalized_geometry_revision"] == (
        geometry.normalized_geometry_revision
    )


def test_missing_scale_uncertainty_and_relative_geometry_remain_explicitly_unknown() -> None:
    metric_geometry = _unverified_geometry()
    metric_measurement = _measurement(
        metric_geometry, "measurement-missing-scale", 10.0, "mm_unverified"
    )
    missing = propagate_measurement_uncertainty(
        metric_geometry,
        metric_measurement,
        normalization_scale=None,
    )
    assert missing.propagated_standard_uncertainty is None
    assert missing.uncertainty_status == "unknown_normalization_scale_evidence_missing"
    assert missing.uncertainty_display == "unknown"

    relative_geometry = _relative_geometry()
    relative_measurement = _measurement(
        relative_geometry, "relative-measurement-r1", 5.0, "reconstruction_units"
    )
    relative = propagate_measurement_uncertainty(
        relative_geometry,
        relative_measurement,
        normalization_scale=None,
    )
    assert relative.propagated_standard_uncertainty is None
    assert relative.uncertainty_status == "unknown_relative_scale_not_physical"


def test_incompatible_units_and_stale_measurement_provenance_are_rejected() -> None:
    geometry = _unverified_geometry()
    with pytest.raises(MeasurementUncertaintyError, match="unit_incompatible"):
        _measurement(
            geometry,
            "bad-unit-r1",
            10.0,
            "mm_unverified",
            standard=0.1,
            standard_unit="reconstruction_units",
        )
    measurement = _measurement(geometry, "stale-measurement-r1", 10.0, "mm_unverified")
    with pytest.raises(MeasurementUncertaintyError, match="unit_invalid"):
        _scale_evidence(geometry, unit="mm")
    with pytest.raises(MeasurementUncertaintyError, match="provenance_link_mismatch"):
        propagate_measurement_uncertainty(
            geometry,
            replace(measurement, normalized_geometry_revision="normalized-r2"),
            normalization_scale=_scale_evidence(geometry),
        )


def test_deterministic_serialization_and_confidence_is_not_physical_tolerance() -> None:
    geometry = _unverified_geometry()
    measurement = _measurement(
        geometry,
        "measurement-deterministic-r1",
        10.123456,
        "mm_unverified",
        standard=0.004,
        standard_unit="mm_unverified",
    )
    kwargs = {
        "normalization_scale": _scale_evidence(geometry),
        "confidence_score": 0.91,
        "confidence_interpretation": "dimensionless calibration consistency score; not physical tolerance",
    }
    first = propagate_measurement_uncertainty(geometry, measurement, **kwargs)
    second = propagate_measurement_uncertainty(geometry, measurement, **kwargs)
    assert first.report_id == second.report_id
    assert serialize_measurement_uncertainty(first) == serialize_measurement_uncertainty(second)
    assert first.as_dict()["confidence"]["converted_to_physical_tolerance"] is False
    assert first.as_dict()["presentation"]["false_precision_claimed"] is False
    assert first.estimate_display == "10.12 mm_unverified"


def test_two_point_measurement_identifier_is_preserved_as_link() -> None:
    geometry = _relative_geometry()
    distance = measure_two_point_distance(
        geometry,
        (0.0, 0.0, 0.0),
        (3.0, 4.0, 0.0),
        snap_policy=SnapPolicy(False, 0.0, 0.0, geometry.coordinate_unit),
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )
    measurement = _measurement(
        geometry,
        distance.measurement_id,
        distance.distance,
        distance.coordinate_unit,
        standard=0.1,
        standard_unit=distance.coordinate_unit,
    )
    report = propagate_measurement_uncertainty(
        geometry,
        measurement,
        normalization_scale=None,
    )
    assert report.measurement_id == distance.measurement_id
    assert report.propagated_standard_uncertainty == pytest.approx(0.1)
    assert report.uncertainty_status == "known_relative_coordinate_uncertainty_only"


def test_confidence_cannot_be_described_as_physical_tolerance() -> None:
    geometry = _unverified_geometry()
    measurement = _measurement(geometry, "measurement-confidence", 10.0, "mm_unverified")
    with pytest.raises(MeasurementUncertaintyError, match="not_physical_tolerance"):
        propagate_measurement_uncertainty(
            geometry,
            measurement,
            normalization_scale=_scale_evidence(geometry),
            confidence_score=0.9,
            confidence_interpretation="physical tolerance",
        )
