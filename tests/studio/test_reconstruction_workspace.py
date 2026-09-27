from __future__ import annotations

import hashlib
import json

import pytest

from packlab_studio.project import ProjectManager
from packlab_studio.project_layout import ProjectLayout
from packlab_studio.provenance import ArtifactStatus, ProvenanceManager
from packlab_studio.reconstruction_workspace import (
    ReconstructionWorkspaceError,
    ReconstructionWorkspaceManager,
    WorkspaceState,
)


def _raw(layout: ProjectLayout, value: bytes = b"immutable raw") -> tuple[str, str]:
    path = layout.path("raw", "capture.packscan")
    path.write_bytes(value)
    return "raw/capture.packscan", hashlib.sha256(value).hexdigest()


def test_project_authority_creates_unique_isolated_revisions_without_raw_mutation(tmp_path) -> None:
    root = tmp_path / "project"
    manager = ProjectManager()
    metadata = manager.new_project(root, "Project")
    assert manager.layout is not None
    source_id, digest = _raw(manager.layout)
    raw_before = manager.layout.path("raw", "capture.packscan").read_bytes()

    first = manager.create_reconstruction_workspace(source_id, digest, revision_id="r1")
    workspace_manager = ReconstructionWorkspaceManager(manager.layout)
    workspace_manager.copy_raw_input(first, "images/capture.packscan")
    workspace_manager.write_output(first, "mesh/result.ply", b"first")
    record = workspace_manager.complete(first, parameters={"preset": "test"})

    second = workspace_manager.create(
        project_id=metadata.project_id,
        project_revision=metadata.revision,
        source_asset_id=source_id,
        source_digest=digest,
        revision_id="r2",
    )
    workspace_manager.write_output(second, "mesh/result.ply", b"second")
    workspace_manager.cancel(second)

    assert first.path != second.path
    assert json.loads((first.path / "manifest.json").read_text(encoding="utf-8"))["state"] == "succeeded"
    assert json.loads((second.path / "manifest.json").read_text(encoding="utf-8"))["state"] == "cancelled"
    assert record.status is ArtifactStatus.FRESH
    assert manager.layout.path("raw", "capture.packscan").read_bytes() == raw_before


def test_failed_workspace_isolated_and_terminal(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    source_id, digest = _raw(layout)
    manager = ReconstructionWorkspaceManager(layout)
    workspace = manager.create(
        project_id="project-1",
        project_revision=0,
        source_asset_id=source_id,
        source_digest=digest,
        revision_id="failed-retry-1",
    )
    failed = manager.fail(workspace, "stage failed")
    assert failed.state is WorkspaceState.FAILED
    with pytest.raises(ReconstructionWorkspaceError, match="terminal"):
        manager.write_output(failed, "mesh/result.ply", b"must not write")
    assert not (workspace.path / "outputs" / "mesh" / "result.ply").exists()


def test_source_change_invalidates_completed_provenance(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    source_id, digest = _raw(layout)
    manager = ReconstructionWorkspaceManager(layout)
    workspace = manager.create(
        project_id="project-1",
        project_revision=0,
        source_asset_id=source_id,
        source_digest=digest,
        revision_id="source-check-1",
    )
    manager.complete(workspace)
    layout.path("raw", "capture.packscan").write_bytes(b"changed")
    invalid = ProvenanceManager(layout).refresh_integrity()
    assert invalid[0].artifact_id == "reconstruction:source-check-1"
    assert invalid[0].status is ArtifactStatus.INVALID


def test_workspace_rejects_wrong_source_digest_and_unsafe_revision(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    source_id, _digest_value = _raw(layout)
    manager = ReconstructionWorkspaceManager(layout)
    with pytest.raises(ReconstructionWorkspaceError, match="does not match"):
        manager.create(
            project_id="project-1",
            project_revision=0,
            source_asset_id=source_id,
            source_digest=hashlib.sha256(b"wrong").hexdigest(),
            revision_id="r1",
        )
    with pytest.raises(ReconstructionWorkspaceError, match="unsafe"):
        manager.create(
            project_id="project-1",
            project_revision=0,
            source_asset_id=source_id,
            source_digest=hashlib.sha256(b"immutable raw").hexdigest(),
            revision_id="../escape",
        )
