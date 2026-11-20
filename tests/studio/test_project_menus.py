"""PL-0454/PL-0455/PL-0457: File/Help menus, route gating, preferences wiring, Engines panel."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from packlab_core.engine_probe import EngineProbeResult, EngineProbeStatus, EngineVersion
from packlab_studio import app as studio_app
from packlab_studio import navigation
from packlab_studio.app import create_application
from packlab_studio.engine_config import (
    DiscoveryStatus,
    EngineDiscoveryReport,
    EnginePathDiagnostic,
)
from packlab_studio.navigation import PROJECT_ROUTES, Route, SettingsView
from packlab_studio.preferences import PreferencesStore
from packlab_studio.shell import StudioMainWindow


def _window(monkeypatch, tmp_path: Path, **kwargs: object):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-menu-test"])
    window = StudioMainWindow(
        diagnostics_root=tmp_path / "diagnostics",
        packaging_library_root=tmp_path / "library",
        settings_path=tmp_path / "settings.ini",
        **kwargs,  # type: ignore[arg-type]
    )
    return app, window


def _enabled(window: StudioMainWindow, route: Route) -> bool:
    for row in range(window.navigation_panel.list.count()):
        item = window.navigation_panel.list.item(row)
        if item.data(0x0100) == route.value:
            return bool(item.flags() & Qt.ItemFlag.ItemIsEnabled)
    raise AssertionError(route)


def test_file_menu_new_close_and_recent_reopen(monkeypatch, tmp_path) -> None:
    app, window = _window(monkeypatch, tmp_path)
    try:
        assert window.project_manager.current is None
        for route in PROJECT_ROUTES:  # Mask Correction included: nav matches view gating
            assert not _enabled(window, route)
            assert not window.route_stack.views[route].isEnabled()
        assert not window.close_project_action.isEnabled()

        target = tmp_path / "Bottle 500 ml"
        window.choose_new_project_path = lambda: str(target)
        window.new_project_action.trigger()
        assert window.project_manager.current is not None
        assert window.project_manager.current.name == "Bottle 500 ml"
        assert "Bottle 500 ml" in window.windowTitle()
        assert all(_enabled(window, route) for route in PROJECT_ROUTES)
        assert window.recent_projects() == [str(target)]

        window.close_project_action.trigger()
        assert window.project_manager.current is None
        assert not _enabled(window, Route.MASK_CORRECTION)

        recent = window.recent_menu.actions()
        assert [action.text() for action in recent] == [str(target)]
        recent[0].trigger()
        assert window.project_manager.current is not None

        window.choose_open_project_path = lambda: str(tmp_path / "not-a-project")
        window.open_project_action.trigger()
        assert "Open project failed" in window.statusBar().currentMessage()
    finally:
        window.close()
        app.processEvents()


def test_default_project_created_on_first_run_and_reopened(monkeypatch, tmp_path) -> None:
    app, window = _window(monkeypatch, tmp_path, default_project_root=tmp_path / "default")
    first_id = window.project_manager.current.project_id  # type: ignore[union-attr]
    window.close()
    app.processEvents()
    app, window = _window(monkeypatch, tmp_path, default_project_root=tmp_path / "default")
    try:
        assert window.project_manager.current is not None
        assert window.project_manager.current.project_id == first_id
    finally:
        window.close()
        app.processEvents()


def test_help_menu_writes_diagnostic_bundle(monkeypatch, tmp_path) -> None:
    app, window = _window(monkeypatch, tmp_path)
    try:
        window.diagnostic_bundle_action.trigger()
        message = window.statusBar().currentMessage()
        assert message.startswith("Diagnostic bundle written: ")
        assert Path(message.split(": ", 1)[1]).is_file()
    finally:
        window.close()
        app.processEvents()


def test_app_run_wires_preferences_settings_and_default_project(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeApp:
        def exec(self) -> int:
            return 0

    class FakeWindow:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def show(self) -> None:
            pass

    monkeypatch.setattr(studio_app, "create_application", lambda _argv: FakeApp())
    monkeypatch.setattr(studio_app, "StudioMainWindow", FakeWindow)
    assert studio_app.run(["PackLabStudio"]) == studio_app.EXIT_SUCCESS
    assert isinstance(captured["preferences"], PreferencesStore)
    assert str(captured["default_project_root"]).endswith("default")
    assert str(captured["settings_path"]).endswith("studio-settings.ini")


def test_settings_engines_panel_lists_discovery_and_rechecks(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    create_application(["packlab-engines-test"])
    report = EngineDiscoveryReport(
        (
            EnginePathDiagnostic(
                "colmap",
                Path("C:/engines/colmap.exe"),
                "environment",
                DiscoveryStatus.CONFIGURED,
                "ok",
            ),
            EnginePathDiagnostic(
                "openmvs.texture_mesh", None, "PATH", DiscoveryStatus.MISSING, "no executable found"
            ),
        )
    )
    monkeypatch.setattr(navigation, "discover_engines", lambda: report)
    probes: list[Path] = []

    def fake_probe(executable: Path, *, runner: object) -> EngineProbeResult:
        probes.append(executable)
        return EngineProbeResult(
            "colmap", str(executable), EngineProbeStatus.UNSUPPORTED, EngineVersion(4, 2, 1), ""
        )

    monkeypatch.setattr(navigation, "probe_colmap", fake_probe)
    view = SettingsView()
    rows = [view.engines.item(i).text() for i in range(view.engines.count())]
    assert rows[0].startswith("colmap: configured via environment")
    assert rows[1] == "openmvs.texture_mesh: missing via PATH | no executable found"
    assert probes == []  # no engine is started just by opening Settings
    view.recheck_button.click()
    assert "version 4.2.1 (unsupported)" in view.engines.item(0).text()
    assert probes == [Path("C:/engines/colmap.exe")]
