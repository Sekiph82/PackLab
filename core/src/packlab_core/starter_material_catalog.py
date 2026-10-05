"""Deterministic generic packaging-material render presets."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .pbr_visual_parameters import NormalDetailReference
from .visual_material_library import (
    MaterialFamily,
    MaterialSourceClass,
    VisualMaterialLibraryRevision,
    VisualMaterialRecord,
    create_visual_material_library,
)

STARTER_MATERIAL_CATALOG_CONTRACT = "packlab.starter-material-catalog.v1"
STARTER_MATERIAL_PRESET_CONTRACT = "packlab.starter-material-preset.v1"


class StarterMaterialCatalogError(ValueError):
    """Raised when a curated visual starter-material preset is inconsistent."""


@dataclass(frozen=True, slots=True)
class StarterMaterialPresetRevision:
    revision_id: str
    material: VisualMaterialRecord
    transmission_factor: float
    ior: float
    normal_detail: NormalDetailReference | None = None
    contract: str = STARTER_MATERIAL_PRESET_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != STARTER_MATERIAL_PRESET_CONTRACT
            or not isinstance(self.material, VisualMaterialRecord)
            or not _unit_interval(self.transmission_factor)
            or not _finite_range(self.ior, 1.0, 3.0)
            or (
                self.normal_detail is not None
                and not isinstance(self.normal_detail, NormalDetailReference)
            )
        ):
            raise StarterMaterialCatalogError("starter_material_preset_invalid")
        opacity = self.material.base_color_rgba[3]
        if opacity < 1.0 and self.transmission_factor > 0.0:
            raise StarterMaterialCatalogError("starter_material_opacity_transmission_conflict")
        if self.transmission_factor > 0.0 and self.material.alpha_mode != "OPAQUE":
            raise StarterMaterialCatalogError("starter_material_transmission_alpha_mode_conflict")
        if self.material.alpha_mode == "BLEND" and opacity >= 1.0:
            raise StarterMaterialCatalogError("starter_material_blend_opacity_conflict")
        if self.revision_id != "starter-material-preset:" + _digest(_preset_identity(self)):
            raise StarterMaterialCatalogError("starter_material_preset_identity_mismatch")

    @property
    def opacity_factor(self) -> float:
        return self.material.base_color_rgba[3]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "revision_id": self.revision_id,
            "material": self.material.as_dict(),
            "pbr_visual_parameters": {
                "base_color_rgb": list(self.material.base_color_rgba[:3]),
                "base_color_alpha": self.opacity_factor,
                "metallic_factor": self.material.metallic_factor,
                "roughness_factor": self.material.roughness_factor,
                "transmission_factor": self.transmission_factor,
                "opacity_factor": self.opacity_factor,
                "alpha_mode": self.material.alpha_mode,
                "ior": self.ior,
                "normal_detail": self.normal_detail.as_dict() if self.normal_detail else None,
            },
            "authority_semantics": "NON_CERTIFIED_VISUAL_REFERENCE",
            "values_are_measured_or_certified_specifications": False,
            "physical_performance_inferred": False,
        }


@dataclass(frozen=True, slots=True)
class StarterMaterialCatalogRevision:
    revision_id: str
    entries: tuple[StarterMaterialPresetRevision, ...]
    library: VisualMaterialLibraryRevision
    contract: str = STARTER_MATERIAL_CATALOG_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != STARTER_MATERIAL_CATALOG_CONTRACT
            or not isinstance(self.entries, tuple)
            or len(self.entries) != 5
            or any(not isinstance(item, StarterMaterialPresetRevision) for item in self.entries)
            or not isinstance(self.library, VisualMaterialLibraryRevision)
            or tuple(item.material.material_id for item in self.entries)
            != tuple(sorted(item.material.material_id for item in self.entries))
            or tuple(item.material for item in self.entries) != self.library.materials
            or self.revision_id != "starter-material-catalog:" + _digest(_catalog_identity(self))
        ):
            raise StarterMaterialCatalogError("starter_material_catalog_invalid")
        ids = tuple(item.material.material_id for item in self.entries)
        if len(ids) != len(set(ids)):
            raise StarterMaterialCatalogError("starter_material_catalog_duplicate_id")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "revision_id": self.revision_id,
            "authority_semantics": "NON_CERTIFIED_VISUAL_REFERENCE",
            "material_library_revision_id": self.library.revision_id,
            "entries": [item.as_dict() for item in self.entries],
            "values_are_measured_or_certified_specifications": False,
            "physical_performance_inferred": False,
            "material_certified": False,
            "recycled_content_certified": False,
            "regulatory_approval": False,
        }

    def canonical_bytes(self) -> bytes:
        return (
            json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("utf-8")


def create_starter_packaging_material_catalog() -> StarterMaterialCatalogRevision:
    """Create five deterministic authored appearance presets, not resin specifications."""
    authored = MaterialSourceClass.USER_AUTHORED_VISUAL
    entries: tuple[StarterMaterialPresetRevision, ...] = (
        _preset(
            "material-hdpe-natural-visual",
            MaterialFamily.HDPE,
            "Natural HDPE visual reference",
            (0.82, 0.79, 0.68, 1.0),
            roughness=0.5,
            transmission=0.0,
            ior=1.5,
            source=authored,
        ),
        _preset(
            "material-hdpe-white-visual",
            MaterialFamily.HDPE,
            "White HDPE visual reference",
            (0.94, 0.94, 0.91, 1.0),
            roughness=0.46,
            transmission=0.0,
            ior=1.5,
            source=authored,
        ),
        _preset(
            "material-pet-clear-visual",
            MaterialFamily.PET,
            "Clear PET visual reference",
            (0.78, 0.92, 0.87, 1.0),
            roughness=0.12,
            transmission=0.9,
            ior=1.55,
            source=authored,
        ),
        _preset(
            "material-pet-colored-visual",
            MaterialFamily.PET,
            "Colored PET visual reference",
            (0.24, 0.57, 0.68, 0.82),
            roughness=0.2,
            transmission=0.0,
            ior=1.55,
            source=authored,
            alpha_mode="BLEND",
        ),
        _preset(
            "material-pp-cap-visual",
            MaterialFamily.PP,
            "PP cap visual reference",
            (0.3, 0.34, 0.38, 1.0),
            roughness=0.4,
            transmission=0.0,
            ior=1.5,
            source=authored,
        ),
    )
    entries = tuple(sorted(entries, key=lambda item: item.material.material_id))
    library = create_visual_material_library(tuple(item.material for item in entries))
    provisional: dict[str, object] = {
        "contract": STARTER_MATERIAL_CATALOG_CONTRACT,
        "library_revision_id": library.revision_id,
        "entry_revision_ids": [item.revision_id for item in entries],
    }
    return StarterMaterialCatalogRevision(
        revision_id="starter-material-catalog:" + _digest(provisional),
        entries=entries,
        library=library,
    )


def _preset(
    material_id: str,
    family: MaterialFamily,
    display_name: str,
    color: tuple[float, float, float, float],
    *,
    roughness: float,
    transmission: float,
    ior: float,
    source: MaterialSourceClass,
    alpha_mode: str = "OPAQUE",
) -> StarterMaterialPresetRevision:
    material = VisualMaterialRecord(
        material_id=material_id,
        family=family,
        display_name=display_name,
        base_color_rgba=color,
        metallic_factor=0.0,
        roughness_factor=roughness,
        source_classification=source,
        alpha_mode=alpha_mode,
    )
    values: dict[str, object] = {
        "contract": STARTER_MATERIAL_PRESET_CONTRACT,
        "material": material.as_dict(),
        "transmission_factor": transmission,
        "ior": ior,
        "normal_detail_revision_id": None,
    }
    return StarterMaterialPresetRevision(
        revision_id="starter-material-preset:" + _digest(values),
        material=material,
        transmission_factor=transmission,
        ior=ior,
    )


def _preset_identity(preset: StarterMaterialPresetRevision) -> dict[str, object]:
    return {
        "contract": preset.contract,
        "material": preset.material.as_dict(),
        "transmission_factor": preset.transmission_factor,
        "ior": preset.ior,
        "normal_detail_revision_id": (
            preset.normal_detail.revision_id if preset.normal_detail is not None else None
        ),
    }


def _catalog_identity(catalog: StarterMaterialCatalogRevision) -> dict[str, object]:
    return {
        "contract": catalog.contract,
        "library_revision_id": catalog.library.revision_id,
        "entry_revision_ids": [item.revision_id for item in catalog.entries],
    }


def _unit_interval(value: object) -> bool:
    return _finite_range(value, 0.0, 1.0)


def _finite_range(value: object, minimum: float, maximum: float) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        number = float(value)
    except OverflowError:
        return False
    return math.isfinite(number) and minimum <= number <= maximum


def _digest(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "STARTER_MATERIAL_CATALOG_CONTRACT",
    "STARTER_MATERIAL_PRESET_CONTRACT",
    "StarterMaterialCatalogError",
    "StarterMaterialCatalogRevision",
    "StarterMaterialPresetRevision",
    "create_starter_packaging_material_catalog",
]
