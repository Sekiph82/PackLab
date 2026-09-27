from __future__ import annotations

from tools.viewport_spike import run_spike


def test_viewport_spike_compares_two_pyside6_compatible_candidates(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    evidence = run_spike((32, 128))
    assert {item["id"] for item in evidence["candidates"]} == {
        "qt-raster-qimage",
        "qt-opengl-offscreen",
    }
    selected = next(item for item in evidence["candidates"] if item["selected"])
    assert selected["id"] == "qt-raster-qimage"
    assert [item["count"] for item in selected["evidence"]] == [32, 128]
    assert evidence["decision"]["native_gpu_measured"] is False
