from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest
from test_design_history import _model

from packlab_core.design_model import revise_design_model_revision
from packlab_core.dimension_fit_proposal import (
    BoundedGridFitOptimizer,
    DimensionFitCandidate,
    DimensionFitOptimizationRequest,
    DimensionFitOptimizerBackend,
    DimensionFitProposal,
    DimensionFitProposalError,
    DimensionFitProposalProvenance,
    MeasuredParameterConstraint,
    NumericParameterValue,
    accept_dimension_fit_proposal,
    create_dimension_fit_request,
)


def _scenario():
    model = _model()
    constraints = tuple(
        sorted(
            (
                MeasuredParameterConstraint(
                    "height",
                    "measure-height-1",
                    "1" * 64,
                    102.0,
                    5.0,
                    "mm_unverified",
                    "owner-1",
                    "2026-10-22T19:00:00Z",
                ),
                MeasuredParameterConstraint(
                    "width",
                    "measure-width-1",
                    "2" * 64,
                    31.0,
                    3.0,
                    "mm_unverified",
                    "owner-1",
                    "2026-10-22T19:00:00Z",
                ),
            ),
            key=lambda item: item.parameter_id,
        )
    )
    request = create_dimension_fit_request(
        model,
        deviation_evidence_sha256="3" * 64,
        maximum_deviation=0.5,
        constraints=constraints,
    )
    proposal = DimensionFitProposal(
        "fit-proposal-1",
        request,
        (
            DimensionFitCandidate(
                "candidate-1",
                (NumericParameterValue("height", 103.0), NumericParameterValue("width", 32.0)),
                0.3,
                "4" * 64,
            ),
            DimensionFitCandidate(
                "candidate-2",
                (NumericParameterValue("height", 100.0), NumericParameterValue("width", 30.0)),
                0.4,
                "5" * 64,
            ),
        ),
        DimensionFitProposalProvenance("fake-optimizer", "fake-model", "not-selected", "test-v1"),
    )
    return model, proposal


def test_fake_optimizer_proposal_is_non_authoritative_and_does_not_mutate_model() -> None:
    model, proposal = _scenario()

    class FakeOptimizer:
        def optimize(self, request):
            assert request.model_revision_id == model.revision_id
            return proposal

    backend: DimensionFitOptimizerBackend = FakeOptimizer()
    result = backend.optimize(proposal.request)
    payload = result.as_dict()

    assert isinstance(backend, DimensionFitOptimizerBackend)
    assert payload["authority_class"] == "AI_DIMENSION_FIT_PROPOSAL"
    assert payload["generated"] is True and payload["accepted"] is False
    assert payload["model_mutated"] is False
    assert payload["mold_use_authorized"] is False
    assert "path" not in json.dumps(payload) and "raw_geometry" not in payload
    assert model.revision_id == proposal.request.model_revision_id


def test_measurement_constraints_require_positive_tolerance_and_canonical_order() -> None:
    model, proposal = _scenario()
    constraint = proposal.request.constraints[0]
    with pytest.raises(DimensionFitProposalError, match="measurement_tolerance_must_be_positive"):
        MeasuredParameterConstraint(
            constraint.parameter_id,
            constraint.measurement_id,
            constraint.measurement_sha256,
            constraint.target_value,
            0.0,
            constraint.unit,
            constraint.actor_id,
            constraint.measured_at_utc,
        )

    with pytest.raises(DimensionFitProposalError, match="measured_constraints_not_canonical"):
        create_dimension_fit_request(
            model,
            deviation_evidence_sha256="3" * 64,
            maximum_deviation=0.5,
            constraints=tuple(reversed(proposal.request.constraints)),
        )


def test_acceptance_creates_immutable_deferred_successor_and_bound_record() -> None:
    model, proposal = _scenario()
    accepted = accept_dimension_fit_proposal(
        model,
        proposal,
        request=proposal.request,
        candidate_id="candidate-1",
        actor_id="owner-1",
        reason="I reviewed the bounded dimension proposal.",
        created_at_utc="2026-10-22T19:05:00Z",
    )

    values = {item.parameter_id: item.value for item in accepted.model.parameters}
    original_values = {item.parameter_id: item.value for item in model.parameters}
    assert values["height"] == 103.0 and values["width"] == 32.0
    assert model.revision_id != accepted.model.revision_id
    assert original_values["height"] == 100.0 and original_values["width"] == 30.0
    assert accepted.model.previous_revision_id == model.revision_id
    assert (
        accepted.model.fitted_to_scan_master_revision_id == model.fitted_to_scan_master_revision_id
    )
    assert accepted.model.scan_master_geometry_sha256 == model.scan_master_geometry_sha256
    assert accepted.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert accepted.model.mold_use_authorized is False
    record = accepted.acceptance.as_dict()
    assert record["source_model_revision_id"] == model.revision_id
    assert record["accepted_model_revision_id"] == accepted.model.revision_id
    assert record["proposal_sha256"] == proposal.digest


def test_acceptance_rejects_stale_model_unknown_candidate_bounds_and_deviation_budget() -> None:
    model, proposal = _scenario()
    changed = revise_design_model_revision(
        model,
        parameters=model.parameters,
        features=model.features,
        actor_id="owner-1",
        reason="Create a newer model revision.",
        created_at_utc="2026-10-22T19:01:00Z",
    )
    with pytest.raises(DimensionFitProposalError, match="proposal_source_revision_stale"):
        accept_dimension_fit_proposal(
            changed,
            proposal,
            request=proposal.request,
            candidate_id="candidate-1",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T19:05:00Z",
        )
    with pytest.raises(DimensionFitProposalError, match="candidate_not_in_proposal"):
        accept_dimension_fit_proposal(
            model,
            proposal,
            request=proposal.request,
            candidate_id="missing",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T19:05:00Z",
        )

    candidate = proposal.candidates[0]
    outside = replace(
        proposal,
        candidates=(
            replace(
                candidate,
                parameter_values=(
                    NumericParameterValue("height", 120.0),
                    NumericParameterValue("width", 32.0),
                ),
            ),
        ),
    )
    with pytest.raises(
        DimensionFitProposalError, match="candidate_outside_measured_dimension_tolerance"
    ):
        accept_dimension_fit_proposal(
            model,
            outside,
            request=proposal.request,
            candidate_id="candidate-1",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T19:05:00Z",
        )

    over_budget = replace(
        proposal,
        candidates=(replace(candidate, estimated_maximum_deviation=0.8),),
    )
    with pytest.raises(DimensionFitProposalError, match="candidate_exceeds_deviation_budget"):
        accept_dimension_fit_proposal(
            model,
            over_budget,
            request=proposal.request,
            candidate_id="candidate-1",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T19:05:00Z",
        )


@pytest.mark.parametrize(
    "tamper",
    [
        lambda c: replace(c, tolerance=95.0),  # backend widens the measured tolerance
        lambda c: replace(c, target_value=3.0, tolerance=2.9),  # backend moves the target
    ],
)
def test_backend_echoing_a_widened_request_cannot_be_accepted(tamper) -> None:
    # Review F-1 (P1): acceptance must use the user's request, not the backend's echo.
    model, proposal = _scenario()
    user_request = proposal.request
    widened = replace(
        user_request,
        constraints=(tamper(user_request.constraints[0]), *user_request.constraints[1:]),
    )
    rogue = replace(
        proposal,
        request=widened,
        candidates=(
            replace(
                proposal.candidates[0],
                parameter_values=(
                    NumericParameterValue("height", 3.0),
                    NumericParameterValue("width", 32.0),
                ),
            ),
        ),
    )
    with pytest.raises(DimensionFitProposalError, match="proposal_request_mismatch"):
        accept_dimension_fit_proposal(
            model,
            rogue,
            request=user_request,
            candidate_id="candidate-1",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T19:05:00Z",
        )


@pytest.mark.parametrize(
    "field_value",
    [("maximum_deviation", 50.0), ("deviation_evidence_sha256", "9" * 64)],
)
def test_backend_cannot_swap_deviation_budget_or_evidence(field_value) -> None:
    model, proposal = _scenario()
    field, value = field_value
    rogue = replace(proposal, request=replace(proposal.request, **{field: value}))
    with pytest.raises(DimensionFitProposalError, match="proposal_request_mismatch"):
        accept_dimension_fit_proposal(
            model,
            rogue,
            request=proposal.request,
            candidate_id="candidate-1",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T19:05:00Z",
        )


def test_candidate_must_cover_exactly_the_constrained_parameters() -> None:
    model, proposal = _scenario()
    partial = replace(
        proposal,
        candidates=(
            replace(
                proposal.candidates[0],
                parameter_values=(NumericParameterValue("height", 103.0),),
            ),
        ),
    )
    with pytest.raises(DimensionFitProposalError, match="candidate_constraint_set_mismatch"):
        accept_dimension_fit_proposal(
            model,
            partial,
            request=proposal.request,
            candidate_id="candidate-1",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T19:05:00Z",
        )


def _synthetic_evaluator(best: dict[str, float]):
    """SYNTHETIC deviation: distance from a known optimum (no geometry, test only)."""
    calls: list[tuple] = []

    def evaluate(parameters):
        calls.append(parameters)
        deviation = max(abs(item.value - best[item.parameter_id]) for item in parameters) / 10
        digest = hashlib.sha256(repr(parameters).encode()).hexdigest()
        return deviation, digest

    return evaluate, calls


def test_bounded_grid_optimizer_finds_the_known_optimum_inside_tolerances() -> None:
    model, proposal = _scenario()
    evaluate, calls = _synthetic_evaluator({"height": 104.5, "width": 29.5})
    optimizer = BoundedGridFitOptimizer(evaluate)
    assert isinstance(optimizer, DimensionFitOptimizerBackend)
    first = optimizer.optimize(proposal.request)
    assert first == BoundedGridFitOptimizer(evaluate).optimize(proposal.request)
    assert len(calls) == 2 * 25
    best = {item.parameter_id: item.value for item in first.candidates[0].parameter_values}
    assert best == {"height": 104.5, "width": 29.5}
    for candidate in first.candidates:
        assert candidate.estimated_maximum_deviation <= proposal.request.maximum_deviation
        for value in candidate.parameter_values:
            constraint = next(
                c for c in proposal.request.constraints if c.parameter_id == value.parameter_id
            )
            assert abs(value.value - constraint.target_value) <= constraint.tolerance
    accepted = accept_dimension_fit_proposal(
        model,
        first,
        request=proposal.request,
        candidate_id=first.candidates[0].candidate_id,
        actor_id="owner-1",
        reason="Reviewed the optimizer proposal.",
        created_at_utc="2026-10-22T19:05:00Z",
    )
    assert accepted.model.mold_use_authorized is False


def test_bounded_grid_optimizer_reports_when_nothing_meets_the_budget() -> None:
    _model_unused, proposal = _scenario()
    with pytest.raises(DimensionFitProposalError, match="no_candidate_within_deviation_budget"):
        BoundedGridFitOptimizer(lambda parameters: (9.0, "a" * 64)).optimize(proposal.request)


@pytest.mark.parametrize(("target", "tolerance"), [(31.0, 0.3), (1.0, 0.1), (102.0, 5.0)])
def test_every_grid_point_satisfies_the_acceptance_tolerance_check(target, tolerance) -> None:
    # Re-review V2-1: float rounding put endpoints like 31.0 +/- 0.3 just outside tolerance.
    constraint = MeasuredParameterConstraint(
        "height",
        "m-1",
        "1" * 64,
        target,
        tolerance,
        "mm_unverified",
        "owner-1",
        "2026-10-22T19:00:00Z",
    )
    request = DimensionFitOptimizationRequest(
        "model-1", "scan-1", "2" * 64, "3" * 64, 10.0, (constraint,)
    )
    proposal = BoundedGridFitOptimizer(lambda parameters: (0.0, "4" * 64), 64).optimize(request)
    values = [item.parameter_values[0].value for item in proposal.candidates]
    assert len(values) == 5
    assert all(abs(value - target) <= tolerance for value in values)
    assert min(values) < target < max(values)


def test_optimizer_bounds_inputs_and_budget_boundary() -> None:
    constraints = tuple(
        MeasuredParameterConstraint(
            f"p{index}",
            f"m-{index}",
            "1" * 64,
            10.0,
            1.0,
            "mm_unverified",
            "owner-1",
            "2026-10-22T19:00:00Z",
        )
        for index in range(5)
    )
    five = DimensionFitOptimizationRequest(
        "model-1", "scan-1", "2" * 64, "3" * 64, 1.0, constraints
    )
    calls: list[object] = []
    with pytest.raises(DimensionFitProposalError, match="grid_search_exceeds_evaluation_bound"):
        BoundedGridFitOptimizer(lambda p: calls.append(p) or (0.0, "4" * 64)).optimize(five)
    assert calls == []  # rejected before any evaluation
    one = DimensionFitOptimizationRequest(
        "model-1", "scan-1", "2" * 64, "3" * 64, 0.5, constraints[:1]
    )
    at_budget = BoundedGridFitOptimizer(lambda p: (0.5, "4" * 64), 64).optimize(one)
    assert len(at_budget.candidates) == 5  # budget boundary is inclusive, like acceptance
    assert len(BoundedGridFitOptimizer(lambda p: (0.5, "4" * 64), 1).optimize(one).candidates) == 1
    for bad in (True, 0, 65, 2.5):
        with pytest.raises(DimensionFitProposalError, match="maximum_candidates_invalid"):
            BoundedGridFitOptimizer(lambda p: (0.0, "4" * 64), bad).optimize(one)  # type: ignore[arg-type]
    with pytest.raises(DimensionFitProposalError, match="evaluator_result_invalid"):
        BoundedGridFitOptimizer(lambda p: 0.0).optimize(one)  # type: ignore[arg-type,return-value]
