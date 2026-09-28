from __future__ import annotations

import hashlib
import json

from test_reconstruction_orchestrator import _request

from packlab_core.reconstruction import CancelToken
from packlab_studio.jobs import JobManager, JobState
from packlab_studio.project_layout import ProjectLayout
from packlab_studio.reconstruction_execution import ReconstructionExecutionService
from packlab_studio.reconstruction_workspace import (
    ReconstructionWorkspaceManager,
    WorkspaceState,
)


def test_cancelled_execution_keeps_source_intact_and_allows_new_revision(tmp_path) -> None:
    root = tmp_path / "project"
    layout = ProjectLayout.create(root)
    raw = layout.path("raw", "capture.packscan")
    raw_bytes = b"immutable raw capture"
    raw.write_bytes(raw_bytes)
    source_id = "raw/capture.packscan"
    digest = hashlib.sha256(raw_bytes).hexdigest()
    workspace_manager = ReconstructionWorkspaceManager(layout)
    workspace = workspace_manager.create(
        project_id="project-1",
        project_revision=3,
        source_asset_id=source_id,
        source_digest=digest,
        revision_id="r-cancelled",
    )
    jobs = JobManager()
    job = jobs.create("Reconstruct Scan", "reconstruction", job_id="job-1")
    token = CancelToken()
    token.cancel()

    execution = ReconstructionExecutionService(jobs, workspace_manager).execute(
        job.job_id, workspace, _request(), cancel=token
    )

    assert execution.result.status.value == "cancelled"
    assert jobs.get(job.job_id).state is JobState.CANCELLED
    manifest = json.loads((workspace.path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["state"] == WorkspaceState.CANCELLED.value
    assert manifest["reason"]
    assert raw.read_bytes() == raw_bytes

    retry = workspace_manager.create(
        project_id="project-1",
        project_revision=3,
        source_asset_id=source_id,
        source_digest=digest,
        revision_id="r-retry",
    )
    assert retry.path != workspace.path
    assert retry.state is WorkspaceState.ACTIVE


def test_repeated_workspace_cancellation_is_idempotent(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    raw = layout.path("raw", "capture.packscan")
    raw.write_bytes(b"raw")
    manager = ReconstructionWorkspaceManager(layout)
    workspace = manager.create(
        project_id="project-1",
        project_revision=0,
        source_asset_id="raw/capture.packscan",
        source_digest=hashlib.sha256(b"raw").hexdigest(),
        revision_id="r1",
    )
    first = manager.cancel(workspace, "first request")
    second = manager.cancel(first, "second request")
    assert first == second
    assert (
        json.loads((workspace.path / "manifest.json").read_text(encoding="utf-8"))["reason"]
        == "first request"
    )
