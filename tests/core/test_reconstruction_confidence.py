from __future__ import annotations

import copy
import json
import math

import pytest
from test_object_mask_lifting import _fixture, _lift

from packlab_core.object_geometry_coverage import (
    ObjectGeometryCoveragePolicy,
    build_object_geometry_coverage_report,
)
from packlab_core.object_mask_lifting import WorldPoint
from packlab_core.reconstruction import (
    ReconstructionBackendId,
    ReconstructionOutputManifest,
    ReconstructionStageResult,
    StageStatus,
)
from packlab_core.reconstruction_artifacts import (
    ReconstructionArtifactPolicy,
    build_reconstruction_artifact_report,
)
from packlab_core.reconstruction_confidence import (
    ReconstructionConfidenceError,
    ReconstructionConfidenceProfile,
    build_reconstruction_confidence_report,
)
from packlab_core.registered_photo_ratio import build_registered_photo_ratio_report
from packlab_core.sparse_connectivity import build_sparse_connectivity_report
from packlab_core.sparse_mapping import (
    STAGE_SUMMARY_CONTRACT,
    SparseMappingRequest,
    normalize_sparse_mapping_result,
)

SOURCE_DIGEST = "a" * 64
REQUEST_DIGEST = "b" * 64
STAGE_DIGEST = "c" * 64
GEOMETRY_ID = f"object-geometry:{'d' * 64}"
MASK_DIGEST = "e" * 64


def _reports(*, score: float = 0.8) -> dict[str, dict[str, object]]:
    return {
        "registration": {
            "contract": "packlab.registered-photo-ratio.v1",
            "observation_status": "observed",
            "acceptance_status": "not_evaluated",
            "source_evidence": {
                "source_revision": "source-synthetic",
                "source_sha256": SOURCE_DIGEST,
                "request_sha256": REQUEST_DIGEST,
                "stage_evidence_sha256": STAGE_DIGEST,
            },
            "statistics": {
                "total_input_photos": 100,
                "registered_photos": int(score * 100),
                "registration_ratio": score,
            },
        },
        "sparse_connectivity": {
            "contract": "packlab.sparse-connectivity.v1",
            "observation_status": "observed",
            "acceptance_status": "not_evaluated",
            "source_evidence": {
                "request_sha256": REQUEST_DIGEST,
                "stage_evidence_sha256": STAGE_DIGEST,
            },
            "graph": {
                "node_count": 100,
                "largest_component_ratio": score,
                "isolated_node_ratio": 1 - score,
            },
        },
        "object_coverage": {
            "contract": "packlab.object-geometry-coverage.v1",
            "observation_status": "observed",
            "acceptance_status": "not_evaluated",
            "source_evidence": {
                "geometry_id": GEOMETRY_ID,
                "parents": {
                    "project_id": "project-synthetic",
                    "source_revision": "source-synthetic",
                    "source_input_digest": SOURCE_DIGEST,
                    "reconstruction_revision": "reconstruction-synthetic",
                    "mask_set_revision_id": "mask-set-synthetic",
                    "mask_set_revision_digest": MASK_DIGEST,
                },
            },
            "statistics": {
                "candidate_point_count": 100,
                "selected_point_count": int(score * 100),
                "selected_point_ratio": score,
                "multiview_support": {
                    "mean_support_ratio_per_selected_point": score,
                },
                "coverage": {"mean_projected_occupancy_ratio": score},
            },
        },
        "artifact_review": {
            "contract": "packlab.reconstruction-artifact-diagnostics.v1",
            "observation_status": "observed",
            "acceptance_status": "not_evaluated",
            "source_evidence": {
                "project_id": "project-synthetic",
                "source_input_digest": SOURCE_DIGEST,
                "reconstruction_revision": "reconstruction-synthetic",
                "geometry_id": GEOMETRY_ID,
                "mask_set_revision_id": "mask-set-synthetic",
                "mask_set_revision_digest": MASK_DIGEST,
            },
            "statistics": {
                "candidate_count": round((1 - score) * 100),
                "component_count": 100,
                "object_point_count": 100,
            },
        },
    }


def _build(reports: dict[str, dict[str, object]], profile=None):
    return build_reconstruction_confidence_report(
        reports.get("registration"),
        reports.get("sparse_connectivity"),
        reports.get("object_coverage"),
        reports.get("artifact_review"),
        profile=ReconstructionConfidenceProfile() if profile is None else profile,
    )


def test_weighted_components_are_explainable_and_provenance_linked() -> None:
    reports = _reports()
    before = copy.deepcopy(reports)
    profile = ReconstructionConfidenceProfile(
        registration_weight=0.4,
        sparse_connectivity_weight=0.2,
        object_coverage_weight=0.25,
        artifact_review_weight=0.15,
        minimum_artifact_review_score=0.8,
        minimum_confidence_score=0.75,
    )
    report = _build(reports, profile).as_dict()

    assert report["observation_status"] == "observed"
    assert report["threshold_status"] == "meets_profile"
    assert report["acceptance_status"] == "not_evaluated"
    assert report["confidence_score"] == pytest.approx(0.8)
    components = {item["component_id"]: item for item in report["components"]}
    assert components["registration"]["score_formula"] == "registered_photos / total_input_photos"
    assert components["registration"]["weight"] == 0.4
    assert components["registration"]["weighted_contribution"] == pytest.approx(0.32)
    assert components["object_coverage"]["input_metrics"]["mean_selected_support_ratio"] == 0.8
    assert report["provenance_status"] == "verified"
    assert reports == before


def test_all_component_and_overall_threshold_boundaries_are_inclusive() -> None:
    reports = _reports(score=0.8)
    profile = ReconstructionConfidenceProfile(
        minimum_registration_score=0.8,
        minimum_sparse_connectivity_score=0.8,
        minimum_object_coverage_score=0.8,
        minimum_artifact_review_score=0.8,
        minimum_confidence_score=0.8,
    )
    report = _build(reports, profile).as_dict()
    assert report["confidence_score"] == pytest.approx(0.8)
    assert report["threshold_status"] == "meets_profile"

    below = _build(
        reports,
        ReconstructionConfidenceProfile(
            minimum_registration_score=math.nextafter(0.8, 1.0),
            minimum_confidence_score=0.8,
        ),
    ).as_dict()
    assert below["threshold_status"] == "below_profile"


def test_missing_required_component_withholds_score_and_threshold_result() -> None:
    reports = _reports()
    del reports["object_coverage"]
    report = _build(reports).as_dict()
    assert report["observation_status"] == "incomplete"
    assert report["confidence_score"] is None
    assert report["partial_weighted_score"] is not None
    assert report["threshold_status"] == "not_evaluated"
    assert report["component_thresholds_met"] is None
    assert report["missing_component_ids"] == ["object_coverage"]
    assert report["missing_data_disposition"] == (
        "overall_score_withheld_when_any_required_component_missing"
    )


def test_incompatible_parent_provenance_and_invalid_metrics_fail_closed() -> None:
    reports = _reports()
    reports["artifact_review"]["source_evidence"]["source_input_digest"] = "f" * 64
    mismatch = _build(reports).as_dict()
    assert mismatch["observation_status"] == "invalid"
    assert mismatch["confidence_score"] is None
    assert mismatch["threshold_status"] == "not_evaluated"
    assert mismatch["provenance_reason_code"] == "source_revision_digest_mismatch"

    invalid = _reports()
    invalid["registration"]["statistics"]["registration_ratio"] = True
    invalid_report = _build(invalid).as_dict()
    assert invalid_report["observation_status"] == "invalid"
    assert invalid_report["confidence_score"] is None
    assert "registration" in invalid_report["invalid_component_ids"]


def test_unavailable_component_is_missing_and_serialization_is_deterministic() -> None:
    reports = _reports()
    unavailable = copy.deepcopy(reports["object_coverage"])
    unavailable["observation_status"] = "empty"
    unavailable["statistics"] = None
    reports["object_coverage"] = unavailable
    first = _build(reports)
    second = _build(copy.deepcopy(reports))
    assert first.serialize() == second.serialize()
    assert first.digest() == second.digest()
    assert first.as_dict()["confidence_score"] is None
    assert first.as_dict()["observation_status"] == "incomplete"


def test_profile_rejects_invalid_weights_and_thresholds() -> None:
    with pytest.raises(ReconstructionConfidenceError, match="registration_weight"):
        ReconstructionConfidenceProfile(registration_weight=0)
    with pytest.raises(ReconstructionConfidenceError, match="minimum_confidence_score"):
        ReconstructionConfidenceProfile(minimum_confidence_score=float("nan"))


def test_actual_versioned_producer_reports_integrate_on_matching_provenance() -> None:
    object_points = tuple(
        WorldPoint(f"point-{index}", position)
        for index, position in enumerate(
            (
                (0.0, 0.0, 2.0),
                (0.001, 0.0, 2.0),
                (0.0, 0.001, 2.0),
                (0.001, 0.001, 2.0),
                (0.002, 0.001, 2.0),
                (0.1, 0.1, 2.0),
            )
        )
    )
    lift_request, _masks, _source_bytes = _fixture(points=object_points)
    geometry = _lift(lift_request)
    image_ids = tuple(asset_id for asset_id, _digest in geometry.source_images)
    mapping_request = SparseMappingRequest(
        image_asset_ids=image_ids,
        source_revision=geometry.source_revision,
        source_digest=geometry.source_input_digest,
        matcher_selection_digest="f" * 64,
    )
    stage_summary = {
        "contract": STAGE_SUMMARY_CONTRACT,
        "total_images": len(image_ids),
        "registered_images": len(image_ids),
        "unregistered_images": 0,
        "registration_ratio": 1.0,
        "sparse_model_asset_id": "working/reconstruction/sparse",
    }
    sparse_run = normalize_sparse_mapping_result(
        mapping_request,
        ReconstructionStageResult(
            "sparse-mapping",
            StageStatus.SUCCEEDED,
            0,
            0.1,
            stdout="PACKLAB_SPARSE_MAPPING_SUMMARY_V1 " + json.dumps(stage_summary, sort_keys=True),
        ),
    )
    ratio_report = build_registered_photo_ratio_report(sparse_run)
    connectivity_report = build_sparse_connectivity_report(
        sparse_run,
        image_ids,
        [(index, index + 1) for index in range(len(image_ids) - 1)],
    )
    coverage_report = build_object_geometry_coverage_report(
        geometry,
        policy=ObjectGeometryCoveragePolicy(minimum_projected_coverage_ratio=0),
    )
    manifest = ReconstructionOutputManifest(
        project_id=geometry.project_id,
        reconstruction_revision=geometry.reconstruction_revision,
        backend_id=ReconstructionBackendId.COLMAP_OPENMVS,
        backend_version="synthetic",
        backend_build="fixture",
        backend_license="synthetic-test-only",
        configuration_digest="0" * 64,
        source_input_digest=geometry.source_input_digest,
        camera_convention=geometry.camera_conventions[0][2],
        point_count=geometry.candidate_count,
        scale_state=geometry.scale_state,
    )
    artifact_report = build_reconstruction_artifact_report(
        manifest,
        geometry,
        policy=ReconstructionArtifactPolicy(
            maximum_candidate_component_ratio=0.2,
            minimum_component_centroid_gap_ratio=0,
        ),
    )

    confidence = build_reconstruction_confidence_report(
        ratio_report,
        connectivity_report,
        coverage_report,
        artifact_report,
    ).as_dict()
    assert confidence["observation_status"] == "observed"
    assert confidence["provenance_status"] == "verified"
    assert confidence["confidence_score"] is not None
