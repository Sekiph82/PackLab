from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from tests.core.test_packaging_asset import _asset

from packlab_core.packaging_components import PackagingComponentKind, ReusablePackagingComponent
from packlab_core.packaging_sku_library import PackagingSkuRevision, PackagingSkuStatus
from packlab_studio.packaging_library_store import (
    AttachmentRole,
    PackagingAttachmentRecord,
    PackagingLibraryStore,
    PackagingLibraryStoreError,
)


def _add(store: PackagingLibraryStore, source: Path, **overrides) -> PackagingAttachmentRecord:
    values = {
        "display_name": "supplier drawing.pdf",
        "media_type": "application/pdf",
        "role": AttachmentRole.DRAWING,
    }
    values.update(overrides)
    return store.add_attachment(source, **values)


def test_duplicate_content_is_deduplicated_and_record_is_path_free(tmp_path: Path) -> None:
    first_source = tmp_path / "supplier-a" / "drawing.pdf"
    second_source = tmp_path / "supplier-b" / "drawing.pdf"
    first_source.parent.mkdir()
    second_source.parent.mkdir()
    payload = b"opaque supplier drawing bytes\x00not parsed"
    first_source.write_bytes(payload)
    second_source.write_bytes(payload)
    first_store = PackagingLibraryStore(tmp_path / "library-a")
    second_store = PackagingLibraryStore(tmp_path / "library-b")

    first = _add(first_store, first_source)
    duplicate = _add(second_store, second_source)

    assert first == duplicate
    assert first.sha256 == hashlib.sha256(payload).hexdigest()
    assert first.byte_length == len(payload)
    assert first.relative_path == f"attachments/sha256/{first.sha256[:2]}/{first.sha256}"
    assert first_store.verify(first)
    assert second_store.verify(duplicate)
    assert first.canonical_json == duplicate.canonical_json
    assert str(first_source) not in first.canonical_json
    assert str(second_source) not in first.canonical_json
    assert str(first_store.library_root) not in first.canonical_json
    assert str(second_store.library_root) not in first.canonical_json
    assert json.loads(first.canonical_json)["source_path_included"] is False


def test_same_content_deduplicates_blob_across_distinct_metadata(tmp_path: Path) -> None:
    source = tmp_path / "input.pdf"
    source.write_bytes(b"shared bytes")
    store = PackagingLibraryStore(tmp_path / "library")

    drawing = _add(store, source)
    quotation = _add(
        store,
        source,
        display_name="supplier quote.pdf",
        role=AttachmentRole.QUOTATION,
    )

    assert drawing.attachment_id != quotation.attachment_id
    assert drawing.sha256 == quotation.sha256
    assert drawing.relative_path == quotation.relative_path
    assert store.read_record(drawing.attachment_id) == drawing
    assert store.read_record(quotation.attachment_id) == quotation
    assert store.verify(drawing)
    assert (
        len(tuple((tmp_path / "library" / "attachments" / "sha256" / drawing.sha256[:2]).glob("*")))
        == 1
    )


def test_tampered_blob_digest_and_stale_related_ids_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "input.pdf"
    source.write_bytes(b"original opaque content")
    store = PackagingLibraryStore(tmp_path / "library")
    asset = _asset()
    component = ReusablePackagingComponent(
        component_id="cap-28mm",
        kind=PackagingComponentKind.CAP,
        display_name="28 mm cap",
    )
    sku = PackagingSkuRevision.create(
        asset,
        sku_id="water-500",
        display_name="500 mL Water",
        status=PackagingSkuStatus.ACTIVE,
    )
    sku_revision = PackagingSkuRevision.create(
        asset,
        sku_id="water-500",
        display_name="500 mL Water Revised",
        status=PackagingSkuStatus.ACTIVE,
    )
    asset_revision = _asset(display_name="500 mL Water Bottle Revised")

    record = _add(
        store,
        source,
        related_asset_id=asset.asset_id,
        related_component_id=component.component_id,
        related_sku_id=sku.sku_id,
        assets=(asset, asset_revision),
        components=(component,),
        skus=(sku, sku_revision),
    )
    blob = store.library_root.joinpath(*record.relative_path.split("/"))
    blob.write_bytes(b"tampered")
    assert not store.verify(record)
    with pytest.raises(PackagingLibraryStoreError, match="existing_blob_mismatch"):
        _add(
            store,
            source,
            related_asset_id=asset.asset_id,
            assets=(asset,),
        )
    with pytest.raises(PackagingLibraryStoreError, match="asset_target_stale_or_ambiguous"):
        _add(store, source, related_asset_id="missing-asset")
    with pytest.raises(PackagingLibraryStoreError, match="component_target_stale_or_ambiguous"):
        _add(store, source, related_component_id=component.component_id)
    with pytest.raises(PackagingLibraryStoreError, match="sku_target_stale_or_ambiguous"):
        _add(store, source, related_sku_id=sku.sku_id)


def test_empty_oversized_traversal_and_executable_inputs_reject_without_publication(
    tmp_path: Path,
) -> None:
    store = PackagingLibraryStore(tmp_path / "library")
    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    with pytest.raises(PackagingLibraryStoreError, match="size_out_of_bounds"):
        _add(store, empty)

    oversized = tmp_path / "oversized.pdf"
    with oversized.open("wb") as handle:
        handle.truncate(32 * 1024 * 1024 + 1)
    with pytest.raises(PackagingLibraryStoreError, match="size_out_of_bounds"):
        _add(store, oversized)

    with pytest.raises(PackagingLibraryStoreError, match="source_traversal_forbidden"):
        _add(store, tmp_path / ".." / "outside.pdf")
    with pytest.raises(PackagingLibraryStoreError, match="display_name_invalid"):
        _add(store, empty, display_name="run.ps1")
    with pytest.raises(PackagingLibraryStoreError, match="media_type_invalid"):
        _add(store, empty, media_type="application/javascript")

    assert not tuple((tmp_path / "library" / "attachments").rglob("*.part"))
    assert not tuple((tmp_path / "library" / "records").glob("*.json"))


def test_symlink_sources_are_rejected(tmp_path: Path, monkeypatch) -> None:
    alias = tmp_path / "alias.pdf"
    alias.write_bytes(b"private bytes")
    store = PackagingLibraryStore(tmp_path / "library")
    original_is_symlink = Path.is_symlink

    def simulated_symlink(path: Path) -> bool:
        return path == alias.absolute() or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", simulated_symlink)
    with pytest.raises(PackagingLibraryStoreError, match="source_symlink_forbidden"):
        _add(store, alias)


def test_unsafe_record_paths_and_library_root_symlinks_reject(tmp_path: Path, monkeypatch) -> None:
    digest = "0" * 64
    with pytest.raises(PackagingLibraryStoreError, match="relative_path_invalid"):
        PackagingAttachmentRecord(
            attachment_id="packaging-attachment:" + "1" * 64,
            sha256=digest,
            byte_length=1,
            display_name="drawing.pdf",
            media_type="application/pdf",
            role=AttachmentRole.DRAWING,
            relative_path="../../private.pdf",
        )

    target = tmp_path / "real-library"
    target.mkdir()
    alias = tmp_path / "library-link"
    alias.mkdir()
    original_is_symlink = Path.is_symlink

    def simulated_symlink(path: Path) -> bool:
        return path == alias.absolute() or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", simulated_symlink)
    with pytest.raises(PackagingLibraryStoreError, match="root_symlink_forbidden"):
        PackagingLibraryStore(alias)


def test_symlink_inside_storage_tree_is_rejected(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "input.pdf"
    source.write_bytes(b"opaque bytes")
    store = PackagingLibraryStore(tmp_path / "library")
    sha_directory = store.library_root / "attachments" / "sha256"
    sha_directory.mkdir()
    original_is_symlink = Path.is_symlink

    def simulated_symlink(path: Path) -> bool:
        return path == sha_directory or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", simulated_symlink)
    with pytest.raises(PackagingLibraryStoreError, match="directory_unsafe"):
        _add(store, source)
