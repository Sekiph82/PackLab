"""Read source-declared PackLab versions without building apps or running CI.

OFFLINE_PREPARATION_ONLY: this is not an accepted/released artifact manifest.
No network access, native dependencies, secret inputs or owner data are required.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import plistlib
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

_SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

_STUDIO_PY = "apps/windows-studio/src/packlab_studio/__init__.py"
_PROJECT = "apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj"
_INFO = "apps/ios-capture/PackLabCapture/Info.plist"
_SCHEMA = "schemas/packscan/manifest.schema.json"
_SCHEMA_CODE = "core/src/packlab_core/packscan/container.py"
_PYPROJECT = "pyproject.toml"
_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


class SourceVersionError(ValueError):
    """An authoritative checked-in version is missing, ambiguous, or invalid."""


def _read(root: Path, relative: str) -> bytes:
    try:
        root = root.resolve()
        source = root / relative
        current = root
        for part in Path(relative).parts:
            current = current / part
            if current.is_symlink() or current.is_junction():
                raise SourceVersionError("LINKED_VERSION_SOURCE_REJECTED")
        resolved = source.resolve(strict=True)
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise SourceVersionError("VERSION_SOURCE_OUTSIDE_REPOSITORY")
        return resolved.read_bytes()
    except SourceVersionError:
        raise
    except (OSError, ValueError) as exc:
        raise SourceVersionError("REQUIRED_SOURCE_UNAVAILABLE") from exc


def _semver(value: Any) -> str:
    if not isinstance(value, str):
        raise SourceVersionError("INVALID_SEMVER")
    match = _SEMVER.fullmatch(value)
    if match is None:
        raise SourceVersionError("INVALID_SEMVER")
    prerelease = match.group("prerelease")
    if prerelease is not None and any(
        re.fullmatch(r"[0-9]+", identifier) and len(identifier) > 1 and identifier[0] == "0"
        for identifier in prerelease.split(".")
    ):
        raise SourceVersionError("INVALID_SEMVER")
    return value


def _studio_py_version(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise SourceVersionError("STUDIO_VERSION_PARSE_ERROR") from exc
    versions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets
        ):
            if not isinstance(node.value, ast.Constant):
                raise SourceVersionError("NON_LITERAL_STUDIO_VERSION")
            versions.append(_semver(node.value.value))
    if len(versions) != 1:
        raise SourceVersionError("AMBIGUOUS_STUDIO_VERSION")
    return versions[0]


def _capture_versions(project: str) -> tuple[str, int, str]:
    # Select only app build configurations, never the XCTest host's bundle id.
    configs = re.findall(
        r"/\* (?:Debug|Release) \*/ = \{isa = XCBuildConfiguration; "
        r"buildSettings = \{([^{}]+)\}; name = (?:Debug|Release); \};",
        project,
    )
    matches: list[tuple[str, int, str]] = []
    for raw in configs:
        if "PRODUCT_BUNDLE_IDENTIFIER = com.packlab.capture;" not in raw:
            continue
        values: list[str] = []
        for key in ("MARKETING_VERSION", "CURRENT_PROJECT_VERSION", "PRODUCT_BUNDLE_IDENTIFIER"):
            fields = re.findall(r"\b" + key + r"\s*=\s*([^;]+);", raw)
            if len(fields) != 1:
                raise SourceVersionError("MISSING_OR_AMBIGUOUS_CAPTURE_FIELD")
            values.append(fields[0].strip().strip('"'))
        version, build_text, identifier = values
        _semver(version)
        if not re.fullmatch(r"[0-9]+", build_text) or int(build_text) < 1:
            raise SourceVersionError("INVALID_CAPTURE_BUILD")
        matches.append((version, int(build_text), identifier))
    if len(matches) != 2 or matches[0] != matches[1]:
        raise SourceVersionError("INCONSISTENT_CAPTURE_CONFIGS")
    return matches[0]


def _schema_code_version(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise SourceVersionError("PACKSCAN_SCHEMA_SOURCE_PARSE_ERROR") from exc
    versions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SCHEMA_VERSION"
            for target in node.targets
        ):
            if not isinstance(node.value, ast.Constant):
                raise SourceVersionError("NON_LITERAL_PACKSCAN_SCHEMA_VERSION")
            versions.append(_semver(node.value.value))
    if len(versions) != 1:
        raise SourceVersionError("AMBIGUOUS_PACKSCAN_SCHEMA_VERSION")
    return versions[0]


def inventory(root: Path) -> dict[str, Any]:
    """Return a source-only inventory; never infer shipped/release compatibility."""
    root = root.resolve()
    try:
        project = tomllib.loads(_read(root, _PYPROJECT).decode("utf-8"))
        studio_toml = _semver(project["project"]["version"])
        studio_python = _studio_py_version(_read(root, _STUDIO_PY).decode("utf-8"))
        if studio_toml != studio_python:
            raise SourceVersionError("STUDIO_VERSION_MISMATCH")

        version, build, bundle = _capture_versions(_read(root, _PROJECT).decode("utf-8"))
        info = plistlib.loads(_read(root, _INFO))
        for key, expected in (
            ("CFBundleShortVersionString", "$(MARKETING_VERSION)"),
            ("CFBundleVersion", "$(CURRENT_PROJECT_VERSION)"),
            ("CFBundleIdentifier", "$(PRODUCT_BUNDLE_IDENTIFIER)"),
        ):
            if info.get(key) != expected:
                raise SourceVersionError("CAPTURE_PLIST_VERSION_BINDING_MISMATCH")

        def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise SourceVersionError("AMBIGUOUS_SCHEMA_VERSION_SOURCE")
                result[key] = value
            return result

        schema = json.loads(
            _read(root, _SCHEMA).decode("utf-8"), object_pairs_hook=reject_duplicate_keys
        )
        schema_version = _semver(schema["properties"]["schema_version"]["const"])
        schema_code_version = _schema_code_version(_read(root, _SCHEMA_CODE).decode("utf-8"))
        if schema_version != schema_code_version:
            raise SourceVersionError("PACKSCAN_SCHEMA_VERSION_MISMATCH")
    except SourceVersionError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError, plistlib.InvalidFileException) as exc:
        raise SourceVersionError("SOURCE_VERSION_READ_FAILED") from exc

    return {
        "status": "OFFLINE_UNVERIFIED_BUILD",
        "studio_version": studio_toml,
        "capture_version": version,
        "capture_build": build,
        "capture_bundle_id": bundle,
        "packscan_schema_version": schema_version,
        "relevant_sources": [
            _PYPROJECT,
            _STUDIO_PY,
            _PROJECT,
            _INFO,
            _SCHEMA_CODE,
            _SCHEMA,
        ],
        "artifact_sha256": None,
        "hosted_build_verified": False,
        "legal_review": "PENDING",
        "factory_release": "NOT_AUTHORIZED",
    }


def release_train_identity(root: Path, source_commit: str) -> dict[str, Any]:
    """Bind independent source versions to one exact Git commit deterministically.

    This is source identity only. It does not assert that artifacts were built,
    tested, signed, accepted, or released from the supplied commit.
    """
    if not isinstance(source_commit, str) or not _COMMIT_SHA.fullmatch(source_commit):
        raise SourceVersionError("INVALID_SOURCE_COMMIT")
    _verify_checkout_commit(root, source_commit)
    source = inventory(root)
    versions = {
        "studio": source["studio_version"],
        "capture": source["capture_version"],
        "capture_build": source["capture_build"],
        "packscan_schema": source["packscan_schema_version"],
    }
    identity = {
        "identity_schema": "packlab-release-train-v1",
        "source_commit": source_commit,
        "versions": versions,
    }
    canonical = json.dumps(
        identity, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    digest = hashlib.sha256(canonical).hexdigest()
    return {
        **source,
        "source_commit": source_commit,
        "release_train": {
            "id": f"packlab-rt-v1-{digest}",
            "identity_sha256": digest,
            "identity_schema": identity["identity_schema"],
            "versions": versions,
        },
    }


def _verify_checkout_commit(root: Path, source_commit: str) -> None:
    """Ensure version-source worktree blobs match the exact checked-out commit."""
    root = root.resolve()
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if head != source_commit:
            raise SourceVersionError("SOURCE_COMMIT_MISMATCH")
        for relative in (_PYPROJECT, _STUDIO_PY, _PROJECT, _INFO, _SCHEMA_CODE, _SCHEMA):
            _read(root, relative)
            committed_blob = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "--verify", f"{head}:{relative}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            working_blob = subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "hash-object",
                    f"--path={relative}",
                    "--",
                    relative,
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            if working_blob != committed_blob:
                raise SourceVersionError("SOURCE_VERSION_TREE_MISMATCH")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SourceVersionError("GIT_SOURCE_COMMIT_UNAVAILABLE") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--commit",
        help="full lowercase 40-character Git SHA for the exact source revision being identified",
    )
    args = parser.parse_args()
    try:
        if args.commit is not None:
            if not _COMMIT_SHA.fullmatch(args.commit):
                raise SourceVersionError("INVALID_SOURCE_COMMIT")
        result = (
            release_train_identity(args.repo, args.commit)
            if args.commit is not None
            else inventory(args.repo)
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except SourceVersionError as exc:
        # Do not echo private absolute local paths or file data on failure.
        print(json.dumps({"status": "OFFLINE_SOURCE_INVENTORY_FAILED", "code": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
