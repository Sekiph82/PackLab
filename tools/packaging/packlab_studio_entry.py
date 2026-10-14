"""PyInstaller entry shim for the production PackLab Studio application."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def _run_open3d_first_probe(native_directories: tuple[str, ...] = ()) -> int:
    """Probe Open3D in a clean frozen process and write path-free evidence."""
    log_path = os.environ.get("PACKLAB_OPEN3D_PROBE_LOG")
    try:
        from packlab_core.geometry_adapter import probe_open3d

        capability = probe_open3d()
        status = capability.status.value
        detail = capability.detail
        if not re.fullmatch(r"[A-Za-z0-9_.;=(), -]{1,600}", detail):
            detail = "diagnostic_omitted"
        registered = ",".join(native_directories) or "none"
        diagnostic = f"status={status};detail={detail};dll_dirs={registered}\n"
        exit_code = 0 if status == "available" else 1
    except Exception as error:
        diagnostic = f"status=probe_error;error_type={type(error).__name__}\n"
        exit_code = 1
    if log_path:
        try:
            Path(log_path).write_text(diagnostic, encoding="utf-8")
        except OSError:
            pass
    return exit_code


if __name__ == "__main__":
    try:
        from packlab_studio.frozen_runtime import (
            register_frozen_native_directories,
            safe_exception_summary,
        )

        native_directories = register_frozen_native_directories()
        if "--packlab-build-open3d-probe" in sys.argv:
            raise SystemExit(_run_open3d_first_probe(native_directories))
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
