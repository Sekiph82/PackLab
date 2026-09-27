from __future__ import annotations

import json
import threading

import pytest
from PySide6.QtCore import Qt

from packlab_core.subprocess_runner import ProcessResult
from packlab_studio.history import HistoryError, HistoryManager
from packlab_studio.jobs import JobManager, JobState
from packlab_studio.project import ProjectBusyError, ProjectManager
from packlab_studio.provenance import ArtifactStatus, ProvenanceManager
from packlab_studio.recovery import RecoveryStatus
from packlab_studio.subprocess_jobs import OwnedSubprocessJob


def test_shell_restore_sanitizes_offscreen_geometry_against_work_area(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio.app import create_application
    from packlab_studio.preferences import PreferencesStore, WindowPreferences
    from packlab_studio.shell import StudioMainWindow

    app = create_application(["packlab-r01-preferences"])
    store = PreferencesStore(tmp_path / "preferences.json")
    store.save(WindowPreferences(geometry=(5000, 5000, 1600, 1200)))
    window = StudioMainWindow(preferences=store, available_work_area=(0, 0, 800, 600))
    assert 0 <= window.x() <= 720
    assert 0 <= window.y() <= 520
    assert window.width() <= 800
    assert window.height() <= 600
    window.close()
    app.processEvents()


def test_owned_subprocess_cancellation_only_finishes_its_owned_job(monkeypatch) -> None:
    import packlab_studio.subprocess_jobs as subprocess_jobs

    manager = JobManager()
    job = manager.create("owned", "process", job_id="owned")
    unrelated_cancelled = threading.Event()
    observed: dict[str, object] = {}

    def fake_run(args, *, cancel_event, cwd):
        observed["args"] = tuple(args)
        observed["cwd"] = cwd
        cancel_event.wait(1.0)
        return ProcessResult(tuple(args), -1, "", "", False, cancel_event.is_set(), None)

    monkeypatch.setattr(subprocess_jobs, "run_process", fake_run)
    owned = OwnedSubprocessJob(manager, job.job_id, ("packlab-owned", "--bounded"))
    worker = threading.Thread(target=owned.run)
    worker.start()
    while manager.get(job.job_id).state is not JobState.RUNNING:
        pass
    manager.request_cancel(job.job_id)
    worker.join(timeout=2.0)
    assert not worker.is_alive()
    assert manager.get(job.job_id).state is JobState.CANCELLED
    assert observed["args"] == ("packlab-owned", "--bounded")
    assert not unrelated_cancelled.is_set()


def test_owned_subprocess_cleanup_failure_is_structured(monkeypatch) -> None:
    import packlab_studio.subprocess_jobs as subprocess_jobs

    manager = JobManager()
    job = manager.create("owned", "process", job_id="owned-failure")

    def fake_run(args, *, cancel_event, cwd):
        cancel_event.wait(1.0)
        return ProcessResult(tuple(args), -1, "", "", False, True, "cleanup denied")

    monkeypatch.setattr(subprocess_jobs, "run_process", fake_run)
    owned = OwnedSubprocessJob(manager, job.job_id, ("packlab-owned",))
    worker = threading.Thread(target=owned.run)
    worker.start()
    while manager.get(job.job_id).state is not JobState.RUNNING:
        pass
    manager.request_cancel(job.job_id)
    worker.join(timeout=2.0)
    assert manager.get(job.job_id).state is JobState.FAILED
    assert manager.get(job.job_id).error == "cleanup denied"


def test_shell_diagnostics_collect_project_jobs_and_errors(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio.app import create_application
    from packlab_studio.shell import StudioMainWindow

    app = create_application(["packlab-r01-diagnostics"])
    window = StudioMainWindow(diagnostics_root=tmp_path / "diagnostics")
    window.new_project(tmp_path / "project", "Project")
    job = window.job_manager.create("broken", "test", job_id="broken")
    window.job_manager.start(job.job_id)
    window.job_manager.fail(job.job_id, r"C:\Users\private\failure")
    bundle = window.create_diagnostic_bundle(tmp_path / "bundle.json", logs="safe log")
    value = json.loads(bundle.path.read_text(encoding="utf-8"))
    assert value["project"]["open"] is True
    assert value["project"]["project_id"] == window.project_manager.current.project_id
    assert value["structured_errors"][0]["error"] == "[PATH_REDACTED]"
    assert "C:\\Users" not in bundle.path.read_text(encoding="utf-8")
    window.close()
    app.processEvents()


def test_project_switch_veto_happens_before_destination_creation(tmp_path) -> None:
    manager = ProjectManager(job_manager=JobManager())
    manager.new_project(tmp_path / "first", "First")
    job = manager.job_manager.create("active", "test", job_id="active")
    manager.job_manager.start(job.job_id)
    replacement = tmp_path / "replacement"
    with pytest.raises(ProjectBusyError):
        manager.new_project(replacement, "Replacement")
    assert not replacement.exists()


def test_shell_route_and_workspace_state_follows_project_manager(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio.app import create_application
    from packlab_studio.navigation import Route
    from packlab_studio.shell import StudioMainWindow
    from packlab_studio.workspace import DockId

    app = create_application(["packlab-r01-project-state"])
    window = StudioMainWindow()
    assert not bool(window.navigation_panel.list.item(1).flags() & Qt.ItemFlag.ItemIsEnabled)
    assert window.workspace.docks[DockId.SCENE].isHidden()
    window.new_project(tmp_path / "project", "Project")
    assert bool(window.navigation_panel.list.item(1).flags() & Qt.ItemFlag.ItemIsEnabled)
    assert not window.workspace.docks[DockId.SCENE].isHidden()
    window.navigation.navigate(Route.EDITOR)
    assert window.navigation.current_route is Route.EDITOR
    window.close()
    app.processEvents()


def test_authority_recovery_keeps_revision_and_state_consistent_after_injected_failure(
    monkeypatch, tmp_path
) -> None:
    root = tmp_path / "project"
    manager = ProjectManager()
    manager.new_project(root, "Project")
    manager.commit_edit({"value": 1}, expected_revision=0)
    monkeypatch.setattr(
        manager,
        "_after_authority_publish",
        lambda *_args: (_ for _ in ()).throw(OSError("injected publication failure")),
    )
    with pytest.raises(OSError):
        manager.commit_edit({"value": 2}, expected_revision=1)
    reopened = ProjectManager()
    metadata = reopened.open_project(root)
    assert metadata.revision == 2
    assert json.loads((root / "working" / "state.json").read_text(encoding="utf-8")) == {"value": 2}
    assert (
        json.loads((root / "working" / "project.json").read_text(encoding="utf-8"))["revision"] == 2
    )


def test_history_authority_survives_partial_mirror_failure_and_rejects_revision_gaps(
    monkeypatch, tmp_path
) -> None:
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    assert manager.layout is not None
    history = HistoryManager(manager.layout, current_revision=1)
    history.append("edit", {"value": 1}, project_revision=1, reversible=True)
    monkeypatch.setattr(
        history,
        "_before_authority_publish",
        lambda: (_ for _ in ()).throw(OSError("injected history failure")),
    )
    with pytest.raises(OSError):
        history.append("edit", {"value": 2}, project_revision=2, reversible=True)
    reopened = HistoryManager(manager.layout, current_revision=1)
    assert [entry.project_revision for entry in reopened.entries] == [1]
    with pytest.raises(HistoryError):
        history.append("gap", {}, project_revision=3, reversible=True)


def test_recovery_lifecycle_exposes_abnormal_reopen_and_preserves_raw(tmp_path) -> None:
    root = tmp_path / "project"
    manager = ProjectManager()
    manager.new_project(root, "Project")
    assert manager.layout is not None and manager.recovery is not None
    raw = manager.layout.path("raw", "source.packscan")
    raw.write_bytes(b"accepted")
    artifact = manager.layout.path("derived", "partial.bin")
    artifact.write_bytes(b"partial")
    manager.recovery.checkpoint(
        "job-1", area="derived", relative_path="partial.bin", resumable=True
    )
    reopened = ProjectManager()
    reopened.open_project(root)
    assert reopened.recovery_items[0].status is RecoveryStatus.RESUMABLE
    reopened.accept_recovery("job-1")
    assert artifact.read_bytes() == b"partial"
    reopened.close()
    assert (
        json.loads((root / "recovery" / "session.json").read_text(encoding="utf-8"))["status"]
        == "clean"
    )
    assert raw.read_bytes() == b"accepted"


def test_provenance_query_and_stale_reopen_propagate_deterministically(tmp_path) -> None:
    root = tmp_path / "project"
    manager = ProjectManager()
    manager.new_project(root, "Project")
    assert manager.layout is not None
    source = manager.layout.path("working", "source.bin")
    source.write_bytes(b"source")
    import hashlib

    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    provenance = ProvenanceManager(manager.layout)
    provenance.register(
        "a", "derived/a.bin", input_digests={"working/source.bin": digest}, project_revision=1
    )
    provenance.register("b", "derived/b.bin", upstream=("a",), project_revision=1)
    provenance.invalidate(changed_inputs={"working/source.bin"})
    reopened = ProvenanceManager(manager.layout)
    assert [record.artifact_id for record in reopened.stale_for_job_planning()] == ["a", "b"]
    assert [record.artifact_id for record in reopened.query(status=ArtifactStatus.STALE)] == [
        "a",
        "b",
    ]
    source.write_bytes(b"tampered")
    invalid = reopened.refresh_integrity()
    assert {record.artifact_id for record in invalid} == {"a", "b"}
