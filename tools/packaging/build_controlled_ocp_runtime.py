"""Build a minimal PackLab OCP/OCCT runtime from verified pinned sources."""

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
from collections import deque
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.validate_windows_native_source_lock import load_source_lock

OCP_SOURCE_ID = "ocp-source-7.9.3.1.1"
OCP_PYWRAP_SOURCE_ID = "ocp-pywrap-source-9251940"
OCCT_SOURCE_ID = "occt-source-7.9.3"
SOURCE_IDS = (OCP_SOURCE_ID, OCP_PYWRAP_SOURCE_ID, OCCT_SOURCE_ID)
WINDOWS_SDK_VERSION = "10.0.26100.0"
DEFAULT_BINDGEN_WORKERS = 4
DEFAULT_CMAKE_PARALLEL = 4
SYSTEM_DLLS = {
    "advapi32.dll",
    "bcrypt.dll",
    "comctl32.dll",
    "comdlg32.dll",
    "dwmapi.dll",
    "gdi32.dll",
    "imm32.dll",
    "kernel32.dll",
    "kernelbase.dll",
    "msvcp140.dll",
    "ntdll.dll",
    "ole32.dll",
    "oleaut32.dll",
    "python312.dll",
    "shell32.dll",
    "user32.dll",
    "ucrtbase.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
    "msvcp140_1.dll",
    "version.dll",
    "winmm.dll",
    "ws2_32.dll",
}


def run(command: list[str], *, cwd: Path | None = None) -> None:
    print("RUN " + " ".join(command), flush=True)
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode:
        raise RuntimeError(f"Build command failed with exit code {result.returncode}")


def timed_run(
    phase: str,
    command: list[str],
    timings: list[dict[str, Any]],
    *,
    cwd: Path | None = None,
    workers: int | None = None,
) -> None:
    started = datetime.now(UTC)
    start = time.monotonic()
    worker_detail = f" workers={workers}" if workers is not None else ""
    print(
        f"CONTROLLED_OCP_PHASE_START phase={phase}{worker_detail} utc={started.isoformat()}",
        flush=True,
    )
    run(command, cwd=cwd)
    ended = datetime.now(UTC)
    elapsed = time.monotonic() - start
    timings.append(
        {
            "phase": phase,
            "started_utc": started.isoformat(),
            "ended_utc": ended.isoformat(),
            "duration_seconds": round(elapsed, 3),
            "worker_count": workers,
        }
    )
    print(
        f"CONTROLLED_OCP_PHASE_END phase={phase}{worker_detail} "
        f"utc={ended.isoformat()} duration_seconds={elapsed:.3f}",
        flush=True,
    )


def extract_archive(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:*") as source:
        members = source.getmembers()
        for member in members:
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Pinned source archive contains an unsafe path")
        source.extractall(destination, members=members, filter="data")
    roots = [path for path in destination.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise ValueError("Pinned source archive does not have one expected source root")
    return roots[0]


def pe_imports(path: Path) -> set[str]:
    try:
        import lief
    except ImportError as error:
        raise RuntimeError(
            "The exact locked LIEF dependency is required for OCP minimization"
        ) from error
    binary = lief.PE.parse(str(path))
    if binary is None:
        raise ValueError(f"A staged OCP native input is not a readable PE file: {path.name}")
    return {item.name.casefold() for item in binary.imports}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def windows_sdk_gl_include_dir() -> tuple[Path, str]:
    sdk_root = os.environ.get("CMAKE_WINDOWS_KITS_10_DIR")
    if not sdk_root:
        program_files_x86 = os.environ.get("ProgramFiles(x86)")
        if not program_files_x86:
            raise RuntimeError("The Windows Kits root is unavailable to the OCP build")
        sdk_root = str(Path(program_files_x86) / "Windows Kits" / "10")
    include_dir = Path(sdk_root) / "Include" / WINDOWS_SDK_VERSION / "um"
    if not (include_dir / "gl" / "GL.h").is_file():
        raise RuntimeError("The selected Windows SDK does not contain the OpenGL GL.h header")
    return include_dir, WINDOWS_SDK_VERSION


def find_generated_binding(ocp_build: Path, native_build: Path) -> tuple[Path, Path]:
    """Return pywrap's generated sources and the separately built extension."""
    generated_package = ocp_build / "OCP"
    if not generated_package.is_dir() or not any(generated_package.glob("*.cpp")):
        raise ValueError("The pinned pywrap target did not produce generated OCP C++ sources")
    bindings = sorted(path for path in native_build.rglob("OCP*.pyd") if path.is_file())
    if len(bindings) != 1 or not bindings[0].stem.startswith("OCP."):
        raise ValueError("The generated OCP project did not produce one unambiguous Python binding")
    return generated_package, bindings[0]


def is_external_runtime(name: str) -> bool:
    if name in SYSTEM_DLLS or name.startswith(("api-ms-win-", "ext-ms-win-")):
        return True
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    return (system_root / name).is_file()


def build_runtime(args: argparse.Namespace) -> dict[str, Any]:
    contract = json.loads(args.build_contract.read_text(encoding="utf-8"))
    if contract.get("ocp_bindgen_workers") != args.bindgen_workers:
        raise ValueError("The bindgen worker count differs from the checked-in build contract")
    if contract.get("cmake_parallel") != args.cmake_parallel:
        raise ValueError("CMake parallelism differs from the checked-in build contract")
    lock_path = args.lock.resolve()
    lock = load_source_lock(lock_path)
    records = {record["id"]: record for record in lock["records"]}
    timings: list[dict[str, Any]] = []
    if any(source_id not in records for source_id in SOURCE_IDS):
        raise ValueError("The controlled OCP source records are missing from the source lock")
    archive_paths = {
        record_id: next(args.source_root.glob(f"{record_id}--*")) for record_id in SOURCE_IDS
    }
    for record_id, archive in archive_paths.items():
        if sha256(archive) != records[record_id]["sha256"]:
            raise ValueError(f"Verified-source digest changed before build: {record_id}")

    extracted = args.build_root / "source"
    shutil.rmtree(extracted / "ocp", ignore_errors=True)
    shutil.rmtree(extracted / "pywrap", ignore_errors=True)
    shutil.rmtree(extracted / "occt", ignore_errors=True)
    ocp_source = extract_archive(archive_paths[OCP_SOURCE_ID], extracted / "ocp")
    pywrap_source = extract_archive(archive_paths[OCP_PYWRAP_SOURCE_ID], extracted / "pywrap")
    occt_source = extract_archive(archive_paths[OCCT_SOURCE_ID], extracted / "occt")
    # The OCP source archive preserves the pywrap gitlink as an empty directory.
    # Populate that exact pinned submodule path before configuring CMake.
    shutil.rmtree(ocp_source / "pywrap", ignore_errors=True)
    shutil.copytree(pywrap_source, ocp_source / "pywrap")
    windows_gl_include, windows_sdk_version = windows_sdk_gl_include_dir()
    occt_prefix = args.build_root / "occt-install"
    occt_build = args.build_root / "occt-build"
    ocp_build = args.build_root / "ocp-build"
    native_build = args.build_root / "ocp-native-build"
    for path in (occt_prefix, occt_build, ocp_build, native_build):
        if path.exists():
            shutil.rmtree(path)

    generator = "Visual Studio 17 2022"
    run(
        [
            "cmake",
            "-S",
            str(occt_source),
            "-B",
            str(occt_build),
            "-G",
            generator,
            "-A",
            "x64",
            f"-DCMAKE_SYSTEM_VERSION={WINDOWS_SDK_VERSION}",
            f"-DCMAKE_INSTALL_PREFIX={occt_prefix}",
            "-DBUILD_LIBRARY_TYPE=Shared",
            "-DBUILD_DOC_Overview=OFF",
            "-DBUILD_DOC_RefMan=OFF",
            "-DBUILD_SAMPLES_MFC=OFF",
            "-DBUILD_SAMPLES_QT=OFF",
            "-DBUILD_Inspector=OFF",
            "-DUSE_TK=OFF",
            "-DUSE_VTK=OFF",
            "-DUSE_TBB=OFF",
            "-DUSE_FREETYPE=OFF",
            "-DUSE_FREEIMAGE=OFF",
            "-DUSE_OPENGL=OFF",
            "-DUSE_FFMPEG=OFF",
            "-DUSE_OPENVR=OFF",
            "-DUSE_RAPIDJSON=OFF",
            "-DUSE_DRACO=OFF",
            "-DUSE_EIGEN=OFF",
            "-DBUILD_WITH_DEBUG=OFF",
            "-DBUILD_USE_PCH=OFF",
        ]
    )
    timed_run(
        "occt_native_build",
        [
            "cmake",
            "--build",
            str(occt_build),
            "--config",
            "Release",
            "--parallel",
            str(args.cmake_parallel),
        ],
        timings,
        workers=args.cmake_parallel,
    )
    run(["cmake", "--install", str(occt_build), "--config", "Release"])

    occt_dlls = [path for path in occt_prefix.rglob("*.dll") if path.is_file()]
    if not occt_dlls:
        raise ValueError("The controlled OCCT build produced no installable runtime DLLs")
    occt_dll_by_name = {path.name.casefold(): path for path in occt_dlls}
    if len(occt_dll_by_name) != len(occt_dlls):
        raise ValueError("The controlled OCCT runtime contains duplicate DLL basenames")
    occt_dll_directory = occt_dlls[0].parent
    if any(path.parent != occt_dll_directory for path in occt_dlls):
        raise ValueError("The controlled OCCT DLL install is not a single flat runtime directory")

    run(
        [
            "cmake",
            "-S",
            str(ocp_source),
            "-B",
            str(ocp_build),
            "-G",
            generator,
            "-A",
            "x64",
            f"-DCMAKE_SYSTEM_VERSION={WINDOWS_SDK_VERSION}",
            f"-DOCCT_LIB_DIR={occt_dll_directory}",
            f"-DCMAKE_PREFIX_PATH={occt_prefix}",
            f"-DPython_EXECUTABLE={sys.executable}",
            f"-DN_PROC={args.bindgen_workers}",
            # CMake 3.31's FindOpenGL leaves OPENGL_INCLUDE_DIR empty on
            # Windows even though GL/gl.h is supplied by the selected SDK.
            # OCP's pinned CMakeLists interpolates OPENGL_INCLUDE_DIRS into
            # repeated pywrap -i options, so bind the exact SDK include path.
            f"-DOPENGL_INCLUDE_DIR={windows_gl_include}",
        ]
    )
    timed_run(
        "pywrap_generation",
        [
            "cmake",
            "--build",
            str(ocp_build),
            "--config",
            "Release",
            "--target",
            "pywrap",
            "--parallel",
            str(args.cmake_parallel),
        ],
        timings,
        workers=args.bindgen_workers,
    )
    generated_cmake = ocp_build / "OCP" / "CMakeLists.txt"
    if not generated_cmake.is_file():
        raise ValueError("The pinned pywrap target did not produce its OCP CMake project")
    run(
        [
            "cmake",
            "-S",
            str(generated_cmake.parent),
            "-B",
            str(native_build),
            "-G",
            generator,
            "-A",
            "x64",
            f"-DCMAKE_SYSTEM_VERSION={WINDOWS_SDK_VERSION}",
            f"-DOpenCASCADE_DIR={occt_prefix / 'cmake'}",
            f"-DPython_EXECUTABLE={sys.executable}",
        ]
    )
    timed_run(
        "ocp_native_compile_link",
        [
            "cmake",
            "--build",
            str(native_build),
            "--config",
            "Release",
            "--target",
            "OCP",
            "--parallel",
            str(args.cmake_parallel),
        ],
        timings,
        workers=args.cmake_parallel,
    )

    generated_package, binding_extension = find_generated_binding(ocp_build, native_build)

    required_occt_dll_names: set[str] = set()
    external_runtime_names: set[str] = set()
    pending = deque(pe_imports(binding_extension))
    visited: set[str] = set()
    while pending:
        name = pending.popleft().casefold()
        if name in visited:
            continue
        if is_external_runtime(name):
            external_runtime_names.add(name)
            continue
        visited.add(name)
        dependency = occt_dll_by_name.get(name)
        if dependency is None:
            raise ValueError(f"Controlled OCP dependency is not owned by OCCT or Windows: {name}")
        required_occt_dll_names.add(name)
        pending.extend(pe_imports(dependency))

    package_target = args.site_packages / "OCP"
    if package_target.exists():
        shutil.rmtree(package_target)
    opaque_wheel_libraries = args.site_packages / "cadquery_ocp_novtk.libs"
    if opaque_wheel_libraries.exists():
        shutil.rmtree(opaque_wheel_libraries)
    package_target.mkdir(parents=True)
    for source in generated_package.rglob("*.py"):
        relative = source.relative_to(generated_package)
        destination = package_target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    shutil.copy2(binding_extension, package_target / binding_extension.name)
    (package_target / "__init__.py").write_text(
        "from .OCP import *\nfrom .OCP import __version__\n", encoding="utf-8"
    )
    for name in sorted(required_occt_dll_names):
        shutil.copy2(occt_dll_by_name[name], package_target / name)

    compiler_metadata = next(occt_build.glob("CMakeFiles/*/CMakeCXXCompiler.cmake"), None)
    if compiler_metadata is None:
        raise ValueError("The exact OCCT C++ compiler version could not be identified")
    compiler_config = compiler_metadata.read_text(encoding="utf-8")
    compiler_id = re.search(r'(?m)^set\(CMAKE_CXX_COMPILER_ID "([^"]+)"\)', compiler_config)
    compiler_version_match = re.search(
        r'(?m)^set\(CMAKE_CXX_COMPILER_VERSION "([^"]+)"\)', compiler_config
    )
    if compiler_id is None or compiler_version_match is None:
        raise ValueError("The exact OCCT compiler ID/version could not be identified")
    compiler_version = f"{compiler_id.group(1)} {compiler_version_match.group(1)}"
    cmake_version = subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0]
    if (
        cmake_version != contract["toolchain"]["cmake"]
        or compiler_version != contract["toolchain"]["compiler"]
        or windows_sdk_version != contract["windows_sdk_version"]
        or sys.version.split()[0] != contract["target"]["python_version"]
        or generator != contract["cmake_generator"]
    ):
        raise ValueError("The native build toolchain differs from the checked-in runtime contract")

    file_records = []
    for path in sorted(package_target.iterdir()):
        if path.suffix.casefold() not in {".pyd", ".dll"}:
            continue
        source_id = OCP_SOURCE_ID if path.suffix.casefold() == ".pyd" else OCCT_SOURCE_ID
        source = records[source_id]
        file_records.append(
            {
                "relative_path": f"OCP/{path.name}",
                "sha256": sha256(path),
                "owning_component": source["component"],
                "source_package_id": source_id,
                "version": source["version"],
                "build_revision": source.get("revision", source["build"]),
                "license_identifier": source["license_identifier"],
                "license_notice_source": source["license_notice_source"],
                "production_purpose": "PackLab CAD binding or its transitive OCCT runtime dependency",
            }
        )
    manifest = {
        "schema_version": 1,
        "status": "PASS",
        "input_lock_sha256": sha256(lock_path),
        "ocp_source_revision": records[OCP_SOURCE_ID]["revision"],
        "ocp_pywrap_source_revision": records[OCP_PYWRAP_SOURCE_ID]["revision"],
        "occt_source_revision": records[OCCT_SOURCE_ID]["revision"],
        "toolchain": {
            "python": sys.version.split()[0],
            "cmake": cmake_version,
            "compiler": compiler_version,
            "windows_sdk": windows_sdk_version,
            "ocp_bindgen_workers": args.bindgen_workers,
            "cmake_parallel": args.cmake_parallel,
            "cmake_generator": generator,
        },
        "build_timings": timings,
        "external_runtime_dependencies": sorted(external_runtime_names),
        "files": file_records,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        "CONTROLLED_OCP_RUNTIME_PASS "
        f"binding_extensions=1 occt_dlls={len(required_occt_dll_names)} "
        f"manifest_sha256={sha256(args.manifest)}",
        flush=True,
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lock", type=Path, default=Path("tools/packaging/windows_native_source_lock.json")
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--site-packages", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--build-contract",
        type=Path,
        default=Path("tools/packaging/controlled_ocp_runtime_contract.json"),
    )
    parser.add_argument("--bindgen-workers", type=int, default=DEFAULT_BINDGEN_WORKERS)
    parser.add_argument("--cmake-parallel", type=int, default=DEFAULT_CMAKE_PARALLEL)
    parser.add_argument("--timings", type=Path)
    args = parser.parse_args()
    if args.bindgen_workers != DEFAULT_BINDGEN_WORKERS:
        raise ValueError("The controlled runtime contract requires exactly four pywrap workers")
    if args.cmake_parallel != DEFAULT_CMAKE_PARALLEL:
        raise ValueError("The controlled runtime contract requires CMake parallelism of four")
    manifest = build_runtime(args)
    if args.timings:
        args.timings.parent.mkdir(parents=True, exist_ok=True)
        args.timings.write_text(
            json.dumps(manifest["build_timings"], indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
