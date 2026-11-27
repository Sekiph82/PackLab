"""PL-0443/PL-0453: Build model from an imported scan, offscreen, with fake engines."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from tests.transfer.test_loopback_receiver import _package

from packlab_core.packscan import write_packscan
from packlab_core.reconstruction import (
    BackendProvenance,
    ReconstructionBackendId,
    ReconstructionStageResult,
    StageStatus,
)
from packlab_core.reconstruction_orchestrator import (
    STAGE_ORDER,
    ReconstructionStageContext,
    ReconstructionStageDefinition,
    ReconstructionStageExecution,
)
from packlab_studio import build_model
from packlab_studio.app import create_application
from packlab_studio.build_model import (
    BuildModelError,
    BuildModelView,
    ColmapOpenMvsBackend,
    _definitions,
)
from packlab_studio.capture_inbox import CaptureInboxView
from packlab_studio.engine_config import (
    DiscoveryStatus,
    EngineDiscoveryReport,
    EnginePathDiagnostic,
)
from packlab_studio.jobs import JobState
from packlab_studio.model_viewer import ModelViewerView
from packlab_studio.navigation import Route, SettingsView
from packlab_studio.receiver_session import ReceiverSession
from packlab_studio.shell import StudioMainWindow

PLY = (
    "ply\nformat ascii 1.0\nelement vertex 4\n"
    "property float x\nproperty float y\nproperty float z\nend_header\n"
    "0 0 0\n1 0 0\n0 1 0\n0 0 1\n"
)


class FakeBackend:
    """Stands in for COLMAP/OpenMVS: writes tiny outputs, can fail or wait for cancel."""

    def __init__(
        self,
        *,
        fail_at: str | None = None,
        block_at: str | None = None,
        provenance_gate: threading.Event | None = None,
    ) -> None:
        self.fail_at = fail_at
        self.block_at = block_at
        self.provenance_gate = provenance_gate

    def provenance(self, workspace_dir: Path) -> BackendProvenance:
        if self.provenance_gate is not None:
            self.provenance_gate.wait(20)
        return BackendProvenance(
            ReconstructionBackendId.COLMAP_OPENMVS, "fake 1", "test", "test-only"
        )

    def stages(
        self, workspace_dir: Path, workspace_asset: str, facts: dict[str, object]
    ) -> tuple[ReconstructionStageDefinition, ...]:
        def make(
            stage_id: str,
        ) -> Callable[[ReconstructionStageContext], ReconstructionStageExecution]:
            def execute(context: ReconstructionStageContext) -> ReconstructionStageExecution:
                if stage_id == self.block_at:
                    context.cancel.event.wait(20)
                    result = ReconstructionStageResult(
                        stage_id,
                        StageStatus.CANCELLED,
                        None,
                        0.1,
                        cancelled=True,
                        failure_reason="stage cancelled",
                    )
                    return ReconstructionStageExecution(stage_id, result)
                if stage_id == self.fail_at:
                    result = ReconstructionStageResult(
                        stage_id, StageStatus.FAILED, 1, 0.1, failure_reason="fake engine exited 1"
                    )
                    return ReconstructionStageExecution(stage_id, result)
                name = "scene_dense.ply" if stage_id == "dense-point-cloud" else f"{stage_id}.txt"
                (workspace_dir / "outputs" / name).write_text(PLY, encoding="ascii")
                facts["registered_images"] = 1
                facts["input_images"] = len(context.job.inputs.image_asset_ids)
                key = "point_cloud" if stage_id == "dense-point-cloud" else "primary"
                return ReconstructionStageExecution(
                    stage_id,
                    ReconstructionStageResult(stage_id, StageStatus.SUCCEEDED, 0, 0.01),
                    {key: f"{workspace_asset}/outputs/{name}"},
                    outputs_verified=True,
                )

            return execute

        return _definitions([make(stage_id) for stage_id in STAGE_ORDER], {"preset": "fake"})


def _window(monkeypatch, tmp_path: Path, backend: object, **kwargs: object):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-build-model-test"])
    window = StudioMainWindow(
        receiver_session_factory=lambda: ReceiverSession(
            tmp_path / "inbox",
            tls_root=tmp_path / "tls",
            port=0,
            bind_host="127.0.0.1",
            lan_host_provider=lambda: "127.0.0.1",
        ),
        diagnostics_root=tmp_path / "diagnostics",
        packaging_library_root=tmp_path / "library",
        default_project_root=tmp_path / "projects" / "default",
        build_backend=backend,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )
    inbox = window.route_stack.views[Route.CAPTURE_INBOX]
    builds = window.route_stack.views[Route.RECONSTRUCTION]
    assert isinstance(inbox, CaptureInboxView) and isinstance(builds, BuildModelView)
    return app, window, inbox, builds


def _pump(app, until: Callable[[], bool], timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while not until():
        assert time.monotonic() < deadline, "timed out waiting for the build"
        app.processEvents()
        time.sleep(0.01)


def _import(inbox: CaptureInboxView, package: Path) -> None:
    inbox._choose_file = lambda _parent: str(package)
    inbox.import_button.click()


def test_import_builds_model_automatically_and_opens_viewer(monkeypatch, tmp_path, repo_root):
    package = _package(tmp_path / "scan.packscan", repo_root)
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    app, window, inbox, builds = _window(monkeypatch, tmp_path, FakeBackend())
    try:
        assert window.project_manager.current is not None  # default project, no dialog
        assert window.navigation_panel.list.item(2).flags()  # Reconstruction reachable
        seen: list[str] = []
        window.job_manager.job_changed.connect(
            lambda job_id: seen.append(window.job_manager.get(job_id).message)
        )
        _import(inbox, package)
        assert "reported" in inbox.status_label.text()
        jobs = window.job_manager.jobs()
        assert len(jobs) == 1 and jobs[0].job_type == "reconstruction"
        assert window.navigation.current_route is Route.RECONSTRUCTION
        _pump(app, lambda: builds.result is not None)

        job = window.job_manager.get(jobs[0].job_id)
        assert job.state is JobState.SUCCEEDED, job.error
        assert any("Building the dense point cloud" in message for message in seen)
        assert builds.result is not None and builds.result.status == "succeeded"
        assert "1/1 photos registered" in builds.result.message
        assert builds.open_button.isEnabled() and not builds.next_steps.isHidden()
        viewer = window.route_stack.views[Route.MODEL_VIEWER]
        assert isinstance(viewer, ModelViewerView)
        assert window.navigation.current_route is Route.MODEL_VIEWER
        assert "scene_dense.ply" in viewer.status.text() and "Model built" in viewer.status.text()

        layout = window.project_manager.layout
        assert layout is not None
        raw = layout.path("raw", f"captures/{digest}.packscan")
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == digest
        manifest = json.loads((builds.result.workspace_dir / "manifest.json").read_text("utf-8"))
        assert manifest["state"] == "succeeded"
        assert manifest["source_asset_id"] == f"raw/captures/{digest}.packscan"
        assert manifest["parameters"]["output"]["authority_class"] == "RECONSTRUCTION_OBSERVATION"
        assert manifest["parameters"]["output"]["scale_state"] == "relative"
        provenance = layout.path("derived", "provenance.json").read_text("utf-8")
        assert '"reconstruction:' in provenance

        # A duplicate import does not queue a second build.
        _import(inbox, package)
        assert "duplicate" in inbox.status_label.text()
        assert len(window.job_manager.jobs()) == 1
    finally:
        window.close()
        app.processEvents()


def test_cancel_stops_build_and_keeps_scan(monkeypatch, tmp_path, repo_root):
    package = _package(tmp_path / "scan.packscan", repo_root)
    app, window, inbox, builds = _window(
        monkeypatch, tmp_path, FakeBackend(block_at="dense-point-cloud")
    )
    try:
        _import(inbox, package)
        job_id = window.job_manager.jobs()[0].job_id
        _pump(app, lambda: "dense point cloud" in window.job_manager.get(job_id).message)
        assert builds.cancel_button.isEnabled()
        builds.cancel_button.click()
        _pump(app, lambda: builds.result is not None)
        assert window.job_manager.get(job_id).state is JobState.CANCELLED
        assert builds.result is not None and builds.result.status == "cancelled"
        assert not builds.open_button.isEnabled()
        manifest = json.loads((builds.result.workspace_dir / "manifest.json").read_text("utf-8"))
        assert manifest["state"] == "cancelled"
        assert window.navigation.current_route is Route.RECONSTRUCTION
    finally:
        window.close()
        app.processEvents()


def test_cancel_while_queued_is_cancelled_not_failed(monkeypatch, tmp_path, repo_root):
    package = _package(tmp_path / "scan.packscan", repo_root)
    gate = threading.Event()
    app, window, inbox, builds = _window(monkeypatch, tmp_path, FakeBackend(provenance_gate=gate))
    try:
        _import(inbox, package)
        job_id = window.job_manager.jobs()[0].job_id
        assert window.job_manager.get(job_id).state is JobState.QUEUED
        builds.cancel_button.click()
        gate.set()
        _pump(app, lambda: builds.result is not None)
        assert window.job_manager.get(job_id).state is JobState.CANCELLED
        assert builds.result is not None and builds.result.status == "cancelled"
    finally:
        window.close()
        app.processEvents()


def test_engine_failure_is_surfaced(monkeypatch, tmp_path, repo_root):
    package = _package(tmp_path / "scan.packscan", repo_root)
    app, window, inbox, builds = _window(monkeypatch, tmp_path, FakeBackend(fail_at="matching"))
    try:
        _import(inbox, package)
        _pump(app, lambda: builds.result is not None)
        job = window.job_manager.jobs()[0]
        assert job.state is JobState.FAILED and "fake engine exited 1" in (job.error or "")
        assert "Build failed: fake engine exited 1" in builds.status.text()
        manifest = json.loads((builds.result.workspace_dir / "manifest.json").read_text("utf-8"))
        assert manifest["state"] == "failed"
    finally:
        window.close()
        app.processEvents()


def test_auto_build_setting_off_then_manual_build_button(monkeypatch, tmp_path, repo_root):
    package = _package(tmp_path / "scan.packscan", repo_root)
    settings = tmp_path / "settings.ini"
    app, window, inbox, builds = _window(
        monkeypatch, tmp_path, FakeBackend(), settings_path=settings
    )
    try:
        view = window.route_stack.views[Route.SETTINGS]
        assert isinstance(view, SettingsView) and view.auto_build.isChecked()  # default ON
        view.auto_build.setChecked(False)
        _import(inbox, package)
        assert window.job_manager.jobs() == ()
        inbox.inbox_list.setCurrentRow(0)
        assert inbox.build_button.isEnabled()
        inbox.build_button.click()
        assert len(window.job_manager.jobs()) == 1
        _pump(app, lambda: builds.result is not None)
    finally:
        window.close()
        app.processEvents()
    app, second, inbox, _builds = _window(
        monkeypatch, tmp_path, FakeBackend(), settings_path=settings
    )
    try:
        view = second.route_stack.views[Route.SETTINGS]
        assert isinstance(view, SettingsView) and not view.auto_build.isChecked()
        inbox.refresh_inbox()  # scans already in the inbox at startup never auto-build
        assert second.job_manager.jobs() == ()
    finally:
        second.close()
        app.processEvents()


def test_missing_engines_are_reported(monkeypatch) -> None:
    report = EngineDiscoveryReport(
        (EnginePathDiagnostic("colmap", None, "PATH", DiscoveryStatus.MISSING, "none"),)
    )
    monkeypatch.setattr(build_model, "discover_engines", lambda: report)
    with pytest.raises(BuildModelError, match="colmap"):
        ColmapOpenMvsBackend.discover()


def test_real_command_plan_is_a_valid_orchestration_plan(tmp_path) -> None:
    backend = ColmapOpenMvsBackend(
        tmp_path / "colmap.exe",
        {
            key: tmp_path / f"{key}.exe"
            for key in (
                "interface_colmap",
                "densify_point_cloud",
                "reconstruct_mesh",
                "refine_mesh",
                "texture_mesh",
            )
        },
        ffmpeg=None,
    )
    stages = backend.stages(tmp_path, "working/reconstruction/r1", {})
    assert tuple(stage.stage_id for stage in stages) == STAGE_ORDER
    assert all(stage.configuration["max_image_size"] == 2000 for stage in stages)
    # PL-0463: seeds and thread counts are part of every stage's recorded configuration.
    assert all(
        stage.configuration[key] == value
        for stage in stages
        for key, value in build_model.DETERMINISM.items()
    )


def test_command_plan_fixes_colmap_seeds_and_mapper_threads(monkeypatch, tmp_path) -> None:
    backend = ColmapOpenMvsBackend(
        tmp_path / "colmap.exe",
        {
            key: tmp_path / f"{key}.exe"
            for key in (
                "interface_colmap",
                "densify_point_cloud",
                "reconstruct_mesh",
                "refine_mesh",
                "texture_mesh",
            )
        },
        ffmpeg=None,
    )
    asset = "working/reconstruction/r1"
    commands: dict[str, list[tuple[str, ...]]] = {}

    def record(stage_id, planned, cancel):
        commands[stage_id] = [tuple(args) for args, _cwd in planned]
        return ReconstructionStageResult(stage_id, StageStatus.FAILED, 1, 0.0, "", "")

    monkeypatch.setattr(build_model, "_run_commands", record)
    copied: list[str] = []
    monkeypatch.setattr(build_model.shutil, "copyfile", lambda s, d: copied.append(Path(s).name))
    context = type(
        "Context",
        (),
        {
            "cancel": None,
            "job": type(
                "Job",
                (),
                {
                    "inputs": type(
                        "Inputs",
                        (),
                        {"image_asset_ids": tuple(f"{asset}/inputs/{n}.jpg" for n in "bac")},
                    )
                },
            ),
        },
    )
    stages = {stage.stage_id: stage for stage in backend.stages(tmp_path, asset, {})}
    for stage_id in ("feature-extraction", "matching", "sparse-mapping"):
        stages[stage_id].execute(context)  # type: ignore[arg-type]
    assert copied == ["a.jpg", "b.jpg", "c.jpg"]  # sorted, not package order

    def option(stage_id: str, name: str) -> str:
        args = commands[stage_id][-1]
        return args[args.index(name) + 1]

    assert option("feature-extraction", "--default_random_seed") == "0"
    threads = str(build_model.worker_threads(1))
    assert option("feature-extraction", "--FeatureExtraction.num_threads") == threads
    assert option("matching", "--FeatureMatching.num_threads") == threads
    assert option("matching", "--TwoViewGeometry.random_seed") == "0"
    assert option("sparse-mapping", "--Mapper.random_seed") == "0"
    assert option("sparse-mapping", "--Mapper.num_threads") == "1"


def _second_package(path: Path, repo_root: Path, number: int = 2) -> Path:
    manifest = json.loads(
        (repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8")
    )
    image = f"IMG{number}".encode()
    manifest["capture_id"] = f"capture-{number}"
    manifest["payloads"][0]["size_bytes"] = len(image)
    manifest["payloads"][0]["sha256"] = hashlib.sha256(image).hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": image, "metadata/photos.json": b"{}"})


def test_existing_scans_never_auto_build_at_startup_with_auto_on(
    monkeypatch, tmp_path, repo_root
) -> None:
    package = _package(tmp_path / "scan.packscan", repo_root)
    ReceiverSession(tmp_path / "inbox", tls_root=tmp_path / "tls", port=0).import_file(package)
    app, window, inbox, _builds = _window(monkeypatch, tmp_path, FakeBackend())
    try:
        settings = window.route_stack.views[Route.SETTINGS]
        assert isinstance(settings, SettingsView) and settings.auto_build.isChecked()
        inbox.refresh_inbox()
        assert inbox.inbox_list.count() == 1
        assert window.job_manager.jobs() == ()
    finally:
        window.close()
        app.processEvents()


def test_unreadable_index_at_startup_fails_closed(monkeypatch, tmp_path, repo_root) -> None:
    package = _package(tmp_path / "scan.packscan", repo_root)
    ReceiverSession(tmp_path / "inbox", tls_root=tmp_path / "tls", port=0).import_file(package)
    real_entries = ReceiverSession.entries
    calls = {"count": 0}

    def flaky_entries(self):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("index locked")
        return real_entries(self)

    monkeypatch.setattr(ReceiverSession, "entries", flaky_entries)
    app, window, inbox, _builds = _window(monkeypatch, tmp_path, FakeBackend())
    try:
        inbox.refresh_inbox()  # the first readable index becomes the baseline
        assert calls["count"] >= 2 and inbox.inbox_list.count() == 1
        assert window.job_manager.jobs() == ()
    finally:
        window.close()
        app.processEvents()


def test_builds_run_up_to_the_limit_in_order_and_duplicates_are_ignored(
    monkeypatch, tmp_path, repo_root
) -> None:
    packages = [
        _package(tmp_path / "first.packscan", repo_root),
        _second_package(tmp_path / "second.packscan", repo_root),
        _second_package(tmp_path / "third.packscan", repo_root, 3),
    ]
    gate = threading.Event()
    app, window, inbox, _builds = _window(monkeypatch, tmp_path, FakeBackend(provenance_gate=gate))
    try:
        settings = window.route_stack.views[Route.SETTINGS]
        assert isinstance(settings, SettingsView)
        assert settings.concurrent_builds.value() == 2 == window.build_model.max_concurrent
        _import(inbox, packages[0])
        first_job = window.job_manager.jobs()[0].job_id
        digest = hashlib.sha256(packages[0].read_bytes()).hexdigest()
        assert window.start_build("loopback-capture", digest) == first_job  # duplicate
        for package in packages[1:]:
            _import(inbox, package)
        jobs = [job.job_id for job in window.job_manager.jobs()]
        assert len(jobs) == 3
        # Two run at once (separate scans, separate workspaces); the third waits its turn.
        assert window.build_model._running == set(jobs[:2])
        assert [job_id for job_id, _start in window.build_model._queue] == jobs[2:]
        assert window.job_manager.get(jobs[2]).state is JobState.QUEUED
        settings.concurrent_builds.setValue(3)  # raising the limit starts the queued build
        assert window.build_model._running == set(jobs) and not window.build_model._queue
        gate.set()
        _pump(
            app,
            lambda: (
                not window.build_model._running
                and all(
                    window.job_manager.get(job_id).state is JobState.SUCCEEDED for job_id in jobs
                )
            ),
        )
    finally:
        window.close()
        app.processEvents()


def test_one_build_at_a_time_when_the_limit_is_one(monkeypatch, tmp_path, repo_root) -> None:
    gate = threading.Event()
    app, window, inbox, _builds = _window(monkeypatch, tmp_path, FakeBackend(provenance_gate=gate))
    try:
        window.build_model.set_max_concurrent(1)
        _import(inbox, _package(tmp_path / "first.packscan", repo_root))
        _import(inbox, _second_package(tmp_path / "second.packscan", repo_root))
        first_job, second_job = (job.job_id for job in window.job_manager.jobs())
        assert window.build_model._running == {first_job}
        assert window.job_manager.get(second_job).state is JobState.QUEUED
        gate.set()
        _pump(app, lambda: window.job_manager.get(second_job).state is JobState.SUCCEEDED)
    finally:
        window.close()
        app.processEvents()


def test_a_build_started_beside_another_gets_its_share_of_cores(
    monkeypatch, tmp_path, repo_root
) -> None:
    real = ColmapOpenMvsBackend(tmp_path / "colmap.exe", {}, ffmpeg=None)
    monkeypatch.setattr(ColmapOpenMvsBackend, "discover", classmethod(lambda cls: real))
    started: list[tuple[object, ...]] = []
    app, window, inbox, _builds = _window(monkeypatch, tmp_path, None)
    try:
        window.build_model._work = lambda *args: started.append(args)  # type: ignore[method-assign]
        _import(inbox, _package(tmp_path / "first.packscan", repo_root))
        _import(inbox, _second_package(tmp_path / "second.packscan", repo_root))
        _pump(app, lambda: len(started) == 2)
        shares = sorted(
            (args[2].cpu_share, args[8]["builds_sharing_cpu_at_start"])  # type: ignore[attr-defined,index]
            for args in started
        )
        assert shares == [(1, 1), (2, 2)]
        assert all(args[8]["max_concurrent_builds"] == 2 for args in started)  # type: ignore[index]
    finally:
        window.close()
        app.processEvents()


def test_thread_split_and_recorded_determinism(monkeypatch) -> None:
    monkeypatch.setattr(build_model.os, "cpu_count", lambda: 16)
    assert build_model.worker_threads(1) == 16 and build_model.worker_threads(2) == 8
    monkeypatch.setattr(build_model.os, "cpu_count", lambda: None)
    assert build_model.worker_threads(4) == 1
    monkeypatch.setattr(build_model.os, "cpu_count", lambda: 16)
    recorded = build_model.determinism(2, 3)
    assert recorded["colmap_extraction_threads"] == recorded["openmvs_max_threads"] == 8
    assert recorded["builds_sharing_cpu_at_start"] == 2 and recorded["max_concurrent_builds"] == 3
    assert recorded["colmap_mapper_threads"] == 1
    assert recorded["image_ids"] == "canonical_sorted_name"


def test_multithreaded_extraction_ids_are_renumbered_by_sorted_name(tmp_path) -> None:
    import sqlite3
    from contextlib import closing

    database = tmp_path / "database.db"
    with closing(sqlite3.connect(database)) as db, db:
        db.executescript(
            "CREATE TABLE images (image_id INTEGER PRIMARY KEY, name TEXT UNIQUE, camera_id INT);"
            "CREATE TABLE keypoints (image_id INTEGER PRIMARY KEY, data TEXT);"
            "CREATE TABLE descriptors (image_id INTEGER PRIMARY KEY, data TEXT);"
            "CREATE TABLE frames (frame_id INTEGER PRIMARY KEY, rig_id INT);"
            "CREATE TABLE frame_data (frame_id INT, data_id INT, sensor_id INT, sensor_type INT);"
            "CREATE TABLE matches (pair_id INTEGER PRIMARY KEY);"
            "CREATE TABLE two_view_geometries (pair_id INTEGER PRIMARY KEY);"
            "CREATE TABLE pose_priors (pose_prior_id INTEGER PRIMARY KEY);"
            "CREATE TABLE rig_sensors (rig_id INT);"
        )
        for image_id, name in enumerate(["c.jpg", "a.jpg", "b.jpg"], start=1):  # completion
            db.execute("INSERT INTO images VALUES (?, ?, 1)", (image_id, name))
            db.execute("INSERT INTO keypoints VALUES (?, ?)", (image_id, f"kp-{name}"))
            db.execute("INSERT INTO descriptors VALUES (?, ?)", (image_id, f"d-{name}"))
            db.execute("INSERT INTO frames VALUES (?, 1)", (image_id,))
            db.execute("INSERT INTO frame_data VALUES (?, ?, 1, 0)", (image_id, image_id))
    build_model.canonicalize_image_ids(database)
    with closing(sqlite3.connect(database)) as db, db:
        names = ["a.jpg", "b.jpg", "c.jpg"]
        assert db.execute("SELECT image_id, name FROM images ORDER BY 1").fetchall() == list(
            enumerate(names, start=1)
        )
        for table, prefix in (("keypoints", "kp"), ("descriptors", "d")):
            rows = db.execute(f"SELECT image_id, data FROM {table} ORDER BY 1").fetchall()
            assert rows == [(i, f"{prefix}-{name}") for i, name in enumerate(names, start=1)]
        assert db.execute("SELECT * FROM frame_data ORDER BY 1").fetchall() == [
            (i, i, 1, 0) for i in (1, 2, 3)
        ]
        db.execute("INSERT INTO matches VALUES (1)")
    with pytest.raises(BuildModelError, match="unexpected COLMAP database layout"):
        build_model.canonicalize_image_ids(database)  # never renumber after matching


def test_heic_decode_is_hardened_and_names_do_not_collide(tmp_path, monkeypatch) -> None:
    command = build_model.heic_decode_command(
        Path("ffmpeg.exe"), Path("in/IMG_1.HEIC"), Path("out/IMG_1.HEIC.jpg")
    )
    assert command[command.index("-protocol_whitelist") + 1] == "file"
    assert command[command.index("-f") + 1] == "mov"
    assert "-nostdin" in command and command.index("-f") < command.index("-i")
    assert build_model.working_image_name(Path("IMG_1.HEIC")) != (
        build_model.working_image_name(Path("IMG_1.JPG"))
    )
    # ffmpeg is never picked up from the current directory.
    (tmp_path / "ffmpeg.exe").write_bytes(b"stub")
    (tmp_path / "ffmpeg").write_bytes(b"stub")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PACKLAB_FFMPEG_PATH", raising=False)
    monkeypatch.setenv("PATH", ".")
    assert build_model.find_ffmpeg() is None


def test_unsupported_colmap_version_fails_closed(monkeypatch, tmp_path) -> None:
    def fake_stage(stage_id, args, **_kwargs):
        text = "COLMAP 3.12.6 -- Structure-from-Motion" if "help" in args else ""
        return ReconstructionStageResult(stage_id, StageStatus.SUCCEEDED, 0, 0.0, text)

    monkeypatch.setattr(build_model, "run_reconstruction_stage", fake_stage)
    (tmp_path / "logs").mkdir()
    backend = ColmapOpenMvsBackend(tmp_path / "colmap.exe", {"interface_colmap": tmp_path / "i"})
    with pytest.raises(BuildModelError, match="needs COLMAP 4.2.1"):
        backend.provenance(tmp_path)


def test_weak_registration_stops_before_dense_stages(monkeypatch, tmp_path) -> None:
    """Real scan 2026-11-22: 3 of 17 photos connected; refuse with retake advice."""
    import struct

    import pytest

    backend = ColmapOpenMvsBackend(
        tmp_path / "colmap.exe",
        {
            key: tmp_path / f"{key}.exe"
            for key in (
                "interface_colmap",
                "densify_point_cloud",
                "reconstruct_mesh",
                "refine_mesh",
                "texture_mesh",
            )
        },
        ffmpeg=None,
    )
    asset = "working/reconstruction/r1"
    sparse = tmp_path / "outputs/colmap/sparse/0"

    def run(stage_id, planned, cancel):
        (tmp_path / "outputs/colmap").mkdir(parents=True, exist_ok=True)
        (tmp_path / "outputs/colmap/database.db").write_bytes(b"db")
        if stage_id == "sparse-mapping":
            sparse.mkdir(parents=True, exist_ok=True)
            (sparse / "images.bin").write_bytes(struct.pack("<Q", registered))
        return ReconstructionStageResult(stage_id, StageStatus.SUCCEEDED, 0, 0.0, "", "")

    monkeypatch.setattr(build_model, "_run_commands", run)
    monkeypatch.setattr(build_model.shutil, "copyfile", lambda s, d: None)
    monkeypatch.setattr(build_model, "canonicalize_image_ids", lambda database: None)
    names = tuple(f"{asset}/inputs/{n:02d}.jpg" for n in range(17))
    context = type(
        "Context",
        (),
        {
            "cancel": None,
            "job": type(
                "Job",
                (),
                {"inputs": type("Inputs", (), {"image_asset_ids": names})},
            ),
        },
    )
    for registered, refused in ((3, True), (8, True), (9, False)):
        facts: dict[str, object] = {}
        stages = {s.stage_id: s for s in backend.stages(tmp_path, asset, facts)}
        for stage_id in ("feature-extraction", "matching"):
            stages[stage_id].execute(context)  # type: ignore[arg-type]
        if refused:
            with pytest.raises(build_model.BuildModelError, match=f"only {registered} of 17"):
                stages["sparse-mapping"].execute(context)  # type: ignore[arg-type]
        else:
            stages["sparse-mapping"].execute(context)  # type: ignore[arg-type]
            assert facts["registered_images"] == 9
