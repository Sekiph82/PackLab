from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from packlab_core.calibration import (
    AssociatedMarkerObservation,
    PhysicalMarkerReference,
    ReconstructedMarkerGeometry,
    ReconstructionScaleError,
    ReconstructionScaleObservation,
    estimate_reconstruction_scale,
)

RECONSTRUCTION_REVISION = "reconstruction-r8"
CAMERA_REVISION = "camera-solution-r7"


def _sample(marker_id: int, *, side_units: float = 100.0) -> ReconstructionScaleObservation:
    source_id = f"raw/images/synthetic-{marker_id:02d}.png"
    digest = hashlib.sha256(source_id.encode()).hexdigest()
    association = AssociatedMarkerObservation(
        marker_id=marker_id,
        corners_px=((0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)),
        quality={"quality_label": "synthetic_geometry", "quality_score": 1.0},
        detector_provenance={"generator": "synthetic_test_fixture_v1"},
        source_image_asset_id=source_id,
        source_digest=digest,
        image_width=640,
        image_height=480,
        camera_id=f"camera-{marker_id:02d}",
        camera_solution_revision=CAMERA_REVISION,
    )
    evidence_digest = hashlib.sha256(f"synthetic-reference-{marker_id}".encode()).hexdigest()
    reference = PhysicalMarkerReference(
        marker_id=marker_id,
        reference_id=f"synthetic-reference-{marker_id}",
        reference_digest=evidence_digest,
        side_length=40.0,
        unit="mm",
        uncertainty_mm=0.1,
        evidence_class="synthetic_test_fixture",
    )
    geometry = ReconstructedMarkerGeometry(
        observation=association,
        reconstruction_revision=RECONSTRUCTION_REVISION,
        coordinate_unit="reconstruction_units",
        corners_reconstruction_units=(
            (0.0, 0.0, 5.0),
            (side_units, 0.0, 5.0),
            (side_units, side_units, 5.0),
            (0.0, side_units, 5.0),
        ),
        corner_uncertainty_units=0.05,
    )
    return ReconstructionScaleObservation(reference, geometry)


def _estimate(samples: tuple[ReconstructionScaleObservation, ...]):
    return estimate_reconstruction_scale(
        samples,
        reconstruction_revision=RECONSTRUCTION_REVISION,
        camera_solution_revision=CAMERA_REVISION,
    )


def test_exact_synthetic_scale_is_recovered_without_metric_promotion() -> None:
    result = _estimate((_sample(1), _sample(2)))
    assert result.status == "estimated"
    assert result.reconstruction_units_to_mm == pytest.approx(0.4)
    assert result.metric_state == "METRIC_UNVERIFIED"
    assert result.provenance["input_geometry_unit"] == "reconstruction_units"
    assert result.provenance["output_unit"] == "mm_per_reconstruction_unit"
    assert result.provenance["evidence_classes"] == "synthetic_test_fixture"


def test_noisy_geometry_records_uncertainty_and_per_observation_residuals() -> None:
    result = _estimate((_sample(1, side_units=100.0), _sample(2, side_units=100.4)))
    assert result.status == "estimated"
    assert result.reconstruction_units_to_mm == pytest.approx(0.4, abs=0.002)
    assert result.uncertainty_mm_per_reconstruction_unit is not None
    assert result.uncertainty_mm_per_reconstruction_unit > 0.0
    assert len(result.residuals) == 2
    assert all("relative_residual" in item for item in result.residuals)


def test_versioned_outlier_policy_rejects_inconsistent_observation() -> None:
    result = _estimate((_sample(1), _sample(2, side_units=100.2), _sample(3, side_units=70.0)))
    assert result.status == "estimated"
    assert len(result.observations_used) == 2
    assert any(item.endswith(":outlier_relative_residual") for item in result.observations_rejected)
    assert result.provenance["outlier_policy_version"] == "median_relative_residual_5pct_v1"


def test_insufficient_evidence_returns_no_usable_scale() -> None:
    result = _estimate((_sample(1),))
    assert result.status == "rejected"
    assert result.reconstruction_units_to_mm is None
    assert result.errors == ("insufficient_camera_bound_scale_observations",)


def test_unit_and_revision_mismatches_fail_closed() -> None:
    sample = _sample(1)
    with pytest.raises(ReconstructionScaleError, match="unit_mismatch"):
        ReconstructedMarkerGeometry(
            sample.reconstructed_geometry.observation,
            RECONSTRUCTION_REVISION,
            "image_pixels",
            sample.reconstructed_geometry.corners_reconstruction_units,
            0.05,
        )

    stale_geometry = ReconstructedMarkerGeometry(
        sample.reconstructed_geometry.observation,
        "reconstruction-r7",
        "reconstruction_units",
        sample.reconstructed_geometry.corners_reconstruction_units,
        0.05,
    )
    stale_reconstruction = ReconstructionScaleObservation(sample.physical_reference, stale_geometry)
    stale_camera_observation = replace(
        sample.reconstructed_geometry.observation,
        camera_solution_revision="camera-solution-old",
    )
    stale_camera_geometry = ReconstructedMarkerGeometry(
        stale_camera_observation,
        RECONSTRUCTION_REVISION,
        "reconstruction_units",
        sample.reconstructed_geometry.corners_reconstruction_units,
        0.05,
    )
    result = _estimate(
        (
            stale_reconstruction,
            ReconstructionScaleObservation(sample.physical_reference, stale_camera_geometry),
        )
    )
    assert result.status == "rejected"
    assert result.reconstruction_units_to_mm is None
    assert any(
        item.endswith(":reconstruction_revision_mismatch") for item in result.observations_rejected
    )
    assert any(
        item.endswith(":camera_solution_revision_mismatch") for item in result.observations_rejected
    )


def test_order_does_not_change_scale_or_provenance() -> None:
    first = _estimate((_sample(1), _sample(2, side_units=100.1), _sample(3, side_units=99.9)))
    second = _estimate((_sample(3, side_units=99.9), _sample(1), _sample(2, side_units=100.1)))
    assert first.as_dict() == second.as_dict()


def test_invalid_reference_unit_is_rejected() -> None:
    with pytest.raises(ReconstructionScaleError, match="unit_must_be_mm"):
        PhysicalMarkerReference(
            marker_id=1,
            reference_id="reference-1",
            reference_digest=hashlib.sha256(b"reference").hexdigest(),
            side_length=40.0,
            unit="cm",
            uncertainty_mm=0.1,
            evidence_class="synthetic_test_fixture",
        )
