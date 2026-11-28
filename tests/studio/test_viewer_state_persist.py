"""Loaded views survive page switches; part clouds load off the UI thread (SYNTHETIC data)."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("open3d")

from PySide6.QtCore import QSettings  # noqa: E402
from test_project_parts import _build, _entry, _jar, _pump, app  # noqa: E402, F401

from packlab_studio import model_viewer  # noqa: E402
from packlab_studio.measure_view import MeasureDesignView  # noqa: E402
from packlab_studio.model_viewer import ModelViewerView  # noqa: E402
from packlab_studio.navigation import Route  # noqa: E402
from packlab_studio.shell import StudioMainWindow  # noqa: E402


def _window(tmp_path):
    window = StudioMainWindow(
        diagnostics_root=tmp_path / "diagnostics", packaging_library_root=tmp_path / "library"
    )
    manager = window.project_manager
    manager.new_project(tmp_path / "jar", "Jar")
    rng = np.random.default_rng(5)
    root = manager.layout.root
    entries = [
        _entry(_build(root, "body-up", _jar(rng, False)), "body"),
        _entry(_build(root, "lid-up", _jar(rng, False)), "closure"),
        _entry(_build(root, "a-up", _jar(rng, False)), "assembled"),
    ]
    window.scene_panel.entries_provider = lambda: entries
    window.scene_panel.refresh()
    return window


def _views(window) -> tuple[ModelViewerView, MeasureDesignView]:
    viewer = window.route_stack.views[Route.MODEL_VIEWER]
    measure = window.route_stack.views[Route.MEASURE_DESIGN]
    assert isinstance(viewer, ModelViewerView) and isinstance(measure, MeasureDesignView)
    return viewer, measure


class _SlowReads:
    """Records which files the viewer reads and on which thread; each read takes ``delay``."""

    def __init__(self, monkeypatch, delay: float = 0.3) -> None:
        self.reads: list[tuple[str, str]] = []
        real = model_viewer.load_geometry

        def slow(path):
            self.reads.append((Path(path).parent.parent.parent.name, _thread()))
            time.sleep(delay)
            return real(path)

        monkeypatch.setattr(model_viewer, "load_geometry", slow)
        model_viewer.clear_cache()


def _thread() -> str:
    return threading.current_thread().name


def test_studio_tests_use_temporary_settings_not_the_registry() -> None:
    assert QSettings().format() is QSettings.Format.IniFormat


def test_views_and_scene_selection_survive_every_page_switch(app, tmp_path) -> None:  # noqa: F811
    window = _window(tmp_path)
    try:
        panel = window.scene_panel
        viewer, measure = _views(window)
        panel.tree.setCurrentItem(panel.items["assembled"])
        _pump(app, lambda: len(viewer.last_paths) == 3)
        window.navigation.navigate(Route.MEASURE_DESIGN)
        assert measure.use_latest_build()  # "Use selected part: Assembled"
        loaded = measure.viewer.service
        shown = viewer.service
        for route in Route:
            window.navigation.navigate(route)
            app.processEvents()
            window.navigation.navigate(Route.MEASURE_DESIGN)
            app.processEvents()
        assert measure.viewer.service is loaded and measure.model is not None
        assert viewer.service is shown and len(shown.scene.visible_objects()) == 3
        assert panel.view["part"] == "assembled"
        assert panel.tree.currentItem() is panel.items["assembled"]

        # Build page "measure" next step keeps the open model and offers the new build.
        builds = window.route_stack.views[Route.RECONSTRUCTION]
        body = panel.states["body"].cloud
        builds.result = SimpleNamespace(model_path=body)
        builds.route_requested.emit(Route.MEASURE_DESIGN.value)
        assert measure.viewer.service is loaded
        assert measure.newer_button.isVisibleTo(measure) and "newer build" in measure.status.text()
        assert measure.load_offered() and measure.model.path == body
        assert not measure.newer_button.isVisibleTo(measure)

        # Reload brings the last model back (fresh, like reopening it).
        assert measure.reload_button.isEnabled() and "scene_dense.ply" in (
            measure.reload_button.text()
        )
        assert measure.reload_last() and measure.model.path == body
    finally:
        window.close()


def test_finished_build_does_not_hijack_page_or_get_overwritten(
    app,  # noqa: F811
    tmp_path,
    monkeypatch,
) -> None:
    window = _window(tmp_path)
    try:
        panel = window.scene_panel
        viewer, _measure = _views(window)
        builds = window.route_stack.views[Route.RECONSTRUCTION]
        monkeypatch.setattr(builds, "show_result", lambda _result: None)
        panel.tree.setCurrentItem(panel.items["assembled"])
        _pump(app, lambda: len(viewer.last_paths) == 3)
        shown = viewer.service
        built = SimpleNamespace(
            status="succeeded", model_path=panel.states["body"].cloud, message="Model built."
        )

        # Owner on Measure & Design: an (auto-)build finishing changes neither page nor view.
        window.navigation.navigate(Route.MEASURE_DESIGN)
        window._on_build_finished(built)
        assert window.navigation.current_route is Route.MEASURE_DESIGN
        assert viewer.service is shown

        # Owner watching the Build page: taken to the result, which later Scene refreshes
        # (build_finished -> scene_panel.refresh) do not replace.
        window.navigation.navigate(Route.RECONSTRUCTION)
        window._on_build_finished(built)
        assert window.navigation.current_route is Route.MODEL_VIEWER
        opened = viewer.service
        assert opened is not shown and viewer.last_paths == (built.model_path,)
        panel._shown = None
        panel.refresh()
        _pump(app, lambda: True)
        time.sleep(0.2)
        app.processEvents()
        assert viewer.service is opened and viewer.pinned

        # Picking a part again is the owner's choice: the viewer follows it.
        panel.tree.setCurrentItem(panel.items["closure"])
        _pump(app, lambda: viewer.last_paths == (panel.states["closure"].cloud,))
        assert not viewer.pinned
    finally:
        window.close()


def test_auto_build_follows_only_from_import_pages(app, tmp_path, monkeypatch) -> None:  # noqa: F811
    window = _window(tmp_path)
    try:
        calls: list[bool] = []
        monkeypatch.setattr(
            window, "start_build", lambda _c, _d, navigate=True: calls.append(navigate)
        )
        inbox = window.route_stack.views[Route.CAPTURE_INBOX]
        settings = window.route_stack.views[Route.SETTINGS]
        settings.auto_build.setChecked(True)
        window.navigation.navigate(Route.MEASURE_DESIGN)
        inbox.scan_imported.emit("cap", "0" * 64)
        window.navigation.navigate(Route.CAPTURE_INBOX)
        inbox.scan_imported.emit("cap", "0" * 64)
        assert calls == [False, True]
    finally:
        window.close()


def test_part_load_runs_off_ui_thread_and_reload_hits_the_cache(
    app,  # noqa: F811
    tmp_path,
    monkeypatch,
) -> None:
    window = _window(tmp_path)
    try:
        viewer, _measure = _views(window)
        slow = _SlowReads(monkeypatch)
        panel = window.scene_panel
        before = viewer.service
        panel.tree.setCurrentItem(panel.items["body"])
        # the read runs on the worker: the service is unchanged right after the click
        assert viewer.service is before and "Loading" in viewer.status.text()
        _pump(app, lambda: viewer.last_paths)
        assert [thread for _name, thread in slow.reads] == ["packlab-viewer-load"]
        assert len(viewer.service.scene.visible_objects()) == 1
        assert viewer.reload_button.isEnabled()
        assert viewer.reload(background=False)
        assert len(slow.reads) == 1  # cached: unchanged file is not read again
    finally:
        window.close()


def test_rapid_loads_coalesce_and_empty_part_cancels_late_result(
    app,  # noqa: F811
    tmp_path,
    monkeypatch,
) -> None:
    window = _window(tmp_path)
    try:
        viewer, _measure = _views(window)
        states = window.scene_panel.states
        slow = _SlowReads(monkeypatch)
        first, middle, last = (states[part].cloud for part in ("body", "closure", "assembled"))
        viewer.load(first, background=True)
        _pump(app, lambda: slow.reads)
        viewer.load(middle, background=True)
        viewer.load(last, background=True)
        _pump(app, lambda: viewer.last_paths == (last,))
        assert [name for name, _thread in slow.reads] == ["body-up", "a-up"]  # middle skipped

        # Selection moves to a part without a scan while a read is running: no late repaint.
        shown = viewer.service
        model_viewer.clear_cache()
        viewer.load(first, background=True)
        _pump(app, lambda: len(slow.reads) == 3)
        window._show_part("closure", ())
        time.sleep(0.5)
        app.processEvents()
        assert viewer.service is shown and viewer.last_paths == (last,)
    finally:
        window.close()


def test_cache_is_bounded_by_shown_points(app, tmp_path, monkeypatch) -> None:  # noqa: F811
    window = _window(tmp_path)
    try:
        viewer, _measure = _views(window)
        states = window.scene_panel.states
        model_viewer.clear_cache()
        assert viewer.load(states["body"].cloud)
        count = next(iter(model_viewer._cache.values()))[2]
        monkeypatch.setattr(model_viewer, "CACHE_POINT_BUDGET", count + 1)
        assert viewer.load(states["closure"].cloud)
        assert [Path(key[0]) for key in model_viewer._cache] == [states["closure"].cloud]
    finally:
        model_viewer.clear_cache()
        window.close()
