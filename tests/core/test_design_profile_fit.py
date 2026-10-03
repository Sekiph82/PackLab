from __future__ import annotations

import math
from dataclasses import replace

import pytest

from packlab_core.cross_section_overlay import CanonicalAxis
from packlab_core.design_profile_fit import (
    DesignProfileFitError,
    ProfileFitStatus,
    ProfileTransitionAnchor,
    ProfileTransitionKind,
    fit_design_profile,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.scan_master_profile import extract_scan_master_vertical_profile

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
BAND_COUNT = 16
ANCHORS = (
    ProfileTransitionAnchor(ProfileTransitionKind.BASE, 3),
    ProfileTransitionAnchor(ProfileTransitionKind.SHOULDER, 12),
)


def _scan_master(
    levels: tuple[float, ...] = tuple(i / 2 for i in range(31)), *, outlier: bool = False
) -> ScanMasterRevision:
    angular_count = 64
    vertices: list[tuple[float, float, float]] = []
    for height in levels:
        radius = 2.0 + 0.035 * math.sin(height * 0.6)
        if height >= 2.5:
            radius += 0.35
        if height >= 11.0:
            radius -= 0.25
        for index in range(angular_count):
            angle = math.tau * index / angular_count
            angular_noise = 0.008 * math.sin(index * 2.31 + height)
            radial = radius + angular_noise
            vertices.append((radial * math.cos(angle), radial * math.sin(angle), height))
    if outlier:
        vertices[10 * angular_count] = (12.0, 0.0, 5.0)
    faces: list[tuple[int, int, int]] = []
    for ring in range(len(levels) - 1):
        for index in range(angular_count):
            following = (index + 1) % angular_count
            first = ring * angular_count + index
            second = ring * angular_count + following
            third = (ring + 1) * angular_count + following
            fourth = (ring + 1) * angular_count + index
            faces.extend(((first, second, third), (first, third, fourth)))
    mesh = TriangleMeshData(tuple(vertices), tuple(faces))
    revision = "scan-master-profile-fit-r1"
    return ScanMasterRevision(
        revision,
        PROJECT,
        mesh,
        {
            "scan_master_revision_id": revision,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(mesh),
            "reconstruction_revision_id": "reconstruction-r1",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-r1",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )


def _profile(levels: tuple[float, ...] = tuple(i / 2 for i in range(31)), *, outlier: bool = False):
    scan = _scan_master(levels, outlier=outlier)
    profile = extract_scan_master_vertical_profile(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        axis=CanonicalAxis.Z,
        plane_origin=(0.0, 0.0, 0.0),
        front_direction=(1.0, 0.0, 0.0),
        lateral_tolerance=0.3,
        band_count=BAND_COUNT,
        minimum_band_samples=3,
        outlier_mad_multiplier=4.5,
        actor_id="operator-1",
        reason="Create fit test evidence.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    return scan, profile


def _fit(
    profile,
    *,
    strength: float = 0.35,
    maximum_adjustment: float = 0.25,
    anchors=ANCHORS,
):
    return fit_design_profile(
        profile,
        transition_anchors=anchors,
        smoothing_strength=strength,
        window_radius=2,
        maximum_relative_adjustment=maximum_adjustment,
    )


def test_noisy_body_fit_is_deterministic_residual_recorded_and_parent_bound() -> None:
    scan, source = _profile(outlier=True)
    fitted = _fit(source)
    assert fitted.status is ProfileFitStatus.FITTED
    assert fitted == _fit(source)
    assert fitted.profile is not None
    assert len(fitted.residuals) == len(source.bands) == BAND_COUNT
    assert any(item.residual != 0 for item in fitted.residuals)
    assert fitted.source_profile_id == source.profile_id
    assert fitted.scan_master_revision_id == scan.revision_id
    assert fitted.scan_master_geometry_sha256 == mesh_sha256(scan.mesh)
    assert fitted.parent_binding == source.parent_binding
    assert fitted.parent_binding.fitted_to_scan_master_revision_id == scan.revision_id
    assert len(source.outliers) == 1
    assert fitted.rejected_source_vertex_indices == (source.outliers[0].source_vertex_index,)
    assert fitted.profile.scale_state is ScaleState.METRIC_UNVERIFIED
    assert fitted.profile.coordinate_unit == "mm_unverified"
    assert fitted.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert fitted.mold_use_authorized is False
    assert fitted.as_dict()["scan_master_replaced"] is False


def test_base_and_shoulder_neighborhoods_are_preserved_exactly() -> None:
    _, source = _profile()
    fitted = _fit(source)
    assert fitted.profile is not None
    for anchor in ANCHORS:
        for index in (anchor.band_index - 1, anchor.band_index, anchor.band_index + 1):
            residual = fitted.residuals[index]
            assert residual.band_index == index
            assert residual.fitted_radius == residual.observed_radius
            assert residual.residual == 0.0


def test_regularization_upper_boundary_is_inclusive_and_overflow_rejected() -> None:
    _, source = _profile()
    assert _fit(source, strength=0.5).status is ProfileFitStatus.FITTED
    with pytest.raises(DesignProfileFitError, match="smoothing_strength_out_of_range"):
        _fit(source, strength=math.nextafter(0.5, math.inf))


def test_coverage_gaps_remain_review_required_without_interpolation() -> None:
    _, source = _profile((0.0, 0.5, 1.0, 1.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0))
    assert source.coverage_gaps
    available = tuple(item.band_index for item in source.bands)
    anchors = (
        ProfileTransitionAnchor(ProfileTransitionKind.BASE, available[0]),
        ProfileTransitionAnchor(ProfileTransitionKind.SHOULDER, available[-1]),
    )
    result = _fit(source, anchors=anchors)
    assert result.status is ProfileFitStatus.REVIEW_REQUIRED
    assert result.profile is None
    assert "source_profile_has_coverage_gaps" in result.uncertainty_codes
    assert result.as_dict()["missing_gaps_interpolated"] is False


def test_excessive_adjustment_stays_review_required_and_rejected_source_is_retained() -> None:
    _, source = _profile()
    result = _fit(source, maximum_adjustment=0.0001)
    assert result.status is ProfileFitStatus.REVIEW_REQUIRED
    assert result.profile is None
    assert "smoothing_adjustment_exceeds_policy" in result.uncertainty_codes


def test_parent_digest_mismatch_and_source_authority_escalation_reject() -> None:
    _, source = _profile()
    mismatched = replace(source, scan_master_geometry_sha256="0" * 64)
    with pytest.raises(DesignProfileFitError, match="source_profile_authority_or_parent_invalid"):
        _fit(mismatched)
    promoted = replace(source, physical_accuracy_validation_status="VALIDATED")
    with pytest.raises(DesignProfileFitError, match="source_profile_authority_or_parent_invalid"):
        _fit(promoted)
