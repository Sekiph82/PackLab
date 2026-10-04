"""Offline, vector-preserving PDF presentation export through selected PySide6/Qt."""

from __future__ import annotations

import hashlib
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import cast

from .technical_drawing_export import TechnicalDrawingVectorExport

PDF_EXPORT_CONTRACT = "packlab.technical-drawing-pdf-export.v1"
_QT_APP = None


class DrawingPdfExportError(ValueError):
    """Raised when the approved Qt vector-PDF path is unavailable or invalid."""


@dataclass(frozen=True, slots=True)
class VectorPdfCapability:
    available: bool
    writer_available: bool
    svg_renderer_available: bool
    pdf_parser_available: bool
    route: str
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class TechnicalDrawingPdfExport:
    contract: str
    pdf_bytes: bytes
    manifest: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "pdf_sha256": hashlib.sha256(self.pdf_bytes).hexdigest(),
            "manifest": self.manifest,
            "raster_source_of_truth": False,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


def probe_vector_pdf_capability() -> VectorPdfCapability:
    """Observe the already-selected Qt writer, SVG renderer, and PDF parser APIs."""
    try:
        from PySide6.QtCore import QBuffer
        from PySide6.QtGui import QPdfWriter
        from PySide6.QtPdf import QPdfDocument
        from PySide6.QtSvg import QSvgRenderer

        return VectorPdfCapability(
            available=all((QBuffer, QPdfWriter, QPdfDocument, QSvgRenderer)),
            writer_available=callable(QPdfWriter),
            svg_renderer_available=callable(QSvgRenderer),
            pdf_parser_available=callable(QPdfDocument),
            route="PySide6.QtSvg.QSvgRenderer -> QPainter -> QtGui.QPdfWriter; QtPdf.QPdfDocument",
        )
    except Exception as error:
        return VectorPdfCapability(
            available=False,
            writer_available=False,
            svg_renderer_available=False,
            pdf_parser_available=False,
            route="PySide6/Qt offline vector route",
            error_code=f"qt_vector_pdf_unavailable:{type(error).__name__}",
        )


def export_technical_drawing_pdf(
    vector_export: TechnicalDrawingVectorExport,
) -> TechnicalDrawingPdfExport:
    """Render the authoritative SVG vector export into a single landscape A4 PDF page."""
    if not isinstance(vector_export, TechnicalDrawingVectorExport):
        raise DrawingPdfExportError("drawing_vector_export_required")
    capability = probe_vector_pdf_capability()
    if not capability.available:
        raise DrawingPdfExportError(capability.error_code or "qt_vector_pdf_unavailable")
    try:
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QMarginsF, QSize
        from PySide6.QtGui import (
            QColor,
            QGuiApplication,
            QPageLayout,
            QPageSize,
            QPainter,
            QPdfWriter,
        )
        from PySide6.QtPdf import QPdfDocument
        from PySide6.QtSvg import QSvgRenderer
    except Exception as error:
        raise DrawingPdfExportError("qt_vector_pdf_import_failed") from error

    global _QT_APP
    try:
        app = QGuiApplication.instance()
        if app is None:
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
            _QT_APP = QGuiApplication([])
            app = _QT_APP
        if app is None:
            raise DrawingPdfExportError("qt_gui_application_unavailable")

        renderer = QSvgRenderer(QByteArray(vector_export.svg_bytes))
        if not renderer.isValid():
            raise DrawingPdfExportError("drawing_svg_source_invalid")
        disclaimer = _source_disclaimer(vector_export.svg_bytes)
        if vector_export.coordinate_unit == "mm_unverified":
            disclaimer_valid = (
                "unverified against the physical benchmark" in disclaimer.casefold()
                and "mold" in disclaimer.casefold()
                and "manufacturing approval" in disclaimer.casefold()
            )
        else:
            disclaimer_valid = "reconstruction-relative" in disclaimer.casefold()
        if not disclaimer_valid:
            raise DrawingPdfExportError("drawing_pdf_authority_disclaimer_missing")
        view_box = renderer.viewBoxF()
        if view_box.width() <= 0.0 or view_box.height() <= 0.0:
            raise DrawingPdfExportError("drawing_svg_viewbox_invalid")

        buffer = QBuffer()
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            raise DrawingPdfExportError("pdf_memory_buffer_open_failed")
        writer = QPdfWriter(buffer)
        writer.setResolution(144)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Landscape)
        writer.setPageMargins(QMarginsF(8.0, 8.0, 8.0, 8.0), QPageLayout.Unit.Millimeter)
        writer.setTitle(str(vector_export.manifest["drawing_revision_id"]))
        writer.setCreator("PackLab")
        painter = QPainter()
        if not painter.begin(writer):
            raise DrawingPdfExportError("pdf_painter_begin_failed")
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        target = writer.pageLayout().paintRectPixels(writer.resolution())
        if target.width() <= 0 or target.height() <= 0:
            painter.end()
            raise DrawingPdfExportError("pdf_page_content_rect_invalid")
        renderer.render(painter, target)
        if not painter.end():
            raise DrawingPdfExportError("pdf_painter_finalize_failed")
        pdf_bytes = cast(bytes, buffer.data().data())
        buffer.close()
        if not pdf_bytes.startswith(b"%PDF-"):
            raise DrawingPdfExportError("pdf_header_invalid")

        pdf_buffer = QBuffer()
        pdf_buffer.setData(QByteArray(pdf_bytes))
        if not pdf_buffer.open(QIODevice.OpenModeFlag.ReadOnly):
            raise DrawingPdfExportError("pdf_parse_buffer_open_failed")
        document = QPdfDocument()
        document.load(pdf_buffer)
        app.processEvents()
        if document.status() is not QPdfDocument.Status.Ready or document.pageCount() != 1:
            raise DrawingPdfExportError("pdf_parse_or_page_count_failed")
        image = document.render(0, QSize(1200, 850))
        if image.isNull():
            raise DrawingPdfExportError("pdf_render_smoke_failed")
        render_bounds, ink_pixels = _ink_bounds(image, QColor)
        width, height = image.width(), image.height()
        if (
            ink_pixels < 64
            or render_bounds is None
            or render_bounds[0] < width * 0.005
            or render_bounds[1] < height * 0.005
            or render_bounds[2] > width * 0.995
            or render_bounds[3] > height * 0.995
        ):
            raise DrawingPdfExportError(
                f"pdf_render_clipping_or_empty_content:bounds={render_bounds};ink={ink_pixels};size={width}x{height}"
            )
    except DrawingPdfExportError:
        raise
    except Exception as error:
        raise DrawingPdfExportError(
            f"qt_vector_pdf_export_failed:{type(error).__name__}"
        ) from error

    manifest: dict[str, object] = {
        "contract": PDF_EXPORT_CONTRACT,
        "drawing_revision_id": vector_export.drawing_revision_id,
        "source_design_model_revision_id": vector_export.source_design_model_revision_id,
        "source_brep_revision_id": vector_export.source_brep_revision_id,
        "parent_authority": {
            "kind": vector_export.parent_kind,
            "revision_id": vector_export.parent_authority_revision_id,
        },
        "scale_state": vector_export.scale_state,
        "coordinate_unit": vector_export.coordinate_unit,
        "page_size": "A4",
        "orientation": "LANDSCAPE",
        "page_count": 1,
        "render_route": capability.route,
        "vector_source_format": "SVG",
        "visible_authority_disclaimer": disclaimer,
        "svg_source_sha256": hashlib.sha256(vector_export.svg_bytes).hexdigest(),
        "dxf_source_sha256": hashlib.sha256(vector_export.dxf_bytes).hexdigest(),
        "parsed_by_qtpdf": True,
        "render_smoke": {
            "status": "PASS",
            "pixel_size": [width, height],
            "ink_bounds": list(render_bounds),
            "ink_pixel_count": ink_pixels,
            "clipping_detected": False,
        },
        "rasterized_pdf_source": False,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "physical_accuracy_inferred": False,
        "manufacturing_suitability_inferred": False,
    }
    manifest["pdf_sha256"] = hashlib.sha256(pdf_bytes).hexdigest()
    return TechnicalDrawingPdfExport(PDF_EXPORT_CONTRACT, pdf_bytes, manifest)


def _ink_bounds(image: object, color_class: type) -> tuple[tuple[int, int, int, int] | None, int]:
    width = image.width()  # type: ignore[attr-defined]
    height = image.height()  # type: ignore[attr-defined]
    low_x, low_y, high_x, high_y = width, height, -1, -1
    count = 0
    for y in range(height):
        for x in range(width):
            pixel = image.pixelColor(x, y)  # type: ignore[attr-defined]
            if pixel.alpha() > 0 and pixel.lightness() < 245:
                low_x, low_y = min(low_x, x), min(low_y, y)
                high_x, high_y = max(high_x, x), max(high_y, y)
                count += 1
    if count == 0:
        return None, 0
    return (low_x, low_y, high_x, high_y), count


def _source_disclaimer(svg_bytes: bytes) -> str:
    try:
        root = ET.fromstring(svg_bytes)
    except ET.ParseError as error:
        raise DrawingPdfExportError("drawing_svg_source_invalid") from error
    return " ".join(
        "".join(element.itertext())
        for element in root.iter()
        if element.tag.endswith("text") and element.attrib.get("data-layer") == "TITLE_BLOCK"
    )


__all__ = [
    "PDF_EXPORT_CONTRACT",
    "DrawingPdfExportError",
    "TechnicalDrawingPdfExport",
    "VectorPdfCapability",
    "export_technical_drawing_pdf",
    "probe_vector_pdf_capability",
]
