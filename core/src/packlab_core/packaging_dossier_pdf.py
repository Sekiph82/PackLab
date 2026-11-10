"""Explicit in-memory PDF dossier export for immutable Packaging Asset V1 records."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import cast

from .packaging_asset import PackagingAsset

PACKAGING_DOSSIER_PDF_CONTRACT = "packlab.packaging-dossier-pdf.v1"
_QT_APP = None
_FIELD_LABELS = (
    ("display_name", "Display name"),
    ("family", "Package family"),
    ("other_family_label", "Other family"),
    ("nominal_volume", "Nominal volume"),
    ("supplier_id", "Supplier ID"),
    ("supplier_name", "Supplier name"),
    ("base_material", "Base material"),
    ("other_material_label", "Other material"),
    ("empty_package_weight", "Empty package weight"),
    ("overall_height", "Overall height"),
    ("body_diameter", "Body diameter"),
    ("neck_finish", "Neck finish"),
    ("neck_finish_diameter", "Neck finish diameter"),
    ("closure_type", "Closure type"),
    ("closure_description", "Closure description"),
    ("status", "Asset status"),
)
_DISCLAIMER = (
    "PACKAGING METADATA ONLY. This dossier does not establish physical accuracy, "
    "supplier certification, regulatory compliance, or manufacturing authorization."
)


class PackagingDossierPdfError(ValueError):
    """Raised when source identity or the local Qt PDF path is invalid."""


@dataclass(frozen=True, slots=True)
class PackagingDossierPdf:
    pdf_bytes: bytes
    manifest: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": PACKAGING_DOSSIER_PDF_CONTRACT,
            "pdf_sha256": hashlib.sha256(self.pdf_bytes).hexdigest(),
            "manifest": self.manifest,
            "physical_accuracy_verified": False,
            "supplier_certification_verified": False,
            "compliance_verified": False,
            "manufacturing_authorized": False,
        }


def export_packaging_dossier_pdf(asset: PackagingAsset) -> PackagingDossierPdf:
    """Render one immutable asset to PDF bytes; this function never writes a file."""
    if not isinstance(asset, PackagingAsset):
        raise PackagingDossierPdfError("packaging_asset_required")
    canonical_source = asset.canonical_json
    source_revision_id = asset.revision_id
    source_sha256 = hashlib.sha256(canonical_source.encode("utf-8")).hexdigest()
    if not source_revision_id.startswith("packaging-asset:"):
        raise PackagingDossierPdfError("packaging_asset_revision_identity_invalid")
    if source_revision_id.rsplit(":", 1)[-1] != source_sha256:
        raise PackagingDossierPdfError("packaging_asset_revision_digest_mismatch")

    try:
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QMarginsF, QSize, Qt
        from PySide6.QtGui import (
            QColor,
            QFont,
            QPageLayout,
            QPageSize,
            QPainter,
            QPdfWriter,
        )
        from PySide6.QtPdf import QPdfDocument
        from PySide6.QtWidgets import QApplication
    except Exception as error:
        raise PackagingDossierPdfError("qt_pdf_import_failed") from error

    global _QT_APP
    try:
        app = QApplication.instance()
        if app is None:
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
            _QT_APP = QApplication([])
            app = _QT_APP
        if app is None:
            raise PackagingDossierPdfError("qt_gui_application_unavailable")

        buffer = QBuffer()
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            raise PackagingDossierPdfError("pdf_memory_buffer_open_failed")
        writer = QPdfWriter(buffer)
        writer.setResolution(96)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Portrait)
        writer.setPageMargins(QMarginsF(12.0, 10.0, 12.0, 10.0), QPageLayout.Unit.Millimeter)
        writer.setTitle(f"PackLab dossier {asset.asset_id} {source_revision_id}")
        writer.setCreator("PackLab")

        painter = QPainter()
        if not painter.begin(writer):
            raise PackagingDossierPdfError("pdf_painter_begin_failed")
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        target = writer.pageLayout().paintRectPixels(writer.resolution())
        painter.setPen(QColor("#172033"))
        title_font = QFont("Arial", 15, QFont.Weight.Bold)
        body_font = QFont("Arial", 8)
        small_font = QFont("Arial", 7)
        x, y = target.left(), target.top()
        width = target.width()
        painter.setFont(title_font)
        painter.drawText(x, y + 22, "PackLab Packaging Technical Dossier")
        painter.setFont(body_font)
        y += 39
        painter.drawText(x, y, f"Asset: {asset.asset_id}    Revision: {source_revision_id}")
        y += 17
        painter.drawText(x, y, f"Source canonical SHA-256: {source_sha256}")
        y += 19
        painter.setPen(QColor("#9b1c1c"))
        painter.setFont(small_font)
        painter.drawText(x, y, width, 28, 0, _DISCLAIMER)
        painter.setPen(QColor("#172033"))
        y += 42

        values = _field_values(asset)
        split_at = (len(_FIELD_LABELS) + 1) // 2
        row_height = 38
        columns = ((_FIELD_LABELS[:split_at], x), (_FIELD_LABELS[split_at:], x + width // 2))
        half_width = width // 2 - 8
        for labels, column_x in columns:
            column_y = y
            for field_name, label in labels:
                value, provenance = values[field_name]
                painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
                painter.drawText(column_x, column_y + 9, label)
                painter.setFont(small_font)
                text = f"{value}  [{provenance}]"
                painter.drawText(
                    column_x,
                    column_y + 18,
                    half_width,
                    25,
                    Qt.TextFlag.TextWordWrap.value,
                    text,
                )
                column_y += row_height

        painter.setFont(small_font)
        painter.drawText(x, target.bottom() - 12, width, 10, 0, f"Contract: {asset.contract}")
        if not painter.end():
            raise PackagingDossierPdfError("pdf_painter_finalize_failed")
        pdf_bytes = cast(bytes, buffer.data().data())
        buffer.close()
        if not pdf_bytes.startswith(b"%PDF-"):
            raise PackagingDossierPdfError("pdf_header_invalid")

        parse_buffer = QBuffer()
        parse_buffer.setData(QByteArray(pdf_bytes))
        if not parse_buffer.open(QIODevice.OpenModeFlag.ReadOnly):
            raise PackagingDossierPdfError("pdf_parse_buffer_open_failed")
        document = QPdfDocument()
        document.load(parse_buffer)
        app.processEvents()
        if document.status() is not QPdfDocument.Status.Ready or document.pageCount() != 1:
            raise PackagingDossierPdfError("pdf_parse_or_page_count_failed")
        image = document.render(0, QSize(800, 1132))
        if image.isNull():
            raise PackagingDossierPdfError("pdf_render_smoke_failed")
    except PackagingDossierPdfError:
        raise
    except Exception as error:
        raise PackagingDossierPdfError(f"qt_pdf_export_failed:{type(error).__name__}") from error

    manifest: dict[str, object] = {
        "contract": PACKAGING_DOSSIER_PDF_CONTRACT,
        "asset_id": asset.asset_id,
        "asset_revision_id": source_revision_id,
        "source_canonical_sha256": source_sha256,
        "source_record": asset.as_dict(),
        "field_order": [field for field, _label in _FIELD_LABELS],
        "visible_disclaimer": _DISCLAIMER,
        "page_size": "A4",
        "orientation": "PORTRAIT",
        "page_count": 1,
        "parsed_by_qtpdf": True,
        "render_smoke": "PASS",
        "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "filesystem_write_performed": False,
        "physical_accuracy_verified": False,
        "supplier_certification_verified": False,
        "compliance_verified": False,
        "manufacturing_authorized": False,
    }
    return PackagingDossierPdf(pdf_bytes, manifest)


def _field_values(asset: PackagingAsset) -> dict[str, tuple[str, str]]:
    values = asset.as_dict()
    dimensions = values["dimensions"]
    neck_closure = values["neck_closure"]
    supplier = values["supplier"]
    assert isinstance(dimensions, dict)
    assert isinstance(neck_closure, dict)
    assert isinstance(supplier, dict)
    raw = {
        "display_name": values["display_name"],
        "family": values["family"],
        "other_family_label": values["other_family_label"],
        "nominal_volume": values["nominal_volume"],
        "supplier_id": supplier["supplier_id"],
        "supplier_name": supplier["name"],
        "base_material": values["base_material"],
        "other_material_label": values["other_material_label"],
        "empty_package_weight": values["empty_package_weight"],
        "overall_height": dimensions["overall_height"],
        "body_diameter": dimensions["body_diameter"],
        "neck_finish": neck_closure["neck_finish"],
        "neck_finish_diameter": neck_closure["neck_finish_diameter"],
        "closure_type": neck_closure["closure_type"],
        "closure_description": neck_closure["closure_description"],
        "status": values["status"],
    }
    provenance = {item["field_name"]: item["classification"] for item in values["field_provenance"]}
    result: dict[str, tuple[str, str]] = {}
    for field_name, _label in _FIELD_LABELS:
        value = raw[field_name]
        if isinstance(value, dict):
            display = f"{value['value']} {value['unit']}"
        else:
            display = "UNKNOWN" if value is None else str(value)
        result[field_name] = (display, str(provenance.get(field_name, "UNKNOWN")))
    return result


__all__ = [
    "PACKAGING_DOSSIER_PDF_CONTRACT",
    "PackagingDossierPdf",
    "PackagingDossierPdfError",
    "export_packaging_dossier_pdf",
]
