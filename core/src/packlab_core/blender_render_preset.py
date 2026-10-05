"""Deterministic presentation-only studio camera and lighting presets."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Literal, cast

RENDER_PRESET_CONTRACT = "packlab.blender-render-preset.v1"
RENDER_PRESET_SCHEMA_VERSION = 1
_VIEWS = ("FRONT", "THREE_QUARTER", "BACK")
_REVISION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_.-]{0,255}$")
_MAX_ABS_COORDINATE = 1_000_000.0


class BlenderRenderPresetError(ValueError):
    """Raised when a render preset is invalid or outside bounded presentation scope."""


@dataclass(frozen=True, slots=True)
class BlenderRenderPreset:
    revision_id: str
    contract: str
    schema_version: int
    view: str
    source_revisions: tuple[tuple[str, str], ...]
    bounds_min: tuple[float, float, float]
    bounds_max: tuple[float, float, float]
    camera_location: tuple[float, float, float]
    camera_target: tuple[float, float, float]
    camera_lens_mm: float
    camera_sensor_width_mm: float
    camera_margin_factor: float
    orthographic: bool
    lights: tuple[dict[str, object], ...]
    transparent_background: bool
    background_rgba: tuple[float, float, float, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "schema_version": self.schema_version,
            "revision_id": self.revision_id,
            "view": self.view,
            "source_revisions": {key: value for key, value in self.source_revisions},
            "bounds_min": list(self.bounds_min),
            "bounds_max": list(self.bounds_max),
            "camera": {
                "location": list(self.camera_location),
                "target": list(self.camera_target),
                "lens_mm": self.camera_lens_mm,
                "sensor_width_mm": self.camera_sensor_width_mm,
                "margin_factor": self.camera_margin_factor,
                "orthographic": self.orthographic,
                "resolution_px": [1024, 1024],
            },
            "lights": list(self.lights),
            "background": {
                "transparent": self.transparent_background,
                "rgba": list(self.background_rgba),
            },
            "authority": "DERIVED_PRESENTATION_ONLY",
            "physical_measurement_inference": False,
        }


def create_blender_render_preset(
    bounds_min: tuple[float, float, float],
    bounds_max: tuple[float, float, float],
    view: Literal["FRONT", "THREE_QUARTER", "BACK"],
    source_revisions: tuple[tuple[str, str], ...],
    *,
    transparent_background: bool = True,
    background_rgba: tuple[float, float, float, float] = (0.08, 0.08, 0.08, 1.0),
) -> BlenderRenderPreset:
    """Create a canonical named studio preset framed from exact scene bounds."""
    low = cast(tuple[float, float, float], _vector(bounds_min, "bounds_min"))
    high = cast(tuple[float, float, float], _vector(bounds_max, "bounds_max"))
    if any(a >= b for a, b in zip(low, high, strict=True)):
        raise BlenderRenderPresetError("render_bounds_extent_invalid")
    if view not in _VIEWS:
        raise BlenderRenderPresetError("render_view_unsupported")
    if not isinstance(source_revisions, tuple) or not source_revisions:
        raise BlenderRenderPresetError("render_source_revisions_invalid")
    normalized_sources: list[tuple[str, str]] = []
    for item in source_revisions:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not all(isinstance(part, str) and _REVISION_ID.fullmatch(part) for part in item)
        ):
            raise BlenderRenderPresetError("render_source_revision_invalid")
        normalized_sources.append(item)
    if len({key for key, _ in normalized_sources}) != len(normalized_sources):
        raise BlenderRenderPresetError("render_source_revision_key_duplicate")
    normalized_sources.sort()
    if not isinstance(transparent_background, bool):
        raise BlenderRenderPresetError("render_transparency_invalid")
    rgba = cast(
        tuple[float, float, float, float], _vector(background_rgba, "background_rgba", size=4)
    )
    if any(not 0.0 <= channel <= 1.0 for channel in rgba):
        raise BlenderRenderPresetError("render_background_channel_out_of_range")

    center = cast(
        tuple[float, float, float],
        tuple((a + b) / 2.0 for a, b in zip(low, high, strict=True)),
    )
    dimensions = tuple(b - a for a, b in zip(low, high, strict=True))
    radius = math.sqrt(sum((dimension / 2.0) ** 2 for dimension in dimensions))
    margin = 1.2
    lens = 50.0
    sensor = 36.0
    fov = 2.0 * math.atan(sensor / (2.0 * lens))
    distance = radius / math.sin(fov / 2.0) * margin
    directions = {
        "FRONT": (0.0, -1.0, 0.0),
        "THREE_QUARTER": (1.0, -1.0, 0.35),
        "BACK": (0.0, 1.0, 0.0),
    }
    direction = directions[view]
    direction_length = math.sqrt(sum(value * value for value in direction))
    direction = cast(
        tuple[float, float, float], tuple(value / direction_length for value in direction)
    )
    camera_location = cast(
        tuple[float, float, float],
        tuple(c + d * distance for c, d in zip(center, direction, strict=True)),
    )
    light_specs = (
        ("KEY", (-1.8, -2.0, 2.2), 1200.0, max(dimensions) * 1.4),
        ("FILL", (2.0, -1.0, 0.8), 650.0, max(dimensions) * 1.2),
        ("RIM", (0.4, 2.0, 1.8), 950.0, max(dimensions) * 1.0),
    )
    lights = tuple(
        {
            "name": name,
            "location": [center[i] + relative[i] * max(dimensions) for i in range(3)],
            "energy_watts": energy,
            "size": size,
            "color": [1.0, 1.0, 1.0],
            "target": list(center),
        }
        for name, relative, energy, size in light_specs
    )
    identity = {
        "contract": RENDER_PRESET_CONTRACT,
        "schema_version": RENDER_PRESET_SCHEMA_VERSION,
        "view": view,
        "source_revisions": dict(normalized_sources),
        "bounds_min": low,
        "bounds_max": high,
        "camera_location": camera_location,
        "camera_target": center,
        "camera_lens_mm": 50.0,
        "camera_sensor_width_mm": 36.0,
        "camera_margin_factor": margin,
        "orthographic": False,
        "lights": lights,
        "transparent_background": transparent_background,
        "background_rgba": rgba,
    }
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False)
    revision_id = "blender-render-preset:" + hashlib.sha256(canonical.encode()).hexdigest()
    return BlenderRenderPreset(
        revision_id=revision_id,
        contract=RENDER_PRESET_CONTRACT,
        schema_version=RENDER_PRESET_SCHEMA_VERSION,
        view=view,
        source_revisions=tuple(normalized_sources),
        bounds_min=low,
        bounds_max=high,
        camera_location=camera_location,
        camera_target=center,
        camera_lens_mm=lens,
        camera_sensor_width_mm=sensor,
        camera_margin_factor=margin,
        orthographic=False,
        lights=lights,
        transparent_background=transparent_background,
        background_rgba=rgba,
    )


def build_blender_render_preset_runner(preset: BlenderRenderPreset) -> bytes:
    """Return the fixed data-only Blender script for applying one validated preset."""
    if not isinstance(preset, BlenderRenderPreset):
        raise BlenderRenderPresetError("render_preset_invalid")
    payload = json.dumps(preset.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)
    payload_literal = repr(payload)
    return (
        "import bpy, json\n"
        "from mathutils import Vector\n"
        f"preset=json.loads({payload_literal})\n"
        "scene=bpy.context.scene\n"
        "for existing in list(bpy.data.objects): bpy.data.objects.remove(existing,do_unlink=True)\n"
        "scene.render.resolution_x=1024\n"
        "scene.render.resolution_y=1024\n"
        "scene.render.resolution_percentage=100\n"
        "scene.render.film_transparent=preset['background']['transparent']\n"
        "scene.world.color=tuple(preset['background']['rgba'][:3])\n"
        "scene.world.use_nodes=True\n"
        "scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=preset['background']['rgba']\n"
        "camera_data=bpy.data.cameras.new('PackLab Studio Camera')\n"
        "camera_data.lens=preset['camera']['lens_mm']\n"
        "camera_data.sensor_width=preset['camera']['sensor_width_mm']\n"
        "camera=bpy.data.objects.new('PackLab Studio Camera',camera_data)\n"
        "scene.collection.objects.link(camera)\n"
        "camera.location=preset['camera']['location']\n"
        "direction=Vector(preset['camera']['target'])-camera.location\n"
        "camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()\n"
        "scene.camera=camera\n"
        "for spec in preset['lights']:\n"
        " data=bpy.data.lights.new(spec['name'],'AREA')\n"
        " data.energy=spec['energy_watts']\n"
        " data.shape='DISK'\n"
        " data.size=spec['size']\n"
        " data.color=spec['color']\n"
        " obj=bpy.data.objects.new('PackLab Studio '+spec['name'],data)\n"
        " scene.collection.objects.link(obj)\n"
        " obj.location=spec['location']\n"
        " obj.rotation_euler=(Vector(spec['target'])-obj.location).to_track_quat('-Z','Y').to_euler()\n"
        "facts={'contract':preset['contract'],'preset_revision_id':preset['revision_id'],"
        "'view':preset['view'],'camera_object':camera.name,'camera_location':list(camera.location),"
        "'camera_target':preset['camera']['target'],'light_objects':sorted(obj.name for obj in scene.objects if obj.type=='LIGHT'),"
        "'light_count':len([obj for obj in scene.objects if obj.type=='LIGHT']),"
        "'transparent_background':scene.render.film_transparent,"
        "'resolution_px':[scene.render.resolution_x,scene.render.resolution_y],"
        "'source_revisions':preset['source_revisions'],"
        "'authority':preset['authority'],'physical_measurement_inference':False}\n"
        "print('PACKLAB_RENDER_PRESET_RESULT:'+json.dumps(facts,sort_keys=True,separators=(',',':')))\n"
    ).encode()


def _vector(values: tuple[float, ...], field: str, *, size: int = 3) -> tuple[float, ...]:
    if not isinstance(values, tuple) or len(values) != size:
        raise BlenderRenderPresetError(f"render_{field}_invalid")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or abs(value) > _MAX_ABS_COORDINATE
        for value in values
    ):
        raise BlenderRenderPresetError(f"render_{field}_out_of_range")
    return tuple(float(value) for value in values)
