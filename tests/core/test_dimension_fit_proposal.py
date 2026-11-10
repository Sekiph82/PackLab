from __future__ import annotations

import json
from dataclasses import replace

import pytest
from test_design_history import _model

from packlab_core.design_model import revise_design_model_revision
from packlab_core.dimension_fit_proposal import (
    DimensionFitCandidate,
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
            candidate_id="candidate-1",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T19:05:00Z",
        )
    with pytest.raises(DimensionFitProposalError, match="candidate_not_in_proposal"):
        accept_dimension_fit_proposal(
            model,
            proposal,
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
            candidate_id="candidate-1",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T19:05:00Z",
        )
