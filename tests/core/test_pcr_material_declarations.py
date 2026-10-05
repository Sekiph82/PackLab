from __future__ import annotations

import pytest

from packlab_core.pcr_material_declarations import (
    ExternalAuthorityReference,
    PCRDeclarationStatus,
    PCRMetadataError,
    create_pcr_declaration,
    create_pcr_visual_variant,
)


def _declaration(
    percentage: float = 35.0,
    status: PCRDeclarationStatus = PCRDeclarationStatus.DECLARED,
    external_authority: ExternalAuthorityReference | None = None,
):
    return create_pcr_declaration(
        material_id="material-hdpe-visual",
        recycled_content_percentage=percentage,
        status=status,
        design_model_revision_id="design-model:revision-42",
        component_id="component-bottle-body",
        external_authority=external_authority,
    )


@pytest.mark.parametrize("percentage", [0, 100, 0.0, 100.0])
def test_declaration_accepts_zero_and_one_hundred_percent(percentage: float) -> None:
    declaration = _declaration(percentage)

    assert declaration.recycled_content_percentage == float(percentage)
    assert declaration.as_dict()["recycled_content_certified"] is False


@pytest.mark.parametrize("percentage", [-0.01, 100.01, float("nan"), float("inf"), True, "35"])
def test_declaration_rejects_invalid_percentages(percentage: object) -> None:
    with pytest.raises(PCRMetadataError, match="percentage_invalid"):
        _declaration(percentage)  # type: ignore[arg-type]


def test_external_reference_status_requires_explicit_bounded_authority() -> None:
    with pytest.raises(PCRMetadataError, match="external_authority_reference_required"):
        _declaration(status=PCRDeclarationStatus.VERIFIED_EXTERNAL_REFERENCE)

    authority = ExternalAuthorityReference(
        authority_name="Supplier declaration",
        reference_id="supplier-doc:2026-04",
        document_sha256="a" * 64,
    )
    declaration = _declaration(
        status=PCRDeclarationStatus.VERIFIED_EXTERNAL_REFERENCE,
        external_authority=authority,
    )
    serialized = declaration.as_dict()

    assert serialized["external_authority_reference"] == authority.as_dict()
    assert serialized["external_reference_independently_verified_by_packlab"] is False
    assert serialized["recycled_content_certified"] is False
    assert serialized["environmental_performance_verified"] is False
    assert serialized["regulatory_approval"] is False
    assert serialized["physical_or_environmental_claim"] is False


def test_external_authority_is_not_accepted_for_unverified_status() -> None:
    authority = ExternalAuthorityReference("Supplier", "supplier-ref:1", "b" * 64)
    with pytest.raises(PCRMetadataError, match="external_authority_status_mismatch"):
        _declaration(external_authority=authority)


@pytest.mark.parametrize(
    ("name", "reference", "digest"),
    [
        ("", "supplier-ref:1", "a" * 64),
        ("Supplier", "C:\\private\\file", "a" * 64),
        ("Supplier", "supplier-ref:1", "A" * 64),
        ("Supplier", "supplier-ref:1", "a" * 63),
    ],
)
def test_external_authority_reference_is_bounded(name: str, reference: str, digest: str) -> None:
    with pytest.raises(PCRMetadataError):
        ExternalAuthorityReference(name, reference, digest)


def test_declaration_identity_is_deterministic_and_pins_exact_provenance() -> None:
    first = _declaration(35)
    second = _declaration(35.0)

    assert first == second
    assert first.revision_id == second.revision_id
    assert first.as_dict()["provenance"] == {
        "design_model_revision_id": "design-model:revision-42",
        "component_id": "component-bottle-body",
    }
    assert _declaration(36).revision_id != first.revision_id


def test_visual_variants_are_deterministic_and_only_add_appearance_metadata() -> None:
    declaration = _declaration()
    args = {
        "variant_id": "variant-natural-grey",
        "display_name": "Natural grey appearance",
        "appearance_color_rgba": (0.42, 0.44, 0.43, 1.0),
        "design_model_revision_id": "design-model:revision-42",
        "component_id": "component-bottle-body",
    }
    first = create_pcr_visual_variant(declaration, **args)
    second = create_pcr_visual_variant(declaration, **args)
    serialized = first.as_dict()

    assert first == second
    assert first.revision_id == second.revision_id
    assert first.declaration_revision_id == declaration.revision_id
    assert first.material_id == declaration.material_id
    assert serialized["provenance"] == declaration.as_dict()["provenance"]
    assert serialized["recycled_content_certified"] is False
    assert serialized["environmental_performance_verified"] is False
    assert serialized["regulatory_approval"] is False
    assert serialized["physical_or_environmental_claim"] is False


def test_visual_variant_rejects_changed_model_or_component_provenance() -> None:
    declaration = _declaration()
    with pytest.raises(PCRMetadataError, match="provenance_mismatch"):
        create_pcr_visual_variant(
            declaration,
            variant_id="variant-one",
            display_name="Variant one",
            appearance_color_rgba=(0.2, 0.3, 0.4, 1.0),
            design_model_revision_id="design-model:other",
            component_id="component-bottle-body",
        )


@pytest.mark.parametrize(
    "color",
    [(0.2, 0.3, 0.4), (0.2, 0.3, 0.4, 1.1), (float("nan"), 0.3, 0.4, 1.0)],
)
def test_visual_variant_rejects_invalid_color(color: tuple[float, ...]) -> None:
    with pytest.raises(PCRMetadataError, match="color_invalid"):
        create_pcr_visual_variant(
            _declaration(),
            variant_id="variant-one",
            display_name="Variant one",
            appearance_color_rgba=color,
            design_model_revision_id="design-model:revision-42",
            component_id="component-bottle-body",
        )
