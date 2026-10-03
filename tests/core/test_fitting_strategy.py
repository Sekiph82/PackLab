from __future__ import annotations

import math
from dataclasses import replace

import pytest

from packlab_core.cross_section_measurement import CrossSectionMeasurement
from packlab_core.fitting_strategy import (
    FittingStrategy,
    FittingStrategyError,
    FittingStrategyPolicy,
    recommend_fitting_strategy,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.vertical_profile import VerticalProfile, VerticalProfileSample

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"


def _ring_mesh(*, profile: str, angular_count: int = 48) -> TriangleMeshData:
    vertices: list[tuple[float, float, float]] = []
    for z in (0.0, 5.0, 10.0):
        for index in range(angular_count):
            theta = 2 * math.pi * index / angular_count
            if profile == "circle":
                radius_x = radius_y = 2.0
                factor = 1.0
            elif profile == "ellipse":
                radius_x, radius_y = 2.0, 1.0
                factor = 1.0
            else:
                radius_x = radius_y = 2.0
                factor = 1.0 + 0.2 * math.cos(theta)
            vertices.append((radius_x * factor * math.cos(theta), radius_y * math.sin(theta), z))
    faces: list[tuple[int, int, int]] = []
    for lower_ring in range(2):
        for index in range(angular_count):
            following = (index + 1) % angular_count
            a = lower_ring * angular_count + index
            b = lower_ring * angular_count + following
            c = (lower_ring + 1) * angular_count + following
            d = (lower_ring + 1) * angular_count + index
            faces.extend(((a, b, c), (a, c, d)))
    return TriangleMeshData(tuple(vertices), tuple(faces))


def _scan_master(profile: str = "circle") -> ScanMasterRevision:
    mesh = _ring_mesh(profile=profile)
    return ScanMasterRevision(
        f"scan-master-{profile}-r1",
        PROJECT,
        mesh,
        {
            "scan_master_revision_id": f"scan-master-{profile}-r1",
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(mesh),
            "reconstruction_revision_id": "reconstruction-r1",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-r1",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "parent_object_geometry_revision_id": "captured-object-r1",
            "alignment_transform": {"transform": {"transform_id": "normalized-r1"}},
        },
    )


def _recommend(scan: ScanMasterRevision, policy: FittingStrategyPolicy | None = None):
    return recommend_fitting_strategy(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        actor_id="operator-1",
        reason="Evaluate parametric fit strategy.",
        created_at_utc="2026-10-03T14:00:00Z",
        policy=policy or FittingStrategyPolicy(),
    )


def test_synthetic_rotational_body_recommends_revolve_deterministically() -> None:
    scan = _scan_master("circle")
    first = _recommend(scan)
    second = _recommend(scan)
    assert first == second
    assert first.recommendation_id == second.recommendation_id
    assert first.strategy is FittingStrategy.AXISYMMETRIC_REVOLVE
    assert first.principal_axis.value == "z"
    assert len(first.section_evidence) == 5
    assert first.scan_master_geometry_sha256 == mesh_sha256(scan.mesh)
    assert first.parent_binding.fitted_to_scan_master_revision_id == scan.revision_id
    as_dict = first.as_dict()
    assert as_dict["coordinate_unit"] == "mm_unverified"
    assert as_dict["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert as_dict["mold_use_authorized"] is False
    assert as_dict["is_design_model_fit"] is False
    assert as_dict["symmetry_is_physical_truth"] is False


def test_non_circular_bilateral_body_recommends_symmetric_loft() -> None:
    recommendation = _recommend(_scan_master("ellipse"))
    assert recommendation.strategy is FittingStrategy.SYMMETRIC_STACKED_SECTION_LOFT
    assert all(
        item.radial_coefficient_of_variation > recommendation.policy.maximum_axisymmetric_radial_cv
        for item in recommendation.section_evidence
    )
    assert all(
        item.left_right_reflection_error <= recommendation.policy.maximum_bilateral_reflection_error
        and item.front_back_reflection_error
        <= recommendation.policy.maximum_bilateral_reflection_error
        for item in recommendation.section_evidence
    )


def test_asymmetric_evidence_requires_review_and_boundary_is_inclusive() -> None:
    asymmetric = _recommend(_scan_master("asymmetric"))
    assert asymmetric.strategy is FittingStrategy.REVIEW_REQUIRED
    assert "cross_sections_not_sufficiently_symmetric" in asymmetric.uncertainty_codes

    exact_axis_threshold = _recommend(
        _scan_master("circle"),
        FittingStrategyPolicy(minimum_axis_elongation_ratio=2.5),
    )
    above_axis_threshold = _recommend(
        _scan_master("circle"),
        FittingStrategyPolicy(minimum_axis_elongation_ratio=math.nextafter(2.5, math.inf)),
    )
    assert exact_axis_threshold.strategy is FittingStrategy.AXISYMMETRIC_REVOLVE
    assert above_axis_threshold.strategy is FittingStrategy.REVIEW_REQUIRED

    baseline = _recommend(_scan_master("circle"))
    radial_limit = max(item.radial_coefficient_of_variation for item in baseline.section_evidence)
    exact_radial_threshold = _recommend(
        _scan_master("circle"),
        FittingStrategyPolicy(maximum_axisymmetric_radial_cv=radial_limit),
    )
    below_radial_threshold = _recommend(
        _scan_master("circle"),
        FittingStrategyPolicy(maximum_axisymmetric_radial_cv=math.nextafter(radial_limit, 0.0)),
    )
    assert exact_radial_threshold.strategy is FittingStrategy.AXISYMMETRIC_REVOLVE
    assert below_radial_threshold.strategy is FittingStrategy.SYMMETRIC_STACKED_SECTION_LOFT


def test_stale_parent_and_invalid_scan_master_authority_reject() -> None:
    scan = _scan_master()
    with pytest.raises(FittingStrategyError, match="selected_scan_master_parent_stale"):
        recommend_fitting_strategy(
            scan,
            expected_scan_master_revision_id="scan-master-newer-r2",
            actor_id="operator-1",
            reason="Stale binding test.",
            created_at_utc="2026-10-03T14:00:00Z",
        )
    invalid = ScanMasterRevision(
        scan.revision_id,
        scan.project_id,
        scan.mesh,
        {
            "scan_master_revision_id": scan.revision_id,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": "0" * 64,
            "reconstruction_revision_id": "reconstruction-r1",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-r1",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    with pytest.raises(FittingStrategyError, match="scan_master_authority_or_digest_invalid"):
        _recommend(invalid)


def test_m09_profile_and_cross_section_evidence_must_match_scan_master_ancestry() -> None:
    scan = _scan_master()
    profile = VerticalProfile(
        "vertical-profile-r1",
        "captured-object-r1",
        "normalized-r1",
        "scale-r1",
        ScaleState.METRIC_UNVERIFIED,
        "mm_unverified",
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        0.1,
        (-2.0, 2.0),
        (0.0, 10.0),
        (
            VerticalProfileSample(0, (0.0, 0.0, 0.0), -1.0, 0.0, 0.0),
            VerticalProfileSample(1, (0.0, 0.0, 10.0), 1.0, 10.0, 0.0),
        ),
    )
    measurement = CrossSectionMeasurement(
        "cross-section-r1",
        "selection-r1",
        "captured-object-r1",
        "normalized-r1",
        "scale-r1",
        ScaleState.METRIC_UNVERIFIED,
        "mm_unverified",
        "pca_covariance_ellipse_v1",
        (0.0, 0.0, 5.0),
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        2.0,
        2.0,
        4.0,
        4.0,
        0.0,
        0.0,
        0.0,
        48,
        0.5,
        "mm_per_reconstruction_unit",
    )
    recommendation = recommend_fitting_strategy(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        actor_id="operator-1",
        reason="Use matching ancestor profile evidence.",
        created_at_utc="2026-10-03T14:00:00Z",
        vertical_profiles=(profile,),
        cross_section_measurements=(measurement,),
    )
    assert recommendation.strategy is FittingStrategy.AXISYMMETRIC_REVOLVE
    assert recommendation.m09_vertical_profile_ids == (profile.profile_id,)
    assert recommendation.m09_cross_section_measurement_ids == (measurement.measurement_id,)
    contradictory_measurement = replace(
        measurement,
        measurement_id="cross-section-contradictory-r1",
        minor_radius=1.0,
    )
    contradictory = recommend_fitting_strategy(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        actor_id="operator-1",
        reason="Review contradictory ancestor evidence.",
        created_at_utc="2026-10-03T14:00:00Z",
        cross_section_measurements=(contradictory_measurement,),
    )
    assert contradictory.strategy is FittingStrategy.REVIEW_REQUIRED
    assert "m09_cross_section_evidence_conflicts_with_revolve" in contradictory.uncertainty_codes

    stale_profile = VerticalProfile(
        profile.profile_id,
        profile.source_geometry_id,
        "normalized-r0",
        profile.scale_provenance_id,
        profile.scale_state,
        profile.coordinate_unit,
        profile.plane_origin,
        profile.horizontal_direction,
        profile.plane_normal,
        profile.lateral_tolerance,
        profile.horizontal_range,
        profile.vertical_range,
        profile.samples,
    )
    with pytest.raises(
        FittingStrategyError,
        match="m09_profile_or_section_evidence_stale_or_mismatched",
    ):
        recommend_fitting_strategy(
            scan,
            expected_scan_master_revision_id=scan.revision_id,
            actor_id="operator-1",
            reason="Reject stale ancestor evidence.",
            created_at_utc="2026-10-03T14:00:00Z",
            vertical_profiles=(stale_profile,),
        )


def test_strategy_thresholds_and_geometry_work_bounds_are_validated() -> None:
    with pytest.raises(
        FittingStrategyError, match="maximum_bilateral_reflection_error_out_of_range"
    ):
        FittingStrategyPolicy(maximum_bilateral_reflection_error=1.1)
    with pytest.raises(FittingStrategyError, match="scan_master_geometry_work_bound_exceeded"):
        _recommend(_scan_master(), FittingStrategyPolicy(maximum_vertices=8))
