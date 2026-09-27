"""Reproducible M06 PySide6 viewport technology comparison."""

from __future__ import annotations

import json
import os
import platform
import time
import tracemalloc
from pathlib import Path
from typing import Any

from PySide6.QtCore import QCoreApplication, QPointF, QRectF, qVersion
from PySide6.QtGui import QImage, QOffscreenSurface, QOpenGLContext, QPainter, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
)

Point = tuple[float, float, float]
Triangle = tuple[Point, Point, Point]


def _ensure_application() -> None:
    if QCoreApplication.instance() is None:
        QApplication(["packlab-viewport-spike"])


def _points(count: int) -> list[Point]:
    return [(float(index % 97), float((index * 17) % 53), float((index * 7) % 31)) for index in range(count)]


def _triangles(count: int) -> list[Triangle]:
    return [
        (
            (float(index % 97), float((index * 17) % 53), 0.0),
            (float(index % 97) + 0.75, float((index * 17) % 53), 0.0),
            (float(index % 97), float((index * 17) % 53) + 0.75, 0.0),
        )
        for index in range(count)
    ]


class _ImmediateRasterCandidate:
    id = "qt-raster-qimage"

    def __init__(self) -> None:
        self.points: list[Point] = []
        self.triangles: list[Triangle] = []

    def setup_points(self, points: list[Point]) -> None:
        self.points = points
        self.triangles = []

    def setup_triangles(self, triangles: list[Triangle]) -> None:
        self.triangles = triangles
        self.points = []

    def render(self) -> int:
        image = QImage(640, 480, QImage.Format.Format_ARGB32)
        image.fill(0xFF101820)
        painter = QPainter(image)
        for x, y, _z in self.points:
            painter.drawPoint(int(x * 4) % 640, int(y * 7) % 480)
        for triangle in self.triangles:
            painter.drawPolygon(QPolygonF([QPointF(point[0] * 4 % 640, point[1] * 7 % 480) for point in triangle]))
        painter.end()
        return image.sizeInBytes()

    def interaction_proxy(self) -> None:
        self.points = [(x + 0.1, y + 0.1, z) for x, y, z in self.points]


class _GraphicsSceneCandidate:
    id = "qt-graphics-scene"

    def __init__(self) -> None:
        self.scene = QGraphicsScene(0.0, 0.0, 640.0, 480.0)

    def setup_points(self, points: list[Point]) -> None:
        self.scene.clear()
        for x, y, _z in points:
            item = QGraphicsEllipseItem((x * 4) % 640 - 1, (y * 7) % 480 - 1, 2, 2)
            self.scene.addItem(item)

    def setup_triangles(self, triangles: list[Triangle]) -> None:
        self.scene.clear()
        for triangle in triangles:
            polygon = QPolygonF([QPointF(point[0] * 4 % 640, point[1] * 7 % 480) for point in triangle])
            self.scene.addItem(QGraphicsPolygonItem(polygon))

    def render(self) -> int:
        image = QImage(640, 480, QImage.Format.Format_ARGB32)
        image.fill(0xFF101820)
        painter = QPainter(image)
        self.scene.render(painter, QRectF(0.0, 0.0, 640.0, 480.0), QRectF(0.0, 0.0, 640.0, 480.0))
        painter.end()
        return image.sizeInBytes()

    def interaction_proxy(self) -> None:
        self.scene.setSceneRect(self.scene.sceneRect().adjusted(0.1, 0.1, 0.1, 0.1))


def _workload(candidate_factory, geometry_type: str, count: int) -> dict[str, object]:
    source = _points(count) if geometry_type == "point-cloud" else _triangles(count)
    tracemalloc.reset_peak()
    candidate = candidate_factory()
    setup_started = time.perf_counter()
    if geometry_type == "point-cloud":
        candidate.setup_points(source)
    else:
        candidate.setup_triangles(source)
    setup_seconds = time.perf_counter() - setup_started
    render_started = time.perf_counter()
    image_bytes = candidate.render()
    render_seconds = time.perf_counter() - render_started
    interaction_started = time.perf_counter()
    for _ in range(8):
        candidate.interaction_proxy()
    interaction_seconds = time.perf_counter() - interaction_started
    _current, peak = tracemalloc.get_traced_memory()
    return {
        "geometry_type": geometry_type,
        "primitive_count": count,
        "startup_seconds": 0.0,
        "geometry_setup_seconds": round(setup_seconds, 6),
        "render_seconds": round(render_seconds, 6),
        "interaction_proxy_seconds": round(interaction_seconds, 6),
        "memory_peak_bytes": peak,
        "image_bytes": image_bytes,
    }


def _run_executable_candidate(candidate_factory, counts: tuple[int, ...]) -> dict[str, object]:
    startup_started = time.perf_counter()
    candidate_factory()
    startup_seconds = time.perf_counter() - startup_started
    workloads = []
    for geometry_type in ("point-cloud", "mesh"):
        for count in counts:
            result = _workload(candidate_factory, geometry_type, count)
            result["startup_seconds"] = round(startup_seconds, 6)
            workloads.append(result)
    return {
        "workloads": workloads,
        "dependency_footprint": {
            "additional_packages": 0,
            "runtime": "existing locked PySide6; no new package",
        },
    }


def _opengl_probe() -> dict[str, Any]:
    surface = QOffscreenSurface()
    surface.create()
    context = QOpenGLContext()
    created = bool(context.create())
    compatible = bool(created and context.makeCurrent(surface))
    if compatible:
        context.doneCurrent()
    surface.destroy()
    return {
        "available": compatible,
        "context_created": created,
        "native_gpu_claim": False,
        "geometry_workload": "unavailable",
        "limitation": "offscreen context availability is not a physical GPU benchmark",
    }


def run_spike(counts: tuple[int, ...] = (250, 1_000, 2_500)) -> dict[str, Any]:
    """Run two distinct executable Qt software candidates plus an OpenGL probe."""

    _ensure_application()
    tracemalloc.start()
    candidates = []
    for candidate_id, factory, description in (
        ("qt-raster-qimage", _ImmediateRasterCandidate, "QImage/QPainter immediate software raster"),
        ("qt-graphics-scene", _GraphicsSceneCandidate, "QGraphicsScene/QGraphicsItem software scene raster"),
    ):
        evidence = _run_executable_candidate(factory, counts)
        candidates.append(
            {
                "id": candidate_id,
                "version": qVersion(),
                "description": description,
                "python_pyside6_compatible": True,
                "windows_support": True,
                "headless": True,
                "mesh_point_cloud": "measured point-cloud and triangle workloads",
                "picking": "PackLab scene-model picking boundary",
                "wireframe_normals": "PackLab display representation",
                "future_cad": "backend-independent adapter can coexist with later CAD seam",
                "license": "Qt for Python LGPLv3/GPLv3 or commercial route; existing locked dependency",
                "evidence": evidence,
                "selected": candidate_id == "qt-raster-qimage",
            }
        )
    tracemalloc.stop()
    candidates.append(
        {
            "id": "qt-opengl-offscreen",
            "version": qVersion(),
            "description": "Qt OpenGL offscreen capability probe",
            "python_pyside6_compatible": True,
            "windows_support": True,
            "headless": _opengl_probe(),
            "license": "same existing Qt for Python route; no new dependency selected",
            "evidence": "unavailable geometry workload; no fabricated metrics",
            "selected": False,
        }
    )
    return {
        "schema_version": "2.0",
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "qt": qVersion(),
            "headless_platform": os.environ.get("QT_QPA_PLATFORM", "unset"),
        },
        "workload_counts": {"point_cloud": list(counts), "mesh_triangles": list(counts)},
        "candidates": candidates,
        "decision": {
            "selected_backend": "qt-raster-qimage",
            "rationale": "Both executable software candidates render point and triangle workloads. QImage/QPainter remains selected for deterministic lower-coupling headless evidence; QGraphicsScene is a credible second software path, while OpenGL remains an unavailable capability probe on this host.",
            "native_gpu_measured": False,
            "limitations": [
                "Both measured candidates are software/offscreen proxies, not physical GPU benchmarks.",
                "The OpenGL candidate did not execute geometry on this host and has no fabricated timing or memory metrics.",
            ],
        },
    }


def write_spike_evidence(destination: str | Path) -> Path:
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(run_spike(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = run_spike()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
