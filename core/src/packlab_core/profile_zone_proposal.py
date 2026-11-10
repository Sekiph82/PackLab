"""Non-authoritative profile-zone placement proposals with explicit confirmation."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol, runtime_checkable

from .design_profile_fit import DesignModelProfileFit
from .design_profile_zones import (
    DesignProfileZones,
    ProfileZoneError,
    override_design_profile_zones,
)

PROFILE_ZONE_PROPOSAL_CONTRACT = "packlab.profile-zone-proposal.v1"
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$", re.ASCII)
_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.ASCII)


_PROVENANCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+:@-]{0,159}", re.ASCII)


class ProfileZoneProposalError(ValueError):
    """Raised when a placement proposal or confirmation violates its contract."""


@dataclass(frozen=True, slots=True)
class ProfileZoneProposalRequest:
    fit_id: str
    zone_revision_id: str
    zone_record_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.fit_id, "fit_id")
        _identifier(self.zone_revision_id, "zone_revision_id")
        _digest(self.zone_record_sha256, "zone_record_sha256")

    def as_dict(self) -> dict[str, str]:
        return {
            "fit_id": self.fit_id,
            "zone_revision_id": self.zone_revision_id,
            "zone_record_sha256": self.zone_record_sha256,
        }


@dataclass(frozen=True, slots=True)
class ProfileZonePlacementCandidate:
    candidate_id: str
    transition_axial: tuple[float, float, float]
    confidence: float

    def __post_init__(self) -> None:
        _identifier(self.candidate_id, "candidate_id")
        if not isinstance(self.transition_axial, tuple) or len(self.transition_axial) != 3:
            raise ProfileZoneProposalError("transition_axial_must_have_three_values")
        normalized: list[float] = []
        for position in self.transition_axial:
            if (
                isinstance(position, bool)
                or not isinstance(position, (int, float))
                or not math.isfinite(position)
            ):
                raise ProfileZoneProposalError("transition_axial_invalid")
            normalized.append(float(position))
        object.__setattr__(self, "transition_axial", tuple(normalized))
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not math.isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 1.0
        ):
            raise ProfileZoneProposalError("candidate_confidence_invalid")
        object.__setattr__(self, "confidence", float(self.confidence))

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "transition_axial": list(self.transition_axial),
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class ProfileZoneProposalProvenance:
    backend_id: str
    model_id: str
    checkpoint_id: str
    version: str
    checkpoint_sha256: str | None = None

    def __post_init__(self) -> None:
        for name in ("backend_id", "model_id", "checkpoint_id", "version"):
            value = getattr(self, name)
            # Opaque identifiers only: no paths, whitespace or control characters (F-3).
            if not isinstance(value, str) or not _PROVENANCE_ID.fullmatch(value):
                raise ProfileZoneProposalError(f"{name}_invalid")
        if self.checkpoint_sha256 is not None:
            _digest(self.checkpoint_sha256, "checkpoint_sha256")

    def as_dict(self) -> dict[str, str | None]:
        return {
            "backend_id": self.backend_id,
            "model_id": self.model_id,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_sha256": self.checkpoint_sha256,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class ProfileZonePlacementProposal:
    proposal_id: str
    request: ProfileZoneProposalRequest
    candidates: tuple[ProfileZonePlacementCandidate, ...]
    provenance: ProfileZoneProposalProvenance

    def __post_init__(self) -> None:
        _identifier(self.proposal_id, "proposal_id")
        if not isinstance(self.request, ProfileZoneProposalRequest):
            raise ProfileZoneProposalError("request_required")
        if not isinstance(self.provenance, ProfileZoneProposalProvenance):
            raise ProfileZoneProposalError("provenance_required")
        if (
            not isinstance(self.candidates, tuple)
            or not 1 <= len(self.candidates) <= 32
            or any(not isinstance(item, ProfileZonePlacementCandidate) for item in self.candidates)
        ):
            raise ProfileZoneProposalError("candidates_invalid")
        ids = tuple(item.candidate_id for item in self.candidates)
        if len(ids) != len(set(ids)):
            raise ProfileZoneProposalError("candidate_id_duplicate")
        expected = tuple(
            sorted(self.candidates, key=lambda item: (-item.confidence, item.candidate_id))
        )
        if self.candidates != expected:
            raise ProfileZoneProposalError("candidates_not_canonically_ordered")

    @property
    def generated(self) -> bool:
        return True

    @property
    def accepted(self) -> bool:
        return False

    @property
    def authority_class(self) -> str:
        return "AI_PROFILE_ZONE_PLACEMENT_PROPOSAL"

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": PROFILE_ZONE_PROPOSAL_CONTRACT,
            "proposal_id": self.proposal_id,
            "request": self.request.as_dict(),
            "candidates": [item.as_dict() for item in self.candidates],
            "provenance": self.provenance.as_dict(),
            "generated": self.generated,
            "accepted": self.accepted,
            "authority_class": self.authority_class,
            "zone_mutated": False,
            "scan_master_replaced": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }

    @property
    def digest(self) -> str:
        return _digest_object(self.as_dict())


@runtime_checkable
class ProfileZoneProposalBackend(Protocol):
    """Replaceable adapter; inference-specific types stay behind the interface."""

    def propose(self, request: ProfileZoneProposalRequest) -> ProfileZonePlacementProposal: ...


@dataclass(frozen=True, slots=True)
class ProfileZoneProposalAcceptance:
    acceptance_id: str
    proposal_id: str
    proposal_sha256: str
    source_fit_id: str
    source_zone_revision_id: str
    accepted_zone_revision_id: str
    candidate_id: str
    transition_axial: tuple[float, float, float]
    actor_id: str
    reason: str
    created_at_utc: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.profile-zone-proposal-acceptance.v1",
            "acceptance_id": self.acceptance_id,
            "proposal_id": self.proposal_id,
            "proposal_sha256": self.proposal_sha256,
            "source_fit_id": self.source_fit_id,
            "source_zone_revision_id": self.source_zone_revision_id,
            "accepted_zone_revision_id": self.accepted_zone_revision_id,
            "candidate_id": self.candidate_id,
            "transition_axial": list(self.transition_axial),
            "authority_class": "USER_CONFIRMED_DESIGN_PROFILE_ZONE_OVERRIDE",
            "actor_id": self.actor_id,
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
        }


@dataclass(frozen=True, slots=True)
class AcceptedProfileZoneProposal:
    zones: DesignProfileZones
    acceptance: ProfileZoneProposalAcceptance


def create_profile_zone_proposal_request(
    fit: DesignModelProfileFit, zones: DesignProfileZones
) -> ProfileZoneProposalRequest:
    if not isinstance(fit, DesignModelProfileFit) or not isinstance(zones, DesignProfileZones):
        raise ProfileZoneProposalError("profile_fit_and_zones_required")
    if fit.fit_id != zones.fit_id:
        raise ProfileZoneProposalError("profile_fit_zone_mismatch")
    return ProfileZoneProposalRequest(
        fit.fit_id, zones.revision_id, _digest_object(zones.as_dict())
    )


def accept_profile_zone_proposal(
    fit: DesignModelProfileFit,
    zones: DesignProfileZones,
    proposal: ProfileZonePlacementProposal,
    *,
    candidate_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> AcceptedProfileZoneProposal:
    """Create a manual zone revision from one explicitly confirmed proposal."""

    if not isinstance(proposal, ProfileZonePlacementProposal):
        raise ProfileZoneProposalError("proposal_required")
    request = proposal.request
    if request.fit_id != fit.fit_id or request.zone_revision_id != zones.revision_id:
        raise ProfileZoneProposalError("proposal_source_revision_stale")
    if request.zone_record_sha256 != _digest_object(zones.as_dict()):
        raise ProfileZoneProposalError("proposal_source_zone_digest_mismatch")
    if zones.fit_id != fit.fit_id:
        raise ProfileZoneProposalError("profile_fit_zone_mismatch")
    selected = next(
        (item for item in proposal.candidates if item.candidate_id == candidate_id), None
    )
    if selected is None:
        raise ProfileZoneProposalError("candidate_not_in_proposal")
    actor = _bounded_text(actor_id, "actor_id", 128)
    why = _bounded_text(reason, "reason", 512)
    timestamp = _utc_timestamp(created_at_utc)
    points = fit.profile.points if fit.profile is not None else ()
    if len(points) < 2:
        raise ProfileZoneProposalError("fitted_profile_required")
    start, end = points[0].axial, points[-1].axial
    transitions = selected.transition_axial
    if any(not start < value < end for value in transitions) or not all(
        left < right for left, right in zip(transitions, transitions[1:])
    ):
        raise ProfileZoneProposalError("candidate_transitions_outside_profile_or_unordered")
    if len(zones.boundaries) != 4:
        raise ProfileZoneProposalError("four_profile_zones_required")
    cuts = (start, *transitions, end)
    boundaries = tuple(
        replace(boundary, start_axial=cuts[index], end_axial=cuts[index + 1])
        for index, boundary in enumerate(zones.boundaries)
    )
    try:
        accepted = override_design_profile_zones(
            zones,
            fit,
            expected_zone_revision_id=zones.revision_id,
            expected_fit_id=fit.fit_id,
            boundaries=boundaries,
            actor_id=actor,
            reason=why,
            created_at_utc=timestamp,
        )
    except ProfileZoneError as error:
        raise ProfileZoneProposalError(f"zone_override_rejected:{error}") from error
    body = {
        "proposal_id": proposal.proposal_id,
        "proposal_sha256": proposal.digest,
        "source_fit_id": fit.fit_id,
        "source_zone_revision_id": zones.revision_id,
        "accepted_zone_revision_id": accepted.revision_id,
        "candidate_id": candidate_id,
        "transition_axial": list(transitions),
        "actor_id": actor,
        "reason": why,
        "created_at_utc": timestamp,
    }
    evidence = ProfileZoneProposalAcceptance(
        acceptance_id="profile-zone-acceptance:" + _digest_object(body),
        proposal_id=proposal.proposal_id,
        proposal_sha256=proposal.digest,
        source_fit_id=fit.fit_id,
        source_zone_revision_id=zones.revision_id,
        accepted_zone_revision_id=accepted.revision_id,
        candidate_id=candidate_id,
        transition_axial=transitions,
        actor_id=actor,
        reason=why,
        created_at_utc=timestamp,
    )
    return AcceptedProfileZoneProposal(accepted, evidence)


def _identifier(value: object, name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ProfileZoneProposalError(f"{name}_invalid")


def _digest(value: object, name: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ProfileZoneProposalError(f"{name}_invalid")


def _digest_object(value: object) -> str:
    try:
        canonical = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
    except (TypeError, ValueError) as error:
        raise ProfileZoneProposalError("canonical_serialization_failed") from error
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _bounded_text(value: object, name: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ProfileZoneProposalError(f"{name}_invalid")
    return value


def _utc_timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProfileZoneProposalError("created_at_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ProfileZoneProposalError("created_at_invalid") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ProfileZoneProposalError("created_at_must_be_utc_z")
    return value


__all__ = [
    "AcceptedProfileZoneProposal",
    "PROFILE_ZONE_PROPOSAL_CONTRACT",
    "ProfileZonePlacementCandidate",
    "ProfileZoneProposalAcceptance",
    "ProfileZoneProposalBackend",
    "ProfileZoneProposalError",
    "ProfileZoneProposalProvenance",
    "ProfileZoneProposalRequest",
    "ProfileZonePlacementProposal",
    "accept_profile_zone_proposal",
    "create_profile_zone_proposal_request",
]
