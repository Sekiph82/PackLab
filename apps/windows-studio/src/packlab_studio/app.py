"""PackLab Studio application ownership and process boundary."""

from __future__ import annotations

import os
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .shell import StudioMainWindow

ORGANIZATION_NAME = "PackLab"
APPLICATION_NAME = "PackLab Studio"
EXIT_SUCCESS = 0
EXIT_STARTUP_FAILURE = 1
BUILD_SMOKE_ARGUMENT = "--packlab-build-smoke"


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the one process-owned QApplication without import-time side effects."""

    existing = QCoreApplication.instance()
    if existing is not None:
        if not isinstance(existing, QApplication):
            raise RuntimeError("PackLab Studio requires a QApplication instance")
        return existing
    arguments = list(argv) if argv is not None else sys.argv
    app = QApplication(arguments)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APPLICATION_NAME)
    app.setApplicationDisplayName(APPLICATION_NAME)
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
            if not window.close():
                raise RuntimeError("StudioMainWindow refused to close during build smoke.")
            app.processEvents()
            if window.isVisible():
                raise RuntimeError("StudioMainWindow remained visible after build smoke close.")
            app.quit()
            return EXIT_SUCCESS
        return int(app.exec())
    except Exception:
        if build_smoke:
            log_path = os.environ.get("PACKLAB_BUILD_SMOKE_LOG")
            if log_path:
                try:
                    Path(log_path).write_text(traceback.format_exc(), encoding="utf-8")
                except OSError:
                    pass
        return EXIT_STARTUP_FAILURE


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
