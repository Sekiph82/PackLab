from __future__ import annotations

import json

import pytest

from packlab_core.front_direction import select_front_direction
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


def test_front_direction_history_persists_and_survives_project_reopen(tmp_path) -> None:
    root = tmp_path / "project"
    manager = ProjectManager()
    manager.new_project(root, "Project")
    parents = {
        "base_plane_selection_id": "plane-r1",
        "upright_alignment_id": "upright-r1",
        "geometry_id": "geometry-r1",
        "reconstruction_revision": "reconstruction-r1",
        "camera_solution_revision": "camera-r1",
    }
    first = select_front_direction(
        (1, 0, 0),
        source="operator_selection",
        actor_id="operator-1",
        evidence_id="event-1",
        **parents,
        coordinate_unit="reconstruction_units",
    )
    manager.persist_front_direction(first, current_parent_ids=parents, expected_revision=0)
    manager.close()
    reopened = ProjectManager()
    reopened.open_project(root)
    second = select_front_direction(
        (0, 1, 0),
        source="operator_selection",
        actor_id="operator-1",
        evidence_id="event-2",
        **parents,
        coordinate_unit="reconstruction_units",
    )
    reopened.persist_front_direction(second, current_parent_ids=parents, expected_revision=1)
    reopened.close()
    persisted = json.loads((root / "working" / "state.json").read_text(encoding="utf-8"))
    history = persisted["measurement_provenance"]["front_direction_revisions"]
    assert [record["revision_id"] for record in history] == [first.revision_id, second.revision_id]
    assert (
        persisted["measurement_provenance"]["active_front_direction_revision"] == second.revision_id
    )


def test_front_direction_persistence_rejects_stale_parents(tmp_path) -> None:
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    parents = {
        "base_plane_selection_id": "plane-r1",
        "upright_alignment_id": "upright-r1",
        "geometry_id": "geometry-r1",
        "reconstruction_revision": "reconstruction-r1",
        "camera_solution_revision": "camera-r1",
    }
    record = select_front_direction(
        (1, 0, 0),
        source="operator_selection",
        actor_id="operator-1",
        evidence_id="event-1",
        **parents,
        coordinate_unit="reconstruction_units",
    )
    with pytest.raises(ProjectError, match="stale_parent"):
        manager.persist_front_direction(
            record,
            current_parent_ids=dict(parents, reconstruction_revision="reconstruction-r2"),
            expected_revision=0,
        )
    assert manager.metadata is not None and manager.metadata.revision == 0
