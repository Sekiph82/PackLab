"""Windows native dependency search setup for the PyInstaller one-directory app."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_DLL_DIRECTORY_HANDLES: list[object] = []
_NATIVE_DIRECTORY_NAMES = (
    "PySide6",
    "shiboken6",
    "OCP",
    "open3d",
    "numpy.libs",
)


def safe_exception_summary(error: Exception) -> str:
    """Return a short diagnostic without leaking machine-specific paths."""
    message = str(error).splitlines()[0] if str(error) else type(error).__name__
    if re.search(r"(?i)(?:[A-Z]:\\|\\\\)", message):
        return "diagnostic omitted because it contains an absolute path"
    return re.sub(r"[\x00-\x1f\x7f]", " ", message)[:240]


def register_frozen_native_directories() -> tuple[str, ...]:
    """Register staged wheel DLL directories before importing their extension modules."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return ()
    bundle_root = Path(getattr(sys, "_MEIPASS"))
    registered: list[str] = []
    for name in _NATIVE_DIRECTORY_NAMES:
        directory = bundle_root / name
        if directory.is_dir():
            _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(str(directory)))
            registered.append(name)
    return tuple(registered)
