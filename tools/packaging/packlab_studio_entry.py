"""PyInstaller entry shim for the production PackLab Studio application."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if __name__ == "__main__":
    try:
        from packlab_studio.frozen_runtime import (
            register_frozen_native_directories,
            safe_exception_summary,
        )

        register_frozen_native_directories()
        from packlab_studio.app import main
    except Exception as error:
        if "--packlab-build-smoke" in sys.argv:
            log_path = os.environ.get("PACKLAB_BUILD_SMOKE_LOG")
            if log_path:
                try:
                    Path(log_path).write_text(
                        "PackLab frozen capability smoke failed during import "
                        f"({type(error).__name__}): {safe_exception_summary(error)}\n",
                        encoding="utf-8",
                    )
                except OSError:
                    pass
        raise
    raise SystemExit(main())
