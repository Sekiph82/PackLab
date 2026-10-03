from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_design_heatmap import (
    DesignModelGeometryReference,
    DistanceSignPolicy,
    HeatmapError,
    HeatmapPolicy,
    compute_scan_design_heatmap,
)
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "f3343d5e-bf9c-44ab-b519-bbdfca5401a0"
FRAME = "packlab-normalized-frame-v1"
PROVENANCE = "scale-provenance-fixture-r1"


def _scan_master(vertices: tuple[tuple[float, float, float], ...]) -> ScanMasterRevision:
    mesh = TriangleMeshData(vertices, ((0, 1, 2),))
    revision_id = "scan-master-fixture-r1"
    raw_digest = hashlib.sha256(b"synthetic heatmap input").hexdigest()
    manifest = {
        "scan_master_revision_id": revision_id,
        "authority_class": "SCAN_MASTER",
        "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        "scale_provenance_id": PROVENANCE,
        "scale_provenance": {
            "provenance_id": PROVENANCE,
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        },
        "project_id": PROJECT,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "output_geometry_sha256": mesh_sha256(mesh),
        "raw_capture_revision_id": "raw-capture-fixture-r1",
        "raw_capture_sha256": raw_digest,
        "parent_object_geometry_source_input_digest": raw_digest,
        "reconstruction_revision_id": "reconstruction-fixture-r1",
        "object_geometry_revision_id": "object-geometry-fixture-r1",
        "parent_object_geometry_revision_id": "object-geometry-fixture-r1",
        "alignment_transform": {
            "transform": {
                "target_frame": FRAME,
                "reconstruction_revision": "reconstruction-fixture-r1",
            },
            "parents": {"object_capture_geometry_id": "object-geometry-fixture-r1"},
        },
    }
    return ScanMasterRevision(revision_id, PROJECT, mesh, manifest)


def _design(mesh: TriangleMeshData, *, parent: str = "scan-master-fixture-r1"):
    return DesignModelGeometryReference(
        revision_id="design-model-fixture-r1",
        project_id=PROJECT,
        fitted_to_scan_master_revision_id=parent,
        mesh=mesh,
        geometry_sha256=mesh_sha256(mesh),
        coordinate_frame_id=FRAME,
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id=PROVENANCE,
    )


def _plane(z: float = 0.0) -> TriangleMeshData:
    return TriangleMeshData(
        ((0.0, 0.0, z), (1.0, 0.0, z), (1.0, 1.0, z), (0.0, 1.0, z)),
        ((0, 1, 2), (0, 2, 3)),
    )


def test_zero_offset_known_offset_and_deterministic_heatmap() -> None:
    same_surface = _scan_master(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0))
    )
    policy = HeatmapPolicy(sample_count=3, magnitude_thresholds=(0.1, 0.3))
    zero = compute_scan_design_heatmap(same_surface, _design(_plane()), policy=policy)
    repeated = compute_scan_design_heatmap(same_surface, _design(_plane()), policy=policy)
    assert zero.signed_distances == pytest.approx((0.0, 0.0, 0.0))
    assert zero.heatmap_id == repeated.heatmap_id
    assert zero.sampled_vertex_indices == (0, 1, 3)
    assert zero.color_bin_indices == (0, 0, 0)

    offset_scan = _scan_master(((0.0, 0.0, 0.2), (1.0, 0.0, 0.2), (0.0, 1.0, 0.2)))
    offset = compute_scan_design_heatmap(offset_scan, _design(_plane()))
    assert offset.signed_distances == pytest.approx((0.2, 0.2, 0.2), abs=1e-6)
    assert offset.distance_units == "mm_unverified"
    assert offset.as_dict()["scale"]["physical_accuracy_validation_status"] == (
        "DEFERRED_OWNER_VALIDATION"
    )
    assert offset.as_dict()["tolerance_interpretation"] == (
        "GEOMETRY_DEVIATION_ONLY_NOT_MANUFACTURING_TOLERANCE"
    )
    assert offset.as_dict()["scale"]["mold_use_authorized"] is False


def test_signed_mode_returns_inside_negative_and_outside_positive() -> None:
    tetrahedron = TriangleMeshData(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )
    scan = _scan_master(((0.1, 0.1, 0.1), (2.0, 2.0, 2.0), (0.2, 0.2, 0.2)))
    result = compute_scan_design_heatmap(
        scan,
        _design(tetrahedron),
        policy=HeatmapPolicy(sign_policy=DistanceSignPolicy.SIGNED_INSIDE_NEGATIVE),
    )
    assert result.signed_distances[0] < 0
    assert result.signed_distances[1] > 0
    assert result.signed_distances[2] < 0
    assert result.as_dict()["policy"]["sign_policy"] == "signed_inside_negative"


def test_signed_mode_rejects_open_target_and_stale_or_mismatched_parents() -> None:
    scan = _scan_master(((0.1, 0.1, 0.1), (0.2, 0.2, 0.2), (0.3, 0.1, 0.2)))
    signed = HeatmapPolicy(sign_policy=DistanceSignPolicy.SIGNED_INSIDE_NEGATIVE)
    with pytest.raises(HeatmapError, match="geometry_adapter_surface_distance_failed"):
        compute_scan_design_heatmap(scan, _design(_plane()), policy=signed)
    with pytest.raises(HeatmapError, match="design_model_parent_stale"):
        compute_scan_design_heatmap(scan, _design(_plane(), parent="older-scan-master"))
    with pytest.raises(HeatmapError, match="design_model_coordinate_or_scale_mismatch"):
        compute_scan_design_heatmap(
            scan,
            replace(_design(_plane()), scale_state=ScaleState.RELATIVE),
        )


def test_sampling_threshold_boundaries_and_scale_parent_metadata_are_recorded() -> None:
    scan = _scan_master(((0.0, 0.0, 0.5), (1.0, 0.0, 1.0), (0.0, 1.0, 2.0), (1.0, 1.0, 3.0)))
    policy = HeatmapPolicy(sample_count=3, magnitude_thresholds=(0.5, 1.0))
    result = compute_scan_design_heatmap(scan, _design(_plane()), policy=policy)
    assert result.sampled_vertex_indices == (0, 1, 3)
    assert result.signed_distances == pytest.approx((0.5, 1.0, 3.0), abs=1e-6)
    assert result.color_bin_indices == (0, 1, 2)
    record = result.as_dict()
    assert record["parents"]["design_model_fitted_to_scan_master_revision_id"] == scan.revision_id
    assert record["sampling"]["source_vertex_count"] == 4
    assert record["sampling"]["sample_count"] == 3
    assert record["scale"]["distance_units"] == "mm_unverified"
    assert record["color_bins"]
