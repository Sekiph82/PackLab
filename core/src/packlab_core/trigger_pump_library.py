"""Verified local-only import contract for reusable trigger/pump design references."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import cast

_MANIFEST_CONTRACT = "packlab.trigger-pump-library-component.v1"
_GEOMETRY_CONTRACT = "packlab.trigger-pump-geometry-reference.v1"
_AUTHORITY = "LIBRARY_DESIGN_COMPONENT"
_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_MAX_MANIFEST_BYTES = 256 * 1024
_MAX_GEOMETRY_BYTES = 1024 * 1024
_MAX_LICENSE_EVIDENCE_BYTES = 256 * 1024
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_PATH_PARTS = frozenset(
    {"private", "raw", "scan", "scans", "owner", "supplier", "confidential", "capture"}
)


class TriggerPumpLibraryError(ValueError):
    """Raised when a local trigger/pump library asset is unsafe or incomplete."""


@dataclass(frozen=True, slots=True)
class ImportedTriggerPumpComponent:
    """Immutable metadata and bounded parameters from one locally verified JSON asset."""

    import_id: str
    component_id: str
    component_version: str
    source_kind: str
    source_reference: str
    provenance_id: str
    license_identifier: str
    license_reviewed_by: str
    license_evidence_sha256: str
    geometry_contract: str
    geometry_asset_sha256: str
    geometry_asset_path: str
    coordinate_unit: str
    geometry_parameters: tuple[tuple[str, float], ...]
    attachment_role: str
    attachment_semantic_key: str

    def __post_init__(self) -> None:
        for field, value in (
            ("import_id", self.import_id),
            ("component_id", self.component_id),
            ("provenance_id", self.provenance_id),
            ("attachment_role", self.attachment_role),
            ("attachment_semantic_key", self.attachment_semantic_key),
        ):
            _validate_identifier(value, field)
        if not _VERSION.fullmatch(self.component_version):
            raise TriggerPumpLibraryError("component_version_invalid")
        if self.geometry_contract != _GEOMETRY_CONTRACT:
            raise TriggerPumpLibraryError("geometry_contract_unsupported")
        if not _SHA256.fullmatch(self.license_evidence_sha256) or not _SHA256.fullmatch(
            self.geometry_asset_sha256
        ):
            raise TriggerPumpLibraryError("library_integrity_digest_invalid")
        if self.coordinate_unit not in {"mm_unverified", "reconstruction_units"}:
            raise TriggerPumpLibraryError("library_coordinate_unit_invalid")
        if not self.geometry_parameters or any(
            not _ID.fullmatch(name) or not math.isfinite(value) or value <= 0.0
            for name, value in self.geometry_parameters
        ):
            raise TriggerPumpLibraryError("library_geometry_parameters_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.imported-trigger-pump-component.v1",
            "import_id": self.import_id,
            "component_id": self.component_id,
            "component_version": self.component_version,
            "source": {
                "kind": self.source_kind,
                "reference": self.source_reference,
                "provenance_id": self.provenance_id,
            },
            "license": {
                "identifier": self.license_identifier,
                "reviewed_by": self.license_reviewed_by,
                "evidence_sha256": self.license_evidence_sha256,
            },
            "geometry": {
                "authority_class": _AUTHORITY,
                "contract": self.geometry_contract,
                "asset_path": self.geometry_asset_path,
                "asset_sha256": self.geometry_asset_sha256,
                "coordinate_unit": self.coordinate_unit,
                "parameters": dict(self.geometry_parameters),
                "attachment_reference": {
                    "role": self.attachment_role,
                    "semantic_key": self.attachment_semantic_key,
                },
            },
            "scan_master_revision_id": None,
            "physical_accuracy_validation_status": _DEFERRED,
            "mold_use_authorized": False,
            "downloaded": False,
            "network_accessed": False,
        }


def import_local_trigger_pump_component(
    library_root: Path, manifest_relative_path: str
) -> ImportedTriggerPumpComponent:
    """Read a verified local JSON reference asset; never fetch or accept binary geometry."""
    root = _root(library_root)
    manifest_path = _local_file(root, manifest_relative_path, "manifest", _MAX_MANIFEST_BYTES)
    manifest = _json_object(manifest_path, _MAX_MANIFEST_BYTES, "library_manifest")
    for required in ("source", "provenance", "license", "geometry_asset"):
        _object_field(manifest, required)
    _keys(
        manifest,
        {
            "contract",
            "component_id",
            "component_version",
            "source",
            "provenance",
            "license",
            "geometry_asset",
        },
        "library_manifest_fields_invalid",
    )
    if manifest.get("contract") != _MANIFEST_CONTRACT:
        raise TriggerPumpLibraryError("library_contract_unsupported")
    component_id = _required_id(manifest, "component_id")
    version = _required_string(manifest, "component_version")
    if not _VERSION.fullmatch(version):
        raise TriggerPumpLibraryError("component_version_invalid")

    source = _object_field(manifest, "source")
    _keys(source, {"kind", "reference"}, "library_source_fields_invalid")
    source_kind = _required_string(source, "kind")
    source_reference = _required_string(source, "reference")
    if source_kind not in {"packlab_authored", "public_reference", "third_party"}:
        raise TriggerPumpLibraryError("library_source_kind_invalid")
    _reject_private_text(source_reference, "library_source_reference_private_or_raw")

    provenance = _object_field(manifest, "provenance")
    _keys(provenance, {"provenance_id", "source_revision"}, "library_provenance_fields_invalid")
    provenance_id = _required_id(provenance, "provenance_id")
    source_revision = _required_string(provenance, "source_revision")
    _reject_private_text(source_revision, "library_provenance_source_private_or_raw")

    license_record = _object_field(manifest, "license")
    _keys(
        license_record,
        {
            "identifier",
            "review_status",
            "reviewed_by",
            "reviewed_at_utc",
            "evidence_path",
            "evidence_sha256",
        },
        "library_license_fields_invalid",
    )
    license_id = _required_string(license_record, "identifier")
    if not re.fullmatch(r"[A-Za-z0-9.+-]{1,80}", license_id):
        raise TriggerPumpLibraryError("library_license_identifier_invalid")
    if _required_string(license_record, "review_status") != "reviewed":
        raise TriggerPumpLibraryError("library_license_not_reviewed")
    reviewed_by = _required_string(license_record, "reviewed_by")
    _required_timestamp(license_record, "reviewed_at_utc")
    license_path_value = _required_string(license_record, "evidence_path")
    license_path = _local_file(root, license_path_value, "license", _MAX_LICENSE_EVIDENCE_BYTES)
    license_digest = _required_digest(license_record, "evidence_sha256")
    if _sha256_file(license_path) != license_digest:
        raise TriggerPumpLibraryError("library_license_evidence_digest_mismatch")

    asset = _object_field(manifest, "geometry_asset")
    _keys(asset, {"path", "format", "sha256"}, "library_geometry_asset_fields_invalid")
    asset_path_value = _required_string(asset, "path")
    if _required_string(asset, "format") != "json":
        raise TriggerPumpLibraryError("library_geometry_format_unsupported")
    asset_path = _local_file(root, asset_path_value, "geometry", _MAX_GEOMETRY_BYTES)
    asset_digest = _required_digest(asset, "sha256")
    if _sha256_file(asset_path) != asset_digest:
        raise TriggerPumpLibraryError("library_geometry_digest_mismatch")

    geometry = _json_object(asset_path, _MAX_GEOMETRY_BYTES, "library_geometry")
    _keys(
        geometry,
        {
            "contract",
            "authority_class",
            "component_id",
            "coordinate_unit",
            "parameters",
            "attachment_reference",
        },
        "library_geometry_fields_invalid",
    )
    if geometry.get("contract") != _GEOMETRY_CONTRACT:
        raise TriggerPumpLibraryError("geometry_contract_unsupported")
    if geometry.get("authority_class") != _AUTHORITY:
        raise TriggerPumpLibraryError("library_geometry_authority_invalid")
    if geometry.get("component_id") != component_id:
        raise TriggerPumpLibraryError("library_geometry_component_mismatch")
    unit = _required_string(geometry, "coordinate_unit")
    if unit not in {"mm_unverified", "reconstruction_units"}:
        raise TriggerPumpLibraryError("library_coordinate_unit_invalid")
    parameters = _object_field(geometry, "parameters")
    if not parameters or len(parameters) > 32:
        raise TriggerPumpLibraryError("library_geometry_parameters_invalid")
    normalized_parameters: list[tuple[str, float]] = []
    for name, value in sorted(parameters.items()):
        if (
            not isinstance(name, str)
            or not _ID.fullmatch(name)
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0.0
        ):
            raise TriggerPumpLibraryError("library_geometry_parameters_invalid")
        normalized_parameters.append((name, float(value)))
    attachment = _object_field(geometry, "attachment_reference")
    _keys(attachment, {"role", "semantic_key"}, "library_attachment_reference_invalid")

    identity = {
        "contract": _MANIFEST_CONTRACT,
        "component_id": component_id,
        "component_version": version,
        "source_kind": source_kind,
        "source_reference": source_reference,
        "provenance_id": provenance_id,
        "license_identifier": license_id,
        "license_evidence_sha256": license_digest,
        "geometry_asset_sha256": asset_digest,
        "coordinate_unit": unit,
        "parameters": normalized_parameters,
        "attachment": attachment,
    }
    import_id = (
        "trigger-pump-library:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
    )
    return ImportedTriggerPumpComponent(
        import_id,
        component_id,
        version,
        source_kind,
        source_reference,
        provenance_id,
        license_id,
        reviewed_by,
        license_digest,
        _GEOMETRY_CONTRACT,
        asset_digest,
        asset_path.relative_to(root).as_posix(),
        unit,
        tuple(normalized_parameters),
        _required_string(attachment, "role"),
        _required_id(attachment, "semantic_key"),
    )


def _root(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TriggerPumpLibraryError("library_root_must_be_local_path")
    try:
        root = path.resolve(strict=True)
    except OSError as error:
        raise TriggerPumpLibraryError("library_root_missing") from error
    if not root.is_dir():
        raise TriggerPumpLibraryError("library_root_not_directory")
    return root


def _local_file(root: Path, value: str, field: str, maximum_bytes: int) -> Path:
    _reject_private_text(value, f"library_{field}_path_private_or_raw")
    windows_path = PureWindowsPath(value)
    posix_path = PurePosixPath(value)
    if (
        not value
        or windows_path.is_absolute()
        or posix_path.is_absolute()
        or windows_path.drive
        or "\\" in value
        or value.startswith("//")
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value)
        or ".." in posix_path.parts
        or "." in posix_path.parts
    ):
        raise TriggerPumpLibraryError(f"library_{field}_path_invalid")
    candidate = root.joinpath(*posix_path.parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        size = resolved.stat().st_size
    except (OSError, ValueError) as error:
        raise TriggerPumpLibraryError(f"library_{field}_path_outside_or_missing") from error
    if not resolved.is_file():
        raise TriggerPumpLibraryError(f"library_{field}_not_file")
    if size > maximum_bytes:
        raise TriggerPumpLibraryError(f"library_{field}_file_too_large")
    return resolved


def _json_object(path: Path, maximum_bytes: int, field: str) -> dict[str, object]:
    try:
        if path.stat().st_size > maximum_bytes:
            raise TriggerPumpLibraryError(f"{field}_file_too_large")
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        if isinstance(error, TriggerPumpLibraryError):
            raise
        raise TriggerPumpLibraryError(f"{field}_json_invalid") from error
    if not isinstance(value, dict):
        raise TriggerPumpLibraryError(f"{field}_must_be_object")
    _reject_private_keys(value)
    return cast(dict[str, object], value)


def _reject_constant(value: str) -> None:
    raise ValueError(f"non_finite_json_constant:{value}")


def _reject_private_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(key, str) and any(
                marker in key.casefold() for marker in ("private", "raw_scan", "supplier_file")
            ):
                raise TriggerPumpLibraryError("library_private_or_raw_content_rejected")
            _reject_private_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_private_keys(nested)


def _reject_private_text(value: str, code: str) -> None:
    normalized = value.replace("\\", "/").casefold()
    markers = tuple(_PRIVATE_PATH_PARTS)
    if any(
        part in _PRIVATE_PATH_PARTS
        or re.search(
            rf"(?:^|[._-])(?:{'|'.join(re.escape(marker) for marker in markers)})(?:[._-]|$)",
            part,
        )
        for part in PurePosixPath(normalized).parts
    ):
        raise TriggerPumpLibraryError(code)


def _keys(value: dict[str, object], expected: set[str], code: str) -> None:
    if set(value) != expected:
        raise TriggerPumpLibraryError(code)


def _object_field(value: dict[str, object], key: str) -> dict[str, object]:
    nested = value.get(key)
    if not isinstance(nested, dict):
        raise TriggerPumpLibraryError(f"library_{key}_must_be_object")
    return cast(dict[str, object], nested)


def _required_string(value: dict[str, object], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip() or result.strip() != result:
        raise TriggerPumpLibraryError(f"library_{key}_required")
    return result


def _required_id(value: dict[str, object], key: str) -> str:
    result = _required_string(value, key)
    _validate_identifier(result, key)
    return result


def _validate_identifier(value: str, field: str) -> None:
    if not _ID.fullmatch(value):
        raise TriggerPumpLibraryError(f"library_{field}_invalid")


def _required_digest(value: dict[str, object], key: str) -> str:
    result = _required_string(value, key)
    if not _SHA256.fullmatch(result):
        raise TriggerPumpLibraryError(f"library_{key}_invalid")
    return result


def _required_timestamp(value: dict[str, object], key: str) -> None:
    timestamp = _required_string(value, key)
    if not timestamp.endswith("Z"):
        raise TriggerPumpLibraryError("library_review_timestamp_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(timestamp[:-1] + "+00:00")
    except ValueError as error:
        raise TriggerPumpLibraryError("library_review_timestamp_invalid") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise TriggerPumpLibraryError("library_review_timestamp_must_be_utc_z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


__all__ = [
    "ImportedTriggerPumpComponent",
    "TriggerPumpLibraryError",
    "import_local_trigger_pump_component",
]
