"""Generate deterministic, explicitly synthetic packaging benchmark renders.

Run with Blender 5.x:
  blender --background --factory-startup --python tools/datasets/generate_packaging_benchmark.py -- --out <outside-git-dir>

This is software-test data. Nominal dimensions, tolerances, optical behavior and
camera calibration are generated assumptions, never physical measurements.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PACKLAB_CORE_SOURCE = Path(__file__).resolve().parents[2] / "core" / "src"
if str(PACKLAB_CORE_SOURCE) not in sys.path:
    sys.path.insert(0, str(PACKLAB_CORE_SOURCE))
DATASET_TOOLS_SOURCE = Path(__file__).resolve().parent
if str(DATASET_TOOLS_SOURCE) not in sys.path:
    sys.path.insert(0, str(DATASET_TOOLS_SOURCE))
from dataset_root import resolve_dataset_root
from packlab_core.benchmark_metrics import synthetic_packaging_metric_bands


GENERATOR_VERSION = "2.0.0"
SEED = 3692026
WIDTH, HEIGHT = 640, 480
MATERIALS = {
    "hdpe_matte": {"polymer": "HDPE", "roughness": 0.76, "metallic": 0.0, "transmission": 0.0, "base": (0.82, 0.86, 0.83, 1.0)},
    "pet_gloss": {"polymer": "PET", "roughness": 0.12, "metallic": 0.0, "transmission": 0.0, "base": (0.13, 0.38, 0.63, 1.0)},
    "pet_clear": {"polymer": "PET", "roughness": 0.025, "metallic": 0.0, "transmission": 0.08, "base": (0.38, 0.68, 0.77, 0.48)},
    "pp_translucent": {"polymer": "PP", "roughness": 0.27, "metallic": 0.0, "transmission": 0.20, "base": (0.91, 0.78, 0.43, 0.68)},
}

# Dimensions in mm; these are controlled synthetic nominal values. Tol. is a
# generated test band, not an industry specification or measured process limit.
FAMILIES = {
    "bottle": {"size": (72, 72, 228), "profile": [(0, .47), (.04, .50), (.10, .48), (.58, .48), (.66, .43), (.73, .29), (.83, .25), (.91, .25), (.93, .17), (1, .17)], "tol": (0.35, 0.55)},
    "jerrycan": {"size": (168, 92, 286), "box": True, "tol": (0.7, 1.0)},
    "jar": {"size": (104, 104, 142), "profile": [(0, .46), (.05, .50), (.10, .50), (.78, .50), (.84, .48), (.88, .39), (.92, .39), (1, .39)], "tol": (0.4, 0.6)},
    "closure": {"size": (42, 42, 28), "profile": [(0, .45), (.08, .50), (.88, .50), (.96, .45), (1, .44)], "tol": (0.15, 0.25)},
    "trigger_spray": {"size": (92, 78, 244), "profile": [(0, .48), (.05, .50), (.12, .48), (.58, .48), (.66, .43), (.74, .27), (.88, .24), (.96, .21), (1, .20)], "tol": (0.45, 0.7)},
    "pump": {"size": (82, 82, 218), "profile": [(0, .48), (.06, .50), (.58, .50), (.68, .34), (.76, .25), (.90, .24), (.94, .18), (1, .18)], "tol": (0.4, 0.65)},
    "tube": {"size": (58, 42, 184), "profile": [(0, .50), (.06, .50), (.10, .45), (.30, .36), (.60, .25), (.86, .18), (.93, .18), (1, .18)], "tol": (0.35, 0.55)},
    "sachet": {"size": (125, 18.36, 190), "box": True, "tol": (0.45, 0.75)},
}


def _material(name: str, spec: dict) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = spec["base"]
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = spec["base"]
    bsdf.inputs["Roughness"].default_value = spec["roughness"]
    bsdf.inputs["Metallic"].default_value = spec["metallic"]
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = spec["transmission"]
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = spec["transmission"]
    if spec["base"][3] < 1:
        material.surface_render_method = "BLENDED"
        bsdf.inputs["Alpha"].default_value = spec["base"][3]
    bsdf.inputs["Coat Weight"].default_value = 0.2 if spec["roughness"] < 0.2 else 0.03
    return material


def _lathe(name: str, profile: list, radius_x: float, radius_y: float, height: float, material: bpy.types.Material) -> bpy.types.Object:
    sides = 64
    verts = []
    faces = []
    for zf, rf in profile:
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            verts.append((radius_x * rf * math.cos(angle), radius_y * rf * math.sin(angle), height * zf))
    for ring in range(len(profile) - 1):
        for i in range(sides):
            a = ring * sides + i
            b = ring * sides + (i + 1) % sides
            c = b + sides
            d = a + sides
            faces.append((a, b, c, d))
    faces.extend([tuple(reversed(range(sides))), tuple((len(profile) - 1) * sides + i for i in range(sides))])
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = len(poly.vertices) == 4
    return obj


def _rounded_box(name: str, dims_m: tuple, material: bpy.types.Material, location=(0, 0, 0)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims_m
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new("molded_edge_radius", "BEVEL")
    bevel.width = min(dims_m) * 0.055
    bevel.segments = 4
    obj.modifiers.new("weighted_corner_normals", "WEIGHTED_NORMAL")
    obj.data.materials.append(material)
    return obj


def _rod(name: str, start: Vector, end: Vector, radius: float, material: bpy.types.Material) -> bpy.types.Object:
    delta = end - start
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=delta.length, location=(start + end) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("soft_edges", "BEVEL")
    bevel.width = min(radius * 0.25, delta.length * 0.02)
    bevel.segments = 2
    return obj


def _build_family(family: str, material: bpy.types.Material) -> None:
    sx, sy, sz = (v / 1000 for v in FAMILIES[family]["size"])
    if family in {"jerrycan", "sachet"}:
        body_dims = (sx, sy, sz * (0.78 if family == "jerrycan" else 0.90))
        body = _rounded_box(f"{family}_body", body_dims, material, (0, 0, sz * (0.39 if family == "jerrycan" else 0.45)))
        if family == "jerrycan":
            # Raised molded handle loop and neck/cap; intentionally visible as
            # geometry while not claiming an injection-mold CAD surface.
            x, y, z = sx * 0.31, -sy * 0.12, sz * 0.80
            for a, b in [((-x, y, z), (-x, y, z + sz * .14)), ((-x, y, z + sz * .14), (x, y, z + sz * .14)), ((x, y, z + sz * .14), (x, y, z))]:
                _rod("jerrycan_handle_bridge", Vector(a), Vector(b), sy * .045, material)
            _lathe("jerrycan_neck", [(0, .42), (.2, .5), (1, .5)], sx * .2, sx * .2, sz * .14, material).location.z = sz * .80
            _lathe("jerrycan_cap", [(0, .45), (.1, .5), (.9, .5), (1, .45)], sx * .24, sx * .24, sz * .055, _material("PP_cap", MATERIALS["pp_translucent"])).location.z = sz * .945
        else:
            # Heat-seal bands and a ribbed fitment are represented as geometry.
            for z in (sz * .0175, sz * .87, sz * .95):
                _rounded_box("sachet_seal", (sx, sy, sz * .035), material, (0, 0, z))
            _lathe("sachet_spout", [(0, .5), (1, .5)], sx * .12, sx * .12, sz * .10, _material("PP_fitment", MATERIALS["pp_translucent"])).location.z = sz * .90
        return

    obj = _lathe(f"{family}_body", FAMILIES[family]["profile"], sx, sy, sz, material)
    if family == "trigger_spray":
        _rounded_box("trigger_sprayer_head", (sx * .62, sy * .42, sz * .10), _material("PP_sprayer", MATERIALS["pp_translucent"]), (sx * .18, 0, sz * .95))
        _rod("trigger_nozzle", Vector((sx * .32, 0, sz * .97)), Vector((sx * .40, 0, sz * .97)), sy * .045, _material("PP_nozzle", MATERIALS["pp_translucent"]))
        _rod("trigger_lever", Vector((sx * .10, -sy * .12, sz * .92)), Vector((sx * .32, -sy * .12, sz * .81)), sy * .035, _material("PP_lever", MATERIALS["pp_translucent"]))
    elif family == "pump":
        _lathe("pump_collar", [(0, .45), (.1, .5), (.9, .5), (1, .45)], sx * .28, sx * .28, sz * .06, _material("PP_collar", MATERIALS["pp_translucent"])).location.z = sz * .91
        _rounded_box("pump_press_head", (sx * .42, sy * .26, sz * .035), _material("PP_pump", MATERIALS["pp_translucent"]), (sx * .10, 0, sz * .98))
        _rod("pump_stem", Vector((0, 0, sz * .92)), Vector((0, 0, sz * .98)), sx * .045, _material("PP_stem", MATERIALS["pp_translucent"]))
    elif family == "closure":
        # Vertical grip ribs make the low part visibly read as a screw cap.
        for idx in range(24):
            angle = 2 * math.pi * idx / 24
            r = sx * 0.235
            _rod("closure_grip_rib", Vector((r * math.cos(angle), r * math.sin(angle), sz * .1)), Vector((r * math.cos(angle), r * math.sin(angle), sz * .9)), sx * .008, material)


def _clear_scene() -> None:
    scene = bpy.context.scene
    if scene.compositing_node_group is not None:
        scene.compositing_node_group = None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.node_groups):
        for item in list(datablocks):
            if item.users == 0:
                datablocks.remove(item)


def _setup_scene() -> tuple[bpy.types.Camera, bpy.types.Material]:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 48
    scene.render.use_compositing = True
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.world.color = (0.18, 0.18, 0.18)
    camera_data = bpy.data.cameras.new("virtual_camera")
    camera = bpy.data.objects.new("virtual_camera", camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.lens = 50.0
    camera.data.sensor_width = 36.0
    camera.data.sensor_height = 27.0
    camera.data.sensor_fit = "HORIZONTAL"
    camera.data.dof.use_dof = False
    mask = bpy.data.materials.new("synthetic_binary_mask")
    mask.diffuse_color = (1, 1, 1, 1)
    mask.use_nodes = True
    bsdf = mask.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 1.0
    return camera, mask


def _aim(obj: bpy.types.Object, point: Vector) -> None:
    obj.rotation_euler = (point - obj.location).to_track_quat("-Z", "Y").to_euler()


def _lighting(seed: int, scale: float) -> list[dict]:
    rng = random.Random(seed)
    records = []
    for idx, (loc, energy, size) in enumerate([
        ((1.0, -1.2, 1.8), 240, 0.65), ((-1.1, -0.1, 1.4), 120, 0.45), ((0.2, 1.2, 1.0), 180, 0.55)
    ]):
        data = bpy.data.lights.new(f"softbox_{idx}", "AREA")
        data.energy = energy * scale * rng.uniform(0.97, 1.03)
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(f"softbox_{idx}", data)
        bpy.context.collection.objects.link(light)
        light.location = loc
        _aim(light, Vector((0, 0, 0.5)))
        records.append({"position_m": list(loc), "energy_w": data.energy, "area_size_m": size})
    return records


def _world_matrix_camera(camera: bpy.types.Object) -> list[float]:
    return [round(float(camera.matrix_world[r][c]), 9) for r in range(4) for c in range(4)]


def _save_render(scene: bpy.types.Scene, camera: bpy.types.Object, mask_material: bpy.types.Material, ground: bpy.types.Object, out_rgb: Path, out_mask: Path, distortion: float) -> None:
    scene.camera = camera
    tree = bpy.data.node_groups.new("M17 synthetic lens distortion", "CompositorNodeTree")
    scene.compositing_node_group = tree
    scene.render.use_compositing = True
    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    render_layers = tree.nodes.new("CompositorNodeRLayers")
    lens = tree.nodes.new("CompositorNodeLensdist")
    lens.inputs["Distortion"].default_value = distortion
    output = tree.nodes.new("NodeGroupOutput")
    tree.links.new(render_layers.outputs["Image"], lens.inputs["Image"])
    tree.links.new(lens.outputs["Image"], output.inputs["Image"])
    scene.render.filepath = str(out_rgb)
    scene.view_layers[0].material_override = None
    bpy.ops.render.render(write_still=True)

    scene.view_layers[0].material_override = mask_material
    ground.hide_render = True
    scene.render.film_transparent = True
    scene.render.filepath = str(out_mask)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False
    ground.hide_render = False
    scene.view_layers[0].material_override = None


def _mesh_truth(objects: list[bpy.types.Object], output: Path) -> dict:
    """Write a world-space ASCII PLY and return its exact generated bounds."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        base = len(vertices)
        vertices.extend(tuple(float(component) for component in evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices)
        faces.extend(tuple(base + int(index) for index in polygon.vertices) for polygon in mesh.polygons if len(polygon.vertices) >= 3)
        evaluated.to_mesh_clear()
    if not vertices or not faces:
        raise ValueError("generated ground-truth mesh is empty")
    lower = tuple(min(vertex[axis] for vertex in vertices) for axis in range(3))
    upper = tuple(max(vertex[axis] for vertex in vertices) for axis in range(3))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="ascii", newline="\n") as stream:
        stream.write("ply\nformat ascii 1.0\n")
        stream.write(f"comment units meters; generated geometry; not physical CAD\nelement vertex {len(vertices)}\n")
        stream.write("property float x\nproperty float y\nproperty float z\n")
        stream.write(f"element face {len(faces)}\nproperty list uchar int vertex_indices\nend_header\n")
        for vertex in vertices:
            stream.write(f"{vertex[0]:.9g} {vertex[1]:.9g} {vertex[2]:.9g}\n")
        for face in faces:
            stream.write(f"{len(face)} {' '.join(str(index) for index in face)}\n")
    bounds_mm = [round((upper[i] - lower[i]) * 1000.0, 3) for i in range(3)]
    return {"path": output.name, "bytes": output.stat().st_size, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "format": "PLY", "vertices": len(vertices), "faces": len(faces), "units": "meters", "bounds_mm_from_generated_vertices": bounds_mm}


def generate(output: Path, count_per_family: int = 12) -> dict:
    root = resolve_dataset_root(output, Path(os.environ["LOCALAPPDATA"]))
    checkout = Path(__file__).resolve().parents[2]
    try:
        root.relative_to(checkout)
    except ValueError:
        pass
    else:
        raise ValueError("Generated data must be outside the Git checkout")
    final_output = root / "synthetic"
    staging_parent = root / ".staging"
    staging = staging_parent / "synthetic-v1"
    if final_output.exists() or staging_parent.exists():
        raise FileExistsError("refusing to overwrite an existing synthetic dataset or staging directory")
    staging.mkdir(parents=True, exist_ok=False)
    records = []
    for family_index, (family, spec) in enumerate(FAMILIES.items()):
        for variant_index, material_id in enumerate(MATERIALS):
            for view_index in range(3):
                _clear_scene()
                camera, mask_material = _setup_scene()
                scene = bpy.context.scene
                material = _material(f"{family}_{material_id}", MATERIALS[material_id])
                _build_family(family, material)
                # Ground plane uses a neutral matte surface and is deliberately
                # excluded from the segmentation mask via object pass index.
                bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
                ground = bpy.context.object
                ground.name = "ground_non_object"
                ground.data.materials.append(_material("studio_ground", {"polymer": "backdrop", "roughness": .85, "metallic": 0, "transmission": 0, "base": (.30, .32, .34, 1)}))
                ground.pass_index = 0
                sx, sy, sz = (v / 1000 for v in spec["size"])
                target = Vector((0, 0, sz * 0.52))
                azimuth = (0.0, math.radians(34), math.radians(-42))[view_index]
                elevation = (math.radians(5), math.radians(12), math.radians(39))[view_index]
                distance = max(sx, sy, sz) * 3.0
                camera.location = target + Vector((math.sin(azimuth) * math.cos(elevation), -math.cos(azimuth) * math.cos(elevation), math.sin(elevation))) * distance
                _aim(camera, target)
                lights = _lighting(SEED + family_index * 31 + variant_index * 7 + view_index, 0.72 + 0.28 * ((variant_index + view_index) % 3))
                sample_id = f"syn_{family}_{material_id}_v{view_index + 1:02d}"
                rgb_path = staging / "rgb" / f"{sample_id}.png"
                mask_path = staging / "masks" / f"{sample_id}.png"
                mesh_path = staging / "ground_truth" / f"{sample_id}.ply"
                rgb_path.parent.mkdir(parents=True, exist_ok=True)
                mask_path.parent.mkdir(parents=True, exist_ok=True)
                mesh_path.parent.mkdir(parents=True, exist_ok=True)
                distortion = (-0.008, 0.0, 0.006)[view_index]
                bpy.context.view_layer.update()
                _save_render(scene, camera, mask_material, ground, rgb_path, mask_path, distortion)
                obj_objects = [obj for obj in scene.objects if obj != ground and obj.type == "MESH"]
                mesh_record = _mesh_truth(obj_objects, mesh_path)
                metric_bands = synthetic_packaging_metric_bands(
                    nominal_dimensions_mm=tuple(float(value) for value in spec["size"]),
                    mesh_extent_mm=tuple(mesh_record["bounds_mm_from_generated_vertices"]),
                    scenario_tolerances_mm=tuple(float(value) for value in spec["tol"]),
                )
                record = {
                    "id": sample_id,
                    "family": family,
                    "synthetic": True,
                    "source": {"kind": "procedural_blender", "generator": "tools/datasets/generate_packaging_benchmark.py", "version": GENERATOR_VERSION, "seed": SEED},
                    "material_appearance": {"polymer_assumption": MATERIALS[material_id]["polymer"], "finish": material_id, "roughness": MATERIALS[material_id]["roughness"], "transmission_weight": MATERIALS[material_id]["transmission"], "warning": "idealized shader; not measured resin optical behavior"},
                    "dimensions_mm_nominal_simulated": list(spec["size"]),
                    "manufacturing_tolerance_mm_simulated": {"each_axis_plus_minus": list(spec["tol"]), "source": "generator scenario input; not supplier or physical tolerance evidence"},
                    "expected_geometry_extent_mm": mesh_record["bounds_mm_from_generated_vertices"],
                    "expected_software_metric_bands": {
                        key: {"lower": band.lower, "upper": band.upper, "unit": band.unit, "provenance": band.provenance, "authority": band.authority}
                        for key, band in sorted(metric_bands.items())
                    },
                    "camera": {"model": "pinhole plus Blender compositor lens distortion", "resolution_px": [WIDTH, HEIGHT], "focal_length_mm": 50.0, "sensor_mm": [36.0, 27.0], "sensor_fit": "HORIZONTAL", "fx_px": round(WIDTH * 50.0 / 36.0, 6), "fy_px": round(WIDTH * 50.0 / 36.0, 6), "cx_px": WIDTH / 2, "cy_px": HEIGHT / 2, "camera_to_world_row_major": _world_matrix_camera(camera), "blender_lens_distortion_factor_simulated": distortion, "view_index": view_index},
                    "lighting": lights,
                    "render": {"engine": "Blender Eevee", "blender_version": bpy.app.version_string, "resolution_px": [WIDTH, HEIGHT], "color_management": "AgX", "controlled_sensor_noise": "not applied", "shadow_and_reflection": "Blender area-light approximations"},
                    "files": {
                        "rgb": {"path": rgb_path.relative_to(staging).as_posix(), "bytes": rgb_path.stat().st_size, "sha256": hashlib.sha256(rgb_path.read_bytes()).hexdigest(), "format": "PNG"},
                        "mask": {"path": mask_path.relative_to(staging).as_posix(), "bytes": mask_path.stat().st_size, "sha256": hashlib.sha256(mask_path.read_bytes()).hexdigest(), "format": "PNG"},
                        "geometry": {**mesh_record, "path": mesh_path.relative_to(staging).as_posix()},
                    },
                    "expected_software_use": ["reconstruction", "segmentation", "camera_calibration", "measurement", "scan_master_preview", "design_model_family_regression"],
                    "measurement_authority": "synthetic generator inputs only; no physical or Kenya ground truth",
                }
                records.append(record)
                # Avoid accumulating scene objects and material memory.
                for obj in list(scene.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)

    manifest = {
        "schema_version": "1.0",
        "dataset_id": "packlab-m17-synthetic-packaging-v2",
        "generator_version": GENERATOR_VERSION,
        "seed": SEED,
        "fully_synthetic": True,
        "physical_measurements_present": False,
        "owner_internal_use_scope": "PackLab development/CI and owner-controlled design-office and future Kenya-factory use; no external reuse, sublicense, sale or marketing permission",
        "samples": records,
    }
    manifest_path = staging / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    with manifest_path.open("xb") as stream:
        stream.write(manifest_bytes)
    staging.rename(final_output)
    staging_parent.rmdir()
    manifest_path = final_output / "manifest.json"
    return {"sample_count": len(records), "manifest": str(manifest_path), "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest()}


def _args() -> Path:
    argv = sys.argv
    if "--" not in argv or len(argv) <= argv.index("--") + 1:
        raise SystemExit("expected -- --out <directory outside Git>")
    tail = argv[argv.index("--") + 1 :]
    if len(tail) != 2 or tail[0] != "--out":
        raise SystemExit("expected -- --out <directory outside Git>")
    # Keep the user spelling intact until resolve_dataset_root has checked it
    # against the canonical path and inspected each suffix component for links.
    return Path(os.path.expandvars(tail[1])).expanduser()


if __name__ == "__main__":
    result = generate(_args())
    print(json.dumps(result, sort_keys=True))
