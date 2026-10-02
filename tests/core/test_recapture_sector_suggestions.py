from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace

from test_object_mask_lifting import _fixture, _lift

from packlab_core.object_geometry_coverage import (
    ObjectGeometryCoveragePolicy,
    build_object_geometry_coverage_report,
)
from packlab_core.object_mask_lifting import ObjectCaptureGeometry
from packlab_core.recapture_sector_suggestions import (
    RecaptureSectorPolicy,
    suggest_recapture_sectors,
)
from packlab_core.reconstruction import ReconstructionStageResult, StageStatus
from packlab_core.registered_photo_ratio import build_registered_photo_ratio_report
from packlab_core.sparse_mapping import SparseMappingRequest, normalize_sparse_mapping_result


def _inputs(*, registered: int = 5, empty: bool = False):
    request, _masks, source_bytes = _fixture()
    geometry = _lift(request)
    if empty:
        votes = tuple(replace(vote, selected=False) for vote in geometry.point_votes)
        geometry = replace(
            geometry,
            threshold_profile=replace(geometry.threshold_profile, minimum_support_ratio=1.0),
            point_count=0,
            point_votes=votes,
            filtered_points=(),
            unfiltered_points=(),
            obb=None,
        )
    image_ids = tuple(asset_id for asset_id, _digest in geometry.source_images)
    sparse_request = SparseMappingRequest(
        image_asset_ids=image_ids,
        source_revision=geometry.source_revision,
        source_digest=geometry.source_input_digest,
        matcher_selection_digest=hashlib.sha256(b"synthetic matcher").hexdigest(),
    )
    summary = {
        "contract": "packlab.sparse-mapping.stage-summary.v1",
        "total_images": len(image_ids),
        "registered_images": registered,
        "unregistered_images": len(image_ids) - registered,
        "registration_ratio": registered / len(image_ids),
        "sparse_model_asset_id": "working/reconstruction/sparse",
    }
    sparse_run = normalize_sparse_mapping_result(
        sparse_request,
        ReconstructionStageResult(
            "sparse-mapping",
            StageStatus.SUCCEEDED,
            0,
            0.1,
            stdout="PACKLAB_SPARSE_MAPPING_SUMMARY_V1 " + json.dumps(summary, sort_keys=True),
        ),
    )
    registration = build_registered_photo_ratio_report(sparse_run)
    coverage = build_object_geometry_coverage_report(
        geometry,
        policy=ObjectGeometryCoveragePolicy(
            grid_resolution=2,
            minimum_selected_point_ratio=0.2,
            minimum_mean_support_ratio=0.7,
            minimum_projected_coverage_ratio=0.25,
        ),
    )
    return geometry, registration, coverage, source_bytes


def _put_camera_centers_in_all_azimuth_sectors(geometry: ObjectCaptureGeometry):
    center = tuple(
        sum(point[axis] for point in geometry.filtered_points) / len(geometry.filtered_points)
        for axis in range(3)
    )
    cameras = []
    for index, camera in enumerate(geometry.camera_evidence):
        angle = 2 * math.pi * (index % 4) / 4 + math.pi / 4
        camera_center = (center[0] + math.cos(angle), center[1] + math.sin(angle), center[2])
        matrix = (
            1,
            0,
            0,
            -camera_center[0],
            0,
            1,
            0,
            -camera_center[1],
            0,
            0,
            1,
            -camera_center[2],
            0,
            0,
            0,
            1,
        )
        cameras.append(replace(camera, normalized_world_to_camera=matrix))
    return replace(geometry, camera_evidence=tuple(cameras))


def test_partial_coverage_suggests_bounded_deterministic_relative_sectors() -> None:
    geometry, registration, coverage, source_bytes = _inputs(registered=5)
    original_geometry = geometry.as_dict()
    original_registration = registration.serialize()
    original_coverage = coverage.serialize()
    original_source = bytes(source_bytes)
    policy = RecaptureSectorPolicy(minimum_projected_occupancy_ratio=0.3)

    first = suggest_recapture_sectors(geometry, registration, coverage, policy=policy)
    second = suggest_recapture_sectors(geometry, registration, coverage, policy=policy)

    payload = first.as_dict()
    assert payload["decision"] == "targeted_recapture"
    assert payload["qa_gaps"] == [
        "registration_below_threshold",
        "projected_occupancy_below_threshold",
    ]
    assert len(payload["suggestions"]) == 6
    assert payload == second.as_dict()
    suggestions = payload["suggestions"]
    assert [item["nearest_observed_view_gap_degrees"] for item in suggestions] == sorted(
        (item["nearest_observed_view_gap_degrees"] for item in suggestions), reverse=True
    )
    assert all("unobserved_view_sector" in item["reason_codes"] for item in suggestions)
    assert all(item["physical_orientation_claimed"] is False for item in suggestions)
    assert geometry.as_dict() == original_geometry
    assert registration.serialize() == original_registration
    assert coverage.serialize() == original_coverage
    assert bytes(source_bytes) == original_source


def test_complete_qa_evidence_reports_no_recapture_and_sector_exhaustion_falls_back() -> None:
    geometry, _registration, _coverage, _source_bytes = _inputs(registered=10)
    policy = RecaptureSectorPolicy(
        azimuth_sector_count=4,
        elevation_band_count=1,
        minimum_registration_ratio=0.7,
        minimum_selected_point_ratio=0.2,
        minimum_mean_support_ratio=0.7,
        minimum_projected_occupancy_ratio=0.25,
    )
    registration = _inputs(registered=10)[1]
    coverage = build_object_geometry_coverage_report(
        geometry,
        policy=ObjectGeometryCoveragePolicy(
            grid_resolution=2,
            minimum_selected_point_ratio=0.2,
            minimum_mean_support_ratio=0.7,
            minimum_projected_coverage_ratio=0.25,
        ),
    )
    assert (
        suggest_recapture_sectors(geometry, registration, coverage, policy=policy).as_dict()[
            "decision"
        ]
        == "no_recapture_indicated"
    )

    distributed = _put_camera_centers_in_all_azimuth_sectors(geometry)
    lower_registration = _inputs(registered=6)[1]
    distributed_coverage = build_object_geometry_coverage_report(
        distributed,
        policy=ObjectGeometryCoveragePolicy(
            grid_resolution=2,
            minimum_selected_point_ratio=0.2,
            minimum_mean_support_ratio=0.7,
            minimum_projected_coverage_ratio=0.25,
        ),
    )
    fallback = suggest_recapture_sectors(
        distributed, lower_registration, distributed_coverage, policy=policy
    ).as_dict()
    assert fallback["decision"] == "full_rescan"
    assert fallback["fallback"]["reason_code"] == "qa_gaps_remain_with_all_view_sectors_observed"


def test_empty_coverage_requires_full_rescan_without_a_localization_anchor() -> None:
    geometry, registration, coverage, _source_bytes = _inputs(registered=0, empty=True)
    payload = suggest_recapture_sectors(geometry, registration, coverage).as_dict()
    assert payload["decision"] == "full_rescan"
    assert payload["fallback"]["reason_code"] == "qa_gap_without_selected_geometry_anchor"
    assert payload["suggestions"] == []


def test_missing_or_unbound_parent_evidence_fails_closed() -> None:
    geometry, registration, coverage, _source_bytes = _inputs()
    assert (
        suggest_recapture_sectors(geometry, None, coverage).as_dict()["decision"] == "unavailable"
    )
    assert (
        suggest_recapture_sectors(geometry, registration, None).as_dict()["decision"]
        == "unavailable"
    )

    stale_geometry = replace(geometry, source_revision="different-source-revision")
    stale_coverage = build_object_geometry_coverage_report(
        stale_geometry,
        policy=ObjectGeometryCoveragePolicy(
            grid_resolution=2,
            minimum_selected_point_ratio=0.2,
            minimum_mean_support_ratio=0.7,
            minimum_projected_coverage_ratio=0.25,
        ),
    )
    assert (
        suggest_recapture_sectors(stale_geometry, registration, stale_coverage).as_dict()[
            "diagnostics"
        ][0]["code"]
        == "registration_evidence_missing_or_unbound"
    )


def test_inclusive_threshold_boundaries_do_not_create_gaps() -> None:
    geometry, _registration, coverage, _source_bytes = _inputs(registered=7)
    registration = _inputs(registered=7)[1]
    policy = RecaptureSectorPolicy(
        minimum_registration_ratio=0.7,
        minimum_selected_point_ratio=0.2,
        minimum_mean_support_ratio=0.7,
        minimum_projected_occupancy_ratio=0.25,
    )
    payload = suggest_recapture_sectors(geometry, registration, coverage, policy=policy).as_dict()
    assert payload["decision"] == "no_recapture_indicated"
    just_above = replace(policy, minimum_registration_ratio=0.700001)
    boundary = suggest_recapture_sectors(
        geometry, registration, coverage, policy=just_above
    ).as_dict()
    assert boundary["qa_gaps"] == ["registration_below_threshold"]
