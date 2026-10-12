"""Verify and deterministically prepare CadQuery's generated Windows OCP sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ARCHIVE_SIZE = 6_481_047
ARCHIVE_SHA256 = "290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b"
ARCHIVE_ROOT = "OCP_src_stubs_Windows"
REMOVED_MODULES = ("IVtk", "IVtkOCC", "IVtkTools", "IVtkVTK")
INPUT_MODULE_COUNT = 319
OUTPUT_MODULE_COUNT = 315
MAX_UNCOMPRESSED_BYTES = 70_000_000
_ENUM_DECL = re.compile(r"^\s*void register_([A-Za-z0-9_]+)_enums\(py::module&\);\s*$")
_MODULE_DECL = re.compile(r"^\s*void register_([A-Za-z0-9_]+)(?<!_enums)\(py::module&\);\s*$")
_ENUM_CALL = re.compile(r"^\s*register_([A-Za-z0-9_]+)_enums\(m\);\s*$")
_MODULE_CALL = re.compile(r"^\s*register_([A-Za-z0-9_]+)(?<!_enums)\(m\);\s*$")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "relative_path": path.relative_to(root).as_posix(),
            "byte_length": path.stat().st_size,
            "sha256": _sha256_bytes(path.read_bytes()),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def _assert_non_vtk_sources_preserved(
    before: list[dict[str, Any]], after: list[dict[str, Any]]
) -> None:
    before_by_path = {item["relative_path"]: item for item in before}
    after_by_path = {item["relative_path"]: item for item in after}
    explicitly_removed = {
        f"{ARCHIVE_ROOT}/{module}{suffix}"
        for module in REMOVED_MODULES
        for suffix in (".cpp", "_pre.cpp", "_tmpl.hxx")
    }
    intentionally_patched = {f"{ARCHIVE_ROOT}/OCP.cpp", f"{ARCHIVE_ROOT}/CMakeLists.txt"}
    if set(before_by_path) - explicitly_removed != set(after_by_path):
        raise ValueError("No-VTK patch changed an unexpected generated-source file set")
    for relative, original in before_by_path.items():
        if relative in explicitly_removed or relative in intentionally_patched:
            continue
        if after_by_path.get(relative) != original:
            raise ValueError(f"No-VTK patch changed unrelated upstream source bytes: {relative}")


def _safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    seen: set[str] = set()
    total = 0
    members: list[zipfile.ZipInfo] = []
    for info in archive.infolist():
        path = PurePosixPath(info.filename)
        if (
            path.is_absolute()
            or ".." in path.parts
            or ":" in info.filename
            or "\\" in info.filename
            or "/./" in info.filename
            or info.filename.startswith("./")
            or "//" in info.filename
            or not path.parts
            or path.parts[0] != ARCHIVE_ROOT
            or (len(path.parts) == 1 and not info.is_dir())
        ):
            raise ValueError(f"unsafe ZIP member path: {info.filename!r}")
        key = "/".join(path.parts).casefold()
        if key and key in seen:
            raise ValueError(f"duplicate or case-colliding ZIP path: {info.filename!r}")
        if key:
            seen.add(key)
        mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode):
            raise ValueError(f"ZIP symlinks are not accepted: {info.filename!r}")
        total += info.file_size
        if total > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("official generated source ZIP exceeds the extraction limit")
        members.append(info)
    return members


def _module_ids(names: set[str]) -> set[str]:
    groups: dict[str, set[str]] = {}
    folded_names: dict[str, str] = {}
    for name in names:
        relative = PurePosixPath(name)
        if len(relative.parts) != 2 or relative.parts[0] != ARCHIVE_ROOT:
            continue
        filename = relative.name
        if filename == "OCP.cpp" or filename == "CMakeLists.txt":
            continue
        for suffix in ("_pre.cpp", "_tmpl.hxx", ".cpp"):
            if filename.endswith(suffix):
                module = filename[: -len(suffix)]
                previous = folded_names.setdefault(module.casefold(), module)
                if previous != module:
                    raise ValueError("generated module IDs contain a case-colliding name")
                groups.setdefault(module, set()).add(suffix)
                break
    required = {".cpp", "_pre.cpp", "_tmpl.hxx"}
    if not groups or any(suffixes != required for suffixes in groups.values()):
        raise ValueError("generated module sources are missing, duplicated, or incomplete")
    return set(groups)


def _assert_registration_inventory(source: str, modules: set[str]) -> None:
    inventories = (
        (_ENUM_DECL, "enum declarations"),
        (_MODULE_DECL, "module declarations"),
        (_ENUM_CALL, "enum registrations"),
        (_MODULE_CALL, "module registrations"),
    )
    lines = source.splitlines()
    for pattern, label in inventories:
        found = [match.group(1) for line in lines if (match := pattern.fullmatch(line))]
        if len(found) != len(set(found)) or set(found) != modules:
            raise ValueError(f"OCP.cpp {label} do not exactly match generated module IDs")


def _patch_source_files(
    source_root: Path,
    modules: set[str],
    ocp_cpp: str,
    cmake: str,
) -> tuple[str, str, set[str]]:
    for module in REMOVED_MODULES:
        if module not in modules:
            raise ValueError("the exact four VTK modules are required before patching")
    for module in REMOVED_MODULES:
        for suffix in (".cpp", "_pre.cpp", "_tmpl.hxx"):
            (source_root / f"{module}{suffix}").unlink(missing_ok=True)

    lines = ocp_cpp.splitlines(keepends=True)
    kept_lines: list[str] = []
    removed_registration_lines: list[str] = []
    removed_patterns = (_ENUM_DECL, _MODULE_DECL, _ENUM_CALL, _MODULE_CALL)
    for line in lines:
        parsed = next(
            (
                match
                for pattern in removed_patterns
                if (match := pattern.fullmatch(line.rstrip("\r\n")))
            ),
            None,
        )
        if parsed and parsed.group(1) in REMOVED_MODULES:
            removed_registration_lines.append(line)
        else:
            kept_lines.append(line)
    expected_removed_lines = len(REMOVED_MODULES) * len(removed_patterns)
    if len(removed_registration_lines) != expected_removed_lines:
        raise ValueError("OCP.cpp did not contain exactly the four expected VTK registrations")
    patched_ocp_cpp = "".join(kept_lines)
    retained_modules = modules - set(REMOVED_MODULES)
    _assert_registration_inventory(patched_ocp_cpp, retained_modules)

    vtk_block = """find_package( VTK REQUIRED
  COMPONENTS
    WrappingPythonCore
    RenderingCore
    RenderingOpenGL2
    CommonDataModel
    CommonExecutionModel
    freetype
)
message(STATUS "VTK ${VTK_VERSION} found")
"""
    if cmake.count(vtk_block) != 1:
        raise ValueError("upstream VTK discovery block differs from the reviewed source")
    patched_cmake = cmake.replace(vtk_block, "")
    vtk_link = "target_link_libraries( OCP PRIVATE pybind11::pybind11 VTK::WrappingPythonCore VTK::RenderingCore VTK::CommonDataModel VTK::CommonExecutionModel fmt::fmt)"
    if patched_cmake.count(vtk_link) != 1:
        raise ValueError("upstream VTK link line differs from the reviewed source")
    patched_cmake = patched_cmake.replace(
        vtk_link,
        "target_link_libraries( OCP PRIVATE pybind11::pybind11 fmt::fmt)",
    )
    if re.search(r"vtk|IVtk", patched_cmake, re.IGNORECASE):
        raise ValueError("VTK references remain in the compiled OCP CMake input")

    (source_root / "OCP.cpp").write_text(patched_ocp_cpp, encoding="utf-8", newline="")
    (source_root / "CMakeLists.txt").write_text(patched_cmake, encoding="utf-8", newline="")
    compiled_inputs = [
        source_root / "OCP.cpp",
        *source_root.glob("*.cpp"),
        *source_root.glob("*_pre.cpp"),
        *source_root.glob("*_tmpl.hxx"),
    ]
    if any(
        re.search(r"vtk|IVtk", path.read_text(encoding="utf-8"), re.IGNORECASE)
        for path in compiled_inputs
    ):
        raise ValueError("VTK references remain in compiled generated C++ inputs")
    return patched_ocp_cpp, patched_cmake, retained_modules


def prepare_generated_sources(
    archive_path: Path, destination: Path, manifest_path: Path
) -> dict[str, Any]:
    raw = archive_path.read_bytes()
    digest = _sha256_bytes(raw)
    if len(raw) != ARCHIVE_SIZE or digest != ARCHIVE_SHA256:
        raise ValueError("official OCP generated-source archive size or SHA-256 mismatch")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("generated-source destination must be empty")

    with zipfile.ZipFile(archive_path) as archive:
        members = _safe_members(archive)
        names = {info.filename for info in members}
        modules = _module_ids(names)
        if len(modules) != INPUT_MODULE_COUNT or not set(REMOVED_MODULES) <= modules:
            raise ValueError("official source inventory is not the exact 319-module contract")
        ocp_cpp_path = f"{ARCHIVE_ROOT}/OCP.cpp"
        cmake_path = f"{ARCHIVE_ROOT}/CMakeLists.txt"
        ocp_cpp = archive.read(ocp_cpp_path).decode("utf-8")
        cmake = archive.read(cmake_path).decode("utf-8")
        _assert_registration_inventory(ocp_cpp, modules)
        version_matches = re.findall(
            r'm\.attr\("__version__"\)\s*=\s*py::cast\("([^"]+)"\)', ocp_cpp
        )
        if version_matches != ["7.9.3.1"]:
            raise ValueError(
                "generated OCP runtime version differs from the audited 7.9.3.1 identity"
            )

        destination.mkdir(parents=True, exist_ok=True)
        for info in members:
            target = destination.joinpath(*PurePosixPath(info.filename).parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))

    source_root = destination / ARCHIVE_ROOT
    pre_patch_files = _file_inventory(destination)
    patched_ocp_cpp, patched_cmake, retained_modules = _patch_source_files(
        source_root, modules, ocp_cpp, cmake
    )
    actual_modules = _module_ids(
        {f"{ARCHIVE_ROOT}/{path.name}" for path in source_root.iterdir() if path.is_file()}
    )
    if actual_modules != retained_modules or len(actual_modules) != OUTPUT_MODULE_COUNT:
        raise ValueError(
            "patched generated source tree does not contain exactly 315 complete modules"
        )

    post_patch_files = _file_inventory(destination)
    _assert_non_vtk_sources_preserved(pre_patch_files, post_patch_files)
    result = {
        "schema_version": 1,
        "status": "PASS",
        "source_archive": {
            "release_version": "7.9.3.1.1",
            "source_revision": "d69b064a3a604ebf245b1f3b14fb54c835a3a571",
            "byte_length": len(raw),
            "sha256": digest,
        },
        "runtime_reported_version": "7.9.3.1",
        "input_module_count": len(modules),
        "output_module_count": len(actual_modules),
        "removed_modules": list(REMOVED_MODULES),
        "retained_modules": sorted(actual_modules),
        "registration_count": len(actual_modules) * 2,
        "patch_rule": "remove exactly four IVtk module triplets/registrations and upstream VTK CMake discovery/linkage",
        "patched_ocp_cpp_sha256": _sha256_bytes(patched_ocp_cpp.encode("utf-8")),
        "patched_cmake_sha256": _sha256_bytes(patched_cmake.encode("utf-8")),
        "pre_patch_files": pre_patch_files,
        "post_patch_files": post_patch_files,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    result = prepare_generated_sources(args.archive, args.destination, args.manifest)
    print(
        f"OCP_GENERATED_SOURCE_PATCH_PASS input={result['input_module_count']} "
        f"output={result['output_module_count']} archive_sha256={result['source_archive']['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
