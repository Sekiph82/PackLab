from __future__ import annotations

import hashlib
import json

import pytest
from PySide6.QtCore import QSize

from packlab_studio.viewport import (
    MeshGeometry,
    PointCloudGeometry,
    SceneObject,
    SceneObjectId,
    SceneObjectKind,
    ViewportErrorCode,
    ViewportLoadError,
    ViewportRenderMode,
    ViewportService,
    axis_metadata,
    grid_spec,
    load_geometry,
)
from packlab_studio.viewport_export import ViewportExportError, ViewportPreviewExporter


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


def test_scene_model_has_stable_objects_selection_and_visibility_rules() -> None:
    service = ViewportService()
    service.add_geometry(
        SceneObjectId.SCAN_MESH.value,
        SceneObjectKind.SCAN_MESH,
        PointCloudGeometry(((0.0, 0.0, 0.0),)),
    )
    with pytest.raises(ValueError, match="duplicate"):
        service.scene.add(SceneObject(SceneObjectId.SCAN_MESH.value, SceneObjectKind.SCAN_MESH))
    assert service.select(SceneObjectId.SCAN_MESH.value)
    service.set_visible(SceneObjectId.SCAN_MESH.value, False)
    assert service.state.selected_object_id is None
    assert not service.select("missing")
    snapshot = service.scene_snapshot()
    assert snapshot["objects"][0]["object_id"] == SceneObjectId.SCAN_MESH.value
    assert snapshot["objects"][0]["visible"] is False


def test_scene_visibility_and_selection_restore_is_deterministic() -> None:
    service = ViewportService()
    service.add_geometry("cap", SceneObjectKind.CAP, PointCloudGeometry(((1.0, 1.0, 1.0),)))
    service.select("cap")
    state = service.state_dict()
    service.clear_selection()
    service.restore_state(state)
    assert service.state.selected_object_id == "cap"
    assert service.scene_snapshot()["selected_object_id"] == "cap"


def test_debug_modes_are_state_only_and_missing_normals_are_truthful(tmp_path) -> None:
    obj = tmp_path / "triangle.obj"
    obj.write_text("v 0 0 0\nv 10 0 0\nv 0 10 0\nf 1 2 3\n", encoding="utf-8")
    before = hashlib.sha256(obj.read_bytes()).hexdigest()
    service = ViewportService()
    service.load("mesh", SceneObjectKind.SCAN_MESH, obj)
    assert service.normals_status("mesh") == "temporary-derived"
    for mode in (ViewportRenderMode.WIREFRAME, ViewportRenderMode.NORMALS, ViewportRenderMode.POINT_CLOUD, ViewportRenderMode.SOLID):
        service.set_render_mode(mode)
        assert service.state.render_mode is mode
        assert not service.render(QSize(240, 180)).isNull()
    assert hashlib.sha256(obj.read_bytes()).hexdigest() == before


def test_viewport_preview_export_is_nonempty_atomic_and_redacted(tmp_path) -> None:
    service = ViewportService()
    service.add_geometry("scan-mesh", SceneObjectKind.SCAN_MESH, PointCloudGeometry(((0.0, 0.0, 0.0),)))
    destination = tmp_path / "export" / "preview.png"
    result = ViewportPreviewExporter().export(
        service, destination, project_id="project-id", revision=3, project_root=tmp_path / "project", size=QSize(160, 120)
    )
    assert result.image_path.stat().st_size > 0
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["visible_object_ids"] == ["scan-mesh"]
    assert metadata["width"] == 160
    assert metadata["paths_redacted"] is True
    assert str(tmp_path) not in result.metadata_path.read_text(encoding="utf-8")
    with pytest.raises(ViewportExportError, match="exists"):
        ViewportPreviewExporter().export(service, destination, project_id="project-id", revision=3)


def test_preview_export_rejects_raw_and_unavailable_backend(tmp_path) -> None:
    service = ViewportService()
    service.add_geometry("reference", SceneObjectKind.REFERENCE_GEOMETRY, PointCloudGeometry(((0.0, 0.0, 0.0),)))
    root = tmp_path / "project"
    (root / "raw").mkdir(parents=True)
    with pytest.raises(ViewportExportError, match="raw"):
        ViewportPreviewExporter().export(service, root / "raw" / "evidence.png", project_root=root)

    class BrokenAdapter:
        backend_name = "broken"
        backend_version = "test"

        def render(self, *_args):
            raise RuntimeError("not available")

        def capabilities(self):
            return {"headless": False}

    broken = ViewportService(adapter=BrokenAdapter())  # type: ignore[arg-type]
    with pytest.raises(ViewportExportError, match="unavailable"):
        ViewportPreviewExporter().export(broken, tmp_path / "broken.png")
