from __future__ import annotations

import json

import pytest

from packlab_studio.project import ProjectError, ProjectManager, RevisionConflict


def test_revision_changes_only_on_authoritative_edit(tmp_path) -> None:
    manager = ProjectManager()
    metadata = manager.new_project(tmp_path / "project", "Project")
    assert metadata.revision == 0
    updated = manager.commit_edit({"name": "editable"}, expected_revision=0)
    assert updated.revision == 1
    assert manager.metadata is not None and manager.metadata.project_id == metadata.project_id
    manager.close()


def test_stale_disk_revision_and_expected_revision_are_rejected(tmp_path) -> None:
    root = tmp_path / "project"
    first = ProjectManager()
    first.new_project(root, "Project")
    second = ProjectManager()
    second.open_project(root)
    first.commit_edit({"value": 1}, expected_revision=0)
    with pytest.raises(RevisionConflict):
        second.commit_edit({"value": 2}, expected_revision=0)
    assert json.loads((root / "working" / "state.json").read_text(encoding="utf-8")) == {"value": 1}


def test_malformed_identity_is_rejected_on_reopen(tmp_path) -> None:
    root = tmp_path / "project"
    manager = ProjectManager()
    manager.new_project(root, "Project")
    metadata_path = root / "working" / "project.json"
    value = json.loads(metadata_path.read_text(encoding="utf-8"))
    value["project_id"] = "not-a-uuid"
    metadata_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ProjectError):
        ProjectManager().open_project(root)
