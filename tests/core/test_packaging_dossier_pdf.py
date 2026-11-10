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


def test_rendered_page_draws_disclaimer_every_field_and_its_provenance_tag(monkeypatch) -> None:
    # Review P2-5: assert what is actually painted into the PDF, not a constant string.
    from PySide6.QtGui import QPainter

    from packlab_core.packaging_dossier_pdf import _DISCLAIMER, _FIELD_LABELS, _field_values

    drawn: list[str] = []
    original = QPainter.drawText

    def recording_draw_text(self, *args):
        drawn.extend(arg for arg in args if isinstance(arg, str))
        return original(self, *args)

    monkeypatch.setattr(QPainter, "drawText", recording_draw_text)
    asset = _asset()
    export_packaging_dossier_pdf(asset)

    assert _DISCLAIMER in drawn
    values = _field_values(asset)
    for field_name, label in _FIELD_LABELS:
        value, provenance = values[field_name]
        assert label in drawn, label
        assert f"{value}  [{provenance}]" in drawn, field_name
    assert any(asset.revision_id in text for text in drawn)


def test_painted_text_matches_literal_expected_strings(monkeypatch) -> None:
    # Re-review P2-6: expectations must not come from the module's own helpers, or a
    # provenance upgrade / weakened disclaimer would pass. Literal strings only.
    from PySide6.QtGui import QPainter

    drawn: list[str] = []
    original = QPainter.drawText

    def recording_draw_text(self, *args):
        drawn.extend(arg for arg in args if isinstance(arg, str))
        return original(self, *args)

    monkeypatch.setattr(QPainter, "drawText", recording_draw_text)
    export_packaging_dossier_pdf(_asset())
    for expected in (
        "Synthetic bottle  [USER_DECLARED]",
        "BOTTLE  [USER_DECLARED]",
        "500.0 mL  [SUPPLIER_FACT]",
        "180.0 mm  [SUPPLIER_FACT]",
        "65.0 mm  [SUPPLIER_FACT]",
        "SCREW_CAP  [SUPPLIER_FACT]",
    ):
        assert expected in drawn, expected
    assert drawn.count("UNKNOWN  [UNKNOWN]") == 7  # unknowns are never upgraded
    disclaimer = next(text for text in drawn if text.startswith("PACKAGING METADATA ONLY."))
    for phrase in (
        "does not establish physical accuracy",
        "supplier certification",
        "regulatory compliance",
        "manufacturing authorization",
    ):
        assert phrase in disclaimer, phrase
