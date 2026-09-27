"""Retry-safe, project-scoped reconstruction workspace authority."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .project_layout import ProjectLayout, ProjectLayoutError, safe_relative_path
from .provenance import ArtifactRecord, ProvenanceManager


class ReconstructionWorkspaceError(RuntimeError):
    pass


class WorkspaceState(StrEnum):
    ACTIVE = "active"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class ReconstructionWorkspace:
    project_id: str
    project_revision: int
    revision_id: str
    source_asset_id: str
    source_digest: str
    path: Path
    state: WorkspaceState

    @property
    def relative_path(self) -> str:
        return f"working/reconstruction/{self.revision_id}"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(target: Path, value: object) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def _atomic_bytes(target: Path, value: bytes) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


class ReconstructionWorkspaceManager:
    def __init__(self, layout: ProjectLayout, provenance: ProvenanceManager | None = None) -> None:
        self.layout = layout
        self.provenance = provenance or ProvenanceManager(layout)

    def create(
        self,
        *,
        project_id: str,
        project_revision: int,
        source_asset_id: str,
        source_digest: str,
        revision_id: str | None = None,
    ) -> ReconstructionWorkspace:
        source = self._source_path(source_asset_id)
        if not re.fullmatch(r"[0-9a-f]{64}", source_digest):
            raise ReconstructionWorkspaceError("source digest is invalid")
        if not source.is_file():
            raise ReconstructionWorkspaceError("RAW_CAPTURE source is missing")
        if _digest(source) != source_digest:
            raise ReconstructionWorkspaceError("RAW_CAPTURE source digest does not match")
        revision = revision_id or f"r-{uuid.uuid4().hex}"
        if not re.fullmatch(r"[A-Za-z0-9_-]+", revision):
            raise ReconstructionWorkspaceError("reconstruction revision is unsafe")
        path = self.layout.path("working", Path("reconstruction") / revision)
        if path.exists():
            raise ReconstructionWorkspaceError("reconstruction revision already exists")
        (path / "inputs").mkdir(parents=True)
        (path / "outputs").mkdir()
        (path / "logs").mkdir()
        workspace = ReconstructionWorkspace(
            project_id,
            project_revision,
            revision,
            source_asset_id,
            source_digest,
            path,
            WorkspaceState.ACTIVE,
        )
        self._write_manifest(workspace)
        return workspace

    def copy_raw_input(self, workspace: ReconstructionWorkspace, destination: str) -> str:
        self._ensure_active(workspace)
        destination_path = safe_relative_path(destination)
        source = self._source_path(workspace.source_asset_id)
        if not self.source_is_intact(workspace):
            raise ReconstructionWorkspaceError("RAW_CAPTURE source changed")
        target = workspace.path / "inputs" / destination_path
        target.parent.mkdir(parents=True, exist_ok=True)
        _atomic_bytes(target, source.read_bytes())
        return f"{workspace.relative_path}/inputs/{destination_path.as_posix()}"

    def write_output(self, workspace: ReconstructionWorkspace, relative_path: str, data: bytes) -> Path:
        self._ensure_active(workspace)
        target = workspace.path / "outputs" / safe_relative_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        _atomic_bytes(target, data)
        return target

    def complete(self, workspace: ReconstructionWorkspace, *, parameters: dict[str, Any] | None = None) -> ArtifactRecord:
        self._ensure_active(workspace)
        if not self.source_is_intact(workspace):
            self.fail(workspace, "RAW_CAPTURE source changed")
            raise ReconstructionWorkspaceError("RAW_CAPTURE source changed")
        completed = ReconstructionWorkspace(
            workspace.project_id,
            workspace.project_revision,
            workspace.revision_id,
            workspace.source_asset_id,
            workspace.source_digest,
            workspace.path,
            WorkspaceState.SUCCEEDED,
        )
        self._write_manifest(completed, parameters=parameters)
        return self.provenance.register(
            f"reconstruction:{workspace.revision_id}",
            workspace.relative_path,
            input_digests={workspace.source_asset_id: workspace.source_digest},
            parameters={"reconstruction_revision": workspace.revision_id, **(parameters or {})},
            project_revision=workspace.project_revision,
        )

    def fail(self, workspace: ReconstructionWorkspace, reason: str) -> ReconstructionWorkspace:
        return self._finish(workspace, WorkspaceState.FAILED, reason)

    def cancel(self, workspace: ReconstructionWorkspace, reason: str = "cancelled") -> ReconstructionWorkspace:
        return self._finish(workspace, WorkspaceState.CANCELLED, reason)

    def source_is_intact(self, workspace: ReconstructionWorkspace) -> bool:
        source = self._source_path(workspace.source_asset_id)
        return source.is_file() and _digest(source) == workspace.source_digest

    def _finish(self, workspace: ReconstructionWorkspace, state: WorkspaceState, reason: str) -> ReconstructionWorkspace:
        self._ensure_active(workspace)
        finished = ReconstructionWorkspace(
            workspace.project_id,
            workspace.project_revision,
            workspace.revision_id,
            workspace.source_asset_id,
            workspace.source_digest,
            workspace.path,
            state,
        )
        self._write_manifest(finished, reason=reason)
        return finished

    def _write_manifest(
        self,
        workspace: ReconstructionWorkspace,
        *,
        reason: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        _atomic_json(
            workspace.path / "manifest.json",
            {
                "schema_version": 1,
                "project_id": workspace.project_id,
                "project_revision": workspace.project_revision,
                "reconstruction_revision": workspace.revision_id,
                "source_asset_id": workspace.source_asset_id,
                "source_digest": workspace.source_digest,
                "workspace": workspace.relative_path,
                "state": workspace.state.value,
                "reason": reason,
                "parameters": parameters or {},
            },
        )

    @staticmethod
    def _ensure_active(workspace: ReconstructionWorkspace) -> None:
        if workspace.state is not WorkspaceState.ACTIVE:
            raise ReconstructionWorkspaceError("workspace is already terminal")

    def _source_path(self, source_asset_id: str) -> Path:
        normalized = source_asset_id.replace("\\", "/")
        if not normalized.startswith("raw/"):
            raise ReconstructionWorkspaceError("reconstruction source must be RAW_CAPTURE")
        try:
            return self.layout.path("raw", safe_relative_path(normalized[4:]))
        except ProjectLayoutError as error:
            raise ReconstructionWorkspaceError("RAW_CAPTURE source path is unsafe") from error
