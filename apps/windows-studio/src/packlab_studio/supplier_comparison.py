"""Descriptive, provenance-preserving comparison of immutable package records."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from packlab_core.packaging_asset import PackagingAsset, PackagingMeasurement, ProvenanceClass

_FIELDS = (
    ("supplier_name", "Supplier name"),
    ("supplier_id", "Supplier ID"),
    ("family", "Package family"),
    ("nominal_volume", "Nominal volume"),
    ("overall_height", "Overall height"),
    ("body_diameter", "Body diameter"),
    ("empty_package_weight", "Empty package weight"),
    ("base_material", "Base material"),
    ("closure_type", "Closure type"),
    ("status", "Asset status"),
)


class SupplierComparisonError(ValueError):
    """Raised for duplicate, missing or malformed package comparison inputs."""


@dataclass(frozen=True, slots=True)
class SupplierComparisonCell:
    field: str
    display_value: str
    provenance: str


@dataclass(frozen=True, slots=True)
class SupplierComparisonColumn:
    asset_id: str
    asset_revision_id: str
    display_name: str
    cells: tuple[SupplierComparisonCell, ...]


@dataclass(frozen=True, slots=True)
class SupplierComparisonReport:
    columns: tuple[SupplierComparisonColumn, ...]

    @classmethod
    def create(cls, assets: tuple[PackagingAsset, ...]) -> SupplierComparisonReport:
        if not isinstance(assets, tuple) or len(assets) < 2:
            raise SupplierComparisonError("supplier_comparison_requires_two_assets")
        if any(not isinstance(asset, PackagingAsset) for asset in assets):
            raise SupplierComparisonError("supplier_comparison_immutable_assets_required")
        revision_ids = tuple(asset.revision_id for asset in assets)
        if len(set(revision_ids)) != len(revision_ids):
            raise SupplierComparisonError("supplier_comparison_duplicate_asset_revision")
        columns = tuple(
            SupplierComparisonColumn(
                asset_id=asset.asset_id,
                asset_revision_id=asset.revision_id,
                display_name=asset.display_name,
                cells=tuple(
                    SupplierComparisonCell(
                        field,
                        _display_value(asset, field),
                        _field_provenance(asset, field).value,
                    )
                    for field, _label in _FIELDS
                ),
            )
            for asset in assets
        )
        return cls(columns)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.supplier-comparison.v1",
            "authority": "DESCRIPTIVE_NON_AUTHORITATIVE",
            "ranked": False,
            "recommendation": None,
            "columns": [
                {
                    "asset_id": column.asset_id,
                    "asset_revision_id": column.asset_revision_id,
                    "display_name": column.display_name,
                    "fields": [
                        {
                            "field": cell.field,
                            "value": cell.display_value,
                            "provenance": cell.provenance,
                        }
                        for cell in column.cells
                    ],
                }
                for column in self.columns
            ],
        }


def _display_value(asset: PackagingAsset, field: str) -> str:
    value = getattr(asset, field)
    if value is None:
        return "UNKNOWN"
    if isinstance(value, PackagingMeasurement):
        return f"{value.value:g} {value.unit.value}"
    enum_value = getattr(value, "value", value)
    if enum_value == "UNKNOWN":
        return "UNKNOWN"
    return str(enum_value)


def _field_provenance(asset: PackagingAsset, field: str) -> ProvenanceClass:
    matching = tuple(item for item in asset.field_provenance if item.field_name == field)
    if len(matching) > 1:
        raise SupplierComparisonError("supplier_comparison_field_provenance_ambiguous")
    return matching[0].classification if matching else ProvenanceClass.UNKNOWN


class SupplierComparisonWidget(QWidget):
    """In-memory table with exact revisions and field provenance in each cell."""

    def __init__(self, report: SupplierComparisonReport, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if not isinstance(report, SupplierComparisonReport):
            raise SupplierComparisonError("supplier_comparison_report_required")
        self.report = report
        self.authority_label = QLabel(
            "DESCRIPTIVE COMPARISON · NON-AUTHORITATIVE · NO RANKING OR RECOMMENDATION"
        )
        self.limitation_label = QLabel(
            "Does not establish supplier eligibility, compliance, quality, price, availability, or suitability."
        )
        self.limitation_label.setWordWrap(True)
        self.table = QTableWidget(len(_FIELDS), len(report.columns) + 1, self)
        self.table.setHorizontalHeaderLabels(
            ["Field"]
            + [
                f"{column.display_name}\n{column.asset_id}\n{column.asset_revision_id}"
                for column in report.columns
            ]
        )
        self.table.setVerticalHeaderLabels([""] * len(_FIELDS))
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setWordWrap(True)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        for row, (field, label) in enumerate(_FIELDS):
            self.table.setItem(row, 0, QTableWidgetItem(label))
            for column_index, column in enumerate(report.columns, 1):
                cell = next(item for item in column.cells if item.field == field)
                self.table.setItem(
                    row,
                    column_index,
                    QTableWidgetItem(f"{cell.display_value}\nProvenance: {cell.provenance}"),
                )
        self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setToolTip("Values retain their source units and are not normalized or ranked.")
        layout = QVBoxLayout(self)
        layout.addWidget(self.authority_label)
        layout.addWidget(self.limitation_label)
        layout.addWidget(self.table)


__all__ = [
    "SupplierComparisonCell",
    "SupplierComparisonColumn",
    "SupplierComparisonError",
    "SupplierComparisonReport",
    "SupplierComparisonWidget",
]
