"""Reproducible M06 PySide6 viewport technology spike."""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import qVersion
from PySide6.QtGui import QGuiApplication, QImage, QOffscreenSurface, QOpenGLContext, QPainter


def _points(count: int) -> list[tuple[float, float, float]]:
    return [
        (float(index % 97), float((index * 17) % 53), float((index * 7) % 31))
        for index in range(count)
    ]


def _raster_proxy(points: list[tuple[float, float, float]]) -> tuple[float, int]:
    started = time.perf_counter()
    image = QImage(640, 480, QImage.Format.Format_ARGB32)
    image.fill(0xFF101820)
    painter = QPainter(image)
    for x, y, _z in points:
        painter.drawPoint(int(x * 4) % 640, int(y * 7) % 480)
    painter.end()
    return time.perf_counter() - started, image.sizeInBytes()


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
        "limitation": "offscreen context availability is not a physical GPU benchmark",
    }


def run_spike(counts: tuple[int, ...] = (1_000, 10_000, 50_000)) -> dict[str, Any]:
    """Run both candidate proxies and return JSON-serializable evidence."""

    if QGuiApplication.instance() is None:
        QGuiApplication(["packlab-viewport-spike"])
    raster_results = []
    for count in counts:
        elapsed, image_bytes = _raster_proxy(_points(count))
        raster_results.append(
            {
                "count": count,
                "render_seconds": round(elapsed, 6),
                "image_bytes": image_bytes,
                "proxy": "QPainter/QImage software raster",
            }
        )
    return {
        "schema_version": "1.0",
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "qt": qVersion(),
            "headless_platform": __import__("os").environ.get("QT_QPA_PLATFORM", "unset"),
        },
        "candidates": [
            {
                "id": "qt-raster-qimage",
                "version": qVersion(),
                "python_pyside6_compatible": True,
                "windows_support": True,
                "headless": True,
                "mesh_point_cloud": "software projected mesh and point cloud primitives",
                "picking": "PackLab scene-model picking boundary",
                "wireframe_normals": "PackLab display representation",
                "future_cad": "backend-independent adapter can coexist with later CAD seam",
                "license": "Qt for Python LGPLv3/GPLv3 or commercial route; existing locked dependency",
                "evidence": raster_results,
                "selected": True,
            },
            {
                "id": "qt-opengl-offscreen",
                "version": qVersion(),
                "python_pyside6_compatible": True,
                "windows_support": True,
                "headless": _opengl_probe(),
                "mesh_point_cloud": "native OpenGL primitives when context is available",
                "picking": "requires additional GPU/render-picking implementation",
                "wireframe_normals": "requires shader/state implementation",
                "future_cad": "possible but increases native/GPU coupling",
                "license": "same existing Qt for Python route; no new dependency selected",
                "evidence": "context probe only; no physical GPU performance claim",
                "selected": False,
            },
        ],
        "decision": {
            "selected_backend": "qt-raster-qimage",
            "rationale": "It is deterministic and executable in the repository's offscreen/headless test environment without claiming native GPU performance or adding a dependency.",
            "native_gpu_measured": False,
            "limitations": [
                "QPainter/QImage evidence is a software/offscreen proxy, not a physical GPU benchmark.",
                "Large-scene performance requires the later display-budget/LOD policy.",
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
        write_spike_evidence(args.output)
    print(json.dumps(evidence, indent=2, sort_keys=True))
