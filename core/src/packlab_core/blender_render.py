"""Offline deterministic-setting still rendering from validated scene packages."""

from __future__ import annotations

import json
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from . import blender_scene_package as scene_package_module
from .blender_render_preset import BlenderRenderPreset
from .blender_scene_package import BlenderScenePackage

BLENDER_RENDER_CONTRACT = "packlab.blender-render-job.v1"
BLENDER_RENDER_EVIDENCE_CONTRACT = "packlab.blender-render-evidence.v1"
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_MIN_DIMENSION = 64
_MAX_DIMENSION = 4096
_MAX_RENDER_TIMEOUT_SECONDS = 600.0


class BlenderRenderError(ValueError):
    """Raised when render inputs, invocation, or semantic output validation fails."""


@dataclass(frozen=True, slots=True)
class BlenderRenderRequest:
    width: int = 512
    height: int = 512
    samples: int = 16
    timeout_seconds: float = 180.0
    output_relative_path: str = "renders/product.png"
    evidence_relative_path: str = "renders/render_result_manifest.json"

    def __post_init__(self) -> None:
        for name, value, minimum, maximum in (
            ("width", self.width, _MIN_DIMENSION, _MAX_DIMENSION),
            ("height", self.height, _MIN_DIMENSION, _MAX_DIMENSION),
            ("samples", self.samples, 1, 128),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not minimum <= value <= maximum
            ):
                raise BlenderRenderError(f"render_{name}_invalid")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(self.timeout_seconds)
            or not 1.0 <= self.timeout_seconds <= _MAX_RENDER_TIMEOUT_SECONDS
        ):
            raise BlenderRenderError("render_timeout_invalid")
        _safe_relative(self.output_relative_path)
        _safe_relative(self.evidence_relative_path)
        if self.output_relative_path == self.evidence_relative_path:
            raise BlenderRenderError("render_output_paths_must_differ")


def build_blender_render_runner(
    package: BlenderScenePackage,
    preset: BlenderRenderPreset,
    request: BlenderRenderRequest | None = None,
) -> bytes:
    """Compose only PackLab's fixed scene validator and fixed render stage."""
    if request is None:
        request = BlenderRenderRequest()
    if (
        not isinstance(package, BlenderScenePackage)
        or package.runner_script != scene_package_module.BLENDER_SCENE_RUNNER.encode("utf-8")
        or not isinstance(preset, BlenderRenderPreset)
        or not isinstance(request, BlenderRenderRequest)
    ):
        raise BlenderRenderError("render_package_runner_untrusted")
    body = package.manifest().get("body")
    if not isinstance(body, dict) or body.get("contract") != "packlab.blender-scene-package.v2":
        raise BlenderRenderError("render_scene_package_invalid")
    settings = {
        "contract": BLENDER_RENDER_CONTRACT,
        "scene_package_revision_id": package.revision_id,
        "scene_package_sha256": package.manifest()["content_sha256"],
        "preset": preset.as_dict(),
        "settings": {
            "engine": "BLENDER_EEVEE",
            "width": request.width,
            "height": request.height,
            "samples": request.samples,
            "image_format": "PNG",
            "color_mode": "RGBA",
            "color_depth": "8",
            "transparent_background": True,
            "output_relative_path": request.output_relative_path,
            "evidence_relative_path": request.evidence_relative_path,
        },
    }
    payload = json.dumps(settings, sort_keys=True, separators=(",", ":"), allow_nan=False)
    stage = _render_stage(payload)
    return package.runner_script.rstrip() + b"\n\n" + stage


def run_blender_render(
    executable: str | Path,
    runner_script: str | Path,
    project_root: str | Path,
    *,
    manifest_relative_path: str = "blender_scene_manifest.json",
    scene_result_relative_path: str = "scene_result_manifest.json",
    timeout_seconds: float = 180.0,
    runner=subprocess.run,
) -> subprocess.CompletedProcess[str]:
    """Run the static render script offline and report generic, path-free failures."""
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or not 1.0 <= timeout_seconds <= _MAX_RENDER_TIMEOUT_SECONDS
    ):
        raise BlenderRenderError("render_timeout_invalid")
    for path in (manifest_relative_path, scene_result_relative_path):
        _safe_relative(path)
    root = Path(project_root)
    if not root.is_dir() or not Path(executable).is_file() or not Path(runner_script).is_file():
        raise BlenderRenderError("render_input_path_unavailable")
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
        raise BlenderRenderError("blender_render_timed_out") from error
    except OSError as error:
        raise BlenderRenderError("blender_render_launch_failed") from error
    if completed.returncode != 0:
        raise BlenderRenderError("blender_render_process_failed")
    if "PACKLAB_BLENDER_RENDER_VALID " not in completed.stdout:
        raise BlenderRenderError("blender_render_semantic_validation_failed")
    return completed


def _safe_relative(value: str) -> PurePosixPath:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 512
        or "\\" in value
        or value.startswith("/")
    ):
        raise BlenderRenderError("render_relative_path_invalid")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in ("", ".", "..") or not _SAFE_SEGMENT.fullmatch(part) for part in path.parts)
    ):
        raise BlenderRenderError("render_relative_path_invalid")
    return path


def _render_stage(payload: str) -> bytes:
    encoded = repr(payload)
    source = f"""import bpy, hashlib, json, math, struct, sys
from pathlib import Path, PurePosixPath
from mathutils import Vector

_job=json.loads({encoded})
_preset=_job['preset']
_settings=_job['settings']
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
  raise ValueError('render_relative_path_invalid')
 _path=PurePosixPath(value)
 if _path.is_absolute() or value != _path.as_posix() or any(part in ('','.','..') for part in _path.parts):
  raise ValueError('render_relative_path_invalid')
 return _path
def _inside(value,create_parent=False):
 _path=_root.joinpath(*_relative(value).parts)
 if create_parent: _path.parent.mkdir(parents=True,exist_ok=True)
 _resolved=_path.resolve()
 if not _resolved.is_relative_to(_root): raise ValueError('render_path_outside_project')
 return _resolved
_package_result=json.loads(_inside(_args.result).read_text('utf-8'))
if _package_result.get('scene_package_sha256') != _job['scene_package_sha256']: raise ValueError('render_scene_package_digest_mismatch')
_package_result['scene_package_revision_id']=_job['scene_package_revision_id']
_scene=bpy.context.scene
_scene.render.engine=_settings['engine']
_scene.eevee.taa_render_samples=_settings['samples']
_scene.render.resolution_x=_settings['width']
_scene.render.resolution_y=_settings['height']
_scene.render.resolution_percentage=100
_scene.render.image_settings.file_format='PNG'
_scene.render.image_settings.color_mode='RGBA'
_scene.render.image_settings.color_depth='8'
_scene.render.image_settings.compression=15
_scene.render.film_transparent=True
_scene.render.use_file_extension=True
_scene.render.filepath=str(_inside(_settings['output_relative_path'],True))
_scene.world.use_nodes=True
_scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=_preset['background']['rgba']
_camera_data=bpy.data.cameras.new('PackLab Studio Camera')
_camera_data.lens=_preset['camera']['lens_mm']
_camera_data.sensor_width=_preset['camera']['sensor_width_mm']
_camera_data.sensor_fit='HORIZONTAL'
_camera=bpy.data.objects.new('PackLab Studio Camera',_camera_data)
_scene.collection.objects.link(_camera)
_camera.location=_preset['camera']['location']
_camera.rotation_euler=(Vector(_preset['camera']['target'])-_camera.location).to_track_quat('-Z','Y').to_euler()
_scene.camera=_camera
for _spec in _preset['lights']:
 _data=bpy.data.lights.new('PackLab Studio '+_spec['name'],'AREA')
 _data.energy=_spec['energy_watts']; _data.shape='DISK'; _data.size=_spec['size']; _data.color=_spec['color']
 _object=bpy.data.objects.new('PackLab Studio '+_spec['name'],_data)
 _scene.collection.objects.link(_object); _object.location=_spec['location']
 _object.rotation_euler=(Vector(_spec['target'])-_object.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
_mesh_objects=[_obj for _obj in _scene.objects if _obj.type=='MESH' and _obj.get('packlab_presentation_only') is not True]
if not _mesh_objects: raise ValueError('render_scene_mesh_missing')
_bounds=[]
for _obj in _mesh_objects:
 for _corner in _obj.bound_box: _bounds.append(_obj.matrix_world @ Vector(_corner))
_bounds_min=[min(_point[_axis] for _point in _bounds) for _axis in range(3)]
_bounds_max=[max(_point[_axis] for _point in _bounds) for _axis in range(3)]
_center=Vector([(a+b)/2.0 for a,b in zip(_bounds_min,_bounds_max)])
_radius=max((_point-_center).length for _point in _bounds)
_preset_target=Vector(_preset['camera']['target'])
_view_direction=(Vector(_preset['camera']['location'])-_preset_target).normalized()
_fov=2.0*math.atan(_camera_data.sensor_width/(2.0*_camera_data.lens))
_distance=_radius/math.sin(_fov/2.0)*_preset['camera']['margin_factor']
_camera.location=_center+_view_direction*_distance
_camera.rotation_euler=(_center-_camera.location).to_track_quat('-Z','Y').to_euler()
_preset_span=max(_preset['bounds_max'][_axis]-_preset['bounds_min'][_axis] for _axis in range(3))
_scene_span=max(_bounds_max[_axis]-_bounds_min[_axis] for _axis in range(3))
for _spec in _preset['lights']:
 _object=bpy.data.objects['PackLab Studio '+_spec['name']]
 _light_relative=[(_spec['location'][_axis]-_preset_target[_axis])/_preset_span for _axis in range(3)]
 _object.location=_center+Vector(_light_relative)*_scene_span
 _object.data.size=_spec['size']/_preset_span*_scene_span
 _object.rotation_euler=(_center-_object.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
_framed=_distance*math.sin(_fov/2.0) >= _radius*_preset['camera']['margin_factor']*0.99
if not _framed: raise ValueError('render_scene_object_clipped')
_source_digest={{_key:_value for _key,_value in _package_result['source'].items() if _key.endswith('_sha256') or _key.endswith('_revision_id')}}
_scene.render.image_settings.color_management='FOLLOW_SCENE'
_scene.view_settings.view_transform='Standard'
_scene.render.filepath=str(_inside(_settings['output_relative_path'],True))
bpy.ops.render.render(write_still=True)
_output=_inside(_settings['output_relative_path'])
if not _output.is_file() or _output.stat().st_size < 64: raise ValueError('render_output_missing_or_empty')
_raw=_output.read_bytes()
if _raw[:8] != b'\\x89PNG\\r\\n\\x1a\\n' or _raw[12:16] != b'IHDR': raise ValueError('render_png_invalid')
_width,_height=struct.unpack('>II',_raw[16:24]); _color_type=_raw[25]
if (_width,_height) != (_settings['width'],_settings['height']) or _color_type != 6: raise ValueError('render_png_dimensions_or_alpha_invalid')
_image=bpy.data.images.load(str(_output),check_existing=False)
_alphas=[float(_image.pixels[_index]) for _index in range(3,len(_image.pixels),4)]
_transparent=sum(1 for _alpha in _alphas if _alpha < 0.99)
_visible=sum(1 for _alpha in _alphas if _alpha > 0.01)
if _transparent <= 0 or _visible <= 0: raise ValueError('render_alpha_semantics_invalid')
_evidence={{
 'contract':{BLENDER_RENDER_EVIDENCE_CONTRACT!r},
 'render_job_contract':_job['contract'],
 'scene_package_contract':_package_result['scene_package_contract'],
 'scene_package_revision_id':_package_result['scene_package_revision_id'],
 'scene_package_sha256':_package_result['scene_package_sha256'],
 'source_revisions_and_digests':_source_digest,
 'render_preset_revision_id':_preset['revision_id'],
 'blender':{{'version':list(bpy.app.version),'version_string':bpy.app.version_string,'build_hash':(bpy.app.build_hash.decode('utf-8','replace') if isinstance(bpy.app.build_hash,bytes) else str(bpy.app.build_hash)),'build_branch':(bpy.app.build_branch.decode('utf-8','replace') if isinstance(bpy.app.build_branch,bytes) else str(bpy.app.build_branch)),'build_date':(bpy.app.build_date.decode('utf-8','replace') if isinstance(bpy.app.build_date,bytes) else str(bpy.app.build_date))}},
 'settings':{{'engine':_scene.render.engine,'width':_settings['width'],'height':_settings['height'],'samples':_settings['samples'],'image_format':'PNG','color_mode':'RGBA','color_depth':'8','transparent_background':_scene.render.film_transparent,'resolution_percentage':_scene.render.resolution_percentage,'view_transform':_scene.view_settings.view_transform,'camera_view':_preset['view'],'camera_location':list(_camera.location),'camera_target':list(_center),'camera_lens_mm':_camera_data.lens,'light_facts':_preset['lights']}},
 'scene_mesh_bounds':{{'minimum':_bounds_min,'maximum':_bounds_max,'unit':'meters_from_mm_unverified_viewer_transform'}},
 'output':{{'media_type':'image/png','sha256':hashlib.sha256(_raw).hexdigest(),'byte_length':len(_raw),'width':_width,'height':_height,'png_color_type':_color_type,'alpha_channel':True,'transparent_pixel_count':_transparent,'visible_pixel_count':_visible,'all_mesh_bounds_inside_camera':_framed}},
 'authority_limits':{{'derived_presentation_only':True,'design_model_mutated':False,'cad_brep_mutated':False,'physical_accuracy_inferred':False,'physical_fit_verified':False,'material_certified':False,'manufacturing_approval_inferred':False,'regulatory_approval_inferred':False}},
 'determinism_claim':'REPRODUCIBLE_SETTINGS_AND_PROVENANCE_ONLY',
 'network_access':'NONE','automatic_downloads':False
}}
_evidence_path=_inside(_settings['evidence_relative_path'],True)
_evidence_bytes=json.dumps(_evidence,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')+b'\\n'
_evidence_path.write_bytes(_evidence_bytes)
print('PACKLAB_BLENDER_RENDER_VALID '+_evidence['output']['sha256'])
"""
    return source.encode("utf-8")


__all__ = [
    "BLENDER_RENDER_CONTRACT",
    "BLENDER_RENDER_EVIDENCE_CONTRACT",
    "BlenderRenderError",
    "BlenderRenderRequest",
    "build_blender_render_runner",
    "run_blender_render",
]
