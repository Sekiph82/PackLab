from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from packlab_core.base_plane import BasePlaneCandidate, BasePlaneSelection
from packlab_core.upright_alignment import (
    ManualUprightCorrection,
    UprightAlignmentError,
    compute_upright_alignment,
    serialize_upright_alignment,
)


def _selection(normal: tuple[float, float, float]) -> BasePlaneSelection:
    candidate = BasePlaneCandidate(
        "base-plane-candidate-1",
        normal,
        -2.0,
        (0, 1, 2, 3, 4, 5),
        0.75,
        0.001,
        0.70,
        "support_residual_heuristic_not_probability_or_accuracy",
    )
    return BasePlaneSelection(
        "base-plane-selection-1",
        "manual_override",
        "captured_geometry_base_plane_override_v1",
        "operator-1",
        "selected captured base plane",
        "object-geometry-1",
        "reconstruction-r1",
        "camera-solution-r1",
        "reconstruction_units",
        hashlib.sha256(b"synthetic points").hexdigest(),
        candidate,
    )


def test_already_upright_returns_identity_without_mutation_or_front_selection() -> None:
    selection = _selection((0.0, 0.0, 1.0))
    result = compute_upright_alignment(selection)
    assert result.quaternion_xyzw == (0.0, 0.0, 0.0, 1.0)
    assert result.rotation_matrix == (
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
    record = result.as_dict()
    assert record["mutates_source_geometry"] is False
    assert record["baked_geometry_created"] is False
    assert record["front_direction_selected"] is False


def test_tilted_up_direction_rotates_to_canonical_positive_z() -> None:
    result = compute_upright_alignment(_selection((0.0, 1.0, 1.0)))
    assert result.aligned_up_direction == pytest.approx((0.0, 0.0, 1.0))
    assert result.quaternion_xyzw[3] > 0.0
    assert result.rotation_matrix[12:16] == (0.0, 0.0, 0.0, 1.0)


@pytest.mark.parametrize("normal", [(0.0, 0.0, -1.0), (0.0, 0.0, 0.0)])
def test_antiparallel_and_degenerate_up_normals_fail_closed(normal) -> None:
    expected = "antiparallel" if normal[2] < 0 else "degenerate"
    with pytest.raises(UprightAlignmentError, match=expected):
        compute_upright_alignment(_selection(normal))


def test_quaternion_matrix_and_serialization_are_deterministic() -> None:
    selection = _selection((1.0, 2.0, 3.0))
    first = compute_upright_alignment(selection)
    second = compute_upright_alignment(selection)
    assert first.as_dict() == second.as_dict()
    assert serialize_upright_alignment(first) == serialize_upright_alignment(second)
    assert sum(value * value for value in first.quaternion_xyzw) == pytest.approx(1.0)
    assert first.aligned_up_direction == pytest.approx((0.0, 0.0, 1.0))


def test_manual_correction_is_actor_and_evidence_bound() -> None:
    selection = _selection((0.0, 0.0, 1.0))
    correction = ManualUprightCorrection(
        correction_id="upright-correction-1",
        actor_id="operator-2",
        evidence_id="operator-up-direction-1",
        evidence_digest=hashlib.sha256(b"synthetic correction evidence").hexdigest(),
        reason="corrected the selected object-up direction",
        base_plane_selection_id=selection.selection_id,
        geometry_id=selection.geometry_id,
        reconstruction_revision=selection.reconstruction_revision,
        camera_solution_revision=selection.camera_solution_revision,
        corrected_up_direction=(0.0, 1.0, 1.0),
    )
    result = compute_upright_alignment(selection, correction)
    assert result.correction_id == correction.correction_id
    assert result.base_plane_up_direction == pytest.approx((0.0, 0.0, 1.0))
    assert result.source_up_direction == pytest.approx((0.0, 2**-0.5, 2**-0.5))
    assert result.correction_actor_id == "operator-2"
    assert result.correction_evidence_id == "operator-up-direction-1"
    assert result.aligned_up_direction == pytest.approx((0.0, 0.0, 1.0))
    assert result.as_dict()["manual_correction"]


def test_parent_invalidation_and_stale_manual_correction_are_rejected() -> None:
    selection = _selection((0.0, 1.0, 1.0))
    result = compute_upright_alignment(selection)
    result.require_current_selection(selection)
    with pytest.raises(UprightAlignmentError, match="stale_base_plane_selection"):
        result.require_current_selection(
            replace(selection, reconstruction_revision="reconstruction-r2")
        )

    stale_correction = ManualUprightCorrection(
        correction_id="upright-correction-2",
        actor_id="operator-2",
        evidence_id="evidence-2",
        evidence_digest=hashlib.sha256(b"other evidence").hexdigest(),
        reason="stale parent correction",
        base_plane_selection_id=selection.selection_id,
        geometry_id=selection.geometry_id,
        reconstruction_revision="reconstruction-r2",
        camera_solution_revision=selection.camera_solution_revision,
        corrected_up_direction=(0.0, 1.0, 1.0),
    )
    with pytest.raises(UprightAlignmentError, match="manual_correction_parent_revision_mismatch"):
        compute_upright_alignment(selection, stale_correction)


def test_manual_correction_rejects_missing_evidence_provenance() -> None:
    selection = _selection((0.0, 1.0, 1.0))
    with pytest.raises(UprightAlignmentError, match="evidence_digest_invalid"):
        ManualUprightCorrection(
            correction_id="upright-correction-3",
            actor_id="operator-2",
            evidence_id="evidence-3",
            evidence_digest="not-a-digest",
            reason="invalid evidence reference",
            base_plane_selection_id=selection.selection_id,
            geometry_id=selection.geometry_id,
            reconstruction_revision=selection.reconstruction_revision,
            camera_solution_revision=selection.camera_solution_revision,
            corrected_up_direction=(0.0, 1.0, 1.0),
        )
