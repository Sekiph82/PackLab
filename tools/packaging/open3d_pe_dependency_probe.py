"""Inspect staged Open3D PE imports without emitting machine-specific paths."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from tools.packaging.windows_native_runtime_policy import is_windows_runtime_dll

_DLL_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.dll$", re.IGNORECASE)
_OPTIONAL_EXCLUDED_DLLS = {"open3d_torch_ops.dll"}


def _system_search_directories() -> tuple[Path, ...]:
    candidates: list[Path] = []
    windows_directory = os.environ.get("WINDIR")
    if windows_directory:
        candidates.append(Path(windows_directory) / "System32")
    candidates.extend(Path(item) for item in os.environ.get("PATH", "").split(os.pathsep) if item)
    return tuple(candidates)


def _resolution(
    dependency: str, staged_names: set[str], system_directories: tuple[Path, ...]
) -> str:
    normalized = dependency.casefold()
    if normalized in staged_names:
        return "STAGED"
    if normalized.startswith(("api-ms-win-", "ext-ms-win-")):
        return "WINDOWS_API_SET"
    if any((directory / dependency).is_file() for directory in system_directories):
        return "HOST_SYSTEM_OR_PATH"
    if is_windows_runtime_dll(dependency):
        return "MICROSOFT_SIGNED_PREREQUISITE"
    return "UNRESOLVED"


def inspect_open3d_imports(stage: Path) -> dict[str, object]:
    """Report static imports for staged Open3D DLLs and Python extensions."""

    import pefile

    stage_root = stage.resolve(strict=True)
    open3d_directory = next(
        (
            item
            for item in stage_root.iterdir()
            if item.is_dir() and item.name.casefold() == "open3d"
        ),
        None,
    )
    if open3d_directory is None:
        return {"schema_version": 1, "status": "FAIL", "error_code": "open3d_directory_missing"}

    binaries = sorted(
        (
            item
            for item in open3d_directory.rglob("*")
            if item.is_file()
            and item.suffix.casefold() in {".dll", ".pyd"}
            and item.name.casefold() not in _OPTIONAL_EXCLUDED_DLLS
        ),
        key=lambda item: item.name.casefold(),
    )
    pybind_binaries = [item for item in binaries if item.name.casefold().startswith("pybind")]
    if not pybind_binaries:
        return {"schema_version": 1, "status": "FAIL", "error_code": "open3d_pybind_missing"}

    staged_names = {item.name.casefold() for item in stage_root.rglob("*") if item.is_file()}
    system_directories = _system_search_directories()
    inspections: list[dict[str, object]] = []
    unresolved = False
    for binary in binaries:
        try:
            image = pefile.PE(str(binary), fast_load=True)
            image.parse_data_directories(
                directories=[
                    pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
                ]
            )
            imports = sorted(
                {
                    entry.dll.decode("ascii")
                    for entry in getattr(image, "DIRECTORY_ENTRY_IMPORT", ())
                },
                key=str.casefold,
            )
        except (OSError, pefile.PEFormatError, UnicodeDecodeError):
            inspections.append({"binary": binary.name, "status": "FAIL"})
            unresolved = True
            continue

        dependencies: list[dict[str, str]] = []
        for dependency in imports:
            if not _DLL_NAME.fullmatch(dependency):
                dependencies.append({"name": "invalid_import_name", "resolution": "UNRESOLVED"})
                unresolved = True
                continue
            resolution = _resolution(dependency, staged_names, system_directories)
            dependencies.append({"name": dependency, "resolution": resolution})
            unresolved |= resolution == "UNRESOLVED"
        inspections.append({"binary": binary.name, "status": "INSPECTED", "imports": dependencies})

    return {
        "schema_version": 1,
        "status": "FAIL" if unresolved else "INSPECTED",
        "binary_count": len(binaries),
        "binaries": inspections,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = inspect_open3d_imports(args.stage)
    except (OSError, ValueError):
        report = {"schema_version": 1, "status": "FAIL", "error_code": "inspection_failed"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
