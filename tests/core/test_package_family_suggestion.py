from __future__ import annotations

import json

import pytest

from packlab_core.package_family_suggestion import (
    PackageFamilyCandidate,
    PackageFamilySuggestion,
    PackageFamilySuggestionBackend,
    PackageFamilySuggestionError,
    PackageFamilySuggestionProvenance,
    PackageFamilySuggestionRequest,
    SuggestionEvidenceKind,
    accept_package_family_suggestion,
)
from packlab_core.packaging_asset import (
    AssetStatus,
    FieldProvenance,
    PackagingAsset,
    PackagingFamily,
    ProvenanceClass,
)


def _asset() -> PackagingAsset:
    return PackagingAsset(
        "asset-1",
        "Example package",
        PackagingFamily.UNKNOWN,
        field_provenance=(FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),),
    )


def _suggestion(asset: PackagingAsset) -> PackageFamilySuggestion:
    request = PackageFamilySuggestionRequest(
        asset_id=asset.asset_id,
        asset_revision_id=asset.revision_id,
        evidence_kind=SuggestionEvidenceKind.METADATA,
        evidence_sha256="1" * 64,
    )
    return PackageFamilySuggestion(
        suggestion_id="suggestion-1",
        request=request,
        candidates=(
            PackageFamilyCandidate(PackagingFamily.BOTTLE, 0.9),
            PackageFamilyCandidate(PackagingFamily.JAR, 0.1),
        ),
        provenance=PackageFamilySuggestionProvenance(
            "fake-backend", "fake-model", "unselected-checkpoint", "test-v1"
        ),
    )


def test_fake_backend_returns_non_authoritative_suggestion_without_mutating_asset() -> None:
    class FakeBackend:
        def suggest(self, request: PackageFamilySuggestionRequest) -> PackageFamilySuggestion:
            assert request.asset_revision_id == asset.revision_id
            return suggestion

    asset = _asset()
    suggestion = _suggestion(asset)
    backend: PackageFamilySuggestionBackend = FakeBackend()

    result = backend.suggest(suggestion.request)

    payload = result.as_dict()
    assert result.generated is True
    assert result.accepted is False
    assert payload["authority_class"] == "AI_PACKAGE_FAMILY_SUGGESTION"
    assert payload["asset_mutated"] is False
    assert asset.family is PackagingFamily.UNKNOWN
    assert "raw_content" not in payload and "path" not in json.dumps(payload)
    assert isinstance(backend, PackageFamilySuggestionBackend)


def test_candidates_require_unique_families_and_canonical_confidence_order() -> None:
    asset = _asset()
    suggestion = _suggestion(asset)

    with pytest.raises(PackageFamilySuggestionError, match="candidate_family_duplicate"):
        PackageFamilySuggestion(
            suggestion.suggestion_id,
            suggestion.request,
            (
                PackageFamilyCandidate(PackagingFamily.BOTTLE, 0.9),
                PackageFamilyCandidate(PackagingFamily.BOTTLE, 0.1),
            ),
            suggestion.provenance,
        )

    with pytest.raises(PackageFamilySuggestionError, match="candidates_not_canonically_ordered"):
        PackageFamilySuggestion(
            suggestion.suggestion_id,
            suggestion.request,
            tuple(reversed(suggestion.candidates)),
            suggestion.provenance,
        )

    with pytest.raises(PackageFamilySuggestionError, match="candidate_confidence_invalid"):
        PackageFamilyCandidate(PackagingFamily.CAN, float("inf"))


def test_acceptance_is_explicit_immutable_and_bound_to_suggestion_and_asset_revision() -> None:
    asset = _asset()
    suggestion = _suggestion(asset)

    accepted = accept_package_family_suggestion(
        asset,
        suggestion,
        chosen_family=PackagingFamily.BOTTLE,
        actor_id="owner-1",
        reason="I confirmed this package is a bottle.",
        created_at_utc="2026-10-22T18:00:00Z",
    )

    assert asset.family is PackagingFamily.UNKNOWN
    assert accepted.asset.family is PackagingFamily.BOTTLE
    family_provenance = {item.field_name: item for item in accepted.asset.field_provenance}[
        "family"
    ]
    assert family_provenance.classification is ProvenanceClass.USER_DECLARED
    record = accepted.acceptance.as_dict()
    assert record["source_asset_revision_id"] == asset.revision_id
    assert record["accepted_asset_revision_id"] == accepted.asset.revision_id
    assert record["suggestion_sha256"] == suggestion.digest
    assert record["authority_class"] == "USER_CONFIRMED_PACKAGING_METADATA"
    assert record["actor_id"] == "owner-1"


def test_acceptance_rejects_stale_asset_and_unconfirmed_candidate() -> None:
    asset = _asset()
    suggestion = _suggestion(asset)
    stale_asset = asset.with_field_update(
        "status",
        AssetStatus.DRAFT,
        FieldProvenance("status", ProvenanceClass.USER_DECLARED),
    )

    with pytest.raises(PackageFamilySuggestionError, match="suggestion_asset_revision_stale"):
        accept_package_family_suggestion(
            stale_asset,
            suggestion,
            chosen_family=PackagingFamily.BOTTLE,
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T18:00:00Z",
        )

    with pytest.raises(PackageFamilySuggestionError, match="chosen_family_not_suggested"):
        accept_package_family_suggestion(
            asset,
            suggestion,
            chosen_family=PackagingFamily.CAN,
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T18:00:00Z",
        )


def test_other_family_acceptance_requires_a_user_label_and_records_it() -> None:
    asset = _asset()
    request = PackageFamilySuggestionRequest(
        asset.asset_id,
        asset.revision_id,
        SuggestionEvidenceKind.METADATA,
        "1" * 64,
    )
    suggestion = PackageFamilySuggestion(
        "suggestion-other",
        request,
        (PackageFamilyCandidate(PackagingFamily.OTHER, 1.0),),
        PackageFamilySuggestionProvenance("fake", "fake", "none", "v1"),
    )

    with pytest.raises(PackageFamilySuggestionError, match="other_family_label_required"):
        accept_package_family_suggestion(
            asset,
            suggestion,
            chosen_family=PackagingFamily.OTHER,
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T18:00:00Z",
        )

    accepted = accept_package_family_suggestion(
        asset,
        suggestion,
        chosen_family=PackagingFamily.OTHER,
        actor_id="owner-1",
        reason="Owner supplied the package type.",
        created_at_utc="2026-10-22T18:00:00Z",
        other_family_label="Custom dispenser",
    )
    assert accepted.asset.other_family_label == "Custom dispenser"
    provenance = {item.field_name: item for item in accepted.asset.field_provenance}
    assert provenance["family"].classification is ProvenanceClass.USER_DECLARED
    assert provenance["other_family_label"].classification is ProvenanceClass.USER_DECLARED


def test_moving_from_other_to_a_suggested_family_clears_the_other_label() -> None:
    # Review F-4: this path used to fail because the stale OTHER label was kept.
    base = _asset()
    other = PackagingAsset(
        base.asset_id,
        base.display_name,
        PackagingFamily.OTHER,
        other_family_label="Custom dispenser",
        field_provenance=(
            FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
            FieldProvenance("family", ProvenanceClass.USER_DECLARED),
            FieldProvenance("other_family_label", ProvenanceClass.USER_DECLARED),
        ),
    )
    accepted = accept_package_family_suggestion(
        other,
        _suggestion(other),
        chosen_family=PackagingFamily.BOTTLE,
        actor_id="owner-1",
        reason="Owner confirmed it is a bottle.",
        created_at_utc="2026-10-22T18:00:00Z",
    )
    assert accepted.asset.family is PackagingFamily.BOTTLE
    assert accepted.asset.other_family_label is None
    assert other.other_family_label == "Custom dispenser"  # source revision untouched


def test_other_label_is_rejected_for_a_non_other_choice() -> None:
    asset = _asset()
    with pytest.raises(PackageFamilySuggestionError, match="other_family_label_not_allowed"):
        accept_package_family_suggestion(
            asset,
            _suggestion(asset),
            chosen_family=PackagingFamily.BOTTLE,
            actor_id="owner-1",
            reason="Reviewed.",
            created_at_utc="2026-10-22T18:00:00Z",
            other_family_label="Should not be stored",
        )
