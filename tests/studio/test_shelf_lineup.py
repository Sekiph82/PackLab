from __future__ import annotations

import pytest

from packlab_core.packaging_asset import (
    FieldProvenance,
    MeasurementUnit,
    PackagingAsset,
    PackagingAssetError,
    PackagingFamily,
    PackagingMeasurement,
    ProvenanceClass,
)
from packlab_core.packaging_sku_library import PackagingSkuRevision, PackagingSkuStatus
from packlab_studio.app import create_application
from packlab_studio.shelf_lineup import (
    ShelfLineupError,
    ShelfLineupPlan,
    ShelfLineupWidget,
)


def _asset(
    asset_id: str,
    *,
    height: PackagingMeasurement | None = PackagingMeasurement(180, MeasurementUnit.MILLIMETER),
    diameter: PackagingMeasurement | None = PackagingMeasurement(58, MeasurementUnit.MILLIMETER),
    height_source: ProvenanceClass = ProvenanceClass.SUPPLIER_FACT,
    diameter_source: ProvenanceClass = ProvenanceClass.USER_DECLARED,
) -> PackagingAsset:
    height_classification = height_source if height is not None else ProvenanceClass.UNKNOWN
    diameter_classification = diameter_source if diameter is not None else ProvenanceClass.UNKNOWN
    height_field = FieldProvenance(
        "overall_height",
        height_classification,
        source_description="Synthetic supplier statement"
        if height_classification is ProvenanceClass.SUPPLIER_FACT
        else None,
    )
    return PackagingAsset(
        asset_id=asset_id,
        display_name=f"POVU {asset_id}",
        family=PackagingFamily.BOTTLE,
        overall_height=height,
        body_diameter=diameter,
        field_provenance=(
            FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
            FieldProvenance("family", ProvenanceClass.USER_DECLARED),
            height_field,
            FieldProvenance("body_diameter", diameter_classification),
        ),
    )


def _sku(asset: PackagingAsset, sku_id: str | None = None) -> PackagingSkuRevision:
    return PackagingSkuRevision.create(
        asset,
        sku_id=sku_id or asset.asset_id.replace("-", "_").title(),
        display_name=asset.display_name,
        status=PackagingSkuStatus.ACTIVE,
    )


def test_lineup_converts_supported_units_and_pins_exact_source_provenance() -> None:
    first_asset = _asset("povu-bottle-1")
    second_asset = _asset(
        "povu-bottle-2",
        height=PackagingMeasurement(20, MeasurementUnit.CENTIMETER),
        diameter=PackagingMeasurement(6, MeasurementUnit.CENTIMETER),
    )
    inputs = ((_sku(first_asset), first_asset), (_sku(second_asset), second_asset))
    source_before = tuple(asset.canonical_json for _, asset in inputs)

    plan = ShelfLineupPlan.create(inputs, gap_mm=20)

    assert [entry.height_mm for entry in plan.entries] == [180, 200]
    assert [entry.body_diameter_mm for entry in plan.entries] == [58, 60]
    assert plan.entries[0].x_mm == 0
    assert plan.entries[1].x_mm == 78
    assert plan.total_width_mm == 138
    assert [asset.canonical_json for _, asset in inputs] == list(source_before)
    data = plan.as_dict()
    assert data["authority"] == "SCHEMATIC_PRESENTATION_ONLY"
    assert data["product_geometry"] is False
    assert data["entries"][0]["height_provenance"] == "SUPPLIER_FACT"


def test_stale_asset_revision_and_duplicate_sku_are_rejected() -> None:
    asset = _asset("povu-source-a")
    sku = _sku(asset, "povu-sku-a")
    stale_asset = _asset("povu-source-b")
    with pytest.raises(ShelfLineupError, match="sku_asset_revision_mismatch"):
        ShelfLineupPlan.create(((sku, stale_asset), (_sku(stale_asset, "povu-sku-b"), stale_asset)))

    duplicate_asset = _asset("povu-source-c")
    duplicate = _sku(duplicate_asset, "povu-sku-a")
    with pytest.raises(ShelfLineupError, match="invalid_or_duplicate"):
        ShelfLineupPlan.create(((sku, asset), (duplicate, duplicate_asset)))


@pytest.mark.parametrize(
    ("height", "diameter", "height_source", "error"),
    [
        (
            None,
            PackagingMeasurement(50, MeasurementUnit.MILLIMETER),
            ProvenanceClass.SUPPLIER_FACT,
            "overall_height_missing",
        ),
        (
            PackagingMeasurement(18, MeasurementUnit.MILLIMETER),
            None,
            ProvenanceClass.SUPPLIER_FACT,
            "body_diameter_missing",
        ),
        (
            PackagingMeasurement(1001, MeasurementUnit.CENTIMETER),
            PackagingMeasurement(50, MeasurementUnit.MILLIMETER),
            ProvenanceClass.SUPPLIER_FACT,
            "overall_height_out_of_display_bounds",
        ),
    ],
)
def test_invalid_or_unverified_dimensions_fail_closed(
    height: PackagingMeasurement | None,
    diameter: PackagingMeasurement | None,
    height_source: ProvenanceClass,
    error: str,
) -> None:
    first = _asset("povu-bad-a", height=height, diameter=diameter, height_source=height_source)
    second = _asset("povu-good-b")
    with pytest.raises(ShelfLineupError, match=error):
        ShelfLineupPlan.create(((_sku(first), first), (_sku(second), second)))


def test_input_count_and_gap_bounds_are_enforced() -> None:
    asset = _asset("povu-only")
    sku = _sku(asset)
    with pytest.raises(ShelfLineupError, match="requires_2_to_12"):
        ShelfLineupPlan.create(((sku, asset),))
    other = _asset("povu-second")
    with pytest.raises(ShelfLineupError, match="gap_out_of_bounds"):
        ShelfLineupPlan.create(((sku, asset), (_sku(other), other)), gap_mm=251)

    too_many_items = []
    for index in range(13):
        selected = _asset(f"povu-count-{index}")
        too_many_items.append((_sku(selected), selected))
    with pytest.raises(ShelfLineupError, match="requires_2_to_12"):
        ShelfLineupPlan.create(tuple(too_many_items))


def test_packaging_asset_rejects_unknown_provenance_for_known_dimensions() -> None:
    with pytest.raises(PackagingAssetError, match="overall_height_provenance_required"):
        _asset("povu-unknown-source", height_source=ProvenanceClass.UNKNOWN)


def test_packaging_asset_rejects_dimensions_with_unsupported_units() -> None:
    with pytest.raises(PackagingAssetError, match="overall_height_unit_invalid"):
        _asset(
            "povu-invalid-unit",
            height=PackagingMeasurement(18, MeasurementUnit.MILLILITER),
        )


def test_widget_labels_revision_dimensions_and_schematic_limit() -> None:
    application = create_application(["packlab-shelf-lineup-test"])
    first = _asset("povu-widget-a")
    second = _asset("povu-widget-b")
    widget = ShelfLineupWidget(
        ShelfLineupPlan.create(((_sku(first), first), (_sku(second), second)))
    )

    assert "NOT PRODUCT GEOMETRY" in widget.authority_label.text()
    assert "NOT SHELF-FIT CERTIFICATION" in widget.authority_label.text()
    assert first.revision_id in widget.rows_label.text()
    assert "180 mm (SUPPLIER_FACT)" in widget.rows_label.text()
    assert "58 mm (USER_DECLARED)" in widget.rows_label.text()
    assert widget.plot.sizeHint().width() >= 2
    widget.resize(960, 480)
    widget.show()
    application.processEvents()
    rendered = widget.plot.grab().toImage()
    assert not rendered.isNull()
    assert any(
        (pixel := rendered.pixelColor(x, y)).green() > 160
        and pixel.red() < 140
        and pixel.blue() > 150
        for y in range(rendered.height())
        for x in range(rendered.width())
    )
    widget.close()
