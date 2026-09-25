from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtWidgets import QApplication

from packlab_studio.app import APPLICATION_NAME, create_application
from packlab_studio.shell import StudioMainWindow


def test_import_does_not_create_qapplication() -> None:
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import packlab_studio.app; from PySide6.QtCore import QCoreApplication; assert QCoreApplication.instance() is None",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stderr


def test_shell_constructs_one_window_and_closes(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-test"])
    window = StudioMainWindow()
    assert isinstance(app, QApplication)
    assert app.applicationName() == APPLICATION_NAME
    assert window.objectName() == StudioMainWindow.WINDOW_OBJECT_NAME
    assert window.centralWidget() is not None
    window.close()
    app.processEvents()
