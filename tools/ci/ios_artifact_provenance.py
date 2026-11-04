"""Create and verify secret-free provenance sidecars for iOS build artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

FORMAT = "packlab-ios-artifact-provenance-v1"
TREE_ALGORITHM = "packlab-sorted-path-length-content-sha256-v1"
ARTIFACT_STATES = {
    "ios_simulator_app": "UNSIGNED",
    "ios_device_archive": "UNSIGNED",
}
METADATA_FIELDS = (
    "artifact_type",
    "signing_state",
    "product_name",
    "capture_version",
    "capture_build",
    "packscan_schema_version",
    "source_commit",
    "xcode_version",
    "xcode_build",
    "sdk_name",
    "sdk_version",
    "bundle_identifier",
    "package_resolved_sha256",
    "repository",
    "workflow_name",
    "workflow_run_id",
    "workflow_run_number",
    "workflow_run_attempt",
    "event_name",
)
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
BUNDLE_ID_RE = re.compile(r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\Z")
PRODUCT_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._ -]{0,127}\Z")
SAFE_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class ProvenanceError(ValueError):
    """A fail-closed, value-redacted provenance validation error."""


def _artifact_inventory(artifact: Path) -> tuple[str, int, int]:
    supplied = artifact
    if supplied.is_symlink() or getattr(supplied, "is_junction", lambda: False)():
        raise ProvenanceError("ARTIFACT_ROOT_LINK_BLOCKED")
    try:
        root = supplied.resolve(strict=True)
    except OSError:
        raise ProvenanceError("ARTIFACT_ROOT_UNAVAILABLE") from None

    if root.is_file():
        files = [(root.name, root)]
    elif root.is_dir():
        files = []
        try:
            entries = sorted(
                root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")
            )
        except OSError:
            raise ProvenanceError("ARTIFACT_INVENTORY_FAILED") from None
        for item in entries:
            if item.is_symlink() or getattr(item, "is_junction", lambda: False)():
                raise ProvenanceError("ARTIFACT_LINK_BLOCKED")
            if item.is_dir():
                continue
            if not item.is_file():
                raise ProvenanceError("ARTIFACT_SPECIAL_FILE_BLOCKED")
            relative = item.relative_to(root).as_posix()
            if PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
                raise ProvenanceError("ARTIFACT_RELATIVE_PATH_INVALID")
            files.append((relative, item))
    else:
        raise ProvenanceError("ARTIFACT_ROOT_NOT_FILE_OR_DIRECTORY")

    if not files:
        raise ProvenanceError("ARTIFACT_EMPTY")

    digest = hashlib.sha256()
    digest.update(TREE_ALGORITHM.encode("ascii") + b"\0")
    total_bytes = 0
    for relative, file_path in files:
        path_bytes = relative.encode("utf-8")
        try:
            expected_size = file_path.stat().st_size
            with file_path.open("rb") as stream:
                digest.update(len(path_bytes).to_bytes(4, "big"))
                digest.update(path_bytes)
                digest.update(expected_size.to_bytes(8, "big"))
                observed_size = 0
                while chunk := stream.read(1024 * 1024):
                    observed_size += len(chunk)
                    digest.update(chunk)
        except OSError:
            raise ProvenanceError("ARTIFACT_READ_FAILED") from None
        if observed_size != expected_size:
            raise ProvenanceError("ARTIFACT_CHANGED_DURING_HASH")
        total_bytes += observed_size
    return digest.hexdigest(), total_bytes, len(files)


def _validate_metadata(metadata: dict[str, Any]) -> None:
    if set(metadata) != set(METADATA_FIELDS):
        raise ProvenanceError("PROVENANCE_METADATA_FIELDS_INVALID")
    artifact_type = metadata.get("artifact_type")
    if artifact_type not in ARTIFACT_STATES:
        raise ProvenanceError("PROVENANCE_ARTIFACT_TYPE_INVALID")
    if metadata.get("signing_state") != ARTIFACT_STATES[artifact_type]:
        raise ProvenanceError("PROVENANCE_SIGNING_STATE_INVALID")
    if not isinstance(metadata.get("product_name"), str) or not PRODUCT_NAME_RE.fullmatch(
        metadata["product_name"]
    ):
        raise ProvenanceError("PROVENANCE_PRODUCT_NAME_INVALID")
    for field in ("capture_version", "packscan_schema_version"):
        if not isinstance(metadata.get(field), str) or not VERSION_RE.fullmatch(metadata[field]):
            raise ProvenanceError("PROVENANCE_VERSION_INVALID")
    if not isinstance(metadata.get("capture_build"), str) or not SAFE_TOKEN_RE.fullmatch(
        metadata["capture_build"]
    ):
        raise ProvenanceError("PROVENANCE_CAPTURE_BUILD_INVALID")
    if not isinstance(metadata.get("source_commit"), str) or not re.fullmatch(
        r"[0-9a-f]{40}", metadata["source_commit"]
    ):
        raise ProvenanceError("PROVENANCE_SOURCE_COMMIT_INVALID")
    for field in ("xcode_version", "xcode_build", "sdk_version", "sdk_name", "event_name"):
        if not isinstance(metadata.get(field), str) or not SAFE_TOKEN_RE.fullmatch(metadata[field]):
            raise ProvenanceError("PROVENANCE_TOOLCHAIN_FIELD_INVALID")
    if metadata.get("sdk_name") not in {"iphoneos", "iphonesimulator"}:
        raise ProvenanceError("PROVENANCE_SDK_NAME_INVALID")
    if not isinstance(metadata.get("bundle_identifier"), str) or not BUNDLE_ID_RE.fullmatch(
        metadata["bundle_identifier"]
    ):
        raise ProvenanceError("PROVENANCE_BUNDLE_IDENTIFIER_INVALID")
    if not isinstance(metadata.get("package_resolved_sha256"), str) or not SHA256_RE.fullmatch(
        metadata["package_resolved_sha256"]
    ):
        raise ProvenanceError("PROVENANCE_PACKAGE_LOCK_DIGEST_INVALID")
    if not isinstance(metadata.get("repository"), str) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", metadata["repository"]
    ):
        raise ProvenanceError("PROVENANCE_REPOSITORY_INVALID")
    if not isinstance(metadata.get("workflow_name"), str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,127}", metadata["workflow_name"]
    ):
        raise ProvenanceError("PROVENANCE_WORKFLOW_INVALID")
    for field in ("workflow_run_id", "workflow_run_number", "workflow_run_attempt"):
        value = metadata.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ProvenanceError("PROVENANCE_WORKFLOW_RUN_INVALID")


def build_manifest(artifact: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    _validate_metadata(metadata)
    digest, byte_length, file_count = _artifact_inventory(artifact)
    manifest: dict[str, Any] = {
        "format": FORMAT,
        **metadata,
        "artifact_tree_algorithm": TREE_ALGORITHM,
        "artifact_sha256": digest,
        "artifact_byte_length": byte_length,
        "artifact_file_count": file_count,
    }
    return manifest


def verify_manifest(artifact: Path, provenance: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(provenance.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ProvenanceError("PROVENANCE_SIDECAR_UNREADABLE") from None
    if not isinstance(manifest, dict) or manifest.get("format") != FORMAT:
        raise ProvenanceError("PROVENANCE_FORMAT_INVALID")
    metadata = {field: manifest.get(field) for field in METADATA_FIELDS}
    _validate_metadata(metadata)
    if set(manifest) != {
        "format",
        *METADATA_FIELDS,
        "artifact_tree_algorithm",
        "artifact_sha256",
        "artifact_byte_length",
        "artifact_file_count",
    }:
        raise ProvenanceError("PROVENANCE_SIDECAR_FIELDS_INVALID")
    if manifest.get("artifact_tree_algorithm") != TREE_ALGORITHM:
        raise ProvenanceError("PROVENANCE_TREE_ALGORITHM_INVALID")
    if not isinstance(manifest.get("artifact_sha256"), str) or not SHA256_RE.fullmatch(
        manifest["artifact_sha256"]
    ):
        raise ProvenanceError("PROVENANCE_ARTIFACT_DIGEST_INVALID")
    for field in ("artifact_byte_length", "artifact_file_count"):
        value = manifest.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ProvenanceError("PROVENANCE_ARTIFACT_SIZE_INVALID")
    digest, byte_length, file_count = _artifact_inventory(artifact)
    if digest != manifest["artifact_sha256"]:
        raise ProvenanceError("PROVENANCE_ARTIFACT_DIGEST_MISMATCH")
    if byte_length != manifest.get("artifact_byte_length"):
        raise ProvenanceError("PROVENANCE_ARTIFACT_LENGTH_MISMATCH")
    if file_count != manifest.get("artifact_file_count"):
        raise ProvenanceError("PROVENANCE_ARTIFACT_INVENTORY_MISMATCH")
    return manifest


def _metadata_from_environment() -> dict[str, Any]:
    string_fields = {
        "artifact_type": "PACKLAB_ARTIFACT_TYPE",
        "signing_state": "PACKLAB_SIGNING_STATE",
        "product_name": "PACKLAB_PRODUCT_NAME",
        "capture_version": "PACKLAB_CAPTURE_VERSION",
        "capture_build": "PACKLAB_CAPTURE_BUILD",
        "packscan_schema_version": "PACKLAB_PACKSCAN_SCHEMA_VERSION",
        "source_commit": "GITHUB_SHA",
        "xcode_version": "PACKLAB_XCODE_VERSION",
        "xcode_build": "PACKLAB_XCODE_BUILD",
        "sdk_name": "PACKLAB_SDK_NAME",
        "sdk_version": "PACKLAB_SDK_VERSION",
        "bundle_identifier": "PACKLAB_BUNDLE_IDENTIFIER",
        "package_resolved_sha256": "PACKLAB_PACKAGE_RESOLVED_SHA256",
        "repository": "GITHUB_REPOSITORY",
        "workflow_name": "GITHUB_WORKFLOW",
        "event_name": "GITHUB_EVENT_NAME",
    }
    metadata: dict[str, Any] = {}
    for field, variable in string_fields.items():
        value = os.environ.get(variable, "")
        if not value:
            raise ProvenanceError("PROVENANCE_REQUIRED_ENVIRONMENT_MISSING")
        metadata[field] = value
    integer_fields = {
        "workflow_run_id": "GITHUB_RUN_ID",
        "workflow_run_number": "GITHUB_RUN_NUMBER",
        "workflow_run_attempt": "GITHUB_RUN_ATTEMPT",
    }
    for field, variable in integer_fields.items():
        try:
            metadata[field] = int(os.environ[variable])
        except (KeyError, ValueError):
            raise ProvenanceError("PROVENANCE_WORKFLOW_RUN_INVALID") from None
    return metadata


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--artifact", type=Path, required=True)
    prepare.add_argument("--sidecar", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--artifact", type=Path, required=True)
    verify.add_argument("--sidecar", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            manifest = build_manifest(args.artifact, _metadata_from_environment())
            args.sidecar.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.sidecar.with_suffix(args.sidecar.suffix + ".tmp")
            temporary.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, args.sidecar)
        else:
            manifest = verify_manifest(args.artifact, args.sidecar)
    except (OSError, ProvenanceError):
        print("PACKLAB_IOS_ARTIFACT_PROVENANCE=BLOCK code=VALIDATION_FAILED")
        return 1
    print(
        "PACKLAB_IOS_ARTIFACT_PROVENANCE=PASS "
        f"type={manifest['artifact_type']} signing={manifest['signing_state']} "
        f"sha256={manifest['artifact_sha256']} bytes={manifest['artifact_byte_length']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
