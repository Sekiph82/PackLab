from __future__ import annotations

import math
from dataclasses import replace

from test_object_mask_lifting import _fixture, _lift

from packlab_core.object_geometry_coverage import (
    ObjectGeometryCoveragePolicy,
    build_object_geometry_coverage_report,
)
from packlab_core.object_mask_lifting import LiftThresholdProfile


def _geometry():
    request, _masks, source_bytes = _fixture()
    before = bytes(source_bytes)
    geometry = _lift(request)
    assert bytes(source_bytes) == before
    return request, source_bytes, geometry


def test_sparse_and_empty_clouds_are_observed_without_surface_claims() -> None:
    _request, source_bytes, geometry = _geometry()
    before = bytes(source_bytes)
    sparse = build_object_geometry_coverage_report(
        geometry,
        policy=ObjectGeometryCoveragePolicy(
            grid_resolution=8,
            minimum_selected_point_ratio=0.2,
            minimum_mean_support_ratio=0.7,
            minimum_projected_coverage_ratio=1 / 64,
        ),
    ).as_dict()
    assert sparse["observation_status"] == "observed"
    assert sparse["threshold_status"] == "pass"
    assert sparse["statistics"]["density"]["occupied_voxel_count"] == 1
    assert sparse["statistics"]["coverage"]["xy_occupancy_ratio"] == 1 / 64
    assert sparse["statistics"]["coverage"]["surface_area_claimed"] is False
    assert sparse["acceptance_status"] == "not_evaluated"
    assert bytes(source_bytes) == before

    empty_votes = tuple(replace(vote, selected=False) for vote in geometry.point_votes)
    empty_geometry = replace(
        geometry,
        threshold_profile=replace(geometry.threshold_profile, minimum_support_ratio=1.0),
        point_count=0,
        point_votes=empty_votes,
        filtered_points=(),
        unfiltered_points=(),
        obb=None,
    )
    empty = build_object_geometry_coverage_report(
        empty_geometry, policy=ObjectGeometryCoveragePolicy()
    ).as_dict()
    assert empty["observation_status"] == "empty"
    assert empty["threshold_status"] == "not_evaluated"
    assert empty["statistics"]["density"]["occupied_voxel_count"] == 0


def test_dense_cloud_reports_bounded_unitless_density_and_support() -> None:
    request, _source_bytes, geometry = _geometry()
    dense_votes = tuple(
        replace(
            vote,
            observed_views=10,
            support_views=10,
            reject_views=0,
            not_observed_views=0,
            behind_camera_views=0,
            out_of_frame_views=0,
            occluded_views=0,
            support_ratio=1.0,
            selected=True,
        )
        for vote in geometry.point_votes
    )
    dense_geometry = replace(
        geometry,
        threshold_profile=LiftThresholdProfile(
            profile_id="dense-test-v1",
            minimum_observed_views=1,
            minimum_support_views=1,
            minimum_support_ratio=1.0,
        ),
        point_count=len(request.points),
        point_votes=dense_votes,
        filtered_points=tuple(point.position for point in request.points),
        unfiltered_points=tuple(point.position for point in request.points),
    )
    report = build_object_geometry_coverage_report(
        dense_geometry,
        policy=ObjectGeometryCoveragePolicy(grid_resolution=4),
    ).as_dict()
    statistics = report["statistics"]
    assert statistics["selected_point_count"] == 5
    assert statistics["density"]["grid_cell_count"] == 64
    assert statistics["density"]["occupied_voxel_count"] > 1
    assert statistics["density"]["physical_units"] is False
    assert statistics["multiview_support"]["support_view_votes"] == 50
    assert statistics["multiview_support"]["mean_support_ratio_per_selected_point"] == 1.0


def test_coverage_boundary_is_inclusive_and_input_order_is_irrelevant() -> None:
    _request, _source, geometry = _geometry()
    policy = ObjectGeometryCoveragePolicy(
        grid_resolution=8,
        minimum_selected_point_ratio=0.2,
        minimum_mean_support_ratio=0.7,
        minimum_projected_coverage_ratio=1 / 64,
    )
    original = build_object_geometry_coverage_report(geometry, policy=policy)
    permuted = replace(
        geometry,
        point_votes=tuple(reversed(geometry.point_votes)),
        filtered_points=tuple(reversed(geometry.filtered_points)),
        unfiltered_points=tuple(reversed(geometry.unfiltered_points)),
        camera_evidence=tuple(reversed(geometry.camera_evidence)),
    )
    reordered = build_object_geometry_coverage_report(permuted, policy=policy)
    assert original.as_dict() == reordered.as_dict()
    assert original.digest() == reordered.digest()
    assert original.as_dict()["threshold_status"] == "pass"
    below_boundary = build_object_geometry_coverage_report(
        geometry,
        policy=replace(
            policy,
            minimum_projected_coverage_ratio=math.nextafter(1 / 64, 1.0),
        ),
    ).as_dict()
    assert below_boundary["threshold_status"] == "below_threshold"


def test_invalid_parent_and_vote_provenance_fail_closed() -> None:
    _request, _source, geometry = _geometry()
    bad_parent = replace(geometry, source_input_digest="not-a-digest")
    bad_parent_report = build_object_geometry_coverage_report(
        bad_parent, policy=ObjectGeometryCoveragePolicy()
    ).as_dict()
    assert bad_parent_report["observation_status"] == "invalid"
    assert bad_parent_report["diagnostics"] == [{"code": "object_geometry_provenance_invalid"}]

    vote = geometry.point_votes[0]
    bad_vote = replace(vote, support_ratio=0.25)
    bad_votes = (bad_vote, *geometry.point_votes[1:])
    invalid_vote_geometry = replace(geometry, point_votes=bad_votes)
    invalid_vote_report = build_object_geometry_coverage_report(
        invalid_vote_geometry, policy=ObjectGeometryCoveragePolicy()
    ).as_dict()
    assert invalid_vote_report["observation_status"] == "invalid"


def test_density_and_coverage_profiles_reject_invalid_bounds() -> None:
    import pytest

    from packlab_core.object_geometry_coverage import ObjectGeometryCoverageError

    with pytest.raises(ObjectGeometryCoverageError, match="grid_resolution"):
        ObjectGeometryCoveragePolicy(grid_resolution=65)
    with pytest.raises(ObjectGeometryCoverageError, match="minimum_projected_coverage_ratio"):
        ObjectGeometryCoveragePolicy(minimum_projected_coverage_ratio=float("nan"))
