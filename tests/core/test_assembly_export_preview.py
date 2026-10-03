from __future__ import annotations

from dataclasses import replace

import pytest
from test_mating_references import _fixture as _mating_fixture

from packlab_core.assembly_export_preview import (
    AssemblyComponentPlacement,
    AssemblyExportPreviewError,
    validate_bottle_closure_assembly_for_export,
)
from packlab_core.design_model import revise_design_model_revision
from packlab_core.mating_references import create_neck_closure_mating_references
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import mesh_sha256

IDENTITY = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)
KNOWN_RIGID = (
    0.0,
    -1.0,
    0.0,
    2.0,
    1.0,
    0.0,
    0.0,
    3.0,
    0.0,
    0.0,
    1.0,
    4.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


def _fixture():
    scan, geometry, model, neck, closure, neck_sections, closure_sections = _mating_fixture()
    mating = create_neck_closure_mating_references(
        scan,
        geometry,
        model,
        neck.feature_id,
        closure.feature_id,
        neck_sections,
        closure_sections,
        expected_scan_master_revision_id=scan.revision_id,
        expected_model_revision_id=model.revision_id,
        actor_id="assembly-test-actor",
        reason="Create exact bottle/cap mating references.",
        created_at_utc="2026-10-03T19:00:00Z",
    )
    bottle = revise_design_model_revision(
        model,
        parameters=model.parameters,
        features=(neck,),
        actor_id="assembly-test-actor",
        reason="Create bottle component revision.",
        created_at_utc="2026-10-03T19:01:00Z",
    )
    cap = revise_design_model_revision(
        model,
        parameters=model.parameters,
        features=(closure,),
        actor_id="assembly-test-actor",
        reason="Create closure component revision.",
        created_at_utc="2026-10-03T19:02:00Z",
    )
    assert mating.model is not None
    return scan, model, bottle, cap, mating, neck, closure


def _placements(args, bottle_matrix=IDENTITY, closure_matrix=IDENTITY):
    _, _, bottle, cap, _, neck, closure = args
    return (
        AssemblyComponentPlacement(
            bottle.revision_id, neck.feature_id, bottle.coordinate_unit, bottle_matrix
        ),
        AssemblyComponentPlacement(
            cap.revision_id, closure.feature_id, cap.coordinate_unit, closure_matrix
        ),
    )


def _validate(args, bottle_matrix=IDENTITY, closure_matrix=IDENTITY, **overrides):
    scan, assembly, bottle, cap, mating, neck, closure = args
    bottle_placement, closure_placement = _placements(args, bottle_matrix, closure_matrix)
    values = {
        "expected_scan_master_revision_id": scan.revision_id,
        "expected_assembly_model_revision_id": assembly.revision_id,
        "expected_bottle_model_revision_id": bottle.revision_id,
        "expected_closure_model_revision_id": cap.revision_id,
        "expected_mating_reference_set_id": mating.reference_set_id,
        "bottle_feature_id": neck.feature_id,
        "neck_feature_id": neck.feature_id,
        "closure_feature_id": closure.feature_id,
    }
    values.update(overrides)
    return validate_bottle_closure_assembly_for_export(
        scan,
        assembly,
        bottle,
        cap,
        mating,
        bottle_placement,
        closure_placement,
        **values,
    )


def test_identity_and_known_rigid_transform_produce_deterministic_preview_metadata() -> None:
    args = _fixture()
    before = mesh_sha256(args[0].mesh)
    identity_preview = _validate(args)
    transformed = _validate(args, KNOWN_RIGID, KNOWN_RIGID)
    repeated = _validate(args, KNOWN_RIGID, KNOWN_RIGID)

    assert identity_preview.as_dict()["export_handoff_ready"] is True
    assert transformed.as_dict() == repeated.as_dict()
    assert transformed.assembly_id == repeated.assembly_id
    assert transformed.as_dict()["coordinate_unit"] == "mm_unverified"
    assert transformed.as_dict()["scale_state"] == ScaleState.METRIC_UNVERIFIED.value
    assert transformed.as_dict()["physical_accuracy_validation_status"] == (
        "DEFERRED_OWNER_VALIDATION"
    )
    assert transformed.as_dict()["step_exported"] is False
    assert transformed.as_dict()["cad_geometry_exported"] is False
    assert transformed.as_dict()["certified_claimed"] is False
    assert transformed.as_dict()["mold_ready_claimed"] is False
    assert transformed.as_dict()["mating_relationship"]["reference_planes_match_after_transform"]
    assert [item["role"] for item in transformed.as_dict()["components"]] == [
        "bottle",
        "closure",
    ]
    assert mesh_sha256(args[0].mesh) == before


def test_stale_component_revision_and_unit_mismatch_reject() -> None:
    args = _fixture()
    with pytest.raises(AssemblyExportPreviewError, match="component_revision_stale"):
        _validate(args, expected_closure_model_revision_id="stale-closure-revision")
    with pytest.raises(AssemblyExportPreviewError, match="mating_references_stale_or_incompatible"):
        _validate(args, expected_mating_reference_set_id="stale-mating-reference")

    bottle_placement, closure_placement = _placements(args)
    with pytest.raises(AssemblyExportPreviewError, match="placement_component_or_unit_mismatch"):
        validate_bottle_closure_assembly_for_export(
            args[0],
            args[1],
            args[2],
            args[3],
            args[4],
            bottle_placement,
            replace(closure_placement, coordinate_unit="mm"),
            expected_scan_master_revision_id=args[0].revision_id,
            expected_assembly_model_revision_id=args[1].revision_id,
            expected_bottle_model_revision_id=args[2].revision_id,
            expected_closure_model_revision_id=args[3].revision_id,
            expected_mating_reference_set_id=args[4].reference_set_id,
            bottle_feature_id=args[5].feature_id,
            neck_feature_id=args[5].feature_id,
            closure_feature_id=args[6].feature_id,
        )


def test_non_rigid_axis_and_plane_mismatches_reject() -> None:
    args = _fixture()
    non_rigid = list(IDENTITY)
    non_rigid[0] = 1.01
    with pytest.raises(AssemblyExportPreviewError, match="closure_transform_not_rigid"):
        _validate(args, closure_matrix=tuple(non_rigid))

    rotated_off_axis = (
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        -1.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )
    with pytest.raises(
        AssemblyExportPreviewError, match="component_axes_mismatch|plane_normals_mismatch"
    ):
        _validate(args, closure_matrix=rotated_off_axis)

    shifted_plane = list(IDENTITY)
    shifted_plane[11] = 0.25
    with pytest.raises(AssemblyExportPreviewError, match="component_reference_planes_mismatch"):
        _validate(args, closure_matrix=tuple(shifted_plane))
