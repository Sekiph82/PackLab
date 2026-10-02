"""PackLab project identity and lifecycle authority."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .jobs import JobManager
from .project_layout import ProjectLayout, ProjectLayoutError
from .recovery import RecoveryItem, RecoveryManager

if TYPE_CHECKING:
    from packlab_core.front_direction import FrontDirectionRecord

PROJECT_SCHEMA_VERSION = "1.0"
AUTHORITY_SCHEMA_VERSION = 1


class ProjectError(RuntimeError):
    pass


class ProjectBusyError(ProjectError):
    pass


class RevisionConflict(ProjectError):
    pass


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    project_id: str
    name: str
    created_at: str
    updated_at: str
    schema_version: str = PROJECT_SCHEMA_VERSION
    revision: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema_version": self.schema_version,
            "revision": self.revision,
        }

    @classmethod
    def from_dict(cls, value: object) -> ProjectMetadata:
        if not isinstance(value, dict):
            raise ProjectError("project metadata must be an object")
        project_id = value.get("project_id")
        name = value.get("name")
        created_at = value.get("created_at")
        updated_at = value.get("updated_at")
        revision = value.get("revision")
        if (
            value.get("schema_version") != PROJECT_SCHEMA_VERSION
            or not isinstance(project_id, str)
            or not isinstance(name, str)
            or not isinstance(created_at, str)
            or not isinstance(updated_at, str)
            or not isinstance(revision, int)
            or revision < 0
        ):
            raise ProjectError("project metadata is malformed or unsupported")
        try:
            uuid.UUID(project_id)
        except (ValueError, AttributeError):
            raise ProjectError("project identity is invalid") from None
        return cls(project_id, name, created_at, updated_at, PROJECT_SCHEMA_VERSION, revision)


class ProjectManager:
    def __init__(self, *, job_manager: JobManager | None = None) -> None:
        self.job_manager = job_manager
        self.layout: ProjectLayout | None = None
        self.metadata: ProjectMetadata | None = None
        self.recovery: RecoveryManager | None = None
        self.recovery_items: tuple[RecoveryItem, ...] = ()
        self._listeners: list[Callable[[ProjectMetadata | None], None]] = []

    @property
    def current(self) -> ProjectMetadata | None:
        return self.metadata

    def add_listener(self, listener: Callable[[ProjectMetadata | None], None]) -> None:
        self._listeners.append(listener)

    def project_summary(self) -> dict[str, Any]:
        if self.metadata is None:
            return {"open": False}
        return {"open": True, **self.metadata.to_dict()}

    def portability_report(self):
        """Return the read-only M06 portability report for the open project."""

        if self.layout is None:
            raise ProjectError("no project is open")
        from .portability import PortabilityReport, scan_project_portability

        report = scan_project_portability(self.layout.root)
        if not isinstance(report, PortabilityReport):
            raise ProjectError("portability scanner returned an invalid report")
        return report

    def create_reconstruction_workspace(
        self,
        source_asset_id: str,
        source_digest: str,
        *,
        revision_id: str | None = None,
    ):
        """Create an isolated reconstruction revision through the project authority."""

        if self.layout is None or self.metadata is None:
            raise ProjectError("no project is open")
        from .reconstruction_workspace import ReconstructionWorkspaceManager

        manager = ReconstructionWorkspaceManager(self.layout)
        return manager.create(
            project_id=self.metadata.project_id,
            project_revision=self.metadata.revision,
            source_asset_id=source_asset_id,
            source_digest=source_digest,
            revision_id=revision_id,
        )

    def materialize_reconstruction_working_set(self, workspace):
        """Prepare backend inputs through the project-owned workspace authority."""

        if self.layout is None or self.metadata is None:
            raise ProjectError("no project is open")
        from .reconstruction_workspace import ReconstructionWorkspaceManager

        if workspace.project_id != self.metadata.project_id:
            raise ProjectError("workspace belongs to another project")
        if workspace.path.parent != self.layout.path("working", "reconstruction"):
            raise ProjectError("workspace is outside the project reconstruction area")
        return ReconstructionWorkspaceManager(self.layout).materialize_working_set(workspace)

    def persist_front_direction(
        self,
        record: FrontDirectionRecord,
        *,
        current_parent_ids: dict[str, str],
        expected_revision: int,
    ) -> ProjectMetadata:
        """Append front-direction provenance to project authority state."""

        if self.layout is None or self.metadata is None:
            raise ProjectError("no project is open")
        from packlab_core.front_direction import (
            FrontDirectionError,
            append_front_direction_revision,
        )

        disk_metadata, state = self._read_authority(self.layout)
        if (
            disk_metadata.project_id != self.metadata.project_id
            or disk_metadata.revision != self.metadata.revision
        ):
            raise RevisionConflict("project metadata changed on disk")
        if expected_revision != self.metadata.revision:
            raise RevisionConflict("editable state revision is stale")
        measurement = state.get("measurement_provenance", {})
        if not isinstance(measurement, dict):
            raise ProjectError("measurement provenance is malformed")
        try:
            history = append_front_direction_revision(
                measurement.get("front_direction_revisions", []),
                record,
                current_parent_ids=current_parent_ids,
            )
        except FrontDirectionError as error:
            raise ProjectError(str(error)) from error
        next_state = dict(state)
        next_measurement = dict(measurement)
        next_measurement["front_direction_revisions"] = history
        next_measurement["active_front_direction_revision"] = record.revision_id
        next_state["measurement_provenance"] = next_measurement
        return self.commit_edit(next_state, expected_revision=expected_revision)

    def import_reconstruction_camera_priors(
        self,
        workspace,
        *,
        use="initialization-only",
        per_image_use=None,
    ):
        """Consume PackScan camera priors through the project-owned workspace authority."""

        if self.layout is None or self.metadata is None:
            raise ProjectError("no project is open")
        from packlab_core.reconstruction import CameraPriorUse

        from .reconstruction_workspace import ReconstructionWorkspaceManager

        if workspace.project_id != self.metadata.project_id:
            raise ProjectError("workspace belongs to another project")
        if workspace.path.parent != self.layout.path("working", "reconstruction"):
            raise ProjectError("workspace is outside the project reconstruction area")
        try:
            prior_use = CameraPriorUse(use)
        except ValueError as error:
            raise ProjectError("camera prior use mode is invalid") from error
        return ReconstructionWorkspaceManager(self.layout).import_camera_priors(
            workspace,
            use=prior_use,
            per_image_use=per_image_use,
        )

    def new_project(self, root: str | Path, name: str) -> ProjectMetadata:
        self._ensure_close_allowed()
        target = Path(root)
        if target.exists():
            raise ProjectError("project destination already exists")
        staging = target.parent / f".{target.name}.creating-{uuid.uuid4().hex}"
        try:
            layout = ProjectLayout.create(staging)
            now = _now()
            metadata = ProjectMetadata(
                str(uuid.uuid4()), name.strip() or "Untitled Project", now, now
            )
            self._write_metadata(layout, metadata)
            self._atomic_json(layout.path("working", "state.json"), {})
            self._write_authority(layout, metadata, {})
            os.replace(staging, target)
        except (OSError, ProjectLayoutError, ProjectError) as error:
            self._remove_staging(staging)
            raise ProjectError("project creation failed") from error
        if self.metadata is not None:
            self.close(allow_active_jobs=True)
        self.layout = ProjectLayout.open(target)
        self.metadata, _ = self._read_authority(self.layout)
        self.recovery = RecoveryManager(self.layout)
        self.recovery_items = self.recovery.inspect()
        self.recovery.mark_start()
        self._notify()
        return self.metadata

    def open_project(self, root: str | Path) -> ProjectMetadata:
        target = Path(root)
        try:
            layout = ProjectLayout.open(target)
            metadata, _ = self._read_authority(layout)
        except (OSError, ValueError, ProjectLayoutError, ProjectError) as error:
            raise ProjectError("project cannot be opened") from error
        self.close()
        self.layout = layout
        self.metadata = metadata
        self.recovery = RecoveryManager(layout)
        self.recovery_items = self.recovery.inspect()
        self.recovery.mark_start()
        self._notify()
        return metadata

    def close(self, *, allow_active_jobs: bool = False) -> None:
        if (
            self.job_manager is not None
            and self.job_manager.active_jobs()
            and not allow_active_jobs
        ):
            raise ProjectBusyError("active jobs must finish or cancel before project close")
        if self.recovery is not None:
            self.recovery.mark_clean_close()
        self.layout = None
        self.metadata = None
        self.recovery = None
        self.recovery_items = ()
        self._notify()

    def accept_recovery(self, item_id: str) -> RecoveryItem | None:
        if self.recovery is None:
            return None
        item = self.recovery.accept(item_id)
        self.recovery_items = self.recovery.inspect()
        return item

    def discard_recovery(self, item_id: str) -> RecoveryItem | None:
        if self.recovery is None:
            return None
        item = self.recovery.discard(item_id)
        self.recovery_items = self.recovery.inspect()
        return item

    def commit_edit(
        self, state: dict[str, object], *, expected_revision: int | None = None
    ) -> ProjectMetadata:
        if self.layout is None or self.metadata is None:
            raise ProjectError("no project is open")
        disk_metadata, _ = self._read_authority(self.layout)
        if (
            disk_metadata.project_id != self.metadata.project_id
            or disk_metadata.revision != self.metadata.revision
        ):
            raise RevisionConflict("project metadata changed on disk")
        if expected_revision is not None and expected_revision != self.metadata.revision:
            raise RevisionConflict("editable state revision is stale")
        next_metadata = ProjectMetadata(
            self.metadata.project_id,
            self.metadata.name,
            self.metadata.created_at,
            _now(),
            self.metadata.schema_version,
            self.metadata.revision + 1,
        )
        self._write_authority(self.layout, next_metadata, state)
        self._after_authority_publish(next_metadata, state)
        self._atomic_json(self.layout.path("working", "state.json"), state)
        self._write_metadata(self.layout, next_metadata)
        self.metadata = next_metadata
        self._notify()
        return next_metadata

    @classmethod
    def _read_authority(cls, layout: ProjectLayout) -> tuple[ProjectMetadata, dict[str, Any]]:
        authority = layout.path("working", "authority.json")
        if authority.exists():
            value = json.loads(authority.read_text(encoding="utf-8"))
            if (
                not isinstance(value, dict)
                or value.get("schema_version") != AUTHORITY_SCHEMA_VERSION
            ):
                raise ProjectError("project authority is malformed or unsupported")
            metadata = ProjectMetadata.from_dict(value.get("metadata"))
            state = value.get("state")
            if not isinstance(state, dict):
                raise ProjectError("project editable state is malformed")
            mirror_metadata = ProjectMetadata.from_dict(
                json.loads(layout.path("working", "project.json").read_text(encoding="utf-8"))
            )
            if (
                mirror_metadata.project_id != metadata.project_id
                or mirror_metadata.name != metadata.name
                or mirror_metadata.created_at != metadata.created_at
                or mirror_metadata.schema_version != metadata.schema_version
            ):
                raise ProjectError("project metadata identity does not match authority")
            mirror_state = json.loads(
                layout.path("working", "state.json").read_text(encoding="utf-8")
            )
            if not isinstance(mirror_state, dict):
                raise ProjectError("project editable state is malformed")
            if mirror_metadata.revision != metadata.revision or mirror_state != state:
                cls._atomic_json(layout.path("working", "state.json"), state)
                cls._write_metadata(layout, metadata)
            return metadata, state
        metadata = ProjectMetadata.from_dict(
            json.loads(layout.path("working", "project.json").read_text(encoding="utf-8"))
        )
        state_path = layout.path("working", "state.json")
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        if not isinstance(state, dict):
            raise ProjectError("project editable state is malformed")
        return metadata, state

    def _ensure_close_allowed(self) -> None:
        if self.job_manager is not None and self.job_manager.active_jobs():
            raise ProjectBusyError("active jobs must finish or cancel before replacing the project")

    def _notify(self) -> None:
        for listener in tuple(self._listeners):
            listener(self.metadata)

    def _after_authority_publish(
        self, _metadata: ProjectMetadata, _state: dict[str, object]
    ) -> None:
        """Failure-injection seam; the authority file is already recoverable here."""

    @staticmethod
    def _write_metadata(layout: ProjectLayout, metadata: ProjectMetadata) -> None:
        target = layout.path("working", "project.json")
        fd, temporary_name = tempfile.mkstemp(prefix=".project-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(metadata.to_dict(), handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    @staticmethod
    def _write_authority(
        layout: ProjectLayout, metadata: ProjectMetadata, state: dict[str, object]
    ) -> None:
        ProjectManager._atomic_json(
            layout.path("working", "authority.json"),
            {
                "schema_version": AUTHORITY_SCHEMA_VERSION,
                "metadata": metadata.to_dict(),
                "state": state,
            },
        )

    @staticmethod
    def _atomic_json(target: Path, value: object) -> None:
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}-", suffix=".tmp", dir=target.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    @staticmethod
    def _remove_staging(path: Path) -> None:
        if not path.exists():
            return
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                child.rmdir()
        path.rmdir()
