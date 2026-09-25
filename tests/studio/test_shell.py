from __future__ import annotations

import importlib

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from packlab_studio.app import APPLICATION_NAME, create_application
from packlab_studio.shell import StudioMainWindow


def test_import_does_not_create_qapplication() -> None:
    assert QCoreApplication.instance() is None
    importlib.import_module("packlab_studio.app")
    assert QCoreApplication.instance() is None


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
