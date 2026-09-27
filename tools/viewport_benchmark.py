"""Reproducible M06 viewport display-budget benchmark."""

from __future__ import annotations

import json
import platform
import time
import tracemalloc
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize, qVersion

from packlab_studio.viewport import PointCloudGeometry, SceneObjectKind, ViewportService
from packlab_studio.viewport_lod import LODPolicy


def synthetic_points(count: int) -> tuple[tuple[float, float, float], ...]:
    return tuple((float(index % 997), float((index * 17) % 503), float((index * 7) % 311)) for index in range(count))


def run_benchmark(counts: tuple[int, ...] = (1_000, 10_000, 50_000)) -> dict[str, Any]:
    policy = LODPolicy(display_budget=10_000)
    results: list[dict[str, object]] = []
    tracemalloc.start()
    for count in counts:
        service = ViewportService()
        started = time.perf_counter()
        service.add_geometry("scan-mesh", SceneObjectKind.SCAN_MESH, PointCloudGeometry(synthetic_points(count)))
        initialized = time.perf_counter() - started
        plan = service.lod_plan("scan-mesh", policy)
        display_started = time.perf_counter()
        display, display_plan = service.display_geometry("scan-mesh", policy)
        display_seconds = time.perf_counter() - display_started
        render_started = time.perf_counter()
        image = service.adapter.render(
            service.scene.__class__(), service.state, QSize(320, 240)
        )
        # Render proxy above is intentionally empty; the display path is measured below.
        proxy_service = ViewportService()
        proxy_service.add_geometry("scan-mesh", SceneObjectKind.SCAN_MESH, display)
        image = proxy_service.render(QSize(320, 240))
        render_seconds = time.perf_counter() - render_started
        _current, peak = tracemalloc.get_traced_memory()
        results.append(
            {
                "source_count": count,
                "display_count": display_plan.display_count,
                "lod": plan.to_dict(),
                "initialize_seconds": round(initialized, 6),
                "display_seconds": round(display_seconds, 6),
                "render_seconds": round(render_seconds, 6),
                "image_bytes": image.sizeInBytes(),
                "peak_tracemalloc_bytes": peak,
            }
        )
    tracemalloc.stop()
    return {
        "schema_version": "1.0",
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "qt": qVersion(),
            "headless_platform": __import__("os").environ.get("QT_QPA_PLATFORM", "unset"),
            "backend": "qt-raster-qimage",
            "native_gpu_claim": False,
        },
        "policy": {"display_budget": policy.display_budget, "decimation": "deterministic-stride"},
        "results": results,
        "limitations": [
            "Measurements are local software/offscreen proxies, not physical GPU throughput.",
            "Synthetic point counts are repository-safe and do not represent a calibrated scan.",
        ],
    }


def write_benchmark_evidence(destination: str | Path) -> Path:
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(run_benchmark(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = run_benchmark()
    if args.output:
        write_benchmark_evidence(args.output)
    print(json.dumps(evidence, indent=2, sort_keys=True))
