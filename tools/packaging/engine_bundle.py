"""Fetch, verify and stage the pinned COLMAP/OpenMVS engine bundle (PL-0444).

Archives are downloaded into a cache outside Git, verified against the pinned
sha256 in ``engine_bundle_manifest.json``, extracted, and staged as
``<dest>/colmap/...`` and ``<dest>/openmvs/...`` with license texts and a
per-file sha256 record (``packlab-engine-bundle.json``). Used by the Windows
build workflow (dest = frozen app dir/engines) and the OwnerDev refresh
(dest = OwnerDev/engines).
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "tools" / "packaging" / "engine_bundle_manifest.json"
RECORD_NAME = "packlab-engine-bundle.json"
METERED_HOTSPOT_PREFIX = "172.20.10."


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    for engine in manifest["engines"]:
        if not engine["url"].startswith("https://github.com/"):
            raise ValueError(f"{engine['id']}: archive URL must be an https GitHub release")
        if len(engine["archive_sha256"]) != 64:
            raise ValueError(f"{engine['id']}: archive sha256 is not pinned")
    return manifest


def assert_unmetered_network() -> None:
    """Refuse downloads while the owner's iPhone hotspot (172.20.10.x) is attached."""

    if os.name != "nt":
        return
    output = subprocess.run(["ipconfig"], capture_output=True, text=True, check=True).stdout
    if METERED_HOTSPOT_PREFIX in output:
        raise RuntimeError(
            "Refusing to download engines: a 172.20.10.x (metered hotspot) interface is active"
        )


def verify_archive(path: Path, engine: dict[str, Any]) -> None:
    actual = sha256_file(path)
    if actual != engine["archive_sha256"]:
        raise ValueError(
            f"{engine['id']}: archive sha256 {actual} does not match pinned {engine['archive_sha256']}"
        )


def fetch_archive(engine: dict[str, Any], cache: Path, seed_dirs: list[Path]) -> Path:
    archive = cache / "archives" / engine["archive_name"]
    if not archive.is_file():
        archive.parent.mkdir(parents=True, exist_ok=True)
        seed = next(
            (
                d / engine["archive_name"]
                for d in seed_dirs
                if (d / engine["archive_name"]).is_file()
            ),
            None,
        )
        partial = archive.with_suffix(".partial")
        if seed is not None:
            shutil.copyfile(seed, partial)
        else:
            assert_unmetered_network()
            request = Request(engine["url"], headers={"User-Agent": "packlab-engine-bundle"})
            with urlopen(request, timeout=120) as response, partial.open("wb") as out:  # noqa: S310
                shutil.copyfileobj(response, out, 1 << 20)
        try:
            verify_archive(partial, engine)
        except ValueError:
            partial.unlink()
            raise
        partial.replace(archive)
    verify_archive(archive, engine)
    return archive


def _excluded(name: str, engine: dict[str, Any]) -> bool:
    return any(
        fnmatch.fnmatch(name.casefold(), pattern.casefold()) for pattern in engine["exclude_globs"]
    )


def extract_archive(archive: Path, engine: dict[str, Any], destination: Path) -> int:
    """Extract archive members under ``archive_subdir`` (minus excludes) into destination."""

    prefix = PurePosixPath(engine["archive_subdir"]) if engine["archive_subdir"] else None
    count = 0
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            if member.is_dir():
                continue
            name = PurePosixPath(member.filename.replace("\\", "/"))
            if name.is_absolute() or ".." in name.parts or ":" in member.filename:
                raise ValueError(f"{engine['id']}: unsafe archive member {member.filename!r}")
            if prefix is not None:
                if name.parts[: len(prefix.parts)] != prefix.parts:
                    continue
                name = PurePosixPath(*name.parts[len(prefix.parts) :])
            if _excluded(name.name, engine):
                continue
            target = destination / Path(*name.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as source, target.open("wb") as out:
                shutil.copyfileobj(source, out, 1 << 20)
            count += 1
    if count == 0:
        raise ValueError(
            f"{engine['id']}: archive produced no files under {engine['archive_subdir']!r}"
        )
    return count


def _record_matches(dest: Path, manifest: dict[str, Any]) -> bool:
    record_path = dest / RECORD_NAME
    if not record_path.is_file():
        return False
    record = json.loads(record_path.read_text(encoding="utf-8"))
    wanted = {(e["id"], e["version"], e["archive_sha256"]) for e in manifest["engines"]}
    if {(e["id"], e["version"], e["archive_sha256"]) for e in record.get("engines", [])} != wanted:
        return False
    return all(
        (dest / item["relative_path"]).is_file()
        and sha256_file(dest / item["relative_path"]) == item["sha256"]
        for item in record["files"]
    )


def stage_bundle(
    cache: Path,
    dest: Path,
    seed_dirs: list[Path] | None = None,
    manifest: dict[str, Any] | None = None,
) -> str:
    """Stage every pinned engine into ``dest``; returns "UP_TO_DATE" or "STAGED"."""

    manifest = manifest or load_manifest()
    if _record_matches(dest, manifest):
        return "UP_TO_DATE"
    staging = dest.with_name(dest.name + ".staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    files: list[dict[str, str]] = []
    for engine in manifest["engines"]:
        archive = fetch_archive(engine, cache, seed_dirs or [])
        engine_root = staging / engine["id"]
        extract_archive(archive, engine, engine_root)
        for relative in engine["executables"].values():
            if not (engine_root / relative).is_file():
                raise ValueError(
                    f"{engine['id']}: expected executable {relative} missing from archive"
                )
        for license_file in engine["license_files"]:
            source = PROJECT_ROOT / license_file["path"]
            if sha256_file(source) != license_file["sha256"]:
                raise ValueError(
                    f"{engine['id']}: license text {license_file['path']} digest mismatch"
                )
            target = engine_root / "LICENSES" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for path in sorted(p for p in engine_root.rglob("*") if p.is_file()):
            files.append(
                {
                    "relative_path": path.relative_to(staging).as_posix(),
                    "sha256": sha256_file(path),
                    "component_id": engine["component_id"],
                }
            )
    record = {
        "schema_version": 1,
        "engines": [
            {
                key: engine[key]
                for key in (
                    "id",
                    "component_id",
                    "version",
                    "url",
                    "archive_sha256",
                    "license_identifier",
                )
            }
            for engine in manifest["engines"]
        ],
        "files": files,
    }
    (staging / RECORD_NAME).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if dest.exists():
        shutil.rmtree(dest)
    staging.replace(dest)
    return "STAGED"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True, help="archive cache outside Git")
    parser.add_argument("--dest", type=Path, required=True, help="engines/ folder to stage into")
    parser.add_argument(
        "--seed-dir",
        type=Path,
        action="append",
        default=[],
        help="folder already holding pinned archives (no download)",
    )
    args = parser.parse_args(argv)
    status = stage_bundle(args.cache.resolve(), args.dest.resolve(), args.seed_dir)
    print(f"ENGINE_BUNDLE_{status} {args.dest.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
