from __future__ import annotations

import math
from dataclasses import replace

import pytest

from packlab_core.cross_section_overlay import CanonicalAxis
from packlab_core.design_model import FeatureKind, stable_feature_id
from packlab_core.design_profile_fit import (
    ProfileTransitionAnchor,
    ProfileTransitionKind,
    fit_design_profile,
)
from packlab_core.design_profile_zones import (
    ProfileZoneError,
    ProfileZoneStatus,
    detect_design_profile_zones,
    override_design_profile_zones,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.scan_master_profile import extract_scan_master_vertical_profile


def _fit_clear_zones(*, ambiguous: bool = False):
    angular_count = 64
    levels = tuple(index / 2 for index in range(31))
    vertices: list[tuple[float, float, float]] = []
    for height in levels:
        radius = (
            2.0
            if ambiguous
            else 0.8
            if height <= 1.5
            else 2.2
            if height <= 8.0
            else 2.05
            if height <= 8.5
            else 1.9
            if height <= 9.0
            else 1.65
            if height <= 10.0
            else 1.4
        )
        for index in range(angular_count):
            angle = math.tau * index / angular_count
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), height))
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
    scan_id = "scan-master-zone-fixture-r1"
    scan = ScanMasterRevision(
        scan_id,
        "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a",
        mesh,
        {
            "scan_master_revision_id": scan_id,
            "project_id": "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a",
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(mesh),
            "reconstruction_revision_id": "reconstruction-r1",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-r1",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    source = extract_scan_master_vertical_profile(
        scan,
        expected_scan_master_revision_id=scan_id,
        axis=CanonicalAxis.Z,
        plane_origin=(0.0, 0.0, 0.0),
        front_direction=(1.0, 0.0, 0.0),
        lateral_tolerance=0.3,
        band_count=16,
        minimum_band_samples=3,
        outlier_mad_multiplier=4.5,
        actor_id="operator-1",
        reason="Create zone fixture evidence.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    return fit_design_profile(
        source,
        transition_anchors=(
            ProfileTransitionAnchor(ProfileTransitionKind.BASE, 3),
            ProfileTransitionAnchor(ProfileTransitionKind.SHOULDER, 12),
        ),
        smoothing_strength=0.0,
        window_radius=2,
        maximum_relative_adjustment=0.25,
    )


def test_clear_synthetic_profile_yields_ordered_stable_editable_zone_features() -> None:
    fitted = _fit_clear_zones()
    first = detect_design_profile_zones(
        fitted, expected_fit_id=fitted.fit_id, component_id="container"
    )
    second = detect_design_profile_zones(
        fitted, expected_fit_id=fitted.fit_id, component_id="container"
    )
    assert first == second
    assert first.status is ProfileZoneStatus.DETECTED
    assert not first.review_required
    assert tuple(item.zone_kind for item in first.boundaries) == (
        "base",
        "body",
        "shoulder",
        "neck",
    )
    assert first.boundaries[0].start_axial == fitted.profile.domain[0]
    assert first.boundaries[-1].end_axial == fitted.profile.domain[1]
    assert all(
        left.end_axial == right.start_axial
        for left, right in zip(first.boundaries, first.boundaries[1:])
    )
    assert all(item.confidence >= 0.8 for item in first.boundaries)
    assert first.boundaries[0].feature_id == stable_feature_id(
        "container", FeatureKind.BASE, "profile-zone:base"
    )
    assert first.as_dict()["thread_or_finish_classified"] is False
    assert first.scan_master_revision_id == fitted.scan_master_revision_id


def test_ambiguous_base_and_neck_boundaries_remain_review_required() -> None:
    fitted = _fit_clear_zones(ambiguous=True)
    zones = detect_design_profile_zones(
        fitted, expected_fit_id=fitted.fit_id, component_id="container"
    )
    assert zones.status is ProfileZoneStatus.REVIEW_REQUIRED
    assert zones.review_required
    assert "base_transition_ambiguous" in zones.uncertainty_codes
    assert "shoulder_neck_boundary_ambiguous" in zones.uncertainty_codes


def test_manual_override_is_immutable_ordered_and_remains_review_required() -> None:
    fitted = _fit_clear_zones()
    original = detect_design_profile_zones(
        fitted, expected_fit_id=fitted.fit_id, component_id="container"
    )
    base, body, shoulder, neck = original.boundaries
    delta = 0.05
    updated = (
        replace(base, end_axial=base.end_axial + delta),
        replace(body, start_axial=body.start_axial + delta),
        shoulder,
        neck,
    )
    overridden = override_design_profile_zones(
        original,
        fitted,
        expected_zone_revision_id=original.revision_id,
        expected_fit_id=fitted.fit_id,
        boundaries=updated,
        actor_id="operator-1",
        reason="Align base transition to reviewed evidence.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    assert overridden.revision_id != original.revision_id
    assert overridden.previous_revision_id == original.revision_id
    assert overridden.status is ProfileZoneStatus.MANUAL_OVERRIDE
    assert overridden.review_required
    assert original.boundaries == (base, body, shoulder, neck)
    assert overridden.boundaries == updated


def test_stale_fit_zone_revision_and_unordered_override_reject() -> None:
    fitted = _fit_clear_zones()
    original = detect_design_profile_zones(
        fitted, expected_fit_id=fitted.fit_id, component_id="container"
    )
    with pytest.raises(ProfileZoneError, match="design_profile_fit_stale"):
        detect_design_profile_zones(
            fitted, expected_fit_id="design-profile-fit:stale", component_id="container"
        )
    with pytest.raises(ProfileZoneError, match="profile_zones_or_fit_stale"):
        override_design_profile_zones(
            original,
            fitted,
            expected_zone_revision_id="design-profile-zones:stale",
            expected_fit_id=fitted.fit_id,
            boundaries=original.boundaries,
            actor_id="operator-1",
            reason="Stale zone override.",
            created_at_utc="2026-10-03T15:00:00Z",
        )
    with pytest.raises(ProfileZoneError, match="profile_zones_identity_invalid"):
        override_design_profile_zones(
            replace(original, uncertainty_codes=("tampered",)),
            fitted,
            expected_zone_revision_id=original.revision_id,
            expected_fit_id=fitted.fit_id,
            boundaries=original.boundaries,
            actor_id="operator-1",
            reason="Tampered zone evidence.",
            created_at_utc="2026-10-03T15:00:00Z",
        )
    invalid = list(original.boundaries)
    invalid[1] = replace(invalid[1], start_axial=invalid[1].start_axial + 0.1)
    with pytest.raises(ProfileZoneError, match="zone_partition_invalid"):
        override_design_profile_zones(
            original,
            fitted,
            expected_zone_revision_id=original.revision_id,
            expected_fit_id=fitted.fit_id,
            boundaries=tuple(invalid),
            actor_id="operator-1",
            reason="Invalid zone ordering.",
            created_at_utc="2026-10-03T15:00:00Z",
        )


def test_tampered_fit_identity_rejects() -> None:
    fitted = _fit_clear_zones()
    forged = replace(fitted, smoothing_strength=0.1)
    with pytest.raises(ProfileZoneError, match="design_profile_fit_identity_invalid"):
        detect_design_profile_zones(forged, expected_fit_id=forged.fit_id, component_id="container")
