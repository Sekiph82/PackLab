from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from packlab_core.base_plane import BasePlaneCandidate, BasePlaneSelection
from packlab_core.calibration.reconstruction_scale import ReconstructionScaleEstimate
from packlab_core.front_direction import select_front_direction
from packlab_core.normalization_transform import (
    NormalizationError,
    apply_normalization_transform,
    compose_normalization_transform,
    serialize_normalization_transform,
)
from packlab_core.object_mask_lifting import (
    LiftThresholdProfile,
    LiftVisibilityPolicy,
    ObjectCaptureGeometry,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.upright_alignment import compute_upright_alignment

POINTS = ((1.0, 2.0, 3.0), (4.0, -1.0, 0.5))


def _geometry(points=POINTS):
    geometry_id = hashlib.sha256(
        json.dumps([list(point) for point in points], separators=(",", ":")).encode("ascii")
    ).hexdigest()
    return ObjectCaptureGeometry(
        geometry_id=f"object-geometry:{geometry_id}",
        project_id="synthetic-project",
        source_revision="source-r1",
        source_input_digest=hashlib.sha256(b"synthetic source").hexdigest(),
        source_images=(),
        source_mask_artifacts=(),
        camera_conventions=(),
        camera_evidence=(),
        reconstruction_revision="reconstruction-r1",
        camera_solution_revision="camera-solution-r1",
        mask_set_revision_id="mask-set-r1",
        mask_set_revision_digest=hashlib.sha256(b"synthetic mask").hexdigest(),
        projection_convention="synthetic-test-camera-convention",
        projection_version="test-v1",
        threshold_profile=LiftThresholdProfile(),
        visibility_policy=LiftVisibilityPolicy(),
        outlier_policy="synthetic-test-only",
        candidate_count=len(points),
        point_count=len(points),
        generated=False,
        authority_class="OBJECT_CAPTURE_GEOMETRY",
        scale_state=ScaleState.RELATIVE,
        point_votes=(),
        filtered_points=points,
        unfiltered_points=points,
        obb=None,
        created_at="2026-10-02T00:00:00Z",
    )


def _parents(geometry, normal=(0.0, 1.0, 1.0), direction=(1.0, 0.0, 0.0)):
    points_digest = hashlib.sha256(
        json.dumps(
            [list(point) for point in geometry.filtered_points],
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    selection = BasePlaneSelection(
        "plane-selection-r1",
        "operator_selection",
        None,
        "operator-1",
        "synthetic test selection",
        geometry.geometry_id,
        geometry.reconstruction_revision,
        geometry.camera_solution_revision,
        "reconstruction_units",
        points_digest,
        BasePlaneCandidate(
            "plane-candidate-r1", normal, 0.0, (0, 1), 1.0, 0.0, 0.9, "synthetic test score"
        ),
    )
    upright = compute_upright_alignment(selection)
    front = select_front_direction(
        direction,
        source="operator_selection",
        actor_id="operator-1",
        evidence_id="synthetic-front-selection",
        base_plane_selection_id=selection.selection_id,
        upright_alignment_id=upright.alignment_id,
        geometry_id=geometry.geometry_id,
        reconstruction_revision=geometry.reconstruction_revision,
        camera_solution_revision=geometry.camera_solution_revision,
        coordinate_unit=upright.coordinate_unit,
    )
    estimate = ReconstructionScaleEstimate(
        "estimated",
        0.4,
        0.01,
        "METRIC_UNVERIFIED",
        ("synthetic-observation-1", "synthetic-observation-2"),
        (),
        ({"observation_id": "synthetic-observation-1", "used": True, "relative_residual": 0.0},),
        {
            "math_version": "synthetic-test-scale-v1",
            "input_geometry_unit": "reconstruction_units",
            "output_unit": "mm_per_reconstruction_unit",
            "reconstruction_revision": geometry.reconstruction_revision,
            "camera_solution_revision": geometry.camera_solution_revision,
            "metric_state": "METRIC_UNVERIFIED",
        },
        (),
    )
    return estimate, selection, upright, front


def _compose(geometry=None, *, normal=(0.0, 1.0, 1.0), direction=(1.0, 0.0, 0.0)):
    captured = _geometry() if geometry is None else geometry
    estimate, selection, upright, front = _parents(captured, normal, direction)
    return (
        captured,
        estimate,
        selection,
        upright,
        front,
        compose_normalization_transform(captured, estimate, selection, upright, front),
    )


def _apply(matrix, point):
    return tuple(
        sum(matrix[row * 4 + column] * point[column] for column in range(3)) + matrix[row * 4 + 3]
        for row in range(3)
    )


def test_transform_composes_scale_then_upright_then_front() -> None:
    geometry, estimate, _selection, upright, front, transform = _compose()
    point = geometry.filtered_points[0]
    scaled = tuple(value * estimate.reconstruction_units_to_mm for value in point)
    upright_point = _apply(upright.rotation_matrix, scaled)
    x, y = front.direction[:2]
    magnitude = (x * x + y * y) ** 0.5
    front_matrix = (
        y / magnitude,
        -x / magnitude,
        0.0,
        0.0,
        x / magnitude,
        y / magnitude,
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
    expected = _apply(front_matrix, upright_point)
    assert transform.apply_point(point) == pytest.approx(expected)


def test_identity_scale_upright_and_front_produce_identity_transform() -> None:
    geometry = _geometry(((1.0, 2.0, 3.0),))
    estimate, selection, upright, front = _parents(
        geometry, normal=(0.0, 0.0, 1.0), direction=(0.0, 1.0, 0.0)
    )
    estimate = replace(estimate, reconstruction_units_to_mm=1.0)
    result = compose_normalization_transform(geometry, estimate, selection, upright, front)
    assert result.matrix == pytest.approx(
        (
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
    )


def test_inverse_recovers_points_and_transform_identity_is_deterministic() -> None:
    geometry, estimate, selection, upright, front, first = _compose()
    second = compose_normalization_transform(geometry, estimate, selection, upright, front)
    assert first.transform_id == second.transform_id
    assert serialize_normalization_transform(first) == serialize_normalization_transform(second)
    point = geometry.filtered_points[0]
    assert first.inverse_point(first.apply_point(point)) == pytest.approx(point)


def test_apply_returns_new_view_without_mutating_parent_or_promoting_authority() -> None:
    geometry, _estimate, _selection, _upright, _front, transform = _compose()
    original = geometry.as_dict()
    view = apply_normalization_transform(geometry, transform)
    assert view.filtered_points[0] == pytest.approx(
        transform.apply_point(geometry.filtered_points[0])
    )
    assert view.source_geometry_id == geometry.geometry_id
    assert view.authority_class == "OBJECT_CAPTURE_GEOMETRY"
    assert view.generated is False
    assert view.scale_state is ScaleState.METRIC_UNVERIFIED
    assert view.baked_geometry_created is False
    assert geometry.as_dict() == original
    assert transform.as_dict()["physical_scale_verified"] is False


def test_stale_parent_scale_or_front_and_verified_authority_are_rejected() -> None:
    geometry, estimate, selection, upright, front, _transform = _compose()
    stale_scale = replace(
        estimate,
        provenance={**estimate.provenance, "reconstruction_revision": "reconstruction-old"},
    )
    with pytest.raises(NormalizationError, match="scale_estimate_invalid_or_stale"):
        compose_normalization_transform(geometry, stale_scale, selection, upright, front)
    stale_front = replace(front, reconstruction_revision="reconstruction-old")
    with pytest.raises(NormalizationError, match="front_direction_parent_revision_mismatch"):
        compose_normalization_transform(geometry, estimate, selection, upright, stale_front)
    verified = replace(
        estimate,
        metric_state="METRIC_VERIFIED",
        provenance={**estimate.provenance, "metric_state": "METRIC_VERIFIED"},
    )
    with pytest.raises(NormalizationError, match="scale_estimate_invalid_or_stale"):
        compose_normalization_transform(geometry, verified, selection, upright, front)


def test_normalized_view_rejects_different_geometry_parent() -> None:
    geometry, _estimate, _selection, _upright, _front, transform = _compose()
    other = _geometry(((0.0, 0.0, 0.0),))
    with pytest.raises(NormalizationError, match="stale_geometry_parent"):
        apply_normalization_transform(other, transform)
