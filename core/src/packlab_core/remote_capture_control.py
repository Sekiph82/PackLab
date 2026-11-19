"""PL-0429 remote iPhone capture control contract (software half, default off).

Windows Studio (controller) sends MAC-authenticated capture-control commands to
a paired iPhone capture endpoint on a trusted LAN. Command/response keys are
derived from the existing short-lived PackLab Transfer session credential
(``pairing.py`` / ``transfer_security.py``); no new pairing, key exchange or
cipher is introduced. TLS with the existing certificate pin is still required
on the real transport; the MAC layer adds per-command integrity, ordering and
replay protection on top of it.

Acknowledgements are capture-control receipts only. They carry no measurement,
scale or Scan Master authority; the ``.packscan`` evidence path is unchanged.

The trusted-LAN assumption is NOT validated here: :func:`require_lan_peer` only
rejects peer literals outside loopback/private/link-local ranges. Physical
iPhone 16, LAN and TLS-on-device acceptance remain open; see
``docs/development/PL-0429_REMOTE_CAPTURE_PROTOCOL.md``.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .transfer_protocol import TransferErrorCode, TransferProtocolError, canonical_json
from .transfer_security import PairingAuthenticator, SessionCredential

COMMAND_SCHEMA = "packlab.remote-capture-command.v1"
RESPONSE_SCHEMA = "packlab.remote-capture-response.v1"
MAX_COMMAND_BYTES = 8192
MAX_RESPONSE_BYTES = 8192
MAX_PLAN_STEPS = 64
MAX_SEQ = 2**31 - 1
TIMESTAMP_WINDOW_MS = 30_000
NONCE_MEMORY = 256
REJECTION_MEMORY = 256
MAX_PENDING = 64
DEFAULT_MAX_COMMANDS_PER_SECOND = 10
CAPTURE_MODES = frozenset({"freehand", "guided_orbit", "turntable"})  # Swift CaptureModeID
FRAME_METADATA_STATUS = "placeholder_not_measured"

_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
_HEX32_RE = re.compile(r"^[0-9a-f]{32}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_ARG_KEYS: dict[str, frozenset[str]] = {
    "start_session": frozenset({"capture_mode"}),
    "set_capture_plan": frozenset({"steps"}),
    "capture_frame": frozenset(),
    "pause": frozenset(),
    "resume": frozenset(),
    "end_session": frozenset(),
    "query_status": frozenset(),
}
COMMANDS = frozenset(_ARG_KEYS)
_COMMAND_KEYS = frozenset(
    {"schema", "command", "session_id", "controller_id", "device_id", "seq", "nonce"}
    | {"issued_at_ms", "args", "mac"}
)
_RESPONSE_KEYS = frozenset(
    {"schema", "session_id", "controller_id", "device_id", "in_reply_to_seq"}
    | {"in_reply_to_nonce", "command", "status", "state", "error_code", "result"}
    | {"issued_at_ms", "mac"}
)
_UNSIGNED_REJECTION_KEYS = frozenset({"schema", "status", "error_code"})
_STATUS_KEYS = frozenset(
    {"state", "capture_mode", "frames_captured", "plan_steps_total", "plan_steps_remaining"}
    | {"last_accepted_seq"}
)
_FRAME_KEYS = frozenset(
    {"frame_index", "plan_step", "ring_id", "planned_turntable_angle_mdeg"}
    | {"device_capture_timestamp_ms", "capture_metadata_status"}
    | {"measurement_authority", "scan_master_authority"}
)
_ALLOWED_PEER_NETWORKS = tuple(
    ipaddress.ip_network(cidr)
    for cidr in (
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
)


class RemoteCaptureErrorCode(StrEnum):
    FEATURE_DISABLED = "feature_disabled"
    NON_LAN_PEER = "non_lan_peer"
    OVERSIZED = "oversized"
    MALFORMED = "malformed"
    NON_CANONICAL = "non_canonical"
    UNKNOWN_COMMAND = "unknown_command"
    BAD_ARGS = "bad_args"
    UNAUTHENTICATED = "unauthenticated"
    UNPAIRED_SESSION = "unpaired_session"
    UNKNOWN_SESSION = "unknown_session"
    IDENTITY_MISMATCH = "identity_mismatch"
    BAD_MAC = "bad_mac"
    SESSION_EXPIRED = "session_expired"
    STALE_COMMAND = "stale_command"
    REPLAYED_COMMAND = "replayed_command"
    RATE_LIMITED = "rate_limited"
    ILLEGAL_TRANSITION = "illegal_transition"
    CAPTURE_PLAN_COMPLETE = "capture_plan_complete"
    UNEXPECTED_RESPONSE = "unexpected_response"
    AUTHORITY_UPGRADE = "authority_upgrade"
    DEVICE_REJECTED_UNAUTHENTICATED = "device_rejected_unauthenticated"


# Fixed messages: errors never echo input, tokens, keys or MACs.
_MESSAGES = {
    RemoteCaptureErrorCode.FEATURE_DISABLED: "remote capture control is disabled",
    RemoteCaptureErrorCode.NON_LAN_PEER: "peer address is not loopback/private LAN",
    RemoteCaptureErrorCode.OVERSIZED: "message exceeds the size bound",
    RemoteCaptureErrorCode.MALFORMED: "message does not match the schema",
    RemoteCaptureErrorCode.NON_CANONICAL: "message is not canonical JSON",
    RemoteCaptureErrorCode.UNKNOWN_COMMAND: "command is not in the allow-list",
    RemoteCaptureErrorCode.BAD_ARGS: "command arguments are invalid",
    RemoteCaptureErrorCode.UNAUTHENTICATED: "command is not from the paired controller",
    RemoteCaptureErrorCode.UNPAIRED_SESSION: "no paired session is active",
    RemoteCaptureErrorCode.UNKNOWN_SESSION: "session does not match the paired session",
    RemoteCaptureErrorCode.IDENTITY_MISMATCH: "controller or device identity does not match",
    RemoteCaptureErrorCode.BAD_MAC: "message authentication failed",
    RemoteCaptureErrorCode.SESSION_EXPIRED: "paired session has expired",
    RemoteCaptureErrorCode.STALE_COMMAND: "command timestamp is outside the window",
    RemoteCaptureErrorCode.REPLAYED_COMMAND: "command sequence or nonce was already used",
    RemoteCaptureErrorCode.RATE_LIMITED: "command rate limit exceeded",
    RemoteCaptureErrorCode.ILLEGAL_TRANSITION: "command is not legal in the device state",
    RemoteCaptureErrorCode.CAPTURE_PLAN_COMPLETE: "every planned capture step was captured",
    RemoteCaptureErrorCode.UNEXPECTED_RESPONSE: "response does not match a pending command",
    RemoteCaptureErrorCode.AUTHORITY_UPGRADE: "capture acknowledgement claimed authority",
    RemoteCaptureErrorCode.DEVICE_REJECTED_UNAUTHENTICATED: "device rejected the command",
}


class RemoteCaptureError(ValueError):
    def __init__(
        self,
        code: RemoteCaptureErrorCode,
        *,
        device_code: RemoteCaptureErrorCode | None = None,
        detail: RemoteCaptureErrorCode | None = None,
    ) -> None:
        self.code = code
        self.device_code = device_code
        self.detail = detail  # local-only diagnosis; never sent on the wire
        suffix = f" ({device_code.value})" if device_code else ""
        super().__init__(f"{code.value}: {_MESSAGES[code]}{suffix}")


class DeviceState(StrEnum):
    IDLE = "IDLE"
    SESSION_OPEN = "SESSION_OPEN"
    CAPTURING = "CAPTURING"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


_S = DeviceState
_TRANSITIONS: dict[str, dict[DeviceState, DeviceState]] = {
    "start_session": {_S.IDLE: _S.SESSION_OPEN},
    "set_capture_plan": {_S.SESSION_OPEN: _S.SESSION_OPEN, _S.PAUSED: _S.PAUSED},
    "capture_frame": {_S.SESSION_OPEN: _S.CAPTURING, _S.CAPTURING: _S.CAPTURING},
    "pause": {_S.CAPTURING: _S.PAUSED},
    "resume": {_S.PAUSED: _S.CAPTURING},
    "end_session": {_S.SESSION_OPEN: _S.CLOSED, _S.CAPTURING: _S.CLOSED, _S.PAUSED: _S.CLOSED},
    "query_status": {state: state for state in DeviceState},
}


def require_lan_peer(address: str) -> None:
    """Reject peer literals outside loopback/RFC1918/ULA/link-local ranges.

    Hostnames are rejected (no DNS). This is a coarse address policy only; it
    does not prove the LAN is trusted.
    """

    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        raise RemoteCaptureError(RemoteCaptureErrorCode.NON_LAN_PEER) from None
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if not any(ip in network for network in _ALLOWED_PEER_NETWORKS):
        raise RemoteCaptureError(RemoteCaptureErrorCode.NON_LAN_PEER)


def _malformed(*_: object) -> Any:
    raise ValueError("non-integer number or duplicate key")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value = dict(pairs)
    if len(value) != len(pairs):
        _malformed()
    return value


def _strict_loads(raw: bytes, limit: int) -> dict[str, Any]:
    if not isinstance(raw, bytes) or len(raw) > limit:
        raise RemoteCaptureError(RemoteCaptureErrorCode.OVERSIZED)
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_float=_malformed,
            parse_constant=_malformed,
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED) from None
    if not isinstance(value, dict):
        raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED)
    try:
        canonical = canonical_json(value)
    except ValueError:  # includes UnicodeEncodeError from lone surrogates
        raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED) from None
    if canonical != raw:
        raise RemoteCaptureError(RemoteCaptureErrorCode.NON_CANONICAL)
    return value


def _is_int(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def _is_str(value: object, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _is_capture_mode(value: object) -> bool:
    return isinstance(value, str) and value in CAPTURE_MODES


def _is_optional_int(value: object, low: int, high: int) -> bool:
    return value is None or _is_int(value, low, high)


def _validate_args(command: object, args: object) -> dict[str, Any]:
    if not isinstance(command, str) or command not in _ARG_KEYS:
        raise RemoteCaptureError(RemoteCaptureErrorCode.UNKNOWN_COMMAND)
    bad = RemoteCaptureError(RemoteCaptureErrorCode.BAD_ARGS)
    if not isinstance(args, dict) or set(args) != _ARG_KEYS[command]:
        raise bad
    if command == "start_session" and not _is_capture_mode(args["capture_mode"]):
        raise bad
    if command == "set_capture_plan":
        steps = args["steps"]
        if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_PLAN_STEPS:
            raise bad
        for step in steps:
            if (
                not isinstance(step, dict)
                or set(step) != {"ring_id", "turntable_angle_mdeg"}
                or not _is_str(step["ring_id"], _ID_RE)
                or not _is_int(step["turntable_angle_mdeg"], 0, 359_999)
            ):
                raise bad
    return args


class _SessionKeys:
    """Per-direction HMAC keys derived from the pinned transfer session token.

    Not serialisable and redacted from ``repr``; the token itself is not kept.
    """

    __slots__ = ("session_id", "controller_id", "device_id", "expires_at", "_keys")

    def __init__(self, credential: SessionCredential, device_id: str) -> None:
        if not _is_str(device_id, _ID_RE) or not _is_str(credential.receiver_instance_id, _ID_RE):
            raise RemoteCaptureError(RemoteCaptureErrorCode.IDENTITY_MISMATCH)
        token = credential.token.encode("utf-8")
        self.session_id = hmac.new(
            token, b"packlab.remote-capture.session-id.v1", hashlib.sha256
        ).hexdigest()[:32]
        self.controller_id = credential.receiver_instance_id
        self.device_id = device_id
        self.expires_at = credential.expires_at
        self._keys = {
            direction: hmac.new(
                token,
                canonical_json(
                    {
                        "label": COMMAND_SCHEMA,
                        "direction": direction,
                        "controller_id": credential.receiver_instance_id,
                        "device_id": device_id,
                        "tls_certificate_fingerprint": credential.certificate_fingerprint,
                    }
                ),
                hashlib.sha256,
            ).digest()
            for direction in ("controller_to_device", "device_to_controller")
        }

    def mac(self, direction: str, body: dict[str, Any]) -> str:
        return hmac.new(self._keys[direction], canonical_json(body), hashlib.sha256).hexdigest()

    def verify(self, direction: str, body: dict[str, Any], mac: object) -> bool:
        return _is_str(mac, _HEX64_RE) and hmac.compare_digest(self.mac(direction, body), str(mac))

    def __repr__(self) -> str:
        return f"_SessionKeys(session_id={self.session_id!r}, keys=<redacted>)"

    def __reduce__(self) -> Any:
        raise TypeError("remote capture session keys are not serialisable")


@dataclass(frozen=True, slots=True)
class RemoteCaptureResponse:
    command: str
    seq: int
    status: str
    state: DeviceState
    error_code: RemoteCaptureErrorCode | None
    result: dict[str, Any]


def _same(left: str, right: object) -> bool:
    return isinstance(right, str) and hmac.compare_digest(
        left.encode(), right.encode("utf-8", "surrogatepass")
    )


# Only post-authentication device decisions may arrive as signed rejections.
_SIGNED_REJECTION_CODES = frozenset(
    {
        RemoteCaptureErrorCode.RATE_LIMITED,
        RemoteCaptureErrorCode.ILLEGAL_TRANSITION,
        RemoteCaptureErrorCode.CAPTURE_PLAN_COMPLETE,
    }
)


def _enum[E: StrEnum](cls: type[E], value: object) -> E | None:
    if not isinstance(value, str):
        return None
    try:
        return cls(value)
    except ValueError:
        return None


def _validate_frame(frame: object) -> None:
    if not isinstance(frame, dict) or set(frame) != _FRAME_KEYS:
        raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED)
    if (
        frame["measurement_authority"] is not False
        or frame["scan_master_authority"] is not False
        or frame["capture_metadata_status"] != FRAME_METADATA_STATUS
    ):
        raise RemoteCaptureError(RemoteCaptureErrorCode.AUTHORITY_UPGRADE)
    planned = (frame["plan_step"], frame["ring_id"], frame["planned_turntable_angle_mdeg"])
    if not (
        _is_int(frame["frame_index"], 0, MAX_SEQ)
        and _is_int(frame["device_capture_timestamp_ms"], 0, 2**53)
        and _is_optional_int(frame["plan_step"], 0, MAX_PLAN_STEPS - 1)
        and (frame["ring_id"] is None or _is_str(frame["ring_id"], _ID_RE))
        and _is_optional_int(frame["planned_turntable_angle_mdeg"], 0, 359_999)
        and len({item is None for item in planned}) == 1  # all planned fields or none
    ):
        raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED)


class RemoteCaptureController:
    """Windows Studio side: signs commands and verifies device responses."""

    def __init__(
        self,
        authenticator: PairingAuthenticator,
        credential: SessionCredential,
        *,
        device_id: str,
        peer_address: str,
        clock: Callable[[], float] = time.time,
        nonce_source: Callable[[], str] = lambda: secrets.token_hex(16),
        enabled: bool = False,
    ) -> None:
        if not enabled:
            raise RemoteCaptureError(RemoteCaptureErrorCode.FEATURE_DISABLED)
        require_lan_peer(peer_address)
        self._authenticator = authenticator
        self._credential = credential
        self._keys = _SessionKeys(credential, device_id)
        self._clock = clock
        self._nonce_source = nonce_source
        self._seq = 0
        # ponytail: oldest pending entries are evicted after MAX_PENDING; their
        # late responses become UNEXPECTED_RESPONSE and need query_status.
        self._pending: OrderedDict[int, tuple[str, str]] = OrderedDict()
        self.last_state: DeviceState | None = None

    def __repr__(self) -> str:
        return f"RemoteCaptureController(device_id={self._keys.device_id!r}, keys=<redacted>)"

    def __reduce__(self) -> Any:
        raise TypeError("remote capture controller is not serialisable")

    def _require_session(self) -> None:
        # TLS is not enforced by this module (transport-agnostic contract); the
        # real transport must be the pinned TLS channel. See the PL-0429 doc.
        mapping: dict[str, RemoteCaptureErrorCode] = {
            TransferErrorCode.UNPAIRED: RemoteCaptureErrorCode.UNPAIRED_SESSION,
            TransferErrorCode.EXPIRED_PAIRING: RemoteCaptureErrorCode.SESSION_EXPIRED,
        }
        try:
            self._authenticator.require_session(
                receiver_instance_id=self._credential.receiver_instance_id,
                token=self._credential.token,
                certificate_fingerprint_value=self._credential.certificate_fingerprint,
            )
        except TransferProtocolError as error:
            code = mapping.get(error.code, RemoteCaptureErrorCode.IDENTITY_MISMATCH)
            raise RemoteCaptureError(code) from None

    def build(self, command: str, args: dict[str, Any] | None = None) -> bytes:
        self._require_session()
        valid_args = _validate_args(command, {} if args is None else args)
        if self._seq >= MAX_SEQ:
            raise RemoteCaptureError(RemoteCaptureErrorCode.SESSION_EXPIRED)
        nonce = self._nonce_source()
        if not _is_str(nonce, _HEX32_RE):
            raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED)
        self._seq += 1
        body = {
            "schema": COMMAND_SCHEMA,
            "command": command,
            "session_id": self._keys.session_id,
            "controller_id": self._keys.controller_id,
            "device_id": self._keys.device_id,
            "seq": self._seq,
            "nonce": nonce,
            "issued_at_ms": int(self._clock() * 1000),
            "args": valid_args,
        }
        wire = canonical_json({**body, "mac": self._keys.mac("controller_to_device", body)})
        if len(wire) > MAX_COMMAND_BYTES:
            raise RemoteCaptureError(RemoteCaptureErrorCode.OVERSIZED)
        self._pending[self._seq] = (command, nonce)
        while len(self._pending) > MAX_PENDING:
            self._pending.popitem(last=False)
        return wire

    @property
    def pending_seqs(self) -> tuple[int, ...]:
        return tuple(self._pending)

    def accept_response(self, wire: bytes) -> RemoteCaptureResponse:
        """Verify a device response. Every failure raises :class:`RemoteCaptureError`."""
        self._require_session()  # expiry/revocation re-checked on receipt too
        try:
            return self._accept_response(wire)
        except RemoteCaptureError:
            raise
        except Exception:  # defensive: hostile input must never escape as a crash
            raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED) from None

    def _accept_response(self, wire: bytes) -> RemoteCaptureResponse:
        value = _strict_loads(wire, MAX_RESPONSE_BYTES)
        if value.get("schema") != RESPONSE_SCHEMA:
            raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED)
        if set(value) == _UNSIGNED_REJECTION_KEYS and value.get("status") == "rejected":
            device_code = _enum(RemoteCaptureErrorCode, value["error_code"])
            if device_code is None:
                device_code = RemoteCaptureErrorCode.MALFORMED
            raise RemoteCaptureError(
                RemoteCaptureErrorCode.DEVICE_REJECTED_UNAUTHENTICATED, device_code=device_code
            )
        if set(value) != _RESPONSE_KEYS:
            raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED)
        body = {key: item for key, item in value.items() if key != "mac"}
        if not self._keys.verify("device_to_controller", body, value["mac"]):
            raise RemoteCaptureError(RemoteCaptureErrorCode.BAD_MAC)
        if not _same(self._keys.session_id, value["session_id"]):
            raise RemoteCaptureError(RemoteCaptureErrorCode.UNKNOWN_SESSION)
        if not (
            _same(self._keys.controller_id, value["controller_id"])
            and _same(self._keys.device_id, value["device_id"])
        ):
            raise RemoteCaptureError(RemoteCaptureErrorCode.IDENTITY_MISMATCH)
        seq = value["in_reply_to_seq"]
        pending = self._pending.get(seq) if _is_int(seq, 1, MAX_SEQ) else None
        if pending is None or not (
            _same(pending[0], value["command"]) and _same(pending[1], value["in_reply_to_nonce"])
        ):
            raise RemoteCaptureError(RemoteCaptureErrorCode.UNEXPECTED_RESPONSE)
        del self._pending[seq]
        response = self._validate_signed(value)
        self.last_state = response.state
        return response

    @staticmethod
    def _validate_signed(value: dict[str, Any]) -> RemoteCaptureResponse:
        """Exact response contract: keys, types and authority, even when MAC-valid."""
        malformed = RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED)
        status, result, command = value["status"], value["result"], value["command"]
        state = _enum(DeviceState, value["state"])
        error_code = (
            None
            if value["error_code"] is None
            else _enum(RemoteCaptureErrorCode, value["error_code"])
        )
        if state is None or not _is_int(value["issued_at_ms"], 0, 2**53):
            raise malformed
        if status == "ok":
            if value["error_code"] is not None:
                raise malformed
        elif status != "rejected" or error_code not in _SIGNED_REJECTION_CODES:
            raise malformed
        frame_expected = status == "ok" and command == "capture_frame"
        expected_keys = _STATUS_KEYS | {"frame"} if frame_expected else _STATUS_KEYS
        if not isinstance(result, dict) or set(result) != expected_keys:
            raise malformed  # also rejects stray frames and extra (authority-like) keys
        steps_total, steps_remaining = result["plan_steps_total"], result["plan_steps_remaining"]
        if not (
            result["state"] == state.value
            and (result["capture_mode"] is None or _is_capture_mode(result["capture_mode"]))
            and _is_int(result["frames_captured"], 0, MAX_SEQ)
            and _is_int(result["last_accepted_seq"], 0, MAX_SEQ)
            and _is_int(steps_total, 0, MAX_PLAN_STEPS)
            and _is_int(steps_remaining, 0, MAX_PLAN_STEPS)
            and steps_remaining <= steps_total
        ):
            raise malformed
        if frame_expected:
            _validate_frame(result["frame"])
        return RemoteCaptureResponse(
            command, value["in_reply_to_seq"], status, state, error_code, result
        )


def _unsigned_rejection(code: RemoteCaptureErrorCode) -> bytes:
    return canonical_json(
        {"schema": RESPONSE_SCHEMA, "status": "rejected", "error_code": code.value}
    )


@dataclass(frozen=True, slots=True)
class _Command:
    command: str
    seq: int
    nonce: str
    issued_at_ms: int
    args: dict[str, Any]


class MockIPhoneCaptureEndpoint:
    """Deterministic in-process stand-in for the iPhone capture endpoint.

    It models the command contract and device state machine only. It captures
    no pixels and its frame metadata are placeholders, never measurements.
    """

    def __init__(
        self,
        credential: SessionCredential,
        *,
        device_id: str,
        clock: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
        enabled: bool = False,
        max_commands_per_second: int = DEFAULT_MAX_COMMANDS_PER_SECOND,
    ) -> None:
        if not _is_int(max_commands_per_second, 1, 1000):
            raise ValueError("max_commands_per_second must be an integer in 1..1000")
        self._keys: _SessionKeys | None = _SessionKeys(credential, device_id)
        self._device_id = device_id
        self._clock = clock
        self._monotonic = monotonic  # rate limiter must not follow wall-clock steps
        self._enabled = enabled
        self._max_rate = max_commands_per_second
        self._recent: deque[float] = deque()
        self._last_seq = 0
        self._nonces: deque[str] = deque(maxlen=NONCE_MEMORY)
        self.state = DeviceState.IDLE
        self.capture_mode: str | None = None
        self.frames_captured = 0
        self._plan: tuple[dict[str, Any], ...] = ()
        self._plan_cursor = 0
        # Local-only diagnostics (detailed codes, no payloads); bounded against floods.
        self.rejections: deque[RemoteCaptureErrorCode] = deque(maxlen=REJECTION_MEMORY)

    def __repr__(self) -> str:
        return f"MockIPhoneCaptureEndpoint(device_id={self._device_id!r}, state={self.state.value})"

    def __reduce__(self) -> Any:
        raise TypeError("remote capture endpoint is not serialisable")

    def revoke(self) -> None:
        """Forget the pairing; later commands get the generic unauthenticated rejection."""
        self._keys = None

    def handle(self, wire: bytes, *, peer_address: str) -> bytes:
        try:
            return self._handle(wire, peer_address)
        except Exception:  # defensive: hostile input must never crash the endpoint
            self.rejections.append(RemoteCaptureErrorCode.MALFORMED)
            return _unsigned_rejection(RemoteCaptureErrorCode.MALFORMED)

    def _handle(self, wire: bytes, peer_address: str) -> bytes:
        try:
            keys, command = self._authenticate(wire, peer_address)
        except RemoteCaptureError as error:
            self.rejections.append(error.detail or error.code)
            return _unsigned_rejection(error.code)
        try:
            self._rate_limit()
            result = self._apply(command)
            status, error_code = "ok", None
        except RemoteCaptureError as error:
            self.rejections.append(error.code)
            result, status, error_code = self._status(), "rejected", error.code.value
        body = {
            "schema": RESPONSE_SCHEMA,
            "session_id": keys.session_id,
            "controller_id": keys.controller_id,
            "device_id": keys.device_id,
            "in_reply_to_seq": command.seq,
            "in_reply_to_nonce": command.nonce,
            "command": command.command,
            "status": status,
            "state": self.state.value,
            "error_code": error_code,
            "result": result,
            "issued_at_ms": int(self._clock() * 1000),
        }
        return canonical_json({**body, "mac": keys.mac("device_to_controller", body)})

    def _authenticate(self, wire: bytes, peer_address: str) -> tuple[_SessionKeys, _Command]:
        if not self._enabled:
            raise RemoteCaptureError(RemoteCaptureErrorCode.FEATURE_DISABLED)
        require_lan_peer(peer_address)
        value = _strict_loads(wire, MAX_COMMAND_BYTES)
        if set(value) != _COMMAND_KEYS or value["schema"] != COMMAND_SCHEMA:
            raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED)
        if not (
            _is_str(value["session_id"], _HEX32_RE)
            and _is_str(value["controller_id"], _ID_RE)
            and _is_str(value["device_id"], _ID_RE)
            and _is_int(value["seq"], 1, MAX_SEQ)
            and _is_str(value["nonce"], _HEX32_RE)
            and _is_int(value["issued_at_ms"], 0, 2**53)
            and _is_str(value["mac"], _HEX64_RE)
        ):
            raise RemoteCaptureError(RemoteCaptureErrorCode.MALFORMED)
        args = _validate_args(value["command"], value["args"])
        # Pre-MAC identity failures share one wire code (no pairing/identity oracle);
        # the specific reason is kept only in the local rejection log.
        keys = self._keys
        detail = None
        if keys is None:
            detail = RemoteCaptureErrorCode.UNPAIRED_SESSION
        elif not _same(keys.session_id, value["session_id"]):
            detail = RemoteCaptureErrorCode.UNKNOWN_SESSION
        elif not (
            _same(keys.controller_id, value["controller_id"])
            and _same(keys.device_id, value["device_id"])
        ):
            detail = RemoteCaptureErrorCode.IDENTITY_MISMATCH
        if keys is None or detail is not None:
            raise RemoteCaptureError(RemoteCaptureErrorCode.UNAUTHENTICATED, detail=detail)
        body = {key: item for key, item in value.items() if key != "mac"}
        if not keys.verify("controller_to_device", body, value["mac"]):
            raise RemoteCaptureError(RemoteCaptureErrorCode.BAD_MAC)
        now = self._clock()
        if now >= keys.expires_at:
            raise RemoteCaptureError(RemoteCaptureErrorCode.SESSION_EXPIRED)
        if abs(int(now * 1000) - value["issued_at_ms"]) > TIMESTAMP_WINDOW_MS:
            raise RemoteCaptureError(RemoteCaptureErrorCode.STALE_COMMAND)
        if value["seq"] <= self._last_seq or value["nonce"] in self._nonces:
            raise RemoteCaptureError(RemoteCaptureErrorCode.REPLAYED_COMMAND)
        # Consumed once authenticated, even if later rejected: exact bytes never re-execute.
        self._last_seq = value["seq"]
        self._nonces.append(value["nonce"])
        command = _Command(
            value["command"], value["seq"], value["nonce"], value["issued_at_ms"], args
        )
        return keys, command

    def _rate_limit(self) -> None:
        now = self._monotonic()
        while self._recent and now - self._recent[0] >= 1.0:
            self._recent.popleft()
        if len(self._recent) >= self._max_rate:
            raise RemoteCaptureError(RemoteCaptureErrorCode.RATE_LIMITED)
        self._recent.append(now)

    def _status(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "capture_mode": self.capture_mode,
            "frames_captured": self.frames_captured,
            "plan_steps_total": len(self._plan),
            "plan_steps_remaining": len(self._plan) - self._plan_cursor,
            "last_accepted_seq": self._last_seq,
        }

    def _apply(self, command: _Command) -> dict[str, Any]:
        next_state = _TRANSITIONS[command.command].get(self.state)
        if next_state is None:
            raise RemoteCaptureError(RemoteCaptureErrorCode.ILLEGAL_TRANSITION)
        frame: dict[str, Any] | None = None
        if command.command == "start_session":
            self.capture_mode = command.args["capture_mode"]
        elif command.command == "set_capture_plan":
            self._plan = tuple(dict(step) for step in command.args["steps"])
            self._plan_cursor = 0
        elif command.command == "capture_frame":
            if self._plan and self._plan_cursor >= len(self._plan):
                raise RemoteCaptureError(RemoteCaptureErrorCode.CAPTURE_PLAN_COMPLETE)
            step = self._plan[self._plan_cursor] if self._plan else None
            frame = {
                "frame_index": self.frames_captured,
                "plan_step": self._plan_cursor if step is not None else None,
                "ring_id": step["ring_id"] if step is not None else None,
                "planned_turntable_angle_mdeg": step["turntable_angle_mdeg"]
                if step is not None
                else None,
                "device_capture_timestamp_ms": int(self._clock() * 1000),
                "capture_metadata_status": FRAME_METADATA_STATUS,
                "measurement_authority": False,
                "scan_master_authority": False,
            }
            self.frames_captured += 1
            self._plan_cursor += 0 if step is None else 1
        self.state = next_state
        result = self._status()
        if frame is not None:
            result["frame"] = frame
        return result
