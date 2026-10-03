from __future__ import annotations

import pytest
from test_symmetric_section_loft import PROJECT, _build, _scan_master

from packlab_core.cross_section import (
    CrossSectionSymmetry,
    SectionPoint,
)
from packlab_core.design_history import DesignModelHistory
from packlab_core.design_symmetry_constraints import (
    DesignSymmetryError,
    revise_section_symmetry,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256


def _slightly_asymmetric_scan():
    source = _scan_master()
    vertices = list(source.mesh.vertices)
    index = next(i for i, point in enumerate(vertices) if point[2] == 2.0)
    x, y, z = vertices[index]
    vertices[index] = (x + 0.0000001, y, z)
    mesh = TriangleMeshData(tuple(vertices), source.mesh.triangles)
    manifest = dict(source.manifest)
    revision_id = source.revision_id + "-perturbed"
    manifest["scan_master_revision_id"] = revision_id
    manifest["output_geometry_sha256"] = mesh_sha256(mesh)
    return ScanMasterRevision(revision_id, PROJECT, mesh, manifest)


def _revise(loft, section, symmetry, **kwargs):
    return revise_section_symmetry(
        loft.model if "model" not in kwargs else kwargs.pop("model"),
        loft,
        section=section,
        section_index=0,
        expected_model_revision_id=(
            loft.model.revision_id
            if "expected_model_revision_id" not in kwargs
            else kwargs.pop("expected_model_revision_id")
        ),
        expected_scan_master_revision_id=loft.scan_master_revision_id,
        expected_scan_master_geometry_sha256=loft.scan_master_geometry_sha256,
        target_symmetry=symmetry,
        actor_id="operator-1",
        reason="Edit section symmetry constraint.",
        created_at_utc="2026-10-03T16:00:00Z",
        **kwargs,
    )


@pytest.mark.parametrize(
    "symmetry",
    [
        CrossSectionSymmetry.LEFT_RIGHT,
        CrossSectionSymmetry.FRONT_BACK,
        CrossSectionSymmetry.BOTH,
        CrossSectionSymmetry.NONE,
    ],
)
def test_symmetry_toggle_creates_deterministic_revision_and_persists_section(symmetry):
    _, loft = _build(_scan_master())
    source = loft.sections[0]
    first = _revise(loft, source, symmetry)
    repeat = _revise(loft, source, symmetry)

    assert first == repeat
    assert first.section.symmetry is symmetry
    assert first.model.previous_revision_id == loft.model.revision_id
    assert first.model.revision_id != loft.model.revision_id
    assert first.model.parent_binding_revision_id == loft.parent_binding_revision_id
    assert first.model.scan_master_geometry_sha256 == loft.scan_master_geometry_sha256
    assert first.model.scale_state is loft.model.scale_state
    assert first.model.coordinate_unit == "mm_unverified"
    assert first.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.model.mold_use_authorized is False
    assert first.parameter.as_dict()["value"]["section"] == first.section.as_dict()
    assert first.as_dict()["scan_master_changed"] is False


def test_control_point_edit_propagates_mirrored_parameter_and_keeps_axes():
    _, loft = _build(_scan_master())
    section = loft.sections[0]
    updated = _revise(
        loft,
        section,
        CrossSectionSymmetry.LEFT_RIGHT,
        edited_point_index=1,
        edited_point=SectionPoint(section.points[1].x + 0.1, section.points[1].y + 0.1),
    )
    changed = updated.section.points[1]

    assert updated.section.center_x == section.center_x
    assert updated.section.center_y == section.center_y
    assert SectionPoint(2 * section.center_x - changed.x, changed.y) in updated.section.points
    assert updated.parameter.as_dict()["value"]["section"]["points"] == [
        {"x": point.x, "y": point.y} for point in updated.section.points
    ]


def test_repeated_toggles_use_the_current_section_and_keep_revision_lineage():
    _, loft = _build(_scan_master())
    first = _revise(loft, loft.sections[0], CrossSectionSymmetry.LEFT_RIGHT)
    second = _revise(
        loft,
        first.section,
        CrossSectionSymmetry.FRONT_BACK,
        model=first.model,
        expected_model_revision_id=first.model.revision_id,
    )
    assert second.section.symmetry is CrossSectionSymmetry.FRONT_BACK
    assert second.model.previous_revision_id == first.model.revision_id
    assert second.parameter.as_dict()["value"]["section"] == second.section.as_dict()


def test_impossible_constraint_and_stale_revision_are_rejected():
    _, asymmetric = _build(_scan_master(asymmetric=True), symmetry=False)
    with pytest.raises(DesignSymmetryError, match="section_constraint_rejected"):
        _revise(asymmetric, asymmetric.sections[0], CrossSectionSymmetry.BOTH)

    _, symmetric = _build(_scan_master())
    with pytest.raises(DesignSymmetryError, match="design_model_revision_stale"):
        _revise(
            symmetric,
            symmetric.sections[0],
            CrossSectionSymmetry.NONE,
            expected_model_revision_id="stale-revision",
        )


def test_scan_evidence_disagreement_is_exposed_without_changing_scan_parent():
    _, loft = _build(_slightly_asymmetric_scan())
    evidence = loft.symmetry_evidence[0]
    assert evidence.left_right_reflection_error_ratio > 0.0
    updated = _revise(
        loft,
        loft.sections[0],
        CrossSectionSymmetry.BOTH,
        evidence_disagreement_tolerance=evidence.left_right_reflection_error_ratio / 2,
    )
    expected_axes = tuple(
        axis
        for axis, error in (
            ("left_right", evidence.left_right_reflection_error_ratio),
            ("front_back", evidence.front_back_reflection_error_ratio),
        )
        if error > evidence.left_right_reflection_error_ratio / 2
    )

    assert updated.disagreement_axes == expected_axes
    assert updated.evidence_disagreement is True
    assert updated.evidence_disagreement is bool(expected_axes)
    evidence = updated.parameter.as_dict()["value"]["scan_evidence"]
    assert evidence["scan_master_revision_id"] == loft.scan_master_revision_id
    assert evidence["scan_master_geometry_sha256"] == loft.scan_master_geometry_sha256
    assert evidence["disagreement_axes"] == list(expected_axes)


def test_history_undo_redo_restores_constraint_parameter_as_new_revisions():
    _, loft = _build(_scan_master())
    edited = _revise(loft, loft.sections[0], CrossSectionSymmetry.FRONT_BACK)
    history = DesignModelHistory(loft.model).apply(
        edited.history_command,
        actor_id="operator-1",
        reason="Edit section symmetry constraint.",
        created_at_utc="2026-10-03T16:00:00Z",
    )
    assert history.current_revision == edited.model

    undone = history.undo(actor_id="operator-1", created_at_utc="2026-10-03T16:01:00Z")
    assert undone.current_revision.previous_revision_id == edited.model.revision_id
    assert edited.parameter.parameter_id not in {
        parameter.parameter_id for parameter in undone.current_revision.parameters
    }
    redone = undone.redo(actor_id="operator-1", created_at_utc="2026-10-03T16:02:00Z")
    assert redone.current_revision.previous_revision_id == undone.current_revision.revision_id
    assert (
        next(
            item
            for item in redone.current_revision.parameters
            if item.parameter_id == edited.parameter.parameter_id
        )
        == edited.parameter
    )


def test_scan_parent_mismatch_and_invalid_tolerance_fail_closed():
    _, loft = _build(_scan_master())
    with pytest.raises(DesignSymmetryError, match="scan_master_parent_binding_mismatch"):
        revise_section_symmetry(
            loft.model,
            loft,
            section=loft.sections[0],
            section_index=0,
            expected_model_revision_id=loft.model.revision_id,
            expected_scan_master_revision_id="another-scan-parent",
            expected_scan_master_geometry_sha256=loft.scan_master_geometry_sha256,
            target_symmetry=CrossSectionSymmetry.NONE,
            actor_id="operator-1",
            reason="Reject wrong parent.",
            created_at_utc="2026-10-03T16:00:00Z",
        )
    with pytest.raises(DesignSymmetryError, match="evidence_disagreement_tolerance_invalid"):
        _revise(
            loft,
            loft.sections[0],
            CrossSectionSymmetry.NONE,
            evidence_disagreement_tolerance=float("nan"),
        )
    with pytest.raises(DesignSymmetryError, match="scan_master_parent_binding_mismatch"):
        revise_section_symmetry(
            loft.model,
            loft,
            section=loft.sections[0],
            section_index=0,
            expected_model_revision_id=loft.model.revision_id,
            expected_scan_master_revision_id=loft.scan_master_revision_id,
            expected_scan_master_geometry_sha256=None,
            target_symmetry=CrossSectionSymmetry.NONE,
            actor_id="operator-1",
            reason="Reject invalid parent digest.",
            created_at_utc="2026-10-03T16:00:00Z",
        )
