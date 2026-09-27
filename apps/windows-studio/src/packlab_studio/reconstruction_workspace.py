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

from packlab_core.packscan import PackScanError, PackScanReport, read_packscan
from packlab_core.reconstruction import ReconstructionInputSet

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


@dataclass(frozen=True, slots=True)
class WorkingSetImage:
    """One immutable PackScan image and its byte-preserving working copy."""

    order: int
    source_asset_id: str
    source_sha256: str
    working_asset_id: str
    working_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "order": self.order,
            "source_asset_id": self.source_asset_id,
            "source_sha256": self.source_sha256,
            "working_asset_id": self.working_asset_id,
            "working_sha256": self.working_sha256,
        }


@dataclass(frozen=True, slots=True)
class ReconstructionWorkingSet:
    """Published, revision-scoped inputs for a reconstruction backend."""

    workspace: ReconstructionWorkspace
    preprocessing_policy: str
    preprocessing_version: str
    images: tuple[WorkingSetImage, ...]
    inputs: ReconstructionInputSet
    manifest_path: Path


WORKING_SET_SCHEMA_VERSION = 1
WORKING_SET_PREPROCESSING_POLICY = "byte-preserving-copy"
WORKING_SET_PREPROCESSING_VERSION = "1"


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

    def materialize_working_set(
        self, workspace: ReconstructionWorkspace
    ) -> ReconstructionWorkingSet:
        """Validate RAW_CAPTURE and publish deterministic, byte-preserving inputs.

        PackScan validation happens before any working input is written. Files are
        staged as atomic individual copies and the existing workspace manifest is
        published last, so a failed preparation cannot advertise a working set.
        """

        self._ensure_active(workspace)
        source = self._source_path(workspace.source_asset_id)
        if not self.source_is_intact(workspace):
            raise ReconstructionWorkspaceError("RAW_CAPTURE source changed")
        try:
            report = read_packscan(source)
        except PackScanError as error:
            raise ReconstructionWorkspaceError(
                f"RAW_CAPTURE PackScan validation failed: {error.code}"
            ) from error

        manifest = self._read_workspace_manifest(workspace)
        if manifest.get("working_set") is not None:
            raise ReconstructionWorkspaceError("working set is already published")

        image_paths = self._declared_image_paths(report)
        input_root = workspace.path / "inputs"
        self._ensure_empty_input_root(input_root)
        targets: list[tuple[str, Path, bytes]] = []
        seen_targets: set[str] = set()
        images: list[WorkingSetImage] = []
        for order, source_asset_id in enumerate(image_paths):
            data = report.payloads.get(source_asset_id)
            if data is None:
                raise ReconstructionWorkspaceError(
                    f"RAW_CAPTURE declared image is missing: {source_asset_id}"
                )
            try:
                relative = safe_relative_path(source_asset_id)
            except ProjectLayoutError as error:
                raise ReconstructionWorkspaceError(
                    f"working-set image path is unsafe: {source_asset_id}"
                ) from error
            working_asset_id = f"{workspace.relative_path}/inputs/{relative.as_posix()}"
            target = self._working_input_path(input_root, relative)
            target_key = target.relative_to(input_root).as_posix().casefold()
            if target_key in seen_targets or target.exists() or target.is_symlink():
                raise ReconstructionWorkspaceError(
                    f"working-set destination collision: {relative.as_posix()}"
                )
            seen_targets.add(target_key)
            digest = hashlib.sha256(data).hexdigest()
            targets.append((relative.as_posix(), target, data))
            images.append(
                WorkingSetImage(
                    order,
                    source_asset_id,
                    digest,
                    working_asset_id,
                    digest,
                )
            )

        if not images:
            raise ReconstructionWorkspaceError("RAW_CAPTURE contains no source images")
        inputs = ReconstructionInputSet(
            project_id=workspace.project_id,
            raw_capture_asset_id=workspace.source_asset_id,
            source_revision=workspace.revision_id,
            source_digest=workspace.source_digest,
            image_asset_ids=tuple(image.working_asset_id for image in images),
        )
        working_set = {
            "schema_version": WORKING_SET_SCHEMA_VERSION,
            "source_packscan_asset_id": workspace.source_asset_id,
            "source_packscan_sha256": workspace.source_digest,
            "preprocessing_policy": WORKING_SET_PREPROCESSING_POLICY,
            "preprocessing_version": WORKING_SET_PREPROCESSING_VERSION,
            "ordering": "lexicographic source asset ID",
            "images": [image.as_dict() for image in images],
            "reconstruction_input_set": inputs.as_dict(),
        }

        created: list[Path] = []
        try:
            for _relative, target, data in targets:
                target.parent.mkdir(parents=True, exist_ok=True)
                _atomic_bytes(target, data)
                created.append(target)
            self._write_manifest(workspace, working_set=working_set)
        except (OSError, ProjectLayoutError, ReconstructionWorkspaceError):
            for target in reversed(created):
                target.unlink(missing_ok=True)
            for directory in sorted(
                (path for path in input_root.rglob("*") if path.is_dir()),
                key=lambda path: len(path.parts),
                reverse=True,
            ):
                if directory != input_root:
                    directory.rmdir()
            raise

        return ReconstructionWorkingSet(
            workspace,
            WORKING_SET_PREPROCESSING_POLICY,
            WORKING_SET_PREPROCESSING_VERSION,
            tuple(images),
            inputs,
            workspace.path / "manifest.json",
        )

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
        working_set: dict[str, object] | None = None,
    ) -> None:
        manifest = {
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
        }
        if working_set is None:
            try:
                existing = json.loads(
                    (workspace.path / "manifest.json").read_text(encoding="utf-8")
                )
            except (OSError, ValueError):
                existing = None
            if isinstance(existing, dict) and "working_set" in existing:
                manifest["working_set"] = existing["working_set"]
        if working_set is not None:
            manifest["working_set"] = working_set
        _atomic_json(
            workspace.path / "manifest.json",
            manifest,
        )

    @staticmethod
    def _read_workspace_manifest(workspace: ReconstructionWorkspace) -> dict[str, object]:
        try:
            value = json.loads((workspace.path / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ReconstructionWorkspaceError("workspace manifest is corrupt") from error
        if not isinstance(value, dict):
            raise ReconstructionWorkspaceError("workspace manifest is corrupt")
        return value

    @staticmethod
    def _declared_image_paths(report: PackScanReport) -> tuple[str, ...]:
        payloads = report.manifest.get("payloads")
        if not isinstance(payloads, list):
            raise ReconstructionWorkspaceError("PackScan payload declaration is invalid")
        paths: list[str] = []
        for item in payloads:
            if not isinstance(item, dict) or item.get("kind") != "image":
                continue
            path = item.get("path")
            if not isinstance(path, str) or not path.startswith("images/"):
                raise ReconstructionWorkspaceError("PackScan image declaration is invalid")
            paths.append(path)
        return tuple(sorted(paths))

    @staticmethod
    def _ensure_empty_input_root(input_root: Path) -> None:
        if input_root.is_symlink() or not input_root.is_dir():
            raise ReconstructionWorkspaceError("working-set input boundary is unsafe")
        if any(input_root.iterdir()):
            raise ReconstructionWorkspaceError("working-set destination collision")

    @staticmethod
    def _working_input_path(input_root: Path, relative: Path) -> Path:
        target = (input_root / relative).resolve(strict=False)
        root = input_root.resolve()
        if os.path.commonpath((str(root), str(target))) != str(root):
            raise ReconstructionWorkspaceError("working-set destination escapes inputs")
        current = input_root
        for part in relative.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise ReconstructionWorkspaceError("working-set destination uses a symlink")
        return target

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
