"""Project-scoped crash markers and conservative recovery classification."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .project_layout import ProjectLayout, ProjectLayoutError


class RecoveryStatus(StrEnum):
    CLEAN = "clean"
    RESUMABLE = "resumable"
    RESTART_REQUIRED = "restart-required"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class RecoveryItem:
    item_id: str
    job_id: str
    status: RecoveryStatus
    area: str | None
    relative_path: str | None
    reason: str


class RecoveryManager:
    def __init__(self, layout: ProjectLayout) -> None:
        self.layout = layout
        self.marker = layout.path("recovery", "session.json")

    def mark_start(self) -> None:
        self._write({"schema_version": 1, "status": "active", "checkpoints": []})

    def checkpoint(self, job_id: str, *, area: str, relative_path: str, resumable: bool) -> None:
        if area not in {"temp", "derived"}:
            raise ValueError("recovery checkpoints may only reference temp or derived artifacts")
        path = self.layout.path(area, relative_path)
        payload = path.read_bytes() if path.is_file() else b""
        value = self._read()
        checkpoints = [item for item in value.get("checkpoints", []) if item.get("job_id") != job_id]
        checkpoints.append({"job_id": job_id, "area": area, "relative_path": relative_path, "resumable": resumable, "sha256": hashlib.sha256(payload).hexdigest()})
        value.update({"schema_version": 1, "status": "active", "checkpoints": checkpoints})
        self._write(value)

    def mark_clean_close(self) -> None:
        self._write({"schema_version": 1, "status": "clean", "checkpoints": []})

    def inspect(self) -> tuple[RecoveryItem, ...]:
        value = self._read()
        if value.get("status") != "active":
            return ()
        items: list[RecoveryItem] = []
        for checkpoint in value.get("checkpoints", []):
            job_id = str(checkpoint.get("job_id", "unknown"))
            area = checkpoint.get("area")
            relative_path = checkpoint.get("relative_path")
            if not isinstance(area, str) or not isinstance(relative_path, str) or area not in {"temp", "derived"}:
                items.append(RecoveryItem(job_id, job_id, RecoveryStatus.INVALID, None, None, "checkpoint metadata is invalid"))
                continue
            try:
                path = self.layout.path(area, relative_path)
            except ProjectLayoutError:
                items.append(RecoveryItem(job_id, job_id, RecoveryStatus.INVALID, area, relative_path, "checkpoint path is unsafe"))
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            expected = checkpoint.get("sha256")
            if digest is None or digest != expected:
                status = RecoveryStatus.INVALID
                reason = "partial artifact is missing or changed"
            elif bool(checkpoint.get("resumable")):
                status = RecoveryStatus.RESUMABLE
                reason = "checkpoint is resumable"
            else:
                status = RecoveryStatus.RESTART_REQUIRED
                reason = "job requires a clean restart"
            items.append(RecoveryItem(job_id, job_id, status, area, relative_path, reason))
        return tuple(items)

    def accept(self, item_id: str) -> RecoveryItem | None:
        return self._remove_item(item_id, delete_artifact=False)

    def discard(self, item_id: str) -> RecoveryItem | None:
        return self._remove_item(item_id, delete_artifact=True)

    def _remove_item(self, item_id: str, *, delete_artifact: bool) -> RecoveryItem | None:
        items = self.inspect()
        selected = next((item for item in items if item.item_id == item_id), None)
        if selected is None:
            return None
        if delete_artifact and selected.area in {"temp", "derived"} and selected.relative_path:
            path = self.layout.path(selected.area, selected.relative_path)
            if path.is_file():
                path.unlink()
        value = self._read()
        value["checkpoints"] = [item for item in value.get("checkpoints", []) if item.get("job_id") != item_id]
        if not value["checkpoints"]:
            value["status"] = "clean"
        self._write(value)
        return selected

    def _read(self) -> dict[str, Any]:
        try:
            value = json.loads(self.marker.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {"schema_version": 1, "status": "clean", "checkpoints": []}
        except (OSError, ValueError) as error:
            raise ValueError("recovery marker is corrupt") from error
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise ValueError("recovery marker is unsupported")
        return value

    def _write(self, value: dict[str, Any]) -> None:
        self.marker.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=".session-", suffix=".tmp", dir=self.marker.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.marker)
        finally:
            Path(temporary_name).unlink(missing_ok=True)
