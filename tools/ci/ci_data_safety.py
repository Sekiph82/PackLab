"""Fail-closed checks for private data in CI source and artifact inputs.

This is a data-stewardship guard, not a general secret scanner. It rejects
known scan/media/document formats outside exact, hash-pinned fixture and
project-asset sets, private-data path families, oversized unknown payloads,
escaping symlinks, owner-specific workflow roots, and a narrow set of Apple
signing/private-key indicators. Diagnostics intentionally omit paths and file
contents.
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
SIGNING_TEXT_SUFFIXES = TEXT_SUFFIXES | {
    ".py",
    ".toml",
    ".plist",
    ".pbxproj",
    ".sh",
    ".ps1",
    ".swift",
    ".ini",
    ".cfg",
    ".properties",
    ".entitlements",
    ".env",
    ".pem",
    ".key",
}
SIGNING_MATERIAL_SUFFIXES = {
    ".p8",
    ".p12",
    ".pfx",
    ".cer",
    ".mobileprovision",
    ".provisionprofile",
    ".keychain",
    ".keychain-db",
}
PRIVATE_KEY_HEADER = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----",
    re.IGNORECASE,
)
SECRET_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:export\s+)?(?:APPLE|APP_STORE|APPSTORE|ASC|GITHUB|GH|SIGNING|PROVISIONING|"
    r"DISTRIBUTION|PRIVATE|CLIENT|ACCESS|API|DEPLOY|CERTIFICATE|MATCH|KEYCHAIN)"
    r"[A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PRIVATE_KEY|API_KEY|SIGNING_KEY|"
    r"SIGNING_CERTIFICATE_BASE64|SIGNING_CERTIFICATE|PROVISIONING_PROFILE|"
    r"CERTIFICATE_P12_BASE64|CERTIFICATE_P12|CERTIFICATE_BASE64|CERTIFICATE|"
    r"PROFILE_BASE64|KEYCHAIN|TEAM_ID|KEY_ID|ISSUER_ID|ID|EMAIL|ACCOUNT)"
    r"\s*[:=]\s*(?:([\"'])([^\"'\r\n]+)\1|([^\s#]+))"
)
SIGNING_DOCUMENT_ALLOWLIST_PATH = Path("tools/ci/ci_signing_material_allowlist.json")
REVIEWED_SIGNING_MARKER_DOCUMENTS = {
    "coordination/sessions/M16-C001/M16_OFFLINE_OCTOBER_CHATGPT_AUDIT_V01.md": "10206292fc83b4ecb8be9f5ef22c86783f0dc7e5d2b6f3b5dfbbd61cacc1815a",
    "coordination/sessions/M16-C001/M16_OFFLINE_OCTOBER_R01_SECURITY_VERSION_TEMP_CLEANUP_PROMPT.md": "15a5265c56c7f5e671147b9fb9b2ea81a2fa6fa54f60dd15f65bb0d7f0613f62",
}
LINE_ENDING_CANONICAL_SUFFIXES = {
    ".svg",
    ".step",
    ".stp",
    ".dxf",
    ".ply",
    ".stl",
    ".obj",
    ".pcd",
    ".xyz",
}
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
            if path.suffix.casefold() in LINE_ENDING_CANONICAL_SUFFIXES:
                # These allowlisted source formats are text. Hash their
                # LF-canonical form across Windows and Linux checkouts.
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


def _load_signing_document_allowlist(root: Path) -> dict[str, dict[str, str]]:
    try:
        manifest = json.loads((root / SIGNING_DOCUMENT_ALLOWLIST_PATH).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("SIGNING_ALLOWLIST_MISSING_OR_INVALID") from None
    if not isinstance(manifest, dict):
        raise ValueError("SIGNING_ALLOWLIST_SCHEMA_INVALID")
    if manifest.get("schema") != "packlab-signing-documents-v1":
        raise ValueError("SIGNING_ALLOWLIST_SCHEMA_INVALID")
    entries = manifest.get("approved_public_documents")
    if not isinstance(entries, dict):
        raise ValueError("SIGNING_ALLOWLIST_ENTRIES_INVALID")
    for relative, entry in entries.items():
        if (
            not isinstance(relative, str)
            or not (
                relative.startswith("docs/security/fixtures/")
                or relative.startswith("coordination/sessions/")
            )
            or not relative.endswith(".md")
            or not isinstance(entry, dict)
            or not isinstance(entry.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
            or not isinstance(entry.get("reason"), str)
            or not entry["reason"].strip()
        ):
            raise ValueError("SIGNING_ALLOWLIST_ENTRY_INVALID")
    return entries


def _matches_reviewed_public_document(
    path: Path, relative: str, allowlist: dict[str, dict[str, str]]
) -> bool:
    entry = allowlist.get(relative)
    reviewed_sha256 = REVIEWED_SIGNING_MARKER_DOCUMENTS.get(relative)
    if (
        not (
            relative.startswith("docs/security/fixtures/")
            or relative.startswith("coordination/sessions/")
        )
        or not relative.endswith(".md")
        or not isinstance(entry, dict)
        or not isinstance(entry.get("reason"), str)
        or not entry["reason"].strip()
        or entry.get("sha256") != reviewed_sha256
        or reviewed_sha256 is None
    ):
        return False
    try:
        contents = path.read_bytes()
    except OSError:
        return False
    # Markdown hashing must be stable between Windows CRLF and Linux LF clones.
    canonical_contents = contents.replace(b"\r\n", b"\n")
    digest = hashlib.sha256(canonical_contents).hexdigest()
    if digest != reviewed_sha256:
        return False
    text = contents.decode("utf-8", errors="strict")
    matches = list(PRIVATE_KEY_HEADER.finditer(text))
    if not matches or re.search(
        r"-----END (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----", text, re.I
    ):
        return False
    # Allow only inline prose markers. A PEM header at a line boundary or
    # with no prose following it is treated as possible key material.
    for match in matches:
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        if line_end < 0:
            line_end = len(text)
        line_tail = text[match.end() : line_end]
        if (
            not text[line_start : match.start()].strip()
            or not line_tail.strip()
            or re.search(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{24,}={0,2}(?![A-Za-z0-9+/=])", line_tail)
        ):
            return False
    return True


def scan_signing_material(
    repository_root: Path,
    paths: Iterable[Path],
    document_allowlist: dict[str, dict[str, str]] | None = None,
) -> list[Finding]:
    """Inspect explicit source paths; return codes only, never matched values."""
    root = repository_root.resolve(strict=True)
    allowlist = document_allowlist or {}
    findings: list[Finding] = []
    for supplied in paths:
        path = supplied if supplied.is_absolute() else root / supplied
        try:
            resolved_path = path.resolve(strict=True)
            resolved_path.relative_to(root)
            if _is_link_or_junction(path):
                findings.append(Finding("SIGNING_SCAN_LINK_INPUT"))
                continue
            if not path.is_file():
                continue
            relative = _relative_posix(resolved_path, root)
            if relative is None:
                findings.append(Finding("SIGNING_SCAN_OUTSIDE_REPOSITORY"))
                continue
            suffix = path.suffix.casefold()
            name = path.name.casefold()
            if suffix in SIGNING_MATERIAL_SUFFIXES:
                findings.append(Finding("APPLE_SIGNING_MATERIAL_FILENAME"))
                continue
            if suffix not in SIGNING_TEXT_SUFFIXES:
                continue
            contents = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError):
            findings.append(Finding("SIGNING_SCAN_UNREADABLE"))
            continue

        # Filename checks use only explicit private-key phrases, so ordinary
        # names such as private_key_policy.md do not trigger this guard.
        if re.search(
            r"(?:^|[._-])(?:apple[-_.]?signing|distribution[-_.]?key|private[-_.]?key)(?:[._-]|$)",
            name,
        ):
            findings.append(Finding("APPLE_SIGNING_MATERIAL_FILENAME"))
            continue
        if PRIVATE_KEY_HEADER.search(contents) and not _matches_reviewed_public_document(
            path, relative, allowlist
        ):
            findings.append(Finding("PRIVATE_KEY_BLOCK_PRESENT"))
            continue
        for match in SECRET_ASSIGNMENT.finditer(contents):
            value = match.group(2) or match.group(3) or ""
            marker = value.upper()
            if (
                "EXAMPLE" in marker
                or "TEST" in marker
                or "REDACTED" in marker
                or "PLACEHOLDER" in marker
            ):
                continue
            if value.startswith("<") and value.endswith(">"):
                continue
            if value.startswith("$") or marker in {"NONE", "NULL", "OS.ENVIRON", "ENV_VAR"}:
                continue
            if re.fullmatch(r"[A-Z_][A-Z0-9_]*(?:\.[A-Z_][A-Z0-9_]*)*", marker):
                continue
            if any(character in value for character in "\\[](){}"):
                continue
            findings.append(Finding("DIRECT_SECRET_ASSIGNMENT"))
            break
    return findings


def tracked_source_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise ValueError("GIT_FILE_INVENTORY_FAILED")
    return [root / os.fsdecode(item) for item in result.stdout.split(b"\0") if item]


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
    parser.add_argument(
        "--check-signing-secrets",
        action="store_true",
        help="Scan tracked source for narrow Apple signing/private-key indicators.",
    )
    args = parser.parse_args(argv)
    root = args.repository.resolve()
    if not any(
        (
            args.tracked,
            args.path,
            args.check_workflows,
            args.check_environment,
            args.check_signing_secrets,
        )
    ):
        parser.error("select at least one scan or check")
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
    if args.check_signing_secrets:
        try:
            allowlist = _load_signing_document_allowlist(root)
            findings.extend(scan_signing_material(root, tracked_source_paths(root), allowlist))
        except (OSError, ValueError):
            findings.append(Finding("SIGNING_SCAN_INCOMPLETE"))
    return _report(findings)


if __name__ == "__main__":
    sys.exit(main())
