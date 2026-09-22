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
from pathlib import Path

CANONICALIZATION = "sha256_32_bytes_lowercase_hex_64_chars_v1"
SCHEMA_VERSION = "1.0.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
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


def _validate_manifest(manifest: object) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    if not isinstance(manifest, dict):
        raise PackScanError("invalid_manifest", "manifest must be a JSON object", "manifest.json")
    version = manifest.get("schema_version")
    if version != SCHEMA_VERSION:
        code = (
            "unsupported_future_version"
            if isinstance(version, str) and version > SCHEMA_VERSION
            else "unsupported_version"
        )
        raise PackScanError(code, f"expected schema version {SCHEMA_VERSION}", "manifest.json")
    for field in (
        "capture_id",
        "created_at",
        "device",
        "capture_mode",
        "payloads",
        "source_evidence",
        "checksums",
    ):
        if field not in manifest:
            raise PackScanError(
                "invalid_manifest", f"missing required field {field}", "manifest.json"
            )
    payloads = manifest["payloads"]
    if not isinstance(payloads, list) or not payloads:
        raise PackScanError(
            "invalid_manifest", "payloads must be a non-empty array", "manifest.json"
        )
    by_path: dict[str, dict[str, object]] = {}
    folded: set[str] = set()
    for item in payloads:
        if not isinstance(item, dict):
            raise PackScanError(
                "invalid_manifest", "each payload must be an object", "manifest.json"
            )
        for field in ("path", "kind", "required", "authority", "size_bytes", "sha256"):
            if field not in item:
                raise PackScanError("invalid_manifest", f"payload missing {field}", "manifest.json")
        path = _safe_entry_name(item["path"])
        if path in _CONTROL_ENTRIES:
            raise PackScanError("invalid_manifest", "control entries cannot be payloads", path)
        if path.casefold() in folded:
            raise PackScanError(
                "duplicate_payload", "case-insensitive payload paths are ambiguous", path
            )
        folded.add(path.casefold())
        if path in by_path:
            raise PackScanError(
                "duplicate_payload", "payload path is declared more than once", path
            )
        if not isinstance(item["required"], bool) or item["authority"] not in {"source", "derived"}:
            raise PackScanError(
                "invalid_manifest", "payload required/authority values are invalid", path
            )
        if not isinstance(item["size_bytes"], int) or item["size_bytes"] < 0:
            raise PackScanError(
                "invalid_manifest", "payload size_bytes must be a non-negative integer", path
            )
        digest = item["sha256"]
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise PackScanError(
                "invalid_checksum", "payload SHA-256 must be 64 lowercase hex characters", path
            )
        kind = item["kind"]
        if kind in {"preview", "thumbnail"} and (
            item["authority"] != "derived"
            or item["required"]
            or not path.startswith(("previews/", "thumbnails/"))
        ):
            raise PackScanError(
                "invalid_manifest",
                "preview/thumbnail declarations are optional derived payloads",
                path,
            )
        if kind == "diagnostics" and (
            item["authority"] != "derived"
            or item["required"]
            or not path.startswith("diagnostics/")
        ):
            raise PackScanError(
                "invalid_manifest", "diagnostics declarations are optional derived payloads", path
            )
        by_path[path] = item
    return manifest, by_path


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
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != SCHEMA_VERSION
        or value.get("algorithm") != "sha256"
        or value.get("canonicalization") != CANONICALIZATION
    ):
        raise PackScanError(
            "invalid_checksums", "checksum index header is invalid", "checksums.json"
        )
    entries = value.get("entries")
    if not isinstance(entries, dict) or not all(
        isinstance(key, str) and isinstance(digest, str) for key, digest in entries.items()
    ):
        raise PackScanError(
            "invalid_checksums", "checksum entries must map paths to strings", "checksums.json"
        )
    for name, digest in entries.items():
        _safe_entry_name(name)
        if not _SHA256_RE.fullmatch(digest):
            raise PackScanError(
                "invalid_checksum", "checksum index contains non-canonical SHA-256", name
            )
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
