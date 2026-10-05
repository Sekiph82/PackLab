"""Offline, digest-bound GLB export from a validated Blender scene package."""

from __future__ import annotations

import json
import math
import re
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from . import blender_scene_package as scene_package_module
from .blender_scene_package import BlenderScenePackage

BLENDER_GLB_EXPORT_CONTRACT = "packlab.blender-glb-export.v1"
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_MAX_TIMEOUT_SECONDS = 600.0


class BlenderGlbExportError(ValueError):
    """Raised when a GLB export request or its output fails validation."""


@dataclass(frozen=True, slots=True)
class BlenderGlbExportRequest:
    output_relative_path: str = "exports/packlab_scene.glb"
    sidecar_relative_path: str = "exports/packlab_scene.manifest.json"
    timeout_seconds: float = 180.0

    def __post_init__(self) -> None:
        _safe_relative(self.output_relative_path)
        _safe_relative(self.sidecar_relative_path)
        if self.output_relative_path == self.sidecar_relative_path:
            raise BlenderGlbExportError("glb_export_paths_must_differ")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(self.timeout_seconds)
            or not 1.0 <= self.timeout_seconds <= _MAX_TIMEOUT_SECONDS
        ):
            raise BlenderGlbExportError("glb_export_timeout_invalid")


def build_blender_glb_export_runner(
    package: BlenderScenePackage,
    request: BlenderGlbExportRequest | None = None,
) -> bytes:
    """Append a fixed export/validation stage to PackLab's fixed scene runner."""
    if request is None:
        request = BlenderGlbExportRequest()
    if (
        not isinstance(package, BlenderScenePackage)
        or package.runner_script != scene_package_module.BLENDER_SCENE_RUNNER.encode("utf-8")
        or not isinstance(request, BlenderGlbExportRequest)
    ):
        raise BlenderGlbExportError("glb_export_runner_untrusted")
    body = package.manifest().get("body")
    if not isinstance(body, dict) or body.get("contract") != "packlab.blender-scene-package.v2":
        raise BlenderGlbExportError("glb_export_scene_package_invalid")
    job = {
        "contract": BLENDER_GLB_EXPORT_CONTRACT,
        "scene_package_revision_id": package.revision_id,
        "scene_package_sha256": package.manifest()["content_sha256"],
        "source": body["source"],
        "artworks": body["artworks"],
        "output_relative_path": request.output_relative_path,
        "sidecar_relative_path": request.sidecar_relative_path,
    }
    payload = json.dumps(job, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return package.runner_script.rstrip() + b"\n\n" + _export_stage(repr(payload))


def run_blender_glb_export(
    executable: str | Path,
    runner_script: str | Path,
    project_root: str | Path,
    *,
    manifest_relative_path: str = "blender_scene_manifest.json",
    scene_result_relative_path: str = "scene_result_manifest.json",
    timeout_seconds: float = 180.0,
    runner=subprocess.run,
) -> subprocess.CompletedProcess[str]:
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or not 1.0 <= timeout_seconds <= _MAX_TIMEOUT_SECONDS
    ):
        raise BlenderGlbExportError("glb_export_timeout_invalid")
    for value in (manifest_relative_path, scene_result_relative_path):
        _safe_relative(value)
    root = Path(project_root)
    if not root.is_dir() or not Path(executable).is_file() or not Path(runner_script).is_file():
        raise BlenderGlbExportError("glb_export_input_path_unavailable")
    command = [
        str(executable),
        "--background",
        "--factory-startup",
        "--disable-autoexec",
        "--python",
        str(runner_script),
        "--",
        "--project-root",
        str(root),
        "--manifest",
        manifest_relative_path,
        "--result",
        scene_result_relative_path,
    ]
    try:
        completed = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=float(timeout_seconds),
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        raise BlenderGlbExportError("blender_glb_export_timed_out") from error
    except OSError as error:
        raise BlenderGlbExportError("blender_glb_export_launch_failed") from error
    if completed.returncode != 0:
        raise BlenderGlbExportError("blender_glb_export_process_failed")
    if "PACKLAB_BLENDER_GLB_EXPORT_VALID " not in completed.stdout:
        raise BlenderGlbExportError("blender_glb_export_semantic_validation_failed")
    return completed


def validate_glb_bytes(data: bytes) -> dict[str, object]:
    """Validate GLB v2 framing, embedded resources, names and bound materials."""
    if not isinstance(data, bytes) or len(data) < 20 or data[:4] != b"glTF":
        raise BlenderGlbExportError("glb_header_invalid")
    version, total_length = struct.unpack_from("<II", data, 4)
    if version != 2 or total_length != len(data):
        raise BlenderGlbExportError("glb_length_or_version_invalid")
    chunks: list[tuple[int, bytes]] = []
    offset = 12
    while offset < len(data):
        if offset + 8 > len(data):
            raise BlenderGlbExportError("glb_chunk_header_invalid")
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        chunk_end = offset + 8 + chunk_length
        if chunk_length % 4 != 0 or chunk_end > len(data):
            raise BlenderGlbExportError("glb_chunk_length_invalid")
        chunks.append((chunk_type, data[offset + 8 : chunk_end]))
        offset = chunk_end
    if offset != len(data) or not chunks or chunks[0][0] != 0x4E4F534A:
        raise BlenderGlbExportError("glb_json_chunk_invalid")
    if any(kind not in {0x4E4F534A, 0x004E4942} for kind, _ in chunks):
        raise BlenderGlbExportError("glb_chunk_type_unsupported")
    if sum(1 for kind, _ in chunks if kind == 0x4E4F534A) != 1:
        raise BlenderGlbExportError("glb_json_chunk_duplicate")
    try:
        document = json.loads(chunks[0][1].decode("utf-8").rstrip(" \t\r\n\0"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BlenderGlbExportError("glb_json_document_invalid") from error
    if (
        not isinstance(document, dict)
        or not isinstance(document.get("asset"), dict)
        or document["asset"].get("version") != "2.0"
    ):
        raise BlenderGlbExportError("glb_document_contract_invalid")
    if _contains_uri(document):
        raise BlenderGlbExportError("glb_external_uri_forbidden")
    images = document.get("images", [])
    materials = document.get("materials", [])
    textures = document.get("textures", [])
    nodes = document.get("nodes", [])
    views = document.get("bufferViews", [])
    buffers = document.get("buffers", [])
    if (
        not isinstance(images, list)
        or not isinstance(materials, list)
        or not isinstance(textures, list)
    ):
        raise BlenderGlbExportError("glb_media_records_invalid")
    if not images or not materials or not textures:
        raise BlenderGlbExportError("glb_material_texture_missing")
    if not isinstance(views, list) or not isinstance(buffers, list):
        raise BlenderGlbExportError("glb_buffer_records_invalid")
    binary_chunks = [chunk for kind, chunk in chunks if kind == 0x004E4942]
    if len(binary_chunks) != 1 or len(buffers) != 1 or not isinstance(buffers[0], dict):
        raise BlenderGlbExportError("glb_binary_buffer_missing")
    binary_length = buffers[0].get("byteLength")
    if (
        isinstance(binary_length, bool)
        or not isinstance(binary_length, int)
        or binary_length < 0
        or binary_length > len(binary_chunks[0])
    ):
        raise BlenderGlbExportError("glb_binary_buffer_length_invalid")
    for view in views:
        if (
            not isinstance(view, dict)
            or view.get("buffer") != 0
            or isinstance(view.get("byteLength"), bool)
            or not isinstance(view.get("byteLength"), int)
            or isinstance(view.get("byteOffset", 0), bool)
            or not isinstance(view.get("byteOffset", 0), int)
            or view.get("byteOffset", 0) < 0
            or view.get("byteOffset", 0) + view["byteLength"] > binary_length
        ):
            raise BlenderGlbExportError("glb_buffer_view_invalid")
    if any(
        not isinstance(image, dict)
        or isinstance(image.get("bufferView"), bool)
        or not isinstance(image.get("bufferView"), int)
        or not 0 <= image["bufferView"] < len(views)
        or image.get("mimeType") not in {"image/png", "image/jpeg", "image/webp"}
        for image in images
    ):
        raise BlenderGlbExportError("glb_image_not_embedded")
    names = [node.get("name") for node in nodes if isinstance(node, dict)]
    if not names or not any(
        name.startswith("PackLabComponent_") for name in names if isinstance(name, str)
    ):
        raise BlenderGlbExportError("glb_semantic_component_name_missing")
    return {
        "node_names": names,
        "material_count": len(materials),
        "texture_count": len(textures),
        "image_count": len(images),
        "all_images_embedded": True,
        "external_uri_count": 0,
    }


def _safe_relative(value: str) -> PurePosixPath:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 512
        or "\\" in value
        or value.startswith("/")
    ):
        raise BlenderGlbExportError("glb_export_relative_path_invalid")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in ("", ".", "..") or not _SAFE_SEGMENT.fullmatch(part) for part in path.parts)
    ):
        raise BlenderGlbExportError("glb_export_relative_path_invalid")
    return path


def _contains_uri(value: object) -> bool:
    if isinstance(value, dict):
        return any(key == "uri" or _contains_uri(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_uri(item) for item in value)
    return False


def _export_stage(payload_literal: str) -> bytes:
    source = f"""import bpy, hashlib, json, struct, sys
from pathlib import Path, PurePosixPath

_job=json.loads({payload_literal})
_tail=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
import argparse
_parser=argparse.ArgumentParser(add_help=False)
_parser.add_argument('--project-root',required=True)
_parser.add_argument('--manifest',required=True)
_parser.add_argument('--result',required=True)
_args=_parser.parse_args(_tail)
_root=Path(_args.project_root).resolve(strict=True)
def _relative(value):
 if not isinstance(value,str) or not value or '\\\\' in value or value.startswith('/'):
  raise ValueError('glb_export_relative_path_invalid')
 _path=PurePosixPath(value)
 if _path.is_absolute() or value != _path.as_posix() or any(part in ('','.','..') for part in _path.parts):
  raise ValueError('glb_export_relative_path_invalid')
 return _path
def _inside(value,create_parent=False):
 _path=_root.joinpath(*_relative(value).parts)
 if create_parent: _path.parent.mkdir(parents=True,exist_ok=True)
 _resolved=_path.resolve()
 if not _resolved.is_relative_to(_root): raise ValueError('glb_export_path_outside_project')
 return _resolved
_scene_result=json.loads(_inside(_args.result).read_text('utf-8'))
if _scene_result.get('scene_package_sha256') != _job['scene_package_sha256']: raise ValueError('glb_export_package_digest_mismatch')
_base_name=_scene_result['base_object']['name']
_base=bpy.data.objects.get(_base_name)
if _base is None or _base.type != 'MESH': raise ValueError('glb_export_component_object_missing')
_component_id=_scene_result['geometry_binding']['component_id']
_base.name='PackLabComponent_'+_component_id
_base.data.name='PackLabMesh_'+_component_id
_expected_name=_base.name
_output=_inside(_job['output_relative_path'],True)
if _output.exists(): raise ValueError('glb_export_output_already_exists')
_export_result=bpy.ops.export_scene.gltf(filepath=str(_output),export_format='GLB',use_selection=False,use_visible=False,use_renderable=False,export_cameras=False,export_lights=False,export_materials='EXPORT',export_image_format='AUTO',export_keep_originals=False,export_texcoords=True,export_normals=True,export_apply=True,export_yup=True,export_animations=False,export_skins=False,export_draco_mesh_compression_enable=False)
if 'FINISHED' not in _export_result: raise ValueError('glb_export_operator_failed')
_raw=_output.read_bytes()
if len(_raw)<20 or _raw[:4] != b'glTF': raise ValueError('glb_export_output_invalid')
_version,_length=struct.unpack_from('<II',_raw,4)
_json_length,_chunk_type=struct.unpack_from('<II',_raw,12)
if _version!=2 or _length!=len(_raw) or _chunk_type!=0x4E4F534A or 20+_json_length>len(_raw): raise ValueError('glb_export_container_invalid')
_document=json.loads(_raw[20:20+_json_length].decode('utf-8').rstrip(' \\t\\r\\n\\0'))
def _contains_uri(value):
 if isinstance(value,dict): return any(key=='uri' or _contains_uri(item) for key,item in value.items())
 if isinstance(value,list): return any(_contains_uri(item) for item in value)
 return False
if _contains_uri(_document): raise ValueError('glb_external_uri_forbidden')
_images=_document.get('images',[]); _textures=_document.get('textures',[]); _materials=_document.get('materials',[])
if not _images or not _textures or not _materials: raise ValueError('glb_material_texture_missing')
if any(not isinstance(item,dict) or not isinstance(item.get('bufferView'),int) for item in _images): raise ValueError('glb_image_not_embedded')
_names=[item.get('name') for item in _document.get('nodes',[]) if isinstance(item,dict)]
if _expected_name not in _names or not all('PackLabLabelOverlay_' in name for name in _names if isinstance(name,str) and name.startswith('PackLabLabelOverlay_')): raise ValueError('glb_semantic_names_invalid')
_digest=hashlib.sha256(_raw).hexdigest()
_sidecar={{'contract':{BLENDER_GLB_EXPORT_CONTRACT!r},'scene_package_revision_id':_job['scene_package_revision_id'],'scene_package_sha256':_job['scene_package_sha256'],'source_revisions_and_digests':_job['source'],'component_id':_component_id,'stable_component_name':_expected_name,'source_to_render_transform':_scene_result['source_to_render_transform'],'blender_imported_base_matrix_world':_scene_result['blender_imported_base_matrix_world'],'geometry_material_assignment_revision_id':_scene_result['base_object']['geometry_material_assignment_revision_id'],'material_id':_scene_result['base_object']['material_id'],'pbr_visual_parameter_revision_id':_scene_result['base_object']['pbr_visual_parameter_revision_id'],'artwork_source_bindings':_job['artworks'],'artwork_overlay_bindings':_scene_result['overlays'],'blender':{{'version':list(bpy.app.version),'version_string':bpy.app.version_string,'build_hash':(bpy.app.build_hash.decode('utf-8','replace') if isinstance(bpy.app.build_hash,bytes) else str(bpy.app.build_hash)),'build_branch':(bpy.app.build_branch.decode('utf-8','replace') if isinstance(bpy.app.build_branch,bytes) else str(bpy.app.build_branch)),'build_date':(bpy.app.build_date.decode('utf-8','replace') if isinstance(bpy.app.build_date,bytes) else str(bpy.app.build_date))}},'export_settings':{{'format':'GLB','materials':'EXPORT','images':'embedded','camera':False,'lights':False,'y_up':True,'animations':False,'skins':False,'draco':False}},'output':{{'relative_path':_job['output_relative_path'],'media_type':'model/gltf-binary','sha256':_digest,'byte_length':len(_raw),'node_names':_names,'material_count':len(_materials),'texture_count':len(_textures),'image_count':len(_images),'all_images_embedded':True,'external_uri_count':0}},'authority_limits':{{'derived_presentation_only':True,'physical_accuracy_inferred':False,'physical_fit_verified':False,'material_certified':False,'manufacturing_approval_inferred':False,'regulatory_approval_inferred':False}},'network_access':'NONE','automatic_downloads':False}}
_sidecar_path=_inside(_job['sidecar_relative_path'],True)
_sidecar_path.write_bytes(json.dumps(_sidecar,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')+b'\\n')
print('PACKLAB_BLENDER_GLB_EXPORT_VALID '+_digest)
"""
    return source.encode("utf-8")


__all__ = [
    "BLENDER_GLB_EXPORT_CONTRACT",
    "BlenderGlbExportError",
    "BlenderGlbExportRequest",
    "build_blender_glb_export_runner",
    "run_blender_glb_export",
    "validate_glb_bytes",
]
