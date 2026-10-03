"""Captured-evidence-only Scan Master promotion and immutable provenance."""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType

from .calibration.scale_provenance import ScaleProvenance
from .geometry_adapter import TriangleMeshData
from .hole_detection import MeshHoleReport
from .normalization_transform import GeometryNormalizationTransform
from .object_mask_lifting import ObjectCaptureGeometry
from .proxy_decimation import PreviewProxyRevision
from .reconstruction import ReconstructionOutputManifest, ScaleState

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ScanMasterError(ValueError):
    """Raised when captured geometry cannot be promoted safely."""


class CleanupOperationKind(StrEnum):
    NO_OP = "no_op_review"
    COMPONENT_CLEANUP = "component_cleanup"
    NORMAL_REPAIR = "normal_repair"
    SMOOTHING = "smoothing"
    HOLE_FILLING = "hole_filling"


def mesh_sha256(mesh: TriangleMeshData) -> str:
    """Return a stable digest of geometry and supported vertex attributes."""

    payload = {
        "vertices": mesh.vertices,
        "triangles": mesh.triangles,
        "vertex_colors": mesh.vertex_colors,
        "vertex_normals": mesh.vertex_normals,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _identifier(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ScanMasterError(f"{field}_invalid")
    if any(ord(character) < 32 for character in value):
        raise ScanMasterError(f"{field}_invalid")


def _digest(value: str, field: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ScanMasterError(f"{field}_invalid")


def _freeze_json(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _utc_timestamp(value: str) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ScanMasterError("promoted_at_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ScanMasterError("promoted_at_invalid") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ScanMasterError("promoted_at_must_be_utc_z")


@dataclass(frozen=True, slots=True)
class CleanupOperationEvidence:
    """A single parent-bound M10 revision in the final full-mesh chain."""

    operation_id: str
    kind: CleanupOperationKind
    parent_revision_id: str
    parent_geometry_sha256: str
    parent_mesh: TriangleMeshData
    output_revision_id: str
    output_geometry_sha256: str
    output_mesh: TriangleMeshData
    parameters: Mapping[str, object]

    def __post_init__(self) -> None:
        _identifier(self.operation_id, "cleanup_operation_id")
        _identifier(self.parent_revision_id, "cleanup_parent_revision")
        _identifier(self.output_revision_id, "cleanup_output_revision")
        _digest(self.parent_geometry_sha256, "cleanup_parent_digest")
        _digest(self.output_geometry_sha256, "cleanup_output_digest")
        if mesh_sha256(self.parent_mesh) != self.parent_geometry_sha256:
            raise ScanMasterError("cleanup_parent_mesh_digest_mismatch")
        if mesh_sha256(self.output_mesh) != self.output_geometry_sha256:
            raise ScanMasterError("cleanup_output_mesh_digest_mismatch")
        if not isinstance(self.kind, CleanupOperationKind):
            raise ScanMasterError("cleanup_operation_kind_invalid")
        try:
            frozen = json.loads(json.dumps(dict(self.parameters), sort_keys=True, allow_nan=False))
        except (TypeError, ValueError) as error:
            raise ScanMasterError("cleanup_parameters_not_json_safe") from error
        if not isinstance(frozen, dict):
            raise ScanMasterError("cleanup_parameters_invalid")
        object.__setattr__(self, "parameters", _freeze_json(frozen))

    def as_dict(self) -> dict[str, object]:
        return {
            "operation_id": self.operation_id,
            "kind": self.kind.value,
            "parent_revision_id": self.parent_revision_id,
            "parent_geometry_sha256": self.parent_geometry_sha256,
            "output_revision_id": self.output_revision_id,
            "output_geometry_sha256": self.output_geometry_sha256,
            "parameters": _thaw_json(self.parameters),
        }


@dataclass(frozen=True, slots=True)
class CapturedScanLineage:
    """Typed input facts needed to traverse immutable PackScan ancestry."""

    project_id: str
    raw_capture_revision_id: str
    raw_capture_sha256: str
    reconstruction: ReconstructionOutputManifest
    object_geometry: ObjectCaptureGeometry
    scale_provenance: ScaleProvenance
    alignment: GeometryNormalizationTransform
    aligned_mesh_revision_id: str
    aligned_mesh: TriangleMeshData

    def __post_init__(self) -> None:
        try:
            canonical_project_id = str(uuid.UUID(self.project_id))
        except (ValueError, TypeError, AttributeError) as error:
            raise ScanMasterError("project_id_must_be_uuid") from error
        if canonical_project_id != self.project_id:
            raise ScanMasterError("project_id_must_be_canonical_uuid")
        _identifier(self.raw_capture_revision_id, "raw_capture_revision")
        _digest(self.raw_capture_sha256, "raw_capture_digest")
        _identifier(self.aligned_mesh_revision_id, "aligned_mesh_revision")
        geometry = self.object_geometry
        reconstruction = self.reconstruction
        scale = self.scale_provenance
        if geometry.generated is not False or geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY":
            raise ScanMasterError("generated_or_non_captured_geometry_forbidden")
        if reconstruction.authority_class != "RECONSTRUCTION_OBSERVATION":
            raise ScanMasterError("reconstruction_authority_invalid")
        if reconstruction.project_id != self.project_id or geometry.project_id != self.project_id:
            raise ScanMasterError("project_lineage_mismatch")
        if geometry.source_revision != self.raw_capture_revision_id:
            raise ScanMasterError("raw_capture_parent_mismatch")
        if (
            reconstruction.source_input_digest != self.raw_capture_sha256
            or geometry.source_input_digest != self.raw_capture_sha256
        ):
            raise ScanMasterError("raw_capture_digest_lineage_mismatch")
        if geometry.reconstruction_revision != reconstruction.reconstruction_revision:
            raise ScanMasterError("reconstruction_parent_mismatch")
        if geometry.scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
            raise ScanMasterError("captured_geometry_scale_state_ineligible")
        if scale.scale_state is not self.alignment.transform.scale_state:
            raise ScanMasterError("scale_state_mismatch")
        if self.alignment.original_scale_state is not geometry.scale_state:
            raise ScanMasterError("alignment_input_scale_state_mismatch")
        if scale.input_reconstruction_revision != reconstruction.reconstruction_revision:
            raise ScanMasterError("scale_provenance_reconstruction_mismatch")
        if self.alignment.geometry_id != geometry.geometry_id:
            raise ScanMasterError("alignment_geometry_parent_mismatch")
        if (
            self.alignment.transform.reconstruction_revision
            != reconstruction.reconstruction_revision
        ):
            raise ScanMasterError("alignment_reconstruction_parent_mismatch")
        if len(self.alignment.matrix) != 16 or any(
            not math.isfinite(value) for value in self.alignment.matrix
        ):
            raise ScanMasterError("alignment_transform_invalid")


@dataclass(frozen=True, slots=True)
class ScanMasterRevision:
    """Immutable full-resolution promoted captured geometry."""

    revision_id: str
    project_id: str
    mesh: TriangleMeshData
    manifest: Mapping[str, object]
    _manifest_json: bytes = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        encoded = json.dumps(
            self.manifest, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        object.__setattr__(self, "_manifest_json", encoded)
        object.__setattr__(self, "manifest", _freeze_json(dict(self.manifest)))

    def manifest_bytes(self) -> bytes:
        return self._manifest_json


def promote_scan_master(
    *,
    lineage: CapturedScanLineage,
    parent_revision_id: str,
    parent_mesh: TriangleMeshData,
    cleanup_operations: tuple[CleanupOperationEvidence, ...],
    final_mesh: TriangleMeshData,
    hole_report: MeshHoleReport,
    promoted_at_utc: str,
    actor_id: str,
    promotion_reason: str,
    known_limitations: tuple[str, ...],
    coverage_gaps: tuple[str, ...],
    preview_proxy: PreviewProxyRevision | None = None,
) -> ScanMasterRevision:
    """Create a deterministic Scan Master revision without mutating its parents."""

    _identifier(parent_revision_id, "parent_revision")
    _identifier(actor_id, "promotion_actor")
    if (
        not isinstance(promotion_reason, str)
        or not promotion_reason.strip()
        or promotion_reason != promotion_reason.strip()
        or len(promotion_reason) > 1000
        or any(ord(character) < 32 and character not in "\t\n" for character in promotion_reason)
    ):
        raise ScanMasterError("promotion_reason_invalid")
    _utc_timestamp(promoted_at_utc)
    if not isinstance(lineage, CapturedScanLineage):
        raise ScanMasterError("captured_lineage_required")
    if not isinstance(cleanup_operations, tuple):
        raise ScanMasterError("cleanup_operations_must_be_tuple")
    if not cleanup_operations:
        raise ScanMasterError("m10_cleanup_revision_required")
    limitations = tuple(known_limitations)
    gaps = tuple(coverage_gaps)
    if any(not isinstance(item, str) or not item.strip() for item in limitations):
        raise ScanMasterError("known_limitations_invalid")
    if not limitations:
        raise ScanMasterError("known_limitations_required")
    if any(not isinstance(item, str) or not item.strip() for item in gaps):
        raise ScanMasterError("coverage_gaps_invalid")
    if not isinstance(hole_report, MeshHoleReport):
        raise ScanMasterError("hole_report_required")

    start_digest = mesh_sha256(parent_mesh)
    if parent_revision_id != lineage.aligned_mesh_revision_id or start_digest != mesh_sha256(
        lineage.aligned_mesh
    ):
        raise ScanMasterError("aligned_mesh_parent_mismatch")
    current_revision = parent_revision_id
    current_digest = start_digest
    current_mesh = parent_mesh
    for operation in cleanup_operations:
        if not isinstance(operation, CleanupOperationEvidence):
            raise ScanMasterError("cleanup_operation_evidence_invalid")
        if (
            operation.parent_revision_id != current_revision
            or operation.parent_geometry_sha256 != current_digest
            or mesh_sha256(operation.parent_mesh) != current_digest
        ):
            raise ScanMasterError("cleanup_lineage_disconnected")
        current_revision = operation.output_revision_id
        current_digest = operation.output_geometry_sha256
        current_mesh = operation.output_mesh
    output_digest = mesh_sha256(final_mesh)
    if current_digest != output_digest or mesh_sha256(current_mesh) != output_digest:
        raise ScanMasterError("final_mesh_digest_mismatch")
    if (
        hole_report.parent_revision_id != current_revision
        or hole_report.parent_geometry_sha256 != output_digest
        or hole_report.scale_state is not lineage.scale_provenance.scale_state
        or hole_report.scale_provenance_id != lineage.scale_provenance.provenance_id
    ):
        raise ScanMasterError("hole_report_final_parent_mismatch")
    if (
        hole_report.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or hole_report.mold_use_authorized is not False
    ):
        raise ScanMasterError("hole_report_physical_authority_mismatch")
    output_scale = lineage.scale_provenance.scale_state
    if output_scale is ScaleState.METRIC_VERIFIED:
        raise ScanMasterError("metric_verified_requires_deferred_frontier_closure")
    proxy_manifest: dict[str, object] | None = None
    if preview_proxy is not None:
        if (
            preview_proxy.authority_class != "PREVIEW_PROXY"
            or preview_proxy.scan_master_eligible is not False
            or preview_proxy.full_parent_revision_id != current_revision
            or preview_proxy.full_parent_geometry_sha256 != output_digest
        ):
            raise ScanMasterError("preview_proxy_parent_mismatch")
        if (
            mesh_sha256(preview_proxy.full_parent_mesh) != output_digest
            or mesh_sha256(preview_proxy.proxy_mesh) != preview_proxy.proxy_geometry_sha256
            or preview_proxy.scale_state is not output_scale
            or preview_proxy.scale_provenance_id != lineage.scale_provenance.provenance_id
            or preview_proxy.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
            or preview_proxy.mold_use_authorized is not False
        ):
            raise ScanMasterError("preview_proxy_evidence_mismatch")
        proxy_manifest = {
            **preview_proxy.as_dict(),
            "relationship": "preview_of_full_scan_master_parent",
        }
    cleanup_manifest = [item.as_dict() for item in cleanup_operations]
    identity_body: dict[str, object] = {
        "contract": "packlab.scan-master.v1",
        "project_id": lineage.project_id,
        "raw_capture_revision_id": lineage.raw_capture_revision_id,
        "raw_capture_sha256": lineage.raw_capture_sha256,
        "reconstruction_revision_id": lineage.reconstruction.reconstruction_revision,
        "object_geometry_revision_id": lineage.object_geometry.geometry_id,
        "mask_set_revision_id": lineage.object_geometry.mask_set_revision_id,
        "scale_provenance_id": lineage.scale_provenance.provenance_id,
        "alignment_transform": lineage.alignment.as_dict(),
        "parent_mesh_revision_id": parent_revision_id,
        "source_geometry_sha256": start_digest,
        "cleanup_operations": cleanup_manifest,
        "hole_report": {
            "report_id": hole_report.report_id,
            "parent_revision_id": hole_report.parent_revision_id,
            "parent_geometry_sha256": hole_report.parent_geometry_sha256,
            "report": hole_report.as_dict(),
        },
        "output_geometry_sha256": output_digest,
        "authority_class": "SCAN_MASTER",
        "scale_state": output_scale.value,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "known_limitations": list(limitations),
        "coverage_gaps": list(gaps),
        "promotion_reason": promotion_reason,
        "preview_proxy": proxy_manifest,
    }
    digest = hashlib.sha256(
        json.dumps(identity_body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
            "utf-8"
        )
    ).hexdigest()
    revision_id = f"scan-master:{digest}"
    manifest = {
        **identity_body,
        "scan_master_revision_id": revision_id,
        "promoted_at_utc": promoted_at_utc,
        "promotion_actor": actor_id,
        "promotion_reason": promotion_reason,
        "parent_object_geometry_revision_id": lineage.object_geometry.geometry_id,
        "parent_object_geometry_source_input_digest": lineage.object_geometry.source_input_digest,
        "mask_set_digest": lineage.object_geometry.mask_set_revision_digest,
        "scale_provenance": lineage.scale_provenance.as_dict(),
        "alignment_transform": lineage.alignment.as_dict(),
    }
    return ScanMasterRevision(revision_id, lineage.project_id, final_mesh, manifest)
