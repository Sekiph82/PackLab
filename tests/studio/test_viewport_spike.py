from __future__ import annotations

from tools.viewport_spike import run_spike


def test_viewport_spike_compares_two_pyside6_compatible_candidates(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    evidence = run_spike((32, 128))
    assert {item["id"] for item in evidence["candidates"]} == {
        "qt-raster-qimage",
        "qt-graphics-scene",
        "qt-opengl-offscreen",
    }
    selected = next(item for item in evidence["candidates"] if item["selected"])
    assert selected["id"] == "qt-raster-qimage"
    assert {item["geometry_type"] for item in selected["evidence"]["workloads"]} == {
        "point-cloud",
        "mesh",
    }
    assert all(
        item["geometry_setup_seconds"] >= 0 and item["memory_peak_bytes"] >= 0
        for item in selected["evidence"]["workloads"]
    )
    scene = next(item for item in evidence["candidates"] if item["id"] == "qt-graphics-scene")
    assert len(scene["evidence"]["workloads"]) == 4
    assert evidence["decision"]["native_gpu_measured"] is False
