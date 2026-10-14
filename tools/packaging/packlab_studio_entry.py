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
        loaded_modules = sorted(
            name
            for name in sys.modules
            if (name.startswith("open3d") or name.startswith("numpy"))
            and all(part.isidentifier() for part in name.split("."))
        )[:30]
        module_summary = ",".join(loaded_modules) or "none"
        if len(module_summary) > 700:
            module_summary = module_summary[:700]
        diagnostic = (
            f"status={status};detail={detail};dll_dirs={registered};"
            f"loaded_modules={module_summary}\n"
        )
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


def _run_numpy_probe() -> int:
    """Probe NumPy native initialization in a separate frozen process."""
    log_path = os.environ.get("PACKLAB_NUMPY_PROBE_LOG")
    try:
        import numpy as np

        values = np.asarray((1.0, 2.0, 3.0), dtype=np.float64)
        if values.shape != (3,) or values.sum() != 6.0:
            raise RuntimeError("numpy_array_contract_failed")
        version = np.__version__
        if not re.fullmatch(r"[0-9A-Za-z.+-]{1,40}", version):
            version = "version_omitted"
        diagnostic = f"status=available;version={version}\n"
        exit_code = 0
    except Exception as error:
        message = str(error).splitlines()[0] if str(error) else type(error).__name__
        if re.search(r"(?i)(?:[A-Z]:\\|\\\\)", message):
            message = "diagnostic_omitted"
        else:
            message = re.sub(r"[\x00-\x1f\x7f]", " ", message)[:180]
        diagnostic = f"status=probe_error;error_type={type(error).__name__};detail={message}\n"
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
        if "--packlab-build-numpy-probe" in sys.argv:
            raise SystemExit(_run_numpy_probe())
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
