"""Minimal production Studio shell; domain services are injected later."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QMainWindow, QSplitter

from .jobs import JobManager
from .navigation import NavigationController, NavigationPanel, Route, RouteStack
from .preferences import PreferencesStore, WindowPreferences
from .workspace import WorkspaceManager


class StudioMainWindow(QMainWindow):
    """The single top-level PackLab Studio window."""

    WINDOW_OBJECT_NAME = "packlab.studio.main-window"

    def __init__(self, *, ingest_controller: object = None, receiver: object = None, preferences: PreferencesStore | None = None) -> None:
        super().__init__()
        self.setObjectName(self.WINDOW_OBJECT_NAME)
        self.setWindowTitle("PackLab Studio")
        self.setWindowIcon(QIcon())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.preferences = preferences
        self.navigation = NavigationController()
        self.job_manager = JobManager()
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
        self.workspace = WorkspaceManager(self, job_manager=self.job_manager)
        self._restore_preferences()

    def _restore_preferences(self) -> None:
        if self.preferences is None:
            self.navigation_panel.select_route(Route.LIBRARY)
            return
        saved = self.preferences.load()
        self.setGeometry(*saved.geometry)
        if saved.maximized:
            self.showMaximized()
        if saved.fullscreen:
            self.showFullScreen()
        if saved.dock_state:
            self.restoreState(QByteArray.fromBase64(saved.dock_state.encode("ascii")))
        try:
            self.navigation.navigate(Route(saved.last_route))
        except ValueError:
            self.navigation.navigate(Route.LIBRARY)
        self.navigation_panel.select_route(self.navigation.current_route)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.preferences is not None:
            state = self.saveState().toBase64().toStdString()
            self.preferences.save(
                WindowPreferences(
                    geometry=(self.x(), self.y(), self.width(), self.height()),
                    maximized=self.isMaximized(),
                    fullscreen=self.isFullScreen(),
                    dock_state=state,
                    last_route=self.navigation.current_route.value,
                )
            )
        super().closeEvent(event)
