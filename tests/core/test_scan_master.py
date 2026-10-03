from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from packlab_core.calibration.scale_provenance import ScaleProvenance, ScaleProvenanceError
from packlab_core.coordinate_frame import NormalizedFrameTransform
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.hole_detection import analyze_mesh_holes
from packlab_core.normalization_transform import GeometryNormalizationTransform
from packlab_core.object_mask_lifting import (
    LiftThresholdProfile,
    LiftVisibilityPolicy,
    ObjectCaptureGeometry,
    ObjectMaskLiftError,
)
from packlab_core.proxy_decimation import (
    PreviewProxyRevision,
    ProxyDecimationPolicy,
    ProxyQualityEvidence,
)
from packlab_core.reconstruction import (
    ReconstructionBackendId,
    ReconstructionOutputManifest,
    ScaleState,
)
from packlab_core.scan_master import (
    CapturedScanLineage,
    CleanupOperationEvidence,
    CleanupOperationKind,
    ScanMasterError,
    mesh_sha256,
    promote_scan_master,
)

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
RAW_DIGEST = hashlib.sha256(b"captured PackScan fixture").hexdigest()
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
)


def _scale_provenance() -> ScaleProvenance:
    identity: dict[str, object] = {
        "contract": "packlab.scale-provenance.v1",
        "version": "scale_provenance_v1",
        "source_method": "synthetic-test-scale",
        "calibration_observation_ids": [],
        "physical_references": [],
        "estimated_scale_factor": 0.4,
        "scale_factor_unit": "mm_per_reconstruction_unit",
        "residuals": [],
        "rejected_observations": [],
        "algorithm_version": "fixture-v1",
        "outlier_policy_version": "fixture-v1",
        "input_reconstruction_revision": "reconstruction-r1",
        "camera_solution_revision": "camera-r1",
        "uncertainty": {"representation": "fixture", "value": 0.01},
        "created_at_utc": "2026-10-02T10:00:00Z",
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
        0.4,
        (),
        (),
        "fixture-v1",
        "fixture-v1",
        "reconstruction-r1",
        "camera-r1",
        {"representation": "fixture", "value": 0.01},
        "2026-10-02T10:00:00Z",
        "fixture",
        "fixture",
        ScaleState.METRIC_UNVERIFIED,
    )


def _lineage(*, authority: str = "OBJECT_CAPTURE_GEOMETRY") -> CapturedScanLineage:
    scale = _scale_provenance()
    geometry = ObjectCaptureGeometry(
        geometry_id="object-geometry-r1",
        project_id=PROJECT,
        source_revision="packscan-r1",
        source_input_digest=RAW_DIGEST,
        source_images=(),
        source_mask_artifacts=(),
        camera_conventions=(),
        camera_evidence=(),
        reconstruction_revision="reconstruction-r1",
        camera_solution_revision="camera-r1",
        mask_set_revision_id="mask-set-r1",
        mask_set_revision_digest=hashlib.sha256(b"mask-set").hexdigest(),
        projection_convention="fixture-camera-v1",
        projection_version="fixture-v1",
        threshold_profile=LiftThresholdProfile(),
        visibility_policy=LiftVisibilityPolicy(),
        outlier_policy="fixture-v1",
        candidate_count=4,
        point_count=4,
        generated=False,
        authority_class=authority,
        scale_state=ScaleState.RELATIVE,
        point_votes=(),
        filtered_points=MESH.vertices,
        unfiltered_points=MESH.vertices,
        obb=None,
        created_at="2026-10-02T10:00:00Z",
    )
    reconstruction = ReconstructionOutputManifest(
        project_id=PROJECT,
        reconstruction_revision="reconstruction-r1",
        backend_id=ReconstructionBackendId.COLMAP_OPENMVS,
        backend_version="fixture-v1",
        backend_build="fixture",
        backend_license="fixture",
        configuration_digest=hashlib.sha256(b"config").hexdigest(),
        source_input_digest=RAW_DIGEST,
        camera_convention="world-to-camera",
    )
    frame = NormalizedFrameTransform(
        transform_id="aligned-frame-r1",
        source_frame="captured-object-v1",
        target_frame="aligned-captured-object-v1",
        reconstruction_revision="reconstruction-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        input_unit="mm_unverified",
        coordinate_unit="mm_unverified",
        matrix=(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0),
        method="fixture-alignment-v1",
        scale_provenance_id="scale-estimate:" + "a" * 64,
    )
    alignment = GeometryNormalizationTransform(
        frame,
        geometry.geometry_id,
        "a" * 64,
        0.4,
        0.01,
        "base-plane-r1",
        "upright-r1",
        "front-r1",
        ScaleState.RELATIVE,
    )
    return CapturedScanLineage(
        PROJECT,
        "packscan-r1",
        RAW_DIGEST,
        reconstruction,
        geometry,
        scale,
        alignment,
        "aligned-mesh-r1",
        MESH,
    )


def _noop_cleanup() -> CleanupOperationEvidence:
    digest = mesh_sha256(MESH)
    return CleanupOperationEvidence(
        "cleanup-review-r1",
        CleanupOperationKind.NO_OP,
        "aligned-mesh-r1",
        digest,
        MESH,
        "cleanup-reviewed-r1",
        digest,
        MESH,
        {"disposition": "no_geometry_change_required"},
    )


def _report(mesh=MESH, revision="cleanup-reviewed-r1"):
    return analyze_mesh_holes(
        mesh,
        parent_revision_id=revision,
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id=_scale_provenance().provenance_id,
        uncertain_vertex_indices=(),
        coverage_gap_vertex_indices=(),
    )


def _promote(**overrides):
    values = {
        "lineage": _lineage(),
        "parent_revision_id": "aligned-mesh-r1",
        "parent_mesh": MESH,
        "cleanup_operations": (_noop_cleanup(),),
        "final_mesh": MESH,
        "hole_report": _report(),
        "promoted_at_utc": "2026-10-02T11:00:00Z",
        "actor_id": "operator-1",
        "promotion_reason": "Operator reviewed captured scan and cleanup lineage.",
        "known_limitations": ("synthetic fixture; no physical accuracy validation",),
        "coverage_gaps": ("synthetic fixture has no measured scan coverage",),
    }
    values.update(overrides)
    return promote_scan_master(**values)


def test_eligible_captured_ancestry_creates_complete_deferred_scan_master() -> None:
    parent_snapshot = (MESH.vertices, MESH.triangles)
    result = _promote()
    manifest = result.manifest
    assert manifest["authority_class"] == "SCAN_MASTER"
    assert manifest["raw_capture_revision_id"] == "packscan-r1"
    assert manifest["reconstruction_revision_id"] == "reconstruction-r1"
    assert manifest["parent_object_geometry_revision_id"] == "object-geometry-r1"
    assert manifest["mask_set_revision_id"] == "mask-set-r1"
    assert manifest["scale_provenance_id"] == _scale_provenance().provenance_id
    assert manifest["alignment_transform"]["transform"]["transform_id"] == "aligned-frame-r1"
    assert manifest["source_geometry_sha256"] == mesh_sha256(MESH)
    assert manifest["output_geometry_sha256"] == mesh_sha256(result.mesh)
    assert manifest["hole_report"]["report_id"] == _report().report_id
    assert manifest["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert manifest["mold_use_authorized"] is False
    assert manifest["scale_state"] == ScaleState.METRIC_UNVERIFIED.value
    assert manifest["coverage_gaps"] == ("synthetic fixture has no measured scan coverage",)
    with pytest.raises(TypeError):
        manifest["coverage_gaps"][0] = "rewritten"
    with pytest.raises(TypeError):
        manifest["authority_class"] = "AI_VISUAL_REFERENCE"
    assert (MESH.vertices, MESH.triangles) == parent_snapshot


def test_generated_ai_or_wrong_captured_authority_is_rejected() -> None:
    generated = _lineage()
    object.__setattr__(generated.object_geometry, "generated", True)
    with pytest.raises(ScanMasterError, match="generated_or_non_captured_geometry_forbidden"):
        CapturedScanLineage(
            **{field: getattr(generated, field) for field in generated.__dataclass_fields__}
        )
    with pytest.raises(ObjectMaskLiftError, match="mask lift output must remain"):
        _lineage(authority="AI_VISUAL_REFERENCE")


def test_raw_digest_or_reconstruction_parent_mismatch_is_rejected() -> None:
    lineage = _lineage()
    with pytest.raises(ScanMasterError, match="raw_capture_digest_lineage_mismatch"):
        CapturedScanLineage(
            lineage.project_id,
            lineage.raw_capture_revision_id,
            "0" * 64,
            lineage.reconstruction,
            lineage.object_geometry,
            lineage.scale_provenance,
            lineage.alignment,
            lineage.aligned_mesh_revision_id,
            lineage.aligned_mesh,
        )


def test_cleanup_chain_and_hole_report_must_bind_to_final_full_mesh() -> None:
    with pytest.raises(ScanMasterError, match="m10_cleanup_revision_required"):
        _promote(cleanup_operations=(), hole_report=_report(revision="aligned-mesh-r1"))
    digest = mesh_sha256(MESH)
    operation = CleanupOperationEvidence(
        "cleanup-op-1",
        CleanupOperationKind.SMOOTHING,
        "aligned-mesh-r1",
        digest,
        MESH,
        "cleaned-mesh-r1",
        digest,
        MESH,
        {"iterations": 1, "relaxation": 0.1},
    )
    result = _promote(
        cleanup_operations=(operation,),
        hole_report=_report(revision="cleaned-mesh-r1"),
    )
    assert result.manifest["cleanup_operations"][0]["parameters"] == {
        "iterations": 1,
        "relaxation": 0.1,
    }
    broken = replace(operation, parent_revision_id="other-parent")
    with pytest.raises(ScanMasterError, match="cleanup_lineage_disconnected"):
        _promote(cleanup_operations=(broken,))
    with pytest.raises(ScanMasterError, match="hole_report_final_parent_mismatch"):
        _promote(
            cleanup_operations=(operation,),
            hole_report=_report(revision="aligned-mesh-r1"),
        )


def test_proxy_can_only_be_linked_to_full_final_parent_never_promoted() -> None:
    digest = mesh_sha256(MESH)
    proxy = PreviewProxyRevision(
        "packlab.preview-proxy-decimation.v1",
        "PREVIEW_PROXY",
        False,
        "cleanup-reviewed-r1",
        digest,
        "proxy-r1",
        mesh_sha256(MESH),
        MESH,
        MESH,
        ProxyDecimationPolicy(2),
        ProxyQualityEvidence(4, 4, 4, 4, 2, False, 0.0, 0.0, 0.0, 0.0, 0.0, (0.0, 0.0, 0.0)),
        "UNAVAILABLE",
        "SUCCEEDED",
        ScaleState.METRIC_UNVERIFIED,
        _scale_provenance().provenance_id,
        "DEFERRED_OWNER_VALIDATION",
        False,
    )
    result = _promote(preview_proxy=proxy)
    assert result.mesh is MESH
    assert result.manifest["preview_proxy"]["proxy_revision_id"] == "proxy-r1"
    wrong_parent = replace(proxy, full_parent_revision_id="proxy-r1")
    with pytest.raises(ScanMasterError, match="preview_proxy_parent_mismatch"):
        _promote(preview_proxy=wrong_parent)


def test_revision_identity_is_deterministic_and_excludes_actor_timestamp() -> None:
    first = _promote()
    second = _promote(promoted_at_utc="2026-10-02T12:00:00Z", actor_id="operator-2")
    assert first.revision_id == second.revision_id
    assert first.manifest_bytes() != second.manifest_bytes()


def test_promotion_reason_is_required_bounded_and_bound_to_revision_identity() -> None:
    first = _promote()
    assert (
        first.manifest["promotion_reason"] == "Operator reviewed captured scan and cleanup lineage."
    )
    assert _promote(actor_id="operator-2").revision_id == first.revision_id
    assert (
        _promote(promotion_reason="Different reviewed disposition.").revision_id
        != first.revision_id
    )
    for reason in ("", "  ", " leading", "trailing ", "x" * 1001):
        with pytest.raises(ScanMasterError, match="promotion_reason_invalid"):
            _promote(promotion_reason=reason)


def test_promoted_mesh_digest_and_scale_state_cannot_be_forged() -> None:
    changed = TriangleMeshData(MESH.vertices, ((0, 1, 2), (0, 1, 3), (1, 2, 3), (2, 0, 3)))
    with pytest.raises(ScanMasterError, match="final_mesh_digest_mismatch"):
        _promote(final_mesh=changed)
    with pytest.raises(ScaleProvenanceError, match="requires_owner_evidence"):
        replace(_scale_provenance(), scale_state=ScaleState.METRIC_VERIFIED)
