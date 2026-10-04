"""Bounded binary STL export with an explicit millimetre and provenance sidecar."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .cad_adapter import CadAdapterError, probe_cad_runtime, tessellate_cad_shape
from .cad_brep import CadBrepRepresentationRevision
from .cad_feature_map import map_design_model_features_to_brep
from .cad_validation import validate_cad_brep
from .design_model import DesignModelRevision
from .reconstruction import ScaleState

CAD_STL_EXPORT_CONTRACT = "packlab.cad-stl-export.v1"
_STL_HEADER = b"PackLab derived preview; mm_unverified; physical accuracy unverified"
_MESH_PRESETS: dict[str, tuple[float, float]] = {
    "COARSE": (0.5, 0.8),
    "STANDARD": (0.1, 0.5),
    "FINE": (0.02, 0.15),
}


class CadStlExportError(ValueError):
    """Raised when a BREP cannot safely produce a unit-declared STL artifact."""


class CadStlMeshQuality(StrEnum):
    COARSE = "COARSE"
    STANDARD = "STANDARD"
    FINE = "FINE"


@dataclass(frozen=True, slots=True)
class CadStlExportRevision:
    export_id: str
    artifact_sha256: str
    artifact_size_bytes: int
    sidecar_sha256: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    source_operation_id: str
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    binding_package: str
    binding_version: str
    kernel_version: str
    quality_preset: str
    linear_deflection: float
    angular_deflection: float
    maximum_vertices: int
    maximum_triangles: int
    maximum_faces: int
    source_face_count: int
    vertex_count: int
    triangle_count: int
    topology_validation_status: str
    feature_mapping: tuple[dict[str, object], ...]
    contract: str = CAD_STL_EXPORT_CONTRACT
    authority_class: str = "DERIVED_PRINTABLE_STL_EXPORT"
    artifact_mode: str = "BINARY_STL"

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": self.authority_class,
            "export_id": self.export_id,
            "artifact_mode": self.artifact_mode,
            "artifact_sha256": self.artifact_sha256,
            "artifact_size_bytes": self.artifact_size_bytes,
            "sidecar_sha256": self.sidecar_sha256,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_brep_geometry_sha256": self.source_brep_geometry_sha256,
            "source_operation_id": self.source_operation_id,
            "binding_package": self.binding_package,
            "binding_version": self.binding_version,
            "kernel_version": self.kernel_version,
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "stl_coordinate_interpretation": "millimetres",
            "millimetres_numerically_encoded_from_unverified_design_units": True,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "topology_validation_status": self.topology_validation_status,
            "quality": {
                "preset": self.quality_preset,
                "linear_deflection": self.linear_deflection,
                "angular_deflection_radians": self.angular_deflection,
                "maximum_vertices": self.maximum_vertices,
                "maximum_triangles": self.maximum_triangles,
                "maximum_faces": self.maximum_faces,
                "source_face_count": self.source_face_count,
                "vertex_count": self.vertex_count,
                "triangle_count": self.triangle_count,
            },
            "feature_mapping": list(self.feature_mapping),
            "disposable_export": True,
            "scan_master_promoted": False,
            "design_model_replaced": False,
            "cad_brep_replaced": False,
            "physical_accuracy_inferred": False,
            "print_fit_inferred": False,
            "production_ready_claimed": False,
            "manufacturing_suitability_inferred": False,
            "limitations": [
                "stl_has_no_reliable_embedded_unit_metadata",
                "sidecar_must_remain_with_artifact_to_interpret_coordinates_as_mm",
                "mesh_tolerance_is_not_physical_accuracy_or_print_fit_evidence",
            ],
        }


def export_design_model_stl(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    output_path: str | Path,
    *,
    quality: CadStlMeshQuality = CadStlMeshQuality.STANDARD,
    maximum_vertices: int = 250_000,
    maximum_triangles: int = 500_000,
    maximum_faces: int = 10_000,
) -> CadStlExportRevision:
    """Write deterministic binary STL and mandatory JSON sidecar from one valid BREP."""
    if not isinstance(model, DesignModelRevision):
        raise CadStlExportError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise CadStlExportError("cad_brep_representation_required")
    if representation.source_design_model_revision_id != model.revision_id:
        raise CadStlExportError("cad_stl_model_revision_mismatch")
    if representation.parent_kind is not model.parent_kind:
        raise CadStlExportError("cad_stl_parent_authority_mismatch")
    parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if representation.parent_authority_revision_id != parent_revision:
        raise CadStlExportError("cad_stl_parent_revision_mismatch")
    if representation.scale_state is not ScaleState.METRIC_UNVERIFIED:
        raise CadStlExportError("cad_stl_mm_unverified_source_required")
    if representation.coordinate_unit != "mm_unverified":
        raise CadStlExportError("cad_stl_mm_unverified_unit_required")
    if (
        representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized is not False
    ):
        raise CadStlExportError("cad_stl_physical_authority_mismatch")
    try:
        preset = CadStlMeshQuality(quality)
    except (TypeError, ValueError) as error:
        raise CadStlExportError("cad_stl_mesh_quality_invalid") from error
    linear_deflection, angular_deflection = _MESH_PRESETS[preset.value]
    try:
        validation = validate_cad_brep(representation)
    except Exception as error:
        raise CadStlExportError("cad_stl_brep_validation_failed") from error
    if not validation.valid_closed_solid:
        raise CadStlExportError("cad_stl_valid_closed_solid_required")
    try:
        feature_mapping = map_design_model_features_to_brep(model, representation)
        tessellation = tessellate_cad_shape(
            representation.shape_handle,
            linear_deflection=linear_deflection,
            angular_deflection=angular_deflection,
            maximum_vertices=maximum_vertices,
            maximum_triangles=maximum_triangles,
            maximum_faces=maximum_faces,
        )
    except (CadAdapterError, ValueError) as error:
        raise CadStlExportError(str(error)) from error
    try:
        stl_bytes = _encode_binary_stl(tessellation.mesh.vertices, tessellation.mesh.triangles)
    except (OverflowError, struct.error, ValueError) as error:
        raise CadStlExportError("cad_stl_binary_encoding_failed") from error

    diagnostics = probe_cad_runtime()
    if (
        diagnostics.status.value != "READY"
        or not diagnostics.binding_version
        or not diagnostics.kernel_version
    ):
        raise CadStlExportError("cad_stl_runtime_version_unavailable")
    stl_capability = diagnostics.capability("stl_write")
    if stl_capability is None or stl_capability.status.value != "AVAILABLE":
        raise CadStlExportError("cad_stl_capability_unavailable")

    destination = Path(output_path)
    if destination.suffix.lower() != ".stl":
        raise CadStlExportError("cad_stl_extension_invalid")
    sidecar_path = Path(str(destination) + ".json")
    if not destination.parent.is_dir():
        raise CadStlExportError("cad_stl_destination_directory_missing")
    if destination.exists() or sidecar_path.exists():
        raise CadStlExportError("cad_stl_destination_exists")
    artifact_sha256 = hashlib.sha256(stl_bytes).hexdigest()
    feature_refs = tuple(reference.as_dict() for reference in feature_mapping.references)
    sidecar_material = {
        "contract": CAD_STL_EXPORT_CONTRACT,
        "artifact_mode": "BINARY_STL",
        "artifact_sha256": artifact_sha256,
        "artifact_size_bytes": len(stl_bytes),
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "source_brep_geometry_sha256": representation.geometry_sha256,
        "source_operation_id": representation.source_operation_id,
        "parent_kind": representation.parent_kind.value,
        "parent_authority_revision_id": representation.parent_authority_revision_id,
        "scale_state": representation.scale_state.value,
        "coordinate_unit": representation.coordinate_unit,
        "stl_coordinate_interpretation": "millimetres",
        "millimetres_numerically_encoded_from_unverified_design_units": True,
        "physical_accuracy_validation_status": representation.physical_accuracy_validation_status,
        "mold_use_authorized": representation.mold_use_authorized,
        "topology_validation_status": validation.status,
        "quality": {
            "preset": preset.value,
            "linear_deflection": tessellation.linear_deflection,
            "angular_deflection_radians": tessellation.angular_deflection,
            "maximum_vertices": tessellation.maximum_vertices,
            "maximum_triangles": tessellation.maximum_triangles,
            "maximum_faces": tessellation.maximum_faces,
            "source_face_count": tessellation.face_count,
            "vertex_count": len(tessellation.mesh.vertices),
            "triangle_count": len(tessellation.mesh.triangles),
        },
        "binding_package": diagnostics.binding_package,
        "binding_version": diagnostics.binding_version,
        "kernel_version": diagnostics.kernel_version,
        "feature_mapping": list(feature_refs),
        "disposable_export": True,
        "scan_master_promoted": False,
        "design_model_replaced": False,
        "cad_brep_replaced": False,
        "physical_accuracy_inferred": False,
        "print_fit_inferred": False,
        "production_ready_claimed": False,
        "manufacturing_suitability_inferred": False,
        "limitations": [
            "stl_has_no_reliable_embedded_unit_metadata",
            "sidecar_must_remain_with_artifact_to_interpret_coordinates_as_mm",
            "mesh_tolerance_is_not_physical_accuracy_or_print_fit_evidence",
        ],
    }
    export_identity = {
        "artifact_sha256": artifact_sha256,
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "parent_kind": representation.parent_kind.value,
        "parent_authority_revision_id": representation.parent_authority_revision_id,
        "quality_preset": preset.value,
        "linear_deflection": tessellation.linear_deflection,
        "angular_deflection": tessellation.angular_deflection,
        "binding_version": diagnostics.binding_version,
        "kernel_version": diagnostics.kernel_version,
    }
    export_id = (
        "cad-stl-export:"
        + hashlib.sha256(
            json.dumps(export_identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    )
    sidecar_material["export_id"] = export_id
    sidecar_bytes = (
        json.dumps(sidecar_material, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    sidecar_sha256 = hashlib.sha256(sidecar_bytes).hexdigest()

    temporary_artifact: Path | None = None
    temporary_sidecar: Path | None = None
    artifact_published = False
    try:
        with tempfile.NamedTemporaryFile(
            prefix="packlab-stl-", suffix=".stl", dir=destination.parent, delete=False
        ) as temporary:
            temporary_artifact = Path(temporary.name)
            temporary.write(stl_bytes)
        with tempfile.NamedTemporaryFile(
            prefix="packlab-stl-", suffix=".json", dir=destination.parent, delete=False
        ) as temporary:
            temporary_sidecar = Path(temporary.name)
            temporary.write(sidecar_bytes)
        temporary_artifact.rename(destination)
        artifact_published = True
        temporary_sidecar.rename(sidecar_path)
    except Exception as error:
        if artifact_published and destination.exists():
            destination.unlink()
        raise CadStlExportError("cad_stl_atomic_publication_failed") from error
    finally:
        for temporary_path in (temporary_artifact, temporary_sidecar):
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    return CadStlExportRevision(
        export_id=export_id,
        artifact_sha256=artifact_sha256,
        artifact_size_bytes=len(stl_bytes),
        sidecar_sha256=sidecar_sha256,
        source_design_model_revision_id=model.revision_id,
        source_brep_revision_id=representation.revision_id,
        source_brep_geometry_sha256=representation.geometry_sha256,
        source_operation_id=representation.source_operation_id,
        parent_kind=representation.parent_kind.value,
        parent_authority_revision_id=representation.parent_authority_revision_id,
        scale_state=representation.scale_state.value,
        coordinate_unit=representation.coordinate_unit,
        physical_accuracy_validation_status=representation.physical_accuracy_validation_status,
        mold_use_authorized=representation.mold_use_authorized,
        binding_package=diagnostics.binding_package,
        binding_version=diagnostics.binding_version,
        kernel_version=diagnostics.kernel_version,
        quality_preset=preset.value,
        linear_deflection=tessellation.linear_deflection,
        angular_deflection=tessellation.angular_deflection,
        maximum_vertices=tessellation.maximum_vertices,
        maximum_triangles=tessellation.maximum_triangles,
        maximum_faces=tessellation.maximum_faces,
        source_face_count=tessellation.face_count,
        vertex_count=len(tessellation.mesh.vertices),
        triangle_count=len(tessellation.mesh.triangles),
        topology_validation_status=validation.status,
        feature_mapping=feature_refs,
    )


def _encode_binary_stl(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
) -> bytes:
    if not triangles or len(triangles) > 0xFFFFFFFF:
        raise CadStlExportError("cad_stl_triangle_count_invalid")
    header = _STL_HEADER[:80].ljust(80, b" ")
    facets = bytearray(header)
    facets.extend(struct.pack("<I", len(triangles)))
    for indices in triangles:
        quantized = tuple(
            tuple(
                struct.unpack("<f", struct.pack("<f", component))[0]
                for component in vertices[index]
            )
            for index in indices
        )
        first, second, third = quantized
        edge_a = tuple(second[axis] - first[axis] for axis in range(3))
        edge_b = tuple(third[axis] - first[axis] for axis in range(3))
        normal = (
            edge_a[1] * edge_b[2] - edge_a[2] * edge_b[1],
            edge_a[2] * edge_b[0] - edge_a[0] * edge_b[2],
            edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0],
        )
        magnitude = math.sqrt(sum(component * component for component in normal))
        if not math.isfinite(magnitude) or magnitude <= 1e-15:
            raise CadStlExportError("cad_stl_degenerate_triangle")
        unit_normal = tuple(component / magnitude for component in normal)
        facets.extend(struct.pack("<12fH", *unit_normal, *first, *second, *third, 0))
    return bytes(facets)


__all__ = [
    "CAD_STL_EXPORT_CONTRACT",
    "CadStlExportError",
    "CadStlExportRevision",
    "CadStlMeshQuality",
    "export_design_model_stl",
]
