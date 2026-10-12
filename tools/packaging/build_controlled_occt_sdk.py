"""Build and seal only the locked OCCT SDK for the hosted OCP pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.validate_windows_native_source_lock import load_source_lock

OCCT_ID = "occt-source-7.9.3"
SDK_VERSION = "10.0.26100.0"
PARALLELISM = 4
GENERATOR = "Visual Studio 17 2022"
OCCT_CMAKE_OPTIONS = {
    "BUILD_LIBRARY_TYPE": "Shared",
    "BUILD_DOC_Overview": False,
    "BUILD_DOC_RefMan": False,
    "BUILD_SAMPLES_MFC": False,
    "BUILD_SAMPLES_QT": False,
    "BUILD_Inspector": False,
    "USE_TK": False,
    "USE_VTK": False,
    "USE_TBB": False,
    "USE_FREETYPE": False,
    "USE_FREEIMAGE": False,
    "USE_OPENGL": True,
    "USE_FFMPEG": False,
    "USE_OPENVR": False,
    "USE_RAPIDJSON": False,
    "USE_DRACO": False,
    "USE_EIGEN": False,
    "BUILD_WITH_DEBUG": False,
    "BUILD_USE_PCH": False,
}
CONTRACT = Path("tools/packaging/controlled_ocp_runtime_contract.json")
LOCK = Path("tools/packaging/windows_native_source_lock.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_source(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:*") as source:
        members = source.getmembers()
        for member in members:
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts or member.issym() or member.islnk():
                raise ValueError("locked OCCT source archive contains an unsafe entry")
        source.extractall(destination, members=members, filter="data")
    roots = [path for path in destination.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise ValueError("locked OCCT source archive does not have one source root")
    return roots[0]


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.is_symlink():
            raise ValueError("OCCT SDK cannot contain symbolic links")
        relative = path.relative_to(root).as_posix()
        if relative.casefold() in seen:
            raise ValueError("OCCT SDK has a case-colliding path")
        seen.add(relative.casefold())
        entries.append(
            {"relative_path": relative, "byte_length": path.stat().st_size, "sha256": sha256(path)}
        )
    if not entries:
        raise ValueError("OCCT install tree is empty")
    return entries


def build_sdk(
    source_archive: Path,
    build_root: Path,
    output: Path,
    metadata_path: Path,
    cache_key: str,
) -> dict[str, Any]:
    lock = load_source_lock(LOCK)
    record = next((row for row in lock["records"] if row["id"] == OCCT_ID), None)
    if record is None or sha256(source_archive) != record["sha256"]:
        raise ValueError("OCCT source does not match the checked-in source lock")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if sys.version.split()[0] != contract["target"]["python_version"]:
        raise ValueError("OCCT SDK producer Python differs from the frozen Windows contract")
    if (
        subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0]
        != contract["toolchain"]["cmake"]
    ):
        raise ValueError("OCCT SDK producer CMake differs from the frozen Windows contract")
    source_root = _extract_source(source_archive, build_root / "source")
    install = build_root / "install"
    cmake_build = build_root / "occt-build"
    for path in (install, cmake_build):
        if path.exists():
            shutil.rmtree(path)
    subprocess.run(
        [
            "cmake",
            "-S",
            str(source_root),
            "-B",
            str(cmake_build),
            "-G",
            GENERATOR,
            "-A",
            "x64",
            f"-DCMAKE_SYSTEM_VERSION={SDK_VERSION}",
            f"-DCMAKE_INSTALL_PREFIX={install}",
            *[
                f"-D{key}={'Shared' if value == 'Shared' else 'ON' if value is True else 'OFF'}"
                for key, value in OCCT_CMAKE_OPTIONS.items()
            ],
        ],
        check=True,
    )
    started = datetime.now(UTC)
    clock = time.monotonic()
    subprocess.run(
        [
            "cmake",
            "--build",
            str(cmake_build),
            "--config",
            "Release",
            "--parallel",
            str(PARALLELISM),
        ],
        check=True,
    )
    duration = round(time.monotonic() - clock, 3)
    ended = datetime.now(UTC)
    subprocess.run(["cmake", "--install", str(cmake_build), "--config", "Release"], check=True)
    compiler_config_path = next(cmake_build.glob("CMakeFiles/*/CMakeCXXCompiler.cmake"), None)
    if compiler_config_path is None:
        raise ValueError("OCCT SDK producer cannot identify the C++ compiler")
    compiler_config = compiler_config_path.read_text(encoding="utf-8")
    compiler_id = re.search(r'(?m)^set\(CMAKE_CXX_COMPILER_ID "([^"]+)"\)', compiler_config)
    compiler_version = re.search(
        r'(?m)^set\(CMAKE_CXX_COMPILER_VERSION "([^"]+)"\)', compiler_config
    )
    if compiler_id is None or compiler_version is None:
        raise ValueError("OCCT SDK compiler identity is incomplete")
    compiler = f"{compiler_id.group(1)} {compiler_version.group(1)}"
    if compiler != contract["toolchain"]["compiler"]:
        raise ValueError("OCCT SDK compiler differs from the frozen Windows contract")
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(install, output)
    entries = _file_inventory(output)
    sdk_files = [entry["relative_path"].casefold() for entry in entries]
    required = {"inc/opengl_context.hxx", "lib/tkopengl.lib", "bin/tkopengl.dll"}
    if not required <= set(sdk_files):
        raise ValueError(
            "OCCT install lacks the required OpenGL header, import library, or runtime DLL"
        )
    if not any("opencascadeconfig.cmake" in name for name in sdk_files):
        raise ValueError("OCCT install lacks its exported CMake package")
    producer_run = os.environ.get("GITHUB_RUN_ID", "local-unset")
    producer_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "local-unset")
    metadata = {
        "schema_version": 2,
        "status": "SEALED",
        "stage": "occt-sdk",
        "producer_job_id": "occt-sdk",
        "producer_run_id": producer_run,
        "producer_run_attempt": producer_attempt,
        "cache_key": cache_key,
        "source_lock_sha256": sha256(LOCK),
        "occt_source_id": OCCT_ID,
        "occt_source_revision": record["revision"],
        "occt_source_sha256": record["sha256"],
        "windows_sdk": SDK_VERSION,
        "python": sys.version.split()[0],
        "cmake": subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0],
        "compiler": compiler,
        "parallelism": PARALLELISM,
        "cmake_options": OCCT_CMAKE_OPTIONS,
        "build_started_utc": started.isoformat(),
        "build_ended_utc": ended.isoformat(),
        "build_duration_seconds": duration,
        "file_count": len(entries),
        "byte_count": sum(entry["byte_length"] for entry in entries),
        "files": entries,
    }
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    metadata["payload_sha256"] = hashlib.sha256(payload).hexdigest()
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", required=True, type=Path)
    parser.add_argument("--build-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--cache-key", required=True)
    args = parser.parse_args()
    metadata = build_sdk(
        args.source_archive, args.build_root, args.output, args.metadata, args.cache_key
    )
    print(
        f"CONTROLLED_OCCT_SDK_SEALED files={metadata['file_count']} bytes={metadata['byte_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
