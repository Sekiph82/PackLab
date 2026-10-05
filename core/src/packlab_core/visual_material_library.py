"""Immutable visual-only material-library metadata; no certified resin claims."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum

VISUAL_MATERIAL_LIBRARY_CONTRACT = "packlab.visual-material-library.v1"
VISUAL_MATERIAL_CONTRACT = "packlab.visual-material.v1"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,255}$")


class VisualMaterialLibraryError(ValueError):
    """Raised when visual material metadata is invalid or ambiguous."""


class MaterialFamily(StrEnum):
    HDPE = "HDPE"
    PET = "PET"
    PP = "PP"
    OTHER = "OTHER"


class MaterialSourceClass(StrEnum):
    USER_AUTHORED_VISUAL = "USER_AUTHORED_VISUAL"
    REFERENCE_VISUAL_ONLY = "REFERENCE_VISUAL_ONLY"


@dataclass(frozen=True, slots=True)
class VisualMaterialRecord:
    material_id: str
    family: MaterialFamily
    display_name: str
    base_color_rgba: tuple[float, float, float, float]
    metallic_factor: float
    roughness_factor: float
    source_classification: MaterialSourceClass
    other_family_label: str | None = None
    pcr_visual_reference_fraction: float | None = None
    source_reference_id: str | None = None
    source_design_model_revision_id: str | None = None
    source_component_id: str | None = None
    alpha_mode: str = "OPAQUE"
    contract: str = VISUAL_MATERIAL_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != VISUAL_MATERIAL_CONTRACT:
            raise VisualMaterialLibraryError("visual_material_contract_invalid")
        if not isinstance(self.material_id, str) or not _IDENTIFIER.fullmatch(self.material_id):
            raise VisualMaterialLibraryError("visual_material_id_invalid")
        if not isinstance(self.family, MaterialFamily):
            raise VisualMaterialLibraryError("visual_material_family_invalid")
        _bounded_text(self.display_name, "display_name", 80)
        if not isinstance(self.base_color_rgba, tuple) or len(self.base_color_rgba) != 4:
            raise VisualMaterialLibraryError("visual_material_base_color_invalid")
        object.__setattr__(
            self,
            "base_color_rgba",
            tuple(_unit_interval(channel, "base_color") for channel in self.base_color_rgba),
        )
        object.__setattr__(
            self, "metallic_factor", _unit_interval(self.metallic_factor, "metallic_factor")
        )
        object.__setattr__(
            self, "roughness_factor", _unit_interval(self.roughness_factor, "roughness_factor")
        )
        if self.pcr_visual_reference_fraction is not None:
            object.__setattr__(
                self,
                "pcr_visual_reference_fraction",
                _unit_interval(self.pcr_visual_reference_fraction, "pcr_visual_reference_fraction"),
            )
        if self.family is MaterialFamily.OTHER:
            _bounded_text(self.other_family_label, "other_family_label", 80)
        elif self.other_family_label is not None:
            raise VisualMaterialLibraryError("visual_material_other_label_wrong_family")
        if not isinstance(self.source_classification, MaterialSourceClass):
            raise VisualMaterialLibraryError("visual_material_source_classification_invalid")
        if self.source_reference_id is not None and (
            not isinstance(self.source_reference_id, str)
            or not _IDENTIFIER.fullmatch(self.source_reference_id)
        ):
            raise VisualMaterialLibraryError("visual_material_source_reference_id_invalid")
        model_id, component_id = (
            self.source_design_model_revision_id,
            self.source_component_id,
        )
        if (model_id is None) != (component_id is None):
            raise VisualMaterialLibraryError(
                "visual_material_model_component_provenance_incomplete"
            )
        if model_id is not None and (
            not isinstance(model_id, str)
            or not _IDENTIFIER.fullmatch(model_id)
            or not isinstance(component_id, str)
            or not _IDENTIFIER.fullmatch(component_id)
        ):
            raise VisualMaterialLibraryError("visual_material_model_component_provenance_invalid")
        if not isinstance(self.alpha_mode, str) or self.alpha_mode not in {
            "OPAQUE",
            "BLEND",
            "MASK",
        }:
            raise VisualMaterialLibraryError("visual_material_alpha_mode_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "material_id": self.material_id,
            "family": self.family.value,
            "family_label": self.other_family_label or self.family.value,
            "display_name": self.display_name,
            "display_metadata": {"base_color_rgba": list(self.base_color_rgba)},
            "pbr_visual_reference": {
                "metallic_factor": self.metallic_factor,
                "roughness_factor": self.roughness_factor,
                "alpha_mode": self.alpha_mode,
                "coordinate_unit": "unitless_visual_metadata",
            },
            "pcr_visual_reference_fraction": self.pcr_visual_reference_fraction,
            "provenance": {
                "source_classification": self.source_classification.value,
                "source_reference_id": self.source_reference_id,
                "source_design_model_revision_id": self.source_design_model_revision_id,
                "source_component_id": self.source_component_id,
            },
            "authority_semantics": "NON_CERTIFIED_VISUAL_REFERENCE",
            "resin_identity_verified": False,
            "material_certified": False,
            "recycled_content_certified": False,
            "food_contact_approved": False,
            "barrier_properties_verified": False,
            "mechanical_properties_verified": False,
            "regulatory_approval": False,
            "physical_or_regulatory_claim": False,
        }


@dataclass(frozen=True, slots=True)
class VisualMaterialLibraryRevision:
    revision_id: str
    materials: tuple[VisualMaterialRecord, ...]
    contract: str = VISUAL_MATERIAL_LIBRARY_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != VISUAL_MATERIAL_LIBRARY_CONTRACT
            or not isinstance(self.materials, tuple)
            or not self.materials
            or any(not isinstance(item, VisualMaterialRecord) for item in self.materials)
        ):
            raise VisualMaterialLibraryError("visual_material_library_invalid")
        ids = tuple(item.material_id for item in self.materials)
        if len(ids) != len(set(ids)):
            raise VisualMaterialLibraryError("visual_material_id_duplicate")
        if ids != tuple(sorted(ids)):
            raise VisualMaterialLibraryError("visual_material_library_order_invalid")
        if self.revision_id != "visual-material-library:" + _digest(
            _library_identity(self.materials)
        ):
            raise VisualMaterialLibraryError("visual_material_library_identity_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "revision_id": self.revision_id,
            "authority_semantics": "NON_CERTIFIED_VISUAL_REFERENCE",
            "materials": [item.as_dict() for item in self.materials],
            "physical_or_regulatory_claim": False,
        }


def create_visual_material_library(
    materials: tuple[VisualMaterialRecord, ...],
) -> VisualMaterialLibraryRevision:
    """Build a deterministic immutable library, canonicalized by stable material ID."""
    if not isinstance(materials, tuple) or not materials:
        raise VisualMaterialLibraryError("visual_material_library_requires_nonempty_tuple")
    if any(not isinstance(item, VisualMaterialRecord) for item in materials):
        raise VisualMaterialLibraryError("visual_material_record_required")
    ids = tuple(item.material_id for item in materials)
    if len(ids) != len(set(ids)):
        raise VisualMaterialLibraryError("visual_material_id_duplicate")
    canonical = tuple(sorted(materials, key=lambda item: item.material_id))
    return VisualMaterialLibraryRevision(
        revision_id="visual-material-library:" + _digest(_library_identity(canonical)),
        materials=canonical,
    )


def create_starter_visual_material_library() -> VisualMaterialLibraryRevision:
    """Return generic display presets for common families, not measured resin data."""
    source = MaterialSourceClass.USER_AUTHORED_VISUAL
    return create_visual_material_library(
        (
            VisualMaterialRecord(
                "material-hdpe-visual",
                MaterialFamily.HDPE,
                "HDPE visual reference",
                (0.82, 0.86, 0.88, 1.0),
                0.0,
                0.42,
                source,
            ),
            VisualMaterialRecord(
                "material-pet-visual",
                MaterialFamily.PET,
                "PET visual reference",
                (0.78, 0.9, 0.86, 0.32),
                0.0,
                0.18,
                source,
                alpha_mode="BLEND",
            ),
            VisualMaterialRecord(
                "material-pp-visual",
                MaterialFamily.PP,
                "PP visual reference",
                (0.88, 0.86, 0.8, 1.0),
                0.0,
                0.38,
                source,
            ),
            VisualMaterialRecord(
                "material-other-visual",
                MaterialFamily.OTHER,
                "Other packaging visual reference",
                (0.75, 0.75, 0.75, 1.0),
                0.0,
                0.5,
                source,
                other_family_label="Other packaging material",
            ),
        )
    )


def _bounded_text(value: object, name: str, maximum: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise VisualMaterialLibraryError(f"visual_material_{name}_invalid")


def _unit_interval(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise VisualMaterialLibraryError(f"visual_material_{name}_invalid")
    try:
        normalized = float(value)
    except OverflowError as error:
        raise VisualMaterialLibraryError(f"visual_material_{name}_invalid") from error
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise VisualMaterialLibraryError(f"visual_material_{name}_invalid")
    return 0.0 if normalized == 0.0 else normalized


def _library_identity(materials: tuple[VisualMaterialRecord, ...]) -> dict[str, object]:
    return {
        "contract": VISUAL_MATERIAL_LIBRARY_CONTRACT,
        "materials": [item.as_dict() for item in materials],
    }


def _digest(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "MaterialFamily",
    "MaterialSourceClass",
    "VISUAL_MATERIAL_CONTRACT",
    "VISUAL_MATERIAL_LIBRARY_CONTRACT",
    "VisualMaterialLibraryError",
    "VisualMaterialLibraryRevision",
    "VisualMaterialRecord",
    "create_starter_visual_material_library",
    "create_visual_material_library",
]
