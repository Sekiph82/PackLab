"""Explicit-root content-addressed storage for opaque packaging-library evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from packlab_core.packaging_asset import PackagingAsset
from packlab_core.packaging_components import ReusablePackagingComponent
from packlab_core.packaging_sku_library import PackagingSkuRevision

_MAX_ATTACHMENT_BYTES = 32 * 1024 * 1024
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_MEDIA_TYPE = re.compile(r"^[a-z0-9][a-z0-9!#$&^_.+-]{0,63}/[a-z0-9][a-z0-9!#$&^_.+-]{0,63}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EXECUTABLE_SUFFIXES = frozenset(
    {
        ".bat",
        ".cmd",
        ".com",
        ".dll",
        ".exe",
        ".jar",
        ".js",
        ".msi",
        ".ps1",
        ".py",
        ".sh",
        ".vbs",
    }
)


class PackagingLibraryStoreError(ValueError):
    """Raised when attachment metadata, source bytes, or storage paths are unsafe."""


class AttachmentRole(StrEnum):
    DRAWING = "DRAWING"
    QUOTATION = "QUOTATION"
    NOTES = "NOTES"


@dataclass(frozen=True, slots=True)
class PackagingAttachmentRecord:
    """Portable attachment metadata; `relative_path` never contains the injected root."""

    attachment_id: str
    sha256: str
    byte_length: int
    display_name: str
    media_type: str
    role: AttachmentRole
    relative_path: str
    related_asset_id: str | None = None
    related_component_id: str | None = None
    related_sku_id: str | None = None
    contract: str = "packlab.packaging-attachment.v1"

    def __post_init__(self) -> None:
        if self.contract != "packlab.packaging-attachment.v1":
            raise PackagingLibraryStoreError("packaging_attachment_contract_invalid")
        _identifier(self.attachment_id, "attachment_id")
        if not isinstance(self.sha256, str) or not _SHA256.fullmatch(self.sha256):
            raise PackagingLibraryStoreError("packaging_attachment_digest_invalid")
        if (
            isinstance(self.byte_length, bool)
            or not isinstance(self.byte_length, int)
            or not 1 <= self.byte_length <= _MAX_ATTACHMENT_BYTES
        ):
            raise PackagingLibraryStoreError("packaging_attachment_length_invalid")
        _display_name(self.display_name)
        _media_type_value(self.media_type)
        if not isinstance(self.role, AttachmentRole):
            raise PackagingLibraryStoreError("packaging_attachment_role_invalid")
        if self.relative_path != _relative_blob_path(self.sha256):
            raise PackagingLibraryStoreError("packaging_attachment_relative_path_invalid")
        for field_name in ("related_asset_id", "related_component_id", "related_sku_id"):
            value = getattr(self, field_name)
            if value is not None:
                _identifier(value, field_name)
        if self.attachment_id != _attachment_record_id(self):
            raise PackagingLibraryStoreError("packaging_attachment_id_digest_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "attachment_id": self.attachment_id,
            "sha256": self.sha256,
            "byte_length": self.byte_length,
            "display_name": self.display_name,
            "media_type": self.media_type,
            "role": self.role.value,
            "related_asset_id": self.related_asset_id,
            "related_component_id": self.related_component_id,
            "related_sku_id": self.related_sku_id,
            "relative_path": self.relative_path,
            "source_path_included": False,
            "attachment_bytes_embedded": False,
        }

    @property
    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)


class PackagingLibraryStore:
    """Copy bounded opaque files into an explicitly supplied local library root."""

    def __init__(self, library_root: str | Path) -> None:
        if not isinstance(library_root, (str, Path)) or not str(library_root).strip():
            raise PackagingLibraryStoreError("packaging_library_root_required")
        root = Path(library_root).expanduser().absolute()
        if root.exists() and root.is_symlink():
            raise PackagingLibraryStoreError("packaging_library_root_symlink_forbidden")
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink() or not root.is_dir():
            raise PackagingLibraryStoreError("packaging_library_root_invalid")
        self._root = root
        self._attachments_root = root / "attachments"
        self._records_root = root / "records"
        self._ensure_directory(self._attachments_root)
        self._ensure_directory(self._records_root)

    @property
    def library_root(self) -> Path:
        """Return the transient, explicitly injected local root for Studio callers."""
        return self._root

    def add_attachment(
        self,
        source: str | Path,
        *,
        display_name: str,
        media_type: str,
        role: AttachmentRole,
        related_asset_id: str | None = None,
        related_component_id: str | None = None,
        related_sku_id: str | None = None,
        assets: tuple[PackagingAsset, ...] = (),
        components: tuple[ReusablePackagingComponent, ...] = (),
        skus: tuple[PackagingSkuRevision, ...] = (),
    ) -> PackagingAttachmentRecord:
        """Stream one local file to content storage without parsing or executing it."""
        _display_name(display_name)
        normalized_media_type = _media_type_value(media_type)
        if not isinstance(role, AttachmentRole):
            raise PackagingLibraryStoreError("packaging_attachment_role_invalid")
        _validate_related_targets(
            related_asset_id,
            related_component_id,
            related_sku_id,
            assets,
            components,
            skus,
        )
        path = _source_path(source)
        source_stat = _stat_regular_file(path)
        if source_stat.st_size < 1 or source_stat.st_size > _MAX_ATTACHMENT_BYTES:
            raise PackagingLibraryStoreError("packaging_attachment_size_out_of_bounds")

        temp_path: Path | None = None
        digest = hashlib.sha256()
        byte_length = 0
        try:
            no_follow = getattr(os, "O_NOFOLLOW", 0)
            try:
                source_fd = os.open(path, os.O_RDONLY | no_follow)
            except OSError as error:
                raise PackagingLibraryStoreError(
                    "packaging_attachment_source_unavailable"
                ) from error
            try:
                opened_stat = os.fstat(source_fd)
                if not stat.S_ISREG(opened_stat.st_mode) or (
                    opened_stat.st_dev,
                    opened_stat.st_ino,
                ) != (source_stat.st_dev, source_stat.st_ino):
                    raise PackagingLibraryStoreError("packaging_attachment_source_changed")
                temp_fd, temp_name = tempfile.mkstemp(
                    prefix=".incoming-", suffix=".part", dir=self._attachments_root
                )
                temp_path = Path(temp_name)
                with (
                    os.fdopen(source_fd, "rb", closefd=False) as input_stream,
                    os.fdopen(temp_fd, "wb") as output_stream,
                ):
                    while chunk := input_stream.read(1024 * 1024):
                        byte_length += len(chunk)
                        if byte_length > _MAX_ATTACHMENT_BYTES:
                            raise PackagingLibraryStoreError(
                                "packaging_attachment_size_out_of_bounds"
                            )
                        digest.update(chunk)
                        output_stream.write(chunk)
                    output_stream.flush()
                    os.fsync(output_stream.fileno())
            finally:
                os.close(source_fd)

            if byte_length == 0:
                raise PackagingLibraryStoreError("packaging_attachment_empty")
            if byte_length != source_stat.st_size:
                raise PackagingLibraryStoreError("packaging_attachment_source_changed")
            content_sha256 = digest.hexdigest()
            relative_path = _relative_blob_path(content_sha256)
            blob_path = self._root.joinpath(*relative_path.split("/"))
            self._ensure_directory(blob_path.parent)
            if blob_path.exists() or blob_path.is_symlink():
                if blob_path.is_symlink() or not _matches_digest(
                    blob_path, content_sha256, byte_length
                ):
                    raise PackagingLibraryStoreError("packaging_attachment_existing_blob_mismatch")
                temp_path.unlink(missing_ok=True)
            else:
                os.replace(temp_path, blob_path)

            metadata: dict[str, object] = {
                "contract": "packlab.packaging-attachment.v1",
                "sha256": content_sha256,
                "byte_length": byte_length,
                "display_name": display_name,
                "media_type": normalized_media_type,
                "role": role.value,
                "related_asset_id": related_asset_id,
                "related_component_id": related_component_id,
                "related_sku_id": related_sku_id,
                "relative_path": relative_path,
                "source_path_included": False,
                "attachment_bytes_embedded": False,
            }
            attachment_id = (
                "packaging-attachment:"
                + hashlib.sha256(_canonical_json(metadata).encode("utf-8")).hexdigest()
            )
            record = PackagingAttachmentRecord(
                attachment_id=attachment_id,
                sha256=content_sha256,
                byte_length=byte_length,
                display_name=display_name,
                media_type=normalized_media_type,
                role=role,
                relative_path=relative_path,
                related_asset_id=related_asset_id,
                related_component_id=related_component_id,
                related_sku_id=related_sku_id,
            )
            self._publish_record(record)
            return record
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def read_record(self, attachment_id: str) -> PackagingAttachmentRecord:
        _identifier(attachment_id, "attachment_id")
        self._ensure_directory(self._records_root)
        path = self._records_root / _record_filename(attachment_id)
        if path.is_symlink() or not path.is_file():
            raise PackagingLibraryStoreError("packaging_attachment_record_missing")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            record = PackagingAttachmentRecord(
                attachment_id=value["attachment_id"],
                sha256=value["sha256"],
                byte_length=value["byte_length"],
                display_name=value["display_name"],
                media_type=value["media_type"],
                role=AttachmentRole(value["role"]),
                relative_path=value["relative_path"],
                related_asset_id=value["related_asset_id"],
                related_component_id=value["related_component_id"],
                related_sku_id=value["related_sku_id"],
                contract=value["contract"],
            )
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise PackagingLibraryStoreError("packaging_attachment_record_invalid") from error
        if (
            record.attachment_id != attachment_id
            or record.attachment_id != _attachment_record_id(record)
            or path.read_text(encoding="utf-8") != (record.canonical_json + "\n")
        ):
            raise PackagingLibraryStoreError("packaging_attachment_record_identity_mismatch")
        return record

    def verify(self, record: PackagingAttachmentRecord) -> bool:
        if not isinstance(record, PackagingAttachmentRecord):
            raise PackagingLibraryStoreError("packaging_attachment_record_required")
        if record.attachment_id != _attachment_record_id(record):
            raise PackagingLibraryStoreError("packaging_attachment_record_identity_mismatch")
        self._ensure_directory(self._attachments_root)
        path = self._root.joinpath(*record.relative_path.split("/"))
        self._ensure_directory(path.parent)
        if path.is_symlink() or not path.is_file():
            return False
        return _matches_digest(path, record.sha256, record.byte_length)

    def _publish_record(self, record: PackagingAttachmentRecord) -> None:
        self._ensure_directory(self._records_root)
        target = self._records_root / _record_filename(record.attachment_id)
        serialized = record.canonical_json + "\n"
        if target.exists() or target.is_symlink():
            if target.is_symlink() or target.read_text(encoding="utf-8") != serialized:
                raise PackagingLibraryStoreError("packaging_attachment_record_conflict")
            return
        _atomic_write_text(target, serialized)

    def _ensure_directory(self, path: Path) -> None:
        try:
            relative = path.relative_to(self._root)
        except ValueError as error:
            raise PackagingLibraryStoreError("packaging_library_directory_outside_root") from error
        current = self._root
        if current.is_symlink() or not current.is_dir():
            raise PackagingLibraryStoreError("packaging_library_directory_unsafe")
        for part in relative.parts:
            current = current / part
            if current.exists() or current.is_symlink():
                if current.is_symlink() or not current.is_dir():
                    raise PackagingLibraryStoreError("packaging_library_directory_unsafe")
            else:
                current.mkdir()
                if current.is_symlink() or not current.is_dir():
                    raise PackagingLibraryStoreError("packaging_library_directory_unsafe")


def _source_path(source: str | Path) -> Path:
    if not isinstance(source, (str, Path)) or not str(source).strip():
        raise PackagingLibraryStoreError("packaging_attachment_source_required")
    raw = str(source)
    if "\x00" in raw or ".." in Path(raw).parts:
        raise PackagingLibraryStoreError("packaging_attachment_source_traversal_forbidden")
    path = Path(source).expanduser().absolute()
    for ancestor in (path, *path.parents):
        try:
            if ancestor.is_symlink():
                raise PackagingLibraryStoreError("packaging_attachment_source_symlink_forbidden")
        except OSError as error:
            raise PackagingLibraryStoreError("packaging_attachment_source_unavailable") from error
    return path


def _stat_regular_file(path: Path) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise PackagingLibraryStoreError("packaging_attachment_source_unavailable") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise PackagingLibraryStoreError("packaging_attachment_source_symlink_forbidden")
    if not stat.S_ISREG(metadata.st_mode):
        raise PackagingLibraryStoreError("packaging_attachment_source_not_regular_file")
    return metadata


def _validate_related_targets(
    asset_id: str | None,
    component_id: str | None,
    sku_id: str | None,
    assets: tuple[PackagingAsset, ...],
    components: tuple[ReusablePackagingComponent, ...],
    skus: tuple[PackagingSkuRevision, ...],
) -> None:
    for value, field_name in (
        (asset_id, "related_asset_id"),
        (component_id, "related_component_id"),
        (sku_id, "related_sku_id"),
    ):
        if value is not None:
            _identifier(value, field_name)
    if not all(isinstance(value, tuple) for value in (assets, components, skus)):
        raise PackagingLibraryStoreError("packaging_attachment_target_registry_invalid")
    if any(not isinstance(item, PackagingAsset) for item in assets):
        raise PackagingLibraryStoreError("packaging_attachment_asset_registry_invalid")
    if any(not isinstance(item, ReusablePackagingComponent) for item in components):
        raise PackagingLibraryStoreError("packaging_attachment_component_registry_invalid")
    if any(not isinstance(item, PackagingSkuRevision) for item in skus):
        raise PackagingLibraryStoreError("packaging_attachment_sku_registry_invalid")
    if asset_id is not None and not any(item.asset_id == asset_id for item in assets):
        raise PackagingLibraryStoreError("packaging_attachment_asset_target_stale_or_ambiguous")
    if component_id is not None and not any(
        item.component_id == component_id for item in components
    ):
        raise PackagingLibraryStoreError("packaging_attachment_component_target_stale_or_ambiguous")
    if sku_id is not None and not any(item.sku_id == sku_id for item in skus):
        raise PackagingLibraryStoreError("packaging_attachment_sku_target_stale_or_ambiguous")


def _display_name(value: object) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 160
        or value in {".", ".."}
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or any(character in value for character in ("/", "\\", ":"))
        or value.casefold().endswith(tuple(_EXECUTABLE_SUFFIXES))
    ):
        raise PackagingLibraryStoreError("packaging_attachment_display_name_invalid")


def _media_type_value(value: object) -> str:
    if not isinstance(value, str):
        raise PackagingLibraryStoreError("packaging_attachment_media_type_invalid")
    normalized = value.strip().lower()
    if not _MEDIA_TYPE.fullmatch(normalized) or normalized in {
        "application/javascript",
        "application/x-executable",
        "application/x-msdownload",
        "text/html",
        "text/javascript",
        "text/x-python",
    }:
        raise PackagingLibraryStoreError("packaging_attachment_media_type_invalid")
    return normalized


def _identifier(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise PackagingLibraryStoreError(f"packaging_attachment_{field_name}_invalid")


def _relative_blob_path(sha256: str) -> str:
    if not isinstance(sha256, str) or not _SHA256.fullmatch(sha256):
        raise PackagingLibraryStoreError("packaging_attachment_digest_invalid")
    return f"attachments/sha256/{sha256[:2]}/{sha256}"


def _record_filename(attachment_id: str) -> str:
    prefix = "packaging-attachment:"
    if not isinstance(attachment_id, str) or not attachment_id.startswith(prefix):
        raise PackagingLibraryStoreError("packaging_attachment_id_invalid")
    digest = attachment_id[len(prefix) :]
    if not _SHA256.fullmatch(digest):
        raise PackagingLibraryStoreError("packaging_attachment_id_invalid")
    return f"{digest}.json"


def _attachment_record_id(record: PackagingAttachmentRecord) -> str:
    identity = record.as_dict()
    identity.pop("attachment_id")
    digest = hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()
    return "packaging-attachment:" + digest


def _matches_digest(path: Path, expected_sha256: str, expected_length: int) -> bool:
    file_descriptor: int | None = None
    try:
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size != expected_length
            or not 1 <= expected_length <= _MAX_ATTACHMENT_BYTES
        ):
            return False
        file_descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        opened = os.fstat(file_descriptor)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
            metadata.st_dev,
            metadata.st_ino,
        ):
            return False
        actual = hashlib.sha256()
        length = 0
        with os.fdopen(file_descriptor, "rb") as handle:
            file_descriptor = None
            while chunk := handle.read(1024 * 1024):
                length += len(chunk)
                if length > _MAX_ATTACHMENT_BYTES:
                    return False
                actual.update(chunk)
    except OSError as error:
        raise PackagingLibraryStoreError("packaging_attachment_blob_unavailable") from error
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
    return length == expected_length and actual.hexdigest() == expected_sha256


def _canonical_json(value: dict[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _atomic_write_text(target: Path, value: str) -> None:
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}-", suffix=".part", dir=target.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)


__all__ = [
    "AttachmentRole",
    "PackagingAttachmentRecord",
    "PackagingLibraryStore",
    "PackagingLibraryStoreError",
]
