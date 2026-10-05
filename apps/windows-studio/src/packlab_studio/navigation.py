"""Stable Studio routes and the single-window navigation seam."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .engineering_export import EngineeringExportView
from .mask_correction import MaskCorrectionView
from .packaging_library_browser import PackagingLibraryBrowserService, PackagingLibraryBrowserView
from .version import AboutView


class Route(StrEnum):
    LIBRARY = "library"
    CAPTURE_INBOX = "capture-inbox"
    RECONSTRUCTION = "reconstruction"
    EDITOR = "editor"
    MASK_CORRECTION = "mask-correction"
    EXPORTS = "exports"
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


class ScanMasterEditorView(QWidget):
    """Studio action surface; all authority and eligibility checks stay in core."""

    promotion_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("packlab.view.editor")
        self.actor_input = QLineEdit(self)
        self.actor_input.setObjectName("packlab.scan-master.actor")
        self.reason_input = QLineEdit(self)
        self.reason_input.setObjectName("packlab.scan-master.reason")
        self.promote_button = QPushButton("Promote to Scan Master", self)
        self.promote_button.setObjectName("packlab.scan-master.promote")
        self.authority_status = QLabel(
            "Before physical validation: DEFERRED_OWNER_VALIDATION; inherited scale state; "
            "mold_use_authorized=false.",
            self,
        )
        self.authority_status.setObjectName("packlab.scan-master.authority-status")
        self.status = QLabel("No promotion requested.", self)
        self.status.setObjectName("packlab.scan-master.status")
        form = QFormLayout()
        form.addRow("Actor", self.actor_input)
        form.addRow("Promotion reason", self.reason_input)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.promote_button)
        layout.addWidget(self.authority_status)
        layout.addWidget(self.status)
        self.promote_button.clicked.connect(self._request_promotion)

    def _request_promotion(self) -> None:
        actor = self.actor_input.text().strip()
        reason = self.reason_input.text().strip()
        if not actor or not reason:
            self.status.setText("Promotion requires an actor and reason.")
            return
        self.promotion_requested.emit(actor, reason)

    def set_promotion_status(self, text: str) -> None:
        self.status.setText(text)


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

    def set_project_available(self, available: bool) -> None:
        for index in range(self.list.count()):
            item = self.list.item(index)
            route = item.data(Qt.ItemDataRole.UserRole)
            if route in {
                Route.CAPTURE_INBOX.value,
                Route.RECONSTRUCTION.value,
                Route.EDITOR.value,
                Route.EXPORTS.value,
            }:
                flags = item.flags()
                item.setFlags(
                    flags | Qt.ItemFlag.ItemIsEnabled
                    if available
                    else flags & ~Qt.ItemFlag.ItemIsEnabled
                )

    def select_route(self, route: Route) -> None:
        for index in range(self.list.count()):
            if self.list.item(index).data(0x0100) == route.value:
                self.list.setCurrentRow(index)
                return

    def _on_item_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is not None:
            self.route_requested.emit(str(current.data(0x0100)))


class RouteStack(QStackedWidget):
    def __init__(
        self,
        *,
        ingest_controller: Any = None,
        receiver: Any = None,
        project_manager: Any = None,
        packaging_library_service: PackagingLibraryBrowserService | None = None,
        design_model_export_source_provider: Any = None,
        export_destination_provider: Any = None,
    ) -> None:
        super().__init__()
        self.setObjectName("packlab.navigation.stack")
        self.views: dict[Route, QWidget] = {}
        for route in Route:
            view: QWidget
            if route is Route.LIBRARY:
                view = PackagingLibraryBrowserView(packaging_library_service)
            elif route is Route.CAPTURE_INBOX:
                view = CaptureInboxView(ingest_controller=ingest_controller, receiver=receiver)
            elif route is Route.MASK_CORRECTION:
                view = MaskCorrectionView()
            elif route is Route.SETTINGS:
                view = AboutView()
            elif route is Route.EDITOR:
                view = ScanMasterEditorView()
            elif route is Route.EXPORTS:
                view = EngineeringExportView(
                    project_manager,
                    design_model_source_provider=design_model_export_source_provider,
                    destination_provider=export_destination_provider,
                )
            else:
                view = QLabel(route.name.replace("_", " ").title())
                view.setObjectName(f"packlab.view.{route.value}")
            self.views[route] = view
            self.addWidget(view)

    def show_route(self, route: Route) -> None:
        self.setCurrentWidget(self.views[route])

    def set_project_available(self, available: bool) -> None:
        for route in (
            Route.CAPTURE_INBOX,
            Route.RECONSTRUCTION,
            Route.EDITOR,
            Route.MASK_CORRECTION,
            Route.EXPORTS,
        ):
            self.views[route].setEnabled(available)
        export_view = self.views[Route.EXPORTS]
        if isinstance(export_view, EngineeringExportView):
            export_view.refresh_source()
