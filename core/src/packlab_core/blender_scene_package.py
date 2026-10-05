"""Deterministic, bounded, data-only input packages for Blender scene work."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from .blender_label_render_overlay import (
    LabelRenderOverlayError,
    create_label_render_overlay_binding,
)
from .cad_brep import CadBrepRepresentationRevision
from .cad_feature_map import map_design_model_features_to_brep
from .cad_label_surface_analysis import CadLabelSurfaceAnalysis
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
from .label_metric_surface_binding import LabelMetricSurfaceBinding
from .label_zone_placement import LabelZonePlacementRevision
from .pbr_visual_parameters import PbrVisualParameterRevision
from .visual_material_library import VisualMaterialLibraryRevision

BLENDER_SCENE_PACKAGE_CONTRACT = "packlab.blender-scene-package.v2"
BLENDER_SCENE_PACKAGE_SCHEMA_VERSION = 2
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
    analysis: CadLabelSurfaceAnalysis | None = None
    metric_binding: LabelMetricSurfaceBinding | None = None


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
    brep_representation: CadBrepRepresentationRevision | None = None,
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
    scene_contract: dict[str, object] | None = None
    if brep_representation is not None:
        scene_contract = _scene_authority_record(
            model, cad_export, brep_representation, material_project
        )
        for binding in artwork_bindings:
            if binding.analysis is None or binding.metric_binding is None:
                raise BlenderScenePackageError("scene_artwork_exact_metric_binding_required")
        scene_contract["overlays"] = [
            _overlay_record(model, brep_representation, item)
            for item in sorted(
                artwork_bindings,
                key=lambda item: (item.placement.zone_id, item.assignment.variant_id),
            )
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
        "scene": scene_contract,
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


def _scene_authority_record(
    model: DesignModelRevision,
    cad_export: CadMeshExportRevision,
    representation: CadBrepRepresentationRevision,
    project: ComponentMaterialProjectDocument,
) -> dict[str, object]:
    if (
        representation.revision_id != cad_export.source_brep_revision_id
        or representation.geometry_sha256 != cad_export.source_brep_geometry_sha256
        or representation.source_design_model_revision_id != model.revision_id
        or not representation.source_feature_ids
    ):
        raise BlenderScenePackageError("scene_brep_export_lineage_mismatch")
    features = {item.feature_id: item for item in model.features}
    try:
        feature_mapping = map_design_model_features_to_brep(model, representation)
    except (TypeError, ValueError) as error:
        raise BlenderScenePackageError("scene_brep_source_feature_resolution_failed") from error
    mapped_ids = {item.feature_id for item in feature_mapping.references}
    if any(feature_id not in mapped_ids for feature_id in representation.source_feature_ids):
        raise BlenderScenePackageError("scene_brep_source_feature_resolution_failed")
    lineage = [features.get(feature_id) for feature_id in representation.source_feature_ids]
    if any(item is None for item in lineage):
        raise BlenderScenePackageError("scene_brep_source_feature_unresolved")
    component_ids = {item.component_id for item in lineage if item is not None}
    if len(component_ids) != 1:
        raise BlenderScenePackageError("component_mesh_partition_unavailable")
    component_id = next(iter(component_ids))
    entries = [item for item in project.entries if item.component_id == component_id]
    if len(entries) != 1:
        raise BlenderScenePackageError("scene_single_component_material_entry_required")
    assignment = entries[0].visual_state.geometry_material_assignment
    if assignment is None or assignment.component_id != component_id:
        raise BlenderScenePackageError("scene_single_component_geometry_material_required")
    return {
        "contract": "packlab.blender-scene-construction.v1",
        "geometry_binding": {
            "mode": "WHOLE_SOLID_SINGLE_COMPONENT",
            "source_brep_revision_id": representation.revision_id,
            "source_brep_geometry_sha256": representation.geometry_sha256,
            "source_feature_ids": sorted(representation.source_feature_ids),
            "feature_mapping_revision_id": feature_mapping.revision_id,
            "component_id": component_id,
            "geometry_material_assignment_revision_id": assignment.revision_id,
            "triangle_partition_created": False,
            "material_slots_synthesized": False,
        },
        "source_to_glb_viewer_transform": cad_export.as_dict().get("coordinate_transform")
        or {
            "kind": "uniform_scale",
            "source_unit": model.coordinate_unit,
            "target_unit": "meters"
            if model.coordinate_unit == "mm_unverified"
            else "relative_viewer_units",
            "scale": [0.001, 0.001, 0.001]
            if model.coordinate_unit == "mm_unverified"
            else [1.0, 1.0, 1.0],
            "inverse_scale": [1000.0, 1000.0, 1000.0]
            if model.coordinate_unit == "mm_unverified"
            else [1.0, 1.0, 1.0],
            "reversible": True,
            "source_coordinates_preserved_in_buffer": True,
            "physical_authority_upgraded": False,
        },
        "authority_semantics": "DERIVED_PRESENTATION_ONLY",
    }


def _overlay_record(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    binding: BlenderArtworkBinding,
) -> dict[str, object]:
    if binding.analysis is None or binding.metric_binding is None:
        raise BlenderScenePackageError("scene_artwork_exact_metric_binding_required")
    try:
        overlay = create_label_render_overlay_binding(
            model,
            representation,
            binding.analysis,
            binding.metric_binding,
            binding.placement,
            binding.mapping,
            binding.assignment,
            binding.artwork,
        )
    except LabelRenderOverlayError as error:
        raise BlenderScenePackageError(str(error)) from error
    except (TypeError, ValueError) as error:
        raise BlenderScenePackageError("scene_artwork_overlay_binding_invalid") from error
    record = overlay.as_dict()
    geometry = record.get("geometry")
    if not isinstance(geometry, dict):
        raise BlenderScenePackageError("scene_artwork_overlay_geometry_invalid")
    record["asset_project_relative_path"] = binding.asset.project_relative_path
    record["asset_sha256"] = binding.asset.sha256
    record["asset_byte_length"] = binding.asset.byte_length
    return record


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


BLENDER_SCENE_RUNNER = r'''"""PackLab static Blender scene builder; consumes JSON data only."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

import bpy

CONTRACT = "packlab.blender-scene-package.v2"
SCHEMA_VERSION = 2
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
    parser.add_argument("--result", default="scene_result_manifest.json")
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
    runner_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    package_revision_id = "blender-scene-package:" + hashlib.sha256(canonical({
        "contract": CONTRACT,
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "runner_sha256": runner_sha256,
    })).hexdigest()
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
    scene = body.get("scene")
    if scene is not None:
        _build_scene(root, body, assets, scene, args.result, package_revision_id)
    print("PACKLAB_SCENE_PACKAGE_VALID", bpy.app.version_string)


def _material_for(component):
    reference = component.get("material_visual_reference")
    assignment = component.get("geometry_material_assignment")
    if not isinstance(reference, dict) or not isinstance(assignment, dict):
        raise ValueError("scene_component_material_missing")
    display = reference.get("display_metadata", {}).get("base_color_rgba")
    pbr = reference.get("pbr_visual_reference", {})
    parameters = component.get("pbr_visual_parameters")
    if not isinstance(display, list) or len(display) != 4 or not isinstance(pbr, dict):
        raise ValueError("scene_component_material_invalid")
    material = bpy.data.materials.new("PackLabGeometry_" + str(reference.get("material_id")))
    rgba = tuple(float(value) for value in display)
    if isinstance(parameters, dict):
        rgba = tuple(float(value) for value in parameters["base_color_rgb"]) + (float(parameters["opacity_factor"]),)
    material.diffuse_color = rgba
    material.use_nodes = True
    shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        raise ValueError("scene_principled_shader_unavailable")
    shader.inputs["Base Color"].default_value = rgba
    shader.inputs["Roughness"].default_value = float(parameters["roughness_factor"] if isinstance(parameters, dict) else pbr["roughness_factor"])
    shader.inputs["Metallic"].default_value = float(pbr["metallic_factor"])
    if isinstance(parameters, dict):
        transmission = shader.inputs.get("Transmission Weight") or shader.inputs.get("Transmission")
        ior = shader.inputs.get("IOR")
        if transmission is not None:
            transmission.default_value = float(parameters["transmission_factor"])
        if ior is not None:
            ior.default_value = float(parameters["ior"])
    material["packlab_geometry_material_assignment_revision_id"] = assignment["revision_id"]
    material["packlab_visual_only"] = True
    return material


def _image_material(overlay, image_path):
    image = bpy.data.images.load(str(image_path), check_existing=False)
    if image is None or image.size[0] <= 0 or image.size[1] <= 0:
        raise ValueError("scene_png_texture_load_failed")
    material = bpy.data.materials.new("PackLabArtwork_" + str(overlay["zone_id"]))
    material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        raise ValueError("scene_principled_shader_unavailable")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.extension = "CLIP"
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    if "Alpha" in shader.inputs:
        material.node_tree.links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    material["packlab_artwork_revision_id"] = overlay["artwork_revision_id"]
    material["packlab_presentation_only"] = True
    return material, image


def _artwork_uv(overlay, u, v, width, height):
    mapping = overlay["geometry"]["artwork_mapping"]
    if overlay["geometry"]["uv_orientation"] == "REVERSED_U":
        boundary = overlay["geometry"]["placement_boundary_normalized_uv"]
        u = float(boundary[0]) + float(boundary[2]) - u
    source_u = (u - float(mapping["translate_u"])) / float(mapping["scale_u"])
    source_v = (v - float(mapping["translate_v"])) / float(mapping["scale_v"])
    if overlay["geometry"].get("artwork_pixel_origin") != "TOP_LEFT":
        raise ValueError("scene_artwork_pixel_origin_unsupported")
    return (source_u / float(width), 1.0 - source_v / float(height))


def _create_overlay(overlay, root, base_matrix):
    geometry = overlay["geometry"]
    mode = overlay["mapping_mode"]
    verts = []
    faces = []
    uv_coords = []
    if mode == "PLANAR_RECTANGULAR":
        corners = geometry.get("zone_corners_mm_unverified")
        if not isinstance(corners, list) or len(corners) != 4:
            raise ValueError("scene_planar_overlay_geometry_invalid")
        from mathutils import Vector
        verts = [tuple(base_matrix @ Vector(tuple(float(c) for c in point))) for point in corners]
        faces = [(0, 1, 2, 3)]
        boundary = geometry["placement_boundary_normalized_uv"]
        uv_coords = [
            (float(boundary[0]), float(boundary[1])),
            (float(boundary[2]), float(boundary[1])),
            (float(boundary[2]), float(boundary[3])),
            (float(boundary[0]), float(boundary[3])),
        ]
    elif mode == "CYLINDRICAL_WRAP":
        theta0 = float(geometry["angular_start_radians"])
        theta1 = float(geometry["angular_end_radians"])
        z0 = float(geometry["axial_start_mm_unverified"])
        z1 = float(geometry["axial_end_mm_unverified"])
        radius = float(geometry["radius_mm_unverified"])
        center = geometry["center_mm_unverified"]
        span = theta1 - theta0
        boundary = geometry["placement_boundary_normalized_uv"]
        segments = max(1, min(128, int(__import__("math").ceil(abs(span) / (2.0 * 3.141592653589793) * 64.0))))
        for index in range(segments + 1):
            u = index / segments
            theta = theta0 + span * u
            x = float(center[0]) + (radius + float(overlay["renderer_only_offset_mm_unverified"])) * __import__("math").sin(theta)
            y = float(center[1]) + (radius + float(overlay["renderer_only_offset_mm_unverified"])) * __import__("math").cos(theta)
            from mathutils import Vector
            verts.extend((
                tuple(base_matrix @ Vector((x, y, z0))),
                tuple(base_matrix @ Vector((x, y, z1))),
            ))
            uv_u = float(boundary[0]) + (float(boundary[2]) - float(boundary[0])) * u
            uv_coords.extend(((uv_u, float(boundary[1])), (uv_u, float(boundary[3]))))
        for index in range(segments):
            start = index * 2
            faces.append((start, start + 2, start + 3, start + 1))
    else:
        raise ValueError("scene_overlay_mapping_unsupported")
    mesh = bpy.data.meshes.new("PackLabOverlayMesh_" + str(overlay["zone_id"]))
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="PackLabRendererUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = _artwork_uv(
                overlay, uv_coords[vertex_index][0], uv_coords[vertex_index][1],
                geometry["artwork_width"], geometry["artwork_height"]
            )
    obj = bpy.data.objects.new("PackLabLabelOverlay_" + str(overlay["zone_id"]), mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["packlab_overlay_binding_revision_id"] = overlay["revision_id"]
    obj["packlab_presentation_only"] = True
    asset_path = safe_relative(overlay["asset_project_relative_path"])
    image_path = root.joinpath(*asset_path.parts).resolve(strict=True)
    if not image_path.is_relative_to(root):
        raise ValueError("scene_overlay_asset_outside_project")
    with image_path.open("rb") as artwork_stream:
        if artwork_stream.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("scene_png_signature_invalid")
    material, image = _image_material(overlay, image_path)
    obj.data.materials.append(material)
    return obj, image


def _build_scene(root, body, assets, scene, result_relative, package_revision_id):
    if scene.get("contract") != "packlab.blender-scene-construction.v1":
        raise ValueError("scene_contract_invalid")
    binding = scene.get("geometry_binding")
    if not isinstance(binding, dict) or binding.get("mode") != "WHOLE_SOLID_SINGLE_COMPONENT":
        raise ValueError("scene_geometry_binding_invalid")
    if (
        binding.get("source_brep_revision_id") != body.get("source", {}).get("cad_brep_revision_id")
        or binding.get("source_brep_geometry_sha256")
        != body.get("source", {}).get("cad_brep_geometry_sha256")
    ):
        raise ValueError("scene_geometry_binding_source_mismatch")
    if binding.get("triangle_partition_created") is not False or binding.get("material_slots_synthesized") is not False:
        raise ValueError("scene_component_partition_forbidden")
    component_id = binding.get("component_id")
    matching = [item for item in body["components"] if item.get("component_id") == component_id]
    if len(matching) != 1:
        raise ValueError("scene_component_material_resolution_invalid")
    glb_record = next((item for item in assets if "design_model_glb" in item.get("roles", [])), None)
    if glb_record is None:
        raise ValueError("scene_glb_asset_missing")
    glb_relative = safe_relative(glb_record["project_relative_path"])
    glb_path = root.joinpath(*glb_relative.parts).resolve(strict=True)
    if not glb_path.is_relative_to(root):
        raise ValueError("scene_glb_outside_project")
    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    imported = [item for item in bpy.data.objects if item.name not in before and item.type == "MESH"]
    if len(imported) != 1:
        raise ValueError("scene_fused_glb_must_import_as_one_mesh")
    base = imported[0]
    if len(base.data.materials) > 1:
        raise ValueError("scene_glb_material_slots_unexpected")
    base.data.materials.clear()
    material = _material_for(matching[0])
    base.data.materials.append(material)
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    transmission = shader.inputs.get("Transmission Weight") or shader.inputs.get("Transmission")
    ior = shader.inputs.get("IOR")
    overlay_facts = []
    assets_by_path = {item["project_relative_path"]: item for item in assets}
    for overlay in scene.get("overlays", []):
        if overlay.get("mapping_mode") not in {"PLANAR_RECTANGULAR", "CYLINDRICAL_WRAP"}:
            raise ValueError("scene_overlay_mapping_unsupported")
        offset = overlay.get("renderer_only_offset_mm_unverified")
        if isinstance(offset, bool) or not isinstance(offset, (int, float)) or float(offset) != 0.001:
            raise ValueError("scene_renderer_offset_unsupported")
        if overlay.get("artwork_sha256") != overlay.get("asset_sha256"):
            raise ValueError("scene_overlay_asset_digest_binding_mismatch")
        if overlay.get("geometry", {}).get("artwork_media_type") != "image/png":
            raise ValueError("scene_svg_scene_texturing_unsupported")
        overlay_geometry = overlay.get("geometry", {})
        artwork_asset = assets_by_path.get(overlay.get("asset_project_relative_path"))
        if (
            not isinstance(artwork_asset, dict)
            or "label_artwork" not in artwork_asset.get("roles", [])
            or artwork_asset.get("sha256") != overlay.get("asset_sha256")
            or artwork_asset.get("byte_length") != overlay.get("asset_byte_length")
        ):
            raise ValueError("scene_overlay_asset_reference_mismatch")
        transform = overlay.get("source_to_glb_viewer_transform", {})
        scale_values = transform.get("scale")
        if (
            transform.get("kind") != "uniform_scale"
            or transform.get("source_unit") != "mm_unverified"
            or transform.get("target_unit") != "meters"
            or not isinstance(scale_values, list)
            or scale_values != [0.001, 0.001, 0.001]
            or transform.get("inverse_scale") != [1000.0, 1000.0, 1000.0]
        ):
            raise ValueError("scene_overlay_viewer_transform_invalid")
        obj, image = _create_overlay(overlay, root, base.matrix_world.copy())
        overlay_facts.append({
            "binding_revision_id": overlay["revision_id"],
            "object_name": obj.name,
            "mapping_mode": overlay["mapping_mode"],
            "vertex_count": len(obj.data.vertices),
            "polygon_count": len(obj.data.polygons),
            "uv_layer_count": len(obj.data.uv_layers),
            "uv_minimum": [
                min(float(loop.uv[axis]) for loop in obj.data.uv_layers[0].data)
                for axis in range(2)
            ],
            "uv_maximum": [
                max(float(loop.uv[axis]) for loop in obj.data.uv_layers[0].data)
                for axis in range(2)
            ],
            "uv_first_loop": [
                float(obj.data.uv_layers[0].data[0].uv[0]),
                float(obj.data.uv_layers[0].data[0].uv[1]),
            ],
            "image_size": [int(image.size[0]), int(image.size[1])],
            "image_loaded": True,
        })
    if not overlay_facts:
        raise ValueError("scene_exact_overlay_required")
    if len(base.data.uv_layers) != 0:
        raise ValueError("scene_base_mesh_uv_authority_forbidden")
    result = {
        "contract": "packlab.blender-scene-result.v1",
        "scene_package_contract": body["contract"],
        "scene_package_revision_id": package_revision_id,
        "scene_package_sha256": hashlib.sha256(canonical(body)).hexdigest(),
        "blender": {
            "version_string": bpy.app.version_string,
            "version": list(bpy.app.version),
            "build_hash": _decode_fact(bpy.app.build_hash),
            "build_branch": _decode_fact(bpy.app.build_branch),
            "build_date": _decode_fact(bpy.app.build_date),
            "background": bool(bpy.app.background),
        },
        "source": body["source"],
        "geometry_binding": binding,
        "base_object": {
            "name": base.name,
            "mesh_name": base.data.name,
            "vertex_count": len(base.data.vertices),
            "polygon_count": len(base.data.polygons),
            "material_slot_count": len(base.material_slots),
            "uv_layer_count": len(base.data.uv_layers),
            "assigned_component_id": component_id,
            "geometry_material_assignment_revision_id": binding["geometry_material_assignment_revision_id"],
            "material_id": matching[0]["material_visual_reference"]["material_id"],
            "pbr_visual_parameter_revision_id": (
                matching[0]["pbr_visual_parameters"]["revision_id"]
                if matching[0].get("pbr_visual_parameters")
                else None
            ),
            "effective_shader_values": {
                "base_color_rgba": list(shader.inputs["Base Color"].default_value),
                "roughness_factor": float(shader.inputs["Roughness"].default_value),
                "metallic_factor": float(shader.inputs["Metallic"].default_value),
                "transmission_factor": float(transmission.default_value) if transmission else 0.0,
                "ior": float(ior.default_value) if ior else None,
            },
        },
        "overlays": overlay_facts,
        "source_to_render_transform": scene["source_to_glb_viewer_transform"],
        "blender_imported_base_matrix_world": [list(row) for row in base.matrix_world],
        "renderer_only_offsets_are_non_physical": True,
        "network_access": "NONE",
        "automatic_downloads": False,
        "mutates_design_model": False,
        "mutates_cad_brep": False,
        "physical_accuracy_inferred": False,
        "physical_fit_verified": False,
        "material_certified": False,
        "manufacturing_suitability_inferred": False,
        "regulatory_approval": False,
    }
    result_bytes = canonical(result) + b"\n"
    result_path = root.joinpath(*safe_relative(result_relative).parts).resolve()
    if not result_path.is_relative_to(root):
        raise ValueError("scene_result_path_invalid")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    if not result_path.parent.resolve().is_relative_to(root):
        raise ValueError("scene_result_path_invalid")
    result_path.write_bytes(result_bytes)


def _decode_fact(value):
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)


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
