from __future__ import annotations

import pytest

from packlab_studio.navigation import NavigationController, NavigationError, Route
from packlab_studio.shell import StudioMainWindow


def test_all_routes_transition_and_state_is_deterministic() -> None:
    controller = NavigationController()
    for route in Route:
        assert controller.navigate(route.value) is route
        assert controller.current_route is route


def test_unknown_route_fails_without_changing_current_route() -> None:
    controller = NavigationController()
    with pytest.raises(NavigationError):
        controller.navigate("not-a-route")
    assert controller.current_route is Route.LIBRARY


def test_window_composes_capture_inbox_with_m05_services(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio.app import create_application

    app = create_application(["packlab-navigation-test"])
    ingest = object()
    receiver = object()
    window = StudioMainWindow(ingest_controller=ingest, receiver=receiver)
    capture = window.route_stack.views[Route.CAPTURE_INBOX]
    assert capture.ingest_controller is ingest
    assert capture.receiver is receiver
    window.navigation.navigate(Route.SETTINGS)
    assert window.navigation.current_route is Route.SETTINGS
    window.close()
    app.processEvents()
