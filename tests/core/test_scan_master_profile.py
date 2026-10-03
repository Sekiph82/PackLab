from __future__ import annotations

import math

import pytest

from packlab_core.cross_section_overlay import CanonicalAxis
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.scan_master_profile import (
    ScanMasterProfileError,
    extract_scan_master_vertical_profile,
)

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"


def _scan_master(
    levels: tuple[float, ...] = tuple(float(value) for value in range(11)),
    *,
    outlier: bool = False,
) -> ScanMasterRevision:
    angular_count = 64
    vertices: list[tuple[float, float, float]] = []
    for height in levels:
        for index in range(angular_count):
            angle = math.tau * index / angular_count
            vertices.append((2.0 * math.cos(angle), 2.0 * math.sin(angle), height))
    faces: list[tuple[int, int, int]] = []
    for ring in range(len(levels) - 1):
        for index in range(angular_count):
            following = (index + 1) % angular_count
            first = ring * angular_count + index
            second = ring * angular_count + following
            third = (ring + 1) * angular_count + following
            fourth = (ring + 1) * angular_count + index
            faces.extend(((first, second, third), (first, third, fourth)))
    if outlier:
        vertices[5 * angular_count] = (12.0, 0.0, 5.0)
    mesh = TriangleMeshData(tuple(vertices), tuple(faces))
    revision = "scan-master-profile-r1"
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


def _extract(scan: ScanMasterRevision, *, bands: int = 10):
    return extract_scan_master_vertical_profile(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        axis=CanonicalAxis.Z,
        plane_origin=(0.0, 0.0, 0.0),
        front_direction=(1.0, 0.0, 0.0),
        lateral_tolerance=0.3,
        band_count=bands,
        minimum_band_samples=3,
        outlier_mad_multiplier=4.5,
        actor_id="operator-1",
        reason="Extract observed profile evidence.",
        created_at_utc="2026-10-03T15:00:00Z",
    )


def test_cylindrical_profile_is_deterministic_ordered_and_parent_bound() -> None:
    scan = _scan_master()
    profile = _extract(scan)
    assert profile == _extract(scan)
    assert profile.profile_id == _extract(scan).profile_id
    assert profile.scan_master_revision_id == scan.revision_id
    assert profile.scan_master_geometry_sha256 == mesh_sha256(scan.mesh)
    assert profile.parent_binding.fitted_to_scan_master_revision_id == scan.revision_id
    assert profile.axis is CanonicalAxis.Z
    assert tuple(item.band_index for item in profile.bands) == tuple(
        sorted(item.band_index for item in profile.bands)
    )
    assert all(item.horizontal_minimum < item.horizontal_maximum for item in profile.bands)
    payload = profile.as_dict()
    assert payload["scale"]["coordinate_unit"] == "mm_unverified"
    assert payload["scale"]["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert payload["scale"]["mold_use_authorized"] is False
    assert payload["closure_invented"] is False
    assert payload["sampling_policy"]["smoothing_applied"] is False


def test_sparse_source_preserves_coverage_gaps_without_fabricating_closure() -> None:
    sparse = _scan_master((0.0, 1.0, 2.0, 8.0, 9.0, 10.0))
    profile = _extract(sparse, bands=10)
    assert profile.coverage_gaps
    assert any(item.reason == "no_in_plane_observations" for item in profile.coverage_gaps)
    assert len(profile.bands) + len(profile.coverage_gaps) == 10
    assert profile.as_dict()["sampling_policy"]["interpolation_applied"] is False


def test_bounded_outlier_is_recorded_and_removed_only_from_band_summary() -> None:
    scan = _scan_master(outlier=True)
    profile = _extract(scan)
    assert len(profile.outliers) == 1
    outlier = profile.outliers[0]
    assert outlier.captured_point == (12.0, 0.0, 5.0)
    assert outlier.source_vertex_index == 5 * 64
    assert outlier.as_dict()["disposition"] == "REJECTED_FROM_PROFILE_SUMMARY_SOURCE_RETAINED"
    assert all(
        outlier.source_vertex_index not in item.source_vertex_indices for item in profile.bands
    )
    assert profile.scan_master_geometry_sha256 == mesh_sha256(scan.mesh)


def test_stale_parent_and_invalid_axis_front_or_work_bounds_reject() -> None:
    scan = _scan_master()
    with pytest.raises(ScanMasterProfileError, match="scan_master_parent_stale"):
        extract_scan_master_vertical_profile(
            scan,
            expected_scan_master_revision_id="newer-scan-master-r2",
            axis=CanonicalAxis.Z,
            plane_origin=(0.0, 0.0, 0.0),
            front_direction=(1.0, 0.0, 0.0),
            lateral_tolerance=0.3,
            band_count=10,
            minimum_band_samples=3,
            outlier_mad_multiplier=4.5,
            actor_id="operator-1",
            reason="Stale parent test.",
            created_at_utc="2026-10-03T15:00:00Z",
        )
    with pytest.raises(ScanMasterProfileError, match="profile_front_direction_must_be_transverse"):
        extract_scan_master_vertical_profile(
            scan,
            expected_scan_master_revision_id=scan.revision_id,
            axis=CanonicalAxis.Z,
            plane_origin=(0.0, 0.0, 0.0),
            front_direction=(0.0, 0.0, 1.0),
            lateral_tolerance=0.3,
            band_count=10,
            minimum_band_samples=3,
            outlier_mad_multiplier=4.5,
            actor_id="operator-1",
            reason="Invalid axis test.",
            created_at_utc="2026-10-03T15:00:00Z",
        )
    with pytest.raises(ScanMasterProfileError, match="profile_band_count_out_of_range"):
        _extract(scan, bands=MAX_BANDS + 1)


MAX_BANDS = 2049
