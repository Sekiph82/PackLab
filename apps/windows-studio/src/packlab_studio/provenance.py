"""Derived-artifact provenance and deterministic invalidation."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .project_layout import ProjectLayout


class ArtifactStatus(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    artifact_id: str
    artifact_path: str
    upstream: tuple[str, ...]
    input_digests: dict[str, str]
    parameters: dict[str, Any]
    parameter_digest: str
    project_revision: int
    status: ArtifactStatus


class ProvenanceManager:
    def __init__(self, layout: ProjectLayout) -> None:
        self.layout = layout
        self.path = layout.path("derived", "provenance.json")
        self._records: dict[str, ArtifactRecord] = self._load()

    def register(self, artifact_id: str, artifact_path: str, *, upstream: tuple[str, ...] = (), input_digests: dict[str, str] | None = None, parameters: dict[str, Any] | None = None, project_revision: int) -> ArtifactRecord:
        params = parameters or {}
        record = ArtifactRecord(artifact_id, artifact_path, upstream, dict(input_digests or {}), params, self._digest(params), project_revision, ArtifactStatus.FRESH)
        self._records[artifact_id] = record
        self._save()
        return record

    def get(self, artifact_id: str) -> ArtifactRecord:
        return self._records[artifact_id]

    def records(self) -> tuple[ArtifactRecord, ...]:
        return tuple(self._records.values())

    def invalidate(self, *, changed_inputs: set[str] = set(), changed_parameters: dict[str, Any] | None = None) -> tuple[ArtifactRecord, ...]:
        changed = set(changed_inputs)
        parameter_digest = self._digest(changed_parameters) if changed_parameters is not None else None
        statuses: dict[str, ArtifactStatus] = {}
        for artifact_id, record in self._records.items():
            if any(item in changed for item in record.input_digests) or (parameter_digest is not None and parameter_digest != record.parameter_digest):
                statuses[artifact_id] = ArtifactStatus.STALE
        changed_ids = set(statuses)
        progress = True
        while progress:
            progress = False
            for artifact_id, record in self._records.items():
                if artifact_id not in statuses and any(parent in changed_ids for parent in record.upstream):
                    statuses[artifact_id] = ArtifactStatus.STALE
                    changed_ids.add(artifact_id)
                    progress = True
        self._apply_statuses(statuses)
        return tuple(self._records[item] for item in statuses)

    def refresh_integrity(self) -> tuple[ArtifactRecord, ...]:
        invalid: dict[str, ArtifactStatus] = {}
        for artifact_id, record in self._records.items():
            for relative, expected in record.input_digests.items():
                path = self.layout.path("raw" if relative.replace("\\", "/").startswith("raw/") else "working", relative.split("/", 1)[1] if relative.replace("\\", "/").startswith(("raw/", "working/")) else relative)
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                    invalid[artifact_id] = ArtifactStatus.INVALID
                    break
        self._apply_statuses(invalid)
        return tuple(self._records[item] for item in invalid)

    def _apply_statuses(self, statuses: dict[str, ArtifactStatus]) -> None:
        for artifact_id, status in statuses.items():
            record = self._records[artifact_id]
            self._records[artifact_id] = ArtifactRecord(record.artifact_id, record.artifact_path, record.upstream, record.input_digests, record.parameters, record.parameter_digest, record.project_revision, status)
        if statuses:
            self._save()

    def _load(self) -> dict[str, ArtifactRecord]:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return {item["artifact_id"]: ArtifactRecord(item["artifact_id"], item["artifact_path"], tuple(item["upstream"]), item["input_digests"], item["parameters"], item["parameter_digest"], int(item["project_revision"]), ArtifactStatus(item["status"])) for item in value["artifacts"]}
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError("provenance metadata is corrupt") from error

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        value = {"schema_version": 1, "artifacts": [self._to_dict(record) for record in self._records.values()]}
        fd, temporary_name = tempfile.mkstemp(prefix=".provenance-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.path)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    @staticmethod
    def _to_dict(record: ArtifactRecord) -> dict[str, Any]:
        return {"artifact_id": record.artifact_id, "artifact_path": record.artifact_path, "upstream": list(record.upstream), "input_digests": record.input_digests, "parameters": record.parameters, "parameter_digest": record.parameter_digest, "project_revision": record.project_revision, "status": record.status.value}

    @staticmethod
    def _digest(value: Any) -> str:
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
