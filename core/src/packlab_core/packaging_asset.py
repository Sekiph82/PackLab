"""Portable, immutable metadata contract for Packaging Library assets."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, cast

from .reconstruction import ScaleState

PACKAGING_ASSET_CONTRACT = "packlab.packaging-asset.v1"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
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


class ProvenanceClass(StrEnum):
    SUPPLIER_FACT = "SUPPLIER_FACT"
    PACKLAB_ESTIMATE = "PACKLAB_ESTIMATE"
    USER_DECLARED = "USER_DECLARED"
    UNKNOWN = "UNKNOWN"


_PROVENANCE_FIELDS = frozenset(
    {
        "display_name",
        "family",
        "nominal_volume",
        "supplier_id",
        "supplier_name",
        "base_material",
        "other_family_label",
        "other_material_label",
        "empty_package_weight",
        "overall_height",
        "body_diameter",
        "neck_finish",
        "neck_finish_diameter",
        "closure_type",
        "closure_description",
        "status",
    }
)
_EDITABLE_FIELDS = _PROVENANCE_FIELDS


@dataclass(frozen=True, slots=True)
class FieldProvenance:
    """Authority metadata for exactly one Packaging Asset field."""

    field_name: str
    classification: ProvenanceClass
    source_reference_id: str | None = None
    source_description: str | None = None
    method_id: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.field_name, str) or self.field_name not in _PROVENANCE_FIELDS:
            raise PackagingAssetError("packaging_asset_provenance_field_invalid")
        if not isinstance(self.classification, ProvenanceClass):
            raise PackagingAssetError("packaging_asset_provenance_class_invalid")
        if self.source_reference_id is not None:
            _identifier(self.source_reference_id, "source_reference_id")
        if self.source_description is not None:
            _bounded_text(self.source_description, "source_description", 160)
        if self.method_id is not None:
            _identifier(self.method_id, "method_id")
        if self.confidence is not None:
            if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
                raise PackagingAssetError("packaging_asset_provenance_confidence_invalid")
            try:
                confidence = float(self.confidence)
            except OverflowError as error:
                raise PackagingAssetError(
                    "packaging_asset_provenance_confidence_invalid"
                ) from error
            if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
                raise PackagingAssetError("packaging_asset_provenance_confidence_invalid")
            object.__setattr__(self, "confidence", confidence)

        if self.classification is ProvenanceClass.SUPPLIER_FACT:
            if (
                self.source_reference_id is None
                and self.source_description is None
                or self.method_id is not None
                or self.confidence is not None
            ):
                raise PackagingAssetError("packaging_asset_supplier_fact_provenance_invalid")
        elif self.classification is ProvenanceClass.PACKLAB_ESTIMATE:
            if (
                self.method_id is None
                or self.source_reference_id is not None
                or self.source_description is not None
            ):
                raise PackagingAssetError("packaging_asset_estimate_provenance_invalid")
        elif any(
            value is not None
            for value in (
                self.source_reference_id,
                self.source_description,
                self.method_id,
                self.confidence,
            )
        ):
            raise PackagingAssetError("packaging_asset_nonfactual_provenance_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "field_name": self.field_name,
            "classification": self.classification.value,
            "source_reference_id": self.source_reference_id,
            "source_description": self.source_description,
            "method_id": self.method_id,
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class RawScanLink:
    """Exact path-free reference to one immutable raw capture in a PackLab project."""

    project_id: str
    revision_id: str
    artifact_sha256: str
    authority_class: str = "RAW_CAPTURE"
    immutable: bool = True

    def __post_init__(self) -> None:
        _identifier(self.project_id, "raw_scan_project_id")
        _identifier(self.revision_id, "raw_scan_revision_id")
        if not isinstance(self.artifact_sha256, str) or not _SHA256.fullmatch(self.artifact_sha256):
            raise PackagingAssetError("packaging_asset_raw_scan_digest_invalid")
        if self.authority_class != "RAW_CAPTURE" or self.immutable is not True:
            raise PackagingAssetError("packaging_asset_raw_scan_authority_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "revision_id": self.revision_id,
            "artifact_sha256": self.artifact_sha256,
            "authority_class": self.authority_class,
            "immutable": self.immutable,
        }


@dataclass(frozen=True, slots=True)
class ScanMasterLink:
    """Exact reference to a promoted Scan Master, retaining its deferred limits."""

    project_id: str
    revision_id: str
    geometry_sha256: str
    scale_state: ScaleState
    scale_provenance_id: str
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False
    authority_class: str = "SCAN_MASTER"

    def __post_init__(self) -> None:
        _identifier(self.project_id, "scan_master_project_id")
        _identifier(self.revision_id, "scan_master_revision_id")
        if not isinstance(self.geometry_sha256, str) or not _SHA256.fullmatch(self.geometry_sha256):
            raise PackagingAssetError("packaging_asset_scan_master_digest_invalid")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise PackagingAssetError("packaging_asset_scan_master_scale_state_invalid")
        _identifier(self.scale_provenance_id, "scan_master_scale_provenance_id")
        if (
            self.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
            or self.mold_use_authorized is not False
            or self.authority_class != "SCAN_MASTER"
        ):
            raise PackagingAssetError("packaging_asset_scan_master_authority_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "revision_id": self.revision_id,
            "geometry_sha256": self.geometry_sha256,
            "authority_class": self.authority_class,
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


@dataclass(frozen=True, slots=True)
class DesignModelLink:
    """Exact reference to an immutable captured or standalone Design Model revision."""

    project_id: str
    revision_id: str
    content_sha256: str
    parent_authority_kind: str
    parent_authority_revision_id: str
    scale_state: ScaleState
    scan_master_revision_id: str | None = None
    scan_master_geometry_sha256: str | None = None
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False
    authority_class: str = "DESIGN_MODEL_REVISION"

    def __post_init__(self) -> None:
        _identifier(self.project_id, "design_model_project_id")
        _identifier(self.revision_id, "design_model_revision_id")
        if not isinstance(self.content_sha256, str) or not _SHA256.fullmatch(self.content_sha256):
            raise PackagingAssetError("packaging_asset_design_model_digest_invalid")
        if not isinstance(self.parent_authority_kind, str) or self.parent_authority_kind not in {
            "CAPTURED_SCAN_MASTER",
            "STANDALONE_DESIGN_GEOMETRY",
        }:
            raise PackagingAssetError("packaging_asset_design_model_parent_kind_invalid")
        _identifier(self.parent_authority_revision_id, "design_model_parent_authority_revision_id")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise PackagingAssetError("packaging_asset_design_model_scale_state_invalid")
        if self.parent_authority_kind == "CAPTURED_SCAN_MASTER":
            _identifier(self.scan_master_revision_id, "design_model_scan_master_revision_id")
            if (
                not isinstance(self.scan_master_geometry_sha256, str)
                or not _SHA256.fullmatch(self.scan_master_geometry_sha256)
                or self.parent_authority_revision_id != self.scan_master_revision_id
            ):
                raise PackagingAssetError("packaging_asset_design_model_parent_digest_invalid")
        elif (
            self.scan_master_revision_id is not None or self.scan_master_geometry_sha256 is not None
        ):
            raise PackagingAssetError("packaging_asset_standalone_model_has_scan_master")
        if (
            self.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
            or self.mold_use_authorized is not False
            or self.authority_class != "DESIGN_MODEL_REVISION"
        ):
            raise PackagingAssetError("packaging_asset_design_model_authority_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "revision_id": self.revision_id,
            "content_sha256": self.content_sha256,
            "authority_class": self.authority_class,
            "parent_authority_kind": self.parent_authority_kind,
            "parent_authority_revision_id": self.parent_authority_revision_id,
            "scan_master_revision_id": self.scan_master_revision_id,
            "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            "scale_state": self.scale_state.value,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


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
    field_provenance: tuple[FieldProvenance, ...] = ()
    raw_scan_links: tuple[RawScanLink, ...] = ()
    scan_master_link: ScanMasterLink | None = None
    design_model_links: tuple[DesignModelLink, ...] = ()
    preferred_design_model_revision_id: str | None = None
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
        if not isinstance(self.field_provenance, tuple) or any(
            not isinstance(item, FieldProvenance) for item in self.field_provenance
        ):
            raise PackagingAssetError("packaging_asset_field_provenance_invalid")
        provenance_names = tuple(item.field_name for item in self.field_provenance)
        if len(provenance_names) != len(set(provenance_names)):
            raise PackagingAssetError("packaging_asset_field_provenance_duplicate")
        if provenance_names != tuple(sorted(provenance_names)):
            object.__setattr__(
                self,
                "field_provenance",
                tuple(sorted(self.field_provenance, key=lambda item: item.field_name)),
            )
        provenance_by_field = {item.field_name: item for item in self.field_provenance}
        for field_name in _PROVENANCE_FIELDS:
            value = getattr(self, field_name)
            source = provenance_by_field.get(field_name)
            if _is_known_value(value):
                if source is None or source.classification is ProvenanceClass.UNKNOWN:
                    raise PackagingAssetError(f"packaging_asset_{field_name}_provenance_required")
            elif source is not None and source.classification is not ProvenanceClass.UNKNOWN:
                raise PackagingAssetError(
                    f"packaging_asset_{field_name}_unknown_provenance_required"
                )
        if not isinstance(self.raw_scan_links, tuple) or any(
            not isinstance(item, RawScanLink) for item in self.raw_scan_links
        ):
            raise PackagingAssetError("packaging_asset_raw_scan_links_invalid")
        raw_ids = tuple((item.project_id, item.revision_id) for item in self.raw_scan_links)
        if len(raw_ids) != len(set(raw_ids)):
            raise PackagingAssetError("packaging_asset_raw_scan_link_duplicate")
        canonical_raw_links = tuple(
            sorted(self.raw_scan_links, key=lambda item: (item.project_id, item.revision_id))
        )
        if canonical_raw_links != self.raw_scan_links:
            object.__setattr__(self, "raw_scan_links", canonical_raw_links)
        if self.scan_master_link is not None and not isinstance(
            self.scan_master_link, ScanMasterLink
        ):
            raise PackagingAssetError("packaging_asset_scan_master_link_invalid")
        if not isinstance(self.design_model_links, tuple) or any(
            not isinstance(item, DesignModelLink) for item in self.design_model_links
        ):
            raise PackagingAssetError("packaging_asset_design_model_links_invalid")
        design_ids = tuple((item.project_id, item.revision_id) for item in self.design_model_links)
        if len(design_ids) != len(set(design_ids)):
            raise PackagingAssetError("packaging_asset_design_model_link_duplicate")
        if self.preferred_design_model_revision_id is not None:
            _identifier(
                self.preferred_design_model_revision_id, "preferred_design_model_revision_id"
            )
            preferred_matches = tuple(
                item
                for item in self.design_model_links
                if item.revision_id == self.preferred_design_model_revision_id
            )
            if len(preferred_matches) != 1:
                raise PackagingAssetError("packaging_asset_preferred_design_model_missing")
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
            "field_provenance": [item.as_dict() for item in self.field_provenance],
            "source_links": {
                "raw_scans": [item.as_dict() for item in self.raw_scan_links],
                "scan_master": (
                    self.scan_master_link.as_dict() if self.scan_master_link is not None else None
                ),
                "design_models": [item.as_dict() for item in self.design_model_links],
                "preferred_design_model_revision_id": self.preferred_design_model_revision_id,
            },
            "status": self.status.value,
            "authority_semantics": "PACKAGING_METADATA_ONLY",
            "supplier_certification_inferred": False,
            "physical_accuracy_verified": False,
            "manufacturing_authorized": False,
        }

    def with_field_update(
        self, field_name: str, value: object, provenance: FieldProvenance
    ) -> PackagingAsset:
        """Return a validated immutable successor with a new value/provenance pair."""
        if not isinstance(field_name, str) or field_name not in _EDITABLE_FIELDS:
            raise PackagingAssetError("packaging_asset_field_not_editable")
        if not isinstance(provenance, FieldProvenance) or provenance.field_name != field_name:
            raise PackagingAssetError("packaging_asset_field_provenance_mismatch")
        updated_provenance = {item.field_name: item for item in self.field_provenance}
        updated_provenance[field_name] = provenance
        return cast(
            PackagingAsset,
            replace(
                cast(Any, self),
                **{
                    field_name: value,
                    "field_provenance": tuple(
                        updated_provenance[name] for name in sorted(updated_provenance)
                    ),
                },
            ),
        )

    def with_source_links(
        self,
        *,
        raw_scan_links: tuple[RawScanLink, ...],
        scan_master_link: ScanMasterLink | None,
        design_model_links: tuple[DesignModelLink, ...],
        preferred_design_model_revision_id: str | None = None,
    ) -> PackagingAsset:
        """Return a new revision with validated immutable source references."""
        return replace(
            self,
            raw_scan_links=raw_scan_links,
            scan_master_link=scan_master_link,
            design_model_links=design_model_links,
            preferred_design_model_revision_id=preferred_design_model_revision_id,
        )


def _identifier(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise PackagingAssetError(f"packaging_asset_{field_name}_invalid")


def _is_known_value(value: object) -> bool:
    return value is not None and getattr(value, "value", None) != "UNKNOWN"


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
    "DesignModelLink",
    "FieldProvenance",
    "MeasurementUnit",
    "PackagingAsset",
    "PackagingAssetError",
    "PackagingFamily",
    "PackagingMeasurement",
    "PACKAGING_ASSET_CONTRACT",
    "ProvenanceClass",
    "RawScanLink",
    "ScanMasterLink",
]
