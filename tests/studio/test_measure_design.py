"""Measure & Design window flow on a synthetic jar + A4 mat scene (no physical claim).

Ground truth here is the synthetic generator itself: 1 reconstruction unit = 100 mm, a 70 mm
jar body, 74 mm lid, 40 mm tall, standing on a nominal PackLab A4 mat seen by 8 pinhole
cameras. Passing proves the wiring and arithmetic, not physical accuracy.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
o3d = pytest.importorskip("open3d")

from PySide6.QtCore import QSettings  # noqa: E402

from packlab_studio import measure_design as md  # noqa: E402
from packlab_studio.app import create_application  # noqa: E402
from packlab_studio.measure_view import BAR_SETTING, MeasureDesignView  # noqa: E402
from packlab_studio.navigation import Route, ScanMasterEditorView  # noqa: E402

UNIT_MM = 100.0
BODY_R, LID_R, LID_FROM, HEIGHT = 0.35, 0.37, 0.33, 0.40
# Marker top-left corners on the A4 mat (mm, SVG coordinates) — see assets/calibration.
MARKERS = {0: (10, 20), 1: (160, 20), 2: (10, 227), 3: (160, 227)}
FX, WIDTH, HEIGHT_PX = 900.0, 1000, 750


def _mat_world(x_mm: float, y_mm: float) -> np.ndarray:
    """Mat centred on the origin in the z = 0 plane, in reconstruction units."""

    return np.array([(x_mm - 105.0) / UNIT_MM, (148.5 - y_mm) / UNIT_MM, 0.0])


def _mat_image(px_per_mm: int = 4) -> np.ndarray:
    image = np.full((297 * px_per_mm, 210 * px_per_mm), 255, np.uint8)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    side = 40 * px_per_mm
    for marker_id, (x, y) in MARKERS.items():
        tag = cv2.aruco.generateImageMarker(dictionary, marker_id, side)
        image[y * px_per_mm : y * px_per_mm + side, x * px_per_mm : x * px_per_mm + side] = tag
    return image


def _look_at(center: np.ndarray, target: np.ndarray) -> np.ndarray:
    z = target - center
    z /= np.linalg.norm(z)
    x = np.cross(z, [0.0, 0.0, 1.0])
    x /= np.linalg.norm(x)
    return np.stack([x, np.cross(z, x), z])


def _quaternion(rotation: np.ndarray) -> tuple[float, float, float, float]:
    vector = cv2.Rodrigues(rotation)[0].reshape(3)
    angle = float(np.linalg.norm(vector))
    axis = vector / angle if angle > 1e-12 else np.zeros(3)
    return (math.cos(angle / 2), *(axis * math.sin(angle / 2)))


def _scene(root: Path) -> Path:
    rng = np.random.default_rng(333)
    images_dir = root / "dense" / "images"
    sparse = root / "dense" / "sparse"
    mvs = root / "mvs"
    for path in (images_dir, sparse, mvs):
        path.mkdir(parents=True)
    mat = _mat_image()
    # mat pixel (u, v) -> world (homogeneous, z = 0 plane coordinates x, y, 1)
    mat_to_plane = np.array(
        [[1 / (4 * UNIT_MM), 0, -1.05], [0, -1 / (4 * UNIT_MM), 1.485], [0, 0, 1]]
    )
    intrinsics = np.array([[FX, 0, WIDTH / 2], [0, FX, HEIGHT_PX / 2], [0, 0, 1]])
    poses = []
    for index in range(8):
        angle = math.tau * index / 8
        center = np.array([2.6 * math.cos(angle), 2.6 * math.sin(angle), 2.4])
        rotation = _look_at(center, np.array([0.0, 0.0, 0.1]))
        translation = -rotation @ center
        plane_to_image = intrinsics @ np.column_stack([rotation[:, 0], rotation[:, 1], translation])
        warped = cv2.warpPerspective(
            mat, plane_to_image @ mat_to_plane, (WIDTH, HEIGHT_PX), borderValue=140
        )
        name = f"view_{index}.jpg"
        cv2.imwrite(str(images_dir / name), warped)
        poses.append((name, rotation, translation))
    with (sparse / "cameras.bin").open("wb") as handle:
        handle.write(struct.pack("<Q", 1))
        handle.write(struct.pack("<iiQQ", 1, 1, WIDTH, HEIGHT_PX))
        handle.write(struct.pack("<4d", FX, FX, WIDTH / 2, HEIGHT_PX / 2))
    with (sparse / "images.bin").open("wb") as handle:
        handle.write(struct.pack("<Q", len(poses)))
        for image_id, (name, rotation, translation) in enumerate(poses, 1):
            handle.write(struct.pack("<I", image_id))
            handle.write(struct.pack("<4d", *_quaternion(rotation)))
            handle.write(struct.pack("<3d", *translation))
            handle.write(struct.pack("<I", 1))
            handle.write(name.encode() + b"\0")
            handle.write(struct.pack("<Q", 0))
    # Dense cloud: table plane + jar wall + lid wall + lid top, 2 mm noise.
    table = np.column_stack([rng.uniform(-2, 2, (20000, 2)), np.zeros(20000)])
    theta = rng.uniform(0, math.tau, 6000)
    z_body = rng.uniform(0, LID_FROM, 6000)
    body = np.column_stack([BODY_R * np.cos(theta), BODY_R * np.sin(theta), z_body])
    theta = rng.uniform(0, math.tau, 1500)
    lid = np.column_stack(
        [LID_R * np.cos(theta), LID_R * np.sin(theta), rng.uniform(LID_FROM, HEIGHT, 1500)]
    )
    radius = LID_R * np.sqrt(rng.uniform(0, 1, 2000))
    theta = rng.uniform(0, math.tau, 2000)
    top = np.column_stack([radius * np.cos(theta), radius * np.sin(theta), np.full(2000, HEIGHT)])
    points = np.vstack([table, body, lid, top]) + rng.normal(0, 0.002, (29500, 3))
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    cloud.colors = o3d.utility.Vector3dVector(rng.uniform(0, 1, (len(points), 3)))
    model_path = mvs / "scene_dense.ply"
    o3d.io.write_point_cloud(str(model_path), cloud)
    # Companion mesh (what OpenMVS ReconstructMesh writes next to the cloud).
    jar = o3d.geometry.TriangleMesh.create_cylinder(BODY_R, LID_FROM, 64, 16)
    jar.translate((0, 0, LID_FROM / 2))
    cap = o3d.geometry.TriangleMesh.create_cylinder(LID_R, HEIGHT - LID_FROM, 64, 4)
    cap.translate((0, 0, (HEIGHT + LID_FROM) / 2 + 0.001))
    floor = o3d.geometry.TriangleMesh.create_box(4, 4, 0.001).translate((-2, -2, -0.001))
    o3d.io.write_triangle_mesh(str(mvs / "scene_dense_mesh.ply"), jar + cap + floor)
    return model_path


@pytest.fixture
def window(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    create_application(["packlab-measure-design"])
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path / "settings")
    )
    from packlab_studio.shell import StudioMainWindow

    studio = StudioMainWindow(
        diagnostics_root=tmp_path / "diagnostics", packaging_library_root=tmp_path / "library"
    )
    yield studio
    studio.close()


def test_measure_design_buttons_drive_the_full_flow(window, tmp_path) -> None:
    model_path = _scene(tmp_path / "scene")
    window.new_project(tmp_path / "project", "Synthetic jar")
    view = window.route_stack.views[Route.MEASURE_DESIGN]
    assert isinstance(view, MeasureDesignView)
    view._choose_file = lambda _parent: str(model_path)
    view.open_button.click()
    assert "8 COLMAP cameras" in view.results.text(), view.status.text()

    view.isolate_button.click()
    assert view.isolation is not None, view.status.text()
    kept = view.model.points[view.isolation.object_indices]
    assert len(kept) > 8000 and np.abs(kept[:, :2]).max() < 0.45  # table removed
    assert not view.viewer.canvas.pixmap().isNull()

    view.bar_mm.setValue(100.0)
    view.marker_button.click()
    assert view.scale is not None, view.status.text()
    assert view.scale.source == "mat_markers"
    assert view.scale.mm_per_unit == pytest.approx(UNIT_MM, rel=0.02)
    assert view.scale.provenance.scale_state.value == "metric-unverified"

    view.measure_button.click()
    result = view.measurements
    assert result is not None, view.status.text()
    assert result.get("height").value_mm == pytest.approx(40.0, abs=2.0)
    assert result.get("max_body_diameter").value_mm == pytest.approx(70.0, abs=2.0)
    assert result.get("lid_diameter").value_mm == pytest.approx(74.0, abs=2.5)
    assert result.get("height").report.propagated_standard_uncertainty > 0
    assert "mm_unverified" in view.results.text()

    view._choose_save = lambda _parent, name: str(tmp_path / "report.json")
    view.report_button.click()
    assert (tmp_path / "report.json").is_file() and (tmp_path / "report.md").is_file()

    view.promote_button.click()
    assert view.scan_master is not None, view.status.text()
    assert window.project_manager.selected_scan_master_revision().revision_id == (
        view.scan_master.revision_id
    )

    view.fit_button.click()  # straight jar: core zone rules need owner review
    assert view.design is None and "owner review" in view.status.text()
    view.owner_review.setChecked(True)
    view.fit_button.click()
    assert view.design is not None, view.status.text()
    first_revision = view.design.model.revision_id
    view.height_mm.setValue(view.design.height + 5.0)
    view.apply_button.click()
    assert view.design.model.revision_id != first_revision
    preview = np.asarray(view.design.preview_mesh().vertices)
    assert np.ptp(preview[:, 2]) == pytest.approx(view.design.height, rel=1e-6)
    view.save_button.click()
    assert view.saved_design_path is not None and view.saved_design_path.is_file()
    assert "derived" in view.saved_design_path.parts


def test_manual_reference_scale_and_editor_promotion(window, tmp_path) -> None:
    model_path = _scene(tmp_path / "scene")
    window.new_project(tmp_path / "project", "Synthetic jar")
    view = window.route_stack.views[Route.MEASURE_DESIGN]
    assert view.load(model_path)
    view.isolate_button.click()
    # Prefilled axis base/top points; owner enters the jar's caliper height.
    view.known_mm.setValue(40.0)
    view.manual_button.click()
    assert view.scale is not None and view.scale.source == "manual_reference"
    assert view.scale.mm_per_unit == pytest.approx(UNIT_MM, rel=0.05)

    editor = window.route_stack.views[Route.EDITOR]
    assert isinstance(editor, ScanMasterEditorView)
    editor.actor_input.setText("owner")
    editor.reason_input.setText("Cleaned object selection from Measure & Design.")
    editor.promote_button.click()
    assert editor.status.text().startswith("Selected Scan Master scan-master:"), (
        editor.status.text()
    )


def test_print_correction_persists_and_scales_marker_side(window) -> None:
    view = window.route_stack.views[Route.MEASURE_DESIGN]
    view.bar_mm.setValue(98.0)
    assert float(QSettings().value(BAR_SETTING)) == 98.0
    reference = md.mat_reference(0.98, "synthetic_test_fixture")[0]
    assert reference.side_length == pytest.approx(39.2)


def test_marker_scale_without_markers_points_to_manual(tmp_path) -> None:
    model_path = _scene(tmp_path / "scene")
    model = md.load_model(model_path)
    images, sparse = md.find_colmap_workspace(model_path)
    for image in images.iterdir():
        cv2.imwrite(str(image), np.full((HEIGHT_PX, WIDTH), 200, np.uint8))
    cameras = md.read_colmap_cameras(sparse)
    isolation = md.isolate_object(model, cameras)
    with pytest.raises(md.MeasureDesignError, match="manual reference"):
        md.estimate_marker_scale(model, isolation, cameras, images, "camera-test")
