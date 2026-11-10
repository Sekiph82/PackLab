from __future__ import annotations

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
from packlab_studio.app import create_application
from packlab_studio.supplier_comparison import (
    SupplierComparisonError,
    SupplierComparisonReport,
    SupplierComparisonWidget,
)


def _asset(
    asset_id: str,
    supplier_id: str | None,
    supplier_name: str | None,
    *,
    height: PackagingMeasurement | None = PackagingMeasurement(180, MeasurementUnit.MILLIMETER),
) -> PackagingAsset:
    provenance = [
        FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
        FieldProvenance("family", ProvenanceClass.USER_DECLARED),
        FieldProvenance("base_material", ProvenanceClass.USER_DECLARED),
        FieldProvenance("closure_type", ProvenanceClass.UNKNOWN),
        FieldProvenance("status", ProvenanceClass.UNKNOWN),
    ]
    for field in ("supplier_id", "supplier_name"):
        value = supplier_id if field == "supplier_id" else supplier_name
        if value is not None:
            provenance.append(
                FieldProvenance(
                    field,
                    ProvenanceClass.SUPPLIER_FACT,
                    source_description="Synthetic supplier record",
                )
            )
    if height is not None:
        provenance.append(
            FieldProvenance(
                "overall_height",
                ProvenanceClass.SUPPLIER_FACT,
                source_description="Synthetic supplier specification",
            )
        )
    else:
        provenance.append(FieldProvenance("overall_height", ProvenanceClass.UNKNOWN))
    return PackagingAsset(
        asset_id=asset_id,
        display_name=f"Package {asset_id}",
        family=PackagingFamily.BOTTLE,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        overall_height=height,
        base_material=BaseMaterial.PET,
        closure_type=ClosureType.UNKNOWN,
        field_provenance=tuple(provenance),
    )


def test_comparison_preserves_order_identity_units_unknowns_and_provenance() -> None:
    first = _asset("asset-povu-01", "supplier-a", "Supplier A")
    second = _asset(
        "asset-povu-02",
        "supplier-b",
        "Supplier B",
        height=PackagingMeasurement(19, MeasurementUnit.CENTIMETER),
    )
    original = (first.canonical_json, second.canonical_json)

    report = SupplierComparisonReport.create((first, second))
    data = report.as_dict()

    assert [column.asset_id for column in report.columns] == [first.asset_id, second.asset_id]
    assert data["authority"] == "DESCRIPTIVE_NON_AUTHORITATIVE"
    assert data["ranked"] is False
    assert data["recommendation"] is None
    first_fields = {item["field"]: item for item in data["columns"][0]["fields"]}
    assert first_fields["overall_height"]["value"] == "180 mm"
    assert first_fields["overall_height"]["provenance"] == "SUPPLIER_FACT"
    assert first_fields["body_diameter"]["value"] == "UNKNOWN"
    assert first_fields["body_diameter"]["provenance"] == "UNKNOWN"
    assert [first.canonical_json, second.canonical_json] == list(original)


def test_missing_supplier_identity_stays_unknown_without_inference() -> None:
    first = _asset("asset-no-supplier", None, None)
    second = _asset("asset-known-supplier", "supplier-b", "Supplier B")
    report = SupplierComparisonReport.create((first, second))

    first_fields = {item.field: item for item in report.columns[0].cells}
    assert first_fields["supplier_id"].display_value == "UNKNOWN"
    assert first_fields["supplier_name"].display_value == "UNKNOWN"
    assert first_fields["supplier_id"].provenance == "UNKNOWN"


def test_fewer_than_two_assets_and_duplicate_revisions_are_rejected() -> None:
    first = _asset("asset-one", "supplier-a", "Supplier A")
    with pytest.raises(SupplierComparisonError, match="requires_two_assets"):
        SupplierComparisonReport.create((first,))
    with pytest.raises(SupplierComparisonError, match="duplicate_asset_revision"):
        SupplierComparisonReport.create((first, first))


def test_qt_table_shows_authority_limitations_and_exact_revision_provenance() -> None:
    application = create_application(["packlab-supplier-comparison-test"])
    first = _asset("asset-table-a", "supplier-a", "Supplier A")
    second = _asset("asset-table-b", "supplier-b", "Supplier B")
    widget = SupplierComparisonWidget(SupplierComparisonReport.create((first, second)))
    widget.resize(1000, 620)
    widget.show()
    application.processEvents()

    assert "NO RANKING OR RECOMMENDATION" in widget.authority_label.text()
    assert "quality" in widget.limitation_label.text()
    assert first.revision_id in widget.table.horizontalHeaderItem(1).text()
    assert "180 mm\nProvenance: SUPPLIER_FACT" in widget.table.item(4, 1).text()
    assert widget.table.item(5, 1).text() == "UNKNOWN\nProvenance: UNKNOWN"
    widget.close()
