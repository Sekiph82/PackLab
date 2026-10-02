from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from packlab_core.calibration.scale_provenance import ScaleProvenance
from packlab_core.coordinate_frame import NormalizedFrameTransform
from packlab_core.geometry_adapter import (
    CapabilityStatus,
    PointCloudData,
    TriangleMeshData,
    probe_open3d,
)
from packlab_core.normalization_transform import GeometryNormalizationTransform
from packlab_core.object_mask_lifting import (
    LiftThresholdProfile,
    LiftVisibilityPolicy,
    ObjectCaptureGeometry,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.repeat_scan_registration import (
    RegistrationError,
    RegistrationPolicy,
    RegistrationRevision,
    register_repeat_scans,
)
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "7c881a57-48c5-4c77-81ac-c79a27a8e469"
POINTS = tuple((float(x), float(y), float(z)) for x in range(3) for y in range(3) for z in range(3))


def _revision(
    revision_id: str,
    points=POINTS,
    *,
    scale_state=ScaleState.METRIC_UNVERIFIED,
    authority="OBJECT_CAPTURE_GEOMETRY",
    generated=False,
    project=PROJECT,
) -> RegistrationRevision:
    cloud = PointCloudData(tuple(points))
    return RegistrationRevision(
        revision_id,
        project,
        hashlib.sha256(repr(cloud.points).encode("ascii")).hexdigest(),
        cloud,
        hashlib.sha256(
            json.dumps(
                {"points": cloud.points, "colors": cloud.colors, "normals": cloud.normals},
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("ascii")
        ).hexdigest(),
        authority,
        generated,
        f"frame-{revision_id}",
        "mm_unverified" if scale_state is ScaleState.METRIC_UNVERIFIED else "reconstruction_units",
        scale_state,
        f"scale-{revision_id}",
        "DEFERRED_OWNER_VALIDATION",
        False,
    )


def _policy(**overrides) -> RegistrationPolicy:
    values = {
        "maximum_correspondence_distance": 0.25,
        "maximum_iterations": 100,
        "minimum_inlier_count": 6,
        "minimum_fitness": 0.8,
        "maximum_inlier_rmse": 0.05,
    }
    values.update(overrides)
    return RegistrationPolicy(**values)


def _translated(points, offset=(0.04, -0.03, 0.02)):
    return tuple(tuple(point[i] + offset[i] for i in range(3)) for point in points)


def _scale_provenance() -> ScaleProvenance:
    identity: dict[str, object] = {
        "contract": "packlab.scale-provenance.v1",
        "version": "scale_provenance_v1",
        "source_method": "synthetic-test-scale",
        "calibration_observation_ids": [],
        "physical_references": [],
        "estimated_scale_factor": 1.0,
        "scale_factor_unit": "mm_per_reconstruction_unit",
        "residuals": [],
        "rejected_observations": [],
        "algorithm_version": "fixture-v1",
        "outlier_policy_version": "fixture-v1",
        "input_reconstruction_revision": "reconstruction-capture-r1",
        "camera_solution_revision": "camera-capture-r1",
        "uncertainty": {"representation": "fixture", "value": 0.01},
        "created_at_utc": "2026-10-03T10:00:00Z",
        "actor_process_provenance": {"actor_id": "fixture", "process_id": "fixture"},
        "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        "promotion_evidence": None,
        "ai_visual_reference_measurement_authority": False,
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    provenance_id = "scale-provenance:" + hashlib.sha256(encoded.encode("ascii")).hexdigest()
    return ScaleProvenance(
        provenance_id,
        "synthetic-test-scale",
        (),
        (),
        1.0,
        (),
        (),
        "fixture-v1",
        "fixture-v1",
        "reconstruction-capture-r1",
        "camera-capture-r1",
        {"representation": "fixture", "value": 0.01},
        "2026-10-03T10:00:00Z",
        "fixture",
        "fixture",
        ScaleState.METRIC_UNVERIFIED,
    )


def _captured_geometry() -> ObjectCaptureGeometry:
    return ObjectCaptureGeometry(
        "object-geometry-capture-r1",
        PROJECT,
        "packscan-capture-r1",
        hashlib.sha256(b"captured input").hexdigest(),
        (),
        (),
        (),
        (),
        "reconstruction-capture-r1",
        "camera-capture-r1",
        "mask-set-capture-r1",
        hashlib.sha256(b"mask fixture").hexdigest(),
        "fixture-camera-v1",
        "fixture-lift-v1",
        LiftThresholdProfile(),
        LiftVisibilityPolicy(),
        "fixture-outlier-policy-v1",
        len(POINTS),
        len(POINTS),
        False,
        "OBJECT_CAPTURE_GEOMETRY",
        ScaleState.RELATIVE,
        (),
        POINTS,
        POINTS,
        None,
        "2026-10-03T10:00:00Z",
    )


def _alignment(geometry: ObjectCaptureGeometry) -> GeometryNormalizationTransform:
    transform = NormalizedFrameTransform(
        "normalized-capture-r1",
        "captured-object-reconstruction-frame-v1",
        "packlab-normalized-frame-v1",
        geometry.reconstruction_revision,
        ScaleState.METRIC_UNVERIFIED,
        "mm_unverified",
        "mm_unverified",
        (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0),
        "fixture-normalization-v1",
        "scale-estimate:" + "a" * 64,
    )
    return GeometryNormalizationTransform(
        transform,
        geometry.geometry_id,
        "a" * 64,
        1.0,
        0.01,
        "base-plane-capture-r1",
        "upright-capture-r1",
        "front-capture-r1",
        ScaleState.RELATIVE,
    )


def test_open3d_adapter_exposes_point_to_point_icp_capability() -> None:
    capability = probe_open3d()
    assert capability.status is CapabilityStatus.AVAILABLE
    assert "point_to_point_registration" in capability.operations


def test_identity_and_known_rigid_transform_register_with_parent_provenance() -> None:
    source = _revision("scan-a")
    target = _revision("scan-b", _translated(POINTS))
    source_before = (source.point_cloud.points, source.parent_digest)
    target_before = (target.point_cloud.points, target.parent_digest)

    result = register_repeat_scans(source, target, policy=_policy())

    assert result.convergence_status == "QUALITY_ACCEPTED_STOP_REASON_UNAVAILABLE"
    assert result.inlier_count == len(POINTS)
    assert result.inlier_ratio == 1.0
    assert result.transform_source_to_target[3] == pytest.approx(0.04, abs=1e-5)
    assert result.transform_source_to_target[7] == pytest.approx(-0.03, abs=1e-5)
    assert result.transform_source_to_target[11] == pytest.approx(0.02, abs=1e-5)
    assert result.source_revision_id == "scan-a"
    assert result.target_revision_id == "scan-b"
    assert result.source_parent_digest == source.parent_digest
    assert result.target_parent_digest == target.parent_digest
    record = result.as_dict()
    assert record["initialization"]["method"] == "identity"
    assert record["convergence_policy"]["scaling_enabled"] is False
    assert record["coordinate_frames"]["transform_direction"] == "source_to_target"
    assert record["parents"]["source_authority_class"] == "OBJECT_CAPTURE_GEOMETRY"
    assert (source.point_cloud.points, source.parent_digest) == source_before
    assert (target.point_cloud.points, target.parent_digest) == target_before
    assert result.as_dict()["physical_repeat_scan_reproducibility_status"] == (
        "DEFERRED_OWNER_VALIDATION"
    )
    assert result.as_dict()["physical_reproducibility_claim"] is False
    assert result.as_dict()["mold_use_authorized"] is False


def test_identity_registration_is_stable_across_repeated_runs() -> None:
    source = _revision("repeat-a")
    target = _revision("repeat-b")
    first = register_repeat_scans(source, target, policy=_policy())
    second = register_repeat_scans(source, target, policy=_policy())
    assert first.registration_id == second.registration_id
    assert first.transform_source_to_target == second.transform_source_to_target
    assert first.residuals == second.residuals


def test_poor_overlap_returns_non_converged_record_without_claim() -> None:
    source = _revision("poor-a")
    target = _revision("poor-b", _translated(POINTS, (100.0, 100.0, 100.0)))
    result = register_repeat_scans(
        source,
        target,
        policy=_policy(maximum_correspondence_distance=0.01),
    )
    assert result.convergence_status == "NON_CONVERGED_INSUFFICIENT_OVERLAP"
    assert result.inlier_count == 0
    assert result.inlier_rmse is None
    assert result.residuals == ()


def test_scale_state_units_and_parent_authority_are_hard_gates() -> None:
    relative = _revision("relative-a", scale_state=ScaleState.RELATIVE)
    relative_target = _revision("relative-b", scale_state=ScaleState.RELATIVE)
    assert register_repeat_scans(relative, relative_target, policy=_policy()).scale_state is (
        ScaleState.RELATIVE
    )
    with pytest.raises(RegistrationError, match="scale_or_unit_mismatch"):
        register_repeat_scans(relative, _revision("metric-b"), policy=_policy())
    with pytest.raises(RegistrationError, match="generated_or_non_captured"):
        _revision("ai", authority="AI_VISUAL_REFERENCE")
    with pytest.raises(RegistrationError, match="generated_or_non_captured"):
        _revision("generated", generated=True)
    with pytest.raises(RegistrationError, match="project_mismatch"):
        register_repeat_scans(
            _revision("project-a"),
            _revision("project-b", project="different-project"),
            policy=_policy(),
        )


def test_registration_rejects_bad_rigid_initialization_and_stale_parent_state() -> None:
    source = _revision("state-a")
    target = _revision("state-b")
    with pytest.raises(RegistrationError, match="initial_transform_not_rigid"):
        register_repeat_scans(
            source,
            target,
            policy=_policy(),
            initial_transform=(
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ),
        )
    with pytest.raises(RegistrationError, match="coordinate_unit_scale_state_mismatch"):
        replace(source, coordinate_unit="reconstruction_units")
    with pytest.raises(RegistrationError, match="point_samples_digest_mismatch"):
        replace(source, point_cloud=PointCloudData(_translated(POINTS)))


def test_registration_policy_and_point_work_are_bounded() -> None:
    with pytest.raises(RegistrationError, match="work_bound_exceeded"):
        _policy(maximum_iterations=1001)
    many = _revision("many", POINTS)
    with pytest.raises(RegistrationError, match="point_limit_exceeded"):
        register_repeat_scans(
            many, _revision("many-target"), policy=_policy(maximum_points_per_revision=10)
        )


def test_scan_master_mesh_factory_binds_manifest_and_full_parent_digest() -> None:
    mesh = TriangleMeshData(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )
    revision_id = "scan-master:fixture-r1"
    manifest = {
        "scan_master_revision_id": revision_id,
        "authority_class": "SCAN_MASTER",
        "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        "scale_provenance_id": "scale-master-r1",
        "scale_provenance": {
            "provenance_id": "scale-master-r1",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        },
        "project_id": PROJECT,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "output_geometry_sha256": mesh_sha256(mesh),
        "raw_capture_revision_id": "packscan-r1",
        "raw_capture_sha256": hashlib.sha256(b"raw scan").hexdigest(),
        "parent_object_geometry_source_input_digest": hashlib.sha256(b"raw scan").hexdigest(),
        "reconstruction_revision_id": "reconstruction-r1",
        "object_geometry_revision_id": "object-geometry-r1",
        "parent_object_geometry_revision_id": "object-geometry-r1",
        "alignment_transform": {
            "transform": {
                "target_frame": "packlab-normalized-frame-v1",
                "reconstruction_revision": "reconstruction-r1",
            },
            "parents": {"object_capture_geometry_id": "object-geometry-r1"},
        },
    }
    scan_master = ScanMasterRevision(revision_id, PROJECT, mesh, manifest)
    registration_input = RegistrationRevision.from_scan_master(scan_master)
    assert registration_input.authority_class == "SCAN_MASTER"
    assert registration_input.parent_digest == mesh_sha256(mesh)
    assert registration_input.coordinate_frame_id == "packlab-normalized-frame-v1"
    with pytest.raises(RegistrationError, match="manifest_invalid"):
        RegistrationRevision.from_scan_master(
            replace(scan_master, manifest={**manifest, "mold_use_authorized": True})
        )


def test_object_capture_factory_applies_exact_m09_alignment_and_scale_provenance() -> None:
    geometry = _captured_geometry()
    provenance = _scale_provenance()
    registration_input = RegistrationRevision.from_object_capture_geometry(
        geometry,
        _alignment(geometry),
        provenance,
    )
    assert registration_input.revision_id == geometry.geometry_id
    assert registration_input.scale_provenance_id == provenance.provenance_id
    assert registration_input.scale_state is ScaleState.METRIC_UNVERIFIED
    assert registration_input.coordinate_frame_id == "packlab-normalized-frame-v1"
    assert registration_input.point_cloud.points == geometry.filtered_points
