from __future__ import annotations

import json
import math
from dataclasses import replace

import pytest
from test_object_mask_lifting import _fixture, _lift

from packlab_core.object_mask_lifting import WorldPoint
from packlab_core.reconstruction import (
    ReconstructionBackendId,
    ReconstructionOutputManifest,
)
from packlab_core.reconstruction_artifacts import (
    ReconstructionArtifactError,
    ReconstructionArtifactPolicy,
    build_reconstruction_artifact_report,
)


def _inputs():
    points = (
        WorldPoint("cluster-0", (0.0, 0.0, 2.0)),
        WorldPoint("cluster-1", (0.001, 0.0, 2.0)),
        WorldPoint("cluster-2", (0.0, 0.001, 2.0)),
        WorldPoint("cluster-3", (0.001, 0.001, 2.0)),
        WorldPoint("cluster-4", (0.002, 0.001, 2.0)),
        WorldPoint("floating-0", (0.1, 0.1, 2.0)),
    )
    request, masks, source_bytes = _fixture(points=points)
    geometry = _lift(request)
    manifest = ReconstructionOutputManifest(
        project_id=geometry.project_id,
        reconstruction_revision=geometry.reconstruction_revision,
        backend_id=ReconstructionBackendId.COLMAP_OPENMVS,
        backend_version="fixture",
        backend_build="synthetic",
        backend_license="synthetic-test-only",
        configuration_digest="0" * 64,
        source_input_digest=geometry.source_input_digest,
        camera_convention=geometry.camera_conventions[0][2],
        point_count=geometry.candidate_count,
        scale_state=geometry.scale_state,
    )
    return manifest, geometry, source_bytes, masks


def test_isolated_component_is_a_review_candidate_without_mutation() -> None:
    manifest, geometry, source_bytes, masks = _inputs()
    manifest_bytes = json.dumps(manifest.as_dict(), sort_keys=True).encode()
    geometry_bytes = json.dumps(geometry.as_dict(), sort_keys=True).encode()
    raw_before = bytes(source_bytes)
    mask_bytes_before = tuple(mask.raster.values for mask in masks)

    report = build_reconstruction_artifact_report(
        manifest,
        geometry,
        policy=ReconstructionArtifactPolicy(
            neighbor_radius_ratio=0.025,
            maximum_candidate_component_ratio=1 / 6,
            minimum_component_centroid_gap_ratio=0.0,
        ),
    ).as_dict()

    assert report["observation_status"] == "observed"
    assert report["candidate_status"] == "candidates_detected"
    assert report["acceptance_status"] == "not_evaluated"
    assert report["statistics"]["component_count"] == 2
    assert report["statistics"]["isolated_component_count"] == 1
    assert report["candidates"][0]["point_count"] == 1
    assert report["candidates"][0]["automatic_removal"] is False
    assert bytes(source_bytes) == raw_before
    assert tuple(mask.raster.values for mask in masks) == mask_bytes_before
    assert json.dumps(manifest.as_dict(), sort_keys=True).encode() == manifest_bytes
    assert json.dumps(geometry.as_dict(), sort_keys=True).encode() == geometry_bytes


def test_connected_cloud_has_no_candidates_and_findings_ignore_input_order() -> None:
    manifest, geometry, _source_bytes, _masks = _inputs()
    cluster_geometry = replace(
        geometry,
        candidate_count=5,
        point_count=5,
        point_votes=geometry.point_votes[:5],
        filtered_points=geometry.filtered_points[:5],
        unfiltered_points=geometry.unfiltered_points[:5],
    )
    connected_policy = ReconstructionArtifactPolicy(
        neighbor_radius_ratio=0.5,
        maximum_candidate_component_ratio=0.2,
        minimum_component_centroid_gap_ratio=0.1,
    )
    connected = build_reconstruction_artifact_report(
        manifest, cluster_geometry, policy=connected_policy
    )
    assert connected.as_dict()["statistics"]["component_count"] == 1
    assert connected.as_dict()["candidate_status"] == "no_candidates_detected"

    permuted = replace(
        geometry,
        point_votes=tuple(reversed(geometry.point_votes)),
        filtered_points=tuple(reversed(geometry.filtered_points)),
        unfiltered_points=tuple(reversed(geometry.unfiltered_points)),
    )
    original = build_reconstruction_artifact_report(
        manifest,
        geometry,
        policy=ReconstructionArtifactPolicy(
            maximum_candidate_component_ratio=0.2,
            minimum_component_centroid_gap_ratio=0.0,
        ),
    )
    reordered = build_reconstruction_artifact_report(
        manifest,
        permuted,
        policy=ReconstructionArtifactPolicy(
            maximum_candidate_component_ratio=0.2,
            minimum_component_centroid_gap_ratio=0.0,
        ),
    )
    assert original.as_dict() == reordered.as_dict()
    assert original.digest() == reordered.digest()


def test_component_size_and_gap_threshold_boundaries_are_inclusive() -> None:
    manifest, geometry, _source_bytes, _masks = _inputs()
    baseline = build_reconstruction_artifact_report(
        manifest,
        geometry,
        policy=ReconstructionArtifactPolicy(
            maximum_candidate_component_ratio=0.2,
            minimum_component_centroid_gap_ratio=0.0,
        ),
    ).as_dict()
    measured_gap = baseline["candidates"][0]["centroid_gap_ratio_to_largest_component"]
    inclusive = build_reconstruction_artifact_report(
        manifest,
        geometry,
        policy=ReconstructionArtifactPolicy(
            maximum_candidate_component_ratio=1 / 6,
            minimum_component_centroid_gap_ratio=measured_gap,
        ),
    ).as_dict()
    assert len(inclusive["candidates"]) == 1

    excluded = build_reconstruction_artifact_report(
        manifest,
        geometry,
        policy=ReconstructionArtifactPolicy(
            maximum_candidate_component_ratio=0.16,
            minimum_component_centroid_gap_ratio=measured_gap,
        ),
    ).as_dict()
    assert excluded["candidate_status"] == "no_candidates_detected"

    gap_excluded = build_reconstruction_artifact_report(
        manifest,
        geometry,
        policy=ReconstructionArtifactPolicy(
            maximum_candidate_component_ratio=1 / 6,
            minimum_component_centroid_gap_ratio=math.nextafter(measured_gap, 1.0),
        ),
    ).as_dict()
    assert gap_excluded["candidate_status"] == "no_candidates_detected"


def test_degenerate_cloud_and_malformed_parent_provenance_fail_closed() -> None:
    manifest, geometry, _source_bytes, _masks = _inputs()
    degenerate = replace(
        geometry,
        filtered_points=((1.0, 1.0, 1.0),) * geometry.point_count,
        unfiltered_points=((1.0, 1.0, 1.0),) * geometry.point_count,
    )
    degenerate_report = build_reconstruction_artifact_report(
        manifest, degenerate, policy=ReconstructionArtifactPolicy()
    ).as_dict()
    assert degenerate_report["observation_status"] == "unavailable"
    assert degenerate_report["diagnostics"] == [{"code": "object_geometry_degenerate"}]

    mismatched_manifest = replace(manifest, reconstruction_revision="other-revision")
    invalid_report = build_reconstruction_artifact_report(
        mismatched_manifest, geometry, policy=ReconstructionArtifactPolicy()
    ).as_dict()
    assert invalid_report["observation_status"] == "unavailable"
    assert invalid_report["diagnostics"] == [{"code": "reconstruction_parent_invalid"}]


def test_policy_bounds_and_pair_budget_are_explicit() -> None:
    with pytest.raises(ReconstructionArtifactError, match="neighbor_radius_ratio"):
        ReconstructionArtifactPolicy(neighbor_radius_ratio=0)
    with pytest.raises(ReconstructionArtifactError, match="max_pair_checks"):
        ReconstructionArtifactPolicy(max_pair_checks=MAX_PAIR_CHECKS + 1)

    manifest, geometry, _source_bytes, _masks = _inputs()
    bounded = build_reconstruction_artifact_report(
        manifest,
        geometry,
        policy=ReconstructionArtifactPolicy(max_pair_checks=1),
    ).as_dict()
    assert bounded["observation_status"] == "unavailable"
    assert bounded["diagnostics"] == [{"code": "component_pair_check_limit_exceeded"}]


MAX_PAIR_CHECKS = 1_000_000
