"""Read source-declared PackLab versions without building apps or running CI.

OFFLINE_PREPARATION_ONLY: this is not an accepted/released artifact manifest.
No network access, native dependencies, secret inputs or owner data are required.
"""

from __future__ import annotations

import argparse
import ast
import json
import plistlib
import re
import tomllib
from pathlib import Path
from typing import Any

_SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

_STUDIO_PY = "apps/windows-studio/src/packlab_studio/__init__.py"
_PROJECT = "apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj"
_INFO = "apps/ios-capture/PackLabCapture/Info.plist"
_SCHEMA = "schemas/packscan/manifest.schema.json"
_PYPROJECT = "pyproject.toml"


class SourceVersionError(ValueError):
    """An authoritative checked-in version is missing, ambiguous, or invalid."""


def _read(root: Path, relative: str) -> bytes:
    try:
        return (root / relative).read_bytes()
    except (OSError, ValueError) as exc:
        raise SourceVersionError("REQUIRED_SOURCE_UNAVAILABLE") from exc


def _semver(value: Any) -> str:
    if not isinstance(value, str) or not _SEMVER.fullmatch(value):
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
        if not build_text.isdigit() or int(build_text) < 1:
            raise SourceVersionError("INVALID_CAPTURE_BUILD")
        matches.append((version, int(build_text), identifier))
    if len(matches) != 2 or matches[0] != matches[1]:
        raise SourceVersionError("INCONSISTENT_CAPTURE_CONFIGS")
    return matches[0]


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

        schema = json.loads(_read(root, _SCHEMA).decode("utf-8"))
        schema_version = _semver(schema["properties"]["schema_version"]["const"])
    except SourceVersionError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError, plistlib.InvalidFileException) as exc:
        raise SourceVersionError("SOURCE_VERSION_READ_FAILED") from exc

    return {
        "status": "OFFLINE_SOURCE_INVENTORY_NOT_RELEASE_ACCEPTANCE",
        "studio_version": studio_toml,
        "capture_version": version,
        "capture_build": build,
        "capture_bundle_id": bundle,
        "packscan_schema_version": schema_version,
        "relevant_sources": [_PYPROJECT, _STUDIO_PY, _PROJECT, _INFO, _SCHEMA],
        "artifact_sha256": None,
        "hosted_build_verified": False,
        "legal_review": "PENDING",
        "factory_release": "NOT_AUTHORIZED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        print(json.dumps(inventory(args.repo), indent=2, sort_keys=True))
        return 0
    except SourceVersionError as exc:
        # Do not echo private absolute local paths or file data on failure.
        print(json.dumps({"status": "OFFLINE_SOURCE_INVENTORY_FAILED", "code": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
