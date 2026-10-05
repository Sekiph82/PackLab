from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from packlab_core.packaging_asset import (
    FieldProvenance,
    PackagingAsset,
    PackagingFamily,
    ProvenanceClass,
)
from packlab_core.packaging_components import (
    CompatibilityBasis,
    CompatibilityClass,
    CompatibilityEvidence,
    CompatibilityResult,
    PackagingCompatibilityIndex,
    PackagingComponentError,
    PackagingComponentKind,
    ReusablePackagingComponent,
    create_compatibility_link,
)


def _body(asset_id: str) -> PackagingAsset:
    return PackagingAsset(
        asset_id=asset_id,
        display_name=f"{asset_id} bottle body",
        family=PackagingFamily.BOTTLE,
        neck_finish="28/410",
        field_provenance=(
            FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
            FieldProvenance("family", ProvenanceClass.USER_DECLARED),
            FieldProvenance("neck_finish", ProvenanceClass.USER_DECLARED),
        ),
    )


def _component(
    component_id: str = "component-closure-1",
    kind: PackagingComponentKind = PackagingComponentKind.CAP,
    interface_reference: str | None = "28/410",
    interface_provenance: FieldProvenance | None = None,
) -> ReusablePackagingComponent:
    if interface_reference is not None and interface_provenance is None:
        interface_provenance = FieldProvenance(
            "component_interface_reference", ProvenanceClass.USER_DECLARED
        )
    return ReusablePackagingComponent(
        component_id,
        kind,
        f"Reusable {kind.value.lower()}",
        interface_reference,
        interface_provenance,
    )


def _user_evidence() -> CompatibilityEvidence:
    return CompatibilityEvidence(
        CompatibilityClass.USER_DECLARED,
        CompatibilityBasis.USER_DECLARATION,
    )


def test_reusable_component_records_cover_cap_trigger_and_pump() -> None:
    components = tuple(
        _component(f"component-{kind.value.lower()}", kind) for kind in PackagingComponentKind
    )

    assert {item.kind for item in components} == set(PackagingComponentKind)
    assert len({item.component_id for item in components}) == 3
    assert len({item.revision_id for item in components}) == 3
    assert all(item.as_dict()["geometry_stored_in_library"] is False for item in components)


def test_component_interface_values_require_field_provenance_and_are_revisioned() -> None:
    with pytest.raises(PackagingComponentError, match="interface_provenance_required"):
        ReusablePackagingComponent(
            "component-no-provenance",
            PackagingComponentKind.CAP,
            "Unprovenanced cap",
            interface_reference="28/410",
        )
    with pytest.raises(PackagingComponentError, match="unknown_provenance_invalid"):
        ReusablePackagingComponent(
            "component-bad-unknown",
            PackagingComponentKind.CAP,
            "Malformed unknown provenance",
            interface_provenance="invalid",  # type: ignore[arg-type]
        )

    first = _component(
        interface_provenance=FieldProvenance(
            "component_interface_reference", ProvenanceClass.USER_DECLARED
        )
    )
    supplier = _component(
        interface_provenance=FieldProvenance(
            "component_interface_reference",
            ProvenanceClass.SUPPLIER_FACT,
            source_reference_id="supplier-cap-sheet-1",
        )
    )

    assert first.interface_reference == supplier.interface_reference
    assert first.revision_id != supplier.revision_id
    assert supplier.as_dict()["interface_provenance"]["classification"] == "SUPPLIER_FACT"
    assert "C:\\" not in supplier.canonical_json


def test_one_component_links_to_many_exact_body_revisions() -> None:
    component = _component()
    body_a = _body("body-asset-a")
    body_b = _body("body-asset-b")
    link_a = create_compatibility_link(
        body_a,
        component,
        result=CompatibilityResult.COMPATIBLE,
        evidence=_user_evidence(),
    )
    link_b = create_compatibility_link(
        body_b,
        component,
        result=CompatibilityResult.COMPATIBLE,
        evidence=_user_evidence(),
    )
    empty = PackagingCompatibilityIndex()
    with_a = empty.with_link(link_a, body_a, component)
    with_b = with_a.with_link(link_b, body_b, component)

    assert len(with_b.links) == 2
    assert {item.component_id for item in with_b.links} == {component.component_id}
    assert with_b.revision_id != empty.revision_id
    assert with_b.revision_id != with_a.revision_id
    assert link_a.revision_id != link_b.revision_id
    assert with_b == PackagingCompatibilityIndex((link_b, link_a))
    assert empty.links == ()


def test_compatibility_requires_exact_live_targets_and_rejects_duplicate_links() -> None:
    body = _body("body-asset-a")
    component = _component()
    link = create_compatibility_link(
        body,
        component,
        result=CompatibilityResult.COMPATIBLE,
        evidence=_user_evidence(),
    )
    index = PackagingCompatibilityIndex().with_link(link, body, component)
    assert link.validate_targets(body, component) is None

    edited_body = body.with_field_update(
        "display_name",
        "Renamed bottle body",
        FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
    )
    edited_component = _component(interface_reference="28/410 modified")
    with pytest.raises(PackagingComponentError, match="body_target_stale_or_missing"):
        link.validate_targets(edited_body, component)
    with pytest.raises(PackagingComponentError, match="component_target_stale_or_missing"):
        link.validate_targets(body, edited_component)
    with pytest.raises(PackagingComponentError, match="compatibility_link_duplicate"):
        index.with_link(link, body, component)


@pytest.mark.parametrize(
    ("classification", "basis", "kwargs", "message"),
    [
        (
            CompatibilityClass.SUPPLIER_DECLARED,
            CompatibilityBasis.SUPPLIER_SPECIFICATION,
            {},
            "supplier_compatibility_evidence_invalid",
        ),
        (
            CompatibilityClass.SUPPLIER_DECLARED,
            CompatibilityBasis.NECK_FINISH_REFERENCE,
            {"source_reference_id": "supplier-doc-1"},
            "supplier_compatibility_evidence_invalid",
        ),
        (
            CompatibilityClass.USER_DECLARED,
            CompatibilityBasis.VISUAL_SIMILARITY,
            {},
            "user_compatibility_evidence_invalid",
        ),
        (
            CompatibilityClass.PACKLAB_ESTIMATE,
            CompatibilityBasis.SUPPLIER_SPECIFICATION,
            {"method_id": "neck-match.v1"},
            "estimated_compatibility_evidence_invalid",
        ),
        (
            CompatibilityClass.PACKLAB_ESTIMATE,
            CompatibilityBasis.NECK_FINISH_REFERENCE,
            {"method_id": "neck-match.v1", "confidence": 1.01},
            "compatibility_confidence_invalid",
        ),
    ],
)
def test_incompatible_compatibility_provenance_rejects(
    classification: CompatibilityClass,
    basis: CompatibilityBasis,
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(PackagingComponentError, match=message):
        CompatibilityEvidence(classification, basis, **kwargs)  # type: ignore[arg-type]


def test_neck_finish_estimates_and_supplier_declarations_never_claim_verified_fit() -> None:
    body = _body("body-asset-a")
    component = _component()
    estimate = CompatibilityEvidence(
        CompatibilityClass.PACKLAB_ESTIMATE,
        CompatibilityBasis.NECK_FINISH_REFERENCE,
        method_id="neck-reference-match.v1",
        confidence=0.8,
    )
    estimated_link = create_compatibility_link(
        body,
        component,
        result=CompatibilityResult.COMPATIBLE,
        evidence=estimate,
    )
    supplier_evidence = CompatibilityEvidence(
        CompatibilityClass.SUPPLIER_DECLARED,
        CompatibilityBasis.SUPPLIER_SPECIFICATION,
        source_reference_id="supplier-fit-sheet-4",
    )
    supplier_link = create_compatibility_link(
        body,
        component,
        result=CompatibilityResult.COMPATIBLE,
        evidence=supplier_evidence,
    )

    for link in (estimated_link, supplier_link):
        serialized = link.as_dict()
        assert serialized["fit_verified"] is False
        assert serialized["supplier_fit_certified"] is False
        assert serialized["compatibility_inferred_from_visual_similarity"] is False
    assert estimated_link.as_dict()["evidence"]["classification"] == "PACKLAB_ESTIMATE"
    assert estimated_link.as_dict()["evidence"]["basis"] == "NECK_FINISH_REFERENCE"


def test_compatibility_index_rejects_mutable_or_oversized_link_sets() -> None:
    with pytest.raises(PackagingComponentError, match="compatibility_index_links_invalid"):
        PackagingCompatibilityIndex([])  # type: ignore[arg-type]

    body = _body("body-asset-a")
    component = _component()
    link = create_compatibility_link(
        body,
        component,
        result=CompatibilityResult.UNKNOWN,
        evidence=_user_evidence(),
    )
    with pytest.raises(PackagingComponentError, match="compatibility_index_limit_exceeded"):
        PackagingCompatibilityIndex((link,) * 10_001)


def test_component_values_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        _component().display_name = "Changed"  # type: ignore[misc]
