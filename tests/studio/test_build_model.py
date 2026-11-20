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
