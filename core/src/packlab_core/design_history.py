"""Immutable command-based history for Design Model parameter/feature edits."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from .design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    revise_design_model_revision,
)

MAX_HISTORY_ENTRIES = 256
_COMMAND_PREFIX = "design-edit-command:"


class DesignHistoryError(ValueError):
    """Raised when an edit command is stale, inconsistent or exceeds history bounds."""


class EditTargetKind(StrEnum):
    PARAMETER = "parameter"
    FEATURE = "feature"


@dataclass(frozen=True, slots=True)
class DesignEditCommand:
    command_id: str
    expected_model_revision_id: str
    target_kind: EditTargetKind
    target_id: str
    before: DesignModelParameter | DesignModelFeatureReference | None
    after: DesignModelParameter | DesignModelFeatureReference | None

    def __post_init__(self) -> None:
        if not isinstance(self.target_kind, EditTargetKind):
            raise DesignHistoryError("edit_target_kind_invalid")
        if not self.expected_model_revision_id or not self.target_id:
            raise DesignHistoryError("edit_command_identity_invalid")
        if self.before is None and self.after is None:
            raise DesignHistoryError("edit_command_has_no_change")
        expected_type = (
            DesignModelParameter
            if self.target_kind is EditTargetKind.PARAMETER
            else DesignModelFeatureReference
        )
        if any(
            value is not None and not isinstance(value, expected_type)
            for value in (self.before, self.after)
        ):
            raise DesignHistoryError("edit_command_value_type_mismatch")
        if self.before is not None and _node_id(self.before) != self.target_id:
            raise DesignHistoryError("edit_command_before_target_mismatch")
        if self.before == self.after:
            raise DesignHistoryError("edit_command_noop")
        if self.command_id != _command_id(
            self.expected_model_revision_id,
            self.target_kind,
            self.target_id,
            self.before,
            self.after,
        ):
            raise DesignHistoryError("edit_command_id_mismatch")


def create_edit_command(
    expected_model_revision_id: str,
    target_kind: EditTargetKind,
    target_id: str,
    before: DesignModelParameter | DesignModelFeatureReference | None,
    after: DesignModelParameter | DesignModelFeatureReference | None,
) -> DesignEditCommand:
    command_id = _command_id(expected_model_revision_id, target_kind, target_id, before, after)
    return DesignEditCommand(
        command_id,
        expected_model_revision_id,
        target_kind,
        target_id,
        before,
        after,
    )


@dataclass(frozen=True, slots=True)
class DesignModelHistory:
    """Functional bounded history; every transition returns a new history value."""

    current_revision: DesignModelRevision
    undo_commands: tuple[DesignEditCommand, ...] = ()
    redo_commands: tuple[DesignEditCommand, ...] = ()
    max_entries: int = 128

    def __post_init__(self) -> None:
        if not isinstance(self.current_revision, DesignModelRevision):
            raise DesignHistoryError("design_model_revision_required")
        if not isinstance(self.undo_commands, tuple) or not isinstance(self.redo_commands, tuple):
            raise DesignHistoryError("history_commands_must_be_immutable_tuples")
        if any(
            not isinstance(command, DesignEditCommand)
            for command in (*self.undo_commands, *self.redo_commands)
        ):
            raise DesignHistoryError("history_command_invalid")
        if isinstance(self.max_entries, bool) or not isinstance(self.max_entries, int):
            raise DesignHistoryError("history_limit_invalid")
        if not 1 <= self.max_entries <= MAX_HISTORY_ENTRIES:
            raise DesignHistoryError("history_limit_out_of_range")
        if len(self.undo_commands) > self.max_entries or len(self.redo_commands) > self.max_entries:
            raise DesignHistoryError("history_entry_limit_exceeded")

    @property
    def can_undo(self) -> bool:
        return bool(self.undo_commands)

    @property
    def can_redo(self) -> bool:
        return bool(self.redo_commands)

    def apply(
        self,
        command: DesignEditCommand,
        *,
        actor_id: str,
        reason: str,
        created_at_utc: str,
    ) -> DesignModelHistory:
        if not isinstance(command, DesignEditCommand):
            raise DesignHistoryError("edit_command_required")
        updated = _apply_command(
            self.current_revision,
            command,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
        return DesignModelHistory(
            updated,
            (*self.undo_commands, command)[-self.max_entries :],
            (),
            self.max_entries,
        )

    def undo(self, *, actor_id: str, created_at_utc: str) -> DesignModelHistory:
        if not self.undo_commands:
            raise DesignHistoryError("undo_history_empty")
        command = self.undo_commands[-1]
        inverse = create_edit_command(
            self.current_revision.revision_id,
            command.target_kind,
            _node_id(command.after) if command.after is not None else command.target_id,
            command.after,
            command.before,
        )
        updated = _apply_command(
            self.current_revision,
            inverse,
            actor_id=actor_id,
            reason=f"Undo {command.command_id}",
            created_at_utc=created_at_utc,
        )
        return DesignModelHistory(
            updated,
            self.undo_commands[:-1],
            (*self.redo_commands, command)[-self.max_entries :],
            self.max_entries,
        )

    def redo(self, *, actor_id: str, created_at_utc: str) -> DesignModelHistory:
        if not self.redo_commands:
            raise DesignHistoryError("redo_history_empty")
        original = self.redo_commands[-1]
        replay = create_edit_command(
            self.current_revision.revision_id,
            original.target_kind,
            original.target_id,
            original.before,
            original.after,
        )
        updated = _apply_command(
            self.current_revision,
            replay,
            actor_id=actor_id,
            reason=f"Redo {original.command_id}",
            created_at_utc=created_at_utc,
        )
        return DesignModelHistory(
            updated,
            (*self.undo_commands, replay)[-self.max_entries :],
            self.redo_commands[:-1],
            self.max_entries,
        )


def _apply_command(
    revision: DesignModelRevision,
    command: DesignEditCommand,
    *,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelRevision:
    if command.expected_model_revision_id != revision.revision_id:
        raise DesignHistoryError("edit_command_expected_revision_stale")
    is_parameter = command.target_kind is EditTargetKind.PARAMETER
    nodes = revision.parameters if is_parameter else revision.features
    matching = tuple(node for node in nodes if _node_id(node) == command.target_id)
    if command.before is None:
        if matching:
            raise DesignHistoryError("edit_command_target_already_exists")
    elif len(matching) != 1 or matching[0] != command.before:
        raise DesignHistoryError("edit_command_target_missing_or_changed")
    if command.after is not None:
        after_id = _node_id(command.after)
        if after_id != command.target_id and any(_node_id(node) == after_id for node in nodes):
            raise DesignHistoryError("edit_command_after_target_already_exists")
    updated_nodes = tuple(node for node in nodes if _node_id(node) != command.target_id)
    if command.after is not None:
        updated_nodes = (*updated_nodes, command.after)
    try:
        return revise_design_model_revision(
            revision,
            parameters=updated_nodes if is_parameter else revision.parameters,  # type: ignore[arg-type]
            features=revision.features if is_parameter else updated_nodes,  # type: ignore[arg-type]
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise DesignHistoryError("edit_command_revision_invalid") from error


def _node_id(node: DesignModelParameter | DesignModelFeatureReference | None) -> str:
    if isinstance(node, DesignModelParameter):
        return node.parameter_id
    if isinstance(node, DesignModelFeatureReference):
        return node.feature_id
    raise DesignHistoryError("edit_command_node_required")


def _node_dict(node: DesignModelParameter | DesignModelFeatureReference | None) -> object:
    return node.as_dict() if node is not None else None


def _command_id(
    expected_revision_id: str,
    target_kind: EditTargetKind,
    target_id: str,
    before: DesignModelParameter | DesignModelFeatureReference | None,
    after: DesignModelParameter | DesignModelFeatureReference | None,
) -> str:
    payload = {
        "contract": "packlab.design-edit-command.v1",
        "expected_model_revision_id": expected_revision_id,
        "target_kind": target_kind.value,
        "target_id": target_id,
        "before": _node_dict(before),
        "after": _node_dict(after),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return _COMMAND_PREFIX + digest


__all__ = [
    "MAX_HISTORY_ENTRIES",
    "DesignEditCommand",
    "DesignHistoryError",
    "DesignModelHistory",
    "EditTargetKind",
    "create_edit_command",
]
