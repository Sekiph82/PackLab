"""PackLab Studio application ownership and process boundary."""

from __future__ import annotations

import sys
from collections.abc import Sequence

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
                return EXIT_STARTUP_FAILURE
            app.processEvents()
            if window.isVisible():
                return EXIT_STARTUP_FAILURE
            app.quit()
            return EXIT_SUCCESS
        return int(app.exec())
    except Exception:
        return EXIT_STARTUP_FAILURE


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
