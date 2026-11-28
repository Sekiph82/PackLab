"""Model Viewer route: open a mesh/point cloud and inspect it with the Qt raster viewport."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import replace
from functools import partial
from pathlib import Path

import numpy as np
from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .viewport import (
    Geometry,
    PointCloudGeometry,
    SceneObjectKind,
    ViewportCamera,
    ViewportLoadError,
    ViewportService,
    load_geometry,
)
from .viewport_lod import LODPolicy, display_geometry, geometry_count

MODEL_FILTER = "3D models (*.ply *.obj *.xyz *.pts *.pcd)"
# ponytail: stride decimation. Colored/large clouds splat vectorized (~50 ms per 200k
# points); meshes still draw per triangle in Python, so they get a small budget.
POINT_DISPLAY_BUDGET = 400_000
MESH_DISPLAY_BUDGET = 20_000
# Camera distance per model radius: the model spans about 80 % of the shorter side.
FIT_DISTANCE_PER_RADIUS = 2.0


# Decoded display geometry per file version, newest last. Python tuples cost ~215 bytes
# per shown point (a 400k colored cloud measured ~86 MB), so the budget is in points.
CACHE_POINT_BUDGET = 2_000_000  # ~430 MB
_cache: OrderedDict[tuple[str, int, int], tuple[Geometry, str, int]] = OrderedDict()
_cache_lock = threading.Lock()


def _display(path: str, mtime_ns: int, size: int) -> tuple[Geometry, str]:
    """Read and decimate one model file; cached per file version so re-showing is instant."""
    key = (path, mtime_ns, size)
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            shown, note, _count = _cache[key]
            return shown, note
    geometry = load_geometry(path)
    is_cloud = isinstance(geometry, PointCloudGeometry)
    budget = POINT_DISPLAY_BUDGET if is_cloud else MESH_DISPLAY_BUDGET
    shown, plan = display_geometry(geometry, LODPolicy(display_budget=budget))
    colored = " colored" if is_cloud and geometry.colors else ""  # type: ignore[union-attr]
    kind = "points" if is_cloud else "triangles"
    shown_note = "" if plan.stride == 1 else f", showing {plan.display_count:,}"
    note = f"{Path(path).name}: {geometry_count(geometry):,}{colored} {kind}{shown_note}"
    count = len(shown.points if isinstance(shown, PointCloudGeometry) else shown.vertices)
    with _cache_lock:
        _cache[key] = (shown, note, count)
        while len(_cache) > 1 and sum(item[2] for item in _cache.values()) > CACHE_POINT_BUDGET:
            _cache.popitem(last=False)
    return shown, note


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()


Box = tuple[tuple[float, float, float], float]


def _fit_box(geometries: list[Geometry]) -> Box | None:
    """Centre and radius of the 2nd-98th percentile box (clouds) or full extent (meshes).

    A few far SfM outliers cannot shrink the model or push it off-centre."""
    arrays = [
        np.asarray(
            item.points if isinstance(item, PointCloudGeometry) else item.vertices, dtype=float
        ).reshape(-1, 3)
        for item in geometries
    ]
    values = np.concatenate(arrays) if arrays else np.empty((0, 3))
    if not len(values):
        return None
    # Meshes have uneven vertex density (a fine cap ring), so they use their full extent.
    robust = all(isinstance(item, PointCloudGeometry) for item in geometries)
    low = np.percentile(values, 2 if robust else 0, axis=0)
    high = np.percentile(values, 98 if robust else 100, axis=0)
    centre = (float(low[0] + high[0]) / 2, float(low[1] + high[1]) / 2, float(low[2] + high[2]) / 2)
    return centre, max(float(np.linalg.norm(high - low)) / 2, 1e-6)


ReadResult = tuple[list[tuple[Geometry, str]], Box | None]


def _read(
    paths: tuple[Path, ...], stale: Callable[[], bool] = lambda: False
) -> ReadResult | str | None:
    """Display geometry + fit box, an owner-facing error, or None once superseded."""
    shown = []
    for item in paths:
        if stale():
            return None  # a newer load was asked for: stop reading
        try:
            stat = item.stat()
            shown.append(_display(str(item), stat.st_mtime_ns, stat.st_size))
        except ViewportLoadError as error:
            return f"Cannot open {item.name}: {error} ({error.code.value})"
        except OSError as error:
            return f"Cannot open {item.name}: {error}"
    return shown, _fit_box([geometry for geometry, _note in shown])


class ViewportCanvas(QLabel):
    """Shows rendered frames; left drag orbits, other drags pan, wheel zooms."""

    def __init__(self, viewer: ModelViewerView) -> None:
        super().__init__(viewer)
        self.viewer = viewer
        self._last: QPoint | None = None
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._last = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._last is None:
            return
        position = event.position().toPoint()
        delta = position - self._last
        self._last = position
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.viewer.orbit(delta.x() * 0.4, delta.y() * 0.4)
        else:
            self.viewer.pan(delta.x(), delta.y())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._last = None

    def wheelEvent(self, event: QWheelEvent) -> None:
        self.viewer.zoom(0.9 ** (event.angleDelta().y() / 120))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.viewer.redraw()


class ModelViewerView(QWidget):
    _read_done = Signal(object, object, object, float)  # token, paths, shown | error, started

    def __init__(self, *, file_chooser: Callable[[QWidget], str] | None = None) -> None:
        super().__init__()
        self.setObjectName("packlab.view.model-viewer")
        self.service = ViewportService()
        self._choose_file = file_chooser or (
            lambda parent: QFileDialog.getOpenFileName(parent, "Open model", "", MODEL_FILTER)[0]
        )
        self.open_button = QPushButton("Open model…", self)
        self.fit_button = QPushButton("Fit", self)
        # Shows the last model(s) again (cached: no re-read unless the file changed).
        self.reload_button = QPushButton("Reload last model", self)
        self.reload_button.setObjectName("packlab.viewer.reload")
        self.reload_button.setEnabled(False)
        self.last_paths: tuple[Path, ...] = ()
        self._pending: object | None = None
        self._next: tuple[object, tuple[Path, ...], float] | None = None
        self._lock = threading.Lock()
        self._worker_running = False
        self.pinned = False  # the owner opened this model; Scene refreshes keep it
        self._read_done.connect(self._finish_read)
        self.status = QLabel("No model loaded. Drag to orbit, right-drag to pan, wheel to zoom.")
        self.status.setWordWrap(True)
        self.canvas = ViewportCanvas(self)
        buttons = QHBoxLayout()
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.fit_button)
        buttons.addWidget(self.reload_button)
        buttons.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(self.status)
        layout.addWidget(self.canvas, 1)
        self.open_button.clicked.connect(self.open_model)
        self.fit_button.clicked.connect(self.fit)
        self.reload_button.clicked.connect(lambda: self.reload())

    def open_model(self) -> None:
        chosen = self._choose_file(self)
        if chosen and self.load(Path(chosen)):
            self.pinned = True

    def load(self, path: Path, *more: Path, background: bool = False) -> bool:
        """Show one model, or several side by side (project parts, PL-0485).

        ``background`` reads the files on one worker thread (large part clouds froze the UI
        for up to a minute); the current view stays until the new one is ready, and only the
        newest request is read (superseded ones stop between files).
        """
        paths = tuple(Path(item) for item in (path, *more))
        started = time.perf_counter()
        token = object()
        self._pending = token
        if not background:
            return self._finish_read(token, paths, _read(paths), started)
        self.status.setText(f"Loading {', '.join(item.name for item in paths)}…")
        with self._lock:
            self._next = (token, paths, started)
            if self._worker_running:
                return True
            self._worker_running = True
        threading.Thread(target=self._work, name="packlab-viewer-load", daemon=True).start()
        return True

    def cancel_load(self) -> None:
        """Drop any pending load: a late result must not repaint the view."""
        self._pending = None

    def _work(self) -> None:
        while True:
            with self._lock:
                job, self._next = self._next, None
                if job is None:
                    self._worker_running = False
                    return
            token, paths, started = job
            try:
                result: object = _read(paths, partial(self._superseded, token))
            except Exception as error:  # never lose a failure on the worker thread
                result = f"Cannot open: {error}"
            if result is None:
                continue
            try:
                self._read_done.emit(token, paths, result, started)
            except RuntimeError:
                return  # the view was destroyed while reading

    def _superseded(self, token: object) -> bool:
        return self._pending is not token

    def reload(self, background: bool = True) -> bool:
        return bool(self.last_paths) and self.load(*self.last_paths, background=background)

    def _finish_read(self, token: object, paths: tuple[Path, ...], result, started) -> bool:
        if token is not self._pending:
            return False  # a newer load (or a cancel) superseded this one
        self._pending = None
        if result is None:
            return False
        if isinstance(result, str):
            self.status.setText(result)
            return False
        shown, box = result
        service = ViewportService(self.service.adapter)
        for index, (geometry, _note) in enumerate(shown):
            service.add_geometry(
                "model" if index == 0 else f"model-{index}", SceneObjectKind.SCAN_MESH, geometry
            )
        self.service = service
        self.last_paths = paths
        self.reload_button.setEnabled(True)
        notes = "; ".join(note for _geometry, note in shown)
        self.status.setText(
            f"{notes} (loaded in {time.perf_counter() - started:.1f} s). "
            "Units as stored in the file."
        )
        self._centre(box)  # computed with the read: no percentile pass on the UI thread
        return True

    def fit(self) -> None:
        """Centre on the visible model(s) and fill the view (F8); any unit scale."""
        self._centre(
            _fit_box(
                [
                    item.geometry
                    for item in self.service.scene.visible_objects()
                    if item.geometry is not None
                ]
            )
        )

    def _centre(self, box: Box | None) -> None:
        if box is not None:
            centre, radius = box
            camera = self.service.state.camera
            self.service.state = replace(
                self.service.state,
                camera=ViewportCamera(
                    centre,
                    radius * FIT_DISTANCE_PER_RADIUS,
                    camera.yaw_degrees,
                    camera.pitch_degrees,
                ),
            )
        self.redraw()

    def orbit(self, yaw: float, pitch: float) -> None:
        self.service.orbit(yaw, pitch)
        self.redraw()

    def pan(self, dx_pixels: int, dy_pixels: int) -> None:
        step = self.service.state.camera.distance / max(
            1, min(self.canvas.width(), self.canvas.height())
        )
        self.service.pan(dx_pixels * step, -dy_pixels * step)
        self.redraw()

    def zoom(self, factor: float) -> None:
        self.service.zoom(factor)
        self.redraw()

    def redraw(self) -> None:
        size = self.canvas.size()
        if size.width() < 2 or size.height() < 2:
            size = QSize(640, 480)
        self.canvas.setPixmap(QPixmap.fromImage(self.service.render(size)))
