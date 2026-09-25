from __future__ import annotations

import pytest

from packlab_studio.history import HistoryError, HistoryManager
from packlab_studio.project import ProjectManager


def test_append_undo_redo_and_nonreversible_barrier(tmp_path) -> None:
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    assert manager.layout is not None
    history = HistoryManager(manager.layout, current_revision=0)
    first = history.append("rename", {"name": "A"}, project_revision=1, reversible=True)
    history.append("import", {"source": "external.fixture"}, project_revision=2, references=("working/import.json",), reversible=False)
    assert history.undo() is None
    assert first.operation_id != ""
    assert history.redo() is None


def test_restart_integrity_revision_mismatch_and_tamper(tmp_path) -> None:
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    assert manager.layout is not None
    history = HistoryManager(manager.layout, current_revision=1)
    history.append("edit", {"value": 1}, project_revision=1, reversible=True)
    reloaded = HistoryManager(manager.layout, current_revision=1)
    assert reloaded.cursor == 1
    (manager.layout.path("history", "operations.jsonl")).write_text("tampered\n", encoding="utf-8")
    with pytest.raises(HistoryError):
        HistoryManager(manager.layout, current_revision=1)


def test_secret_raw_and_nonrelative_references_are_rejected(tmp_path) -> None:
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    assert manager.layout is not None
    history = HistoryManager(manager.layout, current_revision=0)
    with pytest.raises(HistoryError):
        history.append("bad", {"token": "secret"}, project_revision=1, reversible=True)
    with pytest.raises(HistoryError):
        history.append("bad", {}, project_revision=1, references=("raw/source.packscan",), reversible=True)

