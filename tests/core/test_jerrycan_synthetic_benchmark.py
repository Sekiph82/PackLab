from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from tests.core.test_jerrycan_grip_indent import (
    _create,
    _evidence,
)
from tests.core.test_jerrycan_grip_indent import (
    _inputs as grip_inputs,
)
from tests.core.test_jerrycan_handle_opening import _opening
from tests.core.test_symmetric_section_loft import _scan_master

from packlab_core.design_history import DesignModelHistory
from packlab_core.design_model import FeatureKind
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.jerrycan_grip_indent import GripIndentError, create_grip_indent_depth_edit
from packlab_core.jerrycan_handle_opening import (
    move_jerrycan_handle_opening,
    resolve_jerrycan_handle_opening,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

FIXTURE_PATH = (
    Path(__file__).parents[1] / "fixtures" / "geometry" / "jerrycan_synthetic_benchmark_v1.json"
)
BENCHMARK = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _scaled_scan(scale: float, revision_id: str) -> ScanMasterRevision:
    base = _scan_master()
    mesh = TriangleMeshData(
        tuple(tuple(coordinate * scale for coordinate in point) for point in base.mesh.vertices),
        base.mesh.triangles,
    )
    manifest = {
        "scan_master_revision_id": revision_id,
        "project_id": base.project_id,
        "authority_class": "SCAN_MASTER",
        "output_geometry_sha256": mesh_sha256(mesh),
        "reconstruction_revision_id": f"synthetic-reconstruction-{revision_id}",
        "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        "scale_provenance_id": f"synthetic-scale-{revision_id}",
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "coverage_gaps": [],
    }
    return ScanMasterRevision(revision_id, base.project_id, mesh, manifest)


def _scaled_fit(scan: ScanMasterRevision, heights: tuple[float, ...]):
    from packlab_core.cross_section import CrossSectionSymmetry
    from packlab_core.fitting_strategy import recommend_fitting_strategy
    from packlab_core.jerrycan_body_fit import JerrycanFrontDirection, fit_jerrycan_body

    strategy = recommend_fitting_strategy(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        actor_id="benchmark-operator",
        reason="Fit the versioned synthetic jerrycan benchmark fixture.",
        created_at_utc="2026-10-04T12:00:00Z",
    )
    return fit_jerrycan_body(
        scan,
        strategy,
        expected_scan_master_revision_id=scan.revision_id,
        expected_strategy_recommendation_id=strategy.recommendation_id,
        section_heights=heights,
        component_id="benchmark-jerrycan",
        symmetry=CrossSectionSymmetry.BOTH,
        front_direction=JerrycanFrontDirection.POSITIVE_Y,
        actor_id="benchmark-operator",
        reason="Fit the versioned synthetic jerrycan benchmark fixture.",
        created_at_utc="2026-10-04T12:00:00Z",
        maximum_preview_angular_segments=128,
    )


def test_benchmark_fixture_is_explicitly_synthetic_and_non_physical() -> None:
    assert BENCHMARK["benchmark_kind"] == "software_geometry_only"
    assert "Not a physical dimensional-accuracy benchmark" in BENCHMARK["disclaimer"]
    assert "not a substitute" in BENCHMARK["disclaimer"]
    assert "no owner scans" in BENCHMARK["source_class"]
    assert BENCHMARK["authority_limits"] == {
        "coordinate_unit": "mm_unverified",
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "manufacturing_tolerance_claim": False,
        "scan_master_mutable": False,
        "preview_is_parametric_truth": False,
    }
    assert [style["style_id"] for style in BENCHMARK["styles"]] == ["2l_style", "5l_style"]


@pytest.mark.parametrize("style", BENCHMARK["styles"], ids=lambda style: style["style_id"])
def test_synthetic_style_body_fit_and_feature_behavior_are_repeatable(
    style: dict[str, Any],
) -> None:
    scale = float(style["synthetic_scale"])
    heights = tuple(float(value) for value in style["section_heights"])
    scan = _scaled_scan(scale, f"synthetic-jerrycan-{style['style_id']}-r1")
    original_manifest = scan.manifest_bytes()
    original_digest = mesh_sha256(scan.mesh)

    first = _scaled_fit(scan, heights)
    second = _scaled_fit(scan, heights)
    assert first == second
    assert len(first.model.features) == int(style["expected_body_sections"])
    assert first.model.coordinate_unit == "mm_unverified"
    assert first.model.fitted_to_scan_master_revision_id == scan.revision_id
    assert first.model.scan_master_geometry_sha256 == original_digest
    assert first.as_dict()["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert first.as_dict()["preview_is_parametric_truth"] is False
    assert scan.manifest_bytes() == original_manifest
    assert mesh_sha256(scan.mesh) == original_digest

    _, _, _, handle_model, handle_feature = _opening()
    assert handle_feature.feature_kind is FeatureKind.HANDLE_OPENING
    assert any(item.feature_id == handle_feature.feature_id for item in handle_model.features)
    handle_edit = move_jerrycan_handle_opening(
        handle_model, handle_feature.feature_id, offset=(0.01, 0.01)
    )
    handle_history = DesignModelHistory(handle_model).apply(
        handle_edit,
        actor_id="benchmark-operator",
        reason="Apply bounded synthetic benchmark handle edit.",
        created_at_utc="2026-10-04T12:01:00Z",
    )
    assert (
        resolve_jerrycan_handle_opening(
            handle_history.current_revision, handle_feature.feature_id
        ).feature.feature_id
        == handle_feature.feature_id
    )

    grip_scan, grip_model, body = grip_inputs()
    grip_evidence = _evidence(grip_scan, grip_model, body)
    grip_result = _create(grip_scan, grip_model, grip_evidence)
    grip_feature = next(
        feature
        for feature in grip_result.features
        if feature.feature_kind is FeatureKind.GRIP_INDENT
    )
    with pytest.raises(GripIndentError, match="depth_outside_evidence_envelope"):
        create_grip_indent_depth_edit(grip_result, grip_feature.feature_id, 1.1)
    assert grip_result.fitted_to_scan_master_revision_id == grip_scan.revision_id
    assert grip_result.coordinate_unit == "mm_unverified"
    assert grip_result.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"


def test_invalid_synthetic_grip_fixture_stays_review_required() -> None:
    scan, model, body = grip_inputs(surface="ambiguous")
    evidence = _evidence(scan, model, body)
    assert evidence.status.value == "REVIEW_REQUIRED"
    assert "local_indent_depth_not_distinct_from_surface_support" in evidence.uncertainty_codes
