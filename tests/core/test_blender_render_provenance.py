from __future__ import annotations

import pytest

from packlab_core.blender_render_provenance import (
    BlenderRenderProvenanceError,
    create_m14_render_provenance,
)


def _provenance(**overrides):
    values = {
        "packlab_commit": "a" * 40,
        "packlab_version": "0.1.0",
        "blender_executable_sha256": "b" * 64,
        "blender_build": {
            "version": [5, 2, 2],
            "version_string": "5.2.2 LTS",
            "build_hash": "d13f752e3b9c",
            "build_branch": "blender-v5.2-release",
            "build_date": "2026-09-15",
        },
        "scene_package_revision_id": "blender-scene-package:" + "c" * 64,
        "scene_package_sha256": "d" * 64,
        "source_revisions_and_digests": {
            "design_model_revision_id": "design-model:" + "e" * 64,
            "cad_brep_revision_id": "cad-brep:" + "f" * 64,
            "coordinate_unit": "mm_unverified",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        },
        "render_engine": "BLENDER_EEVEE",
        "render_device": "EEVEE_DEFAULT",
        "render_settings": {"width": 256, "height": 256, "samples": 8},
        "camera_light_preset_ids": ["blender-render-preset:" + "1" * 64],
        "outputs": [
            {
                "artifact_type": "STILL_PNG",
                "relative_path": "renders/front.png",
                "sha256": "2" * 64,
                "byte_length": 1024,
                "view": "FRONT",
            }
        ],
    }
    values.update(overrides)
    return create_m14_render_provenance(**values)


def test_shared_provenance_identity_is_deterministic_and_excludes_output_paths() -> None:
    first = _provenance()
    # A portable relative output location is useful evidence but is not identity authority.
    second = _provenance(
        outputs=[
            {
                "artifact_type": "STILL_PNG",
                "relative_path": "elsewhere/front.png",
                "sha256": "2" * 64,
                "byte_length": 1024,
                "view": "FRONT",
            }
        ]
    )
    assert first["identity"] == second["identity"]
    assert first["outputs"][0]["relative_path"] != second["outputs"][0]["relative_path"]
    assert "relative_path" not in first["identity_payload"]["outputs"][0]
    assert "timestamp" not in first["identity_payload"]
    assert first["limitations"]["cross_hardware_pixel_identity_guaranteed"] is False
    assert first["limitations"]["physical_accuracy_inferred"] is False
    assert first["limitations"]["material_certified"] is False
    assert first["limitations"]["production_authority_escalated"] is False


def test_shared_provenance_identity_binds_output_digests_and_packlab_build() -> None:
    original = _provenance()
    changed_output = _provenance(
        outputs=[
            {
                "artifact_type": "STILL_PNG",
                "relative_path": "renders/front.png",
                "sha256": "3" * 64,
                "byte_length": 1024,
                "view": "FRONT",
            }
        ]
    )
    changed_commit = _provenance(packlab_commit="4" * 40)
    assert original["identity"] != changed_output["identity"]
    assert original["identity"] != changed_commit["identity"]


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"packlab_commit": "short"}, "render_provenance_packlab_commit_invalid"),
        (
            {"blender_executable_sha256": "bad"},
            "render_provenance_blender_executable_digest_invalid",
        ),
        (
            {
                "outputs": [
                    {
                        "artifact_type": "GLB",
                        "relative_path": "C:/private/model.glb",
                        "sha256": "2" * 64,
                        "byte_length": 100,
                    }
                ]
            },
            "render_provenance_output_invalid",
        ),
        (
            {"render_settings": {"workspace": "C:\\Users\\sekip\\PackLab"}},
            "render_provenance_ambient_path_forbidden",
        ),
    ],
)
def test_shared_provenance_rejects_invalid_or_private_inputs(override, reason) -> None:
    with pytest.raises(BlenderRenderProvenanceError, match=reason):
        _provenance(**override)
