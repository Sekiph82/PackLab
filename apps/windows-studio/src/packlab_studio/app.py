"""PackLab Studio application ownership and process boundary."""

from __future__ import annotations

import os
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .branding import application_icon, set_windows_app_user_model_id
from .frozen_runtime import safe_exception_summary
from .shell import StudioMainWindow

ORGANIZATION_NAME = "PackLab"
APPLICATION_NAME = "PackLab Studio"
EXIT_SUCCESS = 0
EXIT_STARTUP_FAILURE = 1
BUILD_SMOKE_ARGUMENT = "--packlab-build-smoke"


def _write_ownerdev_startup_failure(error: Exception, *, enabled: bool) -> None:
    """Preserve a local traceback only for the explicit OWNER DEV source launcher."""

    log_path = os.environ.get("PACKLAB_OWNERDEV_STARTUP_LOG")
    if not enabled or not log_path:
        return
    try:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(log_path).write_text(
            "PackLab OWNER DEV source startup exception\n"
            f"deployed_sha={os.environ.get('PACKLAB_OWNERDEV_SOURCE_SHA', 'unknown')}\n"
            f"studio_version={os.environ.get('PACKLAB_OWNERDEV_STUDIO_VERSION', 'unknown')}\n"
            f"exception_type={type(error).__name__}\n"
            f"exception_message={safe_exception_summary(error)}\n"
            "traceback:\n"
            f"{''.join(traceback.format_exception(type(error), error, error.__traceback__))}",
            encoding="utf-8",
        )
    except OSError:
        pass


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the one process-owned QApplication without import-time side effects."""

    existing = QCoreApplication.instance()
    if existing is not None:
        if not isinstance(existing, QApplication):
            raise RuntimeError("PackLab Studio requires a QApplication instance")
        return existing
    set_windows_app_user_model_id()
    arguments = list(argv) if argv is not None else sys.argv
    app = QApplication(arguments)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APPLICATION_NAME)
    app.setApplicationDisplayName(APPLICATION_NAME)
    app.setWindowIcon(application_icon())
    return app


def run(argv: Sequence[str] | None = None) -> int:
    """Start the shell and return a deterministic process exit code."""

    build_smoke = False
    try:
        arguments = list(argv) if argv is not None else sys.argv.copy()
        build_smoke = BUILD_SMOKE_ARGUMENT in arguments
        if build_smoke:
            arguments.remove(BUILD_SMOKE_ARGUMENT)
        app = create_application(arguments)
        window = StudioMainWindow()
        window.show()
        if build_smoke:
            app.processEvents()
            from .build_smoke import run_frozen_capability_smoke

            run_frozen_capability_smoke()
            if not window.close():
                raise RuntimeError("StudioMainWindow refused to close during build smoke.")
            app.processEvents()
            app.quit()
            return EXIT_SUCCESS
        return int(app.exec())
    except Exception as error:
        if build_smoke:
            log_path = os.environ.get("PACKLAB_BUILD_SMOKE_LOG")
            if log_path:
                try:
                    Path(log_path).write_text(
                        "PackLab frozen capability smoke failed "
                        f"({type(error).__name__}): {safe_exception_summary(error)}\n",
                        encoding="utf-8",
                    )
                except OSError:
                    pass
        _write_ownerdev_startup_failure(
            error,
            enabled=os.name == "nt" and os.environ.get("PACKLAB_OWNERDEV_DIAGNOSTICS") == "1",
        )
        return EXIT_STARTUP_FAILURE


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
