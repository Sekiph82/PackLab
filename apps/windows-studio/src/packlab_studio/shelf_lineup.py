"""Schematic, provenance-backed POVU SKU shelf-lineup preview."""

from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from packlab_core.packaging_asset import (
    MeasurementUnit,
    PackagingAsset,
    ProvenanceClass,
)
from packlab_core.packaging_sku_library import PackagingSkuRevision

_MIN_ITEMS = 2
_MAX_ITEMS = 12
_MAX_DIMENSION_MM = 10_000.0
_MAX_GAP_MM = 250.0


class ShelfLineupError(ValueError):
    """Raised when SKU sources or dimensions cannot support a safe schematic."""


@dataclass(frozen=True, slots=True)
class ShelfLineupEntry:
    sku_id: str
    sku_revision_id: str
    display_name: str
    asset_id: str
    asset_revision_id: str
    x_mm: float
    height_mm: float
    body_diameter_mm: float
    height_provenance: ProvenanceClass
    diameter_provenance: ProvenanceClass


@dataclass(frozen=True, slots=True)
class ShelfLineupPlan:
    """Ordered, dimensioned presentation data; not a shelf-fit or product model."""

    entries: tuple[ShelfLineupEntry, ...]
    gap_mm: float
    total_width_mm: float

    @classmethod
    def create(
        cls,
        sku_assets: tuple[tuple[PackagingSkuRevision, PackagingAsset], ...],
        *,
        gap_mm: float = 24.0,
    ) -> ShelfLineupPlan:
        if not isinstance(sku_assets, tuple) or not _MIN_ITEMS <= len(sku_assets) <= _MAX_ITEMS:
            raise ShelfLineupError("shelf_lineup_requires_2_to_12_skus")
        if (
            isinstance(gap_mm, bool)
            or not isinstance(gap_mm, (int, float))
            or not math.isfinite(float(gap_mm))
            or not 0.0 <= float(gap_mm) <= _MAX_GAP_MM
        ):
            raise ShelfLineupError("shelf_lineup_gap_out_of_bounds")
        if any(not isinstance(pair, tuple) or len(pair) != 2 for pair in sku_assets):
            raise ShelfLineupError("shelf_lineup_source_pair_invalid")
        sku_ids = tuple(
            pair[0].sku_id for pair in sku_assets if isinstance(pair[0], PackagingSkuRevision)
        )
        if len(sku_ids) != len(sku_assets) or len(set(sku_ids)) != len(sku_ids):
            raise ShelfLineupError("shelf_lineup_sku_invalid_or_duplicate")

        entries: list[ShelfLineupEntry] = []
        x_mm = 0.0
        for index, pair in enumerate(sku_assets):
            sku, asset = pair
            if not isinstance(sku, PackagingSkuRevision) or not isinstance(asset, PackagingAsset):
                raise ShelfLineupError("shelf_lineup_immutable_sources_required")
            try:
                sku.validate_targets((asset,), sku.artwork_references)
            except ValueError as error:
                raise ShelfLineupError("shelf_lineup_sku_asset_revision_mismatch") from error
            height = _dimension_mm(asset.overall_height, "overall_height")
            diameter = _dimension_mm(asset.body_diameter, "body_diameter")
            height_provenance = _field_provenance(asset, "overall_height")
            diameter_provenance = _field_provenance(asset, "body_diameter")
            entries.append(
                ShelfLineupEntry(
                    sku_id=sku.sku_id,
                    sku_revision_id=sku.revision_id,
                    display_name=sku.display_name,
                    asset_id=asset.asset_id,
                    asset_revision_id=asset.revision_id,
                    x_mm=x_mm,
                    height_mm=height,
                    body_diameter_mm=diameter,
                    height_provenance=height_provenance,
                    diameter_provenance=diameter_provenance,
                )
            )
            x_mm += diameter
            if index < len(sku_assets) - 1:
                x_mm += float(gap_mm)
        return cls(tuple(entries), float(gap_mm), x_mm)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.shelf-lineup-preview.v1",
            "authority": "SCHEMATIC_PRESENTATION_ONLY",
            "shelf_fit_certified": False,
            "product_geometry": False,
            "gap_mm": self.gap_mm,
            "total_width_mm": self.total_width_mm,
            "entries": [
                {
                    "sku_id": item.sku_id,
                    "sku_revision_id": item.sku_revision_id,
                    "display_name": item.display_name,
                    "asset_id": item.asset_id,
                    "asset_revision_id": item.asset_revision_id,
                    "x_mm": item.x_mm,
                    "height_mm": item.height_mm,
                    "body_diameter_mm": item.body_diameter_mm,
                    "height_provenance": item.height_provenance.value,
                    "diameter_provenance": item.diameter_provenance.value,
                }
                for item in self.entries
            ],
        }


def _dimension_mm(measurement: object, field: str) -> float:
    if measurement is None:
        raise ShelfLineupError(f"shelf_lineup_{field}_missing")
    unit = getattr(measurement, "unit", None)
    value = getattr(measurement, "value", None)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ShelfLineupError(f"shelf_lineup_{field}_value_invalid")
    if unit is MeasurementUnit.MILLIMETER:
        normalized = float(value)
    elif unit is MeasurementUnit.CENTIMETER:
        normalized = float(value) * 10.0
    else:
        raise ShelfLineupError(f"shelf_lineup_{field}_unit_unsupported")
    if not math.isfinite(normalized) or not 0.0 < normalized <= _MAX_DIMENSION_MM:
        raise ShelfLineupError(f"shelf_lineup_{field}_out_of_display_bounds")
    return normalized


def _field_provenance(asset: PackagingAsset, field: str) -> ProvenanceClass:
    match = tuple(item for item in asset.field_provenance if item.field_name == field)
    if len(match) != 1 or match[0].classification is ProvenanceClass.UNKNOWN:
        raise ShelfLineupError(f"shelf_lineup_{field}_provenance_required")
    return match[0].classification


class _ShelfPlot(QWidget):
    def __init__(self, plan: ShelfLineupPlan, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.plan = plan
        self.setMinimumHeight(240)
        self.setToolTip(
            "Schematic dimension-scaled silhouettes; not product geometry or shelf-fit certification."
        )

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt override name
        return QSize(960, 340)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override name
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#101820"))
        margin = 24.0
        available_width = max(1.0, self.width() - 2 * margin)
        baseline = self.height() - 36.0
        max_height = max(item.height_mm for item in self.plan.entries)
        scale = min(available_width / self.plan.total_width_mm, (baseline - 28.0) / max_height)
        start_x = margin
        painter.setPen(QPen(QColor("#8aa0b4"), 2.0))
        painter.drawLine(
            QRectF(margin, baseline, available_width, 0.0).topLeft(),
            QRectF(margin, baseline, available_width, 0.0).topRight(),
        )
        for entry in self.plan.entries:
            width = entry.body_diameter_mm * scale
            height = entry.height_mm * scale
            box = QRectF(start_x, baseline - height, width, height)
            painter.setPen(QPen(QColor("#67d5c2"), 1.5))
            painter.setBrush(QColor(103, 213, 194, 75))
            painter.drawRoundedRect(box, min(width * 0.12, 10.0), min(width * 0.12, 10.0))
            start_x += (entry.body_diameter_mm + self.plan.gap_mm) * scale
        painter.end()


class ShelfLineupWidget(QWidget):
    """Dimension-scaled schematic lineup with exact source/provenance labels."""

    def __init__(self, plan: ShelfLineupPlan, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if not isinstance(plan, ShelfLineupPlan):
            raise ShelfLineupError("shelf_lineup_plan_required")
        self.plan = plan
        self.authority_label = QLabel(
            "SCHEMATIC PREVIEW · NOT PRODUCT GEOMETRY · NOT SHELF-FIT CERTIFICATION"
        )
        self.rows_label = QLabel(self._entry_text())
        self.rows_label.setTextFormat(Qt.TextFormat.PlainText)
        self.rows_label.setWordWrap(True)
        self.plot = _ShelfPlot(plan, self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.authority_label)
        layout.addWidget(self.plot)
        layout.addWidget(self.rows_label)

    def _entry_text(self) -> str:
        return "\n".join(
            f"{item.display_name} [{item.sku_id} / {item.sku_revision_id}] → "
            f"asset {item.asset_id} / {item.asset_revision_id}; "
            f"H {item.height_mm:g} mm ({item.height_provenance.value}); "
            f"D {item.body_diameter_mm:g} mm ({item.diameter_provenance.value})"
            for item in self.plan.entries
        )


__all__ = ["ShelfLineupEntry", "ShelfLineupError", "ShelfLineupPlan", "ShelfLineupWidget"]
