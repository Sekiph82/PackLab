"""Module entry point for the PackLab Studio source runtime."""

from __future__ import annotations

import ctypes
import os
import traceback
from datetime import UTC, datetime
from pathlib import Path


def _record_ownerdev_import_failure(error: Exception) -> None:
    """Preserve import-time failures when the owner launcher opted into diagnostics."""

    if os.name != "nt" or os.environ.get("PACKLAB_OWNERDEV_DIAGNOSTICS") != "1":
        return
    log_path = os.environ.get("PACKLAB_OWNERDEV_STARTUP_LOG")
    if not log_path:
        return
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "PackLab OWNER DEV source import exception\n"
            f"deployed_sha={os.environ.get('PACKLAB_OWNERDEV_SOURCE_SHA', 'unknown')}\n"
            f"studio_version={os.environ.get('PACKLAB_OWNERDEV_STUDIO_VERSION', 'unknown')}\n"
            f"exception_type={type(error).__name__}\n"
            f"exception_message={error}\n"
            "traceback:\n"
            f"{''.join(traceback.format_exception(type(error), error, error.__traceback__))}",
            encoding="utf-8",
        )
    except OSError:
        pass


try:
    from .app import main
except Exception as error:
    _record_ownerdev_import_failure(error)
    raise


def _record_startup_failure() -> None:
    """Write a local-only diagnostic when the owner source runtime cannot start."""

    if os.name != "nt":
        return
    root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "PackLab" / "OwnerDev" / "logs"
    try:
        root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        (root / f"startup-{stamp}.log").write_text(
            "PackLab Studio exited during startup with a nonzero status.\n", encoding="utf-8"
        )
    except OSError:
        pass
    try:
        ctypes.windll.user32.MessageBoxW(
            None,
            "PackLab Studio could not start. See the local OwnerDev logs folder for details.",
            "PackLab Studio",
            0x10,
        )
    except (AttributeError, OSError):
        pass


_exit_code = main()
if _exit_code:
    _record_startup_failure()
raise SystemExit(_exit_code)
