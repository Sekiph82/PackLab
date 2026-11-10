"""Non-authoritative package-family suggestions and explicit user acceptance."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from .packaging_asset import (
    FieldProvenance,
    PackagingAsset,
    PackagingAssetError,
    PackagingFamily,
    ProvenanceClass,
)

PACKAGE_FAMILY_SUGGESTION_CONTRACT = "packlab.package-family-suggestion.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.ASCII)
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$", re.ASCII)
_ASSET_REVISION = re.compile(r"^packaging-asset:[0-9a-f]{64}$", re.ASCII)


class PackageFamilySuggestionError(ValueError):
    """Raised when a suggestion or explicit acceptance violates its contract."""


class SuggestionEvidenceKind(StrEnum):
    METADATA = "metadata"
    IMAGE = "image"
    SCAN_MESH = "scan-mesh"


@dataclass(frozen=True, slots=True)
class PackageFamilySuggestionRequest:
    asset_id: str
    asset_revision_id: str
    evidence_kind: SuggestionEvidenceKind
    evidence_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.asset_id, "asset_id")
        if not isinstance(self.asset_revision_id, str) or not _ASSET_REVISION.fullmatch(
            self.asset_revision_id
        ):
            raise PackageFamilySuggestionError("asset_revision_id_invalid")
        if not isinstance(self.evidence_kind, SuggestionEvidenceKind):
            raise PackageFamilySuggestionError("evidence_kind_invalid")
        _digest(self.evidence_sha256, "evidence_sha256")

    def as_dict(self) -> dict[str, object]:
        return {
            "asset_id": self.asset_id,
            "asset_revision_id": self.asset_revision_id,
            "evidence_kind": self.evidence_kind.value,
            "evidence_sha256": self.evidence_sha256,
        }


@dataclass(frozen=True, slots=True)
class PackageFamilySuggestionProvenance:
    backend_id: str
    model_id: str
    checkpoint_id: str
    version: str
    checkpoint_sha256: str | None = None

    def __post_init__(self) -> None:
        for name in ("backend_id", "model_id", "checkpoint_id", "version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                raise PackageFamilySuggestionError(f"{name}_invalid")
        if self.checkpoint_sha256 is not None:
            _digest(self.checkpoint_sha256, "checkpoint_sha256")

    def as_dict(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "model_id": self.model_id,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_sha256": self.checkpoint_sha256,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class PackageFamilyCandidate:
    family: PackagingFamily
    confidence: float

    def __post_init__(self) -> None:
        if not isinstance(self.family, PackagingFamily) or self.family is PackagingFamily.UNKNOWN:
            raise PackageFamilySuggestionError("candidate_family_invalid")
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not math.isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 1.0
        ):
            raise PackageFamilySuggestionError("candidate_confidence_invalid")
        object.__setattr__(self, "confidence", float(self.confidence))

    def as_dict(self) -> dict[str, object]:
        return {"family": self.family.value, "confidence": self.confidence}


@dataclass(frozen=True, slots=True)
class PackageFamilySuggestion:
    suggestion_id: str
    request: PackageFamilySuggestionRequest
    candidates: tuple[PackageFamilyCandidate, ...]
    provenance: PackageFamilySuggestionProvenance

    def __post_init__(self) -> None:
        _identifier(self.suggestion_id, "suggestion_id")
        if not isinstance(self.request, PackageFamilySuggestionRequest):
            raise PackageFamilySuggestionError("request_required")
        if not isinstance(self.provenance, PackageFamilySuggestionProvenance):
            raise PackageFamilySuggestionError("provenance_required")
        if (
            not isinstance(self.candidates, tuple)
            or not 1 <= len(self.candidates) <= len(PackagingFamily) - 1
            or any(not isinstance(item, PackageFamilyCandidate) for item in self.candidates)
        ):
            raise PackageFamilySuggestionError("candidates_invalid")
        families = tuple(item.family for item in self.candidates)
        if len(families) != len(set(families)):
            raise PackageFamilySuggestionError("candidate_family_duplicate")
        ordered = tuple(
            sorted(self.candidates, key=lambda item: (-item.confidence, item.family.value))
        )
        if self.candidates != ordered:
            raise PackageFamilySuggestionError("candidates_not_canonically_ordered")

    @property
    def authority_class(self) -> str:
        return "AI_PACKAGE_FAMILY_SUGGESTION"

    @property
    def generated(self) -> bool:
        return True

    @property
    def accepted(self) -> bool:
        return False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": PACKAGE_FAMILY_SUGGESTION_CONTRACT,
            "suggestion_id": self.suggestion_id,
            "request": self.request.as_dict(),
            "candidates": [item.as_dict() for item in self.candidates],
            "provenance": self.provenance.as_dict(),
            "authority_class": self.authority_class,
            "generated": self.generated,
            "accepted": self.accepted,
            "asset_mutated": False,
        }

    @property
    def digest(self) -> str:
        return _canonical_digest(self.as_dict())


@runtime_checkable
class PackageFamilySuggestionBackend(Protocol):
    """Replaceable inference adapter; model-specific types remain behind it."""

    def suggest(self, request: PackageFamilySuggestionRequest) -> PackageFamilySuggestion: ...


@dataclass(frozen=True, slots=True)
class PackageFamilySuggestionAcceptance:
    acceptance_id: str
    suggestion_id: str
    suggestion_sha256: str
    asset_id: str
    source_asset_revision_id: str
    accepted_asset_revision_id: str
    chosen_family: PackagingFamily
    actor_id: str
    reason: str
    created_at_utc: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.package-family-suggestion-acceptance.v1",
            "acceptance_id": self.acceptance_id,
            "suggestion_id": self.suggestion_id,
            "suggestion_sha256": self.suggestion_sha256,
            "asset_id": self.asset_id,
            "source_asset_revision_id": self.source_asset_revision_id,
            "accepted_asset_revision_id": self.accepted_asset_revision_id,
            "chosen_family": self.chosen_family.value,
            "authority_class": "USER_CONFIRMED_PACKAGING_METADATA",
            "actor_id": self.actor_id,
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
        }


@dataclass(frozen=True, slots=True)
class AcceptedPackageFamilySuggestion:
    asset: PackagingAsset
    acceptance: PackageFamilySuggestionAcceptance


def accept_package_family_suggestion(
    asset: PackagingAsset,
    suggestion: PackageFamilySuggestion,
    *,
    chosen_family: PackagingFamily,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    other_family_label: str | None = None,
) -> AcceptedPackageFamilySuggestion:
    """Create a user-confirmed immutable asset revision from one exact suggestion."""

    if not isinstance(asset, PackagingAsset):
        raise PackageFamilySuggestionError("packaging_asset_required")
    if not isinstance(suggestion, PackageFamilySuggestion):
        raise PackageFamilySuggestionError("suggestion_required")
    request = suggestion.request
    if request.asset_id != asset.asset_id:
        raise PackageFamilySuggestionError("suggestion_asset_id_mismatch")
    if request.asset_revision_id != asset.revision_id:
        raise PackageFamilySuggestionError("suggestion_asset_revision_stale")
    if not isinstance(chosen_family, PackagingFamily) or chosen_family not in {
        item.family for item in suggestion.candidates
    }:
        raise PackageFamilySuggestionError("chosen_family_not_suggested")
    if chosen_family is asset.family:
        raise PackageFamilySuggestionError("chosen_family_does_not_change_asset")
    _identifier(actor_id, "actor_id")
    _bounded_text(reason, "reason", 512)
    _timestamp(created_at_utc)

    updated_provenance = {item.field_name: item for item in asset.field_provenance}
    updated_provenance["family"] = FieldProvenance("family", ProvenanceClass.USER_DECLARED)
    updated_other_label = asset.other_family_label
    if chosen_family is PackagingFamily.OTHER:
        if other_family_label is None:
            raise PackageFamilySuggestionError("other_family_label_required")
        updated_other_label = other_family_label
        updated_provenance["other_family_label"] = FieldProvenance(
            "other_family_label", ProvenanceClass.USER_DECLARED
        )
    elif other_family_label is not None:
        raise PackageFamilySuggestionError("other_family_label_not_allowed")
    try:
        if asset.family is PackagingFamily.OTHER and chosen_family is not PackagingFamily.OTHER:
            updated_provenance["other_family_label"] = FieldProvenance(
                "other_family_label", ProvenanceClass.UNKNOWN
            )
        updated = replace(
            asset,
            family=chosen_family,
            other_family_label=updated_other_label,
            field_provenance=tuple(updated_provenance[name] for name in sorted(updated_provenance)),
        )
    except PackagingAssetError as error:
        raise PackageFamilySuggestionError(f"asset_update_rejected:{error}") from error

    acceptance_body = {
        "suggestion_id": suggestion.suggestion_id,
        "suggestion_sha256": suggestion.digest,
        "asset_id": asset.asset_id,
        "source_asset_revision_id": asset.revision_id,
        "accepted_asset_revision_id": updated.revision_id,
        "chosen_family": chosen_family.value,
        "actor_id": actor_id,
        "reason": reason,
        "created_at_utc": created_at_utc,
    }
    acceptance_id = "package-family-acceptance:" + _canonical_digest(acceptance_body)
    acceptance = PackageFamilySuggestionAcceptance(
        acceptance_id=acceptance_id,
        suggestion_id=suggestion.suggestion_id,
        suggestion_sha256=suggestion.digest,
        asset_id=asset.asset_id,
        source_asset_revision_id=asset.revision_id,
        accepted_asset_revision_id=updated.revision_id,
        chosen_family=chosen_family,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    return AcceptedPackageFamilySuggestion(updated, acceptance)


def _identifier(value: object, name: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise PackageFamilySuggestionError(f"{name}_invalid")


def _digest(value: object, name: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise PackageFamilySuggestionError(f"{name}_invalid")


def _bounded_text(value: object, name: str, maximum: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise PackageFamilySuggestionError(f"{name}_invalid")


def _timestamp(value: object) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PackageFamilySuggestionError("created_at_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise PackageFamilySuggestionError("created_at_invalid") from error
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise PackageFamilySuggestionError("created_at_must_be_utc_z")


def _canonical_digest(value: object) -> str:
    try:
        canonical = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
    except (TypeError, ValueError) as error:
        raise PackageFamilySuggestionError("canonical_serialization_failed") from error
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


__all__ = [
    "AcceptedPackageFamilySuggestion",
    "PACKAGE_FAMILY_SUGGESTION_CONTRACT",
    "PackageFamilyCandidate",
    "PackageFamilySuggestion",
    "PackageFamilySuggestionAcceptance",
    "PackageFamilySuggestionBackend",
    "PackageFamilySuggestionError",
    "PackageFamilySuggestionProvenance",
    "PackageFamilySuggestionRequest",
    "SuggestionEvidenceKind",
    "accept_package_family_suggestion",
]
