"""PL-0464: readable navigation, sane default docks, page headers, title and language."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from packlab_studio.app import create_application
from packlab_studio.capture_inbox import QR_SIZE_PX, qr_pixmap
from packlab_studio.i18n import SETTINGS_KEY, language
from packlab_studio.navigation import ROUTE_TEXT, Route
from packlab_studio.preferences import PreferencesStore
from packlab_studio.shell import StudioMainWindow
from packlab_studio.workspace import DockId

# Logical sizes: owner screens at 100 % and 1920x1080 at 150 % (1280x720 logical).
SIZES = ((1389, 868), (1920, 1080), (1280, 720))


def _labels_fit(window: StudioMainWindow) -> list[str]:
    """Labels whose icon+text do not fit the visible navigation viewport."""
    nav = window.navigation_panel.list
    viewport = nav.viewport().width()
    metrics = nav.fontMetrics()
    icon = nav.iconSize().width()
    bad = []
    for row in range(nav.count()):
        item = nav.item(row)
        needed = metrics.horizontalAdvance(item.text()) + icon + 8
        if needed > viewport or nav.visualItemRect(item).width() < needed:
            bad.append(item.text())
    return bad


def _window(monkeypatch, tmp_path, **kwargs) -> tuple[QApplication, StudioMainWindow]:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-visual-polish-test"])
    window = StudioMainWindow(
        diagnostics_root=tmp_path / "diagnostics",
        packaging_library_root=tmp_path / "library",
        **kwargs,
    )
    return app, window


def test_navigation_labels_are_never_elided(monkeypatch, tmp_path) -> None:
    for code in ("en", "tr"):
        settings = tmp_path / f"{code}.ini"
        QSettings(str(settings), QSettings.Format.IniFormat).setValue(SETTINGS_KEY, code)
        app, window = _window(monkeypatch, tmp_path, settings_path=settings)
        try:
            window.show()
            for width, height in SIZES:
                window.resize(width, height)
                app.processEvents()
                assert _labels_fit(window) == [], (code, width, height)
                assert not window.navigation_panel.list.horizontalScrollBar().isVisible()
        finally:
            window.close()
            app.processEvents()


def test_navigation_fits_at_150_percent_scaling(tmp_path) -> None:
    script = textwrap.dedent(
        """
        from packlab_studio.app import create_application
        from packlab_studio.shell import StudioMainWindow
        app = create_application(["scaled"])
        window = StudioMainWindow()
        window.show()
        nav = window.navigation_panel.list
        for size in ((1389, 868), (1920, 1080)):
            window.resize(*size)
            app.processEvents()
            for row in range(nav.count()):
                item = nav.item(row)
                need = nav.fontMetrics().horizontalAdvance(item.text()) + nav.iconSize().width()
                assert need + 8 <= nav.viewport().width(), (size, item.text())
        assert app.devicePixelRatio() == 1.5, app.devicePixelRatio()
        window.close()
        print("ok")
        """
    )
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_SCALE_FACTOR="1.5")
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, env=env, timeout=120
    )
    assert result.returncode == 0 and "ok" in result.stdout, result.stderr[-2000:]


def test_empty_docks_hidden_and_jobs_dock_compact_until_a_job_runs(monkeypatch, tmp_path) -> None:
    app, window = _window(monkeypatch, tmp_path)
    try:
        window.show()
        app.processEvents()
        docks = window.workspace.docks
        for dock_id in (DockId.SCENE, DockId.PROPERTIES, DockId.LOGS):
            assert docks[dock_id].isHidden()
        view_menu = next(
            m
            for m in window.menuBar().findChildren(type(window.recent_menu))
            if m.objectName() == "packlab.menu.view"
        )
        assert docks[DockId.SCENE].toggleViewAction() in view_menu.actions()
        jobs = docks[DockId.JOBS]
        idle_max = jobs.widget().maximumHeight()
        assert jobs.isVisible() and idle_max < 80
        jobs.hide()
        job = window.job_manager.create("Build model", "build", job_id="job-1")
        window.job_manager.start(job.job_id)
        app.processEvents()
        assert jobs.isVisible() and jobs.widget().maximumHeight() > idle_max
        assert "1" in jobs.windowTitle()
        window.job_manager.succeed(job.job_id)
        assert jobs.widget().maximumHeight() == idle_max
    finally:
        window.close()
        app.processEvents()


def test_every_route_has_a_page_header(monkeypatch, tmp_path) -> None:
    app, window = _window(monkeypatch, tmp_path)
    try:
        window.new_project(tmp_path / "project", "Bottle 500 ml")
        window.show()
        for route in Route:
            window.navigation.navigate(route)
            app.processEvents()
            title, description, _icon = ROUTE_TEXT[route]
            assert window.page_header.title.text() == title
            assert window.page_header.description.text() == description
            assert window.page_header.isVisible()
        # One title, no " - PackLab Studio" suffix added by an application display name.
        assert window.windowTitle() == "PackLab Studio — Bottle 500 ml[*]"
        assert QApplication.applicationDisplayName() in ("", "PackLab Studio")
    finally:
        window.close()
        app.processEvents()


def test_language_setting_persists_and_turkish_applies_on_start(monkeypatch, tmp_path) -> None:
    settings = tmp_path / "settings.ini"
    app, window = _window(monkeypatch, tmp_path, settings_path=settings)
    try:
        assert language() == "en"
        assert window.navigation_panel.list.item(0).text() == "Packaging Library"
        window.language_actions["tr"].trigger()
        assert QSettings(str(settings), QSettings.Format.IniFormat).value(SETTINGS_KEY) == "tr"
    finally:
        window.close()
        app.processEvents()
    app, window = _window(monkeypatch, tmp_path, settings_path=settings)
    try:
        assert language() == "tr"
        assert window.navigation_panel.list.item(0).text() == "Ambalaj Kütüphanesi"
        assert window.page_header.title.text() == "Ambalaj Kütüphanesi"
        inbox = window.route_stack.views[Route.CAPTURE_INBOX]
        assert inbox.receive_button.text() == "iPhone'dan al"
        assert window.menuBar().actions()[0].text() == "&Dosya"
        settings_view = window.route_stack.views[Route.SETTINGS]
        assert settings_view.language.currentData() == "tr"
        # Audit identifiers stay verbatim next to the Turkish explanation.
        editor = window.route_stack.views[Route.EDITOR]
        assert "DEFERRED_OWNER_VALIDATION" in editor.authority_status.text()
        assert "doğrulanmadı" in editor.authority_status.text()
    finally:
        window.close()
        app.processEvents()
    app, window = _window(monkeypatch, tmp_path)  # no settings: English again
    assert language() == "en"
    window.close()
    app.processEvents()


def test_old_saved_dock_state_is_dropped(tmp_path) -> None:
    path = tmp_path / "window-preferences.json"
    path.write_text(json.dumps({"schema_version": 1, "dock_state": "AAAA"}), encoding="utf-8")
    loaded = PreferencesStore(path).load()
    assert loaded.dock_state == "" and loaded.schema_version == 2


def test_qr_code_is_bounded_and_inbox_scrolls(monkeypatch, tmp_path) -> None:
    app, window = _window(monkeypatch, tmp_path)
    try:
        pixmap = qr_pixmap('{"payload": "x"}')
        logical = pixmap.width() / pixmap.devicePixelRatio()
        assert QR_SIZE_PX * 0.6 <= logical <= 300
        inbox = window.route_stack.views[Route.CAPTURE_INBOX]
        assert inbox.scroll_area.widgetResizable()
    finally:
        window.close()
        app.processEvents()
