"""User supplied PCR declarations and appearance variants, never certification."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum

PCR_DECLARATION_CONTRACT = "packlab.pcr-declaration.v1"
PCR_VISUAL_VARIANT_CONTRACT = "packlab.pcr-visual-variant.v1"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,255}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PCRMetadataError(ValueError):
    """Raised when PCR declaration or appearance metadata is invalid."""


class PCRDeclarationStatus(StrEnum):
    DESIGN_INTENT = "DESIGN_INTENT"
    DECLARED = "DECLARED"
    VERIFIED_EXTERNAL_REFERENCE = "VERIFIED_EXTERNAL_REFERENCE"


@dataclass(frozen=True, slots=True)
class ExternalAuthorityReference:
    """Explicit pointer to external material evidence; PackLab does not verify it."""

    authority_name: str
    reference_id: str
    document_sha256: str

    def __post_init__(self) -> None:
        _bounded_text(self.authority_name, "authority_name", 120)
        _identifier(self.reference_id, "authority_reference_id")
        if not isinstance(self.document_sha256, str) or not _SHA256.fullmatch(self.document_sha256):
            raise PCRMetadataError("pcr_authority_document_digest_invalid")

    def as_dict(self) -> dict[str, str]:
        return {
            "authority_name": self.authority_name,
            "reference_id": self.reference_id,
            "document_sha256": self.document_sha256,
        }


@dataclass(frozen=True, slots=True)
class PCRDeclarationRevision:
    revision_id: str
    material_id: str
    recycled_content_percentage: float
    status: PCRDeclarationStatus
    design_model_revision_id: str
    component_id: str
    external_authority: ExternalAuthorityReference | None = None
    contract: str = PCR_DECLARATION_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != PCR_DECLARATION_CONTRACT:
            raise PCRMetadataError("pcr_declaration_contract_invalid")
        _identifier(self.material_id, "material_id")
        percentage = _percentage(self.recycled_content_percentage)
        object.__setattr__(self, "recycled_content_percentage", percentage)
        if not isinstance(self.status, PCRDeclarationStatus):
            raise PCRMetadataError("pcr_declaration_status_invalid")
        _identifier(self.design_model_revision_id, "design_model_revision_id")
        _identifier(self.component_id, "component_id")
        if self.status is PCRDeclarationStatus.VERIFIED_EXTERNAL_REFERENCE:
            if not isinstance(self.external_authority, ExternalAuthorityReference):
                raise PCRMetadataError("pcr_external_authority_reference_required")
        elif self.external_authority is not None:
            raise PCRMetadataError("pcr_external_authority_status_mismatch")
        expected_id = "pcr-declaration:" + _digest(_declaration_identity(self))
        if self.revision_id != expected_id:
            raise PCRMetadataError("pcr_declaration_identity_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "revision_id": self.revision_id,
            "material_id": self.material_id,
            "recycled_content_percentage": self.recycled_content_percentage,
            "status": self.status.value,
            "external_authority_reference": (
                self.external_authority.as_dict() if self.external_authority else None
            ),
            "provenance": {
                "design_model_revision_id": self.design_model_revision_id,
                "component_id": self.component_id,
            },
            "authority_semantics": "USER_SUPPLIED_OR_DESIGN_INTENT_METADATA_ONLY",
            "external_reference_independently_verified_by_packlab": False,
            "recycled_content_certified": False,
            "environmental_performance_verified": False,
            "regulatory_approval": False,
            "physical_or_environmental_claim": False,
        }


@dataclass(frozen=True, slots=True)
class PCRVisualVariantRevision:
    revision_id: str
    declaration_revision_id: str
    material_id: str
    variant_id: str
    display_name: str
    appearance_color_rgba: tuple[float, float, float, float]
    design_model_revision_id: str
    component_id: str
    contract: str = PCR_VISUAL_VARIANT_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != PCR_VISUAL_VARIANT_CONTRACT:
            raise PCRMetadataError("pcr_visual_variant_contract_invalid")
        _identifier(self.declaration_revision_id, "declaration_revision_id")
        _identifier(self.material_id, "material_id")
        _identifier(self.variant_id, "variant_id")
        _bounded_text(self.display_name, "variant_display_name", 80)
        if (
            not isinstance(self.appearance_color_rgba, tuple)
            or len(self.appearance_color_rgba) != 4
        ):
            raise PCRMetadataError("pcr_visual_variant_color_invalid")
        object.__setattr__(
            self,
            "appearance_color_rgba",
            tuple(_unit_interval(value, "variant_color") for value in self.appearance_color_rgba),
        )
        _identifier(self.design_model_revision_id, "design_model_revision_id")
        _identifier(self.component_id, "component_id")
        if self.revision_id != "pcr-visual-variant:" + _digest(_variant_identity(self)):
            raise PCRMetadataError("pcr_visual_variant_identity_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "revision_id": self.revision_id,
            "declaration_revision_id": self.declaration_revision_id,
            "material_id": self.material_id,
            "variant_id": self.variant_id,
            "display_name": self.display_name,
            "appearance_metadata": {
                "color_rgba": list(self.appearance_color_rgba),
                "coordinate_unit": "unitless_visual_metadata",
            },
            "provenance": {
                "design_model_revision_id": self.design_model_revision_id,
                "component_id": self.component_id,
            },
            "authority_semantics": "NON_CERTIFIED_VISUAL_VARIANT",
            "recycled_content_certified": False,
            "environmental_performance_verified": False,
            "regulatory_approval": False,
            "physical_or_environmental_claim": False,
        }


def create_pcr_declaration(
    *,
    material_id: str,
    recycled_content_percentage: float,
    status: PCRDeclarationStatus,
    design_model_revision_id: str,
    component_id: str,
    external_authority: ExternalAuthorityReference | None = None,
) -> PCRDeclarationRevision:
    """Create deterministic user-supplied metadata; never assert certification."""
    if not isinstance(status, PCRDeclarationStatus):
        raise PCRMetadataError("pcr_declaration_status_invalid")
    if external_authority is not None and not isinstance(
        external_authority, ExternalAuthorityReference
    ):
        raise PCRMetadataError("pcr_external_authority_reference_invalid")
    _identifier(material_id, "material_id")
    _identifier(design_model_revision_id, "design_model_revision_id")
    _identifier(component_id, "component_id")
    percentage = _percentage(recycled_content_percentage)
    values: dict[str, object] = {
        "contract": PCR_DECLARATION_CONTRACT,
        "material_id": material_id,
        "recycled_content_percentage": percentage,
        "status": status.value,
        "design_model_revision_id": design_model_revision_id,
        "component_id": component_id,
        "external_authority": external_authority.as_dict() if external_authority else None,
    }
    return PCRDeclarationRevision(
        revision_id="pcr-declaration:" + _digest(values),
        material_id=material_id,
        recycled_content_percentage=percentage,
        status=status,
        design_model_revision_id=design_model_revision_id,
        component_id=component_id,
        external_authority=external_authority,
    )


def create_pcr_visual_variant(
    declaration: PCRDeclarationRevision,
    *,
    variant_id: str,
    display_name: str,
    appearance_color_rgba: tuple[float, float, float, float],
    design_model_revision_id: str,
    component_id: str,
) -> PCRVisualVariantRevision:
    """Create a deterministic swatch variant pinned to a declaration and exact source."""
    if not isinstance(declaration, PCRDeclarationRevision):
        raise PCRMetadataError("pcr_declaration_required")
    if (
        declaration.design_model_revision_id != design_model_revision_id
        or declaration.component_id != component_id
    ):
        raise PCRMetadataError("pcr_visual_variant_provenance_mismatch")
    _identifier(variant_id, "variant_id")
    _bounded_text(display_name, "variant_display_name", 80)
    values: dict[str, object] = {
        "contract": PCR_VISUAL_VARIANT_CONTRACT,
        "declaration_revision_id": declaration.revision_id,
        "material_id": declaration.material_id,
        "variant_id": variant_id,
        "display_name": display_name,
        "appearance_color_rgba": [
            _unit_interval(value, "variant_color") for value in appearance_color_rgba
        ]
        if isinstance(appearance_color_rgba, tuple) and len(appearance_color_rgba) == 4
        else None,
        "design_model_revision_id": design_model_revision_id,
        "component_id": component_id,
    }
    if values["appearance_color_rgba"] is None:
        raise PCRMetadataError("pcr_visual_variant_color_invalid")
    return PCRVisualVariantRevision(
        revision_id="pcr-visual-variant:" + _digest(values),
        declaration_revision_id=declaration.revision_id,
        material_id=declaration.material_id,
        variant_id=variant_id,
        display_name=display_name,
        appearance_color_rgba=tuple(values["appearance_color_rgba"]),  # type: ignore[arg-type]
        design_model_revision_id=design_model_revision_id,
        component_id=component_id,
    )


def _declaration_identity(declaration: PCRDeclarationRevision) -> dict[str, object]:
    return {
        "contract": declaration.contract,
        "material_id": declaration.material_id,
        "recycled_content_percentage": declaration.recycled_content_percentage,
        "status": declaration.status.value,
        "design_model_revision_id": declaration.design_model_revision_id,
        "component_id": declaration.component_id,
        "external_authority": (
            declaration.external_authority.as_dict() if declaration.external_authority else None
        ),
    }


def _variant_identity(variant: PCRVisualVariantRevision) -> dict[str, object]:
    return {
        "contract": variant.contract,
        "declaration_revision_id": variant.declaration_revision_id,
        "material_id": variant.material_id,
        "variant_id": variant.variant_id,
        "display_name": variant.display_name,
        "appearance_color_rgba": list(variant.appearance_color_rgba),
        "design_model_revision_id": variant.design_model_revision_id,
        "component_id": variant.component_id,
    }


def _percentage(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PCRMetadataError("pcr_percentage_invalid")
    try:
        normalized = float(value)
    except OverflowError as error:
        raise PCRMetadataError("pcr_percentage_invalid") from error
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise PCRMetadataError("pcr_percentage_invalid")
    return 0.0 if normalized == 0.0 else normalized


def _unit_interval(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PCRMetadataError(f"pcr_{name}_invalid")
    try:
        normalized = float(value)
    except OverflowError as error:
        raise PCRMetadataError(f"pcr_{name}_invalid") from error
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise PCRMetadataError(f"pcr_{name}_invalid")
    return 0.0 if normalized == 0.0 else normalized


def _identifier(value: object, name: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise PCRMetadataError(f"pcr_{name}_invalid")


def _bounded_text(value: object, name: str, maximum: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise PCRMetadataError(f"pcr_{name}_invalid")


def _digest(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "ExternalAuthorityReference",
    "PCRDeclarationRevision",
    "PCRDeclarationStatus",
    "PCRMetadataError",
    "PCRVisualVariantRevision",
    "create_pcr_declaration",
    "create_pcr_visual_variant",
]
