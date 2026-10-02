from __future__ import annotations

import math
from dataclasses import replace

import pytest

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.cross_section_measurement import (
    CrossSectionSelection,
    measure_cross_section,
)
from packlab_core.horizontal_section import extract_horizontal_section
from packlab_core.neck_finish_candidates import (
    NeckFinishCandidateError,
    NeckFinishPolicy,
    NeckSectionEvidence,
    measure_neck_finish_candidates,
    serialize_neck_finish_candidates,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.vertical_profile import extract_vertical_profile


def _fixture(radii, *, state=ScaleState.RELATIVE, policy=None):
    point_list = []
    indices_by_ring = []
    for z, radius in enumerate(radii):
        ring_indices = []
        for index in range(32):
            angle = 2.0 * math.pi * index / 32
            ring_indices.append(len(point_list))
            point_list.append((radius * math.cos(angle), radius * math.sin(angle), float(z)))
        indices_by_ring.append(tuple(ring_indices))
    metric = state is not ScaleState.RELATIVE
    geometry = NormalizedMeasurementGeometry(
        "normalized-r1",
        "geometry-r1",
        tuple(point_list),
        state,
        "mm_unverified" if metric else "reconstruction_units",
        "scale-r1" if metric else None,
        0.02 if metric else None,
        "mm_per_reconstruction_unit" if metric else None,
    )
    profile = extract_vertical_profile(
        geometry,
        plane_origin=(0.0, 0.0, 0.0),
        horizontal_direction=(1.0, 0.0, 0.0),
        lateral_tolerance=0.21,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )
    evidence = []
    for z, indices in enumerate(indices_by_ring):
        section = extract_horizontal_section(
            geometry,
            float(z),
            slab_half_width=0.0,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id=geometry.scale_provenance_id,
        )
        selection = CrossSectionSelection(
            f"selection-z{z}",
            geometry.source_geometry_id,
            geometry.normalized_geometry_revision,
            indices,
            (0.0, 0.0, float(z)),
            (0.0, 0.0, 1.0),
            1e-9,
        )
        measurement = measure_cross_section(
            geometry,
            selection,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id=geometry.scale_provenance_id,
        )
        evidence.append(NeckSectionEvidence(section, measurement))
    result = measure_neck_finish_candidates(
        geometry,
        tuple(evidence),
        profile,
        policy=policy or NeckFinishPolicy(),
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )
    return geometry, tuple(evidence), profile, result


def test_synthetic_bottle_yields_neck_and_finish_candidates_without_classification() -> None:
    geometry, _, _, result = _fixture((5.0, 5.0, 2.0, 2.0, 1.0, 1.0))
    assert len(result.candidates) == 2
    assert result.candidates[0].section_z_range == (4.0, 5.0)
    assert result.candidates[0].major_radius == pytest.approx(1.0)
    assert result.candidates[0].major_diameter == pytest.approx(2.0)
    assert result.candidates[0].height == 1.0
    assert all(item.candidate_type == "NARROW_REGION_CANDIDATE" for item in result.candidates)
    assert all(
        item.review_required and item.ambiguity_review_required for item in result.candidates
    )
    payload = result.as_dict()
    assert payload["thread_standard_inferred"] is False
    assert payload["closure_spec_inferred"] is False
    assert payload["mold_ready_dimensions_claimed"] is False
    assert geometry.authority_class == "OBJECT_CAPTURE_GEOMETRY"


def test_candidate_reduction_threshold_is_inclusive() -> None:
    _, _, _, result = _fixture(
        (10.0, 10.0, 8.0, 8.0),
        policy=NeckFinishPolicy(minimum_relative_radius_reduction=0.2),
    )
    assert len(result.candidates) == 1
    assert result.candidates[0].relative_radius_reduction == pytest.approx(0.2)


def test_deterministic_ranking_and_candidate_serialization() -> None:
    geometry, evidence, profile, first = _fixture((5.0, 5.0, 2.0, 2.0, 1.0, 1.0))
    second = measure_neck_finish_candidates(
        geometry,
        tuple(reversed(evidence)),
        profile,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=geometry.scale_provenance_id,
    )
    assert first.result_id == second.result_id
    assert serialize_neck_finish_candidates(first) == serialize_neck_finish_candidates(second)
    assert [item.rank for item in first.candidates] == [1, 2]
    assert (
        first.candidates[0].relative_radius_reduction
        > first.candidates[1].relative_radius_reduction
    )


def test_insufficient_section_evidence_is_rejected() -> None:
    geometry, evidence, profile, _ = _fixture((5.0, 2.0, 1.0))
    with pytest.raises(NeckFinishCandidateError, match="insufficient_section_evidence"):
        measure_neck_finish_candidates(
            geometry,
            evidence[:2],
            profile,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id=geometry.scale_provenance_id,
        )


@pytest.mark.parametrize(
    ("state", "unit"),
    [
        (ScaleState.RELATIVE, "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ],
)
def test_candidates_preserve_scale_state_and_units(state, unit) -> None:
    _, _, _, result = _fixture((5.0, 5.0, 2.0, 2.0), state=state)
    assert result.scale_state is state
    assert result.coordinate_unit == unit
    assert result.candidates[0].coordinate_unit == unit


def test_provenance_mismatch_in_profile_or_sections_is_rejected() -> None:
    geometry, evidence, profile, _ = _fixture(
        (5.0, 5.0, 2.0, 2.0), state=ScaleState.METRIC_UNVERIFIED
    )
    stale_profile = replace(profile, scale_provenance_id="scale-r2")
    with pytest.raises(NeckFinishCandidateError, match="vertical_profile_provenance_mismatch"):
        measure_neck_finish_candidates(
            geometry,
            evidence,
            stale_profile,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id=geometry.scale_provenance_id,
        )

    bad_measurement = replace(
        evidence[0].cross_section_measurement,
        scale_provenance_id="scale-r2",
    )
    bad_evidence = (
        replace(evidence[0], cross_section_measurement=bad_measurement),
        *evidence[1:],
    )
    with pytest.raises(NeckFinishCandidateError, match="cross_section_provenance_mismatch"):
        measure_neck_finish_candidates(
            geometry,
            tuple(bad_evidence),
            profile,
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id=geometry.scale_provenance_id,
        )
