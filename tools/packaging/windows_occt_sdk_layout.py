"""Shared, fail-closed contract for the installed Windows OCCT SDK tree."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

CANONICAL_OPENGL_FILES = (
    "inc/OpenGl_Context.hxx",
    "win64/vc14/lib/TKOpenGl.lib",
    "win64/vc14/bin/TKOpenGl.dll",
)
_EXPECTED_FOLDED = {item.casefold(): item for item in CANONICAL_OPENGL_FILES}
_SET_VALUE = re.compile(r"(?is)\bset\s*\(\s*([A-Za-z0-9_]+)\s+([^)]*)\)")
_TARGET_PATH = re.compile(r'(?i)IMPORTED_(IMPLIB|LOCATION)_RELEASE\s+"([^"]+)"')


def _inventory(root: Path) -> dict[str, Path]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("OCCT SDK install root is missing or unsafe")
    files: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("OCCT SDK install contains a symbolic link")
        relative = path.relative_to(root).as_posix()
        parts = relative.split("/")
        if path.is_file() and (
            relative.startswith("/") or any(p in {"", ".", ".."} for p in parts)
        ):
            raise ValueError("OCCT SDK install contains an unsafe relative path")
        if not path.is_file():
            continue
        folded = relative.casefold()
        if folded in files:
            raise ValueError("OCCT SDK install contains case-colliding paths")
        files[folded] = path
    return files


def _set_values(config_text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for name, value in _SET_VALUE.findall(config_text):
        values[name.casefold()] = " ".join(value.strip().strip('"').split())
    return values


def validate_windows_occt_sdk_layout(root: Path) -> dict[str, Any]:
    """Validate required files and actual Windows paths exported by OCCT CMake."""
    files = _inventory(root)
    missing = [item for item in CANONICAL_OPENGL_FILES if item.casefold() not in files]
    if missing:
        raise ValueError("OCCT SDK lacks canonical Windows OpenGL paths: " + ", ".join(missing))

    configs = [
        path for folded, path in files.items() if folded.endswith("/opencascadeconfig.cmake")
    ]
    if len(configs) != 1:
        raise ValueError("OCCT SDK must contain exactly one OpenCASCADEConfig.cmake")
    config = configs[0]
    values = _set_values(config.read_text(encoding="utf-8", errors="replace"))
    prefix = config.parent.parent if config.parent.name.casefold() == "cmake" else None
    if prefix is None:
        raise ValueError("OpenCASCADEConfig.cmake is not in the canonical Windows cmake directory")

    expected_exports = {
        "opencascade_include_dir": "inc",
        "opencascade_library_dir": "win64/vc14/lib",
        "opencascade_binary_dir": "win64/vc14/bin",
    }
    for variable, expected_suffix in expected_exports.items():
        actual = values.get(variable, "").replace("\\", "/").strip('"')
        if (
            not actual
            or actual.casefold() != f"${{opencascade_install_prefix}}/{expected_suffix}".casefold()
        ):
            raise ValueError(f"OpenCASCADEConfig.cmake exports an incorrect {variable} path")

    libraries = values.get("opencascade_libraries", "").replace(";", " ").split()
    if "tkopengl" not in {item.casefold() for item in libraries}:
        raise ValueError("OpenCASCADEConfig.cmake does not export the TKOpenGl toolkit")
    for toolkit in libraries:
        for relative in (
            f"win64/vc14/lib/{toolkit}.lib".casefold(),
            f"win64/vc14/bin/{toolkit}.dll".casefold(),
        ):
            if relative not in files:
                raise ValueError(
                    f"OpenCASCADEConfig.cmake exports a missing toolkit file: {relative}"
                )

    target_exports = [
        path
        for folded, path in files.items()
        if folded.endswith(".cmake") and "opencascade" in folded and "targets" in folded
    ]
    import_lib = False
    runtime_dll = False
    for target_file in target_exports:
        text = target_file.read_text(encoding="utf-8", errors="replace").replace("\\", "/")
        for kind, value in _TARGET_PATH.findall(text):
            normalized = value.casefold()
            if kind.casefold() == "implib" and normalized.endswith("/win64/vc14/lib/tkopengl.lib"):
                import_lib = True
            if kind.casefold() == "location" and normalized.endswith(
                "/win64/vc14/bin/tkopengl.dll"
            ):
                runtime_dll = True
    if not import_lib or not runtime_dll:
        raise ValueError("OpenCASCADE target exports do not resolve TKOpenGl LIB and DLL paths")

    return {
        "required_files": {
            canonical: files[canonical.casefold()].relative_to(root).as_posix()
            for canonical in CANONICAL_OPENGL_FILES
        },
        "config_path": config.relative_to(root).as_posix(),
        "include_dir": "inc",
        "library_dir": "win64/vc14/lib",
        "binary_dir": "win64/vc14/bin",
    }
