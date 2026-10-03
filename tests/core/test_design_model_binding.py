from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from packlab_core.design_model_binding import (
    DesignModelBindingError,
    ParentBindingStatus,
    bind_design_model_parent,
    inspect_design_model_parent,
    rebind_design_model_parent,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _scan_master(suffix: str, reconstruction: str = "reconstruction-r1") -> ScanMasterRevision:
    revision_id = f"scan-master:{hashlib.sha256(suffix.encode()).hexdigest()}"
    manifest = {
        "scan_master_revision_id": revision_id,
        "project_id": PROJECT,
        "authority_class": "SCAN_MASTER",
        "output_geometry_sha256": mesh_sha256(MESH),
        "reconstruction_revision_id": reconstruction,
        "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        "scale_provenance_id": "scale-provenance:r1",
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
    }
    return ScanMasterRevision(revision_id, PROJECT, MESH, manifest)


def _binding(scan: ScanMasterRevision | None = None):
    return bind_design_model_parent(
        _scan_master("sm-1") if scan is None else scan,
        actor_id="operator-1",
        reason="Initial exact Scan Master selection.",
        created_at_utc="2026-10-03T11:00:00Z",
    )


def test_parent_binding_is_deterministic_and_pins_exact_id_digest_and_scale() -> None:
    scan = _scan_master("sm-1")
    first = _binding(scan)
    repeat = bind_design_model_parent(
        scan,
        actor_id="operator-2",
        reason="Initial exact Scan Master selection.",
        created_at_utc="2026-10-03T12:00:00Z",
    )
    assert first.revision_id == repeat.revision_id
    assert first.fitted_to_scan_master_revision_id == scan.revision_id
    assert first.scan_master_geometry_sha256 == mesh_sha256(scan.mesh)
    assert first.scale_state is ScaleState.METRIC_UNVERIFIED
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False


def test_new_scan_master_and_reconstruction_do_not_retarget_existing_binding() -> None:
    pinned = _scan_master("sm-1")
    newer = _scan_master("sm-2", reconstruction="reconstruction-r2")
    binding = _binding(pinned)
    status = inspect_design_model_parent(
        binding,
        available_scan_masters=(pinned, newer),
        latest_scan_master_revision_id=newer.revision_id,
        latest_reconstruction_revision_id="reconstruction-r2",
    )
    assert status.status is ParentBindingStatus.NEWER_SCAN_MASTER_AND_RECONSTRUCTION_AVAILABLE
    assert status.stale is True
    assert status.pinned_parent_available is True
    assert status.newer_scan_master_available is True
    assert status.newer_reconstruction_available is True
    assert status.bound_scan_master_revision_id == pinned.revision_id
    assert binding.fitted_to_scan_master_revision_id == pinned.revision_id


def test_explicit_rebind_creates_new_identity_and_preserves_original_revision() -> None:
    original = _binding(_scan_master("sm-1"))
    original_snapshot = original.as_dict()
    newer = _scan_master("sm-2", reconstruction="reconstruction-r2")
    rebound = rebind_design_model_parent(
        original,
        newer,
        expected_current_binding_revision_id=original.revision_id,
        actor_id="operator-2",
        reason="Owner explicitly selected the newer Scan Master.",
        created_at_utc="2026-10-03T12:00:00Z",
    )
    assert rebound.revision_id != original.revision_id
    assert rebound.previous_binding_revision_id == original.revision_id
    assert rebound.fitted_to_scan_master_revision_id == newer.revision_id
    assert original.as_dict() == original_snapshot


def test_missing_parent_stale_binding_and_unknown_latest_are_rejected() -> None:
    with pytest.raises(DesignModelBindingError, match="scan_master_parent_missing"):
        bind_design_model_parent(
            None,
            actor_id="operator-1",
            reason="Initial exact Scan Master selection.",
            created_at_utc="2026-10-03T11:00:00Z",
        )
    binding = _binding(_scan_master("sm-1"))
    newer = _scan_master("sm-2", reconstruction="reconstruction-r2")
    status = inspect_design_model_parent(
        binding,
        available_scan_masters=(newer,),
        latest_scan_master_revision_id=newer.revision_id,
        latest_reconstruction_revision_id="reconstruction-r2",
    )
    assert status.status is ParentBindingStatus.PINNED_PARENT_MISSING
    with pytest.raises(DesignModelBindingError, match="latest_scan_master_revision_missing"):
        inspect_design_model_parent(
            binding,
            available_scan_masters=(newer,),
            latest_scan_master_revision_id="scan-master:missing",
            latest_reconstruction_revision_id="reconstruction-r2",
        )
    with pytest.raises(DesignModelBindingError, match="design_model_binding_revision_stale"):
        rebind_design_model_parent(
            binding,
            newer,
            expected_current_binding_revision_id="stale-binding",
            actor_id="operator-2",
            reason="Explicit rebind.",
            created_at_utc="2026-10-03T12:00:00Z",
        )


def test_generated_metric_verified_mold_authorized_and_tampered_parents_fail_closed() -> None:
    generated = _scan_master("generated")
    object.__setattr__(
        generated, "manifest", {**generated.manifest, "authority_class": "AI_VISUAL_REFERENCE"}
    )
    with pytest.raises(DesignModelBindingError, match="scan_master_parent_authority_invalid"):
        _binding(generated)
    metric_verified = _scan_master("verified")
    object.__setattr__(
        metric_verified,
        "manifest",
        {**metric_verified.manifest, "scale_state": ScaleState.METRIC_VERIFIED.value},
    )
    with pytest.raises(DesignModelBindingError, match="scan_master_parent_authority_invalid"):
        _binding(metric_verified)
    binding = _binding()
    with pytest.raises(DesignModelBindingError, match="design_model_binding_revision_id_mismatch"):
        replace(binding, fitted_to_scan_master_revision_id="scan-master:tampered")
