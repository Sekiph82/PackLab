"""Reproducible M06 viewport display-budget benchmark."""

from __future__ import annotations

import json
import platform
import time
import tracemalloc
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize, qVersion

from packlab_studio.viewport import (
    MeshGeometry,
    PointCloudGeometry,
    SceneObjectKind,
    ViewportService,
)
from packlab_studio.viewport_lod import LODPolicy


def synthetic_points(count: int) -> tuple[tuple[float, float, float], ...]:
    return tuple((float(index % 997), float((index * 17) % 503), float((index * 7) % 311)) for index in range(count))


def synthetic_mesh(triangle_count: int) -> MeshGeometry:
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for index in range(triangle_count):
        base = len(vertices)
        x = float(index % 997)
        y = float((index * 17) % 503)
        vertices.extend(((x, y, 0.0), (x + 0.75, y, 0.0), (x, y + 0.75, 0.0)))
        triangles.append((base, base + 1, base + 2))
    return MeshGeometry(tuple(vertices), tuple(triangles))


def _benchmark_case(service: ViewportService, geometry_type: str, source_count: int, geometry, policy: LODPolicy) -> dict[str, object]:
    tracemalloc.reset_peak()
    setup_started = time.perf_counter()
    service.add_geometry("benchmark-object", SceneObjectKind.SCAN_MESH, geometry)
    setup_seconds = time.perf_counter() - setup_started
    plan = service.lod_plan("benchmark-object", policy)
    display_started = time.perf_counter()
    display, display_plan = service.display_geometry("benchmark-object", policy)
    display_seconds = time.perf_counter() - display_started
    proxy_service = ViewportService()
    proxy_service.add_geometry("benchmark-object", SceneObjectKind.SCAN_MESH, display)
    render_started = time.perf_counter()
    image = proxy_service.render(QSize(320, 240))
    render_seconds = time.perf_counter() - render_started
    interaction_started = time.perf_counter()
    for _ in range(8):
        proxy_service.orbit(1.0, 0.0)
    interaction_seconds = time.perf_counter() - interaction_started
    _current, peak = tracemalloc.get_traced_memory()
    return {
        "geometry_type": geometry_type,
        "source_primitive_count": source_count,
        "display_primitive_count": display_plan.display_count,
        "source_count": source_count,
        "display_count": display_plan.display_count,
        "lod": plan.to_dict(),
        "initialization_seconds": round(setup_seconds, 6),
        "initialize_seconds": round(setup_seconds, 6),
        "geometry_setup_seconds": round(setup_seconds, 6),
        "display_seconds": round(display_seconds, 6),
        "render_seconds": round(render_seconds, 6),
        "interaction_proxy_seconds": round(interaction_seconds, 6),
        "memory_peak_bytes": peak,
        "peak_tracemalloc_bytes": peak,
        "image_bytes": image.sizeInBytes(),
        "source_geometry_unchanged": service.scene.get("benchmark-object").geometry == geometry,
    }


def run_benchmark(counts: tuple[int, ...] = (1_000, 10_000, 50_000)) -> dict[str, Any]:
    policy = LODPolicy(display_budget=10_000)
    results: list[dict[str, object]] = []
    tracemalloc.start()
    for count in counts:
        service = ViewportService()
        results.append(_benchmark_case(service, "point-cloud", count, PointCloudGeometry(synthetic_points(count)), policy))
        mesh_service = ViewportService()
        results.append(_benchmark_case(mesh_service, "mesh", count, synthetic_mesh(count), policy))
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
        "workload_counts": {"point_cloud": list(counts), "mesh_triangles": list(counts)},
        "results": results,
        "limitations": [
            "Measurements are local software/offscreen proxies, not physical GPU throughput.",
            "Synthetic point and triangle counts are repository-safe and do not represent a calibrated scan.",
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
