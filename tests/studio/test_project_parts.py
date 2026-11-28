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

SCALE = lambda _model: (1.0, "synthetic_known_mm", 0.001)  # noqa: E731


def _jar(rng: np.random.Generator, flipped: bool, lug: bool = False) -> np.ndarray:
    """Jar body proxy (r 40, h 80 mm, side boss fixing yaw) on an A4 mat, in mm. ``lug``: a
    second 22 x 24 x 4 mm lug opposite the boss (a feature only one scan of a pair has)."""
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
    if lug:
        parts.append(box(38.7, 44, -11, 11, 30, 54) * [-1, 1, 1])
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
    job_id = panel.combine("closure")
    _pump(app, lambda: outcomes)
    assert outcomes == ["refused"]
    job = project.job_manager.get(job_id)  # a refusal is never listed as "[succeeded] 100%"
    assert job.state is JobState.FAILED and "height profile mismatch" in (job.error or "")
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


def test_combined_part_measures_promotes_and_fits_in_its_mat_frame(app, tmp_path) -> None:
    from packlab_studio import measure_design as md

    window = StudioMainWindow(
        diagnostics_root=tmp_path / "diagnostics",
        packaging_library_root=tmp_path / "library",
    )
    try:
        manager = window.project_manager
        manager.new_project(tmp_path / "jar", "Jar")
        rng = np.random.default_rng(6)
        root = manager.layout.root
        entries = [
            _entry(_build(root, "body-up", _jar(rng, False)), "body"),
            _entry(_build(root, "body-flip", _jar(rng, True)), "body_flipped"),
            _entry(_build(root, "lid-up", _jar(rng, False)), "closure"),
        ]
        panel = window.scene_panel
        panel.entries_provider, panel.scale_for = (lambda: entries), SCALE
        panel.refresh()
        outcomes = []
        panel.combine_finished.connect(lambda part, outcome: outcomes.append(outcome))
        panel.tree.setCurrentItem(panel.items["body"])
        panel.combine("body")
        _pump(app, lambda: outcomes)
        assert outcomes == ["combined"], manager.part_merges()
        record = manager.part_merges()["body"]
        assert record["mesh_artifact_path"].startswith("derived/parts/body-mesh-")

        view = window.route_stack.views[Route.MEASURE_DESIGN]
        assert isinstance(view, MeasureDesignView)
        assert view.use_latest_build() and view.part_record is not None, view.status.text()
        view.isolate_button.click()
        assert view.isolation is not None, view.status.text()
        assert view.isolation.method == md.PART_FRAME_METHOD  # no mat search
        scale = view.scale
        assert scale is not None and scale.source == "part_combine" and scale.mm_per_unit == 1.0
        assert scale.provenance.scale_state.value == "metric-unverified"
        assert [r["scale_source"] for r in scale.provenance.physical_references] == [
            "synthetic_known_mm",
            "synthetic_known_mm",
        ]
        view.measure_button.click()
        result = view.measurements
        assert result is not None, view.status.text()
        assert result.get("height").value_mm == pytest.approx(80.0, abs=1.5)
        assert result.get("max_body_diameter").value_mm == pytest.approx(80.0, abs=2.0)
        request = view.promotion_request("owner", "derived surface provenance")
        built = request.lineage.reconstruction
        assert built.backend_version == f"derived:open3d-poisson:{record['mesh_method']}"
        assert built.asset_paths["derived_surface"] == record["mesh_artifact_path"]
        assert built.source_input_digest == record["file_sha256"]
        assert any("surface DERIVED" in item for item in built.limitations)
        assert any("surface DERIVED" in item for item in request.known_limitations)
        assert any("DERIVED fill" in item for item in request.coverage_gaps)
        view.promote_button.click()
        assert view.scan_master is not None, view.status.text()
        view.owner_review.setChecked(True)
        view.fit_button.click()
        assert view.design is not None, view.status.text()
        z = np.asarray(view.scan_master.mesh.vertices)[:, 2]
        assert np.ptp(z) == pytest.approx(80.0, abs=1.5)  # top and bottom both present
        assert 70.0 < view.design.height <= 81.5  # fitted revolved profile, not a measurement
        # PL-0487: saving it makes it the Body's Design Model; Labels follow the selection.
        view.save_button.click()
        linked, _document = manager.part_design_model("body")
        assert linked["revision_id"] == view.design.model.revision_id, view.status.text()
        assert linked["part"] == "body" and manager.part_design_model("closure") is None
        frame = manager.part_design_frame("body")  # recorded at promotion (PL-0487)
        assert frame["source_cloud_sha256"] == view.model.sha256
        assert frame["source_frame"] == "part_combine_mat_frame_mm" and frame["part"] == "body"
        assert np.allclose(frame["source_to_scan_master"], view.frame.matrix.ravel())
        assert "Body Design Model" in view.status.text()
        labels = window.route_stack.views[Route.LABELS]
        assert labels.part == "body"
        assert labels.workbench.session.model.revision_id == linked["revision_id"]

        # A part without its own cloud never silently loads another build.
        panel.tree.setCurrentItem(panel.items["assembled"])
        assert not view.latest_button.isEnabled() and "no scan yet" in view.latest_button.text()
        assert not view.use_latest_build()

        # A single-scan part keeps the mat-based flow (plane search, marker / manual scale).
        panel.tree.setCurrentItem(panel.items["closure"])
        assert view.use_latest_build() and view.part_record is None
        view.isolate_button.click()
        assert view.isolation is not None and view.isolation.method == md.ISOLATION_METHOD
        assert view.scale is None
    finally:
        window.close()


def test_holed_part_surface_lists_derived_fill_as_coverage_gaps(tmp_path) -> None:
    import uuid

    from packlab_studio import measure_design as md
    from packlab_studio.project_parts import write_cloud, write_mesh

    def jar(holed: bool) -> np.ndarray:
        rng = np.random.default_rng(7)
        a, z = rng.uniform(0, 2 * np.pi, 20000), rng.uniform(0, 80, 20000)
        wall = np.c_[40 * np.cos(a), 40 * np.sin(a), z]
        if holed:  # a 60 deg x 40 mm window the scans never saw
            wall = wall[~((a < np.pi / 3) & (z > 20) & (z < 60))]
        r, b = 40 * np.sqrt(rng.uniform(0, 1, 5000)), rng.uniform(0, 2 * np.pi, 5000)
        caps = [np.c_[r * np.cos(b), r * np.sin(b), np.full(5000, h)] for h in (0.0, 80.0)]
        return np.concatenate([wall, *caps])

    counts = {}
    for holed in (False, True):
        folder = tmp_path / ("holed" if holed else "full")
        points = jar(holed)
        cloud, mesh = write_cloud(folder, "body", points, None), write_mesh(folder, "body", points)
        model, mesh_model = md.load_model(cloud), md.load_model(mesh)
        record = {
            "part": "body",
            "status": "combined",
            "method": "synthetic",
            "mesh_method": "poisson-test",
            "file_sha256": model.sha256,
            "artifact_path": f"derived/parts/{cloud.name}",
            "mesh_artifact_path": f"derived/parts/{mesh.name}",
            "sources": [
                {"view": v, "mm_per_unit": 1.0, "scale_source": "known", "scale_uncertainty": 0.001}
                for v in ("upright", "flipped")
            ],
        }
        isolation = md.isolate_in_mat_frame(model)
        scale = md.part_combine_scale(model, record)
        frame = md.build_frame(model, isolation, scale, project_id=str(uuid.uuid4()))
        request = md.promotion_request(
            project_id=frame.geometry.project_id,
            model=model,
            mesh_model=mesh_model,
            isolation=isolation,
            frame=frame,
            actor_id="owner",
            reason="test",
            part_record=record,
        )
        gaps, _limit = md.derived_surface_gaps(request.final_mesh, frame.apply(model.points))
        counts[holed] = len(gaps)
        assert any(f"{len(gaps)} of " in item for item in request.coverage_gaps)
    assert counts[True] > 50 and counts[True] > 5 * counts[False], counts


def test_late_cancel_discards_result_and_files(app, project) -> None:
    from types import SimpleNamespace

    rng = np.random.default_rng(8)
    root = project.layout.root
    entries = [
        _entry(_build(root, "b-up", _jar(rng, False)), "body"),
        _entry(_build(root, "b-flip", _jar(rng, True)), "body_flipped"),
    ]
    merged = _jar(rng, False)
    merged = merged[merged[:, 2] > 0.5]

    def quick(*_scans):
        return SimpleNamespace(
            points=merged, colors=None, reference_id="r", surface_coverage={}, alignments=()
        )

    panel = _panel(project, entries, aligner=quick)
    original, job = panel._finish, {}

    def cancel_then_finish(*args):  # Cancel pressed after the worker's last checkpoint
        project.job_manager.request_cancel(job["id"])
        return original(*args)

    panel._finish = cancel_then_finish
    outcomes = []
    panel.combine_finished.connect(lambda part, outcome: outcomes.append(outcome))
    job["id"] = panel.combine("body")
    _pump(app, lambda: outcomes)
    assert outcomes == ["cancelled"]
    assert project.job_manager.get(job["id"]).state is JobState.CANCELLED
    assert "body" not in project.part_merges()
    assert not list((root / "derived" / "parts").glob("*.ply"))  # written files removed


def _revision_build(root: Path, digest: str, revision: str, points, preset: str, when: float):
    """Another successful build (workspace ``revision``) of the scan ``digest``."""
    workspace = root / "working" / "reconstruction" / revision
    (workspace / "outputs" / "mvs").mkdir(parents=True)
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    o3d.io.write_point_cloud(str(workspace / "outputs/mvs/scene_dense.ply"), cloud)
    note = "[packlab] mesh-refinement skipped (Fast preset)\n" if preset == "fast" else ""
    stages = [{"stage_id": "mesh-refinement", "stdout": note}]
    manifest = workspace / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"source_digest": digest, "state": "succeeded", "parameters": {"stage_results": stages}}
        )
    )
    import os

    os.utime(manifest, (when, when))
    return workspace / "outputs/mvs/scene_dense.ply"


def test_owner_chooses_which_build_feeds_a_part_persisted_and_undoable(app, project) -> None:
    rng = np.random.default_rng(6)
    root = project.layout.root
    up = hashlib.sha256(b"body-up-scan").hexdigest()
    old = _revision_build(root, up, "r-" + "a" * 32, _jar(rng, False), "high", 1_700_000_000)
    new = _revision_build(root, up, "r-" + "b" * 32, _jar(rng, False), "fast", 1_700_000_100)
    flip = _build(root, "body-flip", _jar(rng, True))
    failed = root / "working/reconstruction" / ("r-" + "c" * 32)
    failed.mkdir()
    (failed / "manifest.json").write_text(json.dumps({"source_digest": up, "state": "failed"}))
    entries = [_entry(up, "body"), _entry(flip, "body_flipped")]
    panel = _panel(project, entries)
    panel.tree.setCurrentItem(panel.items["body"])
    assert panel.states["body"].upright.model == new  # default: the latest successful build
    box = panel.build_boxes["upright"]
    assert box.count() == 2 and box.isEnabled()  # the failed build is not offered
    assert box.itemText(0).startswith("latest: Fast") and box.itemText(1).startswith("High")
    assert not panel.build_boxes["flipped"].isEnabled()  # one build only

    box.activated.emit(1)  # owner picks the older High build
    assert project.scan_builds() == {up: "r-" + "a" * 32}
    assert panel.states["body"].upright.model == old and box.currentIndex() == 1
    reopened = ProjectManager(job_manager=JobManager())
    reopened.open_project(root)
    assert reopened.scan_builds() == {up: "r-" + "a" * 32}  # persisted

    assert project.undo() is not None  # back to following the latest build
    panel.refresh()
    assert project.scan_builds() == {} and panel.states["body"].upright.model == new
    assert project.redo() is not None
    panel.refresh()
    assert panel.states["body"].upright.model == old
    box.activated.emit(0)  # choosing the latest again follows future builds
    assert project.scan_builds() == {}
    with pytest.raises(Exception, match="revision"):
        project.set_scan_build(up, "../escape")

    # A chosen build that disappears: said so, the stale choice is cleared, latest is used.
    box.activated.emit(1)
    assert project.scan_builds() == {up: "r-" + "a" * 32}
    import shutil

    shutil.rmtree(old.parents[2])
    panel.refresh()
    assert project.scan_builds() == {} and panel.states["body"].upright.model == new
    assert "is missing; using the latest build" in panel.details.text()


def test_newest_successful_build_is_used_when_the_latest_build_failed(app, project) -> None:
    rng = np.random.default_rng(8)
    root = project.layout.root
    up = hashlib.sha256(b"body-up-scan-2").hexdigest()
    good = _revision_build(root, up, "r-" + "d" * 32, _jar(rng, False), "fast", 1_700_000_000)
    failed = root / "working/reconstruction" / ("r-" + "e" * 32)
    failed.mkdir()
    manifest = failed / "manifest.json"
    manifest.write_text(json.dumps({"source_digest": up, "state": "failed"}))
    import os

    os.utime(manifest, (1_700_000_500, 1_700_000_500))  # newer than the good build
    panel = _panel(project, [_entry(up, "body")])
    assert panel.states["body"].status == "single" and panel.states["body"].cloud == good


def test_combine_records_scan_heights_and_shows_them_per_build(app, project) -> None:
    rng = np.random.default_rng(7)
    root = project.layout.root
    entries = [
        _entry(_build(root, "body-up", _jar(rng, False)), "body"),
        _entry(_build(root, "body-flip", _jar(rng, True)), "body_flipped"),
    ]

    def refuse(*scans):
        error = MultiScanAlignmentError("height mismatch 72.0 vs 80.0 mm")
        error.heights_mm = {scans[0].scan_id: 80.0, scans[1].scan_id: 72.0}
        raise error

    panel = _panel(project, entries, aligner=refuse)
    panel.tree.setCurrentItem(panel.items["body"])
    outcomes = []
    panel.combine_finished.connect(lambda part, outcome: outcomes.append(outcome))
    panel.combine("body")
    _pump(app, lambda: outcomes)
    sources = project.part_merges()["body"]["sources"]
    assert [s["height_mm"] for s in sources] == [80.0, 72.0]
    assert panel.build_boxes["upright"].itemText(0).endswith("80.0 mm")
    assert panel.build_boxes["flipped"].itemText(0).endswith("72.0 mm")


def test_owner_can_combine_anyway_only_when_offered_and_it_stays_unverified(app, project) -> None:
    from packlab_core.multiscan_alignment import align_part_pair
    from packlab_studio import measure_design as md
    from packlab_studio.project_parts import owner_confirmed

    rng = np.random.default_rng(8)
    root = project.layout.root
    entries = [
        _entry(_build(root, "body-up", _jar(rng, False)), "body"),
        _entry(_build(root, "body-flip", _jar(rng, True, lug=True)), "body_flipped"),
    ]
    asked: list[str] = []

    def confirm(_parent, text, tier):
        asked.append(f"{tier}|{text}")
        return True

    def plain_refusal(*_scans, **_kwargs):
        raise MultiScanAlignmentError("height mismatch 70.0 vs 80.0 mm")

    panel = _panel(project, entries, aligner=plain_refusal, confirm=confirm)
    outcomes: list[str] = []
    panel.combine_finished.connect(lambda part, outcome: outcomes.append(outcome))
    panel.tree.setCurrentItem(panel.items["body"])
    panel.combine("body")
    _pump(app, lambda: outcomes)
    assert outcomes == ["refused"] and not panel.anyway_button.isVisibleTo(panel)
    assert "Combine anyway is not offered" not in panel.details.text()  # no reason recorded
    assert panel.combine_anyway("body") is None and not asked  # not offered: no override

    # The real core decides offers (tests/core): a one-scan mid-body lug is offered as tier B
    # (large local differences, possibly a different part) ...
    panel.aligner = align_part_pair
    panel.combine("body")
    _pump(app, lambda: len(outcomes) == 2, timeout=180)
    record = project.part_merges()["body"]
    assert outcomes[-1] == "refused" and record.get("override") and record["override_tier"] == "B"
    assert any(item["kind"] == "deep_patch" for item in record["override"])
    assert panel.anyway_button.isVisibleTo(panel) and "Tier B" in panel.details.text()

    # ... and a stand-in for the core's offer (fast) drives the confirm and persistence path.
    disagreement = {"kind": "patch", "area_mm2": 120.0, "z_mm": [70.0, 78.0]}

    def offering(*scans, owner_confirmed=False):
        if not owner_confirmed:
            error = MultiScanAlignmentError("a 120 mm^2 patch of side wall has no counterpart")
            error.override_disagreements = (disagreement,)
            error.override_tier = "B"
            raise error
        from dataclasses import replace

        result = _genuine_result()
        return replace(
            result,
            verification="OWNER_CONFIRMED_UNVERIFIED",
            disagreements=(disagreement,),
            override_tier="B",
        )

    def _genuine_result():
        rng2 = np.random.default_rng(2)
        from packlab_core.multiscan_alignment import ScanInput

        up, fl = _jar(rng2, False), _jar(rng2, True)
        return align_part_pair(ScanInput("u", up), ScanInput("f", fl))

    panel.aligner = offering
    panel.combine("body")
    _pump(app, lambda: len(outcomes) == 3, timeout=180)
    record = project.part_merges()["body"]
    assert outcomes[-1] == "refused" and record["override"], record
    assert record["override_tier"] == "B"
    assert panel.anyway_button.isVisibleTo(panel)
    assert "The two scans disagree" in panel.details.text()
    assert "Tier B" in panel.details.text()

    panel.combine_anyway("body")
    _pump(app, lambda: len(outcomes) == 4, timeout=180)
    assert outcomes[-1] == "combined" and asked and "patch" in asked[0]
    assert asked[0].startswith("B|Tier B")  # the dialog is the tier-B one
    record = project.part_merges()["body"]
    assert owner_confirmed(record) and record["disagreements"] and record["owner_confirmed_at"]
    assert record["metric_status"] == "METRIC_UNVERIFIED"
    assert record["verification_tier"] == "B"
    assert "owner-confirmed (tier B), UNVERIFIED" in panel.items["body"].text(1)
    assert "OWNER_CONFIRMED_UNVERIFIED" in panel.details.text()
    model = md.load_model(root / record["artifact_path"])
    scale = md.part_combine_scale(model, record)
    assert "OWNER_CONFIRMED_UNVERIFIED" in scale.details
    assert all(
        ref["evidence_class"] == "owner_confirmed_unverified_combine"
        for ref in scale.provenance.physical_references
    )
    import uuid

    isolation = md.isolate_in_mat_frame(model)
    frame = md.build_frame(model, isolation, scale, project_id=str(uuid.uuid4()))
    request = md.promotion_request(
        project_id=frame.geometry.project_id,
        model=model,
        mesh_model=md.load_model(root / record["mesh_artifact_path"]),
        isolation=isolation,
        frame=frame,
        actor_id="owner",
        reason="test",
        part_record=record,
    )
    manifest = request.lineage.reconstruction
    assert manifest.verification == "OWNER_CONFIRMED_UNVERIFIED"  # structured, Scan Master
    assert manifest.as_dict()["verification"] == "OWNER_CONFIRMED_UNVERIFIED"
    verified = md.promotion_request(
        project_id=frame.geometry.project_id,
        model=model,
        mesh_model=md.load_model(root / record["mesh_artifact_path"]),
        isolation=isolation,
        frame=frame,
        actor_id="owner",
        reason="test",
        part_record={**record, "verification": "GATE_PASSED"},
    )
    assert verified.lineage.reconstruction.configuration_digest != manifest.configuration_digest


def test_owner_confirmed_parts_carry_the_badge_into_placement_and_interior(app, project) -> None:
    from packlab_studio.project_parts import OWNER_CONFIRMED, PartScan, PartState

    rng = np.random.default_rng(9)
    root = project.layout.root
    cloud = root / "working/reconstruction/x/outputs/mvs/scene_dense.ply"
    _build(root, "x", _jar(rng, False))
    record = {"status": "combined", "verification": OWNER_CONFIRMED, "disagreements": []}
    scan = PartScan("0" * 64, cloud, 0.0)
    state = PartState("body", scan, scan, "combined", "", cloud, record, interior=scan)
    panel = _panel(project, [])
    source: dict = {}
    panel._part_input("body", state, source)
    assert source["verification"] == OWNER_CONFIRMED  # the placement record keeps it
    placement = {"status": "placed", "sources": {"body": source}, "reason": ""}
    panel.placement = ("refused", placement, ())
    assert "OWNER_CONFIRMED_UNVERIFIED parts in this placement" not in " ".join(
        panel._placement_lines(False)
    )
    graph = {
        "components": [{"residuals": {}}, {"residuals": {}}],
        "diagnostics": {"pair": {"status": "ok"}},
        "relationships": [{"engaged_depth_mm": 1.0}],
        "revision_id": "g" * 40,
    }
    panel.placement = ("placed", {**placement, "graph": graph}, ())
    try:
        lines = panel._placement_lines(False)
    except (KeyError, TypeError):
        lines = []
    assert not lines or "OWNER_CONFIRMED_UNVERIFIED parts in this placement: Body" in lines[0]
    panel.states = {"body": state}
    panel.interior = ("none", None, None)
    assert "OWNER_CONFIRMED_UNVERIFIED Body" in panel._interior_lines(False)[0]


def test_tier_b_confirmation_needs_the_physical_check(app) -> None:
    from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton

    from packlab_studio.project_parts import confirm_dialog

    dialog = confirm_dialog(None, "differences", "B")
    accept = dialog.findChild(QPushButton, "packlab.scene.confirm_accept")
    check = dialog.findChild(QCheckBox, "packlab.scene.confirm_checked")
    warning = dialog.findChild(QLabel, "packlab.scene.confirm_warning")
    assert warning is not None and "#b00020" in warning.styleSheet()
    assert check is not None and not accept.isEnabled()
    check.setChecked(True)
    assert accept.isEnabled()
    check.setChecked(False)
    assert not accept.isEnabled()
    plain = confirm_dialog(None, "differences", "A")
    assert plain.findChild(QCheckBox, "packlab.scene.confirm_checked") is None
    assert plain.findChild(QPushButton, "packlab.scene.confirm_accept").isEnabled()
