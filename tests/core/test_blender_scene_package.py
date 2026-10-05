from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest
from tests.core.test_label_zone import BODY_ID, COMPONENT_ID, _model, _representation

import packlab_core.blender_scene_package as scene_package
from packlab_core.blender_scene_package import (
    BLENDER_SCENE_PACKAGE_CONTRACT,
    BLENDER_SCENE_RUNNER,
    BlenderArtworkBinding,
    BlenderScenePackageError,
    ProjectAssetReference,
    create_blender_scene_package,
)
from packlab_core.cad_mesh_export import CadMeshExportRevision
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
from packlab_core.label_zone import LabelZoneBoundary, LabelZoneKind, create_label_zone
from packlab_core.label_zone_placement import create_label_zone_placement_revision
from packlab_core.visual_material_library import (
    MaterialFamily,
    MaterialSourceClass,
    VisualMaterialRecord,
    create_visual_material_library,
)


def _sources():
    model = _model(label="blender-scene-package")
    library = create_visual_material_library(
        (
            VisualMaterialRecord(
                "material-hdpe",
                MaterialFamily.HDPE,
                'HDPE "reference" \\ visual',
                (0.8, 0.85, 0.9, 1.0),
                0.0,
                0.4,
                MaterialSourceClass.USER_AUTHORED_VISUAL,
            ),
        )
    )
    assignment = create_geometry_material_assignment(model, COMPONENT_ID, library, "material-hdpe")
    project = create_component_material_project(
        model,
        library,
        (
            ComponentMaterialProjectEntry(
                COMPONENT_ID,
                create_component_visual_assignment_state(assignment),
            ),
        ),
    )
    glb = b"fixture-glb-data"
    export = CadMeshExportRevision(
        export_id="cad-export:fixture",
        obj_sha256=hashlib.sha256(b"obj").hexdigest(),
        obj_size_bytes=3,
        obj_manifest_id="cad-export-manifest:obj",
        obj_manifest_sha256=hashlib.sha256(b"obj-manifest").hexdigest(),
        glb_sha256=hashlib.sha256(glb).hexdigest(),
        glb_size_bytes=len(glb),
        glb_manifest_id="cad-export-manifest:glb",
        glb_manifest_sha256=hashlib.sha256(b"glb-manifest").hexdigest(),
        source_design_model_revision_id=model.revision_id,
        source_brep_revision_id="cad-brep:fixture",
        source_brep_geometry_sha256=hashlib.sha256(b"brep").hexdigest(),
        source_preview_revision_id="cad-preview:fixture",
        parent_kind=model.parent_kind.value,
        parent_authority_revision_id=model.standalone_root.revision_id,
        scale_state=model.scale_state.value,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status="DEFERRED_OWNER_VALIDATION",
        mold_use_authorized=False,
        semantic_part_name="package-body",
        vertex_count=8,
        triangle_count=12,
        feature_mapping=({"feature_id": BODY_ID, "component_id": COMPONENT_ID},),
    )
    glb_ref = ProjectAssetReference("assets/model.glb", export.glb_sha256, len(glb))
    package = create_blender_scene_package(model, export, glb_ref, project, library)
    return model, export, library, project, glb_ref, package


def test_package_is_deterministic_versioned_and_does_not_mutate_sources() -> None:
    model, export, library, project, glb_ref, first = _sources()
    before = (model.as_dict(), export.as_dict(), project.canonical_bytes(), library.as_dict())
    second = create_blender_scene_package(model, export, glb_ref, project, library)

    assert first == second
    assert first.manifest_bytes.endswith(b"\n")
    assert first.manifest()["body"]["contract"] == BLENDER_SCENE_PACKAGE_CONTRACT
    assert first.manifest()["body"]["source"]["cad_glb_sha256"] == export.glb_sha256
    assert first.manifest()["body"]["source"]["design_model_revision_id"] == model.revision_id
    assert first.manifest()["body"]["assets"][0]["project_relative_path"] == "assets/model.glb"
    material_reference = first.manifest()["body"]["components"][0]["material_visual_reference"]
    assert material_reference["display_name"] == 'HDPE "reference" \\ visual'
    assert material_reference["display_name"].encode() not in first.runner_script
    assert b'arbitrary_user_code_included":false' in first.manifest_bytes
    assert (
        model.as_dict(),
        export.as_dict(),
        project.canonical_bytes(),
        library.as_dict(),
    ) == before


@pytest.mark.parametrize(
    "path",
    [
        "../secret",
        "/absolute/file",
        "C:/secret",
        "assets\\model.glb",
        "assets/../secret",
        "assets//model.glb",
    ],
)
def test_asset_references_reject_unsafe_or_noncanonical_paths(path: str) -> None:
    with pytest.raises(BlenderScenePackageError, match="scene_asset_path_not_safe_relative"):
        ProjectAssetReference(path, "a" * 64, 1)


def test_stale_export_digest_and_ambient_identity_are_rejected_or_absent() -> None:
    model, export, library, project, glb_ref, package = _sources()
    with pytest.raises(BlenderScenePackageError, match="scene_cad_glb_asset_digest_mismatch"):
        create_blender_scene_package(
            model,
            export,
            replace(glb_ref, sha256="0" * 64),
            project,
            library,
        )
    assert str(__import__("pathlib").Path.cwd()).encode() not in package.manifest_bytes
    assert str(__import__("pathlib").Path.cwd()).encode() not in package.runner_script
    assert "exec(" not in BLENDER_SCENE_RUNNER
    assert "eval(" not in BLENDER_SCENE_RUNNER
    json.loads(package.manifest_bytes)


def test_scene_runner_rejects_manifest_body_tampering() -> None:
    # The runner validates a content-addressed data envelope before inspecting assets.
    assert "manifest_digest_invalid" in BLENDER_SCENE_RUNNER
    assert "asset_digest_mismatch" in BLENDER_SCENE_RUNNER
    assert "bpy.app.version[0]" in BLENDER_SCENE_RUNNER


def _artwork_binding(model, export):
    brep = _representation(model, (BODY_ID,))
    export = replace(
        export,
        source_brep_revision_id=brep.revision_id,
        source_brep_geometry_sha256=brep.geometry_sha256,
    )
    zone = create_label_zone(
        model,
        brep,
        zone_kind=LabelZoneKind.FRONT,
        component_id=COMPONENT_ID,
        feature_id=BODY_ID,
        boundary=LabelZoneBoundary(0.1, 0.1, 0.8, 0.9),
    )
    placement = create_label_zone_placement_revision(
        zone,
        zone.boundary,
        actor_id="operator-1",
        reason="Bind scene artwork to the exact label placement.",
        created_at_utc="2026-10-04T14:00:00Z",
    )
    content = (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" '
        b'viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'
    )
    artwork = ingest_label_artwork(content)
    mapping = map_label_artwork_to_zone(artwork, placement)
    assignment = create_label_artwork_assignment(mapping, placement, variant_id="front-primary")
    asset = ProjectAssetReference("assets/label.svg", artwork.content_sha256, artwork.byte_size)
    return export, BlenderArtworkBinding(assignment, placement, mapping, artwork, asset)


def test_artwork_is_bound_to_exact_zone_mapping_and_asset_digest() -> None:
    model, export, library, project, glb_ref, _ = _sources()
    export, binding = _artwork_binding(model, export)
    package = create_blender_scene_package(
        model,
        export,
        glb_ref,
        project,
        library,
        artwork_bindings=(binding,),
    )
    manifest = package.manifest()["body"]
    assert manifest["artworks"][0]["assignment"]["revision_id"] == (binding.assignment.revision_id)
    assert manifest["artworks"][0]["mapping"]["revision_id"] == binding.mapping.revision_id
    assert manifest["artworks"][0]["artwork"]["revision_id"] == binding.artwork.revision_id
    assert manifest["artworks"][0]["asset_project_relative_path"] == "assets/label.svg"
    assert manifest["artworks"][0]["physical_fit_verified"] is False

    stale_binding = replace(binding, asset=replace(binding.asset, sha256="0" * 64))
    with pytest.raises(BlenderScenePackageError, match="scene_artwork_provenance_stale"):
        create_blender_scene_package(
            model,
            export,
            glb_ref,
            project,
            library,
            artwork_bindings=(stale_binding,),
        )


def test_object_material_and_artwork_count_limits_fail_closed(monkeypatch) -> None:
    model, export, library, project, glb_ref, _ = _sources()
    export, binding = _artwork_binding(model, export)
    with monkeypatch.context() as patch:
        patch.setattr(scene_package, "MAX_SCENE_OBJECTS", 0)
        with pytest.raises(BlenderScenePackageError, match="scene_object_count_limit_exceeded"):
            create_blender_scene_package(model, export, glb_ref, project, library)
    with monkeypatch.context() as patch:
        patch.setattr(scene_package, "MAX_SCENE_MATERIALS", 0)
        with pytest.raises(BlenderScenePackageError, match="scene_material_count_limit_exceeded"):
            create_blender_scene_package(model, export, glb_ref, project, library)
    with monkeypatch.context() as patch:
        patch.setattr(scene_package, "MAX_SCENE_ARTWORKS", 0)
        with pytest.raises(BlenderScenePackageError, match="scene_artwork_count_limit_exceeded"):
            create_blender_scene_package(
                model,
                export,
                glb_ref,
                project,
                library,
                artwork_bindings=(binding,),
            )
