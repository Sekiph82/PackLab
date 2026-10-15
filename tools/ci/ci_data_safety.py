"""Fail-closed checks for private data in CI source and artifact inputs.

This is a data-stewardship guard, not a general secret scanner. It rejects
known scan/media/document formats outside exact, hash-pinned fixture and
project-asset sets, private-data path families, oversized unknown payloads,
escaping symlinks, and owner-specific workflow roots. Diagnostics
intentionally omit paths and file contents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

POLICY_PATH = Path("tools/ci/ci_safe_data_policy.json")
SENSITIVE_PAYLOAD_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".bmp",
    ".heic",
    ".dng",
    ".raw",
    ".cr2",
    ".nef",
    ".arw",
    ".exr",
    ".stl",
    ".ply",
    ".pcd",
    ".xyz",
    ".obj",
    ".step",
    ".stp",
    ".3mf",
    ".glb",
    ".gltf",
    ".svg",
    ".ico",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".psd",
    ".ai",
    ".eps",
    ".blend",
    ".xcf",
    ".kra",
    ".e57",
    ".las",
    ".laz",
    ".packscan",
    ".scan",
}
ALWAYS_BLOCK_SUFFIXES = {
    ".heic",
    ".dng",
    ".raw",
    ".cr2",
    ".nef",
    ".arw",
    ".e57",
    ".las",
    ".laz",
    ".packscan",
    ".scan",
}
ARCHIVE_SUFFIXES = {".zip", ".7z", ".rar", ".tar", ".gz", ".tgz"}
UNKNOWN_RAW_SUFFIXES = {".bin", ".dat", ".data", ".capture", ".rawscan"}
STRUCTURED_DATA_SUFFIXES = {".json", ".csv", ".xml", ".txt", ".log", ".yaml", ".yml"}
TEXT_SUFFIXES = {".txt", ".log", ".json", ".yaml", ".yml", ".csv", ".xml", ".md"}
PRIVATE_PATH_COMPONENTS = {
    "supplier",
    "suppliers",
    "povu",
    "customer",
    "customers",
    "client-data",
    "customer-data",
    "customer_data",
    "private-scans",
    "private_scans",
    "private-scan",
    "private_scan",
    "private-sample-scans",
    "private_sample_scans",
    "sample-scans",
    "sample_scans",
    "scan-data",
    "scan_data",
    "scans",
    "raw",
    "raw-scans",
    "raw_scans",
    "capture",
    "captures",
    "raw-captures",
    "raw_captures",
    "kenya-customer",
    "kenya_customers",
    "owner-data",
    "owner_data",
    "personal-data",
    "personal_data",
    "onedrive",
    "dropbox",
    "mnt",
}
PRIVATE_TEXT_ROOTS = re.compile(
    r"(?i)(?:[a-z]:[\\/]+users[\\/]+[^\\/\s]+|"
    r"(?:%USERPROFILE%|\$env:USERPROFILE|OneDrive|Dropbox|/mnt/|"
    r"\\\\[^\\/\s]+[\\/][^\\/\s]+))"
)
TAINTED_ENVIRONMENT = (
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONUSERBASE",
    "VIRTUAL_ENV",
    "QT_PLUGIN_PATH",
    "QT_QPA_PLATFORM_PLUGIN_PATH",
    "QT_API",
    "PYSIDE6_PLUGIN_PATH",
    "QML2_IMPORT_PATH",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
    "CONDA_EXE",
    "CONDA_PYTHON_EXE",
    "MAMBA_ROOT_PREFIX",
    "PACKLAB_DATA_ROOT",
    "PACKLAB_SCAN_ROOT",
)
MAX_UNKNOWN_RAW_BYTES = 1 * 1024 * 1024
MAX_TEXT_SCAN_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 50_000


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str | None = None


def _load_policy(root: Path) -> dict[str, object]:
    try:
        policy = json.loads((root / POLICY_PATH).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("POLICY_MISSING_OR_INVALID") from None
    if policy.get("schema") != "packlab-ci-safe-data-v1":
        raise ValueError("POLICY_SCHEMA_INVALID")
    fixtures = policy.get("approved_synthetic_fixtures")
    if not isinstance(fixtures, dict):
        raise ValueError("POLICY_FIXTURE_SET_INVALID")
    return policy


def _relative_posix(path: Path, root: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def _is_private_component(path: PurePosixPath) -> bool:
    parts = {part.casefold() for part in path.parts}
    return bool(parts & PRIVATE_PATH_COMPONENTS)


def _is_link_or_junction(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or (callable(is_junction) and is_junction())


def _matches_hash_manifest(
    path: Path, relative: str, policy: dict[str, object], manifest_key: str
) -> bool:
    entries = policy.get(manifest_key)
    assert isinstance(entries, dict)
    entry = entries.get(relative)
    if not isinstance(entry, dict):
        return False
    try:
        size = path.stat().st_size
    except OSError:
        return False
    max_bytes = policy.get("maximum_manifested_payload_bytes")
    if not isinstance(max_bytes, int) or size > max_bytes:
        return False
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            if path.suffix.casefold() == ".svg":
                # SVG source is text. Hash its LF-canonical form so the exact
                # allowlist survives Windows autocrlf and Linux hosted checkouts.
                contents = stream.read(max_bytes + 1)
                if len(contents) > max_bytes:
                    return False
                canonical = contents.replace(b"\r\n", b"\n")
                size = len(canonical)
                digest.update(canonical)
            else:
                for chunk in iter(lambda: stream.read(64 * 1024), b""):
                    digest.update(chunk)
    except OSError:
        return False
    return size == entry.get("bytes") and digest.hexdigest() == entry.get("sha256")


def _archive_has_unsafe_member(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return True
    if len(members) > MAX_ARCHIVE_MEMBERS:
        return True
    for member in members:
        name = PurePosixPath(member.filename.replace("\\", "/"))
        if _is_private_component(name) or name.suffix.casefold() in SENSITIVE_PAYLOAD_SUFFIXES:
            return True
        if (
            member.file_size > MAX_UNKNOWN_RAW_BYTES
            and name.suffix.casefold() in UNKNOWN_RAW_SUFFIXES
        ):
            return True
    return False


def _walk_inputs(path: Path) -> Iterable[Path]:
    if _is_link_or_junction(path) or path.is_file():
        yield path
    elif path.is_dir():
        for current, directories, files in os.walk(path, followlinks=False):
            current_path = Path(current)
            for directory in list(directories):
                child = current_path / directory
                if _is_link_or_junction(child):
                    yield child
                    directories.remove(directory)
            yield from (current_path / filename for filename in files)


def _inspect_file(
    path: Path,
    *,
    boundary: Path,
    policy_root: Path,
    policy: dict[str, object],
    scan_text: bool,
) -> Finding | None:
    try:
        relative_to_boundary = _relative_posix(path, boundary)
        # All CLI boundaries are roots; lack of containment is itself unsafe.
        if relative_to_boundary is None:
            return Finding("INPUT_OUTSIDE_BOUNDARY")
        if _is_link_or_junction(path):
            try:
                path.resolve(strict=True).relative_to(boundary.resolve(strict=True))
            except (OSError, ValueError):
                return Finding("SYMLINK_ESCAPE")
            return Finding("SYMLINK_INPUT")
        if not path.is_file():
            return Finding("INPUT_NOT_REGULAR_FILE")
        size = path.stat().st_size
    except OSError:
        return Finding("INPUT_UNREADABLE")

    relative_to_repo = _relative_posix(path, policy_root)
    suffix = path.suffix.casefold()
    path_identity = PurePosixPath(relative_to_repo or str(path).replace("\\", "/"))
    if (
        str(path).startswith("\\\\")
        or str(path).startswith("//")
        or _is_private_component(path_identity)
    ):
        return Finding("PRIVATE_DATA_PATH_FAMILY")
    if suffix in ALWAYS_BLOCK_SUFFIXES:
        return Finding("PRIVATE_OR_RAW_SCAN_FORMAT")
    if suffix in SENSITIVE_PAYLOAD_SUFFIXES:
        if relative_to_repo is None:
            return Finding("UNAPPROVED_SENSITIVE_PAYLOAD", f"suffix={suffix}")
        if _matches_hash_manifest(
            path, relative_to_repo, policy, "approved_synthetic_fixtures"
        ) or _matches_hash_manifest(path, relative_to_repo, policy, "approved_project_assets"):
            return None
        return Finding("UNAPPROVED_SENSITIVE_PAYLOAD", f"suffix={suffix}")
    if suffix in UNKNOWN_RAW_SUFFIXES and size > MAX_UNKNOWN_RAW_BYTES:
        return Finding("OVERSIZED_UNKNOWN_RAW_PAYLOAD")
    if suffix in STRUCTURED_DATA_SUFFIXES and size > MAX_TEXT_SCAN_BYTES:
        return Finding("OVERSIZED_STRUCTURED_DATA")
    if suffix in ARCHIVE_SUFFIXES and _archive_has_unsafe_member(path):
        return Finding("ARCHIVE_CONTAINS_UNSAFE_MEMBER")
    if scan_text and suffix in TEXT_SUFFIXES:
        try:
            contents = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return Finding("TEXT_ARTIFACT_UNREADABLE")
        if PRIVATE_TEXT_ROOTS.search(contents):
            return Finding("OWNER_PATH_IN_TEXT_ARTIFACT")
    return None


def scan_paths(
    repository_root: Path, paths: Iterable[Path], *, scan_text: bool = False
) -> list[Finding]:
    root = repository_root.resolve(strict=True)
    try:
        policy = _load_policy(root)
    except ValueError as error:
        return [Finding(str(error))]
    findings: list[Finding] = []
    for input_path in paths:
        absolute = input_path if input_path.is_absolute() else root / input_path
        if not absolute.exists() and not _is_link_or_junction(absolute):
            findings.append(Finding("INPUT_MISSING"))
            continue
        try:
            if absolute.is_dir() and not _is_link_or_junction(absolute):
                boundary = absolute.resolve(strict=True)
            else:
                boundary = absolute.parent.resolve(strict=True)
        except OSError:
            findings.append(Finding("INPUT_MISSING"))
            continue
        for candidate in _walk_inputs(absolute):
            finding = _inspect_file(
                candidate,
                boundary=boundary,
                policy_root=root,
                policy=policy,
                scan_text=scan_text,
            )
            if finding:
                findings.append(finding)
    return findings


def tracked_and_untracked_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise ValueError("GIT_FILE_INVENTORY_FAILED")
    return [root / os.fsdecode(item) for item in result.stdout.split(b"\0") if item]


def check_workflow_sources(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    workflow_root = root / ".github" / "workflows"
    for path in sorted(workflow_root.glob("*.yml")) + sorted(workflow_root.glob("*.yaml")):
        try:
            contents = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            findings.append(Finding("WORKFLOW_UNREADABLE"))
            continue
        if PRIVATE_TEXT_ROOTS.search(contents):
            findings.append(Finding("OWNER_SPECIFIC_WORKFLOW_ROOT"))
    return findings


def check_environment(environment: dict[str, str] | None = None) -> list[Finding]:
    values = os.environ if environment is None else environment
    if any(values.get(name, "").strip() for name in TAINTED_ENVIRONMENT):
        return [Finding("AMBIENT_DEVELOPER_RUNTIME_INJECTION")]
    return []


def _report(findings: list[Finding]) -> int:
    if findings:
        for finding in findings:
            detail = f" {finding.detail}" if finding.detail else ""
            print(f"PACKLAB_CI_DATA_GUARD=BLOCK code={finding.code}{detail}")
        return 1
    print("PACKLAB_CI_DATA_GUARD=PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "--tracked", action="store_true", help="Scan Git-index and nonignored worktree files."
    )
    parser.add_argument(
        "--path", action="append", type=Path, default=[], help="Scan an explicit artifact input."
    )
    parser.add_argument(
        "--scan-text", action="store_true", help="Inspect uploaded diagnostic text for owner roots."
    )
    parser.add_argument("--check-workflows", action="store_true")
    parser.add_argument("--check-environment", action="store_true")
    args = parser.parse_args(argv)
    root = args.repository.resolve()
    if not args.tracked and not args.path:
        parser.error("at least one of --tracked or --path is required")
    findings: list[Finding] = []
    try:
        if args.tracked:
            findings.extend(scan_paths(root, tracked_and_untracked_paths(root)))
        if args.path:
            findings.extend(scan_paths(root, args.path, scan_text=args.scan_text))
    except (OSError, ValueError):
        findings.append(Finding("SCAN_INCOMPLETE"))
    if args.check_workflows:
        findings.extend(check_workflow_sources(root))
    if args.check_environment:
        findings.extend(check_environment())
    return _report(findings)


if __name__ == "__main__":
    sys.exit(main())
