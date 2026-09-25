"""PackLab project identity and lifecycle authority."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .jobs import JobManager
from .project_layout import ProjectLayout, ProjectLayoutError

PROJECT_SCHEMA_VERSION = "1.0"


class ProjectError(RuntimeError):
    pass


class ProjectBusyError(ProjectError):
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

    @property
    def current(self) -> ProjectMetadata | None:
        return self.metadata

    def new_project(self, root: str | Path, name: str) -> ProjectMetadata:
        target = Path(root)
        if target.exists():
            raise ProjectError("project destination already exists")
        staging = target.parent / f".{target.name}.creating-{uuid.uuid4().hex}"
        try:
            layout = ProjectLayout.create(staging)
            now = _now()
            metadata = ProjectMetadata(str(uuid.uuid4()), name.strip() or "Untitled Project", now, now)
            self._write_metadata(layout, metadata)
            os.replace(staging, target)
        except (OSError, ProjectLayoutError, ProjectError) as error:
            self._remove_staging(staging)
            raise ProjectError("project creation failed") from error
        if self.metadata is not None:
            self.close()
        self.layout = ProjectLayout.open(target)
        self.metadata = ProjectMetadata.from_dict(json.loads((target / "working" / "project.json").read_text(encoding="utf-8")))
        return self.metadata

    def open_project(self, root: str | Path) -> ProjectMetadata:
        target = Path(root)
        try:
            layout = ProjectLayout.open(target)
            metadata = ProjectMetadata.from_dict(json.loads((layout.path("working", "project.json")).read_text(encoding="utf-8")))
        except (OSError, ValueError, ProjectLayoutError, ProjectError) as error:
            raise ProjectError("project cannot be opened") from error
        self.close()
        self.layout = layout
        self.metadata = metadata
        return metadata

    def close(self, *, allow_active_jobs: bool = False) -> None:
        if self.job_manager is not None and self.job_manager.active_jobs() and not allow_active_jobs:
            raise ProjectBusyError("active jobs must finish or cancel before project close")
        self.layout = None
        self.metadata = None

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
    def _remove_staging(path: Path) -> None:
        if not path.exists():
            return
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                child.rmdir()
        path.rmdir()
