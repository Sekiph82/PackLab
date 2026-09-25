from __future__ import annotations

import pytest

from packlab_studio.app import create_application
from packlab_studio.jobs import JobManager, JobPanel, JobState
from packlab_studio.shell import StudioMainWindow
from packlab_studio.workspace import DockId


def test_job_state_progress_failure_and_bounded_messages() -> None:
    manager = JobManager()
    job = manager.create("Reconstruct", "reconstruction", job_id="job-1")
    manager.start(job.job_id)
    manager.update_progress(job.job_id, 0.5, "x" * 500)
    assert job.progress == 0.5
    assert len(job.message) == 256
    with pytest.raises(ValueError):
        manager.update_progress(job.job_id, 0.4)
    manager.fail(job.job_id, "bad input", message="stopped")
    assert job.state is JobState.FAILED
    assert job.error == "bad input"


def test_concurrent_ordering_and_history_retention() -> None:
    manager = JobManager(history_limit=2)
    first = manager.create("One", "test", job_id="one")
    second = manager.create("Two", "test", job_id="two")
    manager.create("Three", "test", job_id="three")
    assert [job.job_id for job in manager.jobs()] == [second.job_id, "three"]
    manager.start(second.job_id)
    manager.succeed(second.job_id)
    manager.start("three")
    assert len(manager.active_jobs()) == 1
    assert first.job_id not in {job.job_id for job in manager.jobs()}


def test_cancel_hook_and_production_panel_composition(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-jobs-test"])
    window = StudioMainWindow()
    job = window.job_manager.create("Capture", "capture", job_id="capture-1")
    manager = window.job_manager
    manager.start(job.job_id)
    manager.register_cancel_hook(job.job_id, lambda: True)
    manager.request_cancel(job.job_id)
    assert manager.get(job.job_id).state is JobState.CANCELLED
    panel = window.workspace.docks[DockId.JOBS].widget()
    assert isinstance(panel, JobPanel)
    assert panel.count() == 1
    window.close()
    app.processEvents()
