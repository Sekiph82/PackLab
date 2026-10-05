"""Project-independent Packaging Library browser service and PySide6 view."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt, Signal
from PySide6.QtGui import QImageReader, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_THUMBNAIL_BYTES = 8 * 1024 * 1024
_MAX_THUMBNAIL_DIMENSION = 4096
_MAX_THUMBNAIL_PIXELS = 4_194_304
_MAX_SEARCH_QUERY_LENGTH = 128


class PackagingLibraryBrowserError(ValueError):
    """Raised when the injected library authority cannot supply a safe asset view."""


class ThumbnailSource(StrEnum):
    LIBRARY = "LIBRARY"
    PROJECT = "PROJECT"


class BrowserDisplayState(StrEnum):
    LOADING = "LOADING"
    READY = "READY"
    EMPTY = "EMPTY"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class PackagingLibraryFilters:
    """Single-select filter values; UNKNOWN is distinct from an inactive filter."""

    nominal_volume: tuple[float, str] | str | None = None
    material: str | None = None
    closure: str | None = None
    status: str | None = None

    def __post_init__(self) -> None:
        volume = self.nominal_volume
        if volume is None or volume == "UNKNOWN":
            return
        if (
            not isinstance(volume, tuple)
            or len(volume) != 2
            or isinstance(volume[0], bool)
            or not isinstance(volume[0], (int, float))
            or not math.isfinite(float(volume[0]))
            or float(volume[0]) <= 0
            or volume[1] not in {"mL", "L"}
        ):
            raise PackagingLibraryBrowserError(
                "library_filter_volume_requires_explicit_value_and_unit"
            )


@dataclass(frozen=True, slots=True)
class LibraryThumbnailReference:
    """Digest-bound local image reference; never a URL or absolute path."""

    sha256: str
    media_type: str
    relative_path: str
    source: ThumbnailSource
    project_id: str | None = None
    revision_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.sha256, str) or not _SHA256.fullmatch(self.sha256):
            raise PackagingLibraryBrowserError("library_thumbnail_digest_invalid")
        if not isinstance(self.media_type, str) or self.media_type not in {
            "image/png",
            "image/jpeg",
        }:
            raise PackagingLibraryBrowserError("library_thumbnail_media_type_invalid")
        if not isinstance(self.source, ThumbnailSource):
            raise PackagingLibraryBrowserError("library_thumbnail_source_invalid")
        path = _safe_relative_path(self.relative_path)
        if self.source is ThumbnailSource.LIBRARY:
            suffix = ".png" if self.media_type == "image/png" else ".jpg"
            expected = PurePosixPath("thumbnails", "sha256", self.sha256[:2], self.sha256 + suffix)
            if path != expected or self.project_id is not None or self.revision_id is not None:
                raise PackagingLibraryBrowserError("library_thumbnail_library_path_invalid")
        else:
            _identifier(self.project_id, "project")
            _identifier(self.revision_id, "revision")


@dataclass(frozen=True, slots=True)
class PackagingLibraryAssetSummary:
    asset_id: str
    revision_id: str
    display_name: str
    family: str
    base_material: str
    nominal_volume: str
    nominal_volume_value: float | None
    nominal_volume_unit: str | None
    status: str
    supplier_id: str = ""
    supplier_name: str = ""
    material_other_label: str = ""
    closure: str = "UNKNOWN"
    field_provenance: tuple[tuple[str, str], ...] = ()
    thumbnail_reference: LibraryThumbnailReference | None = None
    source_project_revisions: tuple[tuple[str, str], ...] = ()

    @property
    def core_metadata(self) -> str:
        return f"{self.family} · {self.base_material} · {self.nominal_volume} · {self.status}"


class PackagingLibraryBrowserService:
    """Read asset summaries from the audit store and resolve only digest-checked local images."""

    def __init__(
        self,
        audit_store: Any,
        library_root: str | Path,
        *,
        thumbnail_reference_provider: Callable[[str], LibraryThumbnailReference | None]
        | None = None,
        project_root_resolver: Callable[[str], Path | None] | None = None,
    ) -> None:
        if audit_store is None or not callable(getattr(audit_store, "snapshot", None)):
            raise PackagingLibraryBrowserError("library_browser_audit_store_required")
        root = Path(library_root).expanduser().absolute()
        if root.exists() and root.is_symlink():
            raise PackagingLibraryBrowserError("library_browser_root_symlink_forbidden")
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink() or not root.is_dir():
            raise PackagingLibraryBrowserError("library_browser_root_invalid")
        self.audit_store = audit_store
        self.library_root = root
        self.thumbnail_reference_provider = thumbnail_reference_provider
        self.project_root_resolver = project_root_resolver

    def list_assets(self) -> tuple[PackagingLibraryAssetSummary, ...]:
        snapshot = self.audit_store.snapshot()
        summaries: list[PackagingLibraryAssetSummary] = []
        for entry in snapshot.assets:
            try:
                document = json.loads(entry.canonical_json)
                if (
                    not isinstance(document, dict)
                    or document.get("asset_id") != entry.asset_id
                    or not isinstance(document.get("display_name"), str)
                ):
                    raise PackagingLibraryBrowserError("library_browser_asset_document_invalid")
                nominal = document.get("nominal_volume")
                volume_value = (
                    float(nominal["value"])
                    if isinstance(nominal, dict)
                    and isinstance(nominal.get("value"), (int, float))
                    and not isinstance(nominal.get("value"), bool)
                    else None
                )
                volume_unit = (
                    nominal.get("unit")
                    if isinstance(nominal, dict) and isinstance(nominal.get("unit"), str)
                    else None
                )
                nominal_volume = (
                    f"{nominal['value']:g} {nominal['unit']}"
                    if isinstance(nominal, dict)
                    and isinstance(nominal.get("value"), (int, float))
                    and isinstance(nominal.get("unit"), str)
                    else "Unknown volume"
                )
                source_projects = _source_project_revisions(document.get("source_links"))
                neck_closure = document.get("neck_closure")
                field_provenance = _field_provenance(document.get("field_provenance"))
                thumbnail: LibraryThumbnailReference | None = None
                if self.thumbnail_reference_provider is not None:
                    try:
                        candidate = self.thumbnail_reference_provider(entry.asset_id)
                        if isinstance(candidate, LibraryThumbnailReference) and (
                            candidate.source is ThumbnailSource.LIBRARY
                            or (candidate.project_id, candidate.revision_id) in source_projects
                        ):
                            thumbnail = candidate
                    except Exception:
                        thumbnail = None
                summaries.append(
                    PackagingLibraryAssetSummary(
                        asset_id=entry.asset_id,
                        revision_id=entry.revision_id,
                        display_name=document["display_name"],
                        family=_display_value(document.get("family")),
                        base_material=_display_value(document.get("base_material")),
                        nominal_volume=nominal_volume,
                        nominal_volume_value=volume_value,
                        nominal_volume_unit=volume_unit,
                        status=_display_value(document.get("status")),
                        supplier_id=_supplier_value(document.get("supplier"), "supplier_id"),
                        supplier_name=_supplier_value(document.get("supplier"), "name"),
                        material_other_label=_display_value(document.get("other_material_label")),
                        closure=(
                            _display_value(neck_closure.get("closure_type"))
                            if isinstance(neck_closure, dict)
                            else "UNKNOWN"
                        ),
                        field_provenance=field_provenance,
                        thumbnail_reference=thumbnail,
                        source_project_revisions=source_projects,
                    )
                )
            except (ValueError, KeyError, TypeError) as error:
                raise PackagingLibraryBrowserError("library_browser_asset_entry_invalid") from error
        return tuple(
            sorted(summaries, key=lambda item: (item.display_name.casefold(), item.asset_id))
        )

    def search_assets(self, query: str) -> tuple[PackagingLibraryAssetSummary, ...]:
        """Search locally loaded metadata without reading attachments or changing state."""
        return self.filter_assets(self.list_assets(), query=query)

    def filter_assets(
        self,
        assets: tuple[PackagingLibraryAssetSummary, ...],
        *,
        query: str = "",
        filters: PackagingLibraryFilters | None = None,
    ) -> tuple[PackagingLibraryAssetSummary, ...]:
        """Apply normalized search and composable, exact metadata filters."""
        if not isinstance(query, str) or len(query) > _MAX_SEARCH_QUERY_LENGTH:
            raise PackagingLibraryBrowserError("library_search_query_invalid_or_too_long")
        if not isinstance(assets, tuple) or any(
            not isinstance(asset, PackagingLibraryAssetSummary) for asset in assets
        ):
            raise PackagingLibraryBrowserError("library_filter_asset_records_invalid")
        active_filters = filters or PackagingLibraryFilters()
        if not isinstance(active_filters, PackagingLibraryFilters):
            raise PackagingLibraryBrowserError("library_filter_selection_invalid")
        normalized_query = _normalize_search_text(query)
        return tuple(
            sorted(
                (
                    asset
                    for asset in assets
                    if (
                        (
                            not normalized_query
                            or any(
                                normalized_query in _normalize_search_text(value)
                                for value in (
                                    asset.asset_id,
                                    asset.display_name,
                                    asset.supplier_id,
                                    asset.supplier_name,
                                    asset.family,
                                )
                                if value
                            )
                        )
                        and _matches_library_filters(asset, active_filters)
                    )
                ),
                key=lambda item: (item.display_name.casefold(), item.asset_id),
            )
        )

    def resolve_thumbnail(self, asset: PackagingLibraryAssetSummary) -> Path | None:
        resolved = self._thumbnail_location(asset)
        if resolved is None:
            return None
        _reference, _root, candidate = resolved
        if self.read_thumbnail_bytes(asset) is None:
            return None
        return candidate

    def read_thumbnail_bytes(self, asset: PackagingLibraryAssetSummary) -> bytes | None:
        """Return only bounded bytes whose digest still matches the local reference."""
        resolved = self._thumbnail_location(asset)
        if resolved is None:
            return None
        reference, root, candidate = resolved
        try:
            initial = _ensure_safe_local_file(root, candidate)
            descriptor = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                opened = os.fstat(descriptor)
                if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
                    initial.st_dev,
                    initial.st_ino,
                ):
                    return None
                digest = hashlib.sha256()
                content = bytearray()
                with os.fdopen(descriptor, "rb") as stream:
                    descriptor = -1
                    while chunk := stream.read(1024 * 1024):
                        content.extend(chunk)
                        if len(content) > _MAX_THUMBNAIL_BYTES:
                            return None
                        digest.update(chunk)
                if digest.hexdigest() != reference.sha256 or not content:
                    return None
                return bytes(content)
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
        except (OSError, ValueError, PackagingLibraryBrowserError):
            return None

    def _thumbnail_location(
        self, asset: PackagingLibraryAssetSummary
    ) -> tuple[LibraryThumbnailReference, Path, Path] | None:
        reference = asset.thumbnail_reference
        if reference is None:
            return None
        if reference.source is ThumbnailSource.LIBRARY:
            root = self.library_root
        else:
            if (
                self.project_root_resolver is None
                or (reference.project_id, reference.revision_id)
                not in asset.source_project_revisions
            ):
                return None
            project_root = self.project_root_resolver(reference.project_id or "")
            if project_root is None:
                return None
            if (
                not isinstance(project_root, Path)
                or project_root.is_symlink()
                or not project_root.is_dir()
            ):
                return None
            root = project_root.absolute()
        try:
            candidate = root.joinpath(*PurePosixPath(reference.relative_path).parts)
            _ensure_safe_local_file(root, candidate)
            if candidate.stat().st_size > _MAX_THUMBNAIL_BYTES:
                return None
            return reference, root, candidate
        except (OSError, ValueError, PackagingLibraryBrowserError):
            return None


class PackagingLibraryBrowserView(QWidget):
    """Grid/list browser with stable selection and deterministic local-thumbnail fallback."""

    selection_changed = Signal(str)

    def __init__(
        self,
        service: PackagingLibraryBrowserService | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("packlab.view.library")
        self.service = service
        self._summaries: tuple[PackagingLibraryAssetSummary, ...] = ()
        self._selected_asset_id: str | None = None
        self.display_state = BrowserDisplayState.LOADING

        self.mode_selector = QComboBox(self)
        self.mode_selector.setObjectName("packlab.library.mode")
        self.mode_selector.addItem("Grid", "grid")
        self.mode_selector.addItem("List", "list")
        self.search_field = QLineEdit(self)
        self.search_field.setObjectName("packlab.library.search")
        self.search_field.setPlaceholderText("Search ID, name, supplier, or family")
        self.search_field.setMaxLength(_MAX_SEARCH_QUERY_LENGTH)
        self.volume_filter = _filter_combo(self, "volume", "Any volume")
        self.material_filter = _filter_combo(self, "material", "Any material")
        self.closure_filter = _filter_combo(self, "closure", "Any closure")
        self.status_filter = _filter_combo(self, "status", "Any status")
        self.clear_filters_button = QPushButton("Clear filters", self)
        self.clear_filters_button.setObjectName("packlab.library.clear-filters")
        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.setObjectName("packlab.library.refresh")
        self.selection_summary = QLabel("No asset selected.", self)
        self.selection_summary.setObjectName("packlab.library.selection")
        self.item_view = QListWidget(self)
        self.item_view.setObjectName("packlab.library.assets")
        self.item_view.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.item_view.setViewMode(QListWidget.ViewMode.IconMode)
        self.item_view.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.item_view.setMovement(QListWidget.Movement.Static)
        self.item_view.setIconSize(QSize(128, 96))
        self.item_view.setGridSize(QSize(220, 190))
        self.item_view.setWordWrap(True)
        self.state_view = QStackedWidget(self)
        self.state_view.setObjectName("packlab.library.state")
        self.state_message = QLabel("Loading Packaging Library…", self)
        self.state_message.setObjectName("packlab.library.state-message")
        self.state_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_view.addWidget(self.item_view)
        self.state_view.addWidget(self.state_message)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.mode_selector)
        toolbar.addWidget(self.search_field, 1)
        toolbar.addWidget(self.refresh_button)
        toolbar.addStretch(1)
        filter_toolbar = QHBoxLayout()
        for combo in (
            self.volume_filter,
            self.material_filter,
            self.closure_filter,
            self.status_filter,
        ):
            filter_toolbar.addWidget(combo)
        filter_toolbar.addWidget(self.clear_filters_button)
        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addLayout(filter_toolbar)
        layout.addWidget(self.state_view, 1)
        layout.addWidget(self.selection_summary)

        self.mode_selector.currentIndexChanged.connect(self._set_mode)
        self.search_field.textChanged.connect(self.refresh)
        for combo in (
            self.volume_filter,
            self.material_filter,
            self.closure_filter,
            self.status_filter,
        ):
            combo.currentIndexChanged.connect(self.refresh)
        self.clear_filters_button.clicked.connect(self._clear_filters)
        self.refresh_button.clicked.connect(self.refresh)
        self.item_view.currentItemChanged.connect(self._selection_changed)
        self.refresh()

    @property
    def selected_asset_id(self) -> str | None:
        item = self.item_view.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else None

    def _replace_filter_options(
        self,
        combo: QComboBox,
        any_label: str,
        values: tuple[object, ...],
        label_for: Callable[[object], str],
    ) -> None:
        selected = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(any_label, None)
        for value in values:
            combo.addItem(label_for(value), value)
        for index in range(combo.count()):
            if combo.itemData(index) == selected:
                combo.setCurrentIndex(index)
                break
        combo.blockSignals(False)

    def _sync_filter_options(self, assets: tuple[PackagingLibraryAssetSummary, ...]) -> None:
        volumes = sorted(
            {
                (asset.nominal_volume_value, asset.nominal_volume_unit)
                for asset in assets
                if asset.nominal_volume_value is not None and asset.nominal_volume_unit is not None
            },
            key=lambda item: (item[1], item[0]),
        )
        volume_options: tuple[object, ...] = ("UNKNOWN", *volumes)
        self._replace_filter_options(
            self.volume_filter,
            "Any volume",
            volume_options,
            _volume_filter_label,
        )
        for combo, label, field in (
            (self.material_filter, "Any material", "base_material"),
            (self.closure_filter, "Any closure", "closure"),
            (self.status_filter, "Any status", "status"),
        ):
            options = {getattr(asset, field) for asset in assets}
            options.add("UNKNOWN")
            values = tuple(sorted(options))
            self._replace_filter_options(
                combo,
                label,
                values,
                lambda value: "Unknown" if value == "UNKNOWN" else str(value),
            )

    def _selected_filters(self) -> PackagingLibraryFilters:
        return PackagingLibraryFilters(
            nominal_volume=self.volume_filter.currentData(),
            material=self.material_filter.currentData(),
            closure=self.closure_filter.currentData(),
            status=self.status_filter.currentData(),
        )

    def _clear_filters(self) -> None:
        for combo in (
            self.volume_filter,
            self.material_filter,
            self.closure_filter,
            self.status_filter,
        ):
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self.refresh()

    def refresh(self, *_args: object) -> None:
        preserved_selection = self.selected_asset_id or self._selected_asset_id
        self.display_state = BrowserDisplayState.LOADING
        self.state_message.setText("Loading Packaging Library…")
        self.state_view.setCurrentWidget(self.state_message)
        try:
            if self.service is None:
                raise PackagingLibraryBrowserError("Packaging Library service is not configured.")
            all_summaries = self.service.list_assets()
            self._sync_filter_options(all_summaries)
            filters = self._selected_filters()
            query = self.search_field.text()
            if query or filters != PackagingLibraryFilters():
                filter_assets = getattr(self.service, "filter_assets", None)
                if callable(filter_assets):
                    summaries = filter_assets(all_summaries, query=query, filters=filters)
                elif query and callable(getattr(self.service, "search_assets", None)):
                    summaries = self.service.search_assets(query)
                else:
                    summaries = all_summaries
            else:
                summaries = all_summaries
        except Exception as error:
            self._summaries = ()
            self._populate((), None)
            self.display_state = BrowserDisplayState.ERROR
            self.state_message.setText(f"Unable to load Packaging Library: {error}")
            self.state_view.setCurrentWidget(self.state_message)
            self.selection_summary.setText("No asset selected.")
            return

        self._summaries = summaries
        if not summaries:
            self._populate((), None)
            self.display_state = BrowserDisplayState.EMPTY
            self.state_message.setText("No packaging assets in this library.")
            self.state_view.setCurrentWidget(self.state_message)
            self.selection_summary.setText("No asset selected.")
            return

        available_ids = {item.asset_id for item in summaries}
        if preserved_selection not in available_ids:
            preserved_selection = None
        self._populate(summaries, preserved_selection)
        self.display_state = BrowserDisplayState.READY
        self.state_view.setCurrentWidget(self.item_view)

    def _populate(
        self,
        summaries: tuple[PackagingLibraryAssetSummary, ...],
        selected_asset_id: str | None,
    ) -> None:
        self.item_view.blockSignals(True)
        self.item_view.clear()
        self._selected_asset_id = selected_asset_id
        selected: QListWidgetItem | None = None
        for summary in summaries:
            image = self._thumbnail(summary)
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, summary.asset_id)
            item.setData(Qt.ItemDataRole.UserRole + 1, summary.revision_id)
            item.setIcon(image)
            item.setText(f"{summary.display_name}\nID: {summary.asset_id}\n{summary.core_metadata}")
            item.setToolTip(f"{summary.display_name}\n{summary.asset_id}\n{summary.revision_id}")
            item.setSizeHint(
                QSize(216, 180) if self.mode_selector.currentData() == "grid" else QSize(0, 112)
            )
            self.item_view.addItem(item)
            if summary.asset_id == selected_asset_id:
                selected = item
        if selected is not None:
            self.item_view.setCurrentItem(selected)
            self.selection_summary.setText(
                f"Selected {selected.text().splitlines()[0]} · {selected.data(Qt.ItemDataRole.UserRole)}"
            )
        else:
            self.item_view.setCurrentRow(-1)
            self.selection_summary.setText("No asset selected.")
        self.item_view.blockSignals(False)

    def _thumbnail(self, summary: PackagingLibraryAssetSummary):
        if self.service is not None:
            try:
                image_bytes = self.service.read_thumbnail_bytes(summary)
                if image_bytes is not None and summary.thumbnail_reference is not None:
                    buffer = QBuffer()
                    buffer.setData(QByteArray(image_bytes))
                    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
                    reader = QImageReader(buffer)
                    reader.setFormat(
                        b"png" if summary.thumbnail_reference.media_type == "image/png" else b"jpeg"
                    )
                    dimensions = reader.size()
                    if (
                        dimensions.isValid()
                        and dimensions.width() <= _MAX_THUMBNAIL_DIMENSION
                        and dimensions.height() <= _MAX_THUMBNAIL_DIMENSION
                        and dimensions.width() * dimensions.height() <= _MAX_THUMBNAIL_PIXELS
                    ):
                        reader.setScaledSize(QSize(128, 96))
                        image = reader.read()
                        if not image.isNull():
                            return QPixmap.fromImage(image)
                    buffer.close()
            except Exception:
                pass
        placeholder = QPixmap(128, 96)
        placeholder.fill(Qt.GlobalColor.lightGray)
        painter = QPainter(placeholder)
        painter.setPen(Qt.GlobalColor.darkGray)
        painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "No preview")
        painter.end()
        return placeholder

    def _set_mode(self, _index: int) -> None:
        self.item_view.setViewMode(
            QListWidget.ViewMode.IconMode
            if self.mode_selector.currentData() == "grid"
            else QListWidget.ViewMode.ListMode
        )
        self.item_view.setGridSize(
            QSize(220, 190) if self.mode_selector.currentData() == "grid" else QSize()
        )
        for index in range(self.item_view.count()):
            self.item_view.item(index).setSizeHint(
                QSize(216, 180) if self.mode_selector.currentData() == "grid" else QSize(0, 112)
            )

    def _selection_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            self._selected_asset_id = None
            self.selection_summary.setText("No asset selected.")
            return
        asset_id = str(current.data(Qt.ItemDataRole.UserRole))
        self._selected_asset_id = asset_id
        self.selection_summary.setText(f"Selected {current.text().splitlines()[0]} · {asset_id}")
        self.selection_changed.emit(asset_id)


def _safe_relative_path(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise PackagingLibraryBrowserError("library_thumbnail_path_invalid")
    path = PurePosixPath(value)
    if (
        not path.parts
        or str(path) != value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise PackagingLibraryBrowserError("library_thumbnail_path_invalid")
    return path


def _ensure_safe_local_file(root: Path, candidate: Path) -> os.stat_result:
    resolved_root = root.resolve(strict=True)
    for parent in (candidate, *candidate.parents):
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise PackagingLibraryBrowserError("library_thumbnail_symlink_forbidden")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise PackagingLibraryBrowserError("library_thumbnail_outside_root")
    metadata = candidate.stat()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_size <= 0
        or metadata.st_size > _MAX_THUMBNAIL_BYTES
    ):
        raise PackagingLibraryBrowserError("library_thumbnail_not_regular_file")
    return metadata


def _source_project_revisions(source_links: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(source_links, dict):
        return ()
    values: set[tuple[str, str]] = set()
    raw_scans = source_links.get("raw_scans", [])
    design_models = source_links.get("design_models", [])
    scan_master = source_links.get("scan_master")
    linked_values = [
        *(raw_scans if isinstance(raw_scans, list) else []),
        *(design_models if isinstance(design_models, list) else []),
    ]
    if isinstance(scan_master, dict):
        linked_values.append(scan_master)
    for item in linked_values:
        if isinstance(item, dict):
            project_id, revision_id = item.get("project_id"), item.get("revision_id")
            if isinstance(project_id, str) and isinstance(revision_id, str):
                values.add((project_id, revision_id))
    return tuple(sorted(values))


def _display_value(value: object) -> str:
    return value if isinstance(value, str) and value else "UNKNOWN"


def _supplier_value(value: object, key: str) -> str:
    if not isinstance(value, dict):
        return ""
    candidate = value.get(key)
    return candidate if isinstance(candidate, str) else ""


def _normalize_search_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()


def _field_provenance(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list):
        return ()
    pairs = {
        (item["field_name"], item["classification"])
        for item in value
        if isinstance(item, dict)
        and isinstance(item.get("field_name"), str)
        and isinstance(item.get("classification"), str)
    }
    return tuple(sorted(pairs))


def _matches_library_filters(
    asset: PackagingLibraryAssetSummary, filters: PackagingLibraryFilters
) -> bool:
    volume_filter = filters.nominal_volume
    if volume_filter == "UNKNOWN":
        if asset.nominal_volume_value is not None or asset.nominal_volume_unit is not None:
            return False
    elif isinstance(volume_filter, tuple) and (
        asset.nominal_volume_value != float(volume_filter[0])
        or asset.nominal_volume_unit != volume_filter[1]
    ):
        return False
    return (
        (filters.material is None or asset.base_material == filters.material)
        and (filters.closure is None or asset.closure == filters.closure)
        and (filters.status is None or asset.status == filters.status)
    )


def _volume_filter_label(value: object) -> str:
    if value == "UNKNOWN":
        return "Unknown volume"
    if (
        isinstance(value, tuple)
        and len(value) == 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], str)
    ):
        return f"{value[0]:g} {value[1]}"
    return "Invalid volume"


def _filter_combo(parent: QWidget, name: str, label: str) -> QComboBox:
    combo = QComboBox(parent)
    combo.setObjectName(f"packlab.library.filter.{name}")
    combo.addItem(label, None)
    return combo


def _identifier(value: object, kind: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise PackagingLibraryBrowserError(f"library_thumbnail_{kind}_id_invalid")


__all__ = [
    "BrowserDisplayState",
    "LibraryThumbnailReference",
    "PackagingLibraryAssetSummary",
    "PackagingLibraryFilters",
    "PackagingLibraryBrowserError",
    "PackagingLibraryBrowserService",
    "PackagingLibraryBrowserView",
    "ThumbnailSource",
]
