"""Minimal production Studio shell; domain services are injected later."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QMainWindow


class StudioMainWindow(QMainWindow):
    """The single top-level PackLab Studio window."""

    WINDOW_OBJECT_NAME = "packlab.studio.main-window"

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName(self.WINDOW_OBJECT_NAME)
        self.setWindowTitle("PackLab Studio")
        self.setWindowIcon(QIcon())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setCentralWidget(QLabel("PackLab Studio", self))
