from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from tools.packaging.pl0352_artifact_retention import (
    INSTALLER_BASENAME,
    INSTALLER_BYTES,
    INSTALLER_SHA256,
    RETAINED_ARTIFACT_NAME,
    SOURCE_ARCHIVE_BYTES,
    SOURCE_ARCHIVE_SHA256,
    SOURCE_ARTIFACT_ID,
    SOURCE_ARTIFACT_NAME,
    SOURCE_REPOSITORY_ID,
    SOURCE_REVISION,
    SOURCE_RUN_ID,
    RetentionBridgeError,
    validate_bundle_evidence,
    validate_source_artifact,
    validate_storage_and_uniqueness,
)

ROOT = Path(__file__).resolve().parents[2]


def source_artifact() -> dict:
    return {
        "id": SOURCE_ARTIFACT_ID,
        "name": SOURCE_ARTIFACT_NAME,
        "size_in_bytes": SOURCE_ARCHIVE_BYTES,
        "digest": f"sha256:{SOURCE_ARCHIVE_SHA256}",
        "expired": False,
        "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        "workflow_run": {
            "id": SOURCE_RUN_ID,
            "head_sha": SOURCE_REVISION,
            "head_branch": "main",
            "repository_id": SOURCE_REPOSITORY_ID,
            "head_repository_id": SOURCE_REPOSITORY_ID,
        },
    }


def bundle_evidence() -> dict:
    return {
        "installer_name": INSTALLER_BASENAME,
        "installer_bytes": INSTALLER_BYTES,
        "installer_sha256": INSTALLER_SHA256,
        "legal_review_required": True,
        "notice_evidence": ["PL-0350 report", "PL-0351 audit"],
        "approved_for_reupload": True,
    }


def test_pl0352_bridge_is_manual_private_main_only_and_bounded() -> None:
    workflow = (ROOT / ".github/workflows/pl0352-private-installer-retention.yml").read_text()
    policy = (ROOT / "docs/packaging/GITHUB_ACTIONS_ARTIFACT_RETENTION_POLICY.md").read_text()
    assert "workflow_dispatch:" in workflow
    assert "refs/heads/main" in workflow
    assert "permissions:\n  actions: read\n  contents: read" in workflow
    assert "retention-days: 60" in workflow
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in workflow
    assert "5,000,000,000-byte active-artifact cap" in policy
    assert "legal_review_required=true" in policy
    assert "public_release_authorized=false" in policy


def test_disposable_windows_preview_is_sha_pinned_and_short_lived() -> None:
    workflow = (ROOT / ".github/workflows/packlab-preview-windows.yml").read_text()
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in workflow
    assert "retention-days: 1" in workflow
    assert "if-no-files-found: error" in workflow


def test_source_artifact_exact_provenance_passes() -> None:
    validate_source_artifact(
        source_artifact(), repository_private=True, ref="refs/heads/main", now=datetime.now(UTC)
    )


@pytest.mark.parametrize(
    ("mutate", "repository_private", "ref", "reason"),
    [
        (lambda a: a.update(expired=True), True, "refs/heads/main", "expired_artifact"),
        (
            lambda a: a.update(digest="sha256:" + "0" * 64),
            True,
            "refs/heads/main",
            "wrong_archive_digest",
        ),
        (
            lambda a: a["workflow_run"].update(head_branch="feature"),
            True,
            "refs/heads/main",
            "wrong_producer_scope",
        ),
        (
            lambda a: a.update(id=SOURCE_ARTIFACT_ID + 1),
            True,
            "refs/heads/main",
            "wrong_artifact_id",
        ),
        (lambda a: None, False, "refs/heads/main", "public_repository_scope"),
        (lambda a: None, True, "refs/heads/feature", "wrong_source_scope"),
    ],
)
def test_source_artifact_rejects_expired_wrong_hash_or_scope(
    mutate, repository_private, ref, reason
) -> None:
    artifact = source_artifact()
    mutate(artifact)
    with pytest.raises(RetentionBridgeError, match=reason):
        validate_source_artifact(
            artifact, repository_private=repository_private, ref=ref, now=datetime.now(UTC)
        )


def test_storage_gate_rejects_storage_cap_and_duplicate_candidate() -> None:
    with pytest.raises(RetentionBridgeError, match="repository_storage_cap"):
        validate_storage_and_uniqueness(
            [{"expired": False, "size_in_bytes": 4_500_000_000}], projected_bytes=600_000_000
        )
    with pytest.raises(RetentionBridgeError, match="duplicate_retained_artifact"):
        validate_storage_and_uniqueness(
            [{"expired": False, "name": RETAINED_ARTIFACT_NAME, "size_in_bytes": 1}],
            projected_bytes=INSTALLER_BYTES,
        )
    with pytest.raises(RetentionBridgeError, match="candidate_storage_cap"):
        validate_storage_and_uniqueness([], projected_bytes=1_000_000_001)


def test_bundle_gate_rejects_wrong_exe_missing_notice_and_unapproved_reupload() -> None:
    evidence = bundle_evidence()
    validate_bundle_evidence(evidence)
    evidence["installer_sha256"] = "0" * 64
    with pytest.raises(RetentionBridgeError, match="wrong_installer_hash"):
        validate_bundle_evidence(evidence)
    evidence = bundle_evidence()
    evidence["notice_evidence"] = []
    with pytest.raises(RetentionBridgeError, match="missing_notice_evidence"):
        validate_bundle_evidence(evidence)
    evidence = bundle_evidence()
    evidence["approved_for_reupload"] = False
    with pytest.raises(RetentionBridgeError, match="unapproved_reupload"):
        validate_bundle_evidence(evidence)
