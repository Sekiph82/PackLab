from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from packlab_core.packscan import read_packscan, write_packscan
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


def _packscan(repo_root: Path, destination: Path, *, image_count: int = 2) -> Path:
    manifest = json.loads(
        (repo_root / "tests" / "fixtures" / "packscan" / "manifest-valid.json").read_text(
            encoding="utf-8"
        )
    )
    payloads: list[dict[str, object]] = [
        {
            "path": f"images/{index:04d}.jpg",
            "kind": "image",
            "required": True,
            "authority": "source",
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "media_type": "image/jpeg",
        }
        for index, data in enumerate(
            (f"IMAGE-{index}".encode("ascii") for index in range(1, image_count + 1)),
            start=1,
        )
    ]
    payloads.append(
        {
            "path": "metadata/photos.json",
            "kind": "photo_metadata",
            "required": True,
            "authority": "source",
            "size_bytes": 2,
            "sha256": hashlib.sha256(b"{}").hexdigest(),
            "media_type": "application/json",
        }
    )
    manifest["capture_id"] = "working-set-capture"
    manifest["payloads"] = payloads
    images = {
        item["path"]: f"IMAGE-{index}".encode("ascii")
        for index, item in enumerate(payloads[:-1], start=1)
    }
    return write_packscan(destination, manifest, {**images, "metadata/photos.json": b"{}"})


def _raw_packscan(layout: ProjectLayout, package: Path) -> tuple[str, str, bytes]:
    raw = layout.path("raw", "capture.packscan")
    data = package.read_bytes()
    raw.write_bytes(data)
    return "raw/capture.packscan", hashlib.sha256(data).hexdigest(), data


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


def test_materialize_working_set_preserves_bytes_and_binds_reconstruction_inputs(
    tmp_path: Path, repo_root: Path
) -> None:
    package = _packscan(repo_root, tmp_path / "capture.packscan")
    manager = ProjectManager()
    metadata = manager.new_project(tmp_path / "project", "Project")
    assert manager.layout is not None
    source_id, source_digest, raw_before = _raw_packscan(manager.layout, package)
    workspace = manager.create_reconstruction_workspace(source_id, source_digest, revision_id="r1")

    result = manager.materialize_reconstruction_working_set(workspace)

    assert result.inputs.project_id == metadata.project_id
    assert result.inputs.raw_capture_asset_id == source_id
    assert result.inputs.source_revision == "r1"
    assert result.inputs.source_digest == source_digest
    assert [image.order for image in result.images] == [0, 1]
    assert [image.source_asset_id for image in result.images] == [
        "images/0001.jpg",
        "images/0002.jpg",
    ]
    assert all(image.source_sha256 == image.working_sha256 for image in result.images)
    source_payloads = read_packscan(package).payloads
    for image in result.images:
        working = manager.layout.root / image.working_asset_id
        assert working.is_file()
        assert working.read_bytes() == source_payloads[image.source_asset_id]
        assert hashlib.sha256(working.read_bytes()).hexdigest() == image.source_sha256
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["working_set"]["preprocessing_policy"] == "byte-preserving-copy"
    assert manifest["working_set"]["preprocessing_version"] == "1"
    assert manifest["working_set"]["reconstruction_input_set"] == result.inputs.as_dict()
    assert manager.layout.path("raw", "capture.packscan").read_bytes() == raw_before


def test_working_set_revisions_are_isolated_and_existing_set_is_not_overwritten(
    tmp_path: Path, repo_root: Path
) -> None:
    package = _packscan(repo_root, tmp_path / "capture.packscan")
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    assert manager.layout is not None
    source_id, source_digest, _raw_before = _raw_packscan(manager.layout, package)
    first = manager.create_reconstruction_workspace(source_id, source_digest, revision_id="r1")
    second = manager.create_reconstruction_workspace(source_id, source_digest, revision_id="r2")

    first_set = manager.materialize_reconstruction_working_set(first)
    second_set = manager.materialize_reconstruction_working_set(second)

    assert first_set.inputs.image_asset_ids != second_set.inputs.image_asset_ids
    first_bytes = (manager.layout.root / first_set.inputs.image_asset_ids[0]).read_bytes()
    with pytest.raises(ReconstructionWorkspaceError, match="already published"):
        manager.materialize_reconstruction_working_set(first)
    assert (manager.layout.root / first_set.inputs.image_asset_ids[0]).read_bytes() == first_bytes


def test_invalid_packscan_fails_closed_without_publishing_inputs(tmp_path: Path, repo_root: Path) -> None:
    package = _packscan(repo_root, tmp_path / "capture.packscan")
    raw_package = tmp_path / "invalid.packscan"
    raw_package.write_bytes(package.read_bytes()[:-10])
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    assert manager.layout is not None
    raw = manager.layout.path("raw", "capture.packscan")
    raw.write_bytes(raw_package.read_bytes())
    workspace = manager.create_reconstruction_workspace(
        "raw/capture.packscan", hashlib.sha256(raw.read_bytes()).hexdigest(), revision_id="r1"
    )

    with pytest.raises(ReconstructionWorkspaceError, match="PackScan validation failed"):
        manager.materialize_reconstruction_working_set(workspace)

    assert not any(workspace.path.joinpath("inputs").rglob("*"))
    assert "working_set" not in json.loads(
        (workspace.path / "manifest.json").read_text(encoding="utf-8")
    )


def test_destination_collision_and_copy_failure_leave_no_partial_working_set(
    tmp_path: Path, repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = _packscan(repo_root, tmp_path / "capture.packscan")
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Project")
    assert manager.layout is not None
    source_id, source_digest, _raw_before = _raw_packscan(manager.layout, package)
    collision = manager.create_reconstruction_workspace(
        source_id, source_digest, revision_id="collision"
    )
    existing = collision.path / "inputs" / "images" / "0001.jpg"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"owner-file")
    with pytest.raises(ReconstructionWorkspaceError, match="destination collision"):
        manager.materialize_reconstruction_working_set(collision)
    assert existing.read_bytes() == b"owner-file"

    failing = manager.create_reconstruction_workspace(
        source_id, source_digest, revision_id="failing"
    )
    import packlab_studio.reconstruction_workspace as module

    original_atomic_bytes = module._atomic_bytes
    calls = 0

    def fail_second_copy(target: Path, value: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic copy failure")
        original_atomic_bytes(target, value)

    monkeypatch.setattr(module, "_atomic_bytes", fail_second_copy)
    with pytest.raises(OSError, match="synthetic copy failure"):
        manager.materialize_reconstruction_working_set(failing)
    assert not any(failing.path.joinpath("inputs").rglob("*"))
    assert "working_set" not in json.loads(
        (failing.path / "manifest.json").read_text(encoding="utf-8")
    )
