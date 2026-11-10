"""Fail-closed PackScan 1.0 container operations.

The implementation intentionally has no platform or device dependencies. It
validates ZIP structure and manifest/checksum evidence before exposing payload
bytes or extracting them to a caller-owned destination.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import struct
import tempfile
import zipfile
import zlib
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from ..resource_paths import packlab_data_root

CANONICALIZATION = "sha256_32_bytes_lowercase_hex_64_chars_v1"
SCHEMA_VERSION = "1.0.0"
_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_CONTROL_ENTRIES = frozenset({"manifest.json", "checksums.json"})
_REQUIRED_ENTRIES = frozenset({"manifest.json", "metadata/photos.json", "checksums.json"})
_ALLOWED_PREFIXES = (
    "metadata/",
    "images/",
    "masks/",
    "previews/",
    "thumbnails/",
    "diagnostics/",
    "calibration/",
)
MAX_PACKSCAN_BYTES = 512 * 1024 * 1024
MAX_PACKSCAN_ENTRIES = 1024
MAX_PACKSCAN_ENTRY_BYTES = 64 * 1024 * 1024
MAX_PACKSCAN_CONTROL_ENTRY_BYTES = 4 * 1024 * 1024
MAX_PACKSCAN_TOTAL_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_PACKSCAN_PATH_BYTES = 4096
MAX_PACKSCAN_CENTRAL_DIRECTORY_BYTES = MAX_PACKSCAN_ENTRIES * (46 + MAX_PACKSCAN_PATH_BYTES)
_ZIP_EOCD = b"PK\x05\x06"
_ZIP_MAX_COMMENT_BYTES = 65535


class PackScanError(ValueError):
    """Structured validation failure with a stable machine-readable code."""

    def __init__(self, code: str, message: str, path: str | None = None) -> None:
        self.code = code
        self.path = path
        suffix = f" ({path})" if path else ""
        super().__init__(f"{code}{suffix}: {message}")


@dataclass(frozen=True)
class PackScanReport:
    """Validated package metadata and payload bytes."""

    source: Path
    manifest: dict[str, object]
    checksums: dict[str, str]
    payloads: dict[str, bytes]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _safe_entry_name(name: object) -> str:
    if not isinstance(name, str) or not name or name.startswith(("/", "\\")) or "\\" in name:
        raise PackScanError("unsafe_path", "entry must be a non-empty relative UTF-8 path")
    if len(name) > 1024:
        raise PackScanError("unsafe_path", "entry path exceeds the PackScan path-length limit", name[:128])
    if _DRIVE_RE.match(name):
        raise PackScanError("unsafe_path", "drive-prefixed entries are forbidden", name)
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PackScanError("unsafe_path", "empty, dot, and dot-dot components are forbidden", name)
    if any(ord(character) < 0x20 for character in name):
        raise PackScanError("unsafe_path", "control characters are forbidden", name)
    return name


def _read_json(data: bytes, code: str, path: str) -> object:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as error:
        raise PackScanError(code, "UTF-8 JSON is invalid", path) from error


@cache
def _schema_validator(schema_name: str) -> Draft202012Validator:
    schema_path = _packscan_schema_dir() / schema_name
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as error:
        raise PackScanError("schema_resource_unavailable", "schema resource is invalid") from error
    return Draft202012Validator(schema)


def _packscan_schema_dir() -> Path:
    schema_dir = packlab_data_root() / "schemas" / "packscan"
    if not schema_dir.is_dir():
        raise PackScanError("schema_resource_unavailable", "packscan schema directory is missing")
    return schema_dir


def _validate_against_schema(value: object, schema_name: str, path: str, code: str) -> None:
    try:
        _schema_validator(schema_name).validate(value)
    except ValidationError as error:
        detail_path = "/".join(str(part) for part in error.absolute_path)
        suffix = f" at {detail_path}" if detail_path else ""
        raise PackScanError(code, f"canonical schema validation failed{suffix}", path) from error
    except RecursionError as error:
        raise PackScanError(code, "schema validation exceeded supported nesting depth", path) from error


def _validate_manifest(manifest: object) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    if not isinstance(manifest, dict):
        raise PackScanError("schema_invalid", "manifest must be a JSON object", "manifest.json")
    version = manifest.get("schema_version")
    if version != SCHEMA_VERSION:
        raise PackScanError(
            _version_error_code(version),
            f"expected schema version {SCHEMA_VERSION}",
            "manifest.json",
        )
    _validate_against_schema(manifest, "manifest.schema.json", "manifest.json", "schema_invalid")
    payloads = manifest["payloads"]
    by_path: dict[str, dict[str, object]] = {}
    folded: set[str] = set()
    for item in payloads:
        path = _safe_entry_name(item["path"])
        if path in _CONTROL_ENTRIES or path.casefold() in folded:
            raise PackScanError("duplicate_payload", "payload path is ambiguous", path)
        folded.add(path.casefold())
        if not any(path.startswith(prefix) for prefix in _ALLOWED_PREFIXES):
            raise PackScanError("schema_invalid", "payload namespace is not registered", path)
        kind = item["kind"]
        if kind == "image" and not path.startswith("images/"):
            raise PackScanError("schema_invalid", "image payload must be under images/", path)
        if kind == "photo_metadata" and path != "metadata/photos.json":
            raise PackScanError("schema_invalid", "photo metadata path is fixed", path)
        if kind in {"preview", "thumbnail"} and (
            item["authority"] != "derived"
            or item["required"]
            or not path.startswith(("previews/", "thumbnails/"))
            or item.get("media_type") not in {"image/jpeg", "image/png", "image/webp"}
        ):
            raise PackScanError("schema_invalid", "preview/thumbnail declaration is invalid", path)
        if kind == "diagnostics" and (
            item["authority"] != "derived"
            or item["required"]
            or not path.startswith("diagnostics/")
            or item.get("media_type") != "application/json"
        ):
            raise PackScanError("schema_invalid", "diagnostics declaration is invalid", path)
        by_path[path] = item
    if "metadata/photos.json" not in by_path or not any(
        item["kind"] == "image" for item in by_path.values()
    ):
        raise PackScanError(
            "schema_invalid",
            "manifest needs metadata/photos.json and an image payload",
            "manifest.json",
        )
    if len(by_path) + len(_CONTROL_ENTRIES) > MAX_PACKSCAN_ENTRIES:
        raise PackScanError(
            "too_many_entries", "manifest payload count exceeds the PackScan limit", "manifest.json"
        )
    declared_total = 0
    for path, item in by_path.items():
        size = item["size_bytes"]
        if isinstance(size, bool) or not isinstance(size, int) or size > MAX_PACKSCAN_ENTRY_BYTES:
            raise PackScanError("entry_too_large", "manifest payload size exceeds the PackScan limit", path)
        declared_total += size
        if declared_total > MAX_PACKSCAN_TOTAL_UNCOMPRESSED_BYTES:
            raise PackScanError("package_expands_too_large", "manifest payload sizes exceed the PackScan limit")
    return manifest, by_path


def _version_error_code(version: object) -> str:
    if not isinstance(version, str):
        return "unsupported_version"
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if match is None:
        return "unsupported_version"
    for actual, supported in zip(match.groups(), ("1", "0", "0")):
        normalized = actual.lstrip("0") or "0"
        if len(normalized) > len(supported) or (
            len(normalized) == len(supported) and normalized > supported
        ):
            return "unsupported_future_version"
        if normalized != supported:
            return "unsupported_version"
    return "unsupported_version"


def _preflight_zip_entry_count(stream, package_bytes: int) -> int:
    """Validate bounded central-directory records before ZipFile materializes them."""
    if package_bytes < 22:
        raise PackScanError("corrupt_zip", "ZIP end record is missing")
    tail_size = min(package_bytes, 22 + _ZIP_MAX_COMMENT_BYTES)
    stream.seek(-tail_size, os.SEEK_END)
    tail = stream.read(tail_size)
    for index in range(len(tail) - 22, -1, -1):
        if tail[index : index + 4] != _ZIP_EOCD:
            continue
        disk_number, central_disk, disk_entries, total_entries, central_size, central_offset, comment_size = (
            struct.unpack_from("<HHHHIIH", tail, index + 4)
        )
        if index + 22 + comment_size != len(tail):
            continue
        if comment_size != 0:
            raise PackScanError("corrupt_zip", "ZIP archive comments are unsupported")
        if disk_number != 0 or central_disk != 0 or disk_entries != total_entries:
            raise PackScanError("corrupt_zip", "multi-disk ZIP archives are unsupported")
        if total_entries == 0xFFFF or central_size == 0xFFFFFFFF or central_offset == 0xFFFFFFFF:
            raise PackScanError("too_many_entries", "ZIP64 exceeds the bounded PackScan layout")
        if total_entries > MAX_PACKSCAN_ENTRIES:
            raise PackScanError("too_many_entries", "ZIP entry count exceeds the PackScan limit")
        eocd_offset = package_bytes - tail_size + index
        if central_size > MAX_PACKSCAN_CENTRAL_DIRECTORY_BYTES:
            raise PackScanError("corrupt_zip", "ZIP central directory exceeds the PackScan limit")
        if central_offset + central_size != eocd_offset:
            raise PackScanError("corrupt_zip", "ZIP central directory bounds do not match its end record")
        stream.seek(central_offset)
        parsed_bytes = 0
        for _ in range(total_entries):
            header = stream.read(46)
            if len(header) != 46:
                raise PackScanError("corrupt_zip", "ZIP central-directory record is truncated")
            fields = struct.unpack("<4s6H3I5H2I", header)
            if fields[0] != b"PK\x01\x02":
                raise PackScanError("corrupt_zip", "ZIP central-directory record signature is invalid")
            compressed_size, uncompressed_size = fields[8], fields[9]
            name_size, extra_size, comment_size = fields[10], fields[11], fields[12]
            disk_start = fields[13]
            local_offset = fields[16]
            if (
                name_size < 1
                or name_size > MAX_PACKSCAN_PATH_BYTES
                or extra_size != 0
                or comment_size != 0
                or disk_start != 0
                or compressed_size == 0xFFFFFFFF
                or uncompressed_size == 0xFFFFFFFF
                or local_offset == 0xFFFFFFFF
            ):
                raise PackScanError("corrupt_zip", "ZIP central-directory metadata is outside PackScan bounds")
            name = stream.read(name_size)
            if len(name) != name_size:
                raise PackScanError("corrupt_zip", "ZIP central-directory name is truncated")
            if b"\x00" in name or any(byte < 0x20 for byte in name):
                raise PackScanError("unsafe_path", "ZIP entry name contains a control byte")
            if any(byte >= 0x80 for byte in name) and not (fields[3] & 0x0800):
                raise PackScanError("unsafe_path", "non-ASCII ZIP entry names must declare UTF-8")
            try:
                name.decode("utf-8")
            except UnicodeDecodeError as error:
                raise PackScanError("unsafe_path", "ZIP entry name is not valid UTF-8") from error
            parsed_bytes += 46 + name_size
        if parsed_bytes != central_size:
            raise PackScanError("corrupt_zip", "ZIP central-directory size does not match its records")
        return total_entries
    raise PackScanError("corrupt_zip", "valid ZIP end record is missing")


def _load_archive(path: Path) -> dict[str, bytes]:
    try:
        with path.open("rb") as source:
            metadata = os.fstat(source.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise PackScanError("package_unavailable", "package must be a regular file")
            if metadata.st_size > MAX_PACKSCAN_BYTES:
                raise PackScanError("package_too_large", "compressed package exceeds the PackScan limit")
            declared_entry_count = _preflight_zip_entry_count(source, metadata.st_size)
            source.seek(0)
            with zipfile.ZipFile(source, mode="r") as archive:
                infos = archive.infolist()
                if len(infos) != declared_entry_count or len(infos) > MAX_PACKSCAN_ENTRIES:
                    raise PackScanError("corrupt_zip", "ZIP entry count differs from its end record")
                names: set[str] = set()
                folded: set[str] = set()
                declared_total = 0
                for info in infos:
                    if info.is_dir() or info.filename.endswith("/"):
                        raise PackScanError(
                            "directory_entry", "directory entries are forbidden", info.filename
                        )
                    name = _safe_entry_name(info.filename)
                    if name in names or name.casefold() in folded:
                        raise PackScanError(
                            "duplicate_entry", "duplicate or case-insensitive duplicate entry", name
                        )
                    if info.file_size > MAX_PACKSCAN_ENTRY_BYTES:
                        raise PackScanError("entry_too_large", "ZIP entry exceeds the PackScan limit", name)
                    if name in _CONTROL_ENTRIES | {"metadata/photos.json"} and info.file_size > MAX_PACKSCAN_CONTROL_ENTRY_BYTES:
                        raise PackScanError("control_entry_too_large", "PackScan control entry exceeds its limit", name)
                    declared_total += info.file_size
                    if declared_total > MAX_PACKSCAN_TOTAL_UNCOMPRESSED_BYTES:
                        raise PackScanError("package_expands_too_large", "uncompressed package exceeds the PackScan limit")
                    names.add(name)
                    folded.add(name.casefold())
                payloads: dict[str, bytes] = {}
                actual_total = 0
                for info in infos:
                    data = bytearray()
                    with archive.open(info, mode="r") as member:
                        while True:
                            remaining_entry = MAX_PACKSCAN_ENTRY_BYTES - len(data)
                            remaining_total = MAX_PACKSCAN_TOTAL_UNCOMPRESSED_BYTES - actual_total - len(data)
                            chunk = member.read(min(1024 * 1024, remaining_entry + 1, remaining_total + 1))
                            if not chunk:
                                break
                            if len(data) + len(chunk) > MAX_PACKSCAN_ENTRY_BYTES:
                                raise PackScanError("entry_too_large", "ZIP entry exceeds the PackScan limit", info.filename)
                            if actual_total + len(data) + len(chunk) > MAX_PACKSCAN_TOTAL_UNCOMPRESSED_BYTES:
                                raise PackScanError("package_expands_too_large", "uncompressed package exceeds the PackScan limit")
                            data.extend(chunk)
                        if len(data) != info.file_size:
                            raise PackScanError("corrupt_zip", "ZIP entry length differs from its central directory", info.filename)
                    actual_total += len(data)
                    payloads[info.filename] = bytes(data)
                return payloads
    except PackScanError:
        raise
    except (FileNotFoundError, IsADirectoryError) as error:
        raise PackScanError("package_unavailable", "package path cannot be opened") from error
    except NotImplementedError as error:
        raise PackScanError("unsupported_compression", "ZIP compression method is not supported") from error
    except (zipfile.BadZipFile, EOFError, RuntimeError, OSError, struct.error, zlib.error) as error:
        raise PackScanError("corrupt_zip", "ZIP structure or entry data is corrupt") from error


def _read_checksums(data: bytes) -> dict[str, str]:
    value = _read_json(data, "corrupt_checksums", "checksums.json")
    _validate_against_schema(value, "checksums.schema.json", "checksums.json", "invalid_checksums")
    if not isinstance(value, dict):
        raise PackScanError(
            "invalid_checksums", "checksum document must be an object", "checksums.json"
        )
    entries = value.get("entries")
    if not isinstance(entries, dict):
        raise PackScanError(
            "invalid_checksums", "checksum entries must be an object", "checksums.json"
        )
    normalized: dict[str, str] = {}
    for name, digest in entries.items():
        if not isinstance(name, str) or not isinstance(digest, str):
            raise PackScanError(
                "invalid_checksums", "checksum names and digests must be strings", "checksums.json"
            )
        _safe_entry_name(name)
        normalized[name] = digest
    return normalized


def validate_packscan(source: str | Path) -> PackScanReport:
    """Validate a PackScan ZIP and return payload bytes only after all checks pass."""

    package_path = Path(source)
    archive = _load_archive(package_path)
    missing_controls = _REQUIRED_ENTRIES - archive.keys()
    if missing_controls:
        raise PackScanError(
            "missing_entry", "required package entry is missing", sorted(missing_controls)[0]
        )
    manifest_value = _read_json(archive["manifest.json"], "corrupt_manifest", "manifest.json")
    manifest, declared = _validate_manifest(manifest_value)
    expected_names = _CONTROL_ENTRIES | set(declared)
    extras = set(archive) - expected_names
    if extras:
        raise PackScanError(
            "extra_entry", "archive contains an undeclared entry", sorted(extras)[0]
        )
    images = [name for name in archive if name.startswith("images/")]
    if not images:
        raise PackScanError(
            "missing_images", "at least one authoritative image is required", "images/"
        )
    checksums = _read_checksums(archive["checksums.json"])
    actual_checksum_names = set(archive) - {"checksums.json"}
    if set(checksums) != actual_checksum_names:
        raise PackScanError(
            "checksum_index_mismatch", "checksum index must cover every non-index entry"
        )
    for name in sorted(actual_checksum_names):
        actual = _sha256(archive[name])
        if checksums[name] != actual:
            raise PackScanError(
                "checksum_mismatch", "checksum index digest does not match bytes", name
            )
    payload_bytes: dict[str, bytes] = {}
    for path, item in declared.items():
        if path not in archive:
            raise PackScanError(
                "missing_declared_entry", "manifest-declared payload is absent", path
            )
        data = archive[path]
        expected_size = item["size_bytes"]
        if isinstance(expected_size, bool) or not isinstance(expected_size, (int, float)):
            raise PackScanError("schema_invalid", "payload size must be numeric", path)
        if len(data) != expected_size:
            code = "truncated_entry" if len(data) < expected_size else "payload_size_mismatch"
            raise PackScanError(code, "payload byte length differs from manifest", path)
        if _sha256(data) != item["sha256"]:
            code = (
                "checksum_mismatch_authoritative"
                if item["authority"] == "source"
                else "checksum_mismatch_derived"
            )
            raise PackScanError(code, "manifest SHA-256 does not match payload bytes", path)
        payload_bytes[path] = data
    return PackScanReport(package_path, manifest, checksums, payload_bytes)


def read_packscan(source: str | Path) -> PackScanReport:
    """Read a package after fail-closed validation."""

    return validate_packscan(source)


def write_packscan(
    destination: str | Path, manifest: Mapping[str, object], payloads: Mapping[str, bytes]
) -> Path:
    """Write one deterministic PackScan ZIP from already-declared payload bytes."""

    manifest_copy = json.loads(json.dumps(dict(manifest)))
    _, declared = _validate_manifest(manifest_copy)
    supplied = set(payloads)
    if supplied != set(declared):
        missing = set(declared) - supplied
        extra = supplied - set(declared)
        raise PackScanError(
            "payload_set_mismatch", f"missing={sorted(missing)} extra={sorted(extra)}"
        )
    files: dict[str, bytes] = {"manifest.json": _canonical_json(manifest_copy)}
    for path, item in declared.items():
        data = payloads[path]
        if not isinstance(data, bytes):
            raise PackScanError("invalid_payload", "payload values must be bytes", path)
        if len(data) != item["size_bytes"] or _sha256(data) != item["sha256"]:
            raise PackScanError(
                "payload_metadata_mismatch", "manifest size or SHA-256 does not match bytes", path
            )
        files[path] = data
    checksum_entries = {name: _sha256(data) for name, data in files.items()}
    checksums = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": "sha256",
        "canonicalization": CANONICALIZATION,
        "entries": checksum_entries,
    }
    files["checksums.json"] = _canonical_json(checksums)
    if len(files) > MAX_PACKSCAN_ENTRIES:
        raise PackScanError("too_many_entries", "package entry count exceeds the PackScan limit")
    if any(len(data) > MAX_PACKSCAN_ENTRY_BYTES for data in files.values()):
        raise PackScanError("entry_too_large", "package entry exceeds the PackScan limit")
    control_names = _CONTROL_ENTRIES | {"metadata/photos.json"}
    if any(len(files[name]) > MAX_PACKSCAN_CONTROL_ENTRY_BYTES for name in control_names):
        raise PackScanError("control_entry_too_large", "PackScan control entry exceeds its limit")
    if sum(len(data) for data in files.values()) > MAX_PACKSCAN_TOTAL_UNCOMPRESSED_BYTES:
        raise PackScanError("package_expands_too_large", "package contents exceed the PackScan limit")
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".packscan-", suffix=".tmp", dir=output.parent, delete=False
        ) as temp_file:
            temp_name = temp_file.name
        with zipfile.ZipFile(
            temp_name, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            order = ["manifest.json", "metadata/photos.json", "checksums.json"]
            order += sorted(name for name in files if name not in order)
            for name in order:
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 0
                archive.writestr(
                    info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
                )
        if Path(temp_name).stat().st_size > MAX_PACKSCAN_BYTES:
            raise PackScanError("package_too_large", "compressed package exceeds the PackScan limit")
        os.replace(temp_name, output)
        temp_name = None
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)
    return output


def extract_packscan(source: str | Path, destination: str | Path) -> Path:
    """Validate, extract through a private temporary directory, then publish atomically."""

    report = validate_packscan(source)
    files = _load_archive(report.source)
    if set(files) - {"checksums.json"} != set(report.checksums):
        raise PackScanError("package_changed", "package entries changed between validation and extraction")
    if _read_checksums(files["checksums.json"]) != report.checksums:
        raise PackScanError("package_changed", "package checksums changed between validation and extraction")
    for name, data in files.items():
        if name == "checksums.json":
            continue
        if _sha256(data) != report.checksums.get(name):
            raise PackScanError("package_changed", "package bytes changed between validation and extraction", name)
    current_manifest = _read_json(files["manifest.json"], "corrupt_manifest", "manifest.json")
    if current_manifest != report.manifest:
        raise PackScanError("package_changed", "package manifest changed between validation and extraction")
    target = Path(destination)
    if target.exists():
        raise PackScanError("destination_exists", "refusing to overwrite an extraction destination")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_directory = Path(tempfile.mkdtemp(prefix=".packscan-extract-", dir=target.parent))
    temporary: Path | None = temporary_directory
    try:
        for name, data in sorted(files.items()):
            safe_name = _safe_entry_name(name)
            output = temporary_directory.joinpath(*safe_name.split("/"))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
        os.replace(temporary_directory, target)
        temporary = None
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)
    return target
