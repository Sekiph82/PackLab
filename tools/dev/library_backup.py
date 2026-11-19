"""PL-0412: immutable library backup sets and verified restore into a clean, empty target.

    python -m tools.dev.library_backup backup LIBRARY_ROOT NEW_BACKUP_SET
    python -m tools.dev.library_backup restore BACKUP_SET EMPTY_TARGET [--expect-manifest-sha256 HEX]
    python -m tools.dev.library_backup verify BACKUP_SET RESTORED_ROOT [--expect-manifest-sha256 HEX]

A backup set is ``<set>/manifest.json`` plus ``<set>/data/<library files>``. The file list uses
the PL-0418 ``scan_copy_manifest`` format and its link/junction/unreadable refusal rules. When the
root is a Studio Packaging Library (``packaging-library-state.json``), the manifest also pins the
state revision, audit head, asset/SKU revisions and attachment ids, and verification re-opens the
restored root through the real ``PackagingLibraryAuditStore``/``PackagingLibraryStore`` loaders.

The manifest's self-digest catches accidental corruption only; a deliberate rewrite is caught by
passing the ``manifest_sha256`` recorded off-band (work record) as ``--expect-manifest-sha256``.
Exit codes: 0 PASS, 1 FAIL (report printed), 2 refused precondition. Stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path, PureWindowsPath
from typing import Any

from tools.dev.scan_copy_manifest import _expected, _files, _is_link, create_manifest

CONTRACT = "packlab.library-backup-set.v1"
REPORT_CONTRACT = "packlab.library-restore-verification.v1"
TOOL_VERSION = "1.0.0"
MANIFEST_NAME = "manifest.json"
DATA_DIR = "data"
STATE_FILE = "packaging-library-state.json"
DEFAULT_MAX_FILES = 100_000
DEFAULT_MAX_BYTES = 64 * 1024**3
_MAX_MANIFEST_BYTES = 64 * 1024**2


class LibraryBackupError(ValueError):
    """A refused precondition: nothing was published at the destination."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _absolute(path: str | Path) -> Path:
    return Path(os.path.abspath(path))


def _refuse_linked_parents(path: Path) -> None:
    if any(_is_link(ancestor) for ancestor in path.parents):
        raise LibraryBackupError("path passes through a symlink or junction")


def _check_bounds(root: Path, max_files: int, max_bytes: int) -> None:
    """Cheap lstat pre-walk so an oversized root is refused before anything is hashed."""
    count = total = 0
    try:
        for directory, _, names in os.walk(root, followlinks=False):
            for name in names:
                count += 1
                total += os.lstat(os.path.join(directory, name)).st_size
                if count > max_files:
                    raise LibraryBackupError(f"file count exceeds {max_files}")
                if total > max_bytes:
                    raise LibraryBackupError(f"total bytes exceed {max_bytes}")
    except OSError as error:
        raise LibraryBackupError(f"unreadable entry: {error.filename}") from error


_RESERVED = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"{name}{suffix}" for name in ("COM", "LPT") for suffix in "123456789¹²³"}
)


def _safe_relative(path: str) -> bool:
    """Portable relative POSIX path: no traversal, drives, streams or Windows device names."""
    return (
        path.isprintable()
        and "\\" not in path
        and ":" not in path
        and not PureWindowsPath(path).drive
        and all(
            part not in ("", ".", "..")
            and not part.endswith((".", " "))
            and part.split(".")[0].rstrip(" ").upper() not in _RESERVED
            for part in path.split("/")
        )
    )


def _path_reasons(paths: list[str]) -> list[str]:
    reasons = [f"manifest_path_unsafe: {path!r}" for path in paths if not _safe_relative(path)]
    if len({path.casefold() for path in paths}) != len(paths):
        reasons.append("manifest_path_case_collision")
    return reasons


def _reject_constant(name: str) -> None:
    raise ValueError(f"non-finite JSON constant: {name}")


def _make_parent(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise LibraryBackupError("destination parent is not a creatable folder") from error
    _refuse_linked_parents(path)


def _copy_verified(source: Path, target: Path, size: int, digest: str) -> None:
    """Copy while hashing; a file that changed since it was manifested aborts the copy."""
    target.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    written = 0
    with source.open("rb") as reader, target.open("xb") as writer:
        for chunk in iter(lambda: reader.read(1 << 20), b""):
            hasher.update(chunk)
            written += len(chunk)
            writer.write(chunk)
        writer.flush()
        os.fsync(writer.fileno())
    if (written, hasher.hexdigest()) != (size, digest):
        raise LibraryBackupError(f"file changed during copy: {target.name}")


def _make_read_only(root: Path) -> None:
    for directory, _, names in os.walk(root):
        for name in names:
            os.chmod(os.path.join(directory, name), stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)


def _library_summary(root: Path) -> dict[str, Any] | None:
    """Re-open ``root`` through the real Packaging Library loaders; None when no library state."""
    if not (root / STATE_FILE).is_file():
        return None
    from packlab_studio.packaging_library_audit import PackagingLibraryAuditStore
    from packlab_studio.packaging_library_store import PackagingLibraryStore

    snapshot = PackagingLibraryAuditStore(root).validate()  # replays the audit chain
    assets = {item.asset_id: item.revision_id for item in snapshot.assets}
    skus: dict[str, dict[str, str]] = {}
    for sku in snapshot.skus:
        if sku.packaging_asset_id not in assets:
            raise LibraryBackupError(f"sku {sku.sku_id} binds a missing asset")
        skus[sku.sku_id] = {
            "revision_id": sku.revision_id,
            "packaging_asset_id": sku.packaging_asset_id,
            "packaging_asset_revision_id": sku.packaging_asset_revision_id,
        }
    attachments: list[str] = []
    if (root / "records").is_dir():
        store = PackagingLibraryStore(root)
        for path in sorted((root / "records").iterdir()):
            if path.suffix != ".json":
                raise LibraryBackupError(f"unexpected record file: {path.name}")
            record = store.read_record("packaging-attachment:" + path.stem)
            if not store.verify(record):
                raise LibraryBackupError(f"attachment does not verify: {path.name}")
            attachments.append(record.attachment_id)
    return {
        "state_revision": snapshot.state_revision,
        "audit_head_digest": snapshot.audit_head_digest,
        "asset_revisions": assets,
        "sku_bindings": skus,
        "attachment_ids": attachments,
    }


def create_backup(
    library_root: str | Path,
    backup_set: str | Path,
    *,
    max_files: int = DEFAULT_MAX_FILES,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    """Publish an immutable backup set atomically and return its manifest."""
    if max_files > DEFAULT_MAX_FILES or max_bytes > DEFAULT_MAX_BYTES:
        raise LibraryBackupError("bounds above the restore defaults would make an unrestorable set")
    root, destination = _absolute(library_root), _absolute(backup_set)
    if destination.exists() or _is_link(destination):
        raise LibraryBackupError("backup set already exists and is immutable")
    if destination.is_relative_to(root) or root.is_relative_to(destination):
        raise LibraryBackupError("backup set and library root overlap")
    _check_bounds(root, max_files, max_bytes)
    try:
        files_manifest = create_manifest(root)  # refuses links (incl. ancestors) and unreadables
    except ValueError as error:
        raise LibraryBackupError(str(error)) from error
    unsafe = _path_reasons([entry["path"] for entry in files_manifest["files"]])  # type: ignore[attr-defined]
    if unsafe:
        raise LibraryBackupError(f"library holds names restore would refuse: {unsafe}")
    _make_parent(destination)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.partial-", dir=destination.parent))
    try:
        for entry in files_manifest["files"]:  # type: ignore[attr-defined]
            relative = entry["path"]
            _copy_verified(
                root / relative, staging / DATA_DIR / relative, entry["size"], entry["sha256"]
            )
        # Summarise the staged copy, not the live root, so revisions match the stored bytes.
        try:
            library = _library_summary(staging / DATA_DIR)
        except (ValueError, OSError, RecursionError) as error:
            raise LibraryBackupError(f"library does not load: {error}") from error
        body = {
            "contract": CONTRACT,
            "tool_version": TOOL_VERSION,
            "library": library,
            "files": files_manifest,
        }
        digest = _sha256(body)
        manifest = {**body, "manifest_sha256": digest}
        # The manifest is written last: a staging folder without one never verifies.
        with (staging / MANIFEST_NAME).open("xb") as writer:
            writer.write(_canonical(manifest))
            writer.flush()
            os.fsync(writer.fileno())
        # Self-check with the exact rules restore applies, before anything is published.
        problems = _load_manifest(staging, digest)[2]
        if problems:
            raise LibraryBackupError(f"backup set fails restore checks: {problems}")
        # ponytail: POSIX rename onto a just-created empty dir would succeed; tiny race accepted.
        # Staging lives in the destination parent: a local user who can write there could swap a
        # staging subfolder for a junction mid-copy (documented; hostile local users out of scope).
        os.rename(staging, destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    _make_read_only(destination)
    return manifest


def _load_manifest(
    backup_set: Path, expected_sha256: str | None
) -> tuple[dict[str, Any] | None, dict[str, tuple[int, str]], list[str]]:
    path = backup_set / MANIFEST_NAME
    try:
        if _is_link(backup_set) or _is_link(path) or path.stat().st_size > _MAX_MANIFEST_BYTES:
            return None, {}, ["manifest_unsafe_or_oversized"]
        manifest = json.loads(path.read_bytes(), parse_constant=_reject_constant)
    except (OSError, ValueError, RecursionError):
        return None, {}, ["manifest_unreadable"]
    if not isinstance(manifest, dict) or manifest.get("contract") != CONTRACT:
        return None, {}, ["manifest_contract_invalid"]
    reasons = []
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    digest = _sha256(body)
    if manifest.get("manifest_sha256") != digest:
        reasons.append("manifest_digest_mismatch")
    if expected_sha256 is not None and expected_sha256 != digest:
        reasons.append("manifest_digest_not_expected")
    if manifest.get("tool_version") != TOOL_VERSION:
        reasons.append("manifest_tool_version_unsupported")
    if not (manifest.get("library") is None or isinstance(manifest.get("library"), dict)):
        reasons.append("manifest_library_invalid")
    files = _expected(manifest.get("files"))
    if files is None:
        return manifest, {}, [*reasons, "manifest_files_invalid"]
    reasons += _path_reasons(list(files))
    if len(files) > DEFAULT_MAX_FILES or sum(s for s, _ in files.values()) > DEFAULT_MAX_BYTES:
        reasons.append("manifest_exceeds_bounds")
    return manifest, files, reasons


def _compare(expected: dict[str, tuple[int, str]], root: Path) -> list[str]:
    try:
        actual = _files(root)
    except ValueError as error:
        return [f"unreadable: {error}"]
    extra_by_content: dict[tuple[int, str], list[str]] = {}
    for path in sorted(actual.keys() - expected.keys()):
        extra_by_content.setdefault(actual[path], []).append(path)
    reasons = []
    for path in sorted(expected.keys() - actual.keys()):
        twins = extra_by_content.get(expected[path])
        reasons.append(f"renamed: {path} -> {twins.pop(0)}" if twins else f"missing: {path}")
    reasons += [f"unexpected: {path}" for paths in extra_by_content.values() for path in paths]
    for path in sorted(expected.keys() & actual.keys()):
        (want_size, want_digest), (size, digest) = expected[path], actual[path]
        if size < want_size:
            reasons.append(f"truncated: {path}")
        elif size > want_size:
            reasons.append(f"grown: {path}")
        elif digest != want_digest:
            reasons.append(f"altered: {path}")
    return reasons


def _report(reasons: list[str], manifest: dict[str, Any] | None, semantic: str) -> dict[str, Any]:
    library = (manifest or {}).get("library")
    body = {
        "contract": REPORT_CONTRACT,
        "tool_version": TOOL_VERSION,
        "verdict": "FAIL" if reasons else "PASS",
        "reasons": reasons,
        "manifest_sha256": (manifest or {}).get("manifest_sha256"),
        "library_state_revision": library.get("state_revision")
        if isinstance(library, dict)
        else None,
        "semantic_check": semantic,
    }
    return {**body, "report_sha256": _sha256(body)}


def verify_restored(
    backup_set: str | Path,
    restored_root: str | Path,
    *,
    expected_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    """Byte and semantic verification of a restored root against a backup set's manifest."""
    manifest, files, reasons = _load_manifest(_absolute(backup_set), expected_manifest_sha256)
    if reasons or manifest is None:
        return _report(reasons, manifest, "skipped")
    reasons = _compare(files, _absolute(restored_root))
    if reasons:
        return _report(reasons, manifest, "skipped")
    try:
        summary = _library_summary(_absolute(restored_root))
    except (ValueError, OSError, RecursionError) as error:  # audit/store errors are ValueErrors
        return _report([f"semantic_load_failed: {error}"], manifest, "failed")
    expected = manifest["library"]
    if summary != expected:
        keys = sorted({*(summary or {}), *(expected or {})})
        diff = [k for k in keys if (summary or {}).get(k) != (expected or {}).get(k)]
        return _report([f"semantic_mismatch: {k}" for k in diff or ["library"]], manifest, "failed")
    return _report([], manifest, "library_reopened" if summary else "no_library_state")


def restore_backup(
    backup_set: str | Path,
    target: str | Path,
    *,
    expected_manifest_sha256: str | None = None,
    read_only: bool = True,
) -> dict[str, Any]:
    """Restore into a missing or empty ``target``; nothing is published unless it verifies."""
    source, destination = _absolute(backup_set), _absolute(target)
    if _is_link(destination) or (
        destination.exists() and (not destination.is_dir() or any(destination.iterdir()))
    ):
        raise LibraryBackupError("restore target must be a missing or empty folder")
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise LibraryBackupError("restore target and backup set overlap")
    _make_parent(destination)
    manifest, files, reasons = _load_manifest(source, expected_manifest_sha256)
    if not reasons:
        _check_bounds(source / DATA_DIR, DEFAULT_MAX_FILES, DEFAULT_MAX_BYTES)
        reasons = _compare(files, source / DATA_DIR)  # reject a corrupt set before copying
    if reasons or manifest is None:
        return _report(reasons, manifest, "skipped")
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.restore-", dir=destination.parent))
    try:
        for relative, (size, digest) in files.items():
            _copy_verified(source / DATA_DIR / relative, staging / relative, size, digest)
        report = verify_restored(source, staging, expected_manifest_sha256=expected_manifest_sha256)
        if report["verdict"] != "PASS":
            shutil.rmtree(staging, ignore_errors=True)
            return report
        if destination.exists():
            destination.rmdir()  # still empty; rmdir refuses otherwise
        os.rename(staging, destination)
    except (LibraryBackupError, OSError) as error:
        shutil.rmtree(staging, ignore_errors=True)
        return _report([f"restore_copy_failed: {error}"], manifest, "skipped")
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if read_only:
        _make_read_only(destination)
    return verify_restored(source, destination, expected_manifest_sha256=expected_manifest_sha256)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup")
    backup.add_argument("library", type=Path)
    backup.add_argument("backup_set", type=Path)
    for name in ("restore", "verify"):
        command = commands.add_parser(name)
        command.add_argument("backup_set", type=Path)
        command.add_argument("target", type=Path)
        command.add_argument("--expect-manifest-sha256")
        if name == "restore":
            command.add_argument(
                "--writable", action="store_true", help="leave restored files writable"
            )
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[2]
    sys.path[:0] = [str(repo / "core" / "src"), str(repo / "apps" / "windows-studio" / "src")]
    try:
        if args.command == "backup":
            print(create_backup(args.library, args.backup_set)["manifest_sha256"])
            return 0
        digest = args.expect_manifest_sha256
        if args.command == "restore":
            report = restore_backup(
                args.backup_set,
                args.target,
                expected_manifest_sha256=digest,
                read_only=not args.writable,
            )
        else:
            report = verify_restored(args.backup_set, args.target, expected_manifest_sha256=digest)
    except LibraryBackupError as error:
        print(f"refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
