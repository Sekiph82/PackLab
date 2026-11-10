from __future__ import annotations

import errno
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


def test_disk_full_during_authority_publish_preserves_last_committed_project(
    tmp_path, monkeypatch
) -> None:
    """An ENOSPC at the atomic publish boundary leaves the prior revision recoverable."""
    import packlab_studio.project as project_module

    root = tmp_path / "project"
    manager = ProjectManager()
    manager.new_project(root, "Project")
    manager.commit_edit({"value": "committed"}, expected_revision=0)
    raw_path = root / "raw" / "capture.packscan"
    raw_path.write_bytes(b"immutable raw")
    prior_authority = (root / "working" / "authority.json").read_bytes()
    real_replace = project_module.os.replace

    def fail_authority_publish(source, target):
        if str(target).endswith("authority.json"):
            raise OSError(errno.ENOSPC, "No space left on device")
        return real_replace(source, target)

    monkeypatch.setattr(project_module.os, "replace", fail_authority_publish)
    with pytest.raises(ProjectError, match="previous revision is preserved") as error:
        manager.commit_edit({"value": "uncommitted"}, expected_revision=1)

    assert isinstance(error.value.__cause__, OSError)
    assert error.value.__cause__.errno == errno.ENOSPC
    assert manager.metadata is not None and manager.metadata.revision == 1
    assert (root / "working" / "authority.json").read_bytes() == prior_authority
    assert json.loads((root / "working" / "state.json").read_text(encoding="utf-8")) == {
        "value": "committed"
    }
    assert raw_path.read_bytes() == b"immutable raw"
    assert not list((root / "working").glob(".authority.json-*.tmp"))


def test_low_space_preflight_is_injected_and_preserves_prior_revision(tmp_path) -> None:
    root = tmp_path / "project"
    manager = ProjectManager(free_space_reader=lambda _path: 0)
    manager.new_project(root, "Project")
    prior_authority = (root / "working" / "authority.json").read_bytes()
    prior_state = (root / "working" / "state.json").read_bytes()
    raw_path = root / "raw" / "capture.packscan"
    raw_path.write_bytes(b"immutable raw")

    with pytest.raises(ProjectError, match="insufficient disk space"):
        manager.commit_edit({"value": "not committed"}, expected_revision=0)

    assert manager.metadata is not None and manager.metadata.revision == 0
    assert (root / "working" / "authority.json").read_bytes() == prior_authority
    assert (root / "working" / "state.json").read_bytes() == prior_state
    assert raw_path.read_bytes() == b"immutable raw"
    assert not list((root / "working").glob(".authority.json-*.tmp"))


@pytest.mark.parametrize(
    "provider_behavior",
    [
        OSError("usage unavailable"),
        RuntimeError("provider failed"),
        True,
        -1,
        1.5,
        None,
    ],
)
def test_invalid_or_failing_space_provider_fails_closed_without_mutation(
    tmp_path, provider_behavior
) -> None:
    def read_space(_path):
        if isinstance(provider_behavior, BaseException):
            raise provider_behavior
        return provider_behavior

    root = tmp_path / "project"
    manager = ProjectManager(free_space_reader=read_space)
    manager.new_project(root, "Project")
    prior_authority = (root / "working" / "authority.json").read_bytes()
    prior_state = (root / "working" / "state.json").read_bytes()
    raw_path = root / "raw" / "capture.packscan"
    raw_path.write_bytes(b"immutable raw")
    expected = (
        "cannot verify free disk space"
        if isinstance(provider_behavior, BaseException)
        else "invalid result"
    )

    with pytest.raises(ProjectError, match=expected):
        manager.commit_edit({"value": "not committed"}, expected_revision=0)

    assert manager.metadata is not None and manager.metadata.revision == 0
    assert (root / "working" / "authority.json").read_bytes() == prior_authority
    assert (root / "working" / "state.json").read_bytes() == prior_state
    assert raw_path.read_bytes() == b"immutable raw"
    assert not list((root / "working").glob(".authority.json-*.tmp"))


def test_restart_repairs_mirrors_from_authority_after_interrupted_commit(tmp_path) -> None:
    root = tmp_path / "project"

    class InterruptedProjectManager(ProjectManager):
        def _after_authority_publish(self, _metadata, _state) -> None:
            raise OSError("simulated process interruption after durable authority publish")

    interrupted = InterruptedProjectManager()
    initial = interrupted.new_project(root, "Project")
    raw_path = root / "raw" / "capture.packscan"
    raw_path.write_bytes(b"immutable raw")
    with pytest.raises(OSError, match="simulated process interruption"):
        interrupted.commit_edit({"value": "durable"}, expected_revision=0)

    # Simulate the crash window: authority is durable while compatibility mirrors are stale.
    assert json.loads((root / "working" / "state.json").read_text(encoding="utf-8")) == {}
    assert (
        json.loads((root / "working" / "project.json").read_text(encoding="utf-8"))["revision"]
        == initial.revision
    )

    restarted = ProjectManager()
    recovered = restarted.open_project(root)
    assert recovered.revision == 1
    assert json.loads((root / "working" / "state.json").read_text(encoding="utf-8")) == {
        "value": "durable"
    }
    assert (
        json.loads((root / "working" / "project.json").read_text(encoding="utf-8"))["revision"]
        == recovered.revision
    )
    assert raw_path.read_bytes() == b"immutable raw"


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
