from __future__ import annotations

import math

import pytest

from packlab_core.fitting_strategy import (
    FittingStrategy,
    PrincipalAxis,
    recommend_fitting_strategy,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.symmetric_section_loft import SectionLoftError, fit_symmetric_section_loft

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"


def _scan_master(*, shape: str = "ellipse", asymmetric: bool = False) -> ScanMasterRevision:
    angular_count = 64
    levels = tuple(float(index) for index in range(13))
    vertices: list[tuple[float, float, float]] = []
    for height in levels:
        vertical_scale = 1.0 - 0.25 * abs(height - 6.0) / 6.0
        for index in range(angular_count):
            angle = math.tau * index / angular_count
            if shape == "rounded_rect":
                cosine = math.cos(angle)
                sine = math.sin(angle)
                x = 3.0 * vertical_scale * math.copysign(abs(cosine) ** 0.5, cosine)
                y = 2.0 * vertical_scale * math.copysign(abs(sine) ** 0.5, sine)
            else:
                x = 3.0 * vertical_scale * math.cos(angle)
                y = 2.0 * vertical_scale * math.sin(angle)
            if asymmetric:
                x *= 1.0 + 0.30 * math.cos(angle)
            vertices.append((x, y, height))
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
    revision = f"scan-master-section-{shape}-{'asym' if asymmetric else 'sym'}-r1"
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


def _build(scan: ScanMasterRevision, *, symmetry: bool = True, heights=(2.0, 5.0, 8.0)):
    strategy = recommend_fitting_strategy(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        actor_id="operator-1",
        reason="Review stacked cross-section strategy.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    result = fit_symmetric_section_loft(
        scan,
        strategy,
        expected_scan_master_revision_id=scan.revision_id,
        expected_strategy_recommendation_id=strategy.recommendation_id,
        section_heights=heights,
        component_id="container",
        symmetry_constraints_enabled=symmetry,
        actor_id="operator-1",
        reason="Fit pinned stacked cross-sections.",
        created_at_utc="2026-10-03T15:00:00Z",
        chord_tolerance=0.25,
        maximum_preview_angular_segments=128,
    )
    return strategy, result


@pytest.mark.parametrize("shape", ["ellipse", "rounded_rect"])
def test_symmetric_elliptical_and_rounded_rect_lofts_are_deterministic(shape: str) -> None:
    scan = _scan_master(shape=shape)
    strategy, first = _build(scan)
    _, second = _build(scan)
    assert strategy.strategy is FittingStrategy.SYMMETRIC_STACKED_SECTION_LOFT
    assert strategy.principal_axis is PrincipalAxis.Z
    assert first == second
    assert first.operation.kind.value == "loft"
    assert first.operation.section_positions == (2.0, 5.0, 8.0)
    assert tuple(item.symmetry.value for item in first.sections) == ("both",) * 3
    assert first.scan_master_revision_id == scan.revision_id
    assert first.scan_master_geometry_sha256 == mesh_sha256(scan.mesh)
    assert first.model.parent_binding_revision_id == strategy.parent_binding.revision_id
    assert first.as_dict()["symmetry_evidence"][0]["symmetry_constraint_enabled"] is True


def test_symmetry_off_preserves_asymmetric_observed_cross_section_points() -> None:
    scan = _scan_master(asymmetric=True)
    strategy, result = _build(scan, symmetry=False)
    assert strategy.strategy in {
        FittingStrategy.SYMMETRIC_STACKED_SECTION_LOFT,
        FittingStrategy.REVIEW_REQUIRED,
    }
    assert tuple(item.symmetry.value for item in result.sections) == ("none",) * 3
    assert result.review_required
    assert all(
        item.disposition
        in {
            "OBSERVED_POINTS_PRESERVED",
            "OBSERVED_ASYMMETRY_PRESERVED_REVIEW_REQUIRED",
        }
        for item in result.symmetry_evidence
    )
    assert all(item.left_right_reflection_error_ratio > 0.05 for item in result.symmetry_evidence)
    observed = {(point[0], point[1]) for point in scan.mesh.vertices if point[2] == 2.0}
    captured = {(point.x, point.y) for point in result.sections[0].points}
    assert len(observed) == len(captured)
    assert max(min(math.hypot(x - px, y - py) for px, py in captured) for x, y in observed) < 1e-9
    observed = {(point[0], point[1]) for point in scan.mesh.vertices if point[2] == 2.0}
    captured = {(point.x, point.y) for point in result.sections[0].points}
    assert len(observed) == len(captured)
    assert max(min(math.hypot(x - px, y - py) for px, py in captured) for x, y in observed) < 1e-9


def test_symmetry_on_rejects_contradictory_evidence_and_sparse_or_unordered_heights() -> None:
    scan = _scan_master(asymmetric=True)
    with pytest.raises(
        SectionLoftError,
        match="strategy_not_supported_for_section_loft|symmetric_loft_strategy_evidence_required",
    ):
        _build(scan, symmetry=True)
    symmetric_scan = _scan_master()
    with pytest.raises(SectionLoftError, match="section_height_count_out_of_range"):
        _build(symmetric_scan, heights=(2.0, 8.0))
    with pytest.raises(SectionLoftError, match="section_heights_must_be_strictly_ordered"):
        _build(symmetric_scan, heights=(2.0, 8.0, 5.0))


def test_preview_is_proxy_only_and_stale_scan_master_rejects() -> None:
    scan = _scan_master(shape="rounded_rect")
    _, result = _build(scan)
    preview = result.preview.as_dict()
    assert preview["authority_class"] == "PREVIEW_PROXY"
    assert preview["scan_master_promoted"] is False
    assert result.as_dict()["scan_master_replaced"] is False
    assert result.as_dict()["cad_or_brep_generated"] is False
    assert result.as_dict()["preview_is_parametric_truth"] is False
    assert len(result.preview.mesh.triangles) > 0

    strategy = recommend_fitting_strategy(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        actor_id="operator-1",
        reason="Stale parent test.",
        created_at_utc="2026-10-03T15:00:00Z",
    )
    with pytest.raises(SectionLoftError, match="scan_master_parent_stale"):
        fit_symmetric_section_loft(
            scan,
            strategy,
            expected_scan_master_revision_id="scan-master-newer",
            expected_strategy_recommendation_id=strategy.recommendation_id,
            section_heights=(2.0, 5.0, 8.0),
            component_id="container",
            symmetry_constraints_enabled=True,
            actor_id="operator-1",
            reason="Reject stale source.",
            created_at_utc="2026-10-03T15:00:00Z",
        )
