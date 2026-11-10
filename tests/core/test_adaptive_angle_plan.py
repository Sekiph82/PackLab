from __future__ import annotations

import pytest

from packlab_core.adaptive_angle_plan import (
    AdaptiveAngleDensityPolicy,
    AdaptiveAnglePlanError,
    AngularComplexityEvidence,
    plan_adaptive_angles,
)


def _sectors():
    return (
        AngularComplexityEvidence("sector-a", 0.0, 180.0, 0.0, "1" * 64),
        AngularComplexityEvidence("sector-b", 180.0, 360.0, 1.0, "2" * 64),
    )


def test_complexity_scores_allocate_bounded_deterministic_planned_angles() -> None:
    first = plan_adaptive_angles("geometry-r1", "a" * 64, _sectors())
    second = plan_adaptive_angles("geometry-r1", "a" * 64, _sectors())

    assert first == second
    assert first.plan_id == second.plan_id
    assert len(first.angles) == 5
    assert [item.sector_id for item in first.angles] == [
        "sector-a",
        "sector-b",
        "sector-b",
        "sector-b",
        "sector-b",
    ]
    assert [item.angle_degrees for item in first.angles] == [90.0, 202.5, 247.5, 292.5, 337.5]
    assert len({item.angle_degrees for item in first.angles}) == 5
    payload = first.as_dict()
    assert payload["complexity_source"] == "CALLER_SUPPLIED_UNTRUSTED_NORMALIZED_SCORE"
    assert all(item["angle_status"] == "PLANNED_NOT_OBSERVED" for item in payload["angles"])
    assert payload["hardware_control_performed"] is False
    assert payload["capture_performed"] is False


def test_sector_partition_must_cover_full_turn_without_gaps_or_overlap() -> None:
    gap = (
        AngularComplexityEvidence("sector-a", 0.0, 170.0, 0.0, "1" * 64),
        AngularComplexityEvidence("sector-b", 180.0, 360.0, 1.0, "2" * 64),
    )
    with pytest.raises(AdaptiveAnglePlanError, match="sector_coverage_gap_or_overlap"):
        plan_adaptive_angles("geometry-r1", "a" * 64, gap)


def test_policy_and_total_angle_limits_reject_oversized_plan() -> None:
    with pytest.raises(AdaptiveAnglePlanError, match="planned_angle_count_exceeds_limit"):
        plan_adaptive_angles(
            "geometry-r1",
            "a" * 64,
            _sectors(),
            policy=AdaptiveAngleDensityPolicy(
                minimum_angles_per_sector=1,
                maximum_angles_per_sector=4,
                maximum_total_angles=4,
            ),
        )

    with pytest.raises(AdaptiveAnglePlanError, match="policy_exceeds_hard_limit"):
        AdaptiveAngleDensityPolicy(maximum_total_angles=513)


def test_complexity_values_and_source_digests_are_validated() -> None:
    with pytest.raises(AdaptiveAnglePlanError, match="normalized_complexity_out_of_range"):
        AngularComplexityEvidence("sector-a", 0.0, 360.0, 1.1, "1" * 64)
    with pytest.raises(AdaptiveAnglePlanError, match="evidence_sha256_invalid"):
        AngularComplexityEvidence("sector-a", 0.0, 360.0, 0.5, "not-a-digest")


def test_too_narrow_sector_fails_instead_of_duplicating_boundary_angles() -> None:
    # Review P2-1: a 1e-12 degree sector produced [0.0, 0.0, 0.0, 0.0, ...].
    sectors = (
        AngularComplexityEvidence("sector-a", 0.0, 1e-12, 1.0, "1" * 64),
        AngularComplexityEvidence("sector-b", 1e-12, 360.0, 0.0, "2" * 64),
    )
    with pytest.raises(AdaptiveAnglePlanError, match="sector_too_narrow_for_planned_angles"):
        plan_adaptive_angles("geometry-r1", "a" * 64, sectors)


def test_plan_identity_binds_the_geometry_digest_and_rejects_bad_digests() -> None:
    first = plan_adaptive_angles("geometry-r1", "a" * 64, _sectors())
    other = plan_adaptive_angles("geometry-r1", "b" * 64, _sectors())
    assert first.plan_id != other.plan_id
    assert other.as_dict()["geometry_sha256"] == "b" * 64
    for bad in ("A" * 64, "a" * 63, "path/to/geometry"):
        with pytest.raises(AdaptiveAnglePlanError, match="geometry_sha256_invalid"):
            plan_adaptive_angles("geometry-r1", bad, _sectors())


@pytest.mark.parametrize(
    "sectors",
    [
        (AngularComplexityEvidence("only", 10.0, 360.0, 0.5, "1" * 64),),
        (AngularComplexityEvidence("only", 0.0, 350.0, 0.5, "1" * 64),),
        (
            AngularComplexityEvidence("same", 0.0, 180.0, 0.5, "1" * 64),
            AngularComplexityEvidence("same", 180.0, 360.0, 0.5, "2" * 64),
        ),
    ],
)
def test_coverage_and_duplicate_sector_ids_are_rejected(sectors) -> None:
    with pytest.raises(AdaptiveAnglePlanError, match="coverage|duplicate"):
        plan_adaptive_angles("geometry-r1", "a" * 64, sectors)


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0.0, 1), (0.16, 1), (0.17, 2), (0.5, 3), (0.83, 3), (0.84, 4), (1.0, 4)],
)
def test_score_to_count_rounding_is_pinned(score: float, expected: int) -> None:
    # Default policy: count = 1 + floor(score * 3 + 0.5).
    sectors = (AngularComplexityEvidence("all", 0.0, 360.0, score, "1" * 64),)
    assert len(plan_adaptive_angles("geometry-r1", "a" * 64, sectors).angles) == expected
