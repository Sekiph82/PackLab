from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage
from tests.core.test_packaging_asset import _asset
from tests.studio.test_packaging_library_browser import _library

from packlab_studio.app import create_application
from packlab_studio.packaging_library_browser import (
    PackagingLibraryBrowserService,
    PreviewResult,
    PreviewState,
)
from packlab_studio.packaging_library_contact_sheet import (
    PackagingLibraryContactSheetError,
    PackagingLibraryContactSheetExporter,
)


def _png_bytes(color: Qt.GlobalColor) -> bytes:
    image = QImage(40, 30, QImage.Format.Format_RGB32)
    image.fill(color)
    buffer = QBuffer()
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    return bytes(buffer.data())


def test_mixed_sources_are_deterministic_and_manifest_is_path_private(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    create_application(["packlab-contact-sheet-test"])
    assets = (
        _asset(asset_id="thumb-asset", display_name="A Bottle"),
        _asset(asset_id="preview-asset", display_name="B Bottle"),
        _asset(asset_id="empty-asset", display_name="C Bottle"),
    )
    root = tmp_path / "library"
    store = _library(root, assets=assets)
    service = PackagingLibraryBrowserService(store, root)
    thumbnail = _png_bytes(Qt.GlobalColor.darkGreen)
    preview_image = QImage(40, 30, QImage.Format.Format_RGB32)
    preview_image.fill(Qt.GlobalColor.darkBlue)
    monkeypatch.setattr(
        service,
        "read_thumbnail_bytes",
        lambda summary: thumbnail if summary.asset_id == "thumb-asset" else None,
    )
    monkeypatch.setattr(
        service,
        "render_preview",
        lambda detail: (
            PreviewResult(PreviewState.AVAILABLE, preview_image)
            if detail.summary.asset_id == "preview-asset"
            else PreviewResult(PreviewState.UNAVAILABLE)
        ),
    )
    exporter = PackagingLibraryContactSheetExporter(service)

    first = exporter.export(tmp_path / "first")
    second = exporter.export(tmp_path / "second")
    assert [tile.source for tile in first.tiles] == [
        "DIGEST_VALID_LOCAL_THUMBNAIL",
        "LOCAL_VIEWPORT_PREVIEW",
        "DETERMINISTIC_PLACEHOLDER",
    ]
    assert first.contact_sheet_path.read_bytes() == second.contact_sheet_path.read_bytes()
    assert [
        path.read_bytes() for path in sorted((first.destination / "thumbnails").glob("*.png"))
    ] == [path.read_bytes() for path in sorted((second.destination / "thumbnails").glob("*.png"))]
    manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
    assert (
        manifest["contact_sheet"]["sha256"]
        == hashlib.sha256(first.contact_sheet_path.read_bytes()).hexdigest()
    )
    assert "first" not in first.manifest_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in first.manifest_path.read_text(encoding="utf-8")
    assert [item["revision_id"] for item in manifest["tiles"]] == [
        item.revision_id for item in first.tiles
    ]


def test_selected_assets_estimate_cue_and_empty_selection(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    create_application(["packlab-contact-sheet-selection-test"])
    asset = _asset(asset_id="estimated-bottle", display_name="Estimated Bottle")
    root = tmp_path / "library"
    store = _library(root, assets=(asset,))
    service = PackagingLibraryBrowserService(store, root)
    summary = service.list_assets()[0]
    estimated = replace(
        summary,
        field_provenance=summary.field_provenance + (("nominal_volume", "PACKLAB_ESTIMATE"),),
    )
    monkeypatch.setattr(service, "list_assets", lambda: (estimated,))
    exporter = PackagingLibraryContactSheetExporter(service)
    selected = exporter.export(tmp_path / "selected", selected_asset_ids=("estimated-bottle",))
    assert [tile.asset_id for tile in selected.tiles] == ["estimated-bottle"]
    manifest = json.loads(selected.manifest_path.read_text(encoding="utf-8"))
    assert "nominal_volume" in manifest["tiles"][0]["provenance_cues"]
    assert "[PackLab estimate]" in manifest["tiles"][0]["displayed_metadata"]["nominal_volume"]
    empty = exporter.export(tmp_path / "empty", selected_asset_ids=())
    assert empty.tiles == ()
    assert empty.contact_sheet_dimensions == (340, 120)
    assert json.loads(empty.manifest_path.read_text(encoding="utf-8"))["tiles"] == []


def test_selection_and_existing_destination_fail_closed(tmp_path: Path):
    create_application(["packlab-contact-sheet-safety-test"])
    root = tmp_path / "library"
    service = PackagingLibraryBrowserService(_library(root), root)
    exporter = PackagingLibraryContactSheetExporter(service)
    with pytest.raises(PackagingLibraryContactSheetError, match="asset_not_in_library"):
        exporter.export(tmp_path / "missing", selected_asset_ids=("missing-asset",))

    existing = tmp_path / "occupied"
    existing.mkdir()
    (existing / "keep.txt").write_text("owner file", encoding="utf-8")
    with pytest.raises(PackagingLibraryContactSheetError, match="destination_not_empty"):
        exporter.export(existing)
    assert (existing / "keep.txt").read_text(encoding="utf-8") == "owner file"
