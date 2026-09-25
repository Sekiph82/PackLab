"""Minimal production Studio shell; domain services are injected later."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QSplitter

from .navigation import NavigationController, NavigationPanel, Route, RouteStack
from .workspace import WorkspaceManager


class StudioMainWindow(QMainWindow):
    """The single top-level PackLab Studio window."""

    WINDOW_OBJECT_NAME = "packlab.studio.main-window"

    def __init__(self, *, ingest_controller: object = None, receiver: object = None) -> None:
        super().__init__()
        self.setObjectName(self.WINDOW_OBJECT_NAME)
        self.setWindowTitle("PackLab Studio")
        self.setWindowIcon(QIcon())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.navigation = NavigationController()
        self.navigation_panel = NavigationPanel()
        self.route_stack = RouteStack(ingest_controller=ingest_controller, receiver=receiver)
        self.navigation_panel.route_requested.connect(self.navigation.navigate)
        self.navigation.route_changed.connect(lambda value: self.route_stack.show_route(Route(value)))
        self.navigation.route_changed.connect(lambda value: self.navigation_panel.select_route(Route(value)))
        splitter = QSplitter(self)
        splitter.setObjectName("packlab.main.splitter")
        splitter.addWidget(self.navigation_panel)
        splitter.addWidget(self.route_stack)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)
        self.workspace = WorkspaceManager(self)
        self.navigation_panel.select_route(Route.LIBRARY)
