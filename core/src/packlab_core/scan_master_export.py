"""Deterministic PLY, OBJ and GLB export for selected captured Scan Masters."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from .geometry_adapter import TriangleMeshData
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

SCAN_MASTER_EXPORT_CONTRACT = "packlab.scan-master-export.v1"
_SUPPORTED_FORMATS = frozenset({"ply", "obj", "glb"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TEXTURE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_PRIVATE_SEGMENTS = frozenset({"private", "secret", "secrets"})


class _ScanMasterFacts(TypedDict):
    geometry_sha256: str
    manifest_sha256: str
    scale_state: ScaleState
    scale_provenance_id: str
    reconstruction_revision_id: str
    unit: str
    known_limitations: tuple[str, ...]
    coverage_gaps: tuple[str, ...]


class ScanMasterExportError(ValueError):
    """Raised when export authority, provenance, format or publication is invalid."""


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_asset_id(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or value.casefold().startswith("raw/")
        or any(part.casefold() in _PRIVATE_SEGMENTS for part in value.split("/"))
    ):
        raise ScanMasterExportError("texture_source_asset_id_invalid")
    return value


def _scan_master_facts(revision: ScanMasterRevision) -> _ScanMasterFacts:
    if not isinstance(revision, ScanMasterRevision):
        raise ScanMasterExportError("scan_master_revision_required")
    manifest = revision.manifest
    geometry_digest = mesh_sha256(revision.mesh)
    scale_value = manifest.get("scale_state")
    if not isinstance(scale_value, str):
        raise ScanMasterExportError("scan_master_scale_state_invalid")
    try:
        scale_state = ScaleState(scale_value)
    except ValueError as error:
        raise ScanMasterExportError("scan_master_scale_state_invalid") from error
    limitations = manifest.get("known_limitations")
    gaps = manifest.get("coverage_gaps", ())
    if (
        not isinstance(limitations, (list, tuple))
        or any(not isinstance(item, str) or not item for item in limitations)
        or not isinstance(gaps, (list, tuple))
        or any(not isinstance(item, str) or not item for item in gaps)
    ):
        raise ScanMasterExportError("scan_master_limitations_invalid")
    required_strings = tuple(
        manifest.get(key)
        for key in (
            "raw_capture_revision_id",
            "reconstruction_revision_id",
            "parent_object_geometry_revision_id",
            "scale_provenance_id",
        )
    )
    if (
        manifest.get("scan_master_revision_id") != revision.revision_id
        or manifest.get("project_id") != revision.project_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != geometry_digest
        or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or manifest.get("mold_use_authorized") is not False
        or scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}
        or any(not isinstance(value, str) or not value for value in required_strings)
        or not limitations
        or not revision.mesh.vertices
        or not revision.mesh.triangles
    ):
        raise ScanMasterExportError("scan_master_authority_or_provenance_invalid")
    return {
        "geometry_sha256": geometry_digest,
        "manifest_sha256": _digest(revision.manifest_bytes()),
        "scale_state": scale_state,
        "scale_provenance_id": str(manifest["scale_provenance_id"]),
        "reconstruction_revision_id": str(manifest["reconstruction_revision_id"]),
        "unit": "mm_unverified"
        if scale_state is ScaleState.METRIC_UNVERIFIED
        else "reconstruction_units",
        "known_limitations": tuple(limitations),
        "coverage_gaps": tuple(gaps),
    }


@dataclass(frozen=True, slots=True)
class ScanMasterTextureAsset:
    """Original reconstruction texture bytes eligible for Scan Master sidecar export."""

    source_asset_id: str
    source_sha256: str
    data: bytes
    parent_reconstruction_revision_id: str
    authority_class: str = "RECONSTRUCTION_OBSERVATION"
    generated: bool = False
    original: bool = True

    def __post_init__(self) -> None:
        _safe_asset_id(self.source_asset_id)
        if (
            not isinstance(self.data, bytes)
            or not isinstance(self.source_sha256, str)
            or not _SHA256.fullmatch(self.source_sha256)
        ):
            raise ScanMasterExportError("texture_asset_digest_invalid")
        if _digest(self.data) != self.source_sha256:
            raise ScanMasterExportError("texture_asset_digest_mismatch")
        if Path(self.source_asset_id).suffix.lower() not in _TEXTURE_EXTENSIONS:
            raise ScanMasterExportError("texture_asset_format_unsupported")
        if (
            self.authority_class != "RECONSTRUCTION_OBSERVATION"
            or self.generated is not False
            or self.original is not True
            or not isinstance(self.parent_reconstruction_revision_id, str)
            or not self.parent_reconstruction_revision_id.strip()
        ):
            raise ScanMasterExportError("texture_asset_authority_invalid")


@dataclass(frozen=True, slots=True)
class ScanMasterExportRequest:
    scan_master: ScanMasterRevision
    selected_scan_master_revision_id: str
    project_root: Path
    destination_relative_dir: str
    formats: tuple[str, ...]
    texture_assets: tuple[ScanMasterTextureAsset, ...] = ()

    def __post_init__(self) -> None:
        facts = _scan_master_facts(self.scan_master)
        if self.selected_scan_master_revision_id != self.scan_master.revision_id:
            raise ScanMasterExportError("selected_scan_master_revision_mismatch")
        if not isinstance(self.project_root, Path) or not self.project_root.is_absolute():
            raise ScanMasterExportError("project_root_must_be_absolute")
        _safe_asset_id(self.destination_relative_dir)
        if not self.destination_relative_dir.startswith("export/"):
            raise ScanMasterExportError("scan_master_export_must_be_under_export")
        if (
            not isinstance(self.formats, tuple)
            or not self.formats
            or any(
                not isinstance(item, str) or item not in _SUPPORTED_FORMATS for item in self.formats
            )
            or len(set(self.formats)) != len(self.formats)
        ):
            raise ScanMasterExportError("scan_master_export_formats_invalid")
        if not isinstance(self.texture_assets, tuple) or any(
            not isinstance(item, ScanMasterTextureAsset) for item in self.texture_assets
        ):
            raise ScanMasterExportError("texture_assets_must_be_eligible_tuple")
        ids = [item.source_asset_id for item in self.texture_assets]
        names = [Path(item).name.casefold() for item in ids]
        if len(set(ids)) != len(ids) or len(set(names)) != len(names):
            raise ScanMasterExportError("texture_asset_identity_collision")
        if any(
            item.parent_reconstruction_revision_id != facts["reconstruction_revision_id"]
            for item in self.texture_assets
        ):
            raise ScanMasterExportError("texture_asset_reconstruction_parent_mismatch")


@dataclass(frozen=True, slots=True)
class ScanMasterExportResult:
    output_directory: Path
    manifest_path: Path
    manifest_sha256: str
    outputs: tuple[tuple[str, str, str], ...]


def _number(value: float) -> str:
    return format(value, ".17g")


def _export_ply(mesh: TriangleMeshData) -> bytes:
    lines = [
        "ply",
        "format ascii 1.0",
        "comment PackLab captured Scan Master geometry",
        f"element vertex {len(mesh.vertices)}",
        "property double x",
        "property double y",
        "property double z",
    ]
    if mesh.vertex_normals is not None:
        lines.extend(("property double nx", "property double ny", "property double nz"))
    if mesh.vertex_colors is not None:
        lines.extend(("property uchar red", "property uchar green", "property uchar blue"))
    lines.extend(
        (
            f"element face {len(mesh.triangles)}",
            "property list uchar int vertex_indices",
            "end_header",
        )
    )
    for index, point in enumerate(mesh.vertices):
        values = [_number(component) for component in point]
        if mesh.vertex_normals is not None:
            values.extend(_number(component) for component in mesh.vertex_normals[index])
        if mesh.vertex_colors is not None:
            values.extend(str(int(channel * 255 + 0.5)) for channel in mesh.vertex_colors[index])
        lines.append(" ".join(values))
    lines.extend("3 " + " ".join(str(index) for index in face) for face in mesh.triangles)
    return ("\n".join(lines) + "\n").encode("ascii")


def _export_obj(mesh: TriangleMeshData, revision_id: str) -> bytes:
    lines = [
        f"# PackLab Scan Master {revision_id}",
        "# coordinates preserved in declared manifest units",
    ]
    lines.extend("v " + " ".join(_number(value) for value in point) for point in mesh.vertices)
    if mesh.vertex_normals is not None:
        lines.extend(
            "vn " + " ".join(_number(value) for value in normal) for normal in mesh.vertex_normals
        )
    for face in mesh.triangles:
        indices = [str(index + 1) for index in face]
        if mesh.vertex_normals is None:
            lines.append("f " + " ".join(indices))
        else:
            lines.append("f " + " ".join(f"{index}//{index}" for index in indices))
    return ("\n".join(lines) + "\n").encode("ascii")


def _export_glb(
    mesh: TriangleMeshData, revision_id: str, unit: str, scale_state: ScaleState
) -> bytes:
    binary = bytearray()
    views: list[dict[str, int]] = []
    accessors: list[dict[str, object]] = []

    def add_accessor(
        data: bytes, *, component_type: int, count: int, kind: str, target: int, bounds=None
    ) -> int:
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        binary.extend(data)
        view_index = len(views)
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(data), "target": target})
        accessor: dict[str, object] = {
            "bufferView": view_index,
            "componentType": component_type,
            "count": count,
            "type": kind,
        }
        if bounds is not None:
            accessor["min"], accessor["max"] = bounds
        accessors.append(accessor)
        return len(accessors) - 1

    packed_positions = [struct.pack("<3f", *point) for point in mesh.vertices]
    float_positions = [struct.unpack("<3f", point) for point in packed_positions]
    position_bounds = (
        [min(point[index] for point in float_positions) for index in range(3)],
        [max(point[index] for point in float_positions) for index in range(3)],
    )
    attributes = {
        "POSITION": add_accessor(
            b"".join(packed_positions),
            component_type=5126,
            count=len(mesh.vertices),
            kind="VEC3",
            target=34962,
            bounds=position_bounds,
        )
    }
    if mesh.vertex_normals is not None:
        attributes["NORMAL"] = add_accessor(
            b"".join(struct.pack("<3f", *normal) for normal in mesh.vertex_normals),
            component_type=5126,
            count=len(mesh.vertex_normals),
            kind="VEC3",
            target=34962,
        )
    if mesh.vertex_colors is not None:
        attributes["COLOR_0"] = add_accessor(
            b"".join(struct.pack("<3f", *color) for color in mesh.vertex_colors),
            component_type=5126,
            count=len(mesh.vertex_colors),
            kind="VEC3",
            target=34962,
        )
    max_index = max((max(face) for face in mesh.triangles), default=0)
    index_type = 5123 if max_index <= 65535 else 5125
    index_format = "<H" if index_type == 5123 else "<I"
    index_bytes = b"".join(
        struct.pack(index_format, value) for face in mesh.triangles for value in face
    )
    index_accessor = add_accessor(
        index_bytes,
        component_type=index_type,
        count=len(mesh.triangles) * 3,
        kind="SCALAR",
        target=34963,
    )
    document = {
        "asset": {"version": "2.0", "generator": "PackLab Scan Master Export"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [
            {
                "primitives": [{"attributes": attributes, "indices": index_accessor, "mode": 4}],
                "extras": {
                    "scanMasterRevisionId": revision_id,
                    "coordinateUnit": unit,
                    "scaleState": scale_state.value,
                    "warning": "Coordinates are preserved verbatim; inspect the PackLab export manifest before interpreting units.",
                },
            }
        ],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": views,
        "accessors": accessors,
    }
    json_chunk = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
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


def _inside(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(candidate))) == str(root)
    except ValueError:
        return False


def _reject_symlink_components(root: Path, relative: str) -> None:
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ScanMasterExportError("export_path_contains_symlink")


def export_scan_master(request: ScanMasterExportRequest) -> ScanMasterExportResult:
    """Atomically export selected full-resolution geometry and verified texture sidecars."""

    facts = _scan_master_facts(request.scan_master)
    root = request.project_root.resolve()
    _reject_symlink_components(root, request.destination_relative_dir)
    target = (root / request.destination_relative_dir).resolve(strict=False)
    if not _inside(root, target) or target == root:
        raise ScanMasterExportError("export_destination_escapes_project")
    if target.exists() or target.is_symlink():
        raise ScanMasterExportError("export_destination_already_exists")

    mesh = request.scan_master.mesh
    exporters = {
        "ply": lambda: _export_ply(mesh),
        "obj": lambda: _export_obj(mesh, request.scan_master.revision_id),
        "glb": lambda: _export_glb(
            mesh,
            request.scan_master.revision_id,
            str(facts["unit"]),
            facts["scale_state"],
        ),
    }
    outputs: list[dict[str, object]] = []
    payloads: dict[str, bytes] = {}
    for format_name in request.formats:
        filename = f"scan-master.{format_name}"
        payload = exporters[format_name]()
        payloads[filename] = payload
        outputs.append(
            {
                "format": format_name,
                "path": filename,
                "sha256": _digest(payload),
                "byte_length": len(payload),
            }
        )

    texture_entries: list[dict[str, object]] = []
    for texture in request.texture_assets:
        filename = Path(texture.source_asset_id).name
        output_path = f"textures/{filename}"
        payloads[output_path] = texture.data
        texture_entries.append(
            {
                "source_asset_id": texture.source_asset_id,
                "source_sha256": texture.source_sha256,
                "output_path": output_path,
                "output_sha256": _digest(texture.data),
                "parent_reconstruction_revision_id": texture.parent_reconstruction_revision_id,
                "authority_class": texture.authority_class,
                "relationship": "original_reconstruction_texture_sidecar",
                "surface_mapping_status": "UNAVAILABLE_NO_UV_COORDINATES_IN_SCAN_MASTER_CONTRACT",
            }
        )

    limitations = list(facts["known_limitations"])
    limitations.extend(facts["coverage_gaps"])
    if mesh.vertex_colors is not None and "obj" in request.formats:
        limitations.append(
            "OBJ export omits vertex colors; PLY and GLB preserve supported color attributes."
        )
    if mesh.vertex_colors is not None and "ply" in request.formats:
        limitations.append(
            "PLY stores normalized vertex colors as 8-bit channels and quantizes color values."
        )
    if "glb" in request.formats:
        limitations.append(
            "GLB stores vertex coordinates as float32; values are not rescaled to meters."
        )
    if request.texture_assets:
        limitations.append(
            "Texture files are preserved as sidecars; no surface mapping is claimed because Scan Master has no UV coordinates."
        )
    else:
        limitations.append(
            "No eligible original texture assets were supplied; geometry exports contain no textures."
        )
    manifest = {
        "contract": SCAN_MASTER_EXPORT_CONTRACT,
        "scan_master_revision_id": request.scan_master.revision_id,
        "project_id": request.scan_master.project_id,
        "authority_class": "SCAN_MASTER",
        "source_geometry_sha256": facts["geometry_sha256"],
        "source_manifest_sha256": facts["manifest_sha256"],
        "source_reconstruction_revision_id": facts["reconstruction_revision_id"],
        "units": facts["unit"],
        "scale_state": facts["scale_state"].value,
        "scale_provenance_id": facts["scale_provenance_id"],
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "known_limitations_and_coverage_gaps": limitations,
        "formats": outputs,
        "textures": texture_entries,
        "texture_status": "SIDECARS_WITHOUT_SURFACE_MAPPING"
        if texture_entries
        else "NOT_AVAILABLE",
        "coordinate_values_transformed": False,
    }
    manifest_bytes = (
        json.dumps(
            manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
        + "\n"
    ).encode("ascii")
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=parent))
    try:
        for relative, payload in payloads.items():
            artifact_path = staging / relative
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            with artifact_path.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        manifest_path = staging / "manifest.json"
        with manifest_path.open("xb") as handle:
            handle.write(manifest_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.rename(staging, target)
    except (OSError, ValueError, TypeError) as error:
        shutil.rmtree(staging, ignore_errors=True)
        raise ScanMasterExportError("scan_master_export_publication_failed") from error
    return ScanMasterExportResult(
        target,
        target / "manifest.json",
        _digest(manifest_bytes),
        tuple((str(item["format"]), str(item["path"]), str(item["sha256"])) for item in outputs),
    )


__all__ = [
    "SCAN_MASTER_EXPORT_CONTRACT",
    "ScanMasterExportError",
    "ScanMasterExportRequest",
    "ScanMasterExportResult",
    "ScanMasterTextureAsset",
    "export_scan_master",
]
