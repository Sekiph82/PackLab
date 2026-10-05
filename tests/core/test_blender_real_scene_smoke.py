from __future__ import annotations

import hashlib
import importlib
import json
import os
import struct
import subprocess
from pathlib import Path

import pytest
from tests.core.test_label_zone import BODY_ID, COMPONENT_ID, _model

from packlab_core.blender_scene_package import (
    BlenderArtworkBinding,
    ProjectAssetReference,
    create_blender_scene_package,
)
from packlab_core.cad_adapter import _registered_shape_build
from packlab_core.cad_brep import _representation_from_lineage
from packlab_core.cad_label_surface_analysis import (
    CadLabelSurfacePolicy,
    analyze_cad_label_surfaces,
)
from packlab_core.cad_mesh_export import export_design_model_obj_glb
from packlab_core.cad_preview import tessellate_brep_preview
from packlab_core.component_material_project import (
    ComponentMaterialProjectEntry,
    create_component_material_project,
)
from packlab_core.component_visual_assignments import (
    create_component_visual_assignment_state,
    create_geometry_material_assignment,
)
from packlab_core.label_artwork import (
    create_label_artwork_assignment,
    ingest_label_artwork,
    map_label_artwork_to_zone,
)
from packlab_core.label_metric_surface_binding import create_label_metric_surface_binding
from packlab_core.label_zone import LabelZoneBoundary, LabelZoneKind, create_label_zone
from packlab_core.label_zone_placement import create_label_zone_placement_revision
from packlab_core.pbr_visual_parameters import create_pbr_visual_parameter_revision
from packlab_core.visual_material_library import (
    MaterialFamily,
    MaterialSourceClass,
    VisualMaterialRecord,
    create_visual_material_library,
)


def _png_rgba_2x2() -> bytes:
    import zlib

    def chunk(name: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + name
            + payload
            + struct.pack(">I", zlib.crc32(name + payload) & 0xFFFFFFFF)
        )

    pixels = b"\x00\xff\x20\x10\xff\x40\xff\x80\xff" + b"\x00\x00\x40\xff\xff\xff\xff\xff\xff"
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


def _hybrid_sources(root: Path):
    model = _model(label="pl0326-real-scene")
    brep_api = importlib.import_module("OCP.BRepPrimAPI")
    boolean_api = importlib.import_module("OCP.BRepAlgoAPI")
    gp = importlib.import_module("OCP.gp")
    box = brep_api.BRepPrimAPI_MakeBox(100.0, 60.0, 40.0).Shape()
    cylinder_axis = gp.gp_Ax2(gp.gp_Pnt(50.0, 30.0, 40.0), gp.gp_Dir(0.0, 0.0, 1.0))
    cylinder = brep_api.BRepPrimAPI_MakeCylinder(cylinder_axis, 5.0, 20.0).Shape()
    fuse = boolean_api.BRepAlgoAPI_Fuse(box, cylinder)
    fuse.Build()
    if not fuse.IsDone():
        raise AssertionError("fixture_fused_brep_failed")
    shape = fuse.Shape()
    shape_build = _registered_shape_build(model, "pl0326-hybrid-fixture", (BODY_ID,), shape, 1)
    brep = _representation_from_lineage(
        model,
        "pl0326-hybrid-fixture",
        (BODY_ID,),
        shape_build,
        source_feature_ids=(BODY_ID,),
    )

    library = create_visual_material_library(
        (
            VisualMaterialRecord(
                "material-hdpe",
                MaterialFamily.HDPE,
                "Visual HDPE",
                (0.75, 0.82, 0.9, 1.0),
                0.0,
                0.4,
                MaterialSourceClass.USER_AUTHORED_VISUAL,
            ),
        )
    )
    material_assignment = create_geometry_material_assignment(
        model, COMPONENT_ID, library, "material-hdpe"
    )
    pbr = create_pbr_visual_parameter_revision(
        material_assignment,
        base_color_rgb=(0.6, 0.7, 0.8),
        roughness_factor=0.35,
        transmission_factor=0.05,
        opacity_factor=1.0,
        ior=1.4,
    )
    project = create_component_material_project(
        model,
        library,
        (
            ComponentMaterialProjectEntry(
                COMPONENT_ID, create_component_visual_assignment_state(material_assignment)
            ),
        ),
    )

    asset_dir = root / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    obj_path, glb_path = asset_dir / "model.obj", asset_dir / "model.glb"
    preview = tessellate_brep_preview(model, brep)
    cad_export = export_design_model_obj_glb(model, brep, preview, obj_path, glb_path)

    png = _png_rgba_2x2()
    artwork_path = asset_dir / "label.png"
    artwork_path.write_bytes(png)
    artwork = ingest_label_artwork(png)
    analysis = analyze_cad_label_surfaces(
        model, brep, CadLabelSurfacePolicy((0.0, 1.0, 0.0), 90.0, 1_000_000.0)
    )
    contexts = []
    for kind, selected in (
        (
            LabelZoneKind.FRONT,
            lambda item: (
                item.surface_type == "GeomAbs_Plane" and item.center[1] == pytest.approx(60.0)
            ),
        ),
        (
            LabelZoneKind.BACK,
            lambda item: (
                item.surface_type == "GeomAbs_Plane" and item.center[1] == pytest.approx(0.0)
            ),
        ),
        (LabelZoneKind.WRAP, lambda item: item.surface_type == "GeomAbs_Cylinder"),
    ):
        boundary = LabelZoneBoundary(0.1, 0.15, 0.8, 0.85)
        zone = create_label_zone(
            model,
            brep,
            zone_kind=kind,
            component_id=COMPONENT_ID,
            feature_id=BODY_ID,
            boundary=boundary,
        )
        placement = create_label_zone_placement_revision(
            zone,
            boundary,
            actor_id="operator-1",
            reason="Create exact scene smoke artwork placement.",
            created_at_utc="2026-10-05T12:00:00Z",
        )
        candidate = next(item for item in analysis.candidates if selected(item))
        metric_binding = create_label_metric_surface_binding(
            model, brep, placement, analysis, candidate.analysis_region_id
        )
        mapping = map_label_artwork_to_zone(artwork, placement, fit_mode="STRETCH")
        assignment = create_label_artwork_assignment(
            mapping,
            placement,
            variant_id=f"{kind.value}-smoke",
            wrap_seam_u_normalized=0.0 if kind is LabelZoneKind.WRAP else None,
        )
        contexts.append(
            BlenderArtworkBinding(
                assignment,
                placement,
                mapping,
                artwork,
                ProjectAssetReference(
                    "assets/label.png", artwork.content_sha256, artwork.byte_size
                ),
                analysis,
                metric_binding,
            )
        )
    glb_bytes = glb_path.read_bytes()
    package = create_blender_scene_package(
        model,
        cad_export,
        ProjectAssetReference(
            "assets/model.glb", hashlib.sha256(glb_bytes).hexdigest(), len(glb_bytes)
        ),
        project,
        library,
        pbr_parameters=(pbr,),
        artwork_bindings=tuple(contexts),
        brep_representation=brep,
    )
    (root / "blender_scene_manifest.json").write_bytes(package.manifest_bytes)
    (root / "blender_scene_runner.py").write_bytes(package.runner_script)
    return package


@pytest.mark.skipif(
    os.environ.get("PACKLAB_REAL_BLENDER_SMOKE") != "1",
    reason="set PACKLAB_REAL_BLENDER_SMOKE=1 to run the approved real Blender scene smoke",
)
def test_real_blender_scene_imports_material_and_planar_cylindrical_png_overlays(
    tmp_path: Path,
) -> None:
    executable = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
    if not executable.is_file():
        pytest.fail("approved_blender_5_2_2_executable_unavailable")
    package = _hybrid_sources(tmp_path)
    command = [
        str(executable),
        "--background",
        "--factory-startup",
        "--disable-autoexec",
        "--python",
        str(tmp_path / "blender_scene_runner.py"),
        "--",
        "--project-root",
        str(tmp_path),
        "--manifest",
        "blender_scene_manifest.json",
        "--result",
        "scene_result_manifest.json",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
    combined = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined[-8_000:]
    assert "PACKLAB_SCENE_PACKAGE_VALID 5.2.2 LTS" in combined
    result = json.loads((tmp_path / "scene_result_manifest.json").read_text("utf-8"))
    assert result["geometry_binding"]["mode"] == "WHOLE_SOLID_SINGLE_COMPONENT"
    assert result["scene_package_revision_id"] == package.revision_id
    assert result["base_object"]["material_slot_count"] == 1
    assert result["base_object"]["uv_layer_count"] == 0
    assert result["base_object"]["pbr_visual_parameter_revision_id"]
    assert result["base_object"]["effective_shader_values"]["roughness_factor"] == pytest.approx(
        0.35
    )
    assert result["base_object"]["effective_shader_values"]["transmission_factor"] == pytest.approx(
        0.05
    )
    assert result["base_object"]["effective_shader_values"]["ior"] == pytest.approx(1.4)
    assert {item["mapping_mode"] for item in result["overlays"]} == {
        "PLANAR_RECTANGULAR",
        "CYLINDRICAL_WRAP",
    }
    assert len(result["overlays"]) == 3
    assert all(item["image_loaded"] and item["uv_layer_count"] == 1 for item in result["overlays"])
    assert all(item["uv_minimum"] == pytest.approx([0.0, 0.0]) for item in result["overlays"])
    assert all(item["uv_maximum"] == pytest.approx([1.0, 1.0]) for item in result["overlays"])
    assert all(item["uv_first_loop"] == pytest.approx([0.0, 1.0]) for item in result["overlays"])
    assert result["renderer_only_offsets_are_non_physical"] is True
    assert result["physical_accuracy_inferred"] is False
    assert result["network_access"] == "NONE"
    assert result["automatic_downloads"] is False
    assert result["blender"]["build_hash"]
    assert result["blender"]["build_branch"]
    assert result["blender"]["build_date"]
    first_result_bytes = (tmp_path / "scene_result_manifest.json").read_bytes()

    manifest_path = tmp_path / "blender_scene_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    tampered_manifest = json.loads(manifest_bytes)
    tampered_manifest["body"]["scene"]["overlays"][0]["revision_id"] = "stale-overlay"
    manifest_path.write_text(json.dumps(tampered_manifest), encoding="utf-8")
    rejected_binding = subprocess.run(
        command, capture_output=True, text=True, timeout=180, check=False
    )
    binding_output = rejected_binding.stdout + rejected_binding.stderr
    assert "manifest_digest_invalid" in binding_output
    assert "PACKLAB_SCENE_PACKAGE_VALID" not in binding_output
    manifest_path.write_bytes(manifest_bytes)

    artwork_path = tmp_path / "assets" / "label.png"
    artwork_bytes = artwork_path.read_bytes()
    artwork_path.write_bytes(artwork_bytes[:-1] + bytes([artwork_bytes[-1] ^ 1]))
    rejected_asset = subprocess.run(
        command, capture_output=True, text=True, timeout=180, check=False
    )
    asset_output = rejected_asset.stdout + rejected_asset.stderr
    assert "asset_digest_mismatch" in asset_output
    assert "PACKLAB_SCENE_PACKAGE_VALID" not in asset_output
    artwork_path.write_bytes(artwork_bytes)

    repeated = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
    repeated_output = repeated.stdout + repeated.stderr
    assert repeated.returncode == 0, repeated_output[-8_000:]
    assert (tmp_path / "scene_result_manifest.json").read_bytes() == first_result_bytes
    assert (
        package.manifest()["body"]["scene"]["geometry_binding"]["mode"]
        == "WHOLE_SOLID_SINGLE_COMPONENT"
    )
