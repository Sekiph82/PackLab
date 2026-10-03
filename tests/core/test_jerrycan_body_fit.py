from __future__ import annotations

import math

import pytest
from tests.core.test_symmetric_section_loft import PROJECT, _scan_master

from packlab_core.cross_section import CrossSectionSymmetry
from packlab_core.design_model import FeatureKind, PackageFamily, stable_feature_id
from packlab_core.fitting_strategy import recommend_fitting_strategy
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.jerrycan_body_fit import (
    JerrycanFrontDirection,
    fit_jerrycan_body,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.symmetric_section_loft import SectionLoftError, SectionLoftStatus


def _fit(scan, *, symmetry=CrossSectionSymmetry.BOTH, heights=(2.0, 5.0, 8.0)):
    strategy = recommend_fitting_strategy(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        actor_id="operator-1",
        reason="Select jerrycan section fitting strategy.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    result = fit_jerrycan_body(
        scan,
        strategy,
        expected_scan_master_revision_id=scan.revision_id,
        expected_strategy_recommendation_id=strategy.recommendation_id,
        section_heights=heights,
        component_id="jerrycan",
        symmetry=symmetry,
        front_direction=JerrycanFrontDirection.POSITIVE_Y,
        actor_id="operator-1",
        reason="Fit observed jerrycan body sections.",
        created_at_utc="2026-10-03T15:00:00Z",
        maximum_preview_angular_segments=128,
    )
    return strategy, result


@pytest.mark.parametrize("shape", ["ellipse", "rounded_rect"])
def test_symmetric_jerrycan_fit_is_deterministic_and_pinned(shape: str) -> None:
    scan = _scan_master(shape=shape)
    before_digest = mesh_sha256(scan.mesh)
    strategy, first = _fit(scan)
    _, second = _fit(scan)

    assert first == second
    assert first.status is SectionLoftStatus.READY
    assert first.model.package_family is PackageFamily.JERRYCAN
    assert first.model.fitted_to_scan_master_revision_id == scan.revision_id
    assert first.model.parent_binding_revision_id == strategy.parent_binding.revision_id
    assert first.scan_master_geometry_sha256 == before_digest == mesh_sha256(scan.mesh)
    assert first.operation.section_positions == (2.0, 5.0, 8.0)
    assert all(section.symmetry is CrossSectionSymmetry.BOTH for section in first.sections)
    assert {feature.semantic_key for feature in first.model.features} == {
        f"jerrycan-body-section:{index:04d}" for index in range(3)
    }
    body_section_0000 = next(
        feature for feature in first.model.features if feature.semantic_key.endswith(":0000")
    )
    assert body_section_0000.feature_id == stable_feature_id(
        "jerrycan", FeatureKind.BODY, "jerrycan-body-section:0000"
    )
    payload = first.as_dict()
    assert payload["section_frame"]["front_direction"] == "+y"
    assert payload["handles_or_voids_modeled"] is False
    assert payload["preview_is_parametric_truth"] is False
    assert payload["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert payload["coordinate_unit"] == "mm_unverified"


def test_asymmetric_body_preserves_observed_points_and_requires_review() -> None:
    scan = _scan_master(asymmetric=True)
    _, result = _fit(scan, symmetry=CrossSectionSymmetry.NONE)

    assert result.status is SectionLoftStatus.REVIEW_REQUIRED
    assert result.review_required
    assert all(section.symmetry is CrossSectionSymmetry.NONE for section in result.sections)
    assert result.model.package_family is PackageFamily.JERRYCAN
    observed = {(x, y) for x, y, z in scan.mesh.vertices if z == 2.0}
    fitted = {(point.x, point.y) for point in result.sections[0].points}
    assert len(fitted) == len(observed)
    assert (
        max(min((x - px) ** 2 + (y - py) ** 2 for px, py in fitted) ** 0.5 for x, y in observed)
        < 1e-9
    )


def test_explicit_single_plane_constraint_rejects_unsupported_evidence() -> None:
    scan = _scan_master(asymmetric=True)
    with pytest.raises(
        SectionLoftError, match="jerrycan_section_constraint_not_supported_by_evidence"
    ):
        _fit(scan, symmetry=CrossSectionSymmetry.LEFT_RIGHT)


def test_missing_sparse_and_unordered_sections_fail_closed() -> None:
    scan = _scan_with_vertical_gap()
    with pytest.raises(SectionLoftError, match="section_height_count_out_of_range"):
        _fit(scan, heights=(2.0, 8.0))
    with pytest.raises(SectionLoftError, match="section_heights_must_be_strictly_ordered"):
        _fit(scan, heights=(2.0, 8.0, 5.0))
    with pytest.raises(SectionLoftError, match="section_intersection_support_out_of_range"):
        _fit(scan, symmetry=CrossSectionSymmetry.NONE, heights=(2.5, 5.0, 8.5))


def _scan_with_vertical_gap() -> ScanMasterRevision:
    angular_count = 64
    levels = (0.0, 1.0, 2.0, 3.0, 7.0, 8.0, 9.0, 12.0)
    vertices = tuple(
        (
            3.0
            * (1.0 - 0.1 * abs(height - 6.0) / 6.0)
            * math.cos(math.tau * index / angular_count),
            2.0
            * (1.0 - 0.1 * abs(height - 6.0) / 6.0)
            * math.sin(math.tau * index / angular_count),
            height,
        )
        for height in levels
        for index in range(angular_count)
    )
    triangles = tuple(
        triangle
        for ring in range(len(levels) - 1)
        if not (levels[ring] == 3.0 and levels[ring + 1] == 7.0)
        for index in range(angular_count)
        for triangle in (
            (
                ring * angular_count + index,
                ring * angular_count + (index + 1) % angular_count,
                (ring + 1) * angular_count + (index + 1) % angular_count,
            ),
            (
                ring * angular_count + index,
                (ring + 1) * angular_count + (index + 1) % angular_count,
                (ring + 1) * angular_count + index,
            ),
        )
    )
    mesh = TriangleMeshData(vertices, triangles)
    revision = "scan-master-jerrycan-gap-r1"
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


def test_front_direction_is_required_and_parent_binding_is_exact() -> None:
    scan = _scan_master()
    strategy = recommend_fitting_strategy(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        actor_id="operator-1",
        reason="Select jerrycan section fitting strategy.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    with pytest.raises(SectionLoftError, match="jerrycan_front_direction_required"):
        fit_jerrycan_body(
            scan,
            strategy,
            expected_scan_master_revision_id=scan.revision_id,
            expected_strategy_recommendation_id=strategy.recommendation_id,
            section_heights=(2.0, 5.0, 8.0),
            component_id="jerrycan",
            symmetry=CrossSectionSymmetry.NONE,
            front_direction="unknown",  # type: ignore[arg-type]
            actor_id="operator-1",
            reason="Reject implicit front/back orientation.",
            created_at_utc="2026-10-03T15:00:00Z",
        )
    with pytest.raises(SectionLoftError, match="scan_master_parent_stale"):
        fit_jerrycan_body(
            scan,
            strategy,
            expected_scan_master_revision_id="scan-master-stale",
            expected_strategy_recommendation_id=strategy.recommendation_id,
            section_heights=(2.0, 5.0, 8.0),
            component_id="jerrycan",
            symmetry=CrossSectionSymmetry.NONE,
            front_direction=JerrycanFrontDirection.POSITIVE_Y,
            actor_id="operator-1",
            reason="Reject stale Scan Master parent.",
            created_at_utc="2026-10-03T15:00:00Z",
        )
