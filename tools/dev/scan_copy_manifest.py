"""PL-0418: SHA-256 manifest for off-machine copies of irreplaceable scan folders.

    python -m tools.dev.scan_copy_manifest create SOURCE_DIR MANIFEST.json
    python -m tools.dev.scan_copy_manifest verify MANIFEST.json COPY_DIR

``verify`` exits 0 only when the copy holds exactly the manifested files with identical
sizes and digests; missing, extra, resized or altered files exit 1. Symlinks and NTFS
junctions (including the copy root) are refused so a copy cannot silently point back at the
source; empty or internally inconsistent manifests are invalid. Stdlib only; read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

CONTRACT = "packlab.scan-copy-manifest.v1"


def _is_link(path: Path) -> bool:
    # NTFS junctions are not symlinks to Path.is_symlink(); check both explicitly.
    return path.is_symlink() or os.path.isjunction(path)


def _files(root: Path) -> dict[str, tuple[int, str]]:
    if _is_link(root):
        raise ValueError("root is a symlink or junction")
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    entries: dict[str, tuple[int, str]] = {}
    for directory, subdirectories, filenames in os.walk(root, followlinks=False):
        here = Path(directory)
        for name in sorted(subdirectories + filenames):
            path = here / name
            if _is_link(path):
                raise ValueError(f"link refused: {path.relative_to(root).as_posix()}")
        for name in sorted(filenames):
            path = here / name
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(chunk)
            entries[path.relative_to(root).as_posix()] = (path.stat().st_size, digest.hexdigest())
    return dict(sorted(entries.items()))


def _expected(manifest: object) -> dict[str, tuple[int, str]] | None:
    if not isinstance(manifest, dict) or manifest.get("contract") != CONTRACT:
        return None
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        return None
    expected: dict[str, tuple[int, str]] = {}
    for item in files:
        if not isinstance(item, dict):
            return None
        path, size, digest = item.get("path"), item.get("size"), item.get("sha256")
        if (
            not isinstance(path, str)
            or not path
            or path in expected
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
            or not isinstance(digest, str)
            or len(digest) != 64
        ):
            return None
        expected[path] = (size, digest)
    if manifest.get("file_count") != len(expected) or manifest.get("total_bytes") != sum(
        size for size, _ in expected.values()
    ):
        return None
    return expected


def create_manifest(source: Path) -> dict[str, object]:
    files = _files(source)
    if not files:
        raise ValueError("source folder holds no files")
    return {
        "contract": CONTRACT,
        "file_count": len(files),
        "total_bytes": sum(size for size, _ in files.values()),
        "files": [{"path": p, "size": s, "sha256": d} for p, (s, d) in files.items()],
    }


def verify_copy(manifest: dict[str, object], copy_root: Path) -> list[str]:
    """Return problems as stable strings; an empty list means the copy is identical."""
    expected = _expected(manifest)
    if expected is None:
        return ["manifest_invalid"]
    try:
        actual = _files(copy_root)
    except ValueError as error:
        return [f"copy_unreadable: {error}"]
    problems = [f"missing: {path}" for path in sorted(expected.keys() - actual.keys())]
    problems += [f"unexpected: {path}" for path in sorted(actual.keys() - expected.keys())]
    problems += [
        f"altered: {path}"
        for path in sorted(expected.keys() & actual.keys())
        if expected[path] != actual[path]
    ]
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("source", type=Path)
    create.add_argument("manifest", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("manifest", type=Path)
    verify.add_argument("copy", type=Path)
    args = parser.parse_args(argv)
    if args.command == "create":
        if args.manifest.exists():
            print("refusing to overwrite an existing manifest", file=sys.stderr)
            return 2
        args.manifest.write_text(
            json.dumps(create_manifest(args.source), indent=1, sort_keys=True), encoding="utf-8"
        )
        return 0
    problems = verify_copy(json.loads(args.manifest.read_text(encoding="utf-8")), args.copy)
    for problem in problems:
        print(problem)
    print("SCAN_COPY_VERIFY_PASS" if not problems else "SCAN_COPY_VERIFY_FAIL")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
