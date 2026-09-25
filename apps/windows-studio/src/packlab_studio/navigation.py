"""Stable Studio routes and the single-window navigation seam."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class Route(StrEnum):
    LIBRARY = "library"
    CAPTURE_INBOX = "capture-inbox"
    RECONSTRUCTION = "reconstruction"
    EDITOR = "editor"
    SETTINGS = "settings"


class NavigationError(ValueError):
    pass


class NavigationController(QObject):
    route_changed = Signal(str)
    project_changed = Signal(object)

    def __init__(self, *, initial_route: Route = Route.LIBRARY) -> None:
        super().__init__()
        self._route = Route(initial_route)
        self._project_context: Any = None

    @property
    def current_route(self) -> Route:
        return self._route

    @property
    def project_context(self) -> Any:
        return self._project_context

    def navigate(self, route: Route | str) -> Route:
        try:
            target = Route(route)
        except ValueError as error:
            raise NavigationError(f"unknown Studio route: {route}") from error
        if target != self._route:
            self._route = target
            self.route_changed.emit(target.value)
        return target

    def set_project_context(self, context: Any) -> None:
        self._project_context = context
        self.project_changed.emit(context)


class CaptureInboxView(QWidget):
    """Presentation-only view composed with accepted M05 services."""

    def __init__(self, *, ingest_controller: Any = None, receiver: Any = None) -> None:
        super().__init__()
        self.setObjectName("packlab.view.capture-inbox")
        self.ingest_controller = ingest_controller
        self.receiver = receiver
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Capture Inbox"))


class NavigationPanel(QWidget):
    route_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("packlab.navigation.panel")
        self.list = QListWidget(self)
        self.list.setObjectName("packlab.navigation.routes")
        for route in Route:
            item = QListWidgetItem(route.name.replace("_", " ").title())
            item.setData(0x0100, route.value)
            self.list.addItem(item)
        self.list.currentItemChanged.connect(self._on_item_changed)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)

    def select_route(self, route: Route) -> None:
        for index in range(self.list.count()):
            if self.list.item(index).data(0x0100) == route.value:
                self.list.setCurrentRow(index)
                return

    def _on_item_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is not None:
            self.route_requested.emit(str(current.data(0x0100)))


class RouteStack(QStackedWidget):
    def __init__(self, *, ingest_controller: Any = None, receiver: Any = None) -> None:
        super().__init__()
        self.setObjectName("packlab.navigation.stack")
        self.views: dict[Route, QWidget] = {}
        for route in Route:
            view: QWidget
            if route is Route.CAPTURE_INBOX:
                view = CaptureInboxView(ingest_controller=ingest_controller, receiver=receiver)
            else:
                view = QLabel(route.name.replace("_", " ").title())
                view.setObjectName(f"packlab.view.{route.value}")
            self.views[route] = view
            self.addWidget(view)

    def show_route(self, route: Route) -> None:
        self.setCurrentWidget(self.views[route])
