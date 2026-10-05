"""Portable, immutable metadata contract for Packaging Library assets."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum

PACKAGING_ASSET_CONTRACT = "packlab.packaging-asset.v1"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_ABSOLUTE_PATH_OR_URI = re.compile(
    r"^(?:[A-Za-z]:[\\/]|[\\/]{1,2}|[A-Za-z][A-Za-z0-9+.-]*://|file:)", re.IGNORECASE
)
_REVISION_PREFIX = "packaging-asset:"
_MAX_AMOUNT = 1_000_000.0


class PackagingAssetError(ValueError):
    """Raised when a Packaging Asset violates the portable library contract."""


class PackagingFamily(StrEnum):
    BOTTLE = "BOTTLE"
    JAR = "JAR"
    TUBE = "TUBE"
    POUCH = "POUCH"
    CAN = "CAN"
    CARTON = "CARTON"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class BaseMaterial(StrEnum):
    HDPE = "HDPE"
    LDPE = "LDPE"
    PET = "PET"
    PP = "PP"
    GLASS = "GLASS"
    ALUMINUM = "ALUMINUM"
    PAPERBOARD = "PAPERBOARD"
    MULTILAYER = "MULTILAYER"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class ClosureType(StrEnum):
    SCREW_CAP = "SCREW_CAP"
    FLIP_TOP = "FLIP_TOP"
    PUMP = "PUMP"
    TRIGGER = "TRIGGER"
    DROPPER = "DROPPER"
    NONE = "NONE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class AssetStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    RETIRED = "RETIRED"


class MeasurementUnit(StrEnum):
    MILLILITER = "mL"
    LITER = "L"
    GRAM = "g"
    KILOGRAM = "kg"
    MILLIMETER = "mm"
    CENTIMETER = "cm"


@dataclass(frozen=True, slots=True)
class PackagingMeasurement:
    """A bounded value with an explicit unit; absent measurements use ``None``."""

    value: float
    unit: MeasurementUnit

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise PackagingAssetError("packaging_measurement_value_invalid")
        try:
            normalized = float(self.value)
        except OverflowError as error:
            raise PackagingAssetError("packaging_measurement_value_invalid") from error
        if not math.isfinite(normalized) or not 0.0 < normalized <= _MAX_AMOUNT:
            raise PackagingAssetError("packaging_measurement_value_invalid")
        if not isinstance(self.unit, MeasurementUnit):
            raise PackagingAssetError("packaging_measurement_unit_invalid")
        object.__setattr__(self, "value", normalized)

    def as_dict(self) -> dict[str, object]:
        return {"value": self.value, "unit": self.unit.value}


@dataclass(frozen=True, slots=True)
class PackagingAsset:
    """Immutable source-neutral metadata; no project paths or source artifact bytes."""

    asset_id: str
    display_name: str
    family: PackagingFamily
    nominal_volume: PackagingMeasurement | None = None
    supplier_id: str | None = None
    supplier_name: str | None = None
    base_material: BaseMaterial = BaseMaterial.UNKNOWN
    other_family_label: str | None = None
    other_material_label: str | None = None
    empty_package_weight: PackagingMeasurement | None = None
    overall_height: PackagingMeasurement | None = None
    body_diameter: PackagingMeasurement | None = None
    neck_finish: str | None = None
    neck_finish_diameter: PackagingMeasurement | None = None
    closure_type: ClosureType = ClosureType.UNKNOWN
    closure_description: str | None = None
    status: AssetStatus = AssetStatus.UNKNOWN
    contract: str = PACKAGING_ASSET_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != PACKAGING_ASSET_CONTRACT:
            raise PackagingAssetError("packaging_asset_contract_invalid")
        _identifier(self.asset_id, "asset_id")
        _bounded_text(self.display_name, "display_name", 120)
        if not isinstance(self.family, PackagingFamily):
            raise PackagingAssetError("packaging_asset_family_invalid")
        if not isinstance(self.base_material, BaseMaterial):
            raise PackagingAssetError("packaging_asset_base_material_invalid")
        if not isinstance(self.closure_type, ClosureType):
            raise PackagingAssetError("packaging_asset_closure_type_invalid")
        if not isinstance(self.status, AssetStatus):
            raise PackagingAssetError("packaging_asset_status_invalid")
        if self.family is PackagingFamily.OTHER:
            _bounded_text(self.other_family_label, "other_family_label", 80)
        elif self.other_family_label is not None:
            raise PackagingAssetError("packaging_asset_other_family_label_wrong_family")
        if self.base_material is BaseMaterial.OTHER:
            _bounded_text(self.other_material_label, "other_material_label", 80)
        elif self.other_material_label is not None:
            raise PackagingAssetError("packaging_asset_other_material_label_wrong_family")

        if (self.supplier_id is None) != (self.supplier_name is None):
            raise PackagingAssetError("packaging_asset_supplier_identity_incomplete")
        if self.supplier_id is not None:
            _identifier(self.supplier_id, "supplier_id")
            _bounded_text(self.supplier_name, "supplier_name", 120)

        for field_name, value in (
            ("neck_finish", self.neck_finish),
            ("closure_description", self.closure_description),
        ):
            if value is not None:
                _bounded_text(value, field_name, 80)

        for field_name, measurement, allowed_units in (
            (
                "nominal_volume",
                self.nominal_volume,
                {MeasurementUnit.MILLILITER, MeasurementUnit.LITER},
            ),
            (
                "empty_package_weight",
                self.empty_package_weight,
                {MeasurementUnit.GRAM, MeasurementUnit.KILOGRAM},
            ),
            (
                "overall_height",
                self.overall_height,
                {MeasurementUnit.MILLIMETER, MeasurementUnit.CENTIMETER},
            ),
            (
                "body_diameter",
                self.body_diameter,
                {MeasurementUnit.MILLIMETER, MeasurementUnit.CENTIMETER},
            ),
            (
                "neck_finish_diameter",
                self.neck_finish_diameter,
                {MeasurementUnit.MILLIMETER, MeasurementUnit.CENTIMETER},
            ),
        ):
            if measurement is not None and (
                not isinstance(measurement, PackagingMeasurement)
                or measurement.unit not in allowed_units
            ):
                raise PackagingAssetError(f"packaging_asset_{field_name}_unit_invalid")

    @property
    def revision_id(self) -> str:
        """Content-derived revision; independent of filesystem and runtime location."""
        return _REVISION_PREFIX + hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()

    @property
    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "asset_id": self.asset_id,
            "display_name": self.display_name,
            "family": self.family.value,
            "other_family_label": self.other_family_label,
            "nominal_volume": _measurement_dict(self.nominal_volume),
            "supplier": {"supplier_id": self.supplier_id, "name": self.supplier_name},
            "base_material": self.base_material.value,
            "other_material_label": self.other_material_label,
            "empty_package_weight": _measurement_dict(self.empty_package_weight),
            "dimensions": {
                "overall_height": _measurement_dict(self.overall_height),
                "body_diameter": _measurement_dict(self.body_diameter),
            },
            "neck_closure": {
                "neck_finish": self.neck_finish,
                "neck_finish_diameter": _measurement_dict(self.neck_finish_diameter),
                "closure_type": self.closure_type.value,
                "closure_description": self.closure_description,
            },
            "status": self.status.value,
            "authority_semantics": "PACKAGING_METADATA_ONLY",
            "supplier_certification_inferred": False,
            "physical_accuracy_verified": False,
            "manufacturing_authorized": False,
        }


def _identifier(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise PackagingAssetError(f"packaging_asset_{field_name}_invalid")


def _bounded_text(value: object, field_name: str, maximum: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or _ABSOLUTE_PATH_OR_URI.match(value.strip()) is not None
    ):
        raise PackagingAssetError(f"packaging_asset_{field_name}_invalid")


def _measurement_dict(value: PackagingMeasurement | None) -> dict[str, object] | None:
    return value.as_dict() if value is not None else None


__all__ = [
    "AssetStatus",
    "BaseMaterial",
    "ClosureType",
    "MeasurementUnit",
    "PackagingAsset",
    "PackagingAssetError",
    "PackagingFamily",
    "PackagingMeasurement",
    "PACKAGING_ASSET_CONTRACT",
]
