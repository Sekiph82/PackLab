"""Deterministic, provenance-bound OBJ and GLB export from one CAD preview."""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .assembly_hierarchy_export import (
    AssemblyHierarchyExportHandoff,
)
from .cad_adapter import probe_cad_runtime
from .cad_brep import CadBrepRepresentationRevision
from .cad_export_manifest import build_cad_export_manifest
from .cad_preview import CadPreviewError, CadPreviewMeshRevision, tessellate_brep_preview
from .cad_validation import validate_cad_brep
from .design_model import DesignModelRevision
from .geometry_adapter import TriangleMeshData
from .reconstruction import ScaleState

CAD_MESH_EXPORT_CONTRACT = "packlab.cad-mesh-export.v1"
_SEMANTIC_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")


class CadMeshExportError(ValueError):
    """Raised when a CAD preview cannot safely produce OBJ and GLB files."""


@dataclass(frozen=True, slots=True)
class CadMeshExportRevision:
    export_id: str
    obj_sha256: str
    obj_size_bytes: int
    obj_manifest_id: str
    obj_manifest_sha256: str
    glb_sha256: str
    glb_size_bytes: int
    glb_manifest_id: str
    glb_manifest_sha256: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    source_preview_revision_id: str
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    semantic_part_name: str
    vertex_count: int
    triangle_count: int
    feature_mapping: tuple[dict[str, object], ...]
    contract: str = CAD_MESH_EXPORT_CONTRACT
    authority_class: str = "DERIVED_CAD_PREVIEW_MESH_EXPORT"

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": self.authority_class,
            "export_id": self.export_id,
            "artifacts": {
                "obj": {"sha256": self.obj_sha256, "byte_length": self.obj_size_bytes},
                "obj_manifest_id": self.obj_manifest_id,
                "obj_manifest_sha256": self.obj_manifest_sha256,
                "glb": {"sha256": self.glb_sha256, "byte_length": self.glb_size_bytes},
                "glb_manifest_id": self.glb_manifest_id,
                "glb_manifest_sha256": self.glb_manifest_sha256,
            },
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_brep_geometry_sha256": self.source_brep_geometry_sha256,
            "source_preview_revision_id": self.source_preview_revision_id,
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "semantic_part_name": self.semantic_part_name,
            "vertex_count": self.vertex_count,
            "triangle_count": self.triangle_count,
            "feature_mapping": list(self.feature_mapping),
            "disposable_export": True,
            "scan_master_promoted": False,
            "design_model_replaced": False,
            "cad_brep_replaced": False,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


def export_design_model_obj_glb(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    preview: CadPreviewMeshRevision | AssemblyHierarchyExportHandoff,
    obj_path: str | Path,
    glb_path: str | Path,
) -> CadMeshExportRevision:
    """Export one exact PREVIEW_PROXY source to deterministic OBJ and GLB files."""
    if isinstance(preview, AssemblyHierarchyExportHandoff):
        raise CadMeshExportError("assembly_geometry_source_not_available")
    if not isinstance(preview, CadPreviewMeshRevision):
        raise CadMeshExportError("cad_preview_revision_required")
    if not isinstance(model, DesignModelRevision):
        raise CadMeshExportError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise CadMeshExportError("cad_brep_representation_required")
    if representation.source_design_model_revision_id != model.revision_id:
        raise CadMeshExportError("cad_mesh_model_revision_mismatch")
    parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if (
        representation.parent_kind is not model.parent_kind
        or representation.parent_authority_revision_id != parent_revision
    ):
        raise CadMeshExportError("cad_mesh_parent_authority_mismatch")
    if (
        representation.scale_state is not model.scale_state
        or representation.coordinate_unit != model.coordinate_unit
        or representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized is not False
    ):
        raise CadMeshExportError("cad_mesh_brep_authority_metadata_mismatch")
    if (
        preview.contract != "packlab.cad-brep-preview.v1"
        or preview.authority_class != "PREVIEW_PROXY"
        or preview.source_design_model_revision_id != model.revision_id
        or preview.source_brep_revision_id != representation.revision_id
        or preview.source_operation_id != representation.source_operation_id
        or preview.parent_kind != representation.parent_kind.value
        or preview.parent_authority_revision_id != representation.parent_authority_revision_id
        or preview.scale_state != representation.scale_state.value
        or preview.coordinate_unit != representation.coordinate_unit
        or preview.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or preview.mold_use_authorized is not False
    ):
        raise CadMeshExportError("cad_mesh_preview_provenance_mismatch")
    try:
        validation = validate_cad_brep(representation)
    except Exception as error:
        raise CadMeshExportError("cad_mesh_brep_validation_failed") from error
    if not validation.valid_closed_solid:
        raise CadMeshExportError("cad_mesh_valid_closed_solid_required")
    diagnostics = probe_cad_runtime()
    if (
        diagnostics.status.value != "READY"
        or not diagnostics.binding_version
        or not diagnostics.kernel_version
    ):
        raise CadMeshExportError("cad_mesh_runtime_version_unavailable")
    try:
        expected_preview = tessellate_brep_preview(
            model,
            representation,
            linear_deflection=preview.linear_deflection,
            angular_deflection=preview.angular_deflection,
            maximum_vertices=preview.maximum_vertices,
            maximum_triangles=preview.maximum_triangles,
            maximum_faces=preview.maximum_faces,
        )
    except (CadPreviewError, ValueError) as error:
        raise CadMeshExportError("cad_mesh_preview_regeneration_failed") from error
    if (
        expected_preview.revision_id != preview.revision_id
        or expected_preview.mesh != preview.mesh
        or expected_preview.feature_mapping_revision_id != preview.feature_mapping_revision_id
    ):
        raise CadMeshExportError("cad_mesh_preview_revision_stale")

    mesh = preview.mesh
    _validate_mesh(mesh)
    semantic_name = _semantic_part_name(model, representation)
    feature_mapping_records: list[dict[str, object]] = []
    for item in preview.feature_references:
        feature_mapping_records.append(
            {
                "feature_id": item.feature_id,
                "status": item.status,
                "mapping_reference_id": item.mapping_reference_id,
                "mapping_scope": item.mapping_scope,
            }
        )
    feature_mapping = tuple(feature_mapping_records)
    source_metadata: dict[str, object] = {
        "contract": CAD_MESH_EXPORT_CONTRACT,
        "sourceDesignModelRevisionId": model.revision_id,
        "sourceCadBrepRevisionId": representation.revision_id,
        "sourceCadBrepGeometrySha256": representation.geometry_sha256,
        "sourceCadPreviewRevisionId": preview.revision_id,
        "parentAuthority": {
            "kind": representation.parent_kind.value,
            "revisionId": representation.parent_authority_revision_id,
        },
        "scaleState": representation.scale_state.value,
        "coordinateUnit": representation.coordinate_unit,
        "physicalAccuracyValidationStatus": representation.physical_accuracy_validation_status,
        "moldUseAuthorized": False,
        "semanticPartName": semantic_name,
        "featureMapping": list(feature_mapping),
        "disposableExport": True,
        "scanMasterPromoted": False,
        "designModelReplaced": False,
        "cadBrepReplaced": False,
        "physicalAccuracyInferred": False,
        "manufacturingSuitabilityInferred": False,
    }
    obj_bytes = _encode_obj(mesh, semantic_name, source_metadata)
    glb_bytes = _encode_glb(mesh, semantic_name, source_metadata, representation.scale_state)
    export_identity = {
        "obj_sha256": _sha256(obj_bytes),
        "glb_sha256": _sha256(glb_bytes),
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "source_preview_revision_id": preview.revision_id,
        "semantic_part_name": semantic_name,
    }
    export_id = "cad-mesh-export:" + _sha256(_canonical_json(export_identity))
    obj_manifest = build_cad_export_manifest(
        model=model,
        representation=representation,
        format="obj",
        export_id=export_id,
        artifact_sha256=_sha256(obj_bytes),
        artifact_size_bytes=len(obj_bytes),
        validation=validation,
        diagnostics=diagnostics,
        part_names=(semantic_name,),
        feature_mapping=feature_mapping,
        coordinate_transform={
            "kind": "identity_source_coordinates",
            "source_unit": representation.coordinate_unit,
            "target_unit": representation.coordinate_unit,
            "scale": [1.0, 1.0, 1.0],
            "reversible": True,
            "physical_authority_upgraded": False,
        },
        tessellation=_preview_tessellation(preview),
        limitations=(
            "obj_coordinates_are_preserved_in_source_units",
            "mesh_is_a_disposable_cad_preview",
            "feature_mapping_is_conservative_and_may_be_unresolved",
        ),
    )
    glb_manifest = build_cad_export_manifest(
        model=model,
        representation=representation,
        format="glb",
        export_id=export_id,
        artifact_sha256=_sha256(glb_bytes),
        artifact_size_bytes=len(glb_bytes),
        validation=validation,
        diagnostics=diagnostics,
        part_names=(semantic_name,),
        feature_mapping=feature_mapping,
        coordinate_transform=_glb_view_transform(representation.scale_state),
        tessellation=_preview_tessellation(preview),
        limitations=(
            "glb_positions_are_float32",
            "glb_node_transform_is_viewer_space_only_and_does_not_upgrade_authority",
            "mesh_is_a_disposable_cad_preview",
        ),
    )
    obj_output, glb_output = Path(obj_path), Path(glb_path)
    _publish_pair(
        (
            (obj_output, obj_bytes),
            (Path(str(obj_output) + ".json"), obj_manifest.canonical_json),
            (glb_output, glb_bytes),
            (Path(str(glb_output) + ".json"), glb_manifest.canonical_json),
        )
    )
    return CadMeshExportRevision(
        export_id=export_id,
        obj_sha256=_sha256(obj_bytes),
        obj_size_bytes=len(obj_bytes),
        obj_manifest_id=obj_manifest.manifest_id,
        obj_manifest_sha256=obj_manifest.manifest_sha256,
        glb_sha256=_sha256(glb_bytes),
        glb_size_bytes=len(glb_bytes),
        glb_manifest_id=glb_manifest.manifest_id,
        glb_manifest_sha256=glb_manifest.manifest_sha256,
        source_design_model_revision_id=model.revision_id,
        source_brep_revision_id=representation.revision_id,
        source_brep_geometry_sha256=representation.geometry_sha256,
        source_preview_revision_id=preview.revision_id,
        parent_kind=representation.parent_kind.value,
        parent_authority_revision_id=representation.parent_authority_revision_id,
        scale_state=representation.scale_state.value,
        coordinate_unit=representation.coordinate_unit,
        physical_accuracy_validation_status=representation.physical_accuracy_validation_status,
        mold_use_authorized=False,
        semantic_part_name=semantic_name,
        vertex_count=len(mesh.vertices),
        triangle_count=len(mesh.triangles),
        feature_mapping=feature_mapping,
    )


def _validate_mesh(mesh: TriangleMeshData) -> None:
    if not isinstance(mesh, TriangleMeshData) or not mesh.vertices or not mesh.triangles:
        raise CadMeshExportError("cad_mesh_geometry_empty")
    for vertex in mesh.vertices:
        if len(vertex) != 3 or any(not math.isfinite(value) for value in vertex):
            raise CadMeshExportError("cad_mesh_vertex_invalid")
        try:
            struct.pack("<3f", *vertex)
        except (OverflowError, struct.error) as error:
            raise CadMeshExportError("cad_mesh_vertex_not_glb_representable") from error
    for triangle in mesh.triangles:
        if (
            len(triangle) != 3
            or any(not isinstance(index, int) or isinstance(index, bool) for index in triangle)
            or any(index < 0 or index >= len(mesh.vertices) for index in triangle)
            or len(set(triangle)) != 3
        ):
            raise CadMeshExportError("cad_mesh_triangle_invalid")
    if len(mesh.vertices) > 0xFFFFFFFF or len(mesh.triangles) > 0xFFFFFFFF // 3:
        raise CadMeshExportError("cad_mesh_geometry_count_invalid")


def _semantic_part_name(
    model: DesignModelRevision, representation: CadBrepRepresentationRevision
) -> str:
    features = {item.feature_id: item for item in model.features}
    source_features = sorted(
        (features[item] for item in representation.source_feature_ids if item in features),
        key=lambda item: (item.component_id, item.semantic_key, item.feature_id),
    )
    if not source_features:
        raise CadMeshExportError("cad_mesh_semantic_part_name_unavailable")
    feature = source_features[0]
    raw_name = f"{feature.component_id}-{feature.semantic_key}"
    safe_name = _SEMANTIC_SAFE.sub("-", raw_name).strip("-._")
    if not safe_name:
        raise CadMeshExportError("cad_mesh_semantic_part_name_invalid")
    return safe_name[:128]


def _encode_obj(mesh: TriangleMeshData, semantic_name: str, metadata: dict[str, object]) -> bytes:
    encoded_metadata = json.dumps(
        metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    lines = [
        f"# PackLab CAD preview export {CAD_MESH_EXPORT_CONTRACT}",
        f"# source_metadata={encoded_metadata}",
        f"o {semantic_name}",
        f"g {semantic_name}",
    ]
    lines.extend(
        "v " + " ".join(format(value, ".17g") for value in vertex) for vertex in mesh.vertices
    )
    lines.extend(
        "f " + " ".join(str(index + 1) for index in triangle) for triangle in mesh.triangles
    )
    return ("\n".join(lines) + "\n").encode("ascii")


def _encode_glb(
    mesh: TriangleMeshData,
    semantic_name: str,
    metadata: dict[str, object],
    scale_state: ScaleState,
) -> bytes:
    # glTF coordinates are metres. The scale is explicit and reversible; it
    # changes only the viewer transform and leaves source provenance unchanged.
    viewer_scale = 0.001 if scale_state is ScaleState.METRIC_UNVERIFIED else 1.0
    metadata = {
        **metadata,
        "sourceToViewerTransform": {
            "kind": "uniform_scale",
            "scale": [viewer_scale, viewer_scale, viewer_scale],
            "inverseScale": [1.0 / viewer_scale] * 3,
            "reversible": True,
            "sourceCoordinatesPreservedInBuffer": True,
            "viewerUnit": "meters"
            if scale_state is ScaleState.METRIC_UNVERIFIED
            else "relative_viewer_units",
        },
    }
    binary = bytearray()
    while len(binary) % 4:
        binary.append(0)
    positions = b"".join(struct.pack("<3f", *vertex) for vertex in mesh.vertices)
    position_offset = len(binary)
    binary.extend(positions)
    quantized = [struct.unpack("<3f", struct.pack("<3f", *vertex)) for vertex in mesh.vertices]
    index_format = "<H" if len(mesh.vertices) <= 65536 else "<I"
    index_type = 5123 if index_format == "<H" else 5125
    index_bytes = b"".join(
        struct.pack(index_format, index) for face in mesh.triangles for index in face
    )
    while len(binary) % 4:
        binary.append(0)
    index_offset = len(binary)
    binary.extend(index_bytes)
    position_accessor = {
        "bufferView": 0,
        "componentType": 5126,
        "count": len(mesh.vertices),
        "type": "VEC3",
        "min": [min(vertex[axis] for vertex in quantized) for axis in range(3)],
        "max": [max(vertex[axis] for vertex in quantized) for axis in range(3)],
    }
    index_accessor = {
        "bufferView": 1,
        "componentType": index_type,
        "count": len(mesh.triangles) * 3,
        "type": "SCALAR",
    }
    node: dict[str, object] = {"name": semantic_name, "mesh": 0, "extras": metadata}
    if viewer_scale != 1.0:
        node["scale"] = [viewer_scale, viewer_scale, viewer_scale]
    document = {
        "asset": {"version": "2.0", "generator": "PackLab CAD Preview Export"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [node],
        "meshes": [
            {
                "name": semantic_name,
                "primitives": [
                    {
                        "attributes": {"POSITION": 0},
                        "indices": 1,
                        "mode": 4,
                    }
                ],
            }
        ],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": position_offset,
                "byteLength": len(positions),
                "target": 34962,
            },
            {
                "buffer": 0,
                "byteOffset": index_offset,
                "byteLength": len(index_bytes),
                "target": 34963,
            },
        ],
        "accessors": [position_accessor, index_accessor],
    }
    json_chunk = _canonical_json(document)
    json_chunk += b" " * ((-len(json_chunk)) % 4)
    binary.extend(b"\x00" * ((-len(binary)) % 4))
    total_length = 12 + 8 + len(json_chunk) + 8 + len(binary)
    return (
        struct.pack("<4sII", b"glTF", 2, total_length)
        + struct.pack("<I4s", len(json_chunk), b"JSON")
        + json_chunk
        + struct.pack("<I4s", len(binary), b"BIN\x00")
        + bytes(binary)
    )


def _preview_tessellation(preview: CadPreviewMeshRevision) -> dict[str, object]:
    return {
        "linear_deflection": preview.linear_deflection,
        "angular_deflection_radians": preview.angular_deflection,
        "maximum_vertices": preview.maximum_vertices,
        "maximum_triangles": preview.maximum_triangles,
        "maximum_faces": preview.maximum_faces,
        "source_face_count": preview.source_face_count,
        "vertex_count": len(preview.mesh.vertices),
        "triangle_count": len(preview.mesh.triangles),
    }


def _glb_view_transform(scale_state: ScaleState) -> dict[str, object]:
    scale = 0.001 if scale_state is ScaleState.METRIC_UNVERIFIED else 1.0
    return {
        "kind": "uniform_scale",
        "source_unit": "mm_unverified"
        if scale_state is ScaleState.METRIC_UNVERIFIED
        else "reconstruction_units",
        "target_unit": "meters"
        if scale_state is ScaleState.METRIC_UNVERIFIED
        else "relative_viewer_units",
        "scale": [scale, scale, scale],
        "inverse_scale": [1.0 / scale] * 3,
        "reversible": True,
        "source_coordinates_preserved_in_buffer": True,
        "physical_authority_upgraded": False,
    }


def _publish_pair(files: tuple[tuple[Path, bytes], ...]) -> None:
    paths = tuple(path for path, _payload in files)
    if any(path.suffix.lower() not in {".obj", ".glb", ".json"} for path in paths):
        raise CadMeshExportError("cad_mesh_export_extension_invalid")
    if len({path.resolve(strict=False) for path in paths}) != len(paths):
        raise CadMeshExportError("cad_mesh_export_destinations_must_differ")
    if not any(path.suffix.lower() == ".obj" for path in paths) or not any(
        path.suffix.lower() == ".glb" for path in paths
    ):
        raise CadMeshExportError("cad_mesh_export_extension_invalid")
    for path in paths:
        if not path.parent.is_dir():
            raise CadMeshExportError("cad_mesh_export_destination_directory_missing")
        if path.exists() or path.is_symlink():
            raise CadMeshExportError("cad_mesh_export_destination_exists")
    temporary: list[Path] = []
    published: list[Path] = []
    try:
        for path, data in files:
            with tempfile.NamedTemporaryFile(
                prefix=".packlab-cad-mesh-", suffix=path.suffix, dir=path.parent, delete=False
            ) as handle:
                temp_path = Path(handle.name)
                temporary.append(temp_path)
                handle.write(data)
        for temp_path, path in zip(temporary, paths):
            temp_path.rename(path)
            published.append(path)
    except Exception as error:
        for path in published:
            if path.exists():
                path.unlink()
        raise CadMeshExportError("cad_mesh_export_atomic_publication_failed") from error
    finally:
        for path in temporary:
            if path.exists():
                path.unlink()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


__all__ = [
    "CAD_MESH_EXPORT_CONTRACT",
    "CadMeshExportError",
    "CadMeshExportRevision",
    "export_design_model_obj_glb",
]
