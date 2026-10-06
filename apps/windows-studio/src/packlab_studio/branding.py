"""Canonical PackLab Studio icon and Windows shell identity."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

from PySide6.QtGui import QIcon

from packlab_core.resource_paths import packlab_data_root

APP_USER_MODEL_ID = "PackLab.Studio"
ICON_RELATIVE_PATH = Path("apps/windows-studio/assets/branding/PackLab.ico")


def icon_path() -> Path:
    """Resolve the canonical icon in a source checkout or frozen bundle."""

    return packlab_data_root() / ICON_RELATIVE_PATH


def application_icon() -> QIcon:
    """Return the application icon, or an empty icon when an optional source icon is absent."""

    path = icon_path()
    return QIcon(str(path)) if path.is_file() else QIcon()


def set_windows_app_user_model_id() -> bool:
    """Set the stable Windows taskbar identity before QApplication is created."""

    if os.name != "nt":
        return False
    try:
        setter = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        return setter(APP_USER_MODEL_ID) == 0
    except (AttributeError, OSError):
        return False
