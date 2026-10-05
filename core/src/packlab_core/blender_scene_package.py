"""Deterministic, bounded, data-only input packages for Blender scene work."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from .cad_mesh_export import CAD_MESH_EXPORT_CONTRACT, CadMeshExportRevision
from .component_material_project import (
    ComponentMaterialProjectDocument,
)
from .design_model import DesignModelRevision
from .label_artwork import (
    LabelArtworkAssetRevision,
    LabelArtworkAssignmentRevision,
    LabelArtworkMappingRevision,
)
from .label_zone_placement import LabelZonePlacementRevision
from .pbr_visual_parameters import PbrVisualParameterRevision
from .visual_material_library import VisualMaterialLibraryRevision

BLENDER_SCENE_PACKAGE_CONTRACT = "packlab.blender-scene-package.v1"
BLENDER_SCENE_PACKAGE_SCHEMA_VERSION = 1
BLENDER_SCENE_MANIFEST_FILENAME = "blender_scene_manifest.json"
BLENDER_SCENE_RUNNER_FILENAME = "blender_scene_runner.py"
MAX_SCENE_PACKAGE_BYTES = 4 * 1024 * 1024
MAX_SCENE_OBJECTS = 128
MAX_SCENE_MATERIALS = 64
MAX_SCENE_ARTWORKS = 32
MAX_REFERENCED_ASSET_BYTES = 256 * 1024 * 1024
MAX_TOTAL_REFERENCED_BYTES = 512 * 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class BlenderScenePackageError(ValueError):
    """Raised when scene inputs are stale, unsafe, unbounded, or ambiguous."""


@dataclass(frozen=True, slots=True)
class ProjectAssetReference:
    """Digest-bound asset path relative to the PackLab project root."""

    project_relative_path: str
    sha256: str
    byte_length: int

    def __post_init__(self) -> None:
        _safe_relative_path(self.project_relative_path)
        if not isinstance(self.sha256, str) or not _SHA256.fullmatch(self.sha256):
            raise BlenderScenePackageError("scene_asset_digest_invalid")
        if (
            isinstance(self.byte_length, bool)
            or not isinstance(self.byte_length, int)
            or not 1 <= self.byte_length <= MAX_REFERENCED_ASSET_BYTES
        ):
            raise BlenderScenePackageError("scene_asset_size_invalid")

    def as_dict(self, roles: tuple[str, ...]) -> dict[str, object]:
        return {
            "project_relative_path": self.project_relative_path,
            "sha256": self.sha256,
            "byte_length": self.byte_length,
            "roles": list(roles),
        }


@dataclass(frozen=True, slots=True)
class BlenderArtworkBinding:
    assignment: LabelArtworkAssignmentRevision
    placement: LabelZonePlacementRevision
    mapping: LabelArtworkMappingRevision
    artwork: LabelArtworkAssetRevision
    asset: ProjectAssetReference


@dataclass(frozen=True, slots=True)
class BlenderScenePackage:
    revision_id: str
    manifest_bytes: bytes
    runner_script: bytes
    contract: str = BLENDER_SCENE_PACKAGE_CONTRACT
    schema_version: int = BLENDER_SCENE_PACKAGE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.contract != BLENDER_SCENE_PACKAGE_CONTRACT
            or isinstance(self.schema_version, bool)
            or self.schema_version != BLENDER_SCENE_PACKAGE_SCHEMA_VERSION
            or not isinstance(self.manifest_bytes, bytes)
            or not 1 <= len(self.manifest_bytes) <= MAX_SCENE_PACKAGE_BYTES
            or not isinstance(self.runner_script, bytes)
            or not self.runner_script
            or self.revision_id
            != "blender-scene-package:"
            + _digest(
                {
                    "contract": self.contract,
                    "schema_version": self.schema_version,
                    "manifest_sha256": hashlib.sha256(self.manifest_bytes).hexdigest(),
                    "runner_sha256": hashlib.sha256(self.runner_script).hexdigest(),
                }
            )
        ):
            raise BlenderScenePackageError("blender_scene_package_invalid")

    def manifest(self) -> dict[str, object]:
        try:
            value = json.loads(self.manifest_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BlenderScenePackageError("blender_scene_package_manifest_invalid") from error
        if not isinstance(value, dict):
            raise BlenderScenePackageError("blender_scene_package_manifest_invalid")
        return value


def create_blender_scene_package(
    model: DesignModelRevision,
    cad_export: CadMeshExportRevision,
    cad_glb_asset: ProjectAssetReference,
    material_project: ComponentMaterialProjectDocument,
    material_library: VisualMaterialLibraryRevision,
    *,
    pbr_parameters: tuple[PbrVisualParameterRevision, ...] = (),
    artwork_bindings: tuple[BlenderArtworkBinding, ...] = (),
) -> BlenderScenePackage:
    """Create stable JSON and a static validator script without embedding user code."""
    _validate_sources(model, cad_export, cad_glb_asset, material_project, material_library)
    if not isinstance(pbr_parameters, tuple) or any(
        not isinstance(item, PbrVisualParameterRevision) for item in pbr_parameters
    ):
        raise BlenderScenePackageError("scene_pbr_parameters_must_be_tuple")
    if not isinstance(artwork_bindings, tuple) or any(
        not isinstance(item, BlenderArtworkBinding) for item in artwork_bindings
    ):
        raise BlenderScenePackageError("scene_artwork_bindings_must_be_tuple")

    components, material_ids = _component_records(
        model, material_project, material_library, pbr_parameters
    )
    if len(components) > MAX_SCENE_OBJECTS:
        raise BlenderScenePackageError("scene_object_count_limit_exceeded")
    if len(material_ids) > MAX_SCENE_MATERIALS:
        raise BlenderScenePackageError("scene_material_count_limit_exceeded")
    if len(artwork_bindings) > MAX_SCENE_ARTWORKS:
        raise BlenderScenePackageError("scene_artwork_count_limit_exceeded")

    artworks = tuple(
        sorted(
            (_artwork_record(model, cad_export, item) for item in artwork_bindings),
            key=lambda item: (str(item["zone_id"]), str(item["variant_id"])),
        )
    )
    if len({(item["zone_id"], item["variant_id"]) for item in artworks}) != len(artworks):
        raise BlenderScenePackageError("scene_artwork_binding_duplicate")

    assets_by_path: dict[str, tuple[ProjectAssetReference, set[str]]] = {}
    _add_asset(assets_by_path, cad_glb_asset, "design_model_glb")
    for item in artwork_bindings:
        _add_asset(assets_by_path, item.asset, "label_artwork")
    total_bytes = sum(reference.byte_length for reference, _ in assets_by_path.values())
    if total_bytes > MAX_TOTAL_REFERENCED_BYTES:
        raise BlenderScenePackageError("scene_total_asset_bytes_limit_exceeded")
    assets = [
        assets_by_path[path][0].as_dict(tuple(sorted(assets_by_path[path][1])))
        for path in sorted(assets_by_path)
    ]
    body: dict[str, object] = {
        "contract": BLENDER_SCENE_PACKAGE_CONTRACT,
        "schema_version": BLENDER_SCENE_PACKAGE_SCHEMA_VERSION,
        "supported_blender_major": 5,
        "source": {
            "design_model_revision_id": model.revision_id,
            "cad_export_contract": cad_export.contract,
            "cad_export_id": cad_export.export_id,
            "cad_export_glb_manifest_id": cad_export.glb_manifest_id,
            "cad_export_glb_manifest_sha256": cad_export.glb_manifest_sha256,
            "cad_glb_sha256": cad_export.glb_sha256,
            "cad_brep_revision_id": cad_export.source_brep_revision_id,
            "cad_brep_geometry_sha256": cad_export.source_brep_geometry_sha256,
            "scale_state": model.scale_state.value,
            "coordinate_unit": model.coordinate_unit,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "material_project_revision_id": material_project.revision_id,
            "material_library_revision_id": material_library.revision_id,
        },
        "limits": {
            "max_scene_objects": MAX_SCENE_OBJECTS,
            "max_scene_materials": MAX_SCENE_MATERIALS,
            "max_scene_artworks": MAX_SCENE_ARTWORKS,
            "max_asset_bytes": MAX_REFERENCED_ASSET_BYTES,
            "max_total_asset_bytes": MAX_TOTAL_REFERENCED_BYTES,
        },
        "counts": {
            "objects": len(components),
            "materials": len(material_ids),
            "artworks": len(artworks),
            "assets": len(assets),
            "total_asset_bytes": total_bytes,
        },
        "components": components,
        "artworks": list(artworks),
        "assets": assets,
        "authority_semantics": "DERIVED_PRESENTATION_INPUT_ONLY",
        "mutates_design_model": False,
        "mutates_cad_brep": False,
        "physical_accuracy_inferred": False,
        "manufacturing_suitability_inferred": False,
        "material_certified": False,
        "regulatory_approval": False,
        "arbitrary_user_code_included": False,
    }
    body_digest = _digest(body)
    manifest = {"body": body, "content_sha256": body_digest}
    manifest_bytes = _canonical_json(manifest) + b"\n"
    if len(manifest_bytes) > MAX_SCENE_PACKAGE_BYTES:
        raise BlenderScenePackageError("blender_scene_package_size_limit_exceeded")
    runner_script = BLENDER_SCENE_RUNNER.encode("utf-8")
    package_id = "blender-scene-package:" + _digest(
        {
            "contract": BLENDER_SCENE_PACKAGE_CONTRACT,
            "schema_version": BLENDER_SCENE_PACKAGE_SCHEMA_VERSION,
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "runner_sha256": hashlib.sha256(runner_script).hexdigest(),
        }
    )
    return BlenderScenePackage(package_id, manifest_bytes, runner_script)


def _validate_sources(
    model: DesignModelRevision,
    cad_export: CadMeshExportRevision,
    cad_glb_asset: ProjectAssetReference,
    material_project: ComponentMaterialProjectDocument,
    material_library: VisualMaterialLibraryRevision,
) -> None:
    if not isinstance(model, DesignModelRevision):
        raise BlenderScenePackageError("design_model_revision_required")
    if not isinstance(cad_export, CadMeshExportRevision) or (
        cad_export.contract != CAD_MESH_EXPORT_CONTRACT
        or cad_export.authority_class != "DERIVED_CAD_PREVIEW_MESH_EXPORT"
        or cad_export.source_design_model_revision_id != model.revision_id
        or cad_export.scale_state != model.scale_state.value
        or cad_export.coordinate_unit != model.coordinate_unit
        or cad_export.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or cad_export.mold_use_authorized is not False
        or cad_export.source_brep_geometry_sha256 is None
        or not _SHA256.fullmatch(cad_export.source_brep_geometry_sha256)
    ):
        raise BlenderScenePackageError("scene_cad_export_source_mismatch")
    if not isinstance(cad_glb_asset, ProjectAssetReference):
        raise BlenderScenePackageError("scene_cad_glb_asset_required")
    if (
        cad_glb_asset.sha256 != cad_export.glb_sha256
        or cad_glb_asset.byte_length != cad_export.glb_size_bytes
    ):
        raise BlenderScenePackageError("scene_cad_glb_asset_digest_mismatch")
    if not isinstance(material_project, ComponentMaterialProjectDocument):
        raise BlenderScenePackageError("component_material_project_required")
    if material_project.design_model_revision_id != model.revision_id:
        raise BlenderScenePackageError("scene_material_project_model_stale")
    if not isinstance(material_library, VisualMaterialLibraryRevision):
        raise BlenderScenePackageError("visual_material_library_required")


def _component_records(
    model: DesignModelRevision,
    project: ComponentMaterialProjectDocument,
    library: VisualMaterialLibraryRevision,
    pbr_parameters: tuple[PbrVisualParameterRevision, ...],
) -> tuple[list[dict[str, object]], set[str]]:
    component_ids = {feature.component_id for feature in model.features}
    materials = {item.material_id: item for item in library.materials}
    pbr_by_component: dict[str, PbrVisualParameterRevision] = {}
    for parameters in pbr_parameters:
        if (
            parameters.source_design_model_revision_id != model.revision_id
            or parameters.component_id not in component_ids
            or parameters.component_id in pbr_by_component
        ):
            raise BlenderScenePackageError("scene_pbr_source_or_duplicate_mismatch")
        pbr_by_component[parameters.component_id] = parameters

    records: list[dict[str, object]] = []
    material_ids: set[str] = set()
    for entry in project.entries:
        if entry.component_id not in component_ids:
            raise BlenderScenePackageError("scene_component_reference_stale")
        state = entry.visual_state
        geometry = state.geometry_material_assignment
        content = state.content_appearance_assignment
        material = None
        pbr = pbr_by_component.get(entry.component_id)
        if geometry is not None:
            if (
                geometry.source_design_model_revision_id != model.revision_id
                or geometry.component_id != entry.component_id
                or geometry.material_library_revision_id != library.revision_id
                or geometry.material_id not in materials
            ):
                raise BlenderScenePackageError("scene_geometry_material_assignment_stale")
            material = materials[geometry.material_id]
            material_ids.add(geometry.material_id)
            if pbr is not None and (
                pbr.source_geometry_material_assignment_revision_id != geometry.revision_id
                or pbr.source_material_library_revision_id != library.revision_id
                or pbr.source_material_id != geometry.material_id
            ):
                raise BlenderScenePackageError("scene_pbr_assignment_stale")
        elif pbr is not None:
            raise BlenderScenePackageError("scene_pbr_without_geometry_material")
        records.append(
            {
                "component_id": entry.component_id,
                "visual_state_revision_id": state.revision_id,
                "geometry_material_assignment": geometry.as_dict() if geometry else None,
                "material_visual_reference": material.as_dict() if material else None,
                "pbr_visual_parameters": pbr.as_dict() if pbr else None,
                "content_appearance_assignment": content.as_dict() if content else None,
                "pcr_declaration": entry.pcr_declaration.as_dict()
                if entry.pcr_declaration
                else None,
                "pcr_visual_variants": [item.as_dict() for item in entry.pcr_visual_variants],
            }
        )
    if len(pbr_by_component) > MAX_SCENE_OBJECTS:
        raise BlenderScenePackageError("scene_pbr_count_limit_exceeded")
    return records, material_ids


def _artwork_record(
    model: DesignModelRevision,
    cad_export: CadMeshExportRevision,
    binding: BlenderArtworkBinding,
) -> dict[str, object]:
    assignment, placement, mapping, artwork, asset = (
        binding.assignment,
        binding.placement,
        binding.mapping,
        binding.artwork,
        binding.asset,
    )
    zone = placement.label_zone
    if (
        assignment.status != "ASSIGNED"
        or assignment.mapping_revision_id != mapping.revision_id
        or assignment.artwork_revision_id != artwork.revision_id
        or assignment.placement_revision_id != placement.revision_id
        or assignment.zone_id != placement.zone_id
        or assignment.zone_kind != zone.zone_kind.value
        or mapping.zone_id != placement.zone_id
        or mapping.placement_revision_id != placement.revision_id
        or mapping.source_artwork_revision_id != artwork.revision_id
        or mapping.source_artwork_sha256 != artwork.content_sha256
        or asset.sha256 != artwork.content_sha256
        or asset.byte_length != artwork.byte_size
        or zone.source_design_model_revision_id != model.revision_id
        or zone.source_brep_revision_id != cad_export.source_brep_revision_id
        or zone.source_brep_geometry_sha256 != cad_export.source_brep_geometry_sha256
    ):
        raise BlenderScenePackageError("scene_artwork_provenance_stale")
    return {
        "zone_id": zone.zone_id,
        "variant_id": assignment.variant_id,
        "assignment": assignment.as_dict(),
        "zone": {
            "zone_id": zone.zone_id,
            "zone_kind": zone.zone_kind.value,
            "source_design_model_revision_id": zone.source_design_model_revision_id,
            "source_brep_revision_id": zone.source_brep_revision_id,
            "source_brep_geometry_sha256": zone.source_brep_geometry_sha256,
            "component_id": zone.component_id,
            "feature_id": zone.feature_id,
            "scale_state": zone.scale_state.value,
            "coordinate_unit": zone.coordinate_unit,
            "boundary_normalized_uv": [
                placement.boundary.u_min,
                placement.boundary.v_min,
                placement.boundary.u_max,
                placement.boundary.v_max,
            ],
            "surface_frame": placement.surface_frame.as_dict(),
        },
        "placement_revision_id": placement.revision_id,
        "mapping": mapping.as_dict(),
        "artwork": artwork.as_dict(),
        "asset_project_relative_path": asset.project_relative_path,
        "physical_fit_verified": False,
        "geometry_authority_created": False,
    }


def _add_asset(
    assets: dict[str, tuple[ProjectAssetReference, set[str]]],
    reference: ProjectAssetReference,
    role: str,
) -> None:
    existing = assets.get(reference.project_relative_path)
    if existing is not None and (
        existing[0].sha256 != reference.sha256 or existing[0].byte_length != reference.byte_length
    ):
        raise BlenderScenePackageError("scene_asset_path_digest_conflict")
    if existing is None:
        assets[reference.project_relative_path] = (reference, {role})
    else:
        existing[1].add(role)


def _safe_relative_path(value: object) -> tuple[str, ...]:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 512
        or "\\" in value
        or "\x00" in value
        or value.startswith("/")
    ):
        raise BlenderScenePackageError("scene_asset_path_not_safe_relative")
    path = PurePosixPath(value)
    parts = path.parts
    if (
        path.is_absolute()
        or not parts
        or any(part in {".", ".."} or not _PATH_SEGMENT.fullmatch(part) for part in parts)
        or value != path.as_posix()
    ):
        raise BlenderScenePackageError("scene_asset_path_not_safe_relative")
    return parts


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise BlenderScenePackageError("scene_package_not_canonical_json") from error


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


BLENDER_SCENE_RUNNER = r'''"""PackLab static Blender scene-package validator; consumes JSON data only."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

import bpy

CONTRACT = "packlab.blender-scene-package.v1"
SCHEMA_VERSION = 1
SUPPORTED_BLENDER_MAJOR = 5
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_ASSET_BYTES = 256 * 1024 * 1024
MAX_TOTAL_ASSET_BYTES = 512 * 1024 * 1024


def safe_relative(value):
    if not isinstance(value, str) or not value or len(value) > 512 or "\\" in value or value.startswith("/"):
        raise ValueError("asset_path_invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("asset_path_invalid")
    if any(not part[0].isalnum() or not all(ch.isalnum() or ch in "_.-" for ch in part) for part in path.parts):
        raise ValueError("asset_path_invalid")
    return path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--manifest", default="blender_scene_manifest.json")
    args = parser.parse_args(tail)
    root = Path(args.project_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("project_root_invalid")
    manifest_relative = safe_relative(args.manifest)
    manifest_path = root.joinpath(*manifest_relative.parts).resolve(strict=True)
    if not manifest_path.is_relative_to(root) or not manifest_path.is_file():
        raise ValueError("manifest_path_invalid")
    raw = manifest_path.read_bytes()
    if not raw or len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError("manifest_size_invalid")
    document = json.loads(raw.decode("utf-8"), parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("nonfinite_json")))
    if not isinstance(document, dict) or set(document) != {"body", "content_sha256"}:
        raise ValueError("manifest_envelope_invalid")
    body = document["body"]
    if not isinstance(body, dict) or body.get("contract") != CONTRACT or body.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("manifest_contract_invalid")
    if hashlib.sha256(canonical(body)).hexdigest() != document["content_sha256"]:
        raise ValueError("manifest_digest_invalid")
    if bpy.app.version[0] != body.get("supported_blender_major", SUPPORTED_BLENDER_MAJOR):
        raise ValueError("blender_version_policy_mismatch")
    limits = body.get("limits")
    counts = body.get("counts")
    components = body.get("components")
    artworks = body.get("artworks")
    if not isinstance(limits, dict) or not isinstance(counts, dict):
        raise ValueError("manifest_bounds_invalid")
    if not isinstance(components, list) or len(components) > 128:
        raise ValueError("object_count_invalid")
    if not isinstance(artworks, list) or len(artworks) > 32:
        raise ValueError("artwork_count_invalid")
    if (
        counts.get("objects") != len(components)
        or counts.get("artworks") != len(artworks)
        or counts.get("materials", 0) > 64
        or counts.get("objects") > limits.get("max_scene_objects", 128)
        or counts.get("materials", 0) > limits.get("max_scene_materials", 64)
        or counts.get("artworks") > limits.get("max_scene_artworks", 32)
    ):
        raise ValueError("manifest_counts_invalid")
    assets = body.get("assets")
    if not isinstance(assets, list) or len(assets) > 1 + 32:
        raise ValueError("asset_count_invalid")
    total = 0
    seen_paths = set()
    for asset in assets:
        if not isinstance(asset, dict) or set(asset) != {"project_relative_path", "sha256", "byte_length", "roles"}:
            raise ValueError("asset_record_invalid")
        relative = safe_relative(asset["project_relative_path"])
        if asset["project_relative_path"] in seen_paths:
            raise ValueError("asset_path_duplicate")
        seen_paths.add(asset["project_relative_path"])
        size = asset["byte_length"]
        digest = asset["sha256"]
        if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= MAX_ASSET_BYTES:
            raise ValueError("asset_size_invalid")
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("asset_digest_invalid")
        total += size
        if total > MAX_TOTAL_ASSET_BYTES:
            raise ValueError("total_asset_size_invalid")
        asset_path = root.joinpath(*relative.parts).resolve(strict=True)
        if not asset_path.is_relative_to(root) or not asset_path.is_file():
            raise ValueError("asset_outside_project")
        hasher = hashlib.sha256()
        measured = 0
        with asset_path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                measured += len(chunk)
                if measured > size:
                    raise ValueError("asset_size_mismatch")
                hasher.update(chunk)
        if measured != size or hasher.hexdigest() != digest:
            raise ValueError("asset_digest_mismatch")
    print("PACKLAB_SCENE_PACKAGE_VALID", bpy.app.version_string)


if __name__ == "__main__":
    main()
'''


__all__ = [
    "BLENDER_SCENE_MANIFEST_FILENAME",
    "BLENDER_SCENE_PACKAGE_CONTRACT",
    "BLENDER_SCENE_PACKAGE_SCHEMA_VERSION",
    "BLENDER_SCENE_RUNNER_FILENAME",
    "BlenderArtworkBinding",
    "BlenderScenePackage",
    "BlenderScenePackageError",
    "MAX_REFERENCED_ASSET_BYTES",
    "MAX_SCENE_ARTWORKS",
    "MAX_SCENE_MATERIALS",
    "MAX_SCENE_OBJECTS",
    "ProjectAssetReference",
    "create_blender_scene_package",
]
