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
        app = create_application(argv)
        window = StudioMainWindow()
        window.show()
        return int(app.exec())
    except Exception:
        return EXIT_STARTUP_FAILURE


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
