"""Loaded views survive page switches; part clouds load off the UI thread (SYNTHETIC data)."""

from __future__ import annotations

import threading
import time
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


def test_views_and_scene_selection_survive_every_page_switch(app, tmp_path) -> None:  # noqa: F811
    window = _window(tmp_path)
    try:
        panel = window.scene_panel
        viewer = window.route_stack.views[Route.MODEL_VIEWER]
        measure = window.route_stack.views[Route.MEASURE_DESIGN]
        assert isinstance(viewer, ModelViewerView) and isinstance(measure, MeasureDesignView)
        measure.settings = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
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

        # Build page "measure" next step must not swap out the model already open.
        builds = window.route_stack.views[Route.RECONSTRUCTION]
        builds.result = SimpleNamespace(model_path=panel.states["body"].cloud)
        builds.route_requested.emit(Route.MEASURE_DESIGN.value)
        assert measure.viewer.service is loaded

        # Reload brings the last model back (fresh, like reopening it).
        assert measure.reload_button.isEnabled() and "scene_dense.ply" in (
            measure.reload_button.text()
        )
        assert measure.reload_last() and measure.model.path == panel.states["assembled"].cloud
    finally:
        window.close()


def test_part_load_runs_off_ui_thread_and_reload_hits_the_cache(app, tmp_path) -> None:  # noqa: F811
    window = _window(tmp_path)
    try:
        viewer = window.route_stack.views[Route.MODEL_VIEWER]
        assert isinstance(viewer, ModelViewerView)
        threads: list[str] = []
        real = model_viewer.load_geometry

        def slow(path):
            threads.append(threading.current_thread().name)
            time.sleep(0.3)
            return real(path)

        model_viewer.load_geometry = slow
        model_viewer._display.cache_clear()
        try:
            panel = window.scene_panel
            before = viewer.service
            started = time.perf_counter()
            panel.tree.setCurrentItem(panel.items["body"])
            assert time.perf_counter() - started < 0.3  # UI thread not blocked by the read
            assert viewer.service is before and "Loading" in viewer.status.text()
            _pump(app, lambda: viewer.last_paths)
            assert threads == ["packlab-viewer-load"]
            assert len(viewer.service.scene.visible_objects()) == 1
            assert viewer.reload_button.isEnabled()
            assert viewer.reload(background=False)
            assert len(threads) == 1  # cached: unchanged file is not read again
        finally:
            model_viewer.load_geometry = real
    finally:
        window.close()
