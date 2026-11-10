from __future__ import annotations

import hashlib

import pytest

from packlab_core.packaging_asset import (
    BaseMaterial,
    ClosureType,
    FieldProvenance,
    MeasurementUnit,
    PackagingAsset,
    PackagingFamily,
    PackagingMeasurement,
    ProvenanceClass,
)
from packlab_core.packaging_dossier_pdf import (
    PACKAGING_DOSSIER_PDF_CONTRACT,
    PackagingDossierPdfError,
    export_packaging_dossier_pdf,
)


def _asset() -> PackagingAsset:
    provenance = tuple(
        sorted(
            (
                FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
                FieldProvenance("family", ProvenanceClass.USER_DECLARED),
                FieldProvenance(
                    "nominal_volume",
                    ProvenanceClass.SUPPLIER_FACT,
                    source_description="Synthetic source",
                ),
                FieldProvenance(
                    "supplier_id",
                    ProvenanceClass.SUPPLIER_FACT,
                    source_description="Synthetic source",
                ),
                FieldProvenance(
                    "supplier_name",
                    ProvenanceClass.SUPPLIER_FACT,
                    source_description="Synthetic source",
                ),
                FieldProvenance(
                    "base_material",
                    ProvenanceClass.SUPPLIER_FACT,
                    source_description="Synthetic source",
                ),
                FieldProvenance("empty_package_weight", ProvenanceClass.UNKNOWN),
                FieldProvenance(
                    "overall_height",
                    ProvenanceClass.SUPPLIER_FACT,
                    source_description="Synthetic source",
                ),
                FieldProvenance(
                    "body_diameter",
                    ProvenanceClass.SUPPLIER_FACT,
                    source_description="Synthetic source",
                ),
                FieldProvenance("neck_finish", ProvenanceClass.UNKNOWN),
                FieldProvenance("neck_finish_diameter", ProvenanceClass.UNKNOWN),
                FieldProvenance(
                    "closure_type",
                    ProvenanceClass.SUPPLIER_FACT,
                    source_description="Synthetic source",
                ),
                FieldProvenance("closure_description", ProvenanceClass.UNKNOWN),
                FieldProvenance("status", ProvenanceClass.UNKNOWN),
            ),
            key=lambda item: item.field_name,
        )
    )
    return PackagingAsset(
        asset_id="asset-dossier-synthetic",
        display_name="Synthetic bottle",
        family=PackagingFamily.BOTTLE,
        nominal_volume=PackagingMeasurement(500, MeasurementUnit.MILLILITER),
        supplier_id="supplier-synthetic",
        supplier_name="Synthetic Supplier",
        base_material=BaseMaterial.PET,
        overall_height=PackagingMeasurement(180, MeasurementUnit.MILLIMETER),
        body_diameter=PackagingMeasurement(65, MeasurementUnit.MILLIMETER),
        closure_type=ClosureType.SCREW_CAP,
        field_provenance=provenance,
    )


def test_dossier_is_one_page_pdf_with_exact_source_and_authority_disclaimer() -> None:
    asset = _asset()
    dossier = export_packaging_dossier_pdf(asset)
    manifest = dossier.manifest
    source_digest = hashlib.sha256(asset.canonical_json.encode("utf-8")).hexdigest()

    assert dossier.pdf_bytes.startswith(b"%PDF-")
    assert manifest["contract"] == PACKAGING_DOSSIER_PDF_CONTRACT
    assert manifest["asset_id"] == asset.asset_id
    assert manifest["asset_revision_id"] == asset.revision_id
    assert manifest["source_canonical_sha256"] == source_digest
    assert manifest["source_record"] == asset.as_dict()
    assert manifest["page_count"] == 1
    assert manifest["parsed_by_qtpdf"] is True
    assert manifest["render_smoke"] == "PASS"
    assert "PACKAGING METADATA ONLY" in manifest["visible_disclaimer"]
    assert manifest["manufacturing_authorized"] is False
    assert manifest["filesystem_write_performed"] is False
    assert dossier.as_dict()["pdf_sha256"] == manifest["pdf_sha256"]


def test_dossier_field_order_is_stable_and_unknowns_keep_unknown_provenance() -> None:
    manifest = export_packaging_dossier_pdf(_asset()).manifest
    assert manifest["field_order"] == [
        "display_name",
        "family",
        "other_family_label",
        "nominal_volume",
        "supplier_id",
        "supplier_name",
        "base_material",
        "other_material_label",
        "empty_package_weight",
        "overall_height",
        "body_diameter",
        "neck_finish",
        "neck_finish_diameter",
        "closure_type",
        "closure_description",
        "status",
    ]
    source = manifest["source_record"]
    assert source["empty_package_weight"] is None
    assert any(
        item["field_name"] == "empty_package_weight" and item["classification"] == "UNKNOWN"
        for item in source["field_provenance"]
    )


def test_dossier_rejects_non_asset_source() -> None:
    with pytest.raises(PackagingDossierPdfError, match="packaging_asset_required"):
        export_packaging_dossier_pdf(object())  # type: ignore[arg-type]
