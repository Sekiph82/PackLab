"""Fail-closed checks used by the one-time PL-0352 private retention bridge."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SOURCE_RUN_ID = 38649528145
SOURCE_ARTIFACT_ID = 11935390977
SOURCE_REPOSITORY_ID = 1359515156
SOURCE_REVISION = "452fe8934b0d56011af8c117555dd059d5c63462"
SOURCE_ARTIFACT_NAME = f"packlab-windows-installer-{SOURCE_REVISION}"
SOURCE_ARCHIVE_BYTES = 877253435
SOURCE_ARCHIVE_SHA256 = "3e9762e4d3faf6d0363f9714bfbdcb0d0b2d9dc9e73769ebfaac757c9af23e15"
INSTALLER_BYTES = 877598790
INSTALLER_SHA256 = "3e7c13c18674fbe0a4de843a2ac329055850d07901a7e33fac8a3dc742d92da6"
RETAINED_ARTIFACT_NAME = f"packlab-internal-installer-candidate-pl0350-warm-{SOURCE_REVISION}"
RETAINED_DAYS = 60
ACTIVE_ARTIFACT_STORAGE_CAP_BYTES = 5_000_000_000
INSTALLER_BASENAME = f"PackLabStudio-0.1.0-{SOURCE_REVISION}-unsigned-setup.exe"


class RetentionBridgeError(ValueError):
    """Raised when source identity, repository scope, or storage bounds fail."""


def validate_source_artifact(
    artifact: dict[str, Any], *, repository_private: bool, ref: str, now: datetime
) -> None:
    if repository_private is not True:
        raise RetentionBridgeError("public_repository_scope")
    if ref != "refs/heads/main":
        raise RetentionBridgeError("wrong_source_scope")
    if artifact.get("id") != SOURCE_ARTIFACT_ID:
        raise RetentionBridgeError("wrong_artifact_id")
    if artifact.get("name") != SOURCE_ARTIFACT_NAME:
        raise RetentionBridgeError("wrong_artifact_name")
    if artifact.get("expired") is not False:
        raise RetentionBridgeError("expired_artifact")
    if artifact.get("size_in_bytes") != SOURCE_ARCHIVE_BYTES:
        raise RetentionBridgeError("wrong_archive_size")
    if artifact.get("digest") != f"sha256:{SOURCE_ARCHIVE_SHA256}":
        raise RetentionBridgeError("wrong_archive_digest")
    expires_at = artifact.get("expires_at")
    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise RetentionBridgeError("invalid_expiry") from exc
    if expiry <= now.astimezone(UTC):
        raise RetentionBridgeError("expired_artifact")
    run = artifact.get("workflow_run") or {}
    if (
        run.get("id") != SOURCE_RUN_ID
        or run.get("head_sha") != SOURCE_REVISION
        or run.get("head_branch") != "main"
        or run.get("repository_id") != SOURCE_REPOSITORY_ID
        or run.get("head_repository_id") != SOURCE_REPOSITORY_ID
    ):
        raise RetentionBridgeError("wrong_producer_scope")


def validate_storage_and_uniqueness(
    artifacts: list[dict[str, Any]], *, projected_bytes: int
) -> None:
    if projected_bytes <= 0 or projected_bytes > 1_000_000_000:
        raise RetentionBridgeError("candidate_storage_cap")
    live = [item for item in artifacts if item.get("expired") is False]
    if any(item.get("name") == RETAINED_ARTIFACT_NAME for item in live):
        raise RetentionBridgeError("duplicate_retained_artifact")
    current_bytes = sum(int(item.get("size_in_bytes", 0)) for item in live)
    if current_bytes + projected_bytes > ACTIVE_ARTIFACT_STORAGE_CAP_BYTES:
        raise RetentionBridgeError("repository_storage_cap")


def validate_bundle_evidence(bundle: dict[str, Any]) -> None:
    if bundle.get("installer_name") != INSTALLER_BASENAME:
        raise RetentionBridgeError("wrong_installer_scope")
    if bundle.get("installer_bytes") != INSTALLER_BYTES:
        raise RetentionBridgeError("wrong_installer_size")
    if bundle.get("installer_sha256") != INSTALLER_SHA256:
        raise RetentionBridgeError("wrong_installer_hash")
    if bundle.get("legal_review_required") is not True:
        raise RetentionBridgeError("legal_boundary_missing")
    notices = bundle.get("notice_evidence")
    if not isinstance(notices, list) or not notices or any(not item for item in notices):
        raise RetentionBridgeError("missing_notice_evidence")
    if bundle.get("approved_for_reupload") is not True:
        raise RetentionBridgeError("unapproved_reupload")


def validate_installer_evidence(
    installer_path: Path, metadata: dict[str, Any], installed_smoke: dict[str, Any]
) -> None:
    import hashlib

    with installer_path.open("rb") as installer_file:
        digest = hashlib.file_digest(installer_file, "sha256").hexdigest()
    if installer_path.stat().st_size != INSTALLER_BYTES or digest != INSTALLER_SHA256:
        raise RetentionBridgeError("wrong_installer_hash_or_size")
    if (
        metadata.get("sha256") != INSTALLER_SHA256
        or metadata.get("byte_length") != INSTALLER_BYTES
        or metadata.get("build_revision") != SOURCE_REVISION
        or metadata.get("signing") != "unsigned"
    ):
        raise RetentionBridgeError("installer_metadata_mismatch")
    if (
        installed_smoke.get("installer_sha256") != INSTALLER_SHA256
        or installed_smoke.get("build_revision") != SOURCE_REVISION
        or not isinstance(installed_smoke.get("installed_executable_sha256"), str)
        or len(installed_smoke["installed_executable_sha256"]) != 64
    ):
        raise RetentionBridgeError("installed_smoke_evidence_mismatch")
