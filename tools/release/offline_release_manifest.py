"""Generate deterministic, preparation-only manifests from source and build receipts.

This tool never builds, signs, publishes, or authorizes a release. Every binary,
build-identity, compatibility, and notice claim must resolve to a path-safe,
content-digest-bound repository reference. A complete result remains explicitly
NOT_RELEASE_AUTHORIZED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.release.offline_version_inventory import (
    SourceVersionError,
    release_train_identity,
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\Z"
)
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,127}\Z")
_ARTIFACT_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
_LIMITATION = re.compile(r"[a-z][a-z0-9_]{1,63}\Z")
_ARTIFACT_KINDS = {
    "windows_installer",
    "ios_simulator_app",
    "ios_unsigned_device_archive",
    "ios_signed_ipa",
}
_BUILD_SOURCE_FILES = (
    "pyproject.toml",
    "apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj",
    "apps/ios-capture/PackLabCapture.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved",
    "tools/packaging/windows_native_source_lock.json",
    "tools/packaging/windows_occt_sdk_build_contract.json",
)
_TOP_FIELDS = {
    "source_commit",
    "release_train_id",
    "versions",
    "artifacts",
    "windows_build_identity",
    "ios_build_identity",
    "packscan_compatibility",
    "third_party_notice_inventory",
    "known_limitations",
}


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")


def _valid_semver(value: Any) -> bool:
    if not isinstance(value, str) or not _SEMVER.fullmatch(value):
        return False
    prerelease = value.split("+", 1)[0].partition("-")[2]
    return not any(
        part.isdigit() and len(part) > 1 and part.startswith("0") for part in prerelease.split(".")
    )


def _safe_path(root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        return None
    if any(
        char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._/-"
        for char in value
    ):
        return None
    if any(part in {"", ".", ".."} for part in value.split("/")):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    if not value.startswith(
        ("coordination/", "docs/", "schemas/", "tools/ci/", "tools/packaging/")
    ):
        return None
    root = root.resolve()
    candidate = root
    for part in path.parts:
        candidate = candidate / part
        if candidate.is_symlink() or candidate.is_junction():
            return None
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None
    if not resolved.is_relative_to(root) or not resolved.is_file():
        return None
    return resolved


def _read_reference(
    root: Path, reference: Any, errors: set[str], *, json_document: bool
) -> tuple[Any, str] | None:
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        errors.add("EVIDENCE_REFERENCE_MISSING_OR_UNEXPECTED")
        return None
    path = _safe_path(root, reference["path"])
    digest = reference["sha256"]
    if path is None:
        errors.add("EVIDENCE_PATH_UNSAFE_OR_MISSING")
        return None
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        errors.add("EVIDENCE_DIGEST_INVALID")
        return None
    try:
        content = path.read_bytes()
    except OSError:
        errors.add("EVIDENCE_UNREADABLE")
        return None
    observed = hashlib.sha256(content).hexdigest()
    if observed != digest:
        errors.add("EVIDENCE_DIGEST_MISMATCH")
        return None
    if not json_document:
        return {"path": reference["path"], "sha256": digest}, digest
    try:
        document = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        errors.add("EVIDENCE_JSON_INVALID")
        return None
    if not isinstance(document, dict):
        errors.add("EVIDENCE_JSON_INVALID")
        return None
    return document, digest


def _token(value: Any) -> bool:
    return isinstance(value, str) and bool(_TOKEN.fullmatch(value))


def _committed_source(root: Path, source_commit: str, relative: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), "show", f"{source_commit}:{relative}"],
        check=True,
        capture_output=True,
    ).stdout


def _runtime_pins(root: Path, source_commit: str) -> dict[str, str]:
    project = tomllib.loads(
        _committed_source(root, source_commit, "pyproject.toml").decode("utf-8")
    )
    deps = project["project"]["dependencies"]
    pins: dict[str, str] = {}
    for dependency in deps:
        match = re.fullmatch(r"([A-Za-z0-9_-]+)==([^;<>=]+)", dependency)
        if match is None:
            raise ValueError("RUNTIME_DEPENDENCY_NOT_EXACTLY_PINNED")
        name, version = match.groups()
        pins[name.lower().replace("_", "-")] = version
    pbx_path = "apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj"
    lock = _committed_source(root, source_commit, pbx_path).decode("utf-8")
    swift_values = re.findall(r"\bSWIFT_VERSION\s*=\s*([^;]+);", lock)
    swift_versions = set(swift_values)
    package_path = "apps/ios-capture/PackLabCapture.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved"
    package_bytes = _committed_source(root, source_commit, package_path)
    package = json.loads(package_bytes.decode("utf-8"))
    native_lock = json.loads(
        _committed_source(
            root, source_commit, "tools/packaging/windows_native_source_lock.json"
        ).decode("utf-8")
    )
    occt_contract = json.loads(
        _committed_source(
            root, source_commit, "tools/packaging/windows_occt_sdk_build_contract.json"
        ).decode("utf-8")
    )
    nextlevel = [pin for pin in package["pins"] if pin.get("identity", "").lower() == "nextlevel"]
    if len(swift_values) != 4 or len(swift_versions) != 1 or len(nextlevel) != 1:
        raise ValueError("BUILD_SOURCE_AMBIGUOUS")
    occt_records = [
        record for record in native_lock["records"] if record.get("component") == "OCCT"
    ]
    if len(occt_records) != 1:
        raise ValueError("OCCT_SOURCE_LOCK_AMBIGUOUS")
    occt_record = occt_records[0]
    if occt_contract.get("occt_source") != {
        "record_id": occt_record.get("id"),
        "version": occt_record.get("version"),
        "revision": occt_record.get("revision"),
        "sha256": occt_record.get("sha256"),
    }:
        raise ValueError("OCCT_SOURCE_CONTRACT_MISMATCH")
    pin = nextlevel[0]["state"]
    return {
        "python_min": "3.12",
        "python_max_exclusive": "3.13",
        "qt": pins["pyside6-essentials"],
        "qt_addons": pins["pyside6-addons"],
        "ocp": pins["cadquery-ocp-novtk"],
        "open3d": pins["open3d"],
        "occt": occt_record["version"],
        "swift_language_mode": next(iter(swift_versions)).strip().strip('"'),
        "nextlevel_version": pin["version"],
        "nextlevel_revision": pin["revision"],
        "package_resolved_sha256": hashlib.sha256(package_bytes).hexdigest(),
    }


def _verify_build_sources(root: Path, source_commit: str) -> None:
    """Reject dependency/toolchain facts read from files differing from HEAD."""
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if head != source_commit:
            raise ValueError("BUILD_SOURCE_COMMIT_MISMATCH")
        for relative in _BUILD_SOURCE_FILES:
            source = root / relative
            current = root
            for part in PurePosixPath(relative).parts:
                current = current / part
                if current.is_symlink() or current.is_junction():
                    raise ValueError("BUILD_SOURCE_LINK_REJECTED")
            committed_blob = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "--verify", f"{head}:{relative}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            working_blob = subprocess.run(
                ["git", "-C", str(root), "hash-object", f"--path={relative}", "--", relative],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            if committed_blob != working_blob or not source.is_file():
                raise ValueError("BUILD_SOURCE_TREE_MISMATCH")
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError("BUILD_SOURCE_UNAVAILABLE") from error


def _validate_candidate(data: Any, root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: set[str] = set()
    if not isinstance(data, dict) or set(data) != _TOP_FIELDS:
        return None, ["CANDIDATE_FIELDS_MISSING_OR_UNEXPECTED"]

    commit = data["source_commit"]
    if not isinstance(commit, str) or not _SHA40.fullmatch(commit):
        errors.add("SOURCE_COMMIT_INVALID")
        train = None
    else:
        try:
            train = release_train_identity(root, commit)
        except (SourceVersionError, OSError, subprocess.SubprocessError):
            errors.add("SOURCE_COMMIT_OR_VERSION_INVENTORY_INVALID")
            train = None
        try:
            _verify_build_sources(root, commit)
        except ValueError as error:
            errors.add(str(error))
    build_pins = None
    if train is not None:
        try:
            build_pins = _runtime_pins(root, commit)
        except (OSError, UnicodeError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
            errors.add("BUILD_SOURCE_UNAVAILABLE")
    if train is not None and data["release_train_id"] != train["release_train"]["id"]:
        errors.add("RELEASE_TRAIN_ID_MISMATCH")
    if train is None and not isinstance(data["release_train_id"], str):
        errors.add("RELEASE_TRAIN_ID_MISSING")

    versions = data["versions"]
    expected_version_fields = {"studio", "capture", "capture_build", "packscan_schema"}
    if not isinstance(versions, dict) or set(versions) != expected_version_fields:
        errors.add("VERSION_FIELDS_MISSING_OR_UNEXPECTED")
    elif train is not None:
        expected = {
            "studio": train["studio_version"],
            "capture": train["capture_version"],
            "capture_build": train["capture_build"],
            "packscan_schema": train["packscan_schema_version"],
        }
        if versions != expected:
            errors.add("SOURCE_VERSION_MISMATCH")

    artifacts_in = data["artifacts"]
    if not isinstance(artifacts_in, list) or not artifacts_in:
        errors.add("ARTIFACTS_MISSING")
        artifacts_in = []
    artifacts: list[dict[str, Any]] = []
    seen_names: set[tuple[str, str]] = set()
    seen_digests: set[str] = set()
    platforms: set[str] = set()
    for item in artifacts_in:
        if not isinstance(item, dict) or set(item) != {"platform", "provenance_ref"}:
            errors.add("ARTIFACT_FIELDS_MISSING_OR_UNEXPECTED")
            continue
        platform = item["platform"]
        if not isinstance(platform, str) or platform not in {"windows", "ios"}:
            errors.add("ARTIFACT_PLATFORM_INVALID")
            continue
        loaded = _read_reference(root, item["provenance_ref"], errors, json_document=True)
        if loaded is None:
            continue
        receipt, receipt_digest = loaded
        required_receipt = {
            "platform",
            "artifact_name",
            "artifact_kind",
            "artifact_sha256",
            "artifact_bytes",
            "source_commit",
            "workflow_run_id",
            "signing_state",
        }
        optional_receipt = {"signature_verification_ref", "package_resolved_sha256"}
        if set(receipt) - required_receipt - optional_receipt or not required_receipt <= set(
            receipt
        ):
            errors.add("ARTIFACT_PROVENANCE_FIELDS_INVALID")
            continue
        name, digest = receipt["artifact_name"], receipt["artifact_sha256"]
        if (
            receipt["platform"] != platform
            or not isinstance(name, str)
            or not _ARTIFACT_NAME.fullmatch(name)
            or (platform, name) in seen_names
        ):
            errors.add("ARTIFACT_IDENTITY_INVALID_OR_DUPLICATE")
        digest_valid = isinstance(digest, str) and bool(_SHA256.fullmatch(digest))
        if not digest_valid or digest in seen_digests:
            errors.add("ARTIFACT_DIGEST_INVALID_OR_DUPLICATE")
        if digest_valid:
            seen_digests.add(digest)
        else:
            digest = ""
        if (
            isinstance(receipt["artifact_bytes"], bool)
            or not isinstance(receipt["artifact_bytes"], int)
            or receipt["artifact_bytes"] <= 0
        ):
            errors.add("ARTIFACT_LENGTH_INVALID")
        if commit is None or receipt["source_commit"] != commit:
            errors.add("ARTIFACT_SOURCE_MISMATCH")
        if platform == "ios":
            if (
                build_pins is None
                or receipt.get("package_resolved_sha256") != build_pins["package_resolved_sha256"]
            ):
                errors.add("IOS_PACKAGE_RESOLVED_PROVENANCE_MISMATCH")
        elif "package_resolved_sha256" in receipt:
            errors.add("WINDOWS_ARTIFACT_HAS_IOS_LOCK_IDENTITY")
        if not isinstance(receipt["workflow_run_id"], str) or not re.fullmatch(
            r"[0-9]{5,20}", receipt["workflow_run_id"]
        ):
            errors.add("ARTIFACT_RUN_ID_INVALID")
        if (
            not isinstance(receipt["artifact_kind"], str)
            or receipt["artifact_kind"] not in _ARTIFACT_KINDS
        ):
            errors.add("ARTIFACT_KIND_INVALID")
        elif (platform == "windows") != (receipt["artifact_kind"] == "windows_installer"):
            errors.add("ARTIFACT_KIND_PLATFORM_MISMATCH")
        signing_state = receipt["signing_state"]
        if (
            receipt["artifact_kind"] == "ios_signed_ipa" and signing_state != "SIGNED_VERIFIED"
        ) or (
            receipt["artifact_kind"] in {"ios_simulator_app", "ios_unsigned_device_archive"}
            and signing_state != "UNSIGNED"
        ):
            errors.add("ARTIFACT_KIND_SIGNING_STATE_MISMATCH")
        signature_sha = None
        signature_ref_path = None
        signature_ref_sha256 = None
        if not isinstance(signing_state, str) or signing_state not in {
            "SIGNED_VERIFIED",
            "UNSIGNED",
        }:
            errors.add("ARTIFACT_SIGNING_STATE_INVALID")
        if signing_state == "SIGNED_VERIFIED":
            signature_loaded = _read_reference(
                root, receipt.get("signature_verification_ref"), errors, json_document=True
            )
            if signature_loaded is None:
                errors.add("SIGNED_ARTIFACT_EVIDENCE_MISSING")
            else:
                signature_document, signature_ref_sha256 = signature_loaded
                if (
                    set(signature_document)
                    != {
                        "artifact_sha256",
                        "signature_sha256",
                        "verification_status",
                        "verification_tool",
                    }
                    or signature_document.get("artifact_sha256") != digest
                    or signature_document.get("verification_status") != "SIGNATURE_VERIFIED"
                    or not isinstance(signature_document.get("signature_sha256"), str)
                    or not _SHA256.fullmatch(signature_document["signature_sha256"])
                    or not _token(signature_document.get("verification_tool"))
                ):
                    errors.add("SIGNED_ARTIFACT_EVIDENCE_INVALID")
                else:
                    signature_sha = signature_document["signature_sha256"]
                    signature_ref_path = receipt["signature_verification_ref"].get("path")
        elif "signature_verification_ref" in receipt:
            errors.add("UNSIGNED_ARTIFACT_HAS_SIGNATURE_CLAIM")
        if isinstance(name, str):
            seen_names.add((platform, name))
        platforms.add(platform)
        artifacts.append(
            {
                "platform": platform,
                "name": name,
                "kind": receipt["artifact_kind"],
                "sha256": digest,
                "bytes": receipt["artifact_bytes"],
                "source_commit": receipt["source_commit"],
                "workflow_run_id": receipt["workflow_run_id"],
                "signing_state": signing_state,
                "signature_sha256": signature_sha,
                "signature_verification_ref": signature_ref_path,
                "signature_verification_sha256": signature_ref_sha256,
                "provenance_ref": item["provenance_ref"]["path"],
                "provenance_sha256": receipt_digest,
            }
        )
    if platforms != {"windows", "ios"}:
        errors.add("WINDOWS_AND_IOS_ARTIFACTS_REQUIRED")

    identities: dict[str, Any] = {}
    identity_fields = {
        "windows": {
            "source_commit",
            "workflow_run_id",
            "artifact_sha256s",
            "python",
            "qt",
            "ocp",
            "occt",
            "open3d",
        },
        "ios": {
            "source_commit",
            "workflow_run_id",
            "artifact_sha256s",
            "package_resolved_sha256",
            "xcode_version",
            "xcode_build",
            "sdk",
            "swift_language_mode",
            "swift_compiler",
            "nextlevel_version",
            "nextlevel_revision",
        },
    }
    for platform, candidate_key in (
        ("windows", "windows_build_identity"),
        ("ios", "ios_build_identity"),
    ):
        item = data[candidate_key]
        if not isinstance(item, dict) or set(item) != {"evidence_ref"}:
            errors.add("BUILD_IDENTITY_REFERENCE_MISSING_OR_UNEXPECTED")
            continue
        loaded = _read_reference(root, item["evidence_ref"], errors, json_document=True)
        if loaded is None:
            continue
        evidence, digest = loaded
        fields = identity_fields[platform]
        scalar_fields = fields - {"artifact_sha256s"}
        if set(evidence) != fields or any(not _token(evidence[field]) for field in scalar_fields):
            errors.add("BUILD_IDENTITY_FIELDS_INVALID")
            continue
        platform_artifacts = [
            artifact for artifact in artifacts if artifact["platform"] == platform
        ]
        expected_hashes = sorted(artifact["sha256"] for artifact in platform_artifacts)
        expected_runs = {artifact["workflow_run_id"] for artifact in platform_artifacts}
        if (
            evidence["source_commit"] != commit
            or not isinstance(evidence["artifact_sha256s"], list)
            or any(
                not isinstance(value, str) or not _SHA256.fullmatch(value)
                for value in evidence["artifact_sha256s"]
            )
            or sorted(evidence["artifact_sha256s"]) != expected_hashes
            or len(expected_runs) != 1
            or evidence["workflow_run_id"] not in expected_runs
        ):
            errors.add("BUILD_IDENTITY_PROVENANCE_MISMATCH")
        if platform == "windows":
            try:
                if build_pins is None:
                    raise ValueError("BUILD_SOURCE_UNAVAILABLE")
                pins = build_pins
                py = evidence["python"].split(".")
                if len(py) != 3 or ".".join(py[:2]) != pins["python_min"] or not py[2].isdigit():
                    errors.add("WINDOWS_PYTHON_IDENTITY_UNSUPPORTED")
                for field, pin in (
                    ("qt", "qt"),
                    ("ocp", "ocp"),
                    ("occt", "occt"),
                    ("open3d", "open3d"),
                ):
                    if evidence[field] != pins[pin]:
                        errors.add("WINDOWS_DEPENDENCY_IDENTITY_MISMATCH")
                if pins["qt"] != pins["qt_addons"]:
                    errors.add("QT_PACKAGE_VERSION_MISMATCH")
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                errors.add("WINDOWS_BUILD_SOURCE_UNAVAILABLE")
        else:
            try:
                if build_pins is None:
                    raise ValueError("BUILD_SOURCE_UNAVAILABLE")
                pins = build_pins
                if evidence["package_resolved_sha256"] != pins["package_resolved_sha256"]:
                    errors.add("IOS_PACKAGE_RESOLVED_IDENTITY_MISMATCH")
                if (
                    not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", evidence["xcode_version"])
                    or not re.fullmatch(r"[0-9]{2}[A-Z][A-Za-z0-9]+", evidence["xcode_build"])
                    or not re.fullmatch(r"[0-9]+\.[0-9]+", evidence["sdk"])
                    or not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", evidence["swift_compiler"])
                    or not _valid_semver(evidence["nextlevel_version"])
                    or not _SHA40.fullmatch(evidence["nextlevel_revision"])
                ):
                    errors.add("IOS_TOOLCHAIN_IDENTITY_INVALID")
                if evidence["swift_language_mode"] != pins["swift_language_mode"]:
                    errors.add("IOS_SWIFT_LANGUAGE_MODE_MISMATCH")
                if (
                    evidence["nextlevel_version"] != pins["nextlevel_version"]
                    or evidence["nextlevel_revision"] != pins["nextlevel_revision"]
                ):
                    errors.add("IOS_NEXTLEVEL_IDENTITY_MISMATCH")
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                errors.add("IOS_BUILD_SOURCE_UNAVAILABLE")
        identities[platform] = {
            **evidence,
            "evidence_ref": item["evidence_ref"]["path"],
            "evidence_sha256": digest,
        }

    compatibility = data["packscan_compatibility"]
    if not isinstance(compatibility, dict) or set(compatibility) != {
        "read_min",
        "read_max",
        "write",
        "migrations",
        "evidence_ref",
    }:
        errors.add("PACKSCAN_COMPATIBILITY_FIELDS_INVALID")
        compatibility_out = None
    else:
        loaded = _read_reference(root, compatibility["evidence_ref"], errors, json_document=False)
        current = train["packscan_schema_version"] if train is not None else None
        if any(not _valid_semver(compatibility[key]) for key in ("read_min", "read_max", "write")):
            errors.add("PACKSCAN_COMPATIBILITY_VERSION_INVALID")
        elif current is None or any(
            compatibility[key] != current for key in ("read_min", "read_max", "write")
        ):
            errors.add("PACKSCAN_COMPATIBILITY_UNSUPPORTED_CLAIM")
        if compatibility["migrations"] != []:
            errors.add("PACKSCAN_MIGRATION_UNSUPPORTED_CLAIM")
        compatibility_out = {
            "read_min": compatibility["read_min"],
            "read_max": compatibility["read_max"],
            "write": compatibility["write"],
            "migrations": [],
        }
        if loaded is not None:
            compatibility_out.update(
                {"evidence_ref": loaded[0]["path"], "evidence_sha256": loaded[1]}
            )

    notice_loaded = _read_reference(
        root, data["third_party_notice_inventory"], errors, json_document=False
    )
    notice_out = notice_loaded[0] if notice_loaded is not None else None

    limitations = data["known_limitations"]
    if (
        not isinstance(limitations, list)
        or not limitations
        or any(not isinstance(item, str) or not _LIMITATION.fullmatch(item) for item in limitations)
        or len(set(limitations)) != len(limitations)
        or "m17_not_accepted" not in limitations
    ):
        errors.add("KNOWN_LIMITATIONS_MISSING_OR_INVALID")

    if errors or train is None or compatibility_out is None or notice_out is None:
        return None, sorted(errors or {"MANIFEST_GENERATION_BLOCKED"})

    artifacts.sort(key=lambda item: (item["platform"], item["name"]))
    limitations = sorted(limitations)
    versions_out = {
        "studio": train["studio_version"],
        "capture": train["capture_version"],
        "capture_build": train["capture_build"],
        "packscan_schema": train["packscan_schema_version"],
    }
    identity_payload = {
        "identity_schema": "packlab-release-manifest-v1",
        "source_commit": commit,
        "release_train_id": train["release_train"]["id"],
        "versions": versions_out,
        "artifacts": [
            {
                key: item[key]
                for key in (
                    "platform",
                    "name",
                    "kind",
                    "sha256",
                    "bytes",
                    "source_commit",
                    "workflow_run_id",
                    "signing_state",
                    "signature_sha256",
                    "signature_verification_sha256",
                    "provenance_sha256",
                )
            }
            for item in artifacts
        ],
        "build_identities": {
            platform: {key: value for key, value in identity.items() if key not in {"evidence_ref"}}
            for platform, identity in sorted(identities.items())
        },
        "packscan_compatibility": {
            key: value for key, value in compatibility_out.items() if key != "evidence_ref"
        },
        "third_party_notice_inventory_sha256": notice_out["sha256"],
        "known_limitations": limitations,
    }
    manifest_digest = hashlib.sha256(_canonical_bytes(identity_payload)).hexdigest()
    manifest = {
        "manifest_schema": "packlab-release-manifest-v1",
        "manifest_id": f"packlab-rm-v1-{manifest_digest}",
        "identity_sha256": manifest_digest,
        "status": "PREPARATION_ONLY_NOT_RELEASE_AUTHORIZATION",
        "release_authorization": "NOT_GRANTED",
        "m17_status": "NOT_ACCEPTED",
        **identity_payload,
        "artifacts": artifacts,
        "build_identities": identities,
        "packscan_compatibility": compatibility_out,
        "third_party_notice_inventory": notice_out,
    }
    return manifest, []


def generate_manifest(data: Any, root: Path) -> dict[str, Any]:
    """Validate a candidate and return the deterministic manifest or redacted errors."""
    try:
        manifest, errors = _validate_candidate(data, root.resolve())
    except (AttributeError, KeyError, OSError, TypeError, ValueError):
        return {"status": "BLOCKED", "errors": ["CANDIDATE_STRUCTURE_INVALID"]}
    if manifest is None:
        return {"status": "BLOCKED", "errors": errors}
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "description", type=Path, help="UTF-8 JSON source/build evidence references"
    )
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output", type=Path, help="write the canonical manifest only after validation"
    )
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.description.read_text(encoding="utf-8"))
        result = generate_manifest(data, args.repo)
    except (OSError, UnicodeError, json.JSONDecodeError):
        result = {"status": "BLOCKED", "errors": ["CANDIDATE_DESCRIPTION_UNREADABLE"]}
    output = _canonical_bytes(result)
    if result["status"] == "BLOCKED":
        print(output.decode("ascii"), end="")
        return 2
    if args.output is not None:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("xb") as handle:
                handle.write(output)
        except OSError:
            print(
                _canonical_bytes(
                    {"status": "BLOCKED", "errors": ["OUTPUT_PATH_UNAVAILABLE"]}
                ).decode("ascii"),
                end="",
            )
            return 2
    else:
        print(output.decode("ascii"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
