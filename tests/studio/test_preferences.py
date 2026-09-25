from __future__ import annotations

import json

from packlab_studio.preferences import PreferencesStore, WindowPreferences, sanitize_geometry


def test_round_trip_and_atomic_file(tmp_path) -> None:
    store = PreferencesStore(tmp_path / "config" / "preferences.json")
    value = WindowPreferences(geometry=(12, 24, 1400, 900), last_route="settings", theme="dark")
    store.save(value)
    assert store.load() == value
    assert not list((tmp_path / "config").glob("*.tmp"))


def test_corrupt_and_future_state_fall_back_to_defaults(tmp_path) -> None:
    path = tmp_path / "preferences.json"
    path.write_text("not-json", encoding="utf-8")
    assert PreferencesStore(path).load() == WindowPreferences()
    path.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    assert PreferencesStore(path).load() == WindowPreferences()


def test_v0_migrates_and_geometry_is_sanitized(tmp_path) -> None:
    path = tmp_path / "preferences.json"
    path.write_text(json.dumps({"schema_version": 0, "last_page": "editor", "geometry": [-5000, 5000, 1, 2]}), encoding="utf-8")
    assert PreferencesStore(path).load().last_route == "editor"
    assert sanitize_geometry([-5000, 5000, 1, 2], bounds=(0, 0, 1920, 1080)) == (0, 1000, 640, 480)


def test_shell_round_trip_uses_injected_store(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio.app import create_application
    from packlab_studio.navigation import Route
    from packlab_studio.shell import StudioMainWindow

    app = create_application(["packlab-preferences-test"])
    store = PreferencesStore(tmp_path / "preferences.json")
    first = StudioMainWindow(preferences=store)
    first.navigation.navigate(Route.SETTINGS)
    first.close()
    app.processEvents()
    second = StudioMainWindow(preferences=store)
    assert second.navigation.current_route is Route.SETTINGS
    second.close()
    app.processEvents()
