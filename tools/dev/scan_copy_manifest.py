"""PL-0418: SHA-256 manifest for off-machine copies of irreplaceable scan folders.

    python -m tools.dev.scan_copy_manifest create SOURCE_DIR MANIFEST.json
    python -m tools.dev.scan_copy_manifest verify MANIFEST.json COPY_DIR

``verify`` exits 0 only when the copy holds exactly the manifested files with identical
sizes and digests; missing, extra, resized or altered files exit 1. Symlinks are refused so
a copy cannot silently point back at the source. Stdlib only; read-only on both trees.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

CONTRACT = "packlab.scan-copy-manifest.v1"


def _files(root: Path) -> dict[str, tuple[int, str]]:
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    entries: dict[str, tuple[int, str]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink refused: {path.relative_to(root).as_posix()}")
        if path.is_file():
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(chunk)
            entries[path.relative_to(root).as_posix()] = (path.stat().st_size, digest.hexdigest())
    return entries


def create_manifest(source: Path) -> dict[str, object]:
    files = _files(source)
    return {
        "contract": CONTRACT,
        "file_count": len(files),
        "total_bytes": sum(size for size, _ in files.values()),
        "files": [{"path": p, "size": s, "sha256": d} for p, (s, d) in files.items()],
    }


def verify_copy(manifest: dict[str, object], copy_root: Path) -> list[str]:
    """Return problems as stable strings; an empty list means the copy is identical."""
    files = manifest.get("files")
    if manifest.get("contract") != CONTRACT or not isinstance(files, list):
        return ["manifest_invalid"]
    expected = {item["path"]: (item["size"], item["sha256"]) for item in files}
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
