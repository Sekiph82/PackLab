"""Validate an OCCT SDK checkpoint before a downstream hosted job consumes it."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.build_controlled_occt_sdk import (
    LOCK,
    OCCT_CMAKE_OPTIONS,
    OCCT_ID,
    PARALLELISM,
    SDK_VERSION,
)
from tools.packaging.validate_windows_native_source_lock import load_source_lock

METADATA_NAME = "occt-sdk-metadata.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_sdk(
    directory: Path,
    expected_run_id: str,
    expected_attempt: str,
    expected_cache_key: str,
    *,
    require_opengl: bool = False,
) -> dict[str, Any]:
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("OCCT SDK checkpoint directory is missing or unsafe")
    metadata_path = directory / METADATA_NAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    lock = load_source_lock(LOCK)
    record = next(row for row in lock["records"] if row["id"] == OCCT_ID)
    if (
        metadata.get("schema_version") not in (1, 2)
        or metadata.get("status") != "SEALED"
        or metadata.get("stage") != "occt-sdk"
        or metadata.get("producer_job_id") != "occt-sdk"
        or metadata.get("producer_run_id") != expected_run_id
        or metadata.get("producer_run_attempt") != expected_attempt
        or metadata.get("cache_key") != expected_cache_key
        or metadata.get("source_lock_sha256") != digest(LOCK)
        or metadata.get("occt_source_id") != OCCT_ID
        or metadata.get("occt_source_revision") != record["revision"]
        or metadata.get("occt_source_sha256") != record["sha256"]
        or metadata.get("windows_sdk") != SDK_VERSION
        or metadata.get("python") != "3.12.15"
        or metadata.get("cmake") != "cmake version 3.31.8"
        or metadata.get("compiler") != "MSVC 19.44.35229.0"
        or metadata.get("parallelism") != PARALLELISM
    ):
        raise ValueError(
            "OCCT SDK checkpoint identity differs from this run or the source/toolchain contract"
        )
    if metadata.get("schema_version") == 2 and metadata.get("cmake_options") != OCCT_CMAKE_OPTIONS:
        raise ValueError("OCCT SDK checkpoint CMake option contract differs from the pinned build")
    if require_opengl and (
        metadata.get("schema_version") != 2
        or metadata.get("cmake_options") != OCCT_CMAKE_OPTIONS
        or metadata["cmake_options"].get("USE_OPENGL") is not True
        or metadata["cmake_options"].get("USE_VTK") is not False
    ):
        raise ValueError("OCCT SDK checkpoint must be sealed with USE_OPENGL=ON and USE_VTK=OFF")
    entries = metadata.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("OCCT SDK checkpoint manifest is empty")
    expected: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for entry in entries:
        relative = entry.get("relative_path")
        relative_path = PurePosixPath(relative) if isinstance(relative, str) else None
        if (
            relative_path is None
            or relative_path.is_absolute()
            or ".." in relative_path.parts
            or not SHA256.fullmatch(entry.get("sha256", ""))
            or not isinstance(entry.get("byte_length"), int)
            or entry["byte_length"] < 0
            or relative.casefold() in {name.casefold() for name in expected}
        ):
            raise ValueError("OCCT SDK checkpoint contains an unsafe or duplicate file record")
        expected[relative] = entry
        total_bytes += entry["byte_length"]
    observed: dict[str, Path] = {}
    for sdk_file in directory.rglob("*"):
        if sdk_file.is_symlink():
            raise ValueError("OCCT SDK checkpoint contains a symbolic link")
        if not sdk_file.is_file() or sdk_file == metadata_path:
            continue
        relative = sdk_file.relative_to(directory).as_posix()
        if relative.casefold() in {name.casefold() for name in observed}:
            raise ValueError("OCCT SDK checkpoint contains case-colliding files")
        observed[relative] = sdk_file
    if set(observed) != set(expected):
        raise ValueError("OCCT SDK checkpoint file set differs from its sealed manifest")
    for relative, path in observed.items():
        entry = expected[relative]
        if path.stat().st_size != entry["byte_length"] or digest(path) != entry["sha256"]:
            raise ValueError(f"OCCT SDK checkpoint file failed hash/size verification: {relative}")
    if metadata.get("file_count") != len(expected) or metadata.get("byte_count") != total_bytes:
        raise ValueError("OCCT SDK checkpoint count or byte total differs from its manifest")
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if metadata.get("payload_sha256") != hashlib.sha256(payload).hexdigest():
        raise ValueError("OCCT SDK checkpoint payload digest differs from its file manifest")
    folded = {name.casefold() for name in observed}
    required = {"inc/opengl_context.hxx", "lib/tkopengl.lib", "bin/tkopengl.dll"}
    if not required <= folded and metadata.get("schema_version") == 2:
        raise ValueError("OCCT SDK checkpoint lacks required OpenGL header, import library, or DLL")
    if (
        not any(name.endswith(".dll") for name in folded)
        or not any(name.endswith(".lib") for name in folded)
        or not any("opencascadeconfig.cmake" in name for name in folded)
    ):
        raise ValueError("OCCT SDK checkpoint lacks required runtime, link, or CMake files")
    return metadata


def republish_cached_sdk(
    directory: Path, cache_key: str, current_run_id: str, current_attempt: str
) -> dict[str, Any]:
    metadata_path = directory / METADATA_NAME
    prior = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata = validate_sdk(
        directory,
        prior.get("producer_run_id", ""),
        prior.get("producer_run_attempt", ""),
        cache_key,
    )
    metadata["cache_origin"] = {
        "producer_run_id": metadata["producer_run_id"],
        "producer_run_attempt": metadata["producer_run_attempt"],
    }
    metadata["producer_run_id"] = current_run_id
    metadata["producer_run_attempt"] = current_attempt
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return validate_sdk(directory, current_run_id, current_attempt, cache_key)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", required=True, type=Path)
    parser.add_argument("--expected-run-id", required=True)
    parser.add_argument("--expected-attempt", required=True)
    parser.add_argument("--expected-cache-key", required=True)
    parser.add_argument("--republish-cache", action="store_true")
    args = parser.parse_args()
    if args.republish_cache:
        result = republish_cached_sdk(
            args.sdk, args.expected_cache_key, args.expected_run_id, args.expected_attempt
        )
    else:
        result = validate_sdk(
            args.sdk, args.expected_run_id, args.expected_attempt, args.expected_cache_key
        )
    print(f"CONTROLLED_OCCT_SDK_VALID files={result['file_count']} bytes={result['byte_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
