"""PL-0485 project parts view on SYNTHETIC tiny clouds (no owner data, no metric claim)."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path

import numpy as np
import pytest

o3d = pytest.importorskip("open3d")

from packlab_core.multiscan_alignment import MultiScanAlignmentError  # noqa: E402
from packlab_studio.app import create_application  # noqa: E402
from packlab_studio.jobs import JobManager, JobState  # noqa: E402
from packlab_studio.measure_view import MeasureDesignView  # noqa: E402
from packlab_studio.model_viewer import ModelViewerView  # noqa: E402
from packlab_studio.navigation import Route  # noqa: E402
from packlab_studio.project import ProjectManager  # noqa: E402
from packlab_studio.project_parts import ScenePanel  # noqa: E402
from packlab_studio.receiver_session import InboxEntry  # noqa: E402
from packlab_studio.shell import StudioMainWindow  # noqa: E402

SCALE = lambda _model: (1.0, "synthetic_known_mm")  # noqa: E731


def _jar(rng: np.random.Generator, flipped: bool) -> np.ndarray:
    """Jar body proxy (r 40, h 80 mm, side boss fixing yaw) on an A4 mat, in mm."""
    d = 0.5  # points per mm^2

    def cyl(r, z0, z1):
        n = int(d * r * 2 * np.pi * (z1 - z0))
        a, z = rng.uniform(0, 2 * np.pi, n), rng.uniform(z0, z1, n)
        return np.c_[r * np.cos(a), r * np.sin(a), z]

    def disc(r, z):
        n = int(d * np.pi * r * r)
        a, s = rng.uniform(0, 2 * np.pi, n), np.sqrt(rng.uniform(0, r * r, n))
        return np.c_[s * np.cos(a), s * np.sin(a), np.full(n, z)]

    def box(x0, x1, y0, y1, z0, z1):  # outside faces of the boss
        n = int(d * 30 * 20)
        faces = [
            np.c_[np.full(n, x1), rng.uniform(y0, y1, n), rng.uniform(z0, z1, n)],
            np.c_[rng.uniform(x0, x1, n // 4), np.full(n // 4, y0), rng.uniform(z0, z1, n // 4)],
            np.c_[rng.uniform(x0, x1, n // 4), np.full(n // 4, y1), rng.uniform(z0, z1, n // 4)],
            np.c_[rng.uniform(x0, x1, n // 4), rng.uniform(y0, y1, n // 4), np.full(n // 4, z0)],
            np.c_[rng.uniform(x0, x1, n // 4), rng.uniform(y0, y1, n // 4), np.full(n // 4, z1)],
        ]
        return np.concatenate(faces)

    parts = [cyl(40, 0, 80), box(38.7, 44, -10, 10, 15, 45), disc(40, 0 if flipped else 80)]
    obj = np.concatenate(parts)
    if flipped:
        obj = obj * [1, -1, -1] + [0, 0, 80]
    yaw = rng.uniform(0, 2 * np.pi)
    c, s = np.cos(yaw), np.sin(yaw)
    obj = obj @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T + [*rng.uniform(-30, 30, 2), 0]
    mat = np.c_[rng.uniform(-148, 148, 18000), rng.uniform(-105, 105, 18000), np.zeros(18000)]
    pts = np.r_[obj, mat]
    return pts + rng.normal(0, 0.15, pts.shape)


def _build(root: Path, name: str, points: np.ndarray, when: float = 0.0) -> str:
    """A fake successful Build-model workspace holding a dense cloud; returns its digest."""
    digest = hashlib.sha256(name.encode()).hexdigest()
    workspace = root / "working" / "reconstruction" / name
    (workspace / "outputs" / "mvs").mkdir(parents=True)
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    o3d.io.write_point_cloud(str(workspace / "outputs/mvs/scene_dense.ply"), cloud)
    manifest = workspace / "manifest.json"
    manifest.write_text(json.dumps({"source_digest": digest, "state": "succeeded"}))
    return digest


def _entry(digest: str, role: str) -> InboxEntry:
    return InboxEntry(digest[:8], digest, "imported", part_role=role, role_declared=True)


def _pump(app, until, timeout=60.0) -> None:
    deadline = time.monotonic() + timeout
    while not until():
        assert time.monotonic() < deadline, "timed out"
        app.processEvents()
        time.sleep(0.01)


@pytest.fixture
def app():
    return create_application(["packlab-project-parts-test"])


@pytest.fixture
def project(tmp_path):
    manager = ProjectManager(job_manager=JobManager())
    manager.new_project(tmp_path / "jar", "Jar")
    return manager


def _panel(project, entries, **kwargs) -> ScenePanel:
    return ScenePanel(project, project.job_manager, lambda: entries, scale_for=SCALE, **kwargs)


def test_missing_and_single_scan_parts(app, project) -> None:
    rng = np.random.default_rng(1)
    up = _build(project.layout.root, "body-up", _jar(rng, False))
    panel = _panel(project, [_entry(up, "body")])
    body = panel.states["body"]
    assert body.status == "single" and "bottom missing" in body.reason
    assert (
        body.cloud
        == project.layout.root / "working/reconstruction/body-up/outputs/mvs/scene_dense.ply"
    )
    assert panel.states["closure"].status == "missing"
    assert "bottom missing" in panel.items["body"].text(1)
    panel.tree.setCurrentItem(panel.items["body"])
    assert project.part_view() == {"part": "body", "hidden": []}
    assert panel.selected_paths() == (body.cloud,)
    assert not panel.combine_button.isEnabled()  # one scan: nothing to combine


def test_combine_part_runs_off_ui_thread_persists_and_reopens(app, project, tmp_path) -> None:
    rng = np.random.default_rng(2)
    root = project.layout.root
    entries = [
        _entry(_build(root, "body-up", _jar(rng, False)), "body"),
        _entry(_build(root, "body-flip", _jar(rng, True)), "body_flipped"),
    ]
    from packlab_core.multiscan_alignment import align_part_pair

    threads = []

    def aligner(*scans):
        threads.append(threading.current_thread())
        return align_part_pair(*scans)

    panel = _panel(project, entries, aligner=aligner)
    assert panel.states["body"].status == "ready"
    panel.tree.setCurrentItem(panel.items["body"])
    assert panel.combine_button.isEnabled()
    outcomes = []
    panel.combine_finished.connect(lambda part, outcome: outcomes.append((part, outcome)))
    job_id = panel.combine("body")
    _pump(app, lambda: outcomes)
    assert outcomes == [("body", "combined")], project.part_merges()
    assert threads and threads[0] is not threading.main_thread()
    assert project.job_manager.get(job_id).state is JobState.SUCCEEDED
    state = panel.states["body"]
    assert state.status == "combined" and state.cloud.parent == root / "derived" / "parts"
    record = project.part_merges()["body"]
    assert record["metric_status"] == "METRIC_UNVERIFIED"
    assert [s["view"] for s in record["sources"]] == ["upright", "flipped"]
    assert record["sources"][1]["package_sha256"] == entries[1].package_sha256
    assert record["file_sha256"] == hashlib.sha256(state.cloud.read_bytes()).hexdigest()
    assert record["alignments"][1]["flipped"] and len(record["alignments"][1]["matrix"]) == 4
    assert "combined" in panel.items["body"].text(1)
    assert panel.selected_paths() == (state.cloud,)

    reopened = ProjectManager(job_manager=JobManager())
    reopened.open_project(root)
    again = _panel(reopened, entries)
    assert again.states["body"].status == "combined" and again.view["part"] == "body"
    # A tampered merged cloud is never shown as combined.
    state.cloud.write_bytes(b"ply\n")
    again.refresh()
    assert (
        again.states["body"].status == "ready" and "changed on disk" in again.states["body"].reason
    )


def test_refused_alignment_is_stored_and_shown(app, project) -> None:
    rng = np.random.default_rng(3)
    root = project.layout.root
    entries = [
        _entry(_build(root, "lid-up", _jar(rng, False)), "closure"),
        _entry(_build(root, "lid-flip", _jar(rng, True)), "closure_flipped"),
    ]

    def refuse(*_scans):
        raise MultiScanAlignmentError("height profile mismatch 4.0 mm > 1.0 mm")

    panel = _panel(project, entries, aligner=refuse)
    outcomes = []
    panel.combine_finished.connect(lambda part, outcome: outcomes.append(outcome))
    panel.combine("closure")
    _pump(app, lambda: outcomes)
    assert outcomes == ["refused"]
    state = panel.states["closure"]
    assert state.status == "refused" and "height profile mismatch" in state.reason
    assert "refused: height profile mismatch" in panel.items["closure"].text(1)
    record = project.part_merges()["closure"]
    assert record["artifact_path"] is None and record["status"] == "refused"
    assert state.cloud is not None  # the upright scan is still shown


def test_cancel_discards_the_result(app, project) -> None:
    rng = np.random.default_rng(4)
    root = project.layout.root
    entries = [
        _entry(_build(root, "a-up", _jar(rng, False)), "assembled"),
        _entry(_build(root, "a-flip", _jar(rng, True)), "assembled_flipped"),
    ]
    entered, release = threading.Event(), threading.Event()

    def slow(*_scans):
        entered.set()
        release.wait(10)
        raise AssertionError("result must be discarded")  # never reaches the project

    panel = _panel(project, entries, aligner=slow)
    panel.tree.setCurrentItem(panel.items["assembled"])
    job_id = panel.combine("assembled")
    _pump(app, entered.is_set)
    assert panel.cancel_button.isEnabled() and "combining" in panel.items["assembled"].text(1)
    panel.cancel("assembled")
    release.set()
    _pump(app, lambda: project.job_manager.get(job_id).state is JobState.CANCELLED)
    assert "assembled" not in project.part_merges()


def test_selection_drives_viewer_and_measure_and_undoes(app, tmp_path) -> None:
    window = StudioMainWindow(
        diagnostics_root=tmp_path / "diagnostics",
        packaging_library_root=tmp_path / "library",
    )
    try:
        manager = window.project_manager
        manager.new_project(tmp_path / "jar", "Jar")
        rng = np.random.default_rng(5)
        root = manager.layout.root
        entries = [
            _entry(_build(root, "body-up", _jar(rng, False)), "body"),
            _entry(_build(root, "lid-up", _jar(rng, False)), "closure"),
            _entry(_build(root, "a-up", _jar(rng, False)), "assembled"),
        ]
        panel = window.scene_panel
        panel.entries_provider = lambda: entries
        panel.refresh()
        viewer = window.route_stack.views[Route.MODEL_VIEWER]
        measure = window.route_stack.views[Route.MEASURE_DESIGN]
        assert isinstance(viewer, ModelViewerView) and isinstance(measure, MeasureDesignView)
        panel.tree.setCurrentItem(panel.items["body"])
        assert "scene_dense.ply" in viewer.status.text()
        assert "Body" in measure.latest_button.text()
        assert measure.use_latest_build()
        assert measure.model.path == panel.states["body"].cloud

        panel.tree.setCurrentItem(panel.items["assembled"])
        assert manager.part_view()["part"] == "assembled", (
            manager.part_view(),
            viewer.status.text(),
        )
        assert len(viewer.service.scene.visible_objects()) == 3  # assembled + body + closure
        child = next(
            panel.items["assembled"].child(i)
            for i in range(panel.items["assembled"].childCount())
            if panel.items["assembled"].child(i).data(0, 0x0100) == "closure"
        )
        from PySide6.QtCore import Qt

        child.setCheckState(0, Qt.CheckState.Unchecked)
        assert manager.part_view() == {"part": "assembled", "hidden": ["closure"]}
        assert len(viewer.service.scene.visible_objects()) == 2

        assert window.undo() is not None  # visibility back
        assert manager.part_view()["hidden"] == []
        assert window.undo() is not None  # selection back to Body
        assert panel.view["part"] == "body"
        assert window.redo() is not None
        assert panel.view["part"] == "assembled"
    finally:
        window.close()


def test_part_strings_have_turkish_entries() -> None:
    import ast

    from packlab_studio import i18n, project_parts

    source = Path(project_parts.__file__).read_text(encoding="utf-8")
    texts = {
        node.args[0].value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == "tr"
        and node.args
        and isinstance(node.args[0], ast.Constant)
    }
    texts |= set(project_parts.STATUS_TEXT.values()) | set(project_parts.PART_LABELS.values())
    texts |= {"Use selected part: {part}"}
    assert texts - set(i18n.TURKISH) == set()
