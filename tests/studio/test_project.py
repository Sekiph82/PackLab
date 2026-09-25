from __future__ import annotations

import pytest

from packlab_studio.jobs import JobManager
from packlab_studio.project import ProjectBusyError, ProjectError, ProjectManager


def test_new_open_close_and_switch_projects(tmp_path) -> None:
    manager = ProjectManager()
    first = manager.new_project(tmp_path / "first", "First")
    assert manager.current == first
    second_root = tmp_path / "second"
    second = manager.new_project(second_root, "Second")
    assert manager.current == second
    reopened = manager.open_project(tmp_path / "first")
    assert reopened.project_id == first.project_id
    manager.close()
    assert manager.current is None


def test_duplicate_corrupt_and_partial_creation_fail_cleanly(tmp_path) -> None:
    manager = ProjectManager()
    root = tmp_path / "project"
    manager.new_project(root, "Project")
    with pytest.raises(ProjectError):
        manager.new_project(root, "Duplicate")
    (root / "working" / "project.json").write_text("broken", encoding="utf-8")
    with pytest.raises(ProjectError):
        manager.open_project(root)
    assert not list(tmp_path.glob(".*.creating-*"))


def test_active_job_requires_explicit_close_policy(monkeypatch, tmp_path) -> None:
    jobs = JobManager()
    manager = ProjectManager(job_manager=jobs)
    manager.new_project(tmp_path / "project", "Project")
    job = jobs.create("work", "owned", job_id="work")
    jobs.start(job.job_id)
    with pytest.raises(ProjectBusyError):
        manager.close()
    manager.close(allow_active_jobs=True)
    assert manager.current is None


def test_shell_context_is_project_manager(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio.app import create_application
    from packlab_studio.shell import StudioMainWindow

    app = create_application(["packlab-project-shell"])
    window = StudioMainWindow()
    assert window.navigation.project_context is window.project_manager
    window.close()
    app.processEvents()
