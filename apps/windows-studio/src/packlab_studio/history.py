"""Append-only, integrity-chained logical project operation history."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .project_layout import ProjectLayout, safe_relative_path


class HistoryError(ValueError):
    pass


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class Operation:
    operation_id: str
    project_revision: int
    timestamp: str
    operation_type: str
    parameters: dict[str, Any]
    references: tuple[str, ...]
    reversible: bool
    previous_digest: str
    digest: str


class HistoryManager:
    def __init__(self, layout: ProjectLayout, *, current_revision: int) -> None:
        self.layout = layout
        self.path = layout.path("history", "operations.jsonl")
        self.cursor_path = layout.path("history", "cursor.json")
        self.entries = self._load(current_revision)
        self.cursor = self._load_cursor()
        if self.cursor > len(self.entries):
            raise HistoryError("history cursor is beyond the operation log")

    def append(
        self,
        operation_type: str,
        parameters: dict[str, Any],
        *,
        project_revision: int,
        references: tuple[str, ...] = (),
        reversible: bool,
    ) -> Operation:
        if self.entries and project_revision != self.entries[-1].project_revision + 1:
            raise HistoryError("operation revision is not continuous")
        if not self.entries and project_revision < 1:
            raise HistoryError("first operation must follow a committed revision")
        safe_reference_paths = tuple(safe_relative_path(reference) for reference in references)
        if any(path.parts[0] == "raw" for path in safe_reference_paths):
            raise HistoryError("raw evidence cannot be referenced as mutable history state")
        safe_references = tuple(str(path) for path in safe_reference_paths)
        self._validate_value(parameters)
        operation_id = uuid.uuid4().hex
        timestamp = _now()
        base: dict[str, Any] = {
            "operation_id": operation_id,
            "project_revision": project_revision,
            "timestamp": timestamp,
            "operation_type": operation_type,
            "parameters": parameters,
            "references": list(safe_references),
            "reversible": reversible,
            "previous_digest": self.entries[-1].digest if self.entries else "",
        }
        digest = self._digest(base)
        operation = Operation(
            base["operation_id"],
            base["project_revision"],
            base["timestamp"],
            base["operation_type"],
            base["parameters"],
            safe_references,
            base["reversible"],
            base["previous_digest"],
            digest,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({**base, "digest": digest}, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.entries.append(operation)
        self.cursor = len(self.entries)
        self._save_cursor()
        return operation

    def undo(self) -> Operation | None:
        if self.cursor == 0 or not self.entries[self.cursor - 1].reversible:
            return None
        self.cursor -= 1
        self._save_cursor()
        return self.entries[self.cursor]

    def redo(self) -> Operation | None:
        if self.cursor >= len(self.entries) or not self.entries[self.cursor].reversible:
            return None
        operation = self.entries[self.cursor]
        self.cursor += 1
        self._save_cursor()
        return operation

    def _load(self, current_revision: int) -> list[Operation]:
        if not self.path.exists():
            return []
        entries: list[Operation] = []
        previous = ""
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
            for line in lines:
                value = json.loads(line)
                if value.get("previous_digest") != previous or value.get("digest") != self._digest({key: value[key] for key in value if key not in {"digest"}}):
                    raise HistoryError("history integrity chain is invalid")
                references = tuple(value.get("references", ()))
                operation = Operation(value["operation_id"], int(value["project_revision"]), value["timestamp"], value["operation_type"], value["parameters"], references, bool(value["reversible"]), value["previous_digest"], value["digest"])
                entries.append(operation)
                previous = operation.digest
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            raise HistoryError("history is corrupt") from error
        if entries and entries[-1].project_revision > current_revision:
            raise HistoryError("history revision is ahead of project metadata")
        return entries

    def _load_cursor(self) -> int:
        try:
            value = json.loads(self.cursor_path.read_text(encoding="utf-8"))
            cursor = value["cursor"]
            if not isinstance(cursor, int) or cursor < 0:
                raise ValueError
            return cursor
        except FileNotFoundError:
            return len(self.entries)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            raise HistoryError("history cursor is corrupt") from error

    def _save_cursor(self) -> None:
        fd, temporary_name = tempfile.mkstemp(prefix=".cursor-", suffix=".tmp", dir=self.cursor_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump({"cursor": self.cursor}, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.cursor_path)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    @staticmethod
    def _digest(value: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @classmethod
    def _validate_value(cls, value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key).lower()
                if any(secret in key_text for secret in ("token", "password", "private_key", "pairing_code")):
                    raise HistoryError("secret-like operation parameter is forbidden")
                cls._validate_value(item)
        elif isinstance(value, list):
            for item in value:
                cls._validate_value(item)
        elif isinstance(value, str) and (Path(value).is_absolute() or "raw/" in value.replace("\\", "/")):
            raise HistoryError("absolute or raw operation reference is forbidden")
