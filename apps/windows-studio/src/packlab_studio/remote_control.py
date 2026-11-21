"""PL-0429 remote capture control: Studio queues one-shot commands for a paired phone.

The phone always initiates: while a scan is active and its operator allowed it, it
long-polls ``GET /v1/control/next`` and posts its status to ``POST /v1/control/status``
over the existing pinned TLS channel with its device session token. Studio never
connects to the phone. A command is only a request to tap Manual Capture (or
Finalize); the phone applies every production gate and reports the outcome. Nothing
here carries measurement, scale or Scan Master authority.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import unicodedata
import uuid
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from packlab_core.transfer_protocol import TransferProtocolError

ACTIONS = ("capture", "finish")
OUTCOMES = ("captured", "refused", "finished", "failed")
COMMAND_TTL_SECONDS = 10.0
POLL_TIMEOUT_SECONDS = 25.0
#: A phone counts as connected while it polled within this window (poll <= 25 s).
CONNECTED_WITHIN_SECONDS = 40.0
MAX_STATUS_BYTES = 4096
#: Waiting long-polls across all devices (each holds a receiver thread up to 25 s).
MAX_ACTIVE_POLLS = 16
#: remote-control-log.jsonl rotates to .jsonl.1 at this size.
MAX_LOG_BYTES = 1024 * 1024
_REASON = re.compile(r"^[a-z0-9_]{1,64}$")
_COMMAND_ID = re.compile(r"^[0-9a-f]{32}$")
_STATUS_KEYS = {
    "scan_active",
    "control_enabled",
    "scan_name",
    "coverage_captured",
    "coverage_total",
    "instruction",
    "last_result",
}
_RESULT_KEYS = {"command_id", "action", "outcome", "reasons", "message"}


class RemoteControlError(TransferProtocolError):
    pass


@dataclass(frozen=True, slots=True)
class RemoteCommand:
    command_id: str
    device_id: str
    action: str
    issued_at: float
    expires_at: float

    def wire(self, now: float) -> dict[str, object]:
        return {
            "message": "remote_command",
            "command_id": self.command_id,
            "action": self.action,
            "expires_in_ms": max(0, int((self.expires_at - now) * 1000)),
        }


@dataclass(frozen=True, slots=True)
class CommandResult:
    command_id: str
    action: str
    outcome: str
    reasons: tuple[str, ...]
    message: str


@dataclass(frozen=True, slots=True)
class DeviceControlStatus:
    scan_active: bool
    control_enabled: bool
    scan_name: str
    coverage_captured: int
    coverage_total: int
    instruction: str
    last_result: CommandResult | None
    received_at: float = field(compare=False)


def _text(value: object, name: str, limit: int) -> str:
    if not isinstance(value, str) or len(value) > limit:
        raise RemoteControlError("bad_request", f"{name} must be a string of at most {limit}")
    # Phone-supplied text: drop control/format characters before Studio shows it.
    return "".join(ch for ch in value if unicodedata.category(ch)[0] != "C").strip()


def _int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1000:
        raise RemoteControlError("bad_request", f"{name} must be an integer 0..1000")
    return value


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise RemoteControlError("bad_request", f"{name} must be a boolean")
    return value


def parse_status(value: dict[str, object], *, received_at: float) -> DeviceControlStatus:
    """Strict, bounded parse of a phone status report (unknown keys refused)."""
    if set(value) - _STATUS_KEYS or not {"scan_active", "control_enabled"} <= set(value):
        raise RemoteControlError("bad_request", "status keys are not recognised")
    result = value.get("last_result")
    parsed: CommandResult | None = None
    if result is not None:
        if not isinstance(result, dict) or set(result) != _RESULT_KEYS:
            raise RemoteControlError("bad_request", "last_result keys are not recognised")
        reasons = result["reasons"]
        if (
            not isinstance(result["command_id"], str)
            or not _COMMAND_ID.fullmatch(result["command_id"])
            or result["action"] not in ACTIONS
            or result["outcome"] not in OUTCOMES
            or not isinstance(reasons, list)
            or len(reasons) > 8
            or any(not isinstance(r, str) or not _REASON.fullmatch(r) for r in reasons)
        ):
            raise RemoteControlError("bad_request", "last_result is malformed")
        parsed = CommandResult(
            result["command_id"],
            str(result["action"]),
            str(result["outcome"]),
            tuple(reasons),
            _text(result["message"], "message", 256),
        )
    return DeviceControlStatus(
        scan_active=_bool(value["scan_active"], "scan_active"),
        control_enabled=_bool(value["control_enabled"], "control_enabled"),
        scan_name=_text(value.get("scan_name", ""), "scan_name", 128),
        coverage_captured=_int(value.get("coverage_captured", 0), "coverage_captured"),
        coverage_total=_int(value.get("coverage_total", 0), "coverage_total"),
        instruction=_text(value.get("instruction", ""), "instruction", 256),
        last_result=parsed,
        received_at=received_at,
    )


class RemoteControlHub:
    """Thread-safe per-device command slot, status and audit log (no secrets stored)."""

    def __init__(
        self,
        *,
        is_active: Callable[[str], bool],
        log_path: str | Path | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._is_active = is_active
        self._log_path = Path(log_path) if log_path is not None else None
        self._clock = clock
        self._cond = threading.Condition()
        self._pending: dict[str, RemoteCommand] = {}
        # Delivered commands awaiting (or holding) their result; bounded.
        self._delivered: OrderedDict[str, tuple[RemoteCommand, CommandResult | None]] = (
            OrderedDict()
        )
        self._status: dict[str, DeviceControlStatus] = {}
        self._last_poll: dict[str, float] = {}
        self._closed = False
        # Long-polls: the newest poll per device wins; all devices share a small cap.
        self._poll_generation: dict[str, int] = {}
        self._active_polls = 0
        self.log: deque[dict[str, object]] = deque(maxlen=256)
        self._unwritten: list[dict[str, object]] = []
        self._file_lock = threading.Lock()

    def _record(self, event: str, device_id: str, **fields: object) -> None:
        """Called under the hub lock; the file write happens later in ``_flush``."""
        entry: dict[str, object] = {"at": time.time(), "event": event, "device_id": device_id}
        entry.update(fields)
        self.log.append(entry)
        if self._log_path is not None:
            self._unwritten.append(entry)

    def _flush(self) -> None:
        """Append recorded entries outside the hub lock, rotating at MAX_LOG_BYTES."""
        if self._log_path is None:
            return
        with self._cond:
            entries, self._unwritten = self._unwritten, []
        if not entries:
            return
        with self._file_lock:
            path = self._log_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.stat().st_size >= MAX_LOG_BYTES:
                # ponytail: one rotated file; bounded at about 2 x MAX_LOG_BYTES on disk.
                os.replace(path, path.with_name(path.name + ".1"))
            with path.open("a", encoding="utf-8") as handle:
                handle.writelines(json.dumps(entry, sort_keys=True) + "\n" for entry in entries)

    def connected(self, device_id: str) -> bool:
        with self._cond:
            seen = self._last_poll.get(device_id)
            return seen is not None and self._clock() - seen < CONNECTED_WITHIN_SECONDS

    def status(self, device_id: str) -> DeviceControlStatus | None:
        with self._cond:
            return self._status.get(device_id)

    def issue(self, device_id: str, action: str) -> RemoteCommand:
        try:
            return self._issue(device_id, action)
        finally:
            self._flush()

    def next_command(
        self, device_id: str, timeout: float = POLL_TIMEOUT_SECONDS
    ) -> dict[str, object] | None:
        """Long-poll: the next unexpired command for this device (consumed once), or None.

        A newer poll from the same device ends this one with None (204); at most
        MAX_ACTIVE_POLLS polls wait at once across all devices (``too_many_polls``).
        """
        try:
            return self._next_command(device_id, timeout)
        finally:
            self._flush()

    def report(self, device_id: str, value: dict[str, object]) -> DeviceControlStatus:
        try:
            return self._report(device_id, value)
        finally:
            self._flush()

    def _issue(self, device_id: str, action: str) -> RemoteCommand:
        if action not in ACTIONS:
            raise RemoteControlError("bad_request", "unknown remote action")
        with self._cond:
            now = self._clock()
            if not self._is_active(device_id):
                raise RemoteControlError("device_revoked", "device is not paired")
            seen = self._last_poll.get(device_id)
            if seen is None or now - seen >= CONNECTED_WITHIN_SECONDS:
                raise RemoteControlError("device_not_connected", "the phone is not polling")
            pending = self._pending.get(device_id)
            if pending is not None and pending.expires_at > now:
                # One at a time: a double click must not become two captures.
                raise RemoteControlError("command_pending", "a command is still waiting")
            command = RemoteCommand(
                uuid.uuid4().hex, device_id, action, now, now + COMMAND_TTL_SECONDS
            )
            self._pending[device_id] = command
            self._record("issued", device_id, command_id=command.command_id, action=action)
            self._cond.notify_all()
            return command

    def _next_command(self, device_id: str, timeout: float) -> dict[str, object] | None:
        with self._cond:
            if self._active_polls >= MAX_ACTIVE_POLLS:
                raise RemoteControlError("too_many_polls", "too many phones are waiting")
            generation = self._poll_generation.get(device_id, 0) + 1
            self._poll_generation[device_id] = generation
            self._cond.notify_all()  # supersede this device's older poll
            self._active_polls += 1
            try:
                return self._wait_for_command(device_id, timeout, generation)
            finally:
                self._active_polls -= 1

    def _wait_for_command(
        self, device_id: str, timeout: float, generation: int
    ) -> dict[str, object] | None:
        deadline = self._clock() + timeout
        self._last_poll[device_id] = self._clock()
        while True:
            now = self._clock()
            if not self._is_active(device_id):
                self._pending.pop(device_id, None)
                raise RemoteControlError("device_revoked", "device is not paired")
            if self._closed or self._poll_generation.get(device_id) != generation:
                return None
            command = self._pending.pop(device_id, None)
            if command is not None and command.expires_at <= now:
                self._record("expired", device_id, command_id=command.command_id)
                command = None
            if command is not None:
                self._delivered[command.command_id] = (command, None)
                while len(self._delivered) > 256:
                    self._delivered.popitem(last=False)
                self._record("delivered", device_id, command_id=command.command_id)
                self._last_poll[device_id] = now
                return command.wire(now)
            if now >= deadline:
                self._last_poll[device_id] = now
                return None
            pending = self._pending.get(device_id)
            wake = deadline if pending is None else min(deadline, pending.expires_at)
            self._cond.wait(max(0.01, wake - now))

    def _report(self, device_id: str, value: dict[str, object]) -> DeviceControlStatus:
        with self._cond:
            status = parse_status(value, received_at=self._clock())
            result = status.last_result
            if result is not None:
                known = self._delivered.get(result.command_id)
                if known is None or known[0].device_id != device_id:
                    self._record("rejected_result", device_id, command_id=result.command_id)
                    raise RemoteControlError("unknown_command", "result for an unknown command")
                if known[0].action != result.action:
                    raise RemoteControlError("bad_request", "result action does not match")
                if known[1] is None:  # first report of this result; repeats are not re-logged
                    self._delivered[result.command_id] = (known[0], result)
                    self._record(
                        "result",
                        device_id,
                        command_id=result.command_id,
                        action=result.action,
                        outcome=result.outcome,
                        reasons=list(result.reasons),
                    )
            self._status[device_id] = status
            return status

    def forget(self, device_id: str) -> None:
        """Revoke kills control: drop queued commands and status, wake its poller."""
        with self._cond:
            self._pending.pop(device_id, None)
            self._status.pop(device_id, None)
            self._last_poll.pop(device_id, None)
            self._cond.notify_all()

    def close(self) -> None:
        with self._cond:
            self._closed = True
            self._cond.notify_all()

    def reopen(self) -> None:
        with self._cond:
            self._closed = False
