from __future__ import annotations

import json
from dataclasses import replace

import pytest
from test_design_profile_zones import _fit_clear_zones

from packlab_core.design_profile_zones import ProfileZoneStatus, detect_design_profile_zones
from packlab_core.profile_zone_proposal import (
    ProfileZonePlacementCandidate,
    ProfileZonePlacementProposal,
    ProfileZoneProposalBackend,
    ProfileZoneProposalError,
    ProfileZoneProposalProvenance,
    ProfileZoneProposalRequest,
    accept_profile_zone_proposal,
    create_profile_zone_proposal_request,
)


def _scenario():
    fit = _fit_clear_zones()
    zones = detect_design_profile_zones(fit, expected_fit_id=fit.fit_id, component_id="container")
    request = create_profile_zone_proposal_request(fit, zones)
    base, body, shoulder, _neck = zones.boundaries
    transitions = (
        base.end_axial + 0.05,
        body.end_axial + 0.05,
        shoulder.end_axial + 0.05,
    )
    proposal = ProfileZonePlacementProposal(
        "proposal-1",
        request,
        (
            ProfileZonePlacementCandidate("candidate-1", transitions, 0.9),
            ProfileZonePlacementCandidate("candidate-2", tuple(sorted(transitions)), 0.4),
        ),
        ProfileZoneProposalProvenance("fake-backend", "fake-model", "not-selected", "test-v1"),
    )
    return fit, zones, proposal


def test_fake_backend_yields_non_authoritative_proposal_without_mutation() -> None:
    fit, zones, proposal = _scenario()

    class FakeBackend:
        def propose(self, request: ProfileZoneProposalRequest) -> ProfileZonePlacementProposal:
            assert request.fit_id == fit.fit_id
            return proposal

    backend: ProfileZoneProposalBackend = FakeBackend()
    result = backend.propose(proposal.request)
    payload = result.as_dict()

    assert isinstance(backend, ProfileZoneProposalBackend)
    assert payload["generated"] is True and payload["accepted"] is False
    assert payload["authority_class"] == "AI_PROFILE_ZONE_PLACEMENT_PROPOSAL"
    assert payload["zone_mutated"] is False
    assert payload["mold_use_authorized"] is False
    assert "path" not in json.dumps(payload) and "profile_samples" not in payload
    assert zones.revision_id == proposal.request.zone_revision_id
    assert fit.fit_id == proposal.request.fit_id


def test_candidates_require_unique_ids_canonical_order_and_finite_confidence() -> None:
    _fit, _zones, proposal = _scenario()
    with pytest.raises(ProfileZoneProposalError, match="candidate_id_duplicate"):
        ProfileZonePlacementProposal(
            proposal.proposal_id,
            proposal.request,
            (
                ProfileZonePlacementCandidate("same", (1.0, 2.0, 3.0), 0.9),
                ProfileZonePlacementCandidate("same", (1.1, 2.1, 3.1), 0.4),
            ),
            proposal.provenance,
        )
    with pytest.raises(ProfileZoneProposalError, match="candidates_not_canonically_ordered"):
        ProfileZonePlacementProposal(
            proposal.proposal_id,
            proposal.request,
            tuple(reversed(proposal.candidates)),
            proposal.provenance,
        )
    with pytest.raises(ProfileZoneProposalError, match="candidate_confidence_invalid"):
        ProfileZonePlacementCandidate("invalid-confidence", (1.0, 2.0, 3.0), float("inf"))


def test_acceptance_creates_manual_review_required_successor_and_evidence() -> None:
    fit, zones, proposal = _scenario()
    selected = proposal.candidates[0]
    accepted = accept_profile_zone_proposal(
        fit,
        zones,
        proposal,
        candidate_id=selected.candidate_id,
        actor_id="owner-1",
        reason="I reviewed these profile section placements.",
        created_at_utc="2026-10-22T18:30:00Z",
    )

    assert accepted.zones.revision_id != zones.revision_id
    assert accepted.zones.previous_revision_id == zones.revision_id
    assert accepted.zones.status is ProfileZoneStatus.MANUAL_OVERRIDE
    assert accepted.zones.review_required is True
    assert (
        tuple(item.end_axial for item in accepted.zones.boundaries[:-1])
        == selected.transition_axial
    )
    assert zones.revision_id == proposal.request.zone_revision_id
    assert fit.fit_id == proposal.request.fit_id
    record = accepted.acceptance.as_dict()
    assert record["source_zone_revision_id"] == zones.revision_id
    assert record["accepted_zone_revision_id"] == accepted.zones.revision_id
    assert record["proposal_sha256"] == proposal.digest
    assert record["authority_class"] == "USER_CONFIRMED_DESIGN_PROFILE_ZONE_OVERRIDE"
    assert accepted.zones.as_dict()["scan_master_replaced"] is False


def test_acceptance_rejects_stale_or_unproposed_candidate() -> None:
    fit, zones, proposal = _scenario()
    with pytest.raises(ProfileZoneProposalError, match="proposal_source_revision_stale"):
        accept_profile_zone_proposal(
            fit,
            replace(zones, revision_id="design-profile-zones:stale"),
            proposal,
            candidate_id="candidate-1",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T18:30:00Z",
        )

    with pytest.raises(ProfileZoneProposalError, match="candidate_not_in_proposal"):
        accept_profile_zone_proposal(
            fit,
            zones,
            proposal,
            candidate_id="not-proposed",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T18:30:00Z",
        )


def test_acceptance_rejects_transitions_outside_the_fitted_profile() -> None:
    fit, zones, proposal = _scenario()
    out_of_range = ProfileZonePlacementProposal(
        "proposal-out-of-range",
        proposal.request,
        (ProfileZonePlacementCandidate("candidate-out-of-range", (-1.0, 2.0, 3.0), 0.9),),
        proposal.provenance,
    )
    with pytest.raises(
        ProfileZoneProposalError,
        match="candidate_transitions_outside_profile_or_unordered",
    ):
        accept_profile_zone_proposal(
            fit,
            zones,
            out_of_range,
            candidate_id="candidate-out-of-range",
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T18:30:00Z",
        )
