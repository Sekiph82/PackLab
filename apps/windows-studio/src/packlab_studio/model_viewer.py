"""Model Viewer route: open a mesh/point cloud and inspect it with the Qt raster viewport."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import replace
from functools import lru_cache
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


@lru_cache(maxsize=4)
def _display(path: str, _mtime_ns: int, _size: int) -> tuple[Geometry, str]:
    """Read and decimate one model file; cached per file version so re-showing is instant.

    ponytail: 4 recent files (~50 MB each at the 400k display budget); widen if owners
    flip between more models.
    """
    geometry = load_geometry(path)
    is_cloud = isinstance(geometry, PointCloudGeometry)
    budget = POINT_DISPLAY_BUDGET if is_cloud else MESH_DISPLAY_BUDGET
    shown, plan = display_geometry(geometry, LODPolicy(display_budget=budget))
    colored = " colored" if is_cloud and geometry.colors else ""  # type: ignore[union-attr]
    kind = "points" if is_cloud else "triangles"
    shown_note = "" if plan.stride == 1 else f", showing {plan.display_count:,}"
    return shown, f"{Path(path).name}: {geometry_count(geometry):,}{colored} {kind}{shown_note}"


def _read(paths: tuple[Path, ...]) -> list[tuple[Geometry, str]] | str:
    """Display geometry per path, or the owner-facing error of the first unreadable one."""
    shown = []
    for item in paths:
        try:
            stat = item.stat()
            shown.append(_display(str(item), stat.st_mtime_ns, stat.st_size))
        except ViewportLoadError as error:
            return f"Cannot open {item.name}: {error} ({error.code.value})"
        except OSError as error:
            return f"Cannot open {item.name}: {error}"
    return shown


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
        if chosen:
            self.load(Path(chosen))

    def load(self, path: Path, *more: Path, background: bool = False) -> bool:
        """Show one model, or several side by side (project parts, PL-0485).

        ``background`` reads the files on a worker thread (large part clouds froze the UI
        for up to a minute); the current view stays until the new one is ready.
        """
        paths = tuple(Path(item) for item in (path, *more))
        started = time.perf_counter()
        token = object()
        self._pending = token
        if not background:
            return self._finish_read(token, paths, _read(paths), started)
        self.status.setText(f"Loading {', '.join(item.name for item in paths)}…")

        def work() -> None:
            try:
                result: object = _read(paths)
            except Exception as error:  # never lose a failure on the worker thread
                result = f"Cannot open: {error}"
            try:
                self._read_done.emit(token, paths, result, started)
            except RuntimeError:
                pass  # the view was destroyed while reading

        threading.Thread(target=work, name="packlab-viewer-load", daemon=True).start()
        return True

    def reload(self, background: bool = True) -> bool:
        return bool(self.last_paths) and self.load(*self.last_paths, background=background)

    def _finish_read(self, token: object, paths: tuple[Path, ...], result, started) -> bool:
        if token is not self._pending:
            return False  # a newer load superseded this one
        self._pending = None
        if isinstance(result, str):
            self.status.setText(result)
            return False
        service = ViewportService(self.service.adapter)
        for index, (shown, _note) in enumerate(result):
            service.add_geometry(
                "model" if index == 0 else f"model-{index}", SceneObjectKind.SCAN_MESH, shown
            )
        self.service = service
        self.last_paths = paths
        self.reload_button.setEnabled(True)
        notes = "; ".join(note for _shown, note in result)
        self.status.setText(
            f"{notes} (loaded in {time.perf_counter() - started:.1f} s). "
            "Units as stored in the file."
        )
        self.fit()
        return True

    def fit(self) -> None:
        """Centre on the model and fill the view (F8).

        Uses the 2nd-98th percentile box of the shown points so a few far SfM outliers
        cannot shrink the model or push it off-centre; works for any unit scale.
        """
        points = [
            point
            for item in self.service.scene.visible_objects()
            if item.geometry is not None
            for point in (
                item.geometry.points
                if isinstance(item.geometry, PointCloudGeometry)
                else item.geometry.vertices
            )
        ]
        if points:
            values = np.asarray(points, dtype=float)
            # Clouds: robust box against outliers. Meshes have uneven vertex density
            # (a fine cap ring), so they use their full extent.
            robust = all(
                isinstance(item.geometry, PointCloudGeometry)
                for item in self.service.scene.visible_objects()
            )
            low = np.percentile(values, 2 if robust else 0, axis=0)
            high = np.percentile(values, 98 if robust else 100, axis=0)
            radius = max(float(np.linalg.norm(high - low)) / 2, 1e-6)
            camera = self.service.state.camera
            self.service.state = replace(
                self.service.state,
                camera=ViewportCamera(
                    tuple(float(value) for value in (low + high) / 2),  # type: ignore[arg-type]
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
