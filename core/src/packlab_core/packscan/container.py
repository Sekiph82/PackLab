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
import tempfile
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

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
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
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
    repo_root = Path(__file__).resolve().parents[4]
    schema_dir = repo_root / "schemas" / "packscan"
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
    return manifest, by_path


def _version_error_code(version: object) -> str:
    if not isinstance(version, str):
        return "unsupported_version"
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    return (
        "unsupported_future_version"
        if match and tuple(int(part) for part in match.groups()) > (1, 0, 0)
        else "unsupported_version"
    )


def _load_archive(path: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(path, mode="r") as archive:
            infos = archive.infolist()
            names: set[str] = set()
            folded: set[str] = set()
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
                names.add(name)
                folded.add(name.casefold())
            try:
                return {name: archive.read(name) for name in names}
            except (KeyError, RuntimeError, zipfile.BadZipFile):
                raise
    except PackScanError:
        raise
    except (FileNotFoundError, IsADirectoryError) as error:
        raise PackScanError("package_unavailable", "package path cannot be opened") from error
    except (zipfile.BadZipFile, EOFError, RuntimeError, OSError) as error:
        raise PackScanError("corrupt_zip", "ZIP structure or entry data is corrupt") from error


def _read_checksums(data: bytes) -> dict[str, str]:
    value = _read_json(data, "corrupt_checksums", "checksums.json")
    _validate_against_schema(value, "checksums.schema.json", "checksums.json", "invalid_checksums")
    entries = value.get("entries")
    for name, digest in entries.items():
        _safe_entry_name(name)
    return dict(entries)


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
        os.replace(temp_name, output)
        temp_name = None
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)
    return output


def extract_packscan(source: str | Path, destination: str | Path) -> Path:
    """Validate, extract through a private temporary directory, then publish atomically."""

    report = validate_packscan(source)
    target = Path(destination)
    if target.exists():
        raise PackScanError("destination_exists", "refusing to overwrite an extraction destination")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = tempfile.mkdtemp(prefix=".packscan-extract-", dir=target.parent)
    try:
        with zipfile.ZipFile(report.source, mode="r") as archive:
            for name in sorted(archive.namelist()):
                safe_name = _safe_entry_name(name)
                output = Path(temporary, *safe_name.split("/"))
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(archive.read(name))
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)
    return target
