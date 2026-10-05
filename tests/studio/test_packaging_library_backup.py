from __future__ import annotations

import hashlib
import json
import stat
import warnings
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from tests.core.test_packaging_asset import _asset

from packlab_studio.packaging_library_audit import PackagingLibraryAuditStore
from packlab_studio.packaging_library_backup import (
    PackagingLibraryBackupError,
    PackagingLibraryBackupService,
)
from packlab_studio.packaging_library_store import (
    AttachmentRole,
    PackagingLibraryStore,
)

_NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


def _populate_library(root: Path, tmp_path: Path) -> tuple[PackagingLibraryAuditStore, str]:
    audit = PackagingLibraryAuditStore(root, clock=lambda: _NOW)
    asset = _asset(asset_id="backup-water", display_name="Backup water package")
    before = audit.snapshot()
    audit.create_asset(
        asset,
        expected_state_revision=before.state_revision,
        actor_id="operator-1",
        reason="Add package metadata before backup",
    )
    drawing = tmp_path / "supplier-drawing.pdf"
    drawing.write_bytes(b"opaque supplier drawing payload")
    store = PackagingLibraryStore(root)
    record = store.add_attachment(
        drawing,
        display_name="supplier drawing.pdf",
        media_type="application/pdf",
        role=AttachmentRole.DRAWING,
        related_asset_id=asset.asset_id,
        assets=(asset,),
    )
    thumbnail = b"local library thumbnail bytes"
    digest = hashlib.sha256(thumbnail).hexdigest()
    thumbnail_path = root / "thumbnails" / "sha256" / digest[:2] / f"{digest}.png"
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    thumbnail_path.write_bytes(thumbnail)
    return audit, record.attachment_id


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _zip_items(path: Path) -> list[tuple[str, bytes, int | None]]:
    with zipfile.ZipFile(path) as archive:
        return [
            (item.filename, archive.read(item), item.external_attr) for item in archive.infolist()
        ]


def _write_zip(path: Path, items: list[tuple[str, bytes, int | None]]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data, external_attr in items:
            item = zipfile.ZipInfo(name)
            item.compress_type = zipfile.ZIP_DEFLATED
            if external_attr is not None:
                item.external_attr = external_attr
            archive.writestr(item, data)


def _manifest_items(path: Path) -> tuple[dict[str, object], list[tuple[str, bytes, int | None]]]:
    items = _zip_items(path)
    manifest = json.loads(next(data for name, data, _ in items if name == "manifest.json"))
    return manifest, items


def _replace_manifest_file(
    manifest: dict[str, object], items: list[tuple[str, bytes, int | None]], path: str, data: bytes
) -> list[tuple[str, bytes, int | None]]:
    files = manifest["files"]
    assert isinstance(files, list)
    entry = next(item for item in files if item["path"] == path)
    entry["byte_length"] = len(data)
    entry["sha256"] = hashlib.sha256(data).hexdigest()
    updated = [
        (
            name,
            (_canonical(manifest) if name == "manifest.json" else data if name == path else raw),
            attr,
        )
        for name, raw, attr in items
    ]
    return updated


def test_backup_is_deterministic_validate_only_and_restores_library_assets(
    tmp_path: Path,
) -> None:
    library = tmp_path / "library"
    audit, attachment_id = _populate_library(library, tmp_path)
    service = PackagingLibraryBackupService()
    first = service.create_backup(library, tmp_path / "first.zip")
    second = service.create_backup(library, tmp_path / "second.zip")

    assert first.archive_sha256 == second.archive_sha256
    assert first.manifest_sha256 == second.manifest_sha256
    assert first.library_state_revision == audit.snapshot().state_revision
    assert {item.path.split("/")[0] for item in first.files} == {
        "packaging-library-state.json",
        "attachments",
        "records",
        "thumbnails",
    }

    empty_destination = tmp_path / "validate-only-empty"
    empty_destination.mkdir()
    validated = service.restore(
        first_path := tmp_path / "first.zip", empty_destination, validate_only=True
    )
    assert validated.archive_sha256 == first.archive_sha256
    assert list(empty_destination.iterdir()) == []

    restored_root = tmp_path / "restored-library"
    restored = service.restore(first_path, restored_root)
    restored_audit = PackagingLibraryAuditStore(restored_root, clock=lambda: _NOW)
    assert restored_audit.validate() == audit.validate()
    assert restored.library_state_revision == audit.snapshot().state_revision
    restored_store = PackagingLibraryStore(restored_root)
    record = restored_store.read_record(attachment_id)
    assert restored_store.verify(record)
    thumbnail_file = next((restored_root / "thumbnails").rglob("*.png"))
    assert hashlib.sha256(thumbnail_file.read_bytes()).hexdigest() == thumbnail_file.stem

    already_empty = tmp_path / "existing-empty-library"
    already_empty.mkdir()
    service.restore(first_path, already_empty)
    assert PackagingLibraryAuditStore(already_empty).validate() == audit.validate()


def test_empty_library_backup_round_trips_without_synthesizing_audit_state(tmp_path: Path) -> None:
    library = tmp_path / "empty-library"
    library.mkdir()
    service = PackagingLibraryBackupService()
    archive = tmp_path / "empty.zip"
    report = service.create_backup(library, archive)
    assert tuple(item.path for item in report.files) == ("packaging-library-state.json",)
    assert not (library / "packaging-library-state.json").exists()

    restored = tmp_path / "empty-restored"
    service.restore(archive, restored)
    assert PackagingLibraryAuditStore(restored).snapshot().assets == ()
    assert (restored / "packaging-library-state.json").is_file()


def test_missing_extra_and_digest_tampering_reject_without_partial_restore(tmp_path: Path) -> None:
    library = tmp_path / "library"
    _populate_library(library, tmp_path)
    service = PackagingLibraryBackupService()
    archive = tmp_path / "good.zip"
    service.create_backup(library, archive)
    original_items = _zip_items(archive)
    file_entry = next(item for item in original_items if item[0].startswith("attachments/"))

    missing = tmp_path / "missing.zip"
    _write_zip(missing, [item for item in original_items if item[0] != file_entry[0]])
    with pytest.raises(PackagingLibraryBackupError, match="inventory_mismatch"):
        service.validate_backup(missing)

    tampered = tmp_path / "tampered.zip"
    _write_zip(
        tampered,
        [
            (name, (data + b"x") if name == file_entry[0] else data, attr)
            for name, data, attr in original_items
        ],
    )
    with pytest.raises(PackagingLibraryBackupError, match="length_mismatch|digest_mismatch"):
        service.validate_backup(tampered)

    extra = tmp_path / "extra.zip"
    extra_bytes = b"extra portable thumbnail"
    extra_digest = hashlib.sha256(extra_bytes).hexdigest()
    extra_path = f"thumbnails/sha256/{extra_digest[:2]}/{extra_digest}.png"
    _write_zip(extra, [*original_items, (extra_path, extra_bytes, None)])
    with pytest.raises(PackagingLibraryBackupError, match="inventory_mismatch"):
        service.validate_backup(extra)

    destination = tmp_path / "must-remain-empty"
    destination.mkdir()
    with pytest.raises(PackagingLibraryBackupError):
        service.restore(tampered, destination)
    assert list(destination.iterdir()) == []


@pytest.mark.parametrize(
    ("entry_name", "entry_attr", "expected_error"),
    [
        ("../escape", None, "path_invalid"),
        ("C:/escape", None, "path_invalid"),
        (
            "records/" + "0" * 64 + ".json",
            (stat.S_IFLNK | 0o777) << 16,
            "symlink_or_special_file",
        ),
    ],
)
def test_unsafe_archive_names_and_symlinks_reject(
    tmp_path: Path, entry_name: str, entry_attr: int | None, expected_error: str
) -> None:
    archive = tmp_path / "unsafe.zip"
    _write_zip(archive, [(entry_name, b"bad", entry_attr)])
    with pytest.raises(PackagingLibraryBackupError, match=expected_error):
        PackagingLibraryBackupService().validate_backup(archive)


def test_duplicate_archive_names_unsupported_manifest_and_corrupt_audit_reject(
    tmp_path: Path,
) -> None:
    library = tmp_path / "library"
    _populate_library(library, tmp_path)
    service = PackagingLibraryBackupService()
    archive = tmp_path / "good.zip"
    service.create_backup(library, archive)
    manifest, items = _manifest_items(archive)

    duplicate = tmp_path / "duplicate.zip"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        _write_zip(duplicate, [*items, items[1]])
    with pytest.raises(PackagingLibraryBackupError, match="duplicate_path"):
        service.validate_backup(duplicate)

    unsupported = tmp_path / "unsupported.zip"
    manifest["schema_version"] = 88
    _write_zip(
        unsupported,
        [
            (name, _canonical(manifest) if name == "manifest.json" else data, attr)
            for name, data, attr in items
        ],
    )
    with pytest.raises(PackagingLibraryBackupError, match="manifest_schema_invalid"):
        service.validate_backup(unsupported)

    manifest, items = _manifest_items(archive)
    state_name = "packaging-library-state.json"
    state = json.loads(next(data for name, data, _ in items if name == state_name))
    state["audit_head_digest"] = "f" * 64
    state_bytes = json.dumps(state, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    corrupted_audit = tmp_path / "corrupted-audit.zip"
    _write_zip(corrupted_audit, _replace_manifest_file(manifest, items, state_name, state_bytes))
    with pytest.raises(PackagingLibraryBackupError, match="library_invalid"):
        service.validate_backup(corrupted_audit)


def test_zip_bomb_budget_and_nonempty_restore_destination_reject(tmp_path: Path) -> None:
    bomb = tmp_path / "bomb.zip"
    bomb_bytes = b"0" * (2 * 1024 * 1024)
    bomb_path = "attachments/sha256/00/" + "0" * 64
    manifest = {
        "contract": "packlab.packaging-library-backup.v1",
        "schema_version": 1,
        "library_state_revision": "packaging-library-state:" + "0" * 64,
        "audit_head_digest": "",
        "files": [{"path": bomb_path, "byte_length": len(bomb_bytes), "sha256": "0" * 64}],
    }
    _write_zip(bomb, [("manifest.json", _canonical(manifest), None), (bomb_path, bomb_bytes, None)])
    with pytest.raises(PackagingLibraryBackupError, match="compression_ratio_invalid"):
        PackagingLibraryBackupService().validate_backup(bomb)

    library = tmp_path / "library"
    _populate_library(library, tmp_path)
    service = PackagingLibraryBackupService()
    archive = tmp_path / "good.zip"
    service.create_backup(library, archive)
    destination = tmp_path / "nonempty"
    destination.mkdir()
    sentinel = destination / "keep.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    with pytest.raises(PackagingLibraryBackupError, match="destination_not_empty"):
        service.restore(archive, destination)
    assert sentinel.read_text(encoding="utf-8") == "preserve"
