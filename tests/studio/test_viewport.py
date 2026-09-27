from __future__ import annotations

import hashlib

import pytest
from PySide6.QtCore import QSize

from packlab_studio.viewport import (
    MeshGeometry,
    PointCloudGeometry,
    SceneObjectKind,
    ViewportErrorCode,
    ViewportLoadError,
    ViewportService,
    axis_metadata,
    grid_spec,
    load_geometry,
)


def test_obj_and_point_cloud_loaders_preserve_source_bytes_and_metadata(tmp_path) -> None:
    obj = tmp_path / "model.obj"
    obj.write_text("v 0 0 0\nv 10 0 0\nv 0 10 0\nf 1 2 3\n", encoding="utf-8")
    points = tmp_path / "points.xyz"
    points.write_text("0 0 0\n10 2 1\n", encoding="utf-8")
    obj_digest = hashlib.sha256(obj.read_bytes()).hexdigest()
    mesh = load_geometry(obj)
    cloud = load_geometry(points)
    assert isinstance(mesh, MeshGeometry)
    assert isinstance(cloud, PointCloudGeometry)
    assert mesh.bounds.maximum == (10.0, 10.0, 0.0)
    assert len(mesh.triangles) == 1
    assert len(cloud.points) == 2
    assert hashlib.sha256(obj.read_bytes()).hexdigest() == obj_digest


def test_viewport_camera_operations_fit_reset_and_state_restore(tmp_path) -> None:
    points = tmp_path / "points.xyz"
    points.write_text("-10 0 0\n10 0 0\n0 10 0\n", encoding="utf-8")
    service = ViewportService()
    service.load("scan", SceneObjectKind.SCAN_MESH, points)
    service.fit_to_view()
    fitted = service.state.camera
    service.orbit(15, 5)
    service.pan(2, -1)
    service.zoom(0.5)
    changed = service.state.camera
    assert changed != fitted
    state = service.state_dict()
    service.reset_camera()
    service.restore_state(state)
    assert service.state.camera == changed


def test_loader_failures_are_structured_and_real_adapter_renders_offscreen(tmp_path) -> None:
    missing = tmp_path / "missing.obj"
    with pytest.raises(ViewportLoadError) as error:
        load_geometry(missing)
    assert error.value.code is ViewportErrorCode.MISSING
    unsupported = tmp_path / "model.stl"
    unsupported.write_text("solid", encoding="utf-8")
    with pytest.raises(ViewportLoadError) as error:
        load_geometry(unsupported)
    assert error.value.code is ViewportErrorCode.UNSUPPORTED
    empty = tmp_path / "empty.xyz"
    empty.write_text("# no points", encoding="utf-8")
    with pytest.raises(ViewportLoadError) as error:
        load_geometry(empty)
    assert error.value.code is ViewportErrorCode.EMPTY

    service = ViewportService()
    service.add_geometry(
        "reference",
        SceneObjectKind.REFERENCE_GEOMETRY,
        PointCloudGeometry(((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))),
    )
    image = service.render(QSize(320, 240))
    assert image.size() == QSize(320, 240)
    assert not image.isNull()


def test_grid_spacing_is_adaptive_visual_mm_metadata_and_axes_are_stable() -> None:
    near = grid_spec(8.0)
    far = grid_spec(800.0)
    assert near.unit == far.unit == "mm"
    assert near.spacing_mm < far.spacing_mm
    assert {axis["axis"] for axis in axis_metadata()} == {"X", "Y", "Z"}
    assert tuple(axis["direction"] for axis in axis_metadata()) == (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )


def test_grid_and_scale_visibility_round_trip_through_production_state() -> None:
    service = ViewportService()
    service.state = service.state.__class__(
        camera=service.state.camera,
        grid_visible=False,
        axes_visible=False,
        scale_cues_visible=False,
    )
    state = service.state_dict()
    restored = ViewportService()
    restored.restore_state(state)
    assert not restored.state.grid_visible
    assert not restored.state.axes_visible
    assert not restored.state.scale_cues_visible
