"""Deterministic, offline backup and validate-only restore for a Packaging Library."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .packaging_library_audit import PackagingLibraryAuditError, PackagingLibraryAuditStore
from .packaging_library_store import (
    PackagingLibraryStore,
    PackagingLibraryStoreError,
)

_MANIFEST_PATH = "manifest.json"
_STATE_PATH = "packaging-library-state.json"
_CONTRACT = "packlab.packaging-library-backup.v1"
_THUMBNAIL = re.compile(r"^thumbnails/sha256/([0-9a-f]{2})/([0-9a-f]{64})\.(png|jpg)$")
_ATTACHMENT = re.compile(r"^attachments/sha256/([0-9a-f]{2})/([0-9a-f]{64})$")
_RECORD = re.compile(r"^records/([0-9a-f]{64})\.json$")
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024
_MAX_FILE_BYTES = 128 * 1024 * 1024
_MAX_TOTAL_BYTES = 512 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
_MAX_FILES = 20_000
_MAX_THUMBNAIL_BYTES = 8 * 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PackagingLibraryBackupError(ValueError):
    """Raised when a backup archive or restore target violates the offline contract."""


@dataclass(frozen=True, slots=True)
class BackupFile:
    path: str
    byte_length: int
    sha256: str

    def as_dict(self) -> dict[str, object]:
        return {"path": self.path, "byte_length": self.byte_length, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class PackagingLibraryBackupReport:
    archive_sha256: str
    files: tuple[BackupFile, ...]
    library_state_revision: str
    audit_head_digest: str
    manifest_sha256: str


class PackagingLibraryBackupService:
    """Create deterministic portable backups and validate/restore them offline."""

    def create_backup(
        self,
        library_root: str | Path,
        archive_path: str | Path,
        *,
        overwrite: bool = False,
    ) -> PackagingLibraryBackupReport:
        root = _library_root(library_root)
        destination = _destination_path(archive_path)
        if destination == root or destination.is_relative_to(root):
            raise PackagingLibraryBackupError("packaging_library_backup_destination_inside_root")
        if destination.exists() and not overwrite:
            raise PackagingLibraryBackupError("packaging_library_backup_destination_exists")
        files_before = _inventory(root)
        if len(files_before) > _MAX_FILES:
            raise PackagingLibraryBackupError("packaging_library_backup_file_limit_exceeded")

        with tempfile.TemporaryDirectory(prefix="packlab-library-backup-") as temporary:
            staged_root = Path(temporary) / "library"
            staged_root.mkdir()
            source_snapshot = PackagingLibraryAuditStore(root).validate()
            backup_files: list[BackupFile] = []
            total_bytes = 0
            for relative_path, source_path, source_stat in files_before:
                data = _read_stable_file(source_path, source_stat, _MAX_FILE_BYTES)
                total_bytes += len(data)
                if total_bytes > _MAX_TOTAL_BYTES:
                    raise PackagingLibraryBackupError(
                        "packaging_library_backup_total_size_limit_exceeded"
                    )
                target = staged_root.joinpath(*relative_path.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                backup_files.append(
                    BackupFile(relative_path, len(data), hashlib.sha256(data).hexdigest())
                )
            if not any(item.path == _STATE_PATH for item in backup_files):
                state_document = {
                    "schema_version": 3,
                    "state_revision": source_snapshot.state_revision,
                    "audit_head_digest": source_snapshot.audit_head_digest,
                    "assets": [],
                    "events": [],
                    "relationships": [],
                    "skus": [],
                }
                state_bytes = _canonical_json(state_document)
                (staged_root / _STATE_PATH).write_bytes(state_bytes)
                backup_files.append(
                    BackupFile(
                        _STATE_PATH, len(state_bytes), hashlib.sha256(state_bytes).hexdigest()
                    )
                )
            _ensure_inventory_unchanged(root, files_before)
            snapshot = _validate_library_root(
                staged_root,
                expected_state_revision=None,
                expected_audit_head_digest=None,
            )
            manifest = _manifest_document(
                snapshot.state_revision, snapshot.audit_head_digest, backup_files
            )
            manifest_bytes = _canonical_json(manifest)
            if len(manifest_bytes) > _MAX_MANIFEST_BYTES:
                raise PackagingLibraryBackupError("packaging_library_backup_manifest_too_large")

            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary_archive = _temporary_file(destination.parent, destination.name)
            try:
                _write_zip(temporary_archive, staged_root, manifest_bytes, backup_files)
                if temporary_archive.stat().st_size > _MAX_ARCHIVE_BYTES:
                    raise PackagingLibraryBackupError(
                        "packaging_library_backup_archive_size_invalid"
                    )
                if destination.exists() and not overwrite:
                    raise PackagingLibraryBackupError("packaging_library_backup_destination_exists")
                os.replace(temporary_archive, destination)
            finally:
                temporary_archive.unlink(missing_ok=True)

            return PackagingLibraryBackupReport(
                archive_sha256=_file_sha256(destination),
                files=tuple(backup_files),
                library_state_revision=snapshot.state_revision,
                audit_head_digest=snapshot.audit_head_digest,
                manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
            )

    def validate_backup(self, archive_path: str | Path) -> PackagingLibraryBackupReport:
        """Validate archive inventory and staged library state without touching a target root."""
        archive = _archive_path(archive_path)
        with tempfile.TemporaryDirectory(prefix="packlab-library-validate-") as temporary:
            stage = Path(temporary) / "library"
            stage.mkdir()
            return _extract_and_validate(archive, stage)

    def restore(
        self,
        archive_path: str | Path,
        library_root: str | Path,
        *,
        validate_only: bool = False,
    ) -> PackagingLibraryBackupReport:
        """Validate a backup or atomically publish it into a new or empty library root."""
        if not isinstance(validate_only, bool):
            raise PackagingLibraryBackupError("packaging_library_restore_validate_only_invalid")
        archive = _archive_path(archive_path)
        if validate_only:
            return self.validate_backup(archive)
        destination = _restore_destination(library_root)
        if destination.exists() and any(destination.iterdir()):
            raise PackagingLibraryBackupError("packaging_library_restore_destination_not_empty")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".packlab-library-restore-", dir=destination.parent
        ) as temporary:
            stage = Path(temporary) / "library"
            stage.mkdir()
            report = _extract_and_validate(archive, stage)
            removed_empty_destination = False
            try:
                if destination.exists():
                    if _is_link_or_junction(destination) or any(destination.iterdir()):
                        raise PackagingLibraryBackupError(
                            "packaging_library_restore_destination_not_empty"
                        )
                    destination.rmdir()
                    removed_empty_destination = True
                os.replace(stage, destination)
            except OSError as error:
                if removed_empty_destination and not destination.exists():
                    destination.mkdir()
                raise PackagingLibraryBackupError(
                    "packaging_library_restore_publish_failed"
                ) from error
            return report


def _manifest_document(
    state_revision: str,
    audit_head_digest: str,
    files: list[BackupFile],
) -> dict[str, object]:
    return {
        "contract": _CONTRACT,
        "schema_version": 1,
        "library_state_revision": state_revision,
        "audit_head_digest": audit_head_digest,
        "files": [item.as_dict() for item in sorted(files, key=lambda item: item.path)],
    }


def _extract_and_validate(archive: Path, stage: Path) -> PackagingLibraryBackupReport:
    try:
        archive_stat = archive.lstat()
        if stat.S_ISLNK(archive_stat.st_mode) or not stat.S_ISREG(archive_stat.st_mode):
            raise PackagingLibraryBackupError("packaging_library_backup_archive_not_regular")
        if archive_stat.st_size <= 0 or archive_stat.st_size > _MAX_ARCHIVE_BYTES:
            raise PackagingLibraryBackupError("packaging_library_backup_archive_size_invalid")
        with zipfile.ZipFile(archive, mode="r") as bundle:
            entries = bundle.infolist()
            manifest_info = _check_zip_entries(entries)
            if manifest_info.file_size > _MAX_MANIFEST_BYTES:
                raise PackagingLibraryBackupError("packaging_library_backup_manifest_too_large")
            manifest_bytes = _read_zip_entry(bundle, manifest_info, _MAX_MANIFEST_BYTES)
            manifest = _parse_manifest(manifest_bytes)
            raw_files = manifest.get("files")
            if not isinstance(raw_files, list):
                raise PackagingLibraryBackupError("packaging_library_backup_manifest_invalid")
            files = tuple(_parse_backup_file(item) for item in raw_files)
            paths = tuple(item.path for item in files)
            if paths != tuple(sorted(paths)) or len(paths) != len(set(paths)):
                raise PackagingLibraryBackupError("packaging_library_backup_manifest_order_invalid")
            if len(files) > _MAX_FILES:
                raise PackagingLibraryBackupError("packaging_library_backup_file_limit_exceeded")
            total_bytes = sum(item.byte_length for item in files)
            if total_bytes > _MAX_TOTAL_BYTES:
                raise PackagingLibraryBackupError(
                    "packaging_library_backup_total_size_limit_exceeded"
                )
            expected_names = {_MANIFEST_PATH, *paths}
            actual_names = {item.filename for item in entries}
            if actual_names != expected_names:
                raise PackagingLibraryBackupError(
                    "packaging_library_backup_file_inventory_mismatch"
                )
            by_name = {item.filename: item for item in entries}
            for item in files:
                info = by_name[item.path]
                if info.file_size != item.byte_length or info.file_size > _MAX_FILE_BYTES:
                    raise PackagingLibraryBackupError(
                        "packaging_library_backup_file_length_mismatch"
                    )
                data = _read_zip_entry(bundle, info, _MAX_FILE_BYTES)
                if len(data) != item.byte_length or hashlib.sha256(data).hexdigest() != item.sha256:
                    raise PackagingLibraryBackupError(
                        "packaging_library_backup_file_digest_mismatch"
                    )
                target = stage.joinpath(*item.path.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    except PackagingLibraryBackupError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError, KeyError, TypeError) as error:
        raise PackagingLibraryBackupError("packaging_library_backup_archive_invalid") from error

    try:
        snapshot = _validate_library_root(
            stage,
            expected_state_revision=manifest["library_state_revision"],
            expected_audit_head_digest=manifest["audit_head_digest"],
        )
    except (PackagingLibraryAuditError, PackagingLibraryStoreError, OSError, ValueError) as error:
        raise PackagingLibraryBackupError("packaging_library_backup_library_invalid") from error
    manifest_file = next((item for item in entries if item.filename == _MANIFEST_PATH), None)
    assert manifest_file is not None
    return PackagingLibraryBackupReport(
        archive_sha256=_file_sha256(archive),
        files=files,
        library_state_revision=snapshot.state_revision,
        audit_head_digest=snapshot.audit_head_digest,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
    )


def _validate_library_root(
    root: Path,
    *,
    expected_state_revision: object,
    expected_audit_head_digest: object,
):
    state_path = root / _STATE_PATH
    if _is_link_or_junction(state_path) or not state_path.is_file():
        raise PackagingLibraryBackupError("packaging_library_backup_state_file_missing")
    audit_store = PackagingLibraryAuditStore(root)
    snapshot = audit_store.validate()
    if expected_state_revision is not None and snapshot.state_revision != expected_state_revision:
        raise PackagingLibraryBackupError("packaging_library_backup_state_revision_mismatch")
    if (
        expected_audit_head_digest is not None
        and snapshot.audit_head_digest != expected_audit_head_digest
    ):
        raise PackagingLibraryBackupError("packaging_library_backup_audit_head_mismatch")

    records_dir = root / "records"
    store = PackagingLibraryStore(root)
    expected_records: set[str] = set()
    expected_blobs: set[str] = set()
    if records_dir.exists():
        for record_path in records_dir.iterdir():
            if (
                _is_link_or_junction(record_path)
                or not record_path.is_file()
                or record_path.suffix != ".json"
            ):
                raise PackagingLibraryBackupError("packaging_library_backup_record_path_invalid")
            attachment_id = "packaging-attachment:" + record_path.stem
            record = store.read_record(attachment_id)
            if not store.verify(record):
                raise PackagingLibraryBackupError(
                    "packaging_library_backup_attachment_digest_invalid"
                )
            expected_records.add(record_path.relative_to(root).as_posix())
            expected_blobs.add(record.relative_path)
    actual_blobs = _files_under(root, "attachments")
    if actual_blobs != expected_blobs:
        raise PackagingLibraryBackupError("packaging_library_backup_attachment_inventory_mismatch")
    actual_records = _files_under(root, "records")
    if actual_records != expected_records:
        raise PackagingLibraryBackupError("packaging_library_backup_record_inventory_mismatch")
    for relative_path in _files_under(root, "thumbnails"):
        match = _THUMBNAIL.fullmatch(relative_path)
        if match is None or match.group(1) != match.group(2)[:2]:
            raise PackagingLibraryBackupError("packaging_library_backup_thumbnail_path_invalid")
        path = root.joinpath(*relative_path.split("/"))
        maximum = _MAX_THUMBNAIL_BYTES
        data = _read_stable_file(path, path.lstat(), maximum)
        if hashlib.sha256(data).hexdigest() != match.group(2):
            raise PackagingLibraryBackupError("packaging_library_backup_thumbnail_digest_invalid")
    _assert_only_library_files(root)
    return snapshot


def _inventory(root: Path) -> tuple[tuple[str, Path, os.stat_result], ...]:
    allowed = {_STATE_PATH, ".packaging-library-state.lock", "attachments", "records", "thumbnails"}
    for item in root.iterdir():
        if item.name not in allowed:
            raise PackagingLibraryBackupError("packaging_library_backup_unrecognized_library_file")
        if _is_link_or_junction(item):
            raise PackagingLibraryBackupError("packaging_library_backup_symlink_forbidden")
    result: list[tuple[str, Path, os.stat_result]] = []
    state = root / _STATE_PATH
    if state.exists():
        metadata = state.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise PackagingLibraryBackupError("packaging_library_backup_state_file_invalid")
        result.append((_STATE_PATH, state, metadata))
    for directory_name in ("attachments", "records", "thumbnails"):
        directory = root / directory_name
        if not directory.exists():
            continue
        if _is_link_or_junction(directory) or not directory.is_dir():
            raise PackagingLibraryBackupError("packaging_library_backup_directory_invalid")
        for current, directories, filenames in os.walk(directory, followlinks=False):
            current_path = Path(current)
            for name in directories:
                if _is_link_or_junction(current_path / name):
                    raise PackagingLibraryBackupError("packaging_library_backup_symlink_forbidden")
            for name in filenames:
                path = current_path / name
                metadata = path.lstat()
                if not stat.S_ISREG(metadata.st_mode):
                    raise PackagingLibraryBackupError("packaging_library_backup_file_not_regular")
                relative = path.relative_to(root).as_posix()
                _safe_library_path(relative)
                result.append((relative, path, metadata))
    return tuple(sorted(result, key=lambda item: item[0]))


def _ensure_inventory_unchanged(
    root: Path,
    initial: tuple[tuple[str, Path, os.stat_result], ...],
) -> None:
    current = _inventory(root)
    initial_identity = tuple(
        (path, info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
        for path, _, info in initial
    )
    current_identity = tuple(
        (path, info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
        for path, _, info in current
    )
    if initial_identity != current_identity:
        raise PackagingLibraryBackupError("packaging_library_backup_source_changed")


def _read_stable_file(path: Path, expected: os.stat_result, maximum: int) -> bytes:
    try:
        if _is_link_or_junction(path):
            raise PackagingLibraryBackupError("packaging_library_backup_symlink_forbidden")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
                expected.st_dev,
                expected.st_ino,
            ):
                raise PackagingLibraryBackupError("packaging_library_backup_source_changed")
            if opened.st_size <= 0 or opened.st_size > maximum:
                raise PackagingLibraryBackupError("packaging_library_backup_file_size_invalid")
            chunks: list[bytes] = []
            length = 0
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                while chunk := handle.read(1024 * 1024):
                    length += len(chunk)
                    if length > maximum:
                        raise PackagingLibraryBackupError(
                            "packaging_library_backup_file_size_invalid"
                        )
                    chunks.append(chunk)
            if length != opened.st_size:
                raise PackagingLibraryBackupError("packaging_library_backup_source_changed")
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    except PackagingLibraryBackupError:
        raise
    except OSError as error:
        raise PackagingLibraryBackupError("packaging_library_backup_source_unavailable") from error


def _check_zip_entries(entries: list[zipfile.ZipInfo]) -> zipfile.ZipInfo:
    if not 1 <= len(entries) <= _MAX_FILES + 1:
        raise PackagingLibraryBackupError("packaging_library_backup_file_limit_exceeded")
    seen: set[str] = set()
    folded: set[str] = set()
    manifest: zipfile.ZipInfo | None = None
    for item in entries:
        name = item.filename
        if name in seen or name.casefold() in folded:
            raise PackagingLibraryBackupError("packaging_library_backup_duplicate_path")
        seen.add(name)
        folded.add(name.casefold())
        _safe_library_path(name, allow_manifest=True)
        if item.is_dir() or item.flag_bits & 0x1:
            raise PackagingLibraryBackupError("packaging_library_backup_zip_entry_invalid")
        mode = item.external_attr >> 16
        kind = stat.S_IFMT(mode)
        if kind not in {0, stat.S_IFREG}:
            raise PackagingLibraryBackupError("packaging_library_backup_symlink_or_special_file")
        if item.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise PackagingLibraryBackupError("packaging_library_backup_compression_invalid")
        if item.file_size < 0 or item.file_size > _MAX_FILE_BYTES:
            if name == _MANIFEST_PATH:
                raise PackagingLibraryBackupError("packaging_library_backup_manifest_too_large")
            raise PackagingLibraryBackupError("packaging_library_backup_file_size_invalid")
        if item.compress_size < 0 or item.compress_size > _MAX_ARCHIVE_BYTES:
            raise PackagingLibraryBackupError("packaging_library_backup_compressed_size_invalid")
        if item.file_size > max(1, item.compress_size) * 1000:
            raise PackagingLibraryBackupError("packaging_library_backup_compression_ratio_invalid")
        if name == _MANIFEST_PATH:
            manifest = item
    if manifest is None:
        raise PackagingLibraryBackupError("packaging_library_backup_manifest_missing")
    return manifest


def _parse_manifest(data: bytes) -> dict[str, object]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PackagingLibraryBackupError("packaging_library_backup_manifest_invalid") from error
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "contract",
            "schema_version",
            "library_state_revision",
            "audit_head_digest",
            "files",
        }
        or value.get("contract") != _CONTRACT
        or isinstance(value.get("schema_version"), bool)
        or value.get("schema_version") != 1
        or not isinstance(value.get("files"), list)
        or not isinstance(value.get("library_state_revision"), str)
        or not isinstance(value.get("audit_head_digest"), str)
        or data != _canonical_json(value)
    ):
        raise PackagingLibraryBackupError("packaging_library_backup_manifest_schema_invalid")
    return value


def _parse_backup_file(value: object) -> BackupFile:
    if not isinstance(value, dict) or set(value) != {"path", "byte_length", "sha256"}:
        raise PackagingLibraryBackupError("packaging_library_backup_manifest_entry_invalid")
    path = value.get("path")
    length = value.get("byte_length")
    digest = value.get("sha256")
    if (
        not isinstance(path, str)
        or isinstance(length, bool)
        or not isinstance(length, int)
        or not 1 <= length <= _MAX_FILE_BYTES
        or not isinstance(digest, str)
        or not _SHA256.fullmatch(digest)
    ):
        raise PackagingLibraryBackupError("packaging_library_backup_manifest_entry_invalid")
    _safe_library_path(path)
    return BackupFile(path, length, digest)


def _safe_library_path(value: str, *, allow_manifest: bool = False) -> None:
    if allow_manifest and value == _MANIFEST_PATH:
        return
    if value == _STATE_PATH:
        return
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "\x00" in value:
        raise PackagingLibraryBackupError("packaging_library_backup_path_invalid")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or str(path) != value
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise PackagingLibraryBackupError("packaging_library_backup_path_invalid")
    match = _ATTACHMENT.fullmatch(value)
    if match is not None and match.group(1) == match.group(2)[:2]:
        return
    match = _RECORD.fullmatch(value)
    if match is not None:
        return
    match = _THUMBNAIL.fullmatch(value)
    if match is not None and match.group(1) == match.group(2)[:2]:
        return
    raise PackagingLibraryBackupError("packaging_library_backup_path_invalid")


def _files_under(root: Path, directory_name: str) -> set[str]:
    directory = root / directory_name
    if not directory.exists():
        return set()
    if _is_link_or_junction(directory) or not directory.is_dir():
        raise PackagingLibraryBackupError("packaging_library_backup_directory_invalid")
    found: set[str] = set()
    for current, directories, filenames in os.walk(directory, followlinks=False):
        current_path = Path(current)
        if any(_is_link_or_junction(current_path / name) for name in directories):
            raise PackagingLibraryBackupError("packaging_library_backup_symlink_forbidden")
        for name in filenames:
            path = current_path / name
            if _is_link_or_junction(path) or not path.is_file():
                raise PackagingLibraryBackupError("packaging_library_backup_file_not_regular")
            found.add(path.relative_to(root).as_posix())
    return found


def _assert_only_library_files(root: Path) -> None:
    allowed = {_STATE_PATH, ".packaging-library-state.lock", "attachments", "records", "thumbnails"}
    for item in root.iterdir():
        if item.name not in allowed:
            raise PackagingLibraryBackupError("packaging_library_backup_unrecognized_library_file")


def _read_zip_entry(bundle: zipfile.ZipFile, item: zipfile.ZipInfo, maximum: int) -> bytes:
    if item.file_size > maximum:
        raise PackagingLibraryBackupError("packaging_library_backup_file_size_invalid")
    data = bytearray()
    try:
        with bundle.open(item, "r") as stream:
            while chunk := stream.read(1024 * 1024):
                data.extend(chunk)
                if len(data) > maximum:
                    raise PackagingLibraryBackupError("packaging_library_backup_file_size_invalid")
    except PackagingLibraryBackupError:
        raise
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        raise PackagingLibraryBackupError("packaging_library_backup_entry_corrupt") from error
    return bytes(data)


def _write_zip(
    target: Path,
    library_root: Path,
    manifest_bytes: bytes,
    files: list[BackupFile],
) -> None:
    try:
        with target.open("wb") as raw:
            with zipfile.ZipFile(
                raw, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
            ) as bundle:
                for name, data in [(_MANIFEST_PATH, manifest_bytes)]:
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | 0o600) << 16
                    bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
                for item in sorted(files, key=lambda item: item.path):
                    info = zipfile.ZipInfo(item.path, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | 0o600) << 16
                    data = library_root.joinpath(*item.path.split("/")).read_bytes()
                    bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            raw.flush()
            os.fsync(raw.fileno())
    except (OSError, zipfile.BadZipFile) as error:
        raise PackagingLibraryBackupError("packaging_library_backup_write_failed") from error


def _library_root(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise PackagingLibraryBackupError("packaging_library_backup_root_required")
    root = Path(value).expanduser().absolute()
    if _is_link_or_junction(root) or not root.is_dir():
        raise PackagingLibraryBackupError("packaging_library_backup_root_invalid")
    return root


def _destination_path(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise PackagingLibraryBackupError("packaging_library_backup_destination_required")
    path = Path(value).expanduser().absolute()
    if _is_link_or_junction(path) or (path.exists() and not path.is_file()):
        raise PackagingLibraryBackupError("packaging_library_backup_destination_invalid")
    return path


def _archive_path(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise PackagingLibraryBackupError("packaging_library_backup_archive_required")
    path = Path(value).expanduser().absolute()
    if _is_link_or_junction(path) or not path.is_file():
        raise PackagingLibraryBackupError("packaging_library_backup_archive_missing")
    return path


def _restore_destination(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise PackagingLibraryBackupError("packaging_library_restore_root_required")
    destination = Path(value).expanduser().absolute()
    if _is_link_or_junction(destination) or (destination.exists() and not destination.is_dir()):
        raise PackagingLibraryBackupError("packaging_library_restore_root_invalid")
    return destination


def _is_link_or_junction(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or (callable(is_junction) and bool(is_junction()))


def _temporary_file(parent: Path, name: str) -> Path:
    descriptor, path = tempfile.mkstemp(prefix=f".{name}-", suffix=".part", dir=parent)
    os.close(descriptor)
    return Path(path)


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "BackupFile",
    "PackagingLibraryBackupError",
    "PackagingLibraryBackupReport",
    "PackagingLibraryBackupService",
]
