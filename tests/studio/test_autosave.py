from __future__ import annotations

import json

from packlab_studio.autosave import AutosaveService, SaveStatus
from packlab_studio.project import ProjectManager


def test_debounce_coalesces_and_flushes_atomically(tmp_path) -> None:
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    service = AutosaveService(manager, debounce_seconds=60)
    service.schedule({"value": 1})
    service.schedule({"value": 2})
    assert service.status is SaveStatus.PENDING
    assert service.flush() is SaveStatus.SAVED
    assert manager.metadata is not None and manager.metadata.revision == 1
    assert json.loads((tmp_path / "project" / "working" / "state.json").read_text(encoding="utf-8")) == {"value": 2}


def test_stale_conflict_and_write_failure_are_structured(tmp_path, monkeypatch) -> None:
    root = tmp_path / "project"
    manager = ProjectManager()
    manager.new_project(root, "Project")
    service = AutosaveService(manager, debounce_seconds=60)
    service.schedule({"value": 1})
    manager.commit_edit({"value": 0}, expected_revision=0)
    assert service.flush() is SaveStatus.CONFLICT
    assert (root / "raw").exists()

    monkeypatch.setattr(manager, "commit_edit", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")))
    service.schedule({"value": 2})
    assert service.flush() is SaveStatus.ERROR


def test_shutdown_flush_policy_does_not_touch_raw(tmp_path) -> None:
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    raw_marker = tmp_path / "project" / "raw" / "accepted.packscan"
    raw_marker.write_bytes(b"immutable")
    service = AutosaveService(manager, debounce_seconds=60)
    service.schedule({"edit": True})
    assert service.shutdown_flush() is SaveStatus.SAVED
    assert raw_marker.read_bytes() == b"immutable"
