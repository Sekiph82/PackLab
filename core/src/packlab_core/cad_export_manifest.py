"""Canonical privacy-safe manifests shared by M13 CAD engineering exports."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import __version__ as PACKLAB_VERSION
from .cad_adapter import CadRuntimeDiagnostics
from .cad_brep import CadBrepRepresentationRevision
from .cad_validation import CadBrepValidationReport
from .design_model import DesignModelRevision

CAD_EXPORT_MANIFEST_CONTRACT = "packlab.cad-export-manifest.v1"
_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
_FORMATS = frozenset({"step", "stl", "obj", "glb"})


class CadExportManifestError(ValueError):
    """Raised when exact CAD export provenance cannot be recorded safely."""


@dataclass(frozen=True, slots=True)
class CadExportManifest:
    manifest_id: str
    export_id: str
    format: str
    artifact_sha256: str
    artifact_size_bytes: int
    manifest_sha256: str
    canonical_json: bytes

    def as_dict(self) -> dict[str, object]:
        value = json.loads(self.canonical_json)
        if not isinstance(value, dict):
            raise CadExportManifestError("cad_export_manifest_invalid")
        return value


def build_cad_export_manifest(
    *,
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    format: str,
    export_id: str,
    artifact_sha256: str,
    artifact_size_bytes: int,
    validation: CadBrepValidationReport,
    diagnostics: CadRuntimeDiagnostics,
    part_names: tuple[str, ...],
    feature_mapping: tuple[dict[str, object], ...],
    coordinate_transform: dict[str, object],
    tessellation: dict[str, object] | None,
    round_trip_validation: dict[str, object] | None = None,
    limitations: tuple[str, ...],
    packlab_commit: str | None = None,
) -> CadExportManifest:
    """Build stable JSON evidence without recording destination or ambient paths."""
    if format not in _FORMATS:
        raise CadExportManifestError("cad_export_manifest_format_invalid")
    if not isinstance(model, DesignModelRevision):
        raise CadExportManifestError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise CadExportManifestError("cad_brep_representation_required")
    if not isinstance(validation, CadBrepValidationReport):
        raise CadExportManifestError("cad_brep_validation_report_required")
    if not isinstance(diagnostics, CadRuntimeDiagnostics):
        raise CadExportManifestError("cad_runtime_diagnostics_required")
    if (
        representation.source_design_model_revision_id != model.revision_id
        or validation.source_design_model_revision_id != model.revision_id
        or validation.source_brep_revision_id != representation.revision_id
        or validation.parent_authority_revision_id != representation.parent_authority_revision_id
        or not validation.valid_closed_solid
    ):
        raise CadExportManifestError("cad_export_manifest_source_mismatch")
    if (
        representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized is not False
        or validation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or validation.mold_use_authorized is not False
    ):
        raise CadExportManifestError("cad_export_manifest_physical_authority_mismatch")
    if (
        not isinstance(export_id, str)
        or not export_id.strip()
        or not isinstance(artifact_sha256, str)
        or not _SHA_PATTERN.fullmatch(artifact_sha256)
        or not isinstance(artifact_size_bytes, int)
        or isinstance(artifact_size_bytes, bool)
        or artifact_size_bytes < 0
    ):
        raise CadExportManifestError("cad_export_manifest_artifact_identity_invalid")
    if (
        not isinstance(part_names, tuple)
        or any(not isinstance(name, str) or not name.strip() for name in part_names)
        or len(part_names) != len(set(part_names))
    ):
        raise CadExportManifestError("cad_export_manifest_part_names_invalid")
    if not isinstance(feature_mapping, tuple) or any(
        not isinstance(item, dict) for item in feature_mapping
    ):
        raise CadExportManifestError("cad_export_manifest_feature_mapping_invalid")
    if not isinstance(coordinate_transform, dict) or not coordinate_transform:
        raise CadExportManifestError("cad_export_manifest_transform_required")
    if tessellation is not None and not isinstance(tessellation, dict):
        raise CadExportManifestError("cad_export_manifest_tessellation_invalid")
    if round_trip_validation is not None and not isinstance(round_trip_validation, dict):
        raise CadExportManifestError("cad_export_manifest_round_trip_validation_invalid")
    if not isinstance(limitations, tuple) or any(
        not isinstance(item, str) or not item.strip() for item in limitations
    ):
        raise CadExportManifestError("cad_export_manifest_limitations_invalid")
    commit = resolve_packlab_commit() if packlab_commit is None else packlab_commit
    if not isinstance(commit, str) or not _COMMIT_PATTERN.fullmatch(commit):
        raise CadExportManifestError("cad_export_manifest_packlab_commit_unavailable")
    if (
        diagnostics.status.value != "READY"
        or not diagnostics.binding_package
        or not diagnostics.binding_version
        or not diagnostics.kernel_version
    ):
        raise CadExportManifestError("cad_export_manifest_software_version_unavailable")

    parent_field = (
        "root_revision_id"
        if representation.parent_kind.value == "STANDALONE_DESIGN_GEOMETRY"
        else "scan_master_binding_revision_id"
    )
    parent_authority = {
        "kind": representation.parent_kind.value,
        parent_field: representation.parent_authority_revision_id,
    }
    body: dict[str, object] = {
        "project_id": model.project_id,
        "export_id": export_id,
        "format": format,
        "source": {
            "design_model_revision_id": model.revision_id,
            "parent_authority": parent_authority,
            "cad_representation_revision_id": representation.revision_id,
            "cad_geometry_sha256": representation.geometry_sha256,
            "source_operation_id": representation.source_operation_id,
            "coordinate_unit": representation.coordinate_unit,
            "scale_state": representation.scale_state.value,
        },
        "coordinate_transform": coordinate_transform,
        "topology_validation": validation.as_dict(),
        "tessellation": tessellation,
        "software": {
            "packlab_version": PACKLAB_VERSION,
            "packlab_commit": commit,
            "python_binding_package": diagnostics.binding_package,
            "python_binding_version": diagnostics.binding_version,
            "occt_kernel_version": diagnostics.kernel_version,
        },
        "artifact": {
            "sha256": artifact_sha256,
            "byte_length": artifact_size_bytes,
        },
        "part_names": list(part_names),
        "named_feature_mapping": [
            {key: value for key, value in item.items() if key in {"feature_id", "status"}}
            for item in feature_mapping
        ],
        "physical_accuracy_validation_status": representation.physical_accuracy_validation_status,
        "mold_use_authorized": False,
        "limitations": list(limitations),
        "authority_claims": {
            "scan_master_promoted": False,
            "design_model_replaced": False,
            "cad_brep_replaced": False,
            "physical_accuracy_inferred": False,
            "mold_or_manufacturing_suitability_inferred": False,
        },
        # Stable flat aliases retain the fields used by the earlier STEP/STL
        # result records while every format shares the canonical contract.
        "artifact_sha256": artifact_sha256,
        "artifact_size_bytes": artifact_size_bytes,
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "source_brep_geometry_sha256": representation.geometry_sha256,
        "source_operation_id": representation.source_operation_id,
        "parent_kind": representation.parent_kind.value,
        "parent_authority_revision_id": representation.parent_authority_revision_id,
        "scale_state": representation.scale_state.value,
        "coordinate_unit": representation.coordinate_unit,
        "topology_validation_status": validation.status,
        "binding_package": diagnostics.binding_package,
        "binding_version": diagnostics.binding_version,
        "kernel_version": diagnostics.kernel_version,
        "feature_mapping": list(feature_mapping),
    }
    if format == "stl":
        body["artifact_mode"] = "BINARY_STL"
        body["quality"] = tessellation
        body["stl_coordinate_interpretation"] = "millimetres"
        body["millimetres_numerically_encoded_from_unverified_design_units"] = True
        body["print_fit_inferred"] = False
        body["production_ready_claimed"] = False
    if format == "step":
        body["encoded_step_unit"] = "millimetre"
        if round_trip_validation is not None:
            body["round_trip_validation"] = round_trip_validation
    manifest_id = "cad-export-manifest:" + hashlib.sha256(_canonical_json(body)).hexdigest()
    document = {"contract": CAD_EXPORT_MANIFEST_CONTRACT, "manifest_id": manifest_id, **body}
    canonical_json = _canonical_json(document) + b"\n"
    return CadExportManifest(
        manifest_id=manifest_id,
        export_id=export_id,
        format=format,
        artifact_sha256=artifact_sha256,
        artifact_size_bytes=artifact_size_bytes,
        manifest_sha256=hashlib.sha256(canonical_json).hexdigest(),
        canonical_json=canonical_json,
    )


def resolve_packlab_commit() -> str:
    """Return the explicit build commit or the enclosing source checkout HEAD."""
    configured = os.environ.get("PACKLAB_COMMIT")
    if configured is not None:
        if _COMMIT_PATTERN.fullmatch(configured):
            return configured
        raise CadExportManifestError("cad_export_manifest_packlab_commit_invalid")
    repository_root = Path(__file__).resolve().parents[3]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            capture_output=True,
            check=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise CadExportManifestError("cad_export_manifest_packlab_commit_unavailable") from error
    commit = result.stdout.strip()
    if not _COMMIT_PATTERN.fullmatch(commit):
        raise CadExportManifestError("cad_export_manifest_packlab_commit_invalid")
    return commit


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


__all__ = [
    "CAD_EXPORT_MANIFEST_CONTRACT",
    "CadExportManifest",
    "CadExportManifestError",
    "build_cad_export_manifest",
    "resolve_packlab_commit",
]
