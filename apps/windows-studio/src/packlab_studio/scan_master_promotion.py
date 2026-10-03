"""Studio action for core-authorized Scan Master promotion and project persistence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.hole_detection import MeshHoleReport
from packlab_core.proxy_decimation import PreviewProxyRevision
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import (
    CapturedScanLineage,
    CleanupOperationEvidence,
    ScanMasterRevision,
    mesh_sha256,
    promote_scan_master,
)

from .project import ProjectError, ProjectManager, RevisionConflict


class ScanMasterPromotionError(ProjectError):
    """A promotion request or persisted Scan Master artifact is invalid."""


@dataclass(frozen=True, slots=True)
class ScanMasterPromotionRequest:
    lineage: CapturedScanLineage
    parent_revision_id: str
    parent_mesh: TriangleMeshData
    cleanup_operations: tuple[CleanupOperationEvidence, ...]
    final_mesh: TriangleMeshData
    hole_report: MeshHoleReport
    promoted_at_utc: str
    actor_id: str
    reason: str
    known_limitations: tuple[str, ...]
    coverage_gaps: tuple[str, ...]
    preview_proxy: PreviewProxyRevision | None = None


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def _mesh_payload(mesh: TriangleMeshData) -> bytes:
    return _canonical_json(
        {
            "contract": "packlab.scan-master-mesh.v1",
            "vertices": mesh.vertices,
            "triangles": mesh.triangles,
            "vertex_colors": mesh.vertex_colors,
            "vertex_normals": mesh.vertex_normals,
        }
    )


class ScanMasterPromotionAction:
    """Delegates all eligibility decisions to core, then persists its immutable result."""

    def __init__(self, project_manager: ProjectManager) -> None:
        self.project_manager = project_manager

    def promote(
        self, request: ScanMasterPromotionRequest, *, expected_project_revision: int
    ) -> ScanMasterRevision:
        manager = self.project_manager
        if manager.layout is None or manager.metadata is None:
            raise ScanMasterPromotionError("no_project_is_open")
        if expected_project_revision != manager.metadata.revision:
            raise RevisionConflict("editable state revision is stale")
        if request.lineage.project_id != manager.metadata.project_id:
            raise ScanMasterPromotionError("promotion_project_mismatch")

        # Core owns authority, ancestry, digest, cleanup, proxy and deferred-state validation.
        revision = promote_scan_master(
            lineage=request.lineage,
            parent_revision_id=request.parent_revision_id,
            parent_mesh=request.parent_mesh,
            cleanup_operations=request.cleanup_operations,
            final_mesh=request.final_mesh,
            hole_report=request.hole_report,
            promoted_at_utc=request.promoted_at_utc,
            actor_id=request.actor_id,
            promotion_reason=request.reason,
            known_limitations=request.known_limitations,
            coverage_gaps=request.coverage_gaps,
            preview_proxy=request.preview_proxy,
        )
        manager.persist_scan_master_revision(revision, expected_revision=expected_project_revision)
        return revision


def load_scan_master_revision(
    project_manager: ProjectManager, revision_id: str
) -> ScanMasterRevision:
    """Reopen one selected or historical immutable Scan Master with digest checks."""

    if project_manager.layout is None or project_manager.metadata is None:
        raise ScanMasterPromotionError("no_project_is_open")
    return project_manager.load_scan_master_revision(revision_id)


def _validate_revision_payload(
    revision: ScanMasterRevision, manifest: Mapping[str, object], mesh: TriangleMeshData
) -> None:
    if (
        not isinstance(manifest, Mapping)
        or manifest.get("scan_master_revision_id") != revision.revision_id
        or manifest.get("project_id") != revision.project_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or manifest.get("mold_use_authorized") is not False
        or manifest.get("scale_state")
        not in {ScaleState.RELATIVE.value, ScaleState.METRIC_UNVERIFIED.value}
        or not isinstance(manifest.get("scale_provenance_id"), str)
        or not manifest.get("scale_provenance_id")
        or not isinstance(manifest.get("promotion_actor"), str)
        or not manifest.get("promotion_actor")
        or not isinstance(manifest.get("promotion_reason"), str)
        or not manifest.get("promotion_reason")
        or not isinstance(manifest.get("raw_capture_sha256"), str)
        or not isinstance(manifest.get("reconstruction_revision_id"), str)
        or not isinstance(manifest.get("parent_object_geometry_revision_id"), str)
        or manifest.get("output_geometry_sha256") != mesh_sha256(mesh)
    ):
        raise ScanMasterPromotionError("scan_master_manifest_authority_invalid")


__all__ = [
    "ScanMasterPromotionAction",
    "ScanMasterPromotionError",
    "ScanMasterPromotionRequest",
    "load_scan_master_revision",
]
