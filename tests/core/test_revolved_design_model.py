from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace

import pytest

from packlab_core.cross_section_overlay import CanonicalAxis
from packlab_core.design_model import PackageFamily
from packlab_core.design_profile_fit import (
    ProfileTransitionAnchor,
    ProfileTransitionKind,
    fit_design_profile,
)
from packlab_core.design_profile_zones import detect_design_profile_zones
from packlab_core.fitting_strategy import (
    STRATEGY_CONTRACT,
    FittingStrategy,
    PrincipalAxis,
    recommend_fitting_strategy,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.revolved_design_model import (
    RevolvedDesignModelError,
    build_axisymmetric_revolved_design_model,
)
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.scan_master_profile import extract_scan_master_vertical_profile


def _evidence():
    angular_count = 64
    levels = tuple(index / 2 for index in range(31))
    vertices: list[tuple[float, float, float]] = []
    for height in levels:
        radius = (
            0.8
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
    scan_id = "scan-master-revolve-fixture-r1"
    project_id = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
    scan = ScanMasterRevision(
        scan_id,
        project_id,
        mesh,
        {
            "scan_master_revision_id": scan_id,
            "project_id": project_id,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(mesh),
            "reconstruction_revision_id": "reconstruction-r1",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-r1",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    source_profile = extract_scan_master_vertical_profile(
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
        reason="Create revolve profile evidence.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    profile_fit = fit_design_profile(
        source_profile,
        transition_anchors=(
            ProfileTransitionAnchor(ProfileTransitionKind.BASE, 3),
            ProfileTransitionAnchor(ProfileTransitionKind.SHOULDER, 12),
        ),
        smoothing_strength=0.0,
        window_radius=2,
        maximum_relative_adjustment=0.25,
    )
    zones = detect_design_profile_zones(
        profile_fit,
        expected_fit_id=profile_fit.fit_id,
        component_id="container",
    )
    strategy = recommend_fitting_strategy(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        actor_id="operator-1",
        reason="Assess axisymmetric revolve suitability.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    return scan, strategy, profile_fit, zones


def _build(evidence=None):
    scan, strategy, profile_fit, zones = evidence or _evidence()
    result = build_axisymmetric_revolved_design_model(
        strategy,
        profile_fit,
        zones,
        expected_strategy_recommendation_id=strategy.recommendation_id,
        expected_profile_fit_id=profile_fit.fit_id,
        expected_feature_zone_revision_id=zones.revision_id,
        component_id="container",
        package_family=PackageFamily.BOTTLE,
        actor_id="operator-1",
        reason="Create editable axisymmetric bottle model.",
        created_at_utc="2026-10-03T15:00:00Z",
        chord_tolerance=0.25,
        profile_samples=32,
        maximum_angular_segments=128,
    )
    return scan, strategy, profile_fit, zones, result


def test_bottle_revolve_links_strategy_profile_and_zones_and_is_deterministic() -> None:
    evidence = _evidence()
    scan, strategy, profile_fit, zones, first = _build(evidence)
    _, _, _, _, second = _build(evidence)
    assert strategy.strategy is FittingStrategy.AXISYMMETRIC_REVOLVE
    assert strategy.principal_axis is PrincipalAxis.Z
    assert first == second
    assert first.model.revision_id == second.model.revision_id
    assert first.operation.operation_id == second.operation.operation_id
    assert first.operation.kind.value == "revolve"
    assert first.operation.angle_degrees == 360.0
    assert first.model.fitted_to_scan_master_revision_id == scan.revision_id
    assert first.model.scan_master_geometry_sha256 == profile_fit.scan_master_geometry_sha256
    assert first.model.parent_binding_revision_id == profile_fit.parent_binding.revision_id
    assert first.profile.profile_id == profile_fit.profile.profile_id
    zone_ids = {item.feature_id for item in zones.boundaries}
    model_ids = {item.feature_id for item in first.model.features}
    assert zone_ids <= model_ids
    metadata = first.as_dict()
    assert metadata["fitting_evidence"] == {
        "strategy_recommendation_id": strategy.recommendation_id,
        "profile_fit_id": profile_fit.fit_id,
        "feature_zone_revision_id": zones.revision_id,
    }
    assert metadata["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert metadata["mold_use_authorized"] is False


def test_preview_uses_existing_proxy_seam_and_cannot_become_scan_master_or_cad() -> None:
    scan, _, _, _, result = _build()
    preview = result.preview.as_dict()
    assert preview["authority_class"] == "PREVIEW_PROXY"
    assert preview["scan_master_promoted"] is False
    assert preview["scan_master_revision_id"] == scan.revision_id
    assert preview["scan_master_geometry_sha256"] == scan.manifest["output_geometry_sha256"]
    assert result.operation.as_dict()["output_geometry"] is None
    assert result.as_dict()["cad_or_brep_generated"] is False
    assert len(result.preview.mesh.vertices) > 0
    assert len(result.preview.mesh.triangles) > 0


def test_stale_strategy_or_profile_parent_and_review_required_zones_reject() -> None:
    scan, strategy, profile_fit, zones = _evidence()
    stale_strategy = replace(strategy, scan_master_revision_id="scan-master-newer")
    with pytest.raises(RevolvedDesignModelError, match="fitting_strategy_not_accepted_for_revolve"):
        _build((scan, stale_strategy, profile_fit, zones))
    with pytest.raises(RevolvedDesignModelError, match="design_profile_fit_stale"):
        build_axisymmetric_revolved_design_model(
            strategy,
            profile_fit,
            zones,
            expected_strategy_recommendation_id=strategy.recommendation_id,
            expected_profile_fit_id="design-profile-fit:stale",
            expected_feature_zone_revision_id=zones.revision_id,
            component_id="container",
            package_family=PackageFamily.BOTTLE,
            actor_id="operator-1",
            reason="Stale fit test.",
            created_at_utc="2026-10-03T15:00:00Z",
        )
    review_zones = replace(zones, status=zones.status.REVIEW_REQUIRED, review_required=True)
    with pytest.raises(
        RevolvedDesignModelError, match="design_profile_zones_not_accepted_or_parent_mismatch"
    ):
        _build((scan, strategy, profile_fit, review_zones))


def test_axis_strategy_must_match_profile_axis() -> None:
    scan, strategy, profile_fit, zones = _evidence()
    wrong_axis = replace(strategy, principal_axis=PrincipalAxis.X)
    axis_index = {PrincipalAxis.X: 0, PrincipalAxis.Y: 1, PrincipalAxis.Z: 2}[
        wrong_axis.principal_axis
    ]
    body = {
        "contract": STRATEGY_CONTRACT,
        "strategy": wrong_axis.strategy.value,
        "axis": axis_index,
        "elongation": wrong_axis.axis_elongation_ratio,
        "sections": [item.as_dict() for item in wrong_axis.section_evidence],
        "scan_master_revision_id": wrong_axis.scan_master_revision_id,
        "scan_master_geometry_sha256": wrong_axis.scan_master_geometry_sha256,
        "parent_binding": wrong_axis.parent_binding.as_dict(),
        "geometry_statistics": wrong_axis.geometry_statistics.as_dict(),
        "m09_vertical_profile_ids": list(wrong_axis.m09_vertical_profile_ids),
        "m09_cross_section_measurement_ids": list(wrong_axis.m09_cross_section_measurement_ids),
        "uncertainty_codes": list(wrong_axis.uncertainty_codes),
        "policy": wrong_axis.policy.as_dict(),
    }
    recommendation_id = (
        "fitting-strategy:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    wrong_axis = replace(wrong_axis, recommendation_id=recommendation_id)
    with pytest.raises(
        RevolvedDesignModelError, match="revolve_profile_axis_must_match_z_strategy"
    ):
        _build((scan, wrong_axis, profile_fit, zones))
