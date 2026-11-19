"""PL-0221 threshold derivation. Synthetic fixtures check the math only; no physical PASS."""

from __future__ import annotations

import math
import statistics
from dataclasses import replace

import pytest
from tests.core.threshold_fixtures import benchmark_fixture as _fixture
from tests.core.threshold_fixtures import owner_acceptance as _acceptance

from packlab_core import acceptance_thresholds as at
from packlab_core.acceptance_thresholds import (
    AcceptanceThresholdError,
    OwnerThresholdAcceptance,
    accept_threshold_proposal,
    derive_test_only_threshold_proposal,
    derive_threshold_proposal,
    proposal_digest_valid,
    tolerance_factor,
)
from packlab_core.physical_accuracy_benchmark import blank_physical_benchmark_record
from packlab_core.reconstruction import ScaleState


@pytest.mark.parametrize(("n", "tabulated"), [(10, 3.379), (30, 2.549), (100, 2.233)])
def test_tolerance_factor_matches_published_two_sided_95_95_table(n: int, tabulated: float) -> None:
    # Wilson-Hilferty is slightly conservative: never below the exact table, within 0.01.
    assert tabulated - 1e-3 <= tolerance_factor(n) <= tabulated + 0.01


@pytest.mark.parametrize("n", [1, 2, 9, True])
def test_tolerance_factor_refuses_small_n(n: int) -> None:
    with pytest.raises(AcceptanceThresholdError, match="minimum_samples"):
        tolerance_factor(n)


def test_test_only_path_computes_documented_rule_and_cannot_claim_physical() -> None:
    record, observations = _fixture()
    proposal = derive_test_only_threshold_proposal([record], observations)
    assert proposal["status"] == at.TEST_ONLY
    assert proposal["simulation_only"] is True
    assert proposal["mold_use_authorized"] is False
    assert proposal["physical_validation_status"] == "PHYSICAL_EVIDENCE_PENDING"
    assert proposal_digest_valid(proposal)
    assert proposal == derive_test_only_threshold_proposal([record], list(reversed(observations)))
    truths = {s.sample_id: s.ground_truth.value_mm for s in record.samples if s.ground_truth}
    groups = proposal["groups"]
    assert isinstance(groups, list) and len(groups) == 3
    for group in groups:
        errors = [
            o.measured_value_mm - truths[o.sample_id]
            for o in observations
            if o.sample_id.startswith(f"SAMPLE-{group['category'].upper()}")
        ]
        bound = abs(statistics.fmean(errors)) + tolerance_factor(10) * statistics.stdev(errors)
        expected = math.ceil(max(bound, max(map(abs, errors)), 0.04) * 100 - 1e-9) / 100
        assert group["status"] == "THRESHOLD_PROPOSED"
        assert group["proposed_tolerance_mm"] == expected
        assert group["proposed_tolerance_mm"] >= group["max_abs_error_mm"]


def test_physical_path_refuses_synthetic_and_simulation_labels() -> None:
    for kind in ("SYNTHETIC", "SIMULATION_ONLY", "PUBLIC_PROXY"):
        record, observations = _fixture(evidence_kind=kind, scale_state=ScaleState.METRIC_VERIFIED)
        with pytest.raises(AcceptanceThresholdError, match="synthetic_or_simulation_input_refused"):
            derive_threshold_proposal([record], observations)


def test_physical_path_requires_metric_verified_scale() -> None:
    record, observations = _fixture(evidence_kind="OWNER_EXECUTED_PHYSICAL")
    with pytest.raises(AcceptanceThresholdError, match="scale_not_metric_verified"):
        derive_threshold_proposal([record], observations)


def test_too_few_samples_refused_and_small_groups_get_no_threshold() -> None:
    record, observations = _fixture(per_category=9)
    with pytest.raises(AcceptanceThresholdError, match="insufficient_samples_for_required"):
        derive_test_only_threshold_proposal([record], observations)
    record, observations = _fixture()
    observations[0] = replace(observations[0], dimension_kind="neck_finish_thread_diameter_t")
    # The matte overall-dimension group now has 9 samples: below the minimum.
    with pytest.raises(AcceptanceThresholdError, match="insufficient_samples_for_required"):
        derive_test_only_threshold_proposal([record], observations)


def test_small_feature_group_reported_insufficient_without_threshold() -> None:
    record, observations = _fixture(per_category=12)
    observations[0] = replace(observations[0], dimension_kind="wall_thickness")
    proposal = derive_test_only_threshold_proposal([record], observations)
    wall = [g for g in proposal["groups"] if g["feature_group"] == "wall_and_feature"]
    assert wall == [
        {
            "category": "matte_bottle",
            "material": "HDPE",
            "feature_group": "wall_and_feature",
            "sample_count": 1,
            "status": "INSUFFICIENT_SAMPLES",
            "proposed_tolerance_mm": None,
        }
    ]


def test_owner_required_record_and_unpaired_or_mislinked_samples_refused() -> None:
    record, observations = _fixture()
    with pytest.raises(AcceptanceThresholdError, match="not_ready_for_audit"):
        derive_test_only_threshold_proposal([blank_physical_benchmark_record()], observations)
    with pytest.raises(AcceptanceThresholdError, match="accepted_sample_without_observation"):
        derive_test_only_threshold_proposal([record], observations[1:])
    bad = [replace(observations[0], measurement_revision_id="meas-rev-2"), *observations[1:]]
    with pytest.raises(AcceptanceThresholdError, match="link_mismatch"):
        derive_test_only_threshold_proposal([record], bad)
    stray = [*observations, replace(observations[0], sample_id="SAMPLE-UNKNOWN")]
    with pytest.raises(AcceptanceThresholdError, match="observation_without_benchmark_sample"):
        derive_test_only_threshold_proposal([record], stray)


def test_acceptance_blocked_today_while_pl0220_deferred() -> None:
    record, observations = _fixture(
        evidence_kind="OWNER_EXECUTED_PHYSICAL", scale_state=ScaleState.METRIC_VERIFIED
    )
    proposal = derive_threshold_proposal([record], observations)
    assert proposal["status"] == at.PROPOSED and proposal["simulation_only"] is False
    with pytest.raises(AcceptanceThresholdError, match="pl0220_physical_benchmark_deferred"):
        accept_threshold_proposal([record], observations, proposal, _acceptance(proposal))


def test_acceptance_mechanics_with_gate_lifted_in_test_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mechanics only: the gate is lifted by monkeypatch and inputs are forged-label fixtures."""

    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", "OWNER_BENCHMARK_EVIDENCE_ACCEPTED")
    record, synthetic = _fixture()
    test_only = derive_test_only_threshold_proposal([record], synthetic)
    with pytest.raises(AcceptanceThresholdError, match="proposal_not_acceptable"):
        accept_threshold_proposal([record], synthetic, test_only, _acceptance(test_only))
    record, observations = _fixture(
        evidence_kind="OWNER_EXECUTED_PHYSICAL", scale_state=ScaleState.METRIC_VERIFIED
    )
    proposal = derive_threshold_proposal([record], observations)
    # A synthetic set relabelled after derivation cannot ride on a physical proposal.
    with pytest.raises(AcceptanceThresholdError, match="synthetic_or_simulation_input_refused"):
        accept_threshold_proposal([record], synthetic, proposal, _acceptance(proposal))
    tampered = dict(proposal, rule={"rule_id": "loose"})
    tampered["proposal_sha256"] = at._digest(
        {k: v for k, v in tampered.items() if k != "proposal_sha256"}
    )
    with pytest.raises(AcceptanceThresholdError, match="does_not_match_physical_inputs"):
        accept_threshold_proposal([record], observations, tampered, _acceptance(tampered))
    with pytest.raises(AcceptanceThresholdError, match="bound_to_different_proposal"):
        accept_threshold_proposal(
            [record],
            observations,
            proposal,
            replace(_acceptance(proposal), proposal_sha256="0" * 64),
        )
    accepted = accept_threshold_proposal([record], observations, proposal, _acceptance(proposal))
    assert accepted["status"] == at.ACCEPTED and accepted["mold_use_authorized"] is False
    assert at.accepted_thresholds_digest_valid(accepted)


def test_owner_acceptance_record_requires_actor_timestamp_and_reason() -> None:
    with pytest.raises(AcceptanceThresholdError, match="actor_reference_invalid"):
        OwnerThresholdAcceptance("a" * 64, "Owner Name", "2026-11-19T00:00:00Z", "ok")
    with pytest.raises(AcceptanceThresholdError, match="timestamp_invalid"):
        OwnerThresholdAcceptance("a" * 64, "ref:owner", "2026-11-19", "ok")
    with pytest.raises(AcceptanceThresholdError, match="reason_required"):
        OwnerThresholdAcceptance("a" * 64, "ref:owner", "2026-11-19T00:00:00Z", " ")


def test_each_rule_term_can_dominate() -> None:
    """Kills rule mutants: max|e| term, caliper floor (factor 2) and abs(mean) of a negative bias."""

    errors = {
        # n=20 with one outlier: max|e| = 1.0 beats |mean| + k*s ~ 0.67.
        "matte_bottle": [0.0] * 19 + [1.0],
        # Tiny errors with caliper u = 0.5 mm: floor 2 * 0.5 = 1.0 dominates.
        "glossy_bottle": [0.01 * (-1) ** i for i in range(10)],
        # Negative bias: |mean| + k*s = 0.5 + 3.387 * 0.0527 ~ 0.68 beats max|e| = 0.55.
        "jerrycan": [-0.5 + 0.05 * (-1) ** i for i in range(10)],
    }
    record, observations = _fixture(errors=errors, uncertainty_mm={"glossy_bottle": 0.5})
    proposal = derive_test_only_threshold_proposal([record], observations)
    by_category = {g["category"]: g for g in proposal["groups"]}
    matte, glossy, jerrycan = (
        by_category[c] for c in ("matte_bottle", "glossy_bottle", "jerrycan")
    )
    assert matte["tolerance_bound_mm"] < 0.7 and matte["proposed_tolerance_mm"] == 1.0
    assert glossy["caliper_floor_mm"] == 1.0 and glossy["proposed_tolerance_mm"] == 1.0
    assert jerrycan["mean_error_mm"] == pytest.approx(-0.5)
    expected = 0.5 + tolerance_factor(10) * statistics.stdev(errors["jerrycan"])
    assert jerrycan["proposed_tolerance_mm"] == math.ceil(expected * 100 - 1e-9) / 100 == 0.68


def test_observation_for_rejected_sample_and_duplicate_observation_refused() -> None:
    record, observations = _fixture()
    base = record.samples[0]
    rejected = replace(
        base, sample_id="SAMPLE-REJECTED-1", disposition="REJECTED", disposition_reason="blurred"
    )
    with_rejected = replace(record, samples=(*record.samples, rejected))
    extra = replace(observations[0], sample_id="SAMPLE-REJECTED-1")
    with pytest.raises(AcceptanceThresholdError, match="observation_sample_not_accepted"):
        derive_test_only_threshold_proposal([with_rejected], [*observations, extra])
    with pytest.raises(AcceptanceThresholdError, match="duplicate_observation_for_sample"):
        derive_test_only_threshold_proposal([record], [*observations, observations[0]])
