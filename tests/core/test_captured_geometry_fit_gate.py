from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest
from test_object_mask_lifting import _fixture, _lift

from packlab_core.captured_geometry_fit_gate import (
    CapturedGeometryFitGatePolicy,
    build_captured_geometry_fit_gate_report,
)
from packlab_core.object_geometry_coverage import (
    OBJECT_GEOMETRY_COVERAGE_CONTRACT,
    ObjectGeometryCoveragePolicy,
    build_object_geometry_coverage_report,
)
from packlab_core.object_mask_lifting import WorldPoint
from packlab_core.reconstruction import ScaleState
from packlab_core.reconstruction_confidence import (
    COMPONENT_IDS,
    ReconstructionConfidenceProfile,
    ReconstructionConfidenceReport,
)

_CONTRACTS = {
    "registration": "packlab.registered-photo-ratio.v1",
    "sparse_connectivity": "packlab.sparse-connectivity.v1",
    "object_coverage": OBJECT_GEOMETRY_COVERAGE_CONTRACT,
    "artifact_review": "packlab.reconstruction-artifact-diagnostics.v1",
}


def _prepared(*, scale_state: ScaleState = ScaleState.RELATIVE):
    points = (
        WorldPoint("fit-point-0", (0.0, 0.0, 2.0)),
        WorldPoint("fit-point-1", (0.001, 0.0, 2.0)),
    )
    request, _masks, source_bytes = _fixture(points=points, scale_state=scale_state)
    geometry = _lift(request)
    coverage = build_object_geometry_coverage_report(
        geometry,
        policy=ObjectGeometryCoveragePolicy(grid_resolution=2),
    )
    coverage_data = coverage.as_dict()
    coverage_stats = coverage_data["statistics"]
    coverage_values = {
        "selected_point_ratio": coverage_stats["selected_point_ratio"],
        "mean_selected_support_ratio": coverage_stats["multiview_support"][
            "mean_support_ratio_per_selected_point"
        ],
        "mean_projected_occupancy_ratio": coverage_stats["coverage"][
            "mean_projected_occupancy_ratio"
        ],
    }
    component_score = (sum(coverage_values.values())) / 3
    score_inputs = {
        "registration": {"registered_photos": 95, "total_input_photos": 100},
        "sparse_connectivity": {
            "largest_component_ratio": 0.95,
            "isolated_node_ratio": 0.05,
        },
        "object_coverage": coverage_values,
        "artifact_review": {
            "review_candidate_component_count": 1,
            "component_count": 20,
        },
    }
    scores = {
        "registration": 0.95,
        "sparse_connectivity": 0.95,
        "object_coverage": component_score,
        "artifact_review": 0.95,
    }
    profile = ReconstructionConfidenceProfile()
    profile_payload = profile.as_dict()
    weights = {item["component_id"]: item for item in profile_payload["components"]}
    source_digests = {
        component_id: hashlib.sha256(component_id.encode()).hexdigest()
        for component_id in COMPONENT_IDS
    }
    source_digests["object_coverage"] = coverage.digest()
    components = []
    for component_id in COMPONENT_IDS:
        component_profile = weights[component_id]
        score = scores[component_id]
        components.append(
            {
                "component_id": component_id,
                "contract": _CONTRACTS[component_id],
                "observation_status": "observed",
                "score": score,
                "weight": component_profile["weight"],
                "normalized_weight": component_profile["normalized_weight"],
                "weighted_contribution": score * component_profile["normalized_weight"],
                "minimum_component_score": component_profile["minimum_component_score"],
                "threshold_met": score >= component_profile["minimum_component_score"],
                "score_formula": {
                    "registration": "registered_photos / total_input_photos",
                    "sparse_connectivity": "(largest_component_ratio + (1 - isolated_node_ratio)) / 2",
                    "object_coverage": "(selected_point_ratio + mean_selected_support_ratio + mean_projected_occupancy_ratio) / 3",
                    "artifact_review": "1 - review_candidate_component_count / component_count",
                }[component_id],
                "input_metrics": score_inputs[component_id],
                "source_report_sha256": source_digests[component_id],
                "reason_code": None,
            }
        )
    overall_score = sum(item["weighted_contribution"] for item in components)
    confidence = ReconstructionConfidenceReport(
        {
            "contract": "packlab.reconstruction-confidence.v1",
            "authority": "diagnostic_only_no_physical_accuracy_or_acceptance_claim",
            "observation_status": "observed",
            "threshold_status": "meets_profile",
            "acceptance_status": "not_evaluated",
            "confidence_score": overall_score,
            "partial_weighted_score": overall_score,
            "component_thresholds_met": True,
            "missing_component_ids": [],
            "invalid_component_ids": [],
            "missing_data_disposition": "overall_score_withheld_when_any_required_component_missing",
            "provenance_status": "verified",
            "provenance_reason_code": None,
            "source_report_digests": source_digests,
            "components": components,
            "threshold_profile": profile_payload,
            "aggregation": {
                "method": "normalized_weighted_arithmetic_mean",
                "available_weight": 1.0,
                "total_weight": 1.0,
                "partial_score_is_not_confidence": True,
                "physical_accuracy_claimed": False,
            },
            "diagnostics": [],
        }
    )
    return geometry, coverage, confidence, source_bytes


def test_captured_geometry_with_current_explainable_qa_is_fit_eligible() -> None:
    geometry, coverage, confidence, source_bytes = _prepared()
    before = bytes(source_bytes)
    geometry_before = geometry.as_dict()
    coverage_before = coverage.as_dict()
    confidence_before = confidence.as_dict()

    report = build_captured_geometry_fit_gate_report(geometry, coverage, confidence).as_dict()

    assert report["decision"] == "eligible_for_downstream_parametric_fit"
    assert report["acceptance_status"] == "not_evaluated"
    assert report["parametric_fit_executed"] is False
    assert report["metric_accuracy_claimed"] is False
    assert report["diagnostics"] == []
    assert bytes(source_bytes) == before
    assert geometry.as_dict() == geometry_before
    assert coverage.as_dict() == coverage_before
    assert confidence.as_dict() == confidence_before


@pytest.mark.parametrize("scale_state", [ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED])
def test_relative_and_metric_unverified_scale_are_allowed(scale_state: ScaleState) -> None:
    geometry, coverage, confidence, _source = _prepared(scale_state=scale_state)
    report = build_captured_geometry_fit_gate_report(geometry, coverage, confidence).as_dict()
    assert report["decision"] == "eligible_for_downstream_parametric_fit"


def test_ai_reference_generated_and_missing_scale_inputs_are_rejected() -> None:
    geometry, coverage, confidence, _source = _prepared()
    ai_report = build_captured_geometry_fit_gate_report(
        {"authority_class": "AI_VISUAL_REFERENCE"}, coverage, confidence
    ).as_dict()
    assert ai_report["decision"] == "blocked"
    assert "ai_visual_reference_rejected" in {item["code"] for item in ai_report["diagnostics"]}

    object.__setattr__(geometry, "generated", True)
    generated_report = build_captured_geometry_fit_gate_report(
        geometry, coverage, confidence
    ).as_dict()
    assert generated_report["decision"] == "blocked"
    assert "generated_geometry_rejected" in {
        item["code"] for item in generated_report["diagnostics"]
    }

    geometry, coverage, confidence, _source = _prepared()
    object.__setattr__(geometry, "scale_state", None)
    missing_scale_report = build_captured_geometry_fit_gate_report(
        geometry, coverage, confidence
    ).as_dict()
    assert missing_scale_report["decision"] == "blocked"
    assert "geometry_scale_state_missing" in {
        item["code"] for item in missing_scale_report["diagnostics"]
    }


def test_weak_coverage_missing_confidence_and_parent_mismatch_block() -> None:
    geometry, coverage, confidence, _source = _prepared()
    weak = build_captured_geometry_fit_gate_report(
        geometry,
        coverage,
        confidence,
        policy=CapturedGeometryFitGatePolicy(minimum_projected_occupancy_ratio=0.5),
    ).as_dict()
    assert weak["decision"] == "blocked"
    assert "coverage_projected_occupancy_below_threshold" in {
        item["code"] for item in weak["diagnostics"]
    }

    no_confidence = build_captured_geometry_fit_gate_report(geometry, coverage, None).as_dict()
    assert no_confidence["decision"] == "blocked"
    assert "confidence_evidence_missing" in {item["code"] for item in no_confidence["diagnostics"]}

    stale_geometry = replace(geometry, mask_set_revision_digest="0" * 64)
    stale = build_captured_geometry_fit_gate_report(stale_geometry, coverage, confidence).as_dict()
    assert stale["decision"] == "blocked"
    assert "coverage_parent_identity_mismatch" in {item["code"] for item in stale["diagnostics"]}


def test_threshold_boundaries_are_inclusive_and_report_is_deterministic() -> None:
    geometry, coverage, confidence, _source = _prepared()
    metrics = coverage.as_dict()["statistics"]
    policy = CapturedGeometryFitGatePolicy(
        minimum_confidence_score=confidence.as_dict()["confidence_score"],
        minimum_selected_point_ratio=metrics["selected_point_ratio"],
        minimum_mean_support_ratio=metrics["multiview_support"][
            "mean_support_ratio_per_selected_point"
        ],
        minimum_projected_occupancy_ratio=metrics["coverage"]["mean_projected_occupancy_ratio"],
    )
    first = build_captured_geometry_fit_gate_report(geometry, coverage, confidence, policy=policy)
    second = build_captured_geometry_fit_gate_report(geometry, coverage, confidence, policy=policy)
    assert first.as_dict()["decision"] == "eligible_for_downstream_parametric_fit"
    assert first.serialize() == second.serialize()
    assert first.digest() == second.digest()


def test_gate_policy_rejects_out_of_range_thresholds() -> None:
    from packlab_core.captured_geometry_fit_gate import CapturedGeometryFitGateError

    with pytest.raises(CapturedGeometryFitGateError, match="minimum_confidence_score"):
        CapturedGeometryFitGatePolicy(minimum_confidence_score=1.01)
