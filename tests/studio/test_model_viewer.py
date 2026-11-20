from __future__ import annotations

import os
import struct
from pathlib import Path

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage

from packlab_studio.app import create_application
from packlab_studio.model_viewer import ModelViewerView
from packlab_studio.navigation import Route
from packlab_studio.viewport import (
    MeshGeometry,
    PointCloudGeometry,
    SceneObjectKind,
    ViewportErrorCode,
    ViewportLoadError,
    ViewportService,
    load_geometry,
)

COLORS = ((255, 0, 0), (0, 255, 0), (0, 0, 255), (250, 250, 0))
POINTS = ((0.0, 0.0, 0.0), (40.0, 0.0, 0.0), (0.0, 40.0, 0.0), (0.0, 0.0, 40.0))


def _binary_dense_ply(path: Path) -> Path:
    """OpenMVS-style layout: float xyz, uchar rgb, float normal, then variable lists."""

    header = (
        "ply\nformat binary_little_endian 1.0\nelement vertex 4\n"
        "property float x\nproperty float y\nproperty float z\n"
        "property uchar red\nproperty uchar green\nproperty uchar blue\n"
        "property float nx\nproperty float ny\nproperty float nz\n"
        "property list uchar uint view_indices\nproperty list uchar float view_weights\n"
        "end_header\n"
    ).encode("ascii")
    body = b""
    for index, (point, color) in enumerate(zip(POINTS, COLORS)):
        views = list(range(index + 1))
        body += struct.pack("<3f3B3f", *point, *color, 0.0, 0.0, 1.0)
        body += struct.pack(f"<B{len(views)}I", len(views), *views)
        body += struct.pack(f"<B{len(views)}f", len(views), *([0.5] * len(views)))
    path.write_bytes(header + body)
    return path


def _binary_mesh_ply(path: Path) -> Path:
    header = (
        "ply\nformat binary_little_endian 1.0\nelement vertex 3\n"
        "property float x\nproperty float y\nproperty float z\n"
        "element face 1\nproperty list uchar int vertex_indices\nend_header\n"
    ).encode("ascii")
    body = struct.pack("<9f", 0, 0, 0, 10, 0, 0, 0, 10, 0) + struct.pack("<B3i", 3, 0, 1, 2)
    path.write_bytes(header + body)
    return path


def _colored_pixels(image: QImage) -> int:
    count = 0
    for y in range(0, image.height(), 2):
        for x in range(0, image.width(), 2):
            color = image.pixelColor(x, y)
            if (color.red(), color.green(), color.blue()) in {(255, 0, 0), (0, 0, 255)}:
                count += 1
    return count


def test_binary_and_ascii_colored_ply_load_exactly(tmp_path) -> None:
    cloud = load_geometry(_binary_dense_ply(tmp_path / "dense.ply"))
    assert isinstance(cloud, PointCloudGeometry)
    assert cloud.points == POINTS and cloud.colors == COLORS
    ascii_ply = tmp_path / "crop.ply"
    ascii_ply.write_text(
        "ply\nformat ascii 1.0\nelement vertex 2\nproperty double x\nproperty double y\n"
        "property double z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\n"
        "end_header\n0.5 -0.5 0.25 218 221 224\n1 2 3 1 2 3\n",
        encoding="ascii",
    )
    crop = load_geometry(ascii_ply)
    assert isinstance(crop, PointCloudGeometry)
    assert crop.points[0] == (0.5, -0.5, 0.25) and crop.colors[0] == (218, 221, 224)
    mesh = load_geometry(_binary_mesh_ply(tmp_path / "mesh.ply"))
    assert isinstance(mesh, MeshGeometry) and mesh.triangles == ((0, 1, 2),)
    truncated = tmp_path / "truncated.ply"
    truncated.write_bytes((tmp_path / "dense.ply").read_bytes()[:-5])
    with pytest.raises(ViewportLoadError) as error:
        load_geometry(truncated)
    assert error.value.code is ViewportErrorCode.CORRUPT


def test_colored_cloud_renders_and_orbit_changes_image(tmp_path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    create_application(["packlab-model-viewer-render"])
    service = ViewportService()
    service.load("cloud", SceneObjectKind.SCAN_MESH, _binary_dense_ply(tmp_path / "dense.ply"))
    service.fit_to_view()
    first = service.render(QSize(320, 240))
    assert _colored_pixels(first) > 0  # per-point colors survive to pixels
    service.orbit(60, 20)
    assert service.render(QSize(320, 240)) != first


def test_model_viewer_route_opens_file_and_responds_to_orbit_zoom_fit(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-model-viewer-route"])
    from packlab_studio.shell import StudioMainWindow

    window = StudioMainWindow(
        diagnostics_root=tmp_path / "diagnostics", packaging_library_root=tmp_path / "library"
    )
    try:
        view = window.route_stack.views[Route.MODEL_VIEWER]
        assert isinstance(view, ModelViewerView) and view.isEnabled()
        path = _binary_dense_ply(tmp_path / "dense.ply")
        view._choose_file = lambda _parent: str(path)
        view.open_button.click()
        assert "4 colored points" in view.status.text()
        before = view.canvas.pixmap().toImage()
        view.orbit(45, 10)
        orbited = view.canvas.pixmap().toImage()
        assert orbited != before
        view.zoom(0.5)
        assert view.canvas.pixmap().toImage() != orbited
        view.fit_button.click()
        assert view.service.state.camera.distance > 0
        bad = tmp_path / "bad.ply"
        bad.write_bytes(b"not a ply")
        assert not view.load(bad) and "Cannot open bad.ply" in view.status.text()
    finally:
        window.close()
        app.processEvents()
