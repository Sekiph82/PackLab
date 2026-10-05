"""Project-independent Packaging Library browser service and PySide6 view."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import tempfile
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
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from packlab_core.packaging_asset import DesignModelLink, ScaleState
from packlab_core.packaging_sku_library import (
    PackagingSkuRevision,
    PackagingSkuStatus,
    SkuArtworkPresentationReference,
)

from .packaging_library_audit import PackagingAssetRelationship
from .viewport import QtRasterViewportAdapter, SceneObjectKind, ViewportService

_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_THUMBNAIL_BYTES = 8 * 1024 * 1024
_MAX_THUMBNAIL_DIMENSION = 4096
_MAX_THUMBNAIL_PIXELS = 4_194_304
_MAX_SEARCH_QUERY_LENGTH = 128
_MAX_PREVIEW_BYTES = 64 * 1024 * 1024


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


class PreviewState(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
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
class LinkedProjectRevision:
    role: str
    project_id: str
    revision_id: str
    sha256: str
    authority_class: str


@dataclass(frozen=True, slots=True)
class LibraryRelatedRecord:
    record_type: str
    record_id: str
    display_name: str
    revision_id: str | None = None

    def __post_init__(self) -> None:
        if self.record_type not in {"COMPONENT", "ARTWORK", "SKU"}:
            raise PackagingLibraryBrowserError("library_related_record_type_invalid")
        if not _ID.fullmatch(self.record_id) or (
            self.revision_id is not None and not _ID.fullmatch(self.revision_id)
        ):
            raise PackagingLibraryBrowserError("library_related_record_id_invalid")
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise PackagingLibraryBrowserError("library_related_record_name_invalid")


@dataclass(frozen=True, slots=True)
class PackagingLibraryAssetDetail:
    summary: PackagingLibraryAssetSummary
    dimensions: tuple[tuple[str, str], ...]
    raw_scans: tuple[LinkedProjectRevision, ...]
    scan_master: LinkedProjectRevision | None
    design_models: tuple[LinkedProjectRevision, ...]
    preview_candidates: tuple[LinkedProjectRevision, ...]
    preferred_design_model_revision_id: str | None
    asset_relationships: tuple[PackagingAssetRelationship, ...]
    related_records: tuple[LibraryRelatedRecord, ...]


@dataclass(frozen=True, slots=True)
class PreviewResult:
    state: PreviewState
    image: Any | None = None
    revision_label: str = ""
    message: str = ""


@dataclass(frozen=True, slots=True)
class ProjectPreviewResolution:
    """Transient local root/path result from an injected project authority resolver."""

    project_root: Path
    relative_path: str
    sha256: str


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
    relationship_badges: tuple[str, ...] = ()
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
        preview_resolver: Callable[[LinkedProjectRevision], ProjectPreviewResolution | None]
        | None = None,
        related_records_resolver: Callable[[str], tuple[LibraryRelatedRecord, ...]] | None = None,
        sku_artwork_references_provider: Callable[
            [str, str], tuple[SkuArtworkPresentationReference, ...]
        ]
        | None = None,
        preview_adapter: QtRasterViewportAdapter | None = None,
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
        self.preview_resolver = preview_resolver
        self.related_records_resolver = related_records_resolver
        self.sku_artwork_references_provider = sku_artwork_references_provider
        self.preview_adapter = preview_adapter or QtRasterViewportAdapter()

    def available_sku_artwork_references(
        self, asset_id: str, asset_revision_id: str
    ) -> tuple[SkuArtworkPresentationReference, ...]:
        if self.sku_artwork_references_provider is None:
            return ()
        references = self.sku_artwork_references_provider(asset_id, asset_revision_id)
        if not isinstance(references, tuple) or any(
            not isinstance(item, SkuArtworkPresentationReference) for item in references
        ):
            raise PackagingLibraryBrowserError("library_sku_artwork_references_invalid")
        return references

    def create_sku_from_asset(
        self,
        summary: PackagingLibraryAssetSummary,
        *,
        sku_id: str,
        display_name: str,
        status: PackagingSkuStatus,
        artwork_references: tuple[SkuArtworkPresentationReference, ...],
        expected_state_revision: str,
        actor_id: str,
        reason: str,
    ):
        if not isinstance(summary, PackagingLibraryAssetSummary):
            raise PackagingLibraryBrowserError("library_asset_summary_required")
        snapshot = self.audit_store.snapshot()
        entry = next((item for item in snapshot.assets if item.asset_id == summary.asset_id), None)
        if entry is None or entry.revision_id != summary.revision_id:
            raise PackagingLibraryBrowserError("library_asset_detail_revision_stale")
        document = json.loads(entry.canonical_json)
        source_links = document.get("source_links", {})
        preferred_revision = source_links.get("preferred_design_model_revision_id")
        linked_models = source_links.get("design_models", [])
        preferred_document = next(
            (
                item
                for item in linked_models
                if isinstance(item, dict) and item.get("revision_id") == preferred_revision
            ),
            None,
        )
        preferred_link = (
            _design_model_link_from_dict(preferred_document)
            if preferred_document is not None
            else None
        )
        sku = PackagingSkuRevision(
            sku_id=sku_id,
            display_name=display_name,
            status=status,
            packaging_asset_id=entry.asset_id,
            packaging_asset_revision_id=entry.revision_id,
            preferred_design_model_link=preferred_link,
            artwork_references=artwork_references,
        )
        current_artwork = self.available_sku_artwork_references(entry.asset_id, entry.revision_id)
        if not set(sku.artwork_references).issubset(current_artwork):
            raise PackagingLibraryBrowserError("library_sku_artwork_reference_stale")
        design_model_revision_ids = {
            item.get("revision_id")
            for item in linked_models
            if isinstance(item, dict) and isinstance(item.get("revision_id"), str)
        }
        if any(
            item.label_zone_design_model_revision_id not in design_model_revision_ids
            for item in sku.artwork_references
        ):
            raise PackagingLibraryBrowserError("library_sku_artwork_design_model_mismatch")
        return self.audit_store.create_sku(
            sku,
            expected_state_revision=expected_state_revision,
            expected_asset_revision_id=entry.revision_id,
            current_artwork_references=current_artwork,
            actor_id=actor_id,
            reason=reason,
        )

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
                relationship_badges = tuple(
                    sorted(
                        {
                            relation.relationship_type
                            for relation in snapshot.relationships
                            if entry.asset_id in {relation.asset_a_id, relation.asset_b_id}
                        }
                    )
                )
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
                        relationship_badges=relationship_badges,
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

    def asset_detail(self, summary: PackagingLibraryAssetSummary) -> PackagingLibraryAssetDetail:
        """Resolve one unchanged canonical metadata revision and its path-free relationships."""
        if not isinstance(summary, PackagingLibraryAssetSummary):
            raise PackagingLibraryBrowserError("library_asset_summary_required")
        snapshot = self.audit_store.snapshot()
        entry = next((item for item in snapshot.assets if item.asset_id == summary.asset_id), None)
        if entry is None or entry.revision_id != summary.revision_id:
            raise PackagingLibraryBrowserError("library_asset_detail_revision_stale")
        try:
            document = json.loads(entry.canonical_json)
            dimensions_doc = document.get("dimensions", {})
            closure_doc = document.get("neck_closure", {})
            source_links = document.get("source_links", {})
            dimensions = (
                ("Overall height", _measurement_label(dimensions_doc.get("overall_height"))),
                ("Body diameter", _measurement_label(dimensions_doc.get("body_diameter"))),
                (
                    "Neck finish diameter",
                    _measurement_label(closure_doc.get("neck_finish_diameter")),
                ),
                ("Neck finish", _display_value(closure_doc.get("neck_finish"))),
                ("Closure description", _display_value(closure_doc.get("closure_description"))),
                (
                    "Empty package weight",
                    _measurement_label(document.get("empty_package_weight")),
                ),
            )
            raw_scans = _linked_revision_list(source_links.get("raw_scans"), "RAW_SCAN")
            scan_master_value = source_links.get("scan_master")
            scan_master = (
                _linked_revision(scan_master_value, "SCAN_MASTER", "geometry_sha256")
                if isinstance(scan_master_value, dict)
                else None
            )
            design_models = _linked_revision_list(
                source_links.get("design_models"), "DESIGN_MODEL", digest_key="content_sha256"
            )
            preferred = source_links.get("preferred_design_model_revision_id")
            if not isinstance(preferred, str):
                preferred = None
            ordered_models = sorted(
                design_models,
                key=lambda item: (item.revision_id != preferred, item.revision_id),
            )
            preview_candidates = tuple(
                [*ordered_models, *([scan_master] if scan_master is not None else []), *raw_scans]
            )
            related = (
                self.related_records_resolver(summary.asset_id)
                if self.related_records_resolver is not None
                else ()
            )
            if not isinstance(related, tuple) or any(
                not isinstance(item, LibraryRelatedRecord) for item in related
            ):
                raise PackagingLibraryBrowserError("library_related_records_invalid")
            persisted_skus = tuple(
                LibraryRelatedRecord("SKU", item.sku_id, item.display_name, item.revision_id)
                for item in getattr(snapshot, "skus", ())
                if item.packaging_asset_id == summary.asset_id
            )
            persisted_sku_ids = {item.record_id for item in persisted_skus}
            related = (
                tuple(
                    item
                    for item in related
                    if item.record_type != "SKU" or item.record_id not in persisted_sku_ids
                )
                + persisted_skus
            )
            return PackagingLibraryAssetDetail(
                summary=summary,
                dimensions=dimensions,
                raw_scans=raw_scans,
                scan_master=scan_master,
                design_models=design_models,
                preview_candidates=preview_candidates,
                preferred_design_model_revision_id=preferred,
                asset_relationships=tuple(
                    sorted(
                        (
                            item
                            for item in snapshot.relationships
                            if summary.asset_id in {item.asset_a_id, item.asset_b_id}
                        ),
                        key=lambda item: (
                            item.relationship_type,
                            item.asset_a_id,
                            item.asset_b_id,
                        ),
                    )
                ),
                related_records=tuple(
                    sorted(
                        related,
                        key=lambda item: (item.record_type, item.display_name, item.record_id),
                    )
                ),
            )
        except (ValueError, KeyError, TypeError) as error:
            if isinstance(error, PackagingLibraryBrowserError):
                raise
            raise PackagingLibraryBrowserError("library_asset_detail_document_invalid") from error

    def render_preview(self, detail: PackagingLibraryAssetDetail) -> PreviewResult:
        """Load one exact linked project revision through the existing raster viewport path."""
        if not isinstance(detail, PackagingLibraryAssetDetail):
            raise PackagingLibraryBrowserError("library_asset_detail_required")
        if not detail.preview_candidates or self.preview_resolver is None:
            return PreviewResult(
                PreviewState.UNAVAILABLE,
                message="No locally resolved linked project geometry is available.",
            )
        reference = detail.preview_candidates[0]
        label = f"{reference.project_id} · {reference.revision_id}"
        try:
            resolution = self.preview_resolver(reference)
        except Exception as error:
            return PreviewResult(
                PreviewState.ERROR,
                revision_label=label,
                message=f"The linked project resolver failed: {error}",
            )
        if resolution is None:
            return PreviewResult(
                PreviewState.UNAVAILABLE,
                revision_label=label,
                message="The linked project revision is unavailable locally.",
            )
        if not isinstance(resolution, ProjectPreviewResolution):
            return PreviewResult(
                PreviewState.ERROR,
                revision_label=label,
                message="The project preview resolver returned an invalid result.",
            )
        try:
            if resolution.sha256 != reference.sha256 or not _SHA256.fullmatch(resolution.sha256):
                return PreviewResult(
                    PreviewState.STALE,
                    revision_label=label,
                    message="Resolved geometry digest does not match the linked revision.",
                )
            suffix = PurePosixPath(resolution.relative_path).suffix.lower()
            if suffix not in {".obj", ".ply", ".xyz", ".pts", ".pcd"}:
                return PreviewResult(
                    PreviewState.ERROR,
                    revision_label=label,
                    message="The linked geometry format cannot be previewed.",
                )
            payload = _read_verified_project_artifact(resolution)
            if payload is None:
                return PreviewResult(
                    PreviewState.STALE,
                    revision_label=label,
                    message="The linked project artifact is missing, unsafe, oversized, or stale.",
                )
            with tempfile.TemporaryDirectory(prefix="packlab-library-preview-") as directory:
                preview_path = Path(directory) / ("verified-preview" + suffix)
                preview_path.write_bytes(payload)
                viewport = ViewportService(self.preview_adapter)
                geometry = self.preview_adapter.load(preview_path)
                viewport.add_geometry(
                    "packaging-library-preview", SceneObjectKind.REFERENCE_GEOMETRY, geometry
                )
                viewport.fit_to_view()
                image = viewport.render(QSize(480, 320))
            if image.isNull():
                raise PackagingLibraryBrowserError("library_preview_render_empty")
            return PreviewResult(PreviewState.AVAILABLE, image, label, "Verified linked revision.")
        except Exception as error:
            return PreviewResult(
                PreviewState.ERROR,
                revision_label=label,
                message=f"Linked geometry could not be previewed: {error}",
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


class CreatePackagingSkuDialog(QDialog):
    """Create an immutable SKU while retaining the selected asset's exact identity."""

    def __init__(
        self,
        service: PackagingLibraryBrowserService,
        summary: PackagingLibraryAssetSummary,
        *,
        expected_state_revision: str,
        preview: PreviewResult,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("packlab.library.create-sku-dialog")
        self.setWindowTitle("Create SKU from Existing Geometry")
        self.service = service
        self.summary = summary
        self.expected_state_revision = expected_state_revision
        self.created_sku: PackagingSkuRevision | None = None

        layout = QVBoxLayout(self)
        self.source_preview = QLabel(self)
        self.source_preview.setObjectName("packlab.library.create-sku.preview")
        self.source_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.source_preview.setMinimumSize(QSize(320, 180))
        if preview.state is PreviewState.AVAILABLE and preview.image is not None:
            self.source_preview.setPixmap(
                QPixmap.fromImage(preview.image).scaled(
                    QSize(400, 260),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.source_preview.setText(
                f"Geometry preview {preview.state.value.lower()}: {preview.message}"
            )
        layout.addWidget(self.source_preview)
        self.source_identity = QLabel(
            f"Reusing {summary.display_name}\n"
            f"Asset: {summary.asset_id}\nAsset revision: {summary.revision_id}\n"
            f"Supplier: {summary.supplier_name or 'Unknown'} "
            f"({summary.supplier_id or 'Unknown'})\n"
            "Source field provenance stays with the Packaging Asset:\n"
            + "\n".join(f"{field}: {kind}" for field, kind in summary.field_provenance)
            + "\nGeometry remains linked and unchanged.",
            self,
        )
        self.source_identity.setObjectName("packlab.library.create-sku.source")
        layout.addWidget(self.source_identity)

        form = QFormLayout()
        self.sku_id_field = QLineEdit(self)
        self.sku_id_field.setObjectName("packlab.library.create-sku.id")
        self.sku_id_field.setMaxLength(128)
        self.display_name_field = QLineEdit(self)
        self.display_name_field.setObjectName("packlab.library.create-sku.name")
        self.display_name_field.setMaxLength(120)
        self.status_selector = QComboBox(self)
        self.status_selector.setObjectName("packlab.library.create-sku.status")
        for status in PackagingSkuStatus:
            self.status_selector.addItem(status.value, status)
        self.artwork_view = QListWidget(self)
        self.artwork_view.setObjectName("packlab.library.create-sku.artwork")
        self.artwork_view.setMaximumHeight(120)
        self.error_label = QLabel("", self)
        self.error_label.setObjectName("packlab.library.create-sku.error")
        form.addRow("SKU ID", self.sku_id_field)
        form.addRow("Name", self.display_name_field)
        form.addRow("Status", self.status_selector)
        form.addRow("Accepted artwork assignments", self.artwork_view)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        try:
            artwork = service.available_sku_artwork_references(
                summary.asset_id, summary.revision_id
            )
        except Exception as error:
            artwork = ()
            self.error_label.setText(f"Artwork choices unavailable: {error}")
        for reference in artwork:
            item = QListWidgetItem(
                f"{reference.label_zone_id} · {reference.variant_id} · "
                f"assignment {reference.assignment_revision_id}"
            )
            item.setData(Qt.ItemDataRole.UserRole, reference)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.artwork_view.addItem(item)
        if not artwork:
            self.artwork_view.addItem("No accepted artwork assignment references available.")
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName(
            "packlab.library.create-sku.save"
        )
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setObjectName(
            "packlab.library.create-sku.cancel"
        )
        buttons.accepted.connect(self._create)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create(self) -> None:
        selected = tuple(
            self.artwork_view.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.artwork_view.count())
            if self.artwork_view.item(index).checkState() is Qt.CheckState.Checked
        )
        selected = tuple(
            item for item in selected if isinstance(item, SkuArtworkPresentationReference)
        )
        try:
            raw_status = self.status_selector.currentData()
            status = (
                raw_status
                if isinstance(raw_status, PackagingSkuStatus)
                else PackagingSkuStatus(raw_status)
            )
            snapshot = self.service.create_sku_from_asset(
                self.summary,
                sku_id=self.sku_id_field.text().strip(),
                display_name=self.display_name_field.text(),
                status=status,
                artwork_references=selected,
                expected_state_revision=self.expected_state_revision,
                actor_id="studio-user",
                reason="Create Packaging SKU from existing library geometry",
            )
            self.created_sku = next(
                item for item in snapshot.skus if item.sku_id == self.sku_id_field.text().strip()
            )
        except Exception as error:
            self.error_label.setText(f"Unable to create SKU: {error}")
            return
        self.accept()


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
        self.create_sku_button = QPushButton("Create SKU from selected geometry", self)
        self.create_sku_button.setObjectName("packlab.library.create-sku")
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
        self.state_view.addWidget(self.state_message)

        self.preview_label = QLabel("No 3D preview selected.", self)
        self.preview_label.setObjectName("packlab.library.detail.preview")
        self.preview_label.setMinimumSize(QSize(320, 220))
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_text = QTextBrowser(self)
        self.detail_text.setObjectName("packlab.library.detail.metadata")
        self.detail_text.setOpenExternalLinks(False)
        self.detail_text.setReadOnly(True)
        self.related_asset_view = QListWidget(self)
        self.related_asset_view.setObjectName("packlab.library.detail.related-assets")
        self.related_asset_view.setMaximumHeight(110)
        detail_panel = QWidget(self)
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.addWidget(self.preview_label)
        detail_layout.addWidget(QLabel("Related Packaging Assets", detail_panel))
        detail_layout.addWidget(self.related_asset_view)
        detail_layout.addWidget(self.detail_text, 1)
        self.results_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.results_splitter.addWidget(self.item_view)
        self.results_splitter.addWidget(detail_panel)
        self.results_splitter.setStretchFactor(0, 2)
        self.results_splitter.setStretchFactor(1, 1)
        self.state_view.insertWidget(0, self.results_splitter)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.mode_selector)
        toolbar.addWidget(self.search_field, 1)
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.create_sku_button)
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
        self.create_sku_button.clicked.connect(self._create_sku)
        self.item_view.currentItemChanged.connect(self._selection_changed)
        self.related_asset_view.itemClicked.connect(self._navigate_related_asset)
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
        self.state_view.setCurrentWidget(self.results_splitter)

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
            badges = (
                f" · {' / '.join(summary.relationship_badges)}"
                if summary.relationship_badges
                else ""
            )
            item.setText(
                f"{summary.display_name}\nID: {summary.asset_id}\n{summary.core_metadata}{badges}"
            )
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
        self._show_details(self.selected_asset_id)

    def _show_details(self, asset_id: str | None) -> None:
        if asset_id is None:
            self.related_asset_view.clear()
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("No 3D preview selected.")
            self.detail_text.setPlainText(
                "Select a packaging asset to inspect its metadata and links."
            )
            return
        summary = next((item for item in self._summaries if item.asset_id == asset_id), None)
        if summary is None or self.service is None:
            self.related_asset_view.clear()
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Preview unavailable.")
            self.detail_text.setPlainText("The selected asset is no longer available.")
            return
        try:
            detail = self.service.asset_detail(summary)
            preview = self.service.render_preview(detail)
        except Exception as error:
            self.related_asset_view.clear()
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Preview unavailable.")
            self.detail_text.setPlainText(f"Asset details are unavailable: {error}")
            return
        if preview.state is PreviewState.AVAILABLE and preview.image is not None:
            self.preview_label.setPixmap(
                QPixmap.fromImage(preview.image).scaled(
                    QSize(480, 320),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.preview_label.setText("")
        else:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(
                f"3D preview {preview.state.value.lower()}: {preview.message}"
            )
        self.related_asset_view.clear()
        for relationship in detail.asset_relationships:
            if relationship.relationship_type == "DUPLICATE":
                other_asset_id = (
                    relationship.asset_b_id
                    if relationship.asset_a_id == asset_id
                    else relationship.asset_a_id
                )
                relationship_label = f"DUPLICATE · {other_asset_id}"
            elif relationship.asset_a_id == asset_id:
                other_asset_id = relationship.asset_b_id
                relationship_label = f"VARIANT BASE → {other_asset_id}"
            else:
                other_asset_id = relationship.asset_a_id
                relationship_label = f"VARIANT OF {other_asset_id}"
            link_item = QListWidgetItem(relationship_label)
            link_item.setData(Qt.ItemDataRole.UserRole, other_asset_id)
            self.related_asset_view.addItem(link_item)
        if not detail.asset_relationships:
            self.related_asset_view.addItem("No duplicate or variant relationships.")
        lines = [
            f"Asset ID: {summary.asset_id}",
            f"Asset revision: {summary.revision_id}",
            f"Name: {summary.display_name}",
            f"Family: {summary.family}",
            f"Material: {summary.base_material}",
            f"Other material label: {summary.material_other_label}",
            f"Closure type: {summary.closure}",
            f"Nominal volume: {summary.nominal_volume}",
            f"Status: {summary.status}",
            f"Supplier: {summary.supplier_name or 'Unknown'} ({summary.supplier_id or 'Unknown'})",
            "",
            "Dimensions and finish:",
            *(f"  {label}: {value}" for label, value in detail.dimensions),
            "",
            "Field provenance:",
            *(f"  {field}: {classification}" for field, classification in summary.field_provenance),
            "",
            "Raw scan revisions:",
            *(_linked_revision_label(item) for item in detail.raw_scans),
            "Scan Master revision:",
            *([_linked_revision_label(detail.scan_master)] if detail.scan_master else ["  None"]),
            "Design Model revisions:",
            *(_linked_revision_label(item) for item in detail.design_models),
            f"Preferred Design Model revision: {detail.preferred_design_model_revision_id or 'None'}",
            "",
            "Reusable components:",
            *_related_record_labels(detail.related_records, "COMPONENT"),
            "Linked artworks:",
            *_related_record_labels(detail.related_records, "ARTWORK"),
            "Linked SKUs:",
            *_related_record_labels(detail.related_records, "SKU"),
            "",
            "Duplicate and variant relationship revisions:",
            *(
                f"  {item.relationship_type} · {item.relationship_id} · {item.revision_id}\n"
                f"    provenance={item.provenance_class}; actor={item.actor_id}; reason={item.reason}"
                for item in detail.asset_relationships
            ),
            "",
            f"Preview source: {preview.revision_label or 'No linked revision'}",
            f"Preview state: {preview.state.value}",
        ]
        self.detail_text.setPlainText("\n".join(lines))

    def _navigate_related_asset(self, item: QListWidgetItem) -> None:
        target_asset_id = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(target_asset_id, str):
            return
        visible = next(
            (
                row
                for row in range(self.item_view.count())
                if self.item_view.item(row).data(Qt.ItemDataRole.UserRole) == target_asset_id
            ),
            None,
        )
        if visible is None:
            self.search_field.blockSignals(True)
            self.search_field.clear()
            self.search_field.blockSignals(False)
            self._clear_filters()
            visible = next(
                (
                    row
                    for row in range(self.item_view.count())
                    if self.item_view.item(row).data(Qt.ItemDataRole.UserRole) == target_asset_id
                ),
                None,
            )
        if visible is not None:
            self.item_view.setCurrentRow(visible)

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
        self._show_details(asset_id)

    def _create_sku(self) -> None:
        summary = next(
            (item for item in self._summaries if item.asset_id == self.selected_asset_id), None
        )
        if summary is None or self.service is None:
            self.selection_summary.setText("Select a packaging asset before creating a SKU.")
            return
        try:
            detail = self.service.asset_detail(summary)
            preview = self.service.render_preview(detail)
            snapshot = self.service.audit_store.snapshot()
            dialog = CreatePackagingSkuDialog(
                self.service,
                summary,
                expected_state_revision=snapshot.state_revision,
                preview=preview,
                parent=self,
            )
        except Exception as error:
            self.selection_summary.setText(f"Unable to open SKU workflow: {error}")
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()


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


def _design_model_link_from_dict(value: dict[str, object]) -> DesignModelLink:
    return DesignModelLink(
        project_id=value["project_id"],
        revision_id=value["revision_id"],
        content_sha256=value["content_sha256"],
        parent_authority_kind=value["parent_authority_kind"],
        parent_authority_revision_id=value["parent_authority_revision_id"],
        scale_state=ScaleState(value["scale_state"]),
        scan_master_revision_id=value["scan_master_revision_id"],
        scan_master_geometry_sha256=value["scan_master_geometry_sha256"],
        physical_accuracy_validation_status=value["physical_accuracy_validation_status"],
        mold_use_authorized=value["mold_use_authorized"],
        authority_class=value["authority_class"],
    )


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


def _linked_revision_list(
    value: object,
    role: str,
    *,
    digest_key: str = "artifact_sha256",
) -> tuple[LinkedProjectRevision, ...]:
    if not isinstance(value, list):
        return ()
    references = tuple(
        _linked_revision(item, role, digest_key) for item in value if isinstance(item, dict)
    )
    return tuple(sorted(references, key=lambda item: (item.project_id, item.revision_id)))


def _linked_revision(value: dict[str, Any], role: str, digest_key: str) -> LinkedProjectRevision:
    project_id = value.get("project_id")
    revision_id = value.get("revision_id")
    digest = value.get(digest_key)
    authority = value.get("authority_class", role)
    if (
        not isinstance(project_id, str)
        or not isinstance(revision_id, str)
        or not isinstance(digest, str)
        or not _SHA256.fullmatch(digest)
        or not isinstance(authority, str)
    ):
        raise PackagingLibraryBrowserError("library_project_revision_link_invalid")
    return LinkedProjectRevision(role, project_id, revision_id, digest, authority)


def _measurement_label(value: object) -> str:
    if (
        isinstance(value, dict)
        and isinstance(value.get("value"), (int, float))
        and not isinstance(value.get("value"), bool)
        and isinstance(value.get("unit"), str)
    ):
        return f"{value['value']:g} {value['unit']}"
    return "Unknown"


def _linked_revision_label(reference: LinkedProjectRevision) -> str:
    return (
        f"  {reference.project_id} / {reference.revision_id} · "
        f"{reference.authority_class} · SHA-256 {reference.sha256}"
    )


def _related_record_labels(
    records: tuple[LibraryRelatedRecord, ...], record_type: str
) -> list[str]:
    matches = [
        f"  {item.display_name} · {item.record_id}"
        + (f" · {item.revision_id}" if item.revision_id else "")
        for item in records
        if item.record_type == record_type
    ]
    return matches or ["  No linked records"]


def _read_verified_project_artifact(resolution: ProjectPreviewResolution) -> bytes | None:
    try:
        root = Path(resolution.project_root).expanduser().absolute()
        if root.is_symlink() or not root.is_dir():
            return None
        relative = _safe_relative_path(resolution.relative_path)
        candidate = root.joinpath(*relative.parts)
        metadata = _ensure_safe_local_file(root, candidate)
        if metadata.st_size < 1 or metadata.st_size > _MAX_PREVIEW_BYTES:
            return None
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(candidate, os.O_RDONLY | no_follow)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
                metadata.st_dev,
                metadata.st_ino,
            ):
                return None
            chunks: list[bytes] = []
            size = 0
            digest = hashlib.sha256()
            while chunk := os.read(descriptor, min(1024 * 1024, _MAX_PREVIEW_BYTES + 1 - size)):
                size += len(chunk)
                if size > _MAX_PREVIEW_BYTES:
                    return None
                digest.update(chunk)
                chunks.append(chunk)
            if size != metadata.st_size or digest.hexdigest() != resolution.sha256:
                return None
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    except (OSError, ValueError, PackagingLibraryBrowserError):
        return None


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
    "LibraryRelatedRecord",
    "LinkedProjectRevision",
    "PackagingLibraryAssetSummary",
    "PackagingLibraryAssetDetail",
    "PackagingLibraryFilters",
    "PackagingLibraryBrowserError",
    "PackagingLibraryBrowserService",
    "PackagingLibraryBrowserView",
    "PreviewResult",
    "PreviewState",
    "ProjectPreviewResolution",
    "ThumbnailSource",
]
