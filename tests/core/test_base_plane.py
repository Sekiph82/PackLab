from __future__ import annotations

import hashlib
from dataclasses import replace
from types import SimpleNamespace

import pytest

from packlab_core.base_plane import (
    BasePlaneError,
    BasePlaneOverride,
    BasePlaneOverrideError,
    BasePlaneProfile,
    apply_base_plane_override,
    detect_base_plane_candidates,
)
from packlab_core.coordinate_frame import coordinate_unit_for_scale_state
from packlab_core.object_mask_lifting import (
    LiftThresholdProfile,
    LiftVisibilityPolicy,
    ObjectCaptureGeometry,
)
from packlab_core.reconstruction import ScaleState


def _geometry(points: tuple[tuple[float, float, float], ...]):
    digest = hashlib.sha256(repr(points).encode()).hexdigest()
    return ObjectCaptureGeometry(
        geometry_id=f"synthetic-object-geometry:{digest}",
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
        mask_set_revision_digest=hashlib.sha256(b"synthetic mask set").hexdigest(),
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


def _grid(z: float, *, size: int = 3, jitter: tuple[float, ...] | None = None):
    values = []
    for row in range(size):
        for column in range(size):
            index = row * size + column
            noise = 0.0 if jitter is None else jitter[index]
            values.append((float(column), float(row), z + noise))
    return tuple(values)


def test_flat_synthetic_base_returns_candidate_with_bound_evidence() -> None:
    points = _grid(2.0) + ((8.0, 8.0, 4.0),)
    geometry = _geometry(points)
    result = detect_base_plane_candidates(
        geometry,
        BasePlaneProfile(minimum_inliers=8, minimum_inlier_ratio=0.75),
    )
    assert result.status == "candidate"
    candidate = result.candidates[0]
    assert len(candidate.inlier_indices) == 9
    assert candidate.normal == pytest.approx((0.0, 0.0, 1.0))
    assert candidate.offset == pytest.approx(-2.0)
    assert candidate.confidence_semantics.endswith("not_probability_or_accuracy")
    assert result.geometry_id == geometry.geometry_id
    assert result.reconstruction_revision == geometry.reconstruction_revision
    assert result.coordinate_unit == "reconstruction_units"


def test_noisy_outlier_cloud_uses_deterministic_bounded_robust_policy() -> None:
    jitter = (0.001, -0.002, 0.003, -0.001, 0.0, 0.002, -0.003, 0.001, 0.0)
    points = _grid(1.5, jitter=jitter) + ((8.0, 9.0, 5.0), (-4.0, 7.0, -3.0))
    geometry = _geometry(points)
    profile = BasePlaneProfile(
        distance_tolerance=0.01,
        minimum_inliers=8,
        minimum_inlier_ratio=0.75,
        maximum_hypotheses=200,
    )
    first = detect_base_plane_candidates(geometry, profile)
    second = detect_base_plane_candidates(geometry, profile)
    assert first.as_dict() == second.as_dict()
    assert first.status == "candidate"
    assert first.hypotheses_evaluated <= profile.maximum_hypotheses
    assert len(first.candidates[0].inlier_indices) == 9


def test_two_similarly_supported_planes_are_reported_as_ambiguous() -> None:
    horizontal = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0))
    vertical = ((5.0, 0.0, 2.0), (5.0, 1.0, 2.0), (5.0, 0.0, 3.0), (5.0, 1.0, 3.0))
    result = detect_base_plane_candidates(
        _geometry(horizontal + vertical),
        BasePlaneProfile(
            distance_tolerance=0.001,
            minimum_inliers=4,
            minimum_inlier_ratio=0.49,
            maximum_hypotheses=512,
        ),
    )
    assert result.status == "ambiguous"
    assert len(result.candidates) >= 2
    assert result.errors == ("multiple_similarly_supported_planes_require_user_selection",)


def test_no_plane_and_inclusive_distance_threshold() -> None:
    scattered = tuple((float(i), float((i * 7) % 5), float((i * 11) % 13)) for i in range(12))
    no_plane = detect_base_plane_candidates(
        _geometry(scattered),
        BasePlaneProfile(minimum_inliers=8, minimum_inlier_ratio=0.5, maximum_hypotheses=256),
    )
    assert no_plane.status == "no_plane"

    boundary = _grid(0.0) + ((1.0, 1.0, 0.1),)
    included = detect_base_plane_candidates(
        _geometry(boundary),
        BasePlaneProfile(
            distance_tolerance=0.1,
            minimum_inliers=9,
            minimum_inlier_ratio=0.9,
            maximum_hypotheses=256,
        ),
    )
    assert included.status == "candidate"
    assert len(included.candidates[0].inlier_indices) == 10


def test_manual_override_is_versioned_bound_and_does_not_mutate_source() -> None:
    points = _grid(2.0)
    geometry = _geometry(points)
    before = geometry.filtered_points
    override = BasePlaneOverride(
        override_id="override-1",
        actor_id="operator-1",
        reason="selected the photographed container base",
        geometry_id=geometry.geometry_id,
        reconstruction_revision=geometry.reconstruction_revision,
        camera_solution_revision=geometry.camera_solution_revision,
        normal=(0.0, 0.0, 2.0),
        offset=-4.0,
        evidence_point_indices=(0, 1, 3, 4),
    )
    selection = apply_base_plane_override(geometry, override)
    assert selection.selection_method == "manual_override"
    assert selection.override_version == "captured_geometry_base_plane_override_v1"
    assert selection.actor_id == "operator-1"
    assert selection.candidate.normal == pytest.approx((0.0, 0.0, 1.0))
    assert selection.coordinate_unit == coordinate_unit_for_scale_state(ScaleState.RELATIVE)
    assert geometry.filtered_points == before
    selection.require_current_geometry(geometry)


def test_manual_override_rejects_unsupported_plane_and_stale_parent() -> None:
    geometry = _geometry(_grid(2.0))
    base = BasePlaneOverride(
        "override-2",
        "operator-1",
        "wrong plane",
        geometry.geometry_id,
        geometry.reconstruction_revision,
        geometry.camera_solution_revision,
        (0.0, 0.0, 1.0),
        -3.0,
        (0, 1, 3),
    )
    with pytest.raises(BasePlaneOverrideError, match="not_supported"):
        apply_base_plane_override(geometry, base)

    good = replace(base, reason="base selection", offset=-2.0)
    selection = apply_base_plane_override(geometry, good)
    stale = replace(geometry, reconstruction_revision="reconstruction-r-next")
    with pytest.raises(BasePlaneError, match="stale_parent_geometry"):
        selection.require_current_geometry(stale)


def test_generated_geometry_is_not_an_authoritative_base_plane_input() -> None:
    with pytest.raises(BasePlaneError, match="non_generated_object_capture_geometry"):
        detect_base_plane_candidates(
            SimpleNamespace(authority_class="AI_VISUAL_REFERENCE", generated=True)
        )  # type: ignore[arg-type]
