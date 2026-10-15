"""Fail-closed checks for draft release-candidate descriptions.

This stdlib-only validator never builds or publishes a release artifact. Even
complete input returns a preparation status, not release authorization.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

_SHA40_OR_64 = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\Z"
)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _semver(value: Any) -> bool:
    if not isinstance(value, str) or not _SEMVER.fullmatch(value):
        return False
    prerelease = value.split("+", 1)[0].partition("-")[2]
    return not any(
        part.isdigit() and len(part) > 1 and part.startswith("0")
        for part in prerelease.split(".")
    )


def validate_candidate(data: Any) -> dict[str, Any]:
    """Return stable, redacted validation codes for a candidate description."""
    errors: set[str] = set()
    top_keys = {
        "source", "versions", "packscan_compatibility", "artifacts",
        "license_notices", "acceptance", "signed_release", "signatures",
    }
    if not isinstance(data, dict) or set(data) != top_keys:
        return {"status": "BLOCKED", "errors": ["CANDIDATE_FIELDS_MISSING_OR_UNEXPECTED"]}

    source = data.get("source")
    if not isinstance(source, dict) or set(source) != {"sha"} or not (
        isinstance(source.get("sha"), str) and _SHA40_OR_64.fullmatch(source["sha"])
    ):
        errors.add("SOURCE_SHA_MISSING_OR_INVALID")
        source_sha = None
    else:
        source_sha = source["sha"]

    versions = data.get("versions")
    expected_versions = {"studio", "capture", "capture_build", "packscan_schema"}
    if not isinstance(versions, dict) or set(versions) != expected_versions:
        errors.add("VERSION_TRIAD_MISSING_OR_UNEXPECTED")
    else:
        for field in ("studio", "capture", "packscan_schema"):
            if not _semver(versions[field]):
                errors.add("VERSION_TRIAD_INVALID")
        build = versions["capture_build"]
        if isinstance(build, bool) or not isinstance(build, int) or build < 1:
            errors.add("CAPTURE_BUILD_INVALID")

    compatibility = data.get("packscan_compatibility")
    if not isinstance(compatibility, dict) or set(compatibility) != {"read", "write"}:
        errors.add("PACKSCAN_SUPPORT_MISSING_OR_UNEXPECTED")
    else:
        read = compatibility["read"]
        if (
            not isinstance(read, list) or not read
            or any(not _semver(version) for version in read)
            or len(set(read)) != len(read)
            or not _semver(compatibility["write"])
        ):
            errors.add("PACKSCAN_SUPPORT_INVALID")

    artifacts = data.get("artifacts")
    artifact_names: set[str] = set()
    artifact_digests: set[str] = set()
    if not isinstance(artifacts, list) or not artifacts:
        errors.add("ARTIFACTS_MISSING")
        artifacts = []
    for artifact in artifacts:
        keys = {"name", "sha256", "source_sha", "provenance_id"}
        if not isinstance(artifact, dict) or set(artifact) != keys:
            errors.add("ARTIFACT_FIELDS_MISSING_OR_UNEXPECTED")
            continue
        name, digest = artifact["name"], artifact["sha256"]
        if not _nonempty(name) or name in artifact_names:
            errors.add("ARTIFACT_NAME_MISSING_OR_DUPLICATE")
        else:
            artifact_names.add(name)
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            errors.add("ARTIFACT_DIGEST_MISSING_OR_INVALID")
        else:
            artifact_digests.add(digest)
        if not _nonempty(artifact["provenance_id"]):
            errors.add("ARTIFACT_PROVENANCE_MISSING")
        if source_sha is None or artifact["source_sha"] != source_sha:
            errors.add("ARTIFACT_SOURCE_MISMATCH")

    notices = data.get("license_notices")
    notice_names: set[str] = set()
    if not isinstance(notices, list) or not notices:
        errors.add("LICENSE_NOTICES_MISSING")
        notices = []
    for notice in notices:
        keys = {"artifact_name", "license_id", "notice_ref"}
        if not isinstance(notice, dict) or set(notice) != keys:
            errors.add("LICENSE_NOTICE_FIELDS_MISSING_OR_UNEXPECTED")
            continue
        name = notice["artifact_name"]
        if not all(_nonempty(notice[field]) for field in keys):
            errors.add("LICENSE_NOTICE_INCOMPLETE")
        if isinstance(name, str):
            notice_names.add(name)
    if artifact_names - notice_names:
        errors.add("ARTIFACT_LICENSE_NOTICE_MISSING")
    if notice_names - artifact_names:
        errors.add("LICENSE_NOTICE_ARTIFACT_UNKNOWN")

    acceptance = data.get("acceptance")
    if not isinstance(acceptance, dict) or set(acceptance) != {"pl0354_full_xctest", "m17", "independent_audits"}:
        errors.add("ACCEPTANCE_GATES_MISSING_OR_UNEXPECTED")
    else:
        if acceptance["pl0354_full_xctest"] != "AUDITED_PASS":
            errors.add("PL0354_FULL_XCTEST_NOT_ACCEPTED")
        if acceptance["m17"] != "AUDITED_PASS":
            errors.add("M17_NOT_ACCEPTED")
        audits = acceptance["independent_audits"]
        if not isinstance(audits, list) or not audits:
            errors.add("INDEPENDENT_AUDITS_MISSING")
        else:
            audit_ids: set[str] = set()
            for audit in audits:
                if not isinstance(audit, dict) or set(audit) != {"id", "status", "audit_ref"}:
                    errors.add("INDEPENDENT_AUDIT_INCOMPLETE")
                    continue
                audit_id = audit["id"]
                if not _nonempty(audit_id) or audit_id in audit_ids:
                    errors.add("INDEPENDENT_AUDIT_ID_MISSING_OR_DUPLICATE")
                elif isinstance(audit_id, str):
                    audit_ids.add(audit_id)
                if audit["status"] != "AUDITED_PASS" or not _nonempty(audit["audit_ref"]):
                    errors.add("INDEPENDENT_AUDIT_NOT_ACCEPTED")

    signed = data.get("signed_release")
    signatures = data.get("signatures")
    if not isinstance(signed, bool) or not isinstance(signatures, list):
        errors.add("SIGNING_DECLARATION_INVALID")
    elif signed:
        signed_digests: set[str] = set()
        for signature in signatures:
            if not isinstance(signature, dict) or set(signature) != {
                "artifact_sha256", "signature_sha256", "identity_ref"
            }:
                errors.add("SIGNATURE_RECORD_INCOMPLETE")
                continue
            if (
                not isinstance(signature["artifact_sha256"], str)
                or not _SHA256.fullmatch(signature["artifact_sha256"])
                or not isinstance(signature["signature_sha256"], str)
                or not _SHA256.fullmatch(signature["signature_sha256"])
                or not _nonempty(signature["identity_ref"])
            ):
                errors.add("SIGNATURE_RECORD_INVALID")
                continue
            digest = signature["artifact_sha256"]
            if digest in signed_digests:
                errors.add("SIGNATURE_DUPLICATE")
            signed_digests.add(digest)
        if artifact_digests - signed_digests:
            errors.add("SIGNED_ARTIFACT_SIGNATURE_MISSING")
        if signed_digests - artifact_digests:
            errors.add("SIGNATURE_ARTIFACT_UNKNOWN")

    status = "PREPARATION_INPUT_COMPLETE_NOT_RELEASE_AUTHORIZATION" if not errors else "BLOCKED"
    return {"status": status, "errors": sorted(errors)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("description", type=Path, help="UTF-8 JSON candidate description")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.description.read_text(encoding="utf-8"))
        result = validate_candidate(data)
    except (OSError, UnicodeError, json.JSONDecodeError):
        result = {"status": "BLOCKED", "errors": ["CANDIDATE_DESCRIPTION_UNREADABLE"]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
