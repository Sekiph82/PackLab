"""Module entry point for the PackLab Studio source runtime."""

from __future__ import annotations

import ctypes
import os
from datetime import UTC, datetime
from pathlib import Path

from .app import main


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
