"""Append-only project revision metadata and explicit active selection."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .reconstruction import ScaleState

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DEFERRED = "DEFERRED_OWNER_VALIDATION"
MAX_PROJECT_REVISIONS = 10_000
MAX_SERIALIZED_REGISTRY_BYTES = 25_000_000


class ProjectRevisionError(ValueError):
    """Raised for stale, invalid, or unauthorized project revision metadata."""


class ProjectRevisionKind(StrEnum):
    RECONSTRUCTION = "reconstruction"
    OBJECT_GEOMETRY = "object_geometry"
    M10_CLEANUP = "m10_cleanup"
    SCAN_MASTER = "scan_master"


@dataclass(frozen=True, slots=True)
class ImmutableCaptureReference:
    revision_id: str
    artifact_sha256: str
    authority_class: str = "RAW_CAPTURE"
    immutable: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(self.revision_id, str)
            or not self.revision_id
            or self.revision_id.strip() != self.revision_id
        ):
            raise ProjectRevisionError("capture_source_revision_id_invalid")
        if not isinstance(self.artifact_sha256, str) or not _SHA256.fullmatch(self.artifact_sha256):
            raise ProjectRevisionError("capture_source_digest_invalid")
        if self.authority_class != "RAW_CAPTURE" or self.immutable is not True:
            raise ProjectRevisionError("reconstruction_source_must_remain_immutable_raw_capture")

    def as_dict(self) -> dict[str, object]:
        return {
            "revision_id": self.revision_id,
            "artifact_sha256": self.artifact_sha256,
            "authority_class": self.authority_class,
            "immutable": self.immutable,
        }


@dataclass(frozen=True, slots=True)
class ProjectRevisionRecord:
    revision_id: str
    kind: ProjectRevisionKind
    artifact_sha256: str
    parent_revision_ids: tuple[str, ...]
    scale_state: ScaleState
    scale_provenance_id: str | None
    authority_class: str
    generated: bool = False
    physical_accuracy_validation_status: str | None = None
    mold_use_authorized: bool = False
    source_capture_references: tuple[ImmutableCaptureReference, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.revision_id, str)
            or not self.revision_id
            or self.revision_id.strip() != self.revision_id
        ):
            raise ProjectRevisionError("project_revision_id_invalid")
        if not isinstance(self.kind, ProjectRevisionKind):
            raise ProjectRevisionError("project_revision_kind_invalid")
        if not isinstance(self.artifact_sha256, str) or not _SHA256.fullmatch(self.artifact_sha256):
            raise ProjectRevisionError("project_revision_digest_invalid")
        if not isinstance(self.parent_revision_ids, tuple) or any(
            not isinstance(item, str) or not item.strip() for item in self.parent_revision_ids
        ):
            raise ProjectRevisionError("project_revision_parent_ids_invalid")
        if len(set(self.parent_revision_ids)) != len(self.parent_revision_ids):
            raise ProjectRevisionError("project_revision_duplicate_parent")
        if not isinstance(self.scale_state, ScaleState):
            raise ProjectRevisionError("project_revision_scale_state_invalid")
        if self.scale_provenance_id is not None and (
            not isinstance(self.scale_provenance_id, str) or not self.scale_provenance_id.strip()
        ):
            raise ProjectRevisionError("project_revision_scale_provenance_invalid")
        expected_authority = {
            ProjectRevisionKind.RECONSTRUCTION: "RECONSTRUCTION_OBSERVATION",
            ProjectRevisionKind.OBJECT_GEOMETRY: "OBJECT_CAPTURE_GEOMETRY",
            ProjectRevisionKind.M10_CLEANUP: "M10_CLEANUP",
            ProjectRevisionKind.SCAN_MASTER: "SCAN_MASTER",
        }[self.kind]
        if self.authority_class != expected_authority:
            raise ProjectRevisionError("project_revision_authority_class_invalid")
        if self.generated is not False:
            raise ProjectRevisionError("generated_geometry_forbidden_in_captured_revision_chain")
        if not isinstance(self.source_capture_references, tuple) or any(
            not isinstance(item, ImmutableCaptureReference)
            for item in self.source_capture_references
        ):
            raise ProjectRevisionError("source_capture_references_invalid")
        if len({item.revision_id for item in self.source_capture_references}) != len(
            self.source_capture_references
        ):
            raise ProjectRevisionError("duplicate_raw_capture_source_reference")
        if self.kind is ProjectRevisionKind.RECONSTRUCTION:
            if self.parent_revision_ids:
                raise ProjectRevisionError("reconstruction_must_not_rewrite_registered_parent")
            if not self.source_capture_references:
                raise ProjectRevisionError("reconstruction_raw_capture_parent_required")
        elif self.source_capture_references:
            raise ProjectRevisionError("raw_capture_references_only_allowed_on_reconstruction")
        if self.physical_accuracy_validation_status not in (None, _DEFERRED):
            raise ProjectRevisionError("physical_validation_status_must_remain_deferred")
        if self.mold_use_authorized is not False:
            raise ProjectRevisionError("mold_use_must_remain_unauthorized")
        if self.kind is ProjectRevisionKind.SCAN_MASTER and (
            self.scale_state is ScaleState.METRIC_VERIFIED
            or not self.scale_provenance_id
            or self.physical_accuracy_validation_status != _DEFERRED
        ):
            raise ProjectRevisionError("scan_master_scale_and_deferred_authority_required")

    def as_dict(self) -> dict[str, object]:
        return {
            "revision_id": self.revision_id,
            "kind": self.kind.value,
            "artifact_sha256": self.artifact_sha256,
            "parent_revision_ids": list(self.parent_revision_ids),
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "authority_class": self.authority_class,
            "generated": self.generated,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "source_capture_references": [
                item.as_dict() for item in self.source_capture_references
            ],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ProjectRevisionRecord:
        try:
            references = tuple(
                ImmutableCaptureReference(
                    str(item["revision_id"]),
                    str(item["artifact_sha256"]),
                    str(item["authority_class"]),
                    item["immutable"],
                )
                for item in value["source_capture_references"]
            )
            return cls(
                str(value["revision_id"]),
                ProjectRevisionKind(value["kind"]),
                str(value["artifact_sha256"]),
                tuple(value["parent_revision_ids"]),
                ScaleState(value["scale_state"]),
                value["scale_provenance_id"],
                str(value["authority_class"]),
                value["generated"],
                value["physical_accuracy_validation_status"],
                value["mold_use_authorized"],
                references,
            )
        except (KeyError, TypeError, ValueError) as error:
            if isinstance(error, ProjectRevisionError):
                raise
            raise ProjectRevisionError("project_revision_record_malformed") from error


@dataclass(frozen=True, slots=True)
class RevisionSelectionEvent:
    state_revision: int
    kind: ProjectRevisionKind
    previous_revision_id: str | None
    selected_revision_id: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.state_revision, bool)
            or not isinstance(self.state_revision, int)
            or self.state_revision < 1
        ):
            raise ProjectRevisionError("revision_selection_event_state_revision_invalid")
        if not isinstance(self.kind, ProjectRevisionKind):
            raise ProjectRevisionError("revision_selection_event_kind_invalid")
        if self.previous_revision_id is not None and (
            not isinstance(self.previous_revision_id, str) or not self.previous_revision_id.strip()
        ):
            raise ProjectRevisionError("revision_selection_event_previous_id_invalid")
        if not isinstance(self.selected_revision_id, str) or not self.selected_revision_id.strip():
            raise ProjectRevisionError("revision_selection_event_selected_id_invalid")
        if self.previous_revision_id == self.selected_revision_id:
            raise ProjectRevisionError("revision_selection_event_must_change_selection")

    def as_dict(self) -> dict[str, object]:
        return {
            "state_revision": self.state_revision,
            "kind": self.kind.value,
            "previous_revision_id": self.previous_revision_id,
            "selected_revision_id": self.selected_revision_id,
        }


@dataclass(frozen=True, slots=True)
class ProjectRevisionRegistry:
    project_id: str
    state_revision: int = 0
    revisions: tuple[ProjectRevisionRecord, ...] = ()
    active_revision_ids: tuple[tuple[ProjectRevisionKind, str], ...] = ()
    selection_events: tuple[RevisionSelectionEvent, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ProjectRevisionError("project_id_required")
        if (
            isinstance(self.state_revision, bool)
            or not isinstance(self.state_revision, int)
            or self.state_revision < 0
        ):
            raise ProjectRevisionError("registry_state_revision_invalid")
        if not isinstance(self.revisions, tuple) or not isinstance(self.selection_events, tuple):
            raise ProjectRevisionError("registry_history_must_be_immutable_tuples")
        if not isinstance(self.active_revision_ids, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], ProjectRevisionKind)
            or not isinstance(item[1], str)
            for item in self.active_revision_ids
        ):
            raise ProjectRevisionError("active_revision_ids_invalid")
        if len(self.revisions) > MAX_PROJECT_REVISIONS:
            raise ProjectRevisionError("project_revision_history_limit_exceeded")
        if self.state_revision != len(self.revisions) + len(self.selection_events):
            raise ProjectRevisionError("registry_state_revision_history_mismatch")
        by_id: dict[str, ProjectRevisionRecord] = {}
        for record in self.revisions:
            if not isinstance(record, ProjectRevisionRecord):
                raise ProjectRevisionError("project_revision_record_invalid")
            if record.revision_id in by_id:
                raise ProjectRevisionError("duplicate_project_revision_id")
            if record.kind is not ProjectRevisionKind.RECONSTRUCTION:
                if len(record.parent_revision_ids) != 1:
                    raise ProjectRevisionError("revision_kind_requires_one_explicit_parent")
                parent_id = record.parent_revision_ids[0]
                parent = by_id.get(parent_id)
                if parent is None:
                    raise ProjectRevisionError("project_revision_parent_missing_or_not_append_only")
                expected_parents = {
                    ProjectRevisionKind.OBJECT_GEOMETRY: {ProjectRevisionKind.RECONSTRUCTION},
                    ProjectRevisionKind.M10_CLEANUP: {
                        ProjectRevisionKind.OBJECT_GEOMETRY,
                        ProjectRevisionKind.M10_CLEANUP,
                    },
                    ProjectRevisionKind.SCAN_MASTER: {ProjectRevisionKind.M10_CLEANUP},
                }[record.kind]
                if parent.kind not in expected_parents:
                    raise ProjectRevisionError("project_revision_parent_kind_invalid")
                if (
                    record.scale_state is not parent.scale_state
                    or record.scale_provenance_id != parent.scale_provenance_id
                ):
                    raise ProjectRevisionError(
                        "project_revision_scale_provenance_must_be_inherited"
                    )
            by_id[record.revision_id] = record
        active_kinds: set[ProjectRevisionKind] = set()
        for kind, revision_id in self.active_revision_ids:
            if kind in active_kinds:
                raise ProjectRevisionError("duplicate_active_revision_kind")
            active_kinds.add(kind)
            active_record = by_id.get(revision_id)
            if active_record is None:
                raise ProjectRevisionError("active_project_revision_missing")
            if active_record.kind is not kind:
                raise ProjectRevisionError("active_project_revision_kind_mismatch")
        replayed_active: dict[ProjectRevisionKind, str] = {}
        previous_event_state_revision = 0
        for event_index, event in enumerate(self.selection_events):
            if not isinstance(event, RevisionSelectionEvent):
                raise ProjectRevisionError("revision_selection_event_invalid")
            selected_record = by_id.get(event.selected_revision_id)
            if selected_record is None or selected_record.kind is not event.kind:
                raise ProjectRevisionError("revision_selection_event_target_invalid")
            if (
                event.state_revision <= previous_event_state_revision
                or event.state_revision <= event_index
                or event.state_revision > self.state_revision
            ):
                raise ProjectRevisionError("revision_selection_event_order_invalid")
            if event.previous_revision_id != replayed_active.get(event.kind):
                raise ProjectRevisionError("revision_selection_event_history_disconnected")
            replayed_active[event.kind] = event.selected_revision_id
            previous_event_state_revision = event.state_revision
        if replayed_active != dict(self.active_revision_ids):
            raise ProjectRevisionError("active_revision_pointer_history_mismatch")

    @classmethod
    def create(cls, project_id: str) -> ProjectRevisionRegistry:
        return cls(project_id)

    def get_revision(self, revision_id: str) -> ProjectRevisionRecord:
        for record in self.revisions:
            if record.revision_id == revision_id:
                return record
        raise ProjectRevisionError("project_revision_missing")

    def active_revision(self, kind: ProjectRevisionKind) -> ProjectRevisionRecord | None:
        selected_id = dict(self.active_revision_ids).get(kind)
        return None if selected_id is None else self.get_revision(selected_id)

    def append_revision(
        self,
        record: ProjectRevisionRecord,
        *,
        expected_state_revision: int,
    ) -> ProjectRevisionRegistry:
        self._check_expected_revision(expected_state_revision)
        if len(self.revisions) >= MAX_PROJECT_REVISIONS:
            raise ProjectRevisionError("project_revision_history_limit_exceeded")
        if any(existing.revision_id == record.revision_id for existing in self.revisions):
            raise ProjectRevisionError("duplicate_project_revision_id")
        return ProjectRevisionRegistry(
            self.project_id,
            self.state_revision + 1,
            (*self.revisions, record),
            self.active_revision_ids,
            self.selection_events,
        )

    def select_active(
        self,
        kind: ProjectRevisionKind,
        revision_id: str,
        *,
        expected_state_revision: int,
    ) -> ProjectRevisionRegistry:
        self._check_expected_revision(expected_state_revision)
        record = self.get_revision(revision_id)
        if record.kind is not kind:
            raise ProjectRevisionError("selected_project_revision_kind_mismatch")
        current = dict(self.active_revision_ids)
        previous = current.get(kind)
        if previous == revision_id:
            return self
        current[kind] = revision_id
        new_state_revision = self.state_revision + 1
        event = RevisionSelectionEvent(new_state_revision, kind, previous, revision_id)
        return ProjectRevisionRegistry(
            self.project_id,
            new_state_revision,
            self.revisions,
            tuple(sorted(current.items(), key=lambda item: item[0].value)),
            (*self.selection_events, event),
        )

    def serialize(self) -> bytes:
        body = self._body_dict()
        content_sha256 = hashlib.sha256(_canonical_json(body)).hexdigest()
        return _canonical_json({"body": body, "content_sha256": content_sha256})

    @classmethod
    def deserialize(cls, payload: bytes | str) -> ProjectRevisionRegistry:
        raw = payload.encode("utf-8") if isinstance(payload, str) else payload
        if not isinstance(raw, bytes) or len(raw) > MAX_SERIALIZED_REGISTRY_BYTES:
            raise ProjectRevisionError("serialized_registry_size_invalid")
        try:
            envelope = json.loads(raw, object_pairs_hook=_unique_object)
            body = envelope["body"]
            digest = envelope["content_sha256"]
            if not isinstance(body, dict) or not isinstance(digest, str):
                raise ProjectRevisionError("serialized_registry_envelope_invalid")
            if hashlib.sha256(_canonical_json(body)).hexdigest() != digest:
                raise ProjectRevisionError("serialized_registry_digest_mismatch")
            if body.get("contract") != "packlab.project-revision-registry.v1":
                raise ProjectRevisionError("serialized_registry_contract_invalid")
            revisions = tuple(ProjectRevisionRecord.from_dict(item) for item in body["revisions"])
            events = tuple(
                RevisionSelectionEvent(
                    item["state_revision"],
                    ProjectRevisionKind(item["kind"]),
                    item["previous_revision_id"],
                    item["selected_revision_id"],
                )
                for item in body["selection_events"]
            )
            active = tuple(
                (ProjectRevisionKind(item[0]), item[1]) for item in body["active_revision_ids"]
            )
            return cls(body["project_id"], body["state_revision"], revisions, active, events)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            if isinstance(error, ProjectRevisionError):
                raise
            raise ProjectRevisionError("serialized_registry_malformed") from error

    def _body_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.project-revision-registry.v1",
            "project_id": self.project_id,
            "state_revision": self.state_revision,
            "revisions": [record.as_dict() for record in self.revisions],
            "active_revision_ids": [
                [kind.value, revision_id] for kind, revision_id in self.active_revision_ids
            ],
            "selection_events": [event.as_dict() for event in self.selection_events],
        }

    def _check_expected_revision(self, expected_state_revision: int) -> None:
        if (
            isinstance(expected_state_revision, bool)
            or not isinstance(expected_state_revision, int)
            or expected_state_revision != self.state_revision
        ):
            raise ProjectRevisionError("project_revision_concurrency_conflict")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectRevisionError("serialized_registry_duplicate_json_key")
        result[key] = value
    return result


__all__ = [
    "ImmutableCaptureReference",
    "ProjectRevisionError",
    "ProjectRevisionKind",
    "ProjectRevisionRecord",
    "ProjectRevisionRegistry",
    "RevisionSelectionEvent",
]
