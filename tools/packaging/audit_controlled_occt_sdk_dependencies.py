"""Audit the 315 generated OCP translation units against a sealed OCCT SDK."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tarfile
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.build_controlled_occt_sdk import LOCK, OCCT_ID, SDK_VERSION, sha256
from tools.packaging.prepare_official_ocp_generated_sources import prepare_generated_sources
from tools.packaging.validate_controlled_occt_sdk import validate_sdk
from tools.packaging.validate_windows_native_source_lock import load_source_lock

INCLUDE = re.compile(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]", re.MULTILINE)
TARGET = re.compile(r"\bTK[A-Za-z0-9_]+\b")
MODULES = 315
UNITS = 2 * MODULES


def sdk_dependency_deficiencies(
    missing_headers: dict[str, set[str]], required_toolkits: set[str], file_names: set[str]
) -> tuple[list[str], list[str]]:
    """Return every required toolkit import LIB and runtime DLL absent from the SDK."""
    libraries = [
        f"{toolkit}.lib"
        for toolkit in sorted(required_toolkits)
        if f"{toolkit}.lib".casefold() not in file_names
    ]
    runtimes = [
        f"{toolkit}.dll"
        for toolkit in sorted(required_toolkits)
        if f"{toolkit}.dll".casefold() not in file_names
    ]
    if "opengl_context.hxx" in {key.split("/")[-1].casefold() for key in missing_headers}:
        if "tkopengl" not in {name.casefold() for name in required_toolkits}:
            required_toolkits.add("TKOpenGl")
        if "TKOpenGl.lib" not in libraries and "tkopengl.lib" not in file_names:
            libraries.append("TKOpenGl.lib")
        if "TKOpenGl.dll" not in runtimes and "tkopengl.dll" not in file_names:
            runtimes.append("TKOpenGl.dll")
    return sorted(set(libraries)), sorted(set(runtimes))


def windows_opengl_prerequisites(sdk_root: Path, version: str) -> dict[str, Any]:
    include = sdk_root / "Include" / version / "um" / "GL" / "gl.h"
    library = sdk_root / "Lib" / version / "um" / "x64" / "opengl32.lib"
    runtime = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "opengl32.dll"
    result = {
        "windows_sdk_root": str(sdk_root),
        "windows_sdk_version": version,
        "gl_header": str(include),
        "opengl32_import_library": str(library),
        "opengl32_system_runtime": str(runtime),
        "gl_header_present": include.is_file(),
        "opengl32_import_library_present": library.is_file(),
        "opengl32_system_runtime_present": runtime.is_file(),
    }
    if not all(
        result[key]
        for key in (
            "gl_header_present",
            "opengl32_import_library_present",
            "opengl32_system_runtime_present",
        )
    ):
        raise ValueError(
            "Windows 2022 SDK is missing required OpenGL system headers/library/runtime"
        )
    return result


def ensure_sdk_dependencies_complete(
    missing_headers: dict[str, set[str]], missing_libraries: list[str], missing_runtimes: list[str]
) -> None:
    if missing_headers or missing_libraries or missing_runtimes:
        raise DependencyAuditError(
            {
                "missing_occt_headers": {
                    key: sorted(value) for key, value in sorted(missing_headers.items())
                },
                "missing_import_libraries": sorted(missing_libraries),
                "missing_runtime_dlls": sorted(missing_runtimes),
            }
        )


def compile_opengl_sdk_probe(
    sdk: Path, work_root: Path, timeout_seconds: int = 180
) -> dict[str, Any]:
    config = next(sdk.rglob("OpenCASCADEConfig.cmake"), None)
    if config is None:
        raise ValueError("OpenGL SDK probe cannot find OpenCASCADEConfig.cmake")
    source = work_root / "opengl-sdk-probe.cxx"
    source.write_text('#include "OpenGl_Context.hxx"\nint main() { return 0; }\n', encoding="utf-8")
    cmake_lists = work_root / "CMakeLists.txt"
    cmake_lists.write_text(
        "\n".join(
            (
                "cmake_minimum_required(VERSION 3.20)",
                "project(PackLabOpenGlSdkProbe LANGUAGES CXX)",
                "find_package(OpenCASCADE REQUIRED CONFIG)",
                "add_executable(packlab_opengl_sdk_probe opengl-sdk-probe.cxx)",
                "target_include_directories(packlab_opengl_sdk_probe PRIVATE ${OpenCASCADE_INCLUDE_DIR})",
                "target_link_libraries(packlab_opengl_sdk_probe PRIVATE ${OpenCASCADE_LIBRARIES} opengl32)",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    build = work_root / "opengl-sdk-probe-build"
    commands = (
        [
            "cmake",
            "-S",
            str(work_root),
            "-B",
            str(build),
            "-G",
            "Visual Studio 17 2022",
            "-A",
            "x64",
            f"-DCMAKE_SYSTEM_VERSION={SDK_VERSION}",
            f"-DOpenCASCADE_DIR={config.parent}",
        ],
        ["cmake", "--build", str(build), "--config", "Release", "--parallel", "4"],
    )
    output = []
    for command in commands:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        output.append(result.stdout + result.stderr)
        if result.returncode != 0:
            raise ValueError(
                "real OpenGl_Context.hxx compile/link probe failed: "
                + (result.stdout + result.stderr)[-4000:]
            )
    executable = build / "Release" / "packlab_opengl_sdk_probe.exe"
    if not executable.is_file():
        raise ValueError("OpenGL SDK compile/link probe succeeded without producing its executable")
    return {
        "status": "PASS",
        "header": "OpenGl_Context.hxx",
        "link_closure": "OpenCASCADE_LIBRARIES + opengl32",
        "executable_bytes": executable.stat().st_size,
        "log_tail": "\n".join(output)[-2000:],
    }


def extract_occt_source(archive: Path, destination: Path) -> Path:
    lock = load_source_lock(LOCK)
    record = next(row for row in lock["records"] if row["id"] == OCCT_ID)
    if sha256(archive) != record["sha256"]:
        raise ValueError("OCCT source archive differs from the pinned source lock")
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, "r:*") as source:
        members = source.getmembers()
        names: set[str] = set()
        total = 0
        for member in members:
            path = PurePosixPath(member.name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or member.issym()
                or member.islnk()
                or member.isdev()
                or member.name.casefold() in names
            ):
                raise ValueError("locked OCCT source archive contains an unsafe or duplicate entry")
            names.add(member.name.casefold())
            total += max(member.size, 0)
            if total > 500_000_000:
                raise ValueError(
                    "locked OCCT source archive exceeds the bounded 500 MB extraction limit"
                )
        source.extractall(destination, members=members, filter="data")
    roots = [path for path in destination.iterdir() if path.is_dir()]
    if len(roots) != 1 or not (roots[0] / "src").is_dir():
        raise ValueError("locked OCCT source archive does not contain one recognizable source root")
    return roots[0]


def audit_dependencies(
    sdk: Path,
    generated_source_zip: Path,
    occt_source_archive: Path,
    work_root: Path,
    *,
    expected_run_id: str,
    expected_attempt: str,
    expected_cache_key: str,
    require_opengl: bool = False,
) -> dict[str, Any]:
    metadata = validate_sdk(
        sdk,
        expected_run_id,
        expected_attempt,
        expected_cache_key,
        require_opengl=require_opengl,
    )
    if work_root.exists():
        raise ValueError("dependency audit work root must not already exist")
    work_root.mkdir(parents=True)
    generated_root = work_root / "generated"
    generated_manifest = work_root / "generated-manifest.json"
    patched = prepare_generated_sources(generated_source_zip, generated_root, generated_manifest)
    source_root = extract_occt_source(occt_source_archive, work_root / "occt-source")
    binding_root = generated_root / "OCP_src_stubs_Windows"
    units = sorted(
        [path for path in binding_root.glob("*.cpp") if not path.name.endswith("_pre.cpp")]
        + list(binding_root.glob("*_pre.cpp"))
    )
    module_names = {
        path.name.removesuffix("_pre.cpp").removesuffix(".cpp")
        for path in units
        if path.name not in {"OCP.cpp"}
    }
    if len(module_names) != MODULES or len(units) != UNITS + 1:
        raise ValueError("prepared generated source is not exactly 315 modules plus OCP.cpp")

    sdk_includes = [
        path
        for path in sdk.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".h", ".hxx", ".hpp"}
    ]
    include_by_name: dict[str, list[Path]] = defaultdict(list)
    for header in sdk_includes:
        include_by_name[header.name.casefold()].append(header)
    source_headers = [
        path
        for path in (source_root / "src").rglob("*")
        if path.is_file() and path.suffix.casefold() in {".h", ".hxx", ".hpp"}
    ]
    source_by_name: dict[str, list[Path]] = defaultdict(list)
    for header in source_headers:
        source_by_name[header.name.casefold()].append(header)

    missing_headers: dict[str, set[str]] = defaultdict(set)
    required_toolkits: set[str] = set()
    non_occt_unresolved: dict[str, set[str]] = defaultdict(set)
    for unit in units:
        text = unit.read_text(encoding="utf-8", errors="replace")
        for included in INCLUDE.findall(text):
            normalized = included.replace("\\", "/")
            basename = PurePosixPath(normalized).name.casefold()
            source_matches = source_by_name.get(basename, [])
            if source_matches:
                if basename not in include_by_name:
                    missing_headers[normalized].add(unit.name)
                for header in source_matches:
                    relative = header.relative_to(source_root / "src")
                    if relative.parts:
                        required_toolkits.add("TK" + relative.parts[0])
            elif not include_by_name.get(basename) and not normalized.startswith(
                ("pybind11/", "Python.h", "numpy/", "fmt/", "windows.h", "Windows.h")
            ):
                # Keep third-party and platform includes visible in the report; they are
                # resolved by the locked OCP environment or Windows SDK, not by OCCT.
                non_occt_unresolved[normalized].add(unit.name)

    if "OpenGl_Context.hxx" in {key.split("/")[-1] for key in missing_headers}:
        required_toolkits.add("TKOpenGl")

    cmake_config = next(sdk.rglob("OpenCASCADEConfig.cmake"), None)
    if cmake_config is None:
        raise ValueError("sealed OCCT SDK is missing OpenCASCADEConfig.cmake")
    cmake_text = cmake_config.read_text(encoding="utf-8", errors="replace")
    library_match = re.search(r"(?is)set\s*\(\s*OpenCASCADE_LIBRARIES\s+([^)]*)\)", cmake_text)
    if library_match is None:
        raise ValueError("OpenCASCADEConfig.cmake does not export OpenCASCADE_LIBRARIES")
    exported_toolkits = set(TARGET.findall(library_match.group(1)))
    # The generated consumer links OpenCASCADE_LIBRARIES. Imported targets mentioned
    # by unrelated optional packages are not part of this consumer's closure.
    all_files = [path for path in sdk.rglob("*") if path.is_file() and not path.is_symlink()]
    file_names = {path.name.casefold() for path in all_files}
    missing_libraries, missing_runtimes = sdk_dependency_deficiencies(
        missing_headers, required_toolkits | exported_toolkits, file_names
    )

    result = {
        "generated_source_sha256": patched["source_archive"]["sha256"],
        "generated_modules": len(module_names),
        "translation_units_including_OCP_cpp": len(units),
        "scanned_include_directives": sum(
            len(INCLUDE.findall(unit.read_text(encoding="utf-8", errors="replace")))
            for unit in units
        ),
        "occt_source_header_count": len(source_headers),
        "sdk_installed_header_count": len(sdk_includes),
        "required_toolkits_from_includes": sorted(required_toolkits),
        "exported_toolkits": sorted(exported_toolkits),
        "missing_occt_headers": {
            key: sorted(value) for key, value in sorted(missing_headers.items())
        },
        "missing_import_libraries": missing_libraries,
        "missing_runtime_dlls": missing_runtimes,
        "unresolved_non_occt_includes_review": {
            key: sorted(value) for key, value in sorted(non_occt_unresolved.items())
        },
        "open_gl_header_present": any(
            path.name.casefold() == "opengl_context.hxx" for path in sdk_includes
        ),
        "tkopengl_lib_present": "tkopengl.lib" in file_names,
        "tkopengl_dll_present": "tkopengl.dll" in file_names,
        "windows_opengl_system": windows_opengl_prerequisites(
            Path(os.environ.get("WindowsSdkDir", r"C:\Program Files (x86)\Windows Kits\10")),
            os.environ.get("WindowsSDKVersion", "10.0.26100.0").rstrip("\\/"),
        ),
        "occt_source_revision": metadata["occt_source_revision"],
        "inner_sdk_payload_sha256": metadata["payload_sha256"],
    }
    if len(module_names) != MODULES:
        raise ValueError("generated module count changed during dependency audit")
    try:
        ensure_sdk_dependencies_complete(missing_headers, missing_libraries, missing_runtimes)
    except DependencyAuditError:
        result["status"] = "FAIL"
        raise DependencyAuditError(result)
    result["opengl_compile_link_probe"] = compile_opengl_sdk_probe(sdk, work_root)
    result["status"] = "PASS"
    return result


class DependencyAuditError(ValueError):
    def __init__(self, report: dict[str, Any]):
        self.report = report
        super().__init__("generated 315-module source has unresolved OCCT SDK dependencies")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--generated-source-zip", type=Path, required=True)
    parser.add_argument("--occt-source-archive", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--expected-run-id", required=True)
    parser.add_argument("--expected-attempt", required=True)
    parser.add_argument("--expected-cache-key", required=True)
    parser.add_argument("--require-opengl", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = audit_dependencies(
            args.sdk,
            args.generated_source_zip,
            args.occt_source_archive,
            args.work_root,
            expected_run_id=args.expected_run_id,
            expected_attempt=args.expected_attempt,
            expected_cache_key=args.expected_cache_key,
            require_opengl=args.require_opengl,
        )
    except DependencyAuditError as error:
        report = json.dumps(error.report, indent=2, sort_keys=True)
        if args.report:
            args.report.write_text(report + "\n", encoding="utf-8")
        print(report)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.report:
        args.report.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
