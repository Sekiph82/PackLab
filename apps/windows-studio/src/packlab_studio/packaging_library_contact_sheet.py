"""Deterministic, local-only Packaging Library thumbnail and contact-sheet export."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QPainter

from .packaging_library_browser import (
    PackagingLibraryAssetSummary,
    PackagingLibraryBrowserService,
    PreviewState,
)

_THUMBNAIL_SIZE = (256, 160)
_TILE_SIZE = (340, 316)
_COLUMNS = 3
_ESTIMATE_CLASSIFICATIONS = {"PACKLAB_ESTIMATE", "PACKLAB_ESTIMATED"}


class PackagingLibraryContactSheetError(ValueError):
    """Raised when the requested export cannot be produced safely."""


@dataclass(frozen=True, slots=True)
class ExportedTile:
    asset_id: str
    revision_id: str
    image_path: str
    image_sha256: str
    image_dimensions: tuple[int, int]
    source: str
    provenance_cues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContactSheetExport:
    destination: Path
    manifest_path: Path
    contact_sheet_path: Path
    contact_sheet_sha256: str
    contact_sheet_dimensions: tuple[int, int]
    tiles: tuple[ExportedTile, ...]


class PackagingLibraryContactSheetExporter:
    """Export digest-bound local thumbnails and metadata cards to an explicit destination."""

    def __init__(self, browser: PackagingLibraryBrowserService) -> None:
        if not isinstance(browser, PackagingLibraryBrowserService):
            raise PackagingLibraryContactSheetError("contact_sheet_browser_required")
        self.browser = browser

    def export(
        self,
        destination: str | Path,
        *,
        selected_asset_ids: tuple[str, ...] | None = None,
    ) -> ContactSheetExport:
        """Write a complete export directory at the caller-selected path.

        ``None`` selects every library asset; a tuple selects exactly those IDs.
        A missing destination is created. Existing non-empty directories are never
        overwritten, so a prior export cannot be silently replaced.
        """
        target = Path(destination).expanduser().absolute()
        summaries = self._selected_summaries(selected_asset_ids)
        if target.exists():
            if not target.is_dir() or target.is_symlink() or any(target.iterdir()):
                raise PackagingLibraryContactSheetError("contact_sheet_destination_not_empty")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)

        target.mkdir(parents=True, exist_ok=True)
        tile_dir = target / "thumbnails"
        tile_dir.mkdir()

        tiles: list[ExportedTile] = []
        tile_images: list[tuple[PackagingLibraryAssetSummary, QImage, ExportedTile]] = []
        for summary in summaries:
            image, source = self._source_image(summary)
            thumbnail = _fit_image(image, *_THUMBNAIL_SIZE)
            image_bytes = _png_bytes(thumbnail)
            logical_id = hashlib.sha256(summary.asset_id.encode("utf-8")).hexdigest()[:16]
            relative_path = f"thumbnails/{logical_id}.png"
            (target / relative_path).write_bytes(image_bytes)
            cues = _provenance_cues(summary)
            record = ExportedTile(
                summary.asset_id,
                summary.revision_id,
                relative_path,
                hashlib.sha256(image_bytes).hexdigest(),
                _THUMBNAIL_SIZE,
                source,
                cues,
            )
            tiles.append(record)
            tile_images.append((summary, thumbnail, record))

        sheet = _contact_sheet(tile_images)
        sheet_bytes = _png_bytes(sheet)
        sheet_path = target / "contact-sheet.png"
        sheet_path.write_bytes(sheet_bytes)
        manifest = {
            "schema": "packlab.packaging-library-contact-sheet.v1",
            "contact_sheet": {
                "path": "contact-sheet.png",
                "sha256": hashlib.sha256(sheet_bytes).hexdigest(),
                "dimensions": list(sheet.size().toTuple()),
            },
            "tiles": [
                {
                    "asset_id": tile.asset_id,
                    "revision_id": tile.revision_id,
                    "path": tile.image_path,
                    "sha256": tile.image_sha256,
                    "dimensions": list(tile.image_dimensions),
                    "source": tile.source,
                    "displayed_metadata": _metadata(summaries[index], tile.provenance_cues),
                    "provenance_cues": list(tile.provenance_cues),
                }
                for index, tile in enumerate(tiles)
            ],
        }
        manifest_path = target / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return ContactSheetExport(
            target,
            manifest_path,
            sheet_path,
            hashlib.sha256(sheet_bytes).hexdigest(),
            sheet.size().toTuple(),
            tuple(tiles),
        )

    def _selected_summaries(
        self, selected_asset_ids: tuple[str, ...] | None
    ) -> tuple[PackagingLibraryAssetSummary, ...]:
        available = {summary.asset_id: summary for summary in self.browser.list_assets()}
        if selected_asset_ids is None:
            chosen = tuple(available.values())
        else:
            if not isinstance(selected_asset_ids, tuple) or any(
                not isinstance(asset_id, str) or not asset_id for asset_id in selected_asset_ids
            ):
                raise PackagingLibraryContactSheetError("contact_sheet_selection_invalid")
            if len(selected_asset_ids) != len(set(selected_asset_ids)):
                raise PackagingLibraryContactSheetError("contact_sheet_selection_duplicate")
            missing = set(selected_asset_ids) - set(available)
            if missing:
                raise PackagingLibraryContactSheetError("contact_sheet_asset_not_in_library")
            chosen = tuple(available[asset_id] for asset_id in selected_asset_ids)
        return tuple(sorted(chosen, key=lambda item: (item.display_name.casefold(), item.asset_id)))

    def _source_image(self, summary: PackagingLibraryAssetSummary) -> tuple[QImage, str]:
        try:
            payload = self.browser.read_thumbnail_bytes(summary)
        except Exception:
            payload = None
        if payload:
            image = QImage()
            if image.loadFromData(payload) and _valid_source_image(image):
                return image, "DIGEST_VALID_LOCAL_THUMBNAIL"

        try:
            preview = self.browser.render_preview(self.browser.asset_detail(summary))
        except Exception:
            preview = None
        if (
            preview is not None
            and preview.state == PreviewState.AVAILABLE
            and isinstance(preview.image, QImage)
            and _valid_source_image(preview.image)
        ):
            return preview.image.copy(), "LOCAL_VIEWPORT_PREVIEW"
        return _placeholder(summary), "DETERMINISTIC_PLACEHOLDER"


def _valid_source_image(image: QImage) -> bool:
    return (
        not image.isNull()
        and 0 < image.width() <= 4096
        and 0 < image.height() <= 4096
        and image.width() * image.height() <= 4_194_304
    )


def _fit_image(source: QImage, width: int, height: int) -> QImage:
    result = QImage(width, height, QImage.Format.Format_ARGB32)
    result.fill(QColor("#f2f4f5"))
    painter = QPainter(result)
    scaled = source.scaled(
        width - 12,
        height - 12,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = (width - scaled.width()) // 2
    y = (height - scaled.height()) // 2
    painter.drawImage(x, y, scaled)
    painter.end()
    return result


def _png_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly) or not image.save(  # type: ignore[call-overload]
        buffer, "PNG"
    ):
        raise PackagingLibraryContactSheetError("contact_sheet_png_encode_failed")
    return buffer.data().data()


def _provenance_cues(summary: PackagingLibraryAssetSummary) -> tuple[str, ...]:
    provenance = dict(summary.field_provenance)
    fields = {
        "nominal_volume": ("nominal_volume",),
        "material": ("base_material", "material"),
        "closure": ("closure", "closure_type"),
        "supplier": ("supplier_name", "supplier"),
    }
    return tuple(
        label
        for label, aliases in fields.items()
        if any(provenance.get(key) in _ESTIMATE_CLASSIFICATIONS for key in aliases)
    )


def _metadata(summary: PackagingLibraryAssetSummary, cues: tuple[str, ...]) -> dict[str, str]:
    cue_set = set(cues)

    def display(label: str, value: str) -> str:
        return f"{value} [PackLab estimate]" if label in cue_set else value

    material = summary.material_other_label or summary.base_material
    return {
        "supplier": display("supplier", summary.supplier_name or "UNKNOWN"),
        "nominal_volume": display("nominal_volume", summary.nominal_volume),
        "material": display("material", material),
        "closure": display("closure", summary.closure),
    }


def _placeholder(summary: PackagingLibraryAssetSummary) -> QImage:
    image = QImage(480, 300, QImage.Format.Format_ARGB32)
    image.fill(QColor("#e7ebee"))
    painter = QPainter(image)
    painter.setPen(QColor("#58636d"))
    painter.setFont(QFont("Arial", 15))
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "No local preview")
    painter.end()
    return image


def _contact_sheet(
    tiles: list[tuple[PackagingLibraryAssetSummary, QImage, ExportedTile]],
) -> QImage:
    if not tiles:
        image = QImage(_TILE_SIZE[0], 120, QImage.Format.Format_ARGB32)
        image.fill(QColor("white"))
        painter = QPainter(image)
        painter.setPen(QColor("#303840"))
        painter.setFont(QFont("Arial", 14))
        painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "No assets selected")
        painter.end()
        return image

    columns = min(_COLUMNS, len(tiles))
    rows = (len(tiles) + columns - 1) // columns
    image = QImage(columns * _TILE_SIZE[0], rows * _TILE_SIZE[1], QImage.Format.Format_ARGB32)
    image.fill(QColor("#dfe4e8"))
    painter = QPainter(image)
    painter.setPen(QColor("#202830"))
    painter.setFont(QFont("Arial", 10))
    metrics = QFontMetrics(painter.font())
    for index, (summary, thumbnail, record) in enumerate(tiles):
        x = (index % columns) * _TILE_SIZE[0]
        y = (index // columns) * _TILE_SIZE[1]
        painter.fillRect(x + 6, y + 6, _TILE_SIZE[0] - 12, _TILE_SIZE[1] - 12, QColor("white"))
        painter.drawImage(x + 42, y + 14, thumbnail)
        metadata = _metadata(summary, record.provenance_cues)
        lines = [
            f"ID: {summary.asset_id}",
            f"Name: {summary.display_name}",
            f"Supplier: {metadata['supplier']}",
            f"Volume: {metadata['nominal_volume']}",
            f"Material: {metadata['material']}",
            f"Closure: {metadata['closure']}",
        ]
        for line_index, line in enumerate(lines):
            suffix = " [PackLab estimate]" if " [PackLab estimate]" in line else ""
            prefix = line[: -len(suffix)] if suffix else line
            available_width = _TILE_SIZE[0] - 28 - metrics.horizontalAdvance(suffix)
            text = metrics.elidedText(prefix, Qt.TextElideMode.ElideRight, available_width) + suffix
            painter.drawText(x + 14, y + 184 + line_index * 20, text)
    painter.end()
    return image
