"""PL-0425 prototype: transport-agnostic turntable driver with a software safety state machine.

No physical turntable exists yet: make/model, BLE/USB protocol and e-stop wiring are
owner-gated. This module is the hardware-independent half only:

* ``TurntableDriver`` speaks a tiny frame protocol (``HOME``/``MOVE``/``STOP``/``ESTOP``
  frames, ``Ack`` and ``StatusReport`` messages) over an injectable ``TurntableTransport``.
  Every command has a timeout and returns an immutable ``CommandResult``.
* ``SimulatedTurntableTransport`` is a deterministic device model (seeded RNG, virtual
  clock, no real sleeps) with speed/acceleration limits, step quantisation, backlash,
  settle ringing, position-report jitter and injectable faults.
* ``run_turntable_capture_plan`` turns settled stops into exactly the
  ``turntable_sync.TurntableAngleEvent`` objects consumed by
  ``synchronize_turntable_angles`` (PL-0426).

Angles follow PackScan's frozen ``clockwise_from_reference`` convention (platter turns
clockwise seen from above), in degrees. Absolute moves always finish with a clockwise
approach so gear backlash is taken up the same way at every stop.

Concurrency: the driver is synchronous and not thread-safe; ``rotate_to``/``home`` block
until settle or timeout. Only ``request_emergency_stop`` may be called from another thread; it
is checked between transport polls, so it cannot interrupt a poll already blocked in the
transport, and the device keeps moving until it receives the ESTOP frame.

Safety: the e-stop here is a SOFTWARE latch only. A hardware e-stop circuit is NOT
validated by this code or its tests; a real station must cut motor power independently of
any software. A fault, disconnect or e-stop refuses all motion until an operator
acknowledges, ``reset_fault`` clears it, and the table is re-homed. A settled angle is
reported only after N consecutive in-tolerance, not-moving position reports; it is a
device-encoder report, not observed geometry, and is not physically calibrated.

Feature flag: off by default (``PACKLAB_TURNTABLE_DRIVER_ENABLED``, same strict
``true``/``false`` parsing as ``packlab_core.config``). When disabled or faulted, the
fallback is manual capture with no angle authority.
"""

from __future__ import annotations

import heapq
import hmac
import math
import os
import random
import re
import secrets
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Literal, Protocol

from packlab_core.config import ConfigError
from packlab_core.turntable_sync import TurntableAngleEvent

TURNTABLE_DRIVER_CONTRACT: Final = "packlab.turntable-driver.v1"
TURNTABLE_DRIVER_FLAG_ENV: Final = "PACKLAB_TURNTABLE_DRIVER_ENABLED"
LIMITATIONS: Final = (
    "SIMULATION_ONLY_NO_REAL_DEVICE_PROTOCOL: no BLE/USB device or vendor protocol is "
    "integrated; transports are simulated or test doubles",
    "HARDWARE_ESTOP_CIRCUIT_NOT_VALIDATED: the e-stop is a software latch only; a physical "
    "e-stop must cut motor power independently of this software and has not been tested",
    "ANGLE_ACCURACY_NOT_PHYSICALLY_CALIBRATED: settled angles are device-encoder reports, "
    "not observed geometry; platter slip invisible to the encoder cannot be detected",
    "LATENCY_AND_LINK_LOSS_BEHAVIOUR_UNVERIFIED: real link latency and device behaviour on "
    "link loss are unknown; the simulator assumes the device halts",
    "DEVICE_ROTATION_DIRECTION_UNVERIFIED: that a real device's positive direction is "
    "clockwise seen from above (clockwise_from_reference) has not been checked on hardware",
    "SINGLE_THREADED_NO_PREEMPTIVE_SOFTWARE_ESTOP: commands block until settle or timeout; "
    "a software e-stop from another thread (request_emergency_stop) is honoured only between "
    "transport polls (worst case status_timeout_s on a silent link) and the device keeps "
    "executing its last command until it receives the ESTOP frame",
)
_OPERATOR = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")
_STALL_PROGRESS_DEG: Final = 0.05


def turntable_driver_enabled(env: Mapping[str, str] | None = None) -> bool:
    """Feature flag, default off; strict ``true``/``false`` like ``packlab_core.config``."""
    raw = (os.environ if env is None else env).get(TURNTABLE_DRIVER_FLAG_ENV)
    if raw is None:
        return False
    if raw.lower() not in {"true", "false"}:
        raise ConfigError(f"environment: {TURNTABLE_DRIVER_FLAG_ENV} must be true or false")
    return raw.lower() == "true"


class TurntableState(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    IDLE = "IDLE"
    HOMING = "HOMING"
    MOVING = "MOVING"
    SETTLING = "SETTLING"
    FAULT = "FAULT"
    ESTOP_LATCHED = "ESTOP_LATCHED"


_S = TurntableState
_HALT = {_S.FAULT, _S.ESTOP_LATCHED, _S.DISCONNECTED}
_ALLOWED: Final[Mapping[TurntableState, frozenset[TurntableState]]] = {
    _S.DISCONNECTED: frozenset({_S.IDLE, _S.ESTOP_LATCHED}),
    _S.IDLE: frozenset({_S.HOMING, _S.MOVING, *_HALT}),
    _S.HOMING: frozenset({_S.SETTLING, *_HALT}),
    _S.MOVING: frozenset({_S.SETTLING, *_HALT}),
    _S.SETTLING: frozenset({_S.IDLE, _S.MOVING, _S.HOMING, *_HALT}),  # moved again
    _S.FAULT: frozenset({_S.IDLE, _S.ESTOP_LATCHED, _S.DISCONNECTED}),
    # Only reset_fault (with an operator token) leaves the latch; a disconnect keeps it.
    _S.ESTOP_LATCHED: frozenset({_S.IDLE, _S.DISCONNECTED}),
}


class TurntableDriverError(RuntimeError):
    """Base class for refused driver commands."""


class IllegalTransitionError(TurntableDriverError):
    """The command is not allowed from the current state."""


class MotionRefusedError(IllegalTransitionError):
    """Motion requested while not IDLE (e.g. FAULT, ESTOP_LATCHED, DISCONNECTED)."""


class NotHomedError(MotionRefusedError):
    """Motion requested before (re-)homing after connect, fault, disconnect or e-stop."""


class AcknowledgementRequiredError(TurntableDriverError):
    """reset_fault called without the current operator acknowledgement token."""


class TurntableCommandError(ValueError):
    """Malformed command argument (angle, timeout, operator id)."""


class TurntableTransportDisconnected(ConnectionError):
    """Raised by a transport when the link is down."""


@dataclass(frozen=True, slots=True)
class CommandFrame:
    command_id: int
    verb: Literal["HOME", "MOVE", "STOP", "ESTOP"]
    target_deg: float | None = None  # continuous device-frame degrees for MOVE


@dataclass(frozen=True, slots=True)
class Ack:
    command_id: int
    accepted: bool = True


@dataclass(frozen=True, slots=True)
class StatusReport:
    report_seq: int
    position_deg: float  # measured, [0, 360), clockwise_from_reference
    moving: bool
    estop_input: bool = False


Message = Ack | StatusReport


class TurntableTransport(Protocol):
    """Injectable link. ``receive`` blocks up to ``timeout_s`` (virtual or real time)."""

    def open(self, timeout_s: float) -> None: ...
    def close(self) -> None: ...
    def send(self, frame: CommandFrame) -> None: ...
    def receive(self, timeout_s: float) -> Message | None: ...
    def now(self) -> float: ...


@dataclass(frozen=True, slots=True)
class DriverEvent:
    time_s: float
    kind: str
    state: TurntableState
    position_deg: float | None
    detail: str | None = None


def _norm(angle: float) -> float:
    value = angle % 360.0
    return 0.0 if value >= 360.0 else value + 0.0


def _signed(a: float, b: float) -> float:
    """Signed shortest difference a - b in (-180, 180]."""
    return -(((b - a) + 180.0) % 360.0 - 180.0)


@dataclass(frozen=True, slots=True)
class SettledAngle:
    commanded_angle_deg: float
    measured_angle_deg: float  # commanded + mean signed error of the settle samples
    sample_count: int
    max_abs_error_deg: float
    time_s: float

    def to_angle_event(self, sequence: int, source_id: str) -> TurntableAngleEvent:
        """The exact PL-0426 event type consumed by ``synchronize_turntable_angles``."""
        return TurntableAngleEvent(
            sequence, self.commanded_angle_deg, self.measured_angle_deg, source_id
        )


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: str
    ok: bool
    reason_code: str | None
    state: TurntableState
    homed: bool
    position_deg: float | None
    settled: SettledAngle | None
    elapsed_s: float
    events: tuple[DriverEvent, ...]
    limitations: tuple[str, ...] = LIMITATIONS


class _Abort(Exception):
    def __init__(self, reason: str, *, estop: bool = False) -> None:
        super().__init__(reason)
        self.reason, self.estop = reason, estop


def _timeout(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TurntableCommandError("timeout_invalid")
    if not math.isfinite(value) or not 0.0 < value <= 600.0:
        raise TurntableCommandError("timeout_invalid")
    return float(value)


class TurntableDriver:
    """Synchronous driver; see the module docstring for safety scope and limits."""

    def __init__(
        self,
        transport: TurntableTransport,
        *,
        settle_tolerance_deg: float = 0.2,
        settle_samples: int = 5,
        ack_timeout_s: float = 0.25,
        status_timeout_s: float = 0.25,
        stall_window_s: float = 0.5,
        anti_backlash_deg: float = 1.0,
    ) -> None:
        if not 0.0 < settle_tolerance_deg <= 5.0 or not 1 <= settle_samples <= 100:
            raise TurntableCommandError("settle_parameters_invalid")
        if not anti_backlash_deg > 2 * settle_tolerance_deg:
            raise TurntableCommandError("anti_backlash_invalid")
        self._t = transport
        self.settle_tolerance_deg = float(settle_tolerance_deg)
        self.settle_samples = settle_samples
        self.ack_timeout_s = _timeout(ack_timeout_s)
        self.status_timeout_s = _timeout(status_timeout_s)
        self.stall_window_s = _timeout(stall_window_s)
        self.anti_backlash_deg = float(anti_backlash_deg)
        self._state = _S.DISCONNECTED
        self._connected = False
        self._homed = False
        self._cont = 0.0  # last commanded continuous device angle
        self._position: float | None = None
        self._last_seq = -1
        self._next_id = 1
        self._token: str | None = None
        self._events: list[DriverEvent] = []
        self._connecting = False
        self._estop_request = threading.Event()  # the only cross-thread entry point

    # -- read-only view -------------------------------------------------------------
    @property
    def state(self) -> TurntableState:
        return self._state

    @property
    def homed(self) -> bool:
        return self._homed

    @property
    def events(self) -> tuple[DriverEvent, ...]:
        return tuple(self._events)

    # -- commands -------------------------------------------------------------------
    def connect(self, timeout_s: float = 2.0) -> CommandResult:
        if self._connected:
            raise IllegalTransitionError("already_connected")

        def body(deadline: float) -> None:
            self._t.open(deadline - self._t.now())
            self._connected = True
            self._last_seq = -1
            self._await_report(deadline)  # a device e-stop input here latches (review P3-2)
            if self._state is _S.DISCONNECTED:
                self._transition(_S.IDLE)

        self._connecting = True
        try:
            return self._run("connect", timeout_s, body)
        finally:
            self._connecting = False

    def home(self, timeout_s: float = 30.0) -> CommandResult:
        self._require_idle(homing=True)

        def body(deadline: float) -> SettledAngle | None:
            self._transition(_S.HOMING)
            self._await_ack(self._send("HOME"), deadline)
            settled = self._await_position(0.0, deadline, settle=True)
            self._cont, self._homed = 0.0, True
            self._transition(_S.IDLE)
            return settled

        return self._run("home", timeout_s, body)

    def rotate_to(self, angle_deg: float, timeout_s: float = 15.0) -> CommandResult:
        """Move clockwise (seen from above) to an absolute angle in [0, 360)."""
        if isinstance(angle_deg, bool) or not isinstance(angle_deg, (int, float)):
            raise TurntableCommandError("angle_invalid")
        if not math.isfinite(angle_deg) or not 0.0 <= angle_deg < 360.0:
            raise TurntableCommandError("angle_invalid")
        self._require_idle()
        delta = (float(angle_deg) - self._cont) % 360.0
        if abs(_signed(angle_deg, self._cont)) < 1e-9:
            delta = 0.0  # already there: verify settle without a lap
        return self._move("rotate_to", self._cont + delta, timeout_s)

    def rotate_by(self, delta_deg: float, timeout_s: float = 15.0) -> CommandResult:
        """Relative move in [-360, 360]; counter-clockwise moves end with a clockwise approach."""
        if isinstance(delta_deg, bool) or not isinstance(delta_deg, (int, float)):
            raise TurntableCommandError("delta_invalid")
        if not math.isfinite(delta_deg) or abs(delta_deg) > 360.0:
            raise TurntableCommandError("delta_invalid")
        self._require_idle()
        return self._move("rotate_by", self._cont + float(delta_deg), timeout_s)

    def stop(self, timeout_s: float = 1.0) -> CommandResult:
        """Controlled stop; allowed in any connected state and never changes the latch."""
        if not self._connected:
            raise IllegalTransitionError("not_connected")
        return self._run(
            "stop", timeout_s, lambda deadline: self._await_ack(self._send("STOP"), deadline)
        )

    def emergency_stop(self, timeout_s: float = 0.5) -> CommandResult:
        """Latch ESTOP in software first, then best-effort ESTOP frame to the device.

        Software only: a hardware e-stop circuit is NOT validated by this driver.
        """
        start, mark = self._t.now(), len(self._events)
        self._latch("operator_software_estop")
        if not self._connected:
            return self._result(
                "emergency_stop", False, "estop_not_sent_disconnected", None, start, mark
            )
        return self._run(
            "emergency_stop",
            timeout_s,
            lambda deadline: self._await_ack(self._send("ESTOP"), deadline),
        )

    def request_emergency_stop(self) -> None:
        """Thread-safe: latch ESTOP at the running command's next transport poll.

        Software only; it cannot interrupt a poll already blocked in the transport, and a
        hardware e-stop circuit is NOT validated. An idle driver latches on its next command.
        """
        self._estop_request.set()

    def acknowledge(self, operator_id: str) -> str:
        """Operator acknowledgement of the current fault/e-stop; returns a one-time token."""
        if self._state not in (_S.FAULT, _S.ESTOP_LATCHED):
            raise IllegalTransitionError(f"nothing_to_acknowledge_in_{self._state}")
        if not isinstance(operator_id, str) or not _OPERATOR.fullmatch(operator_id):
            raise TurntableCommandError("operator_id_invalid")
        self._token = secrets.token_urlsafe(16)
        self._event("OPERATOR_ACKNOWLEDGED", operator_id)
        return self._token

    def reset_fault(self, token: str, timeout_s: float = 0.5) -> CommandResult:
        """Clear FAULT/ESTOP_LATCHED with the acknowledgement token; re-homing is still needed."""
        if self._state not in (_S.FAULT, _S.ESTOP_LATCHED):
            raise IllegalTransitionError(f"nothing_to_reset_in_{self._state}")
        expected, self._token = self._token, None
        if expected is None or not isinstance(token, str):
            raise AcknowledgementRequiredError("operator_acknowledgement_required")
        if not hmac.compare_digest(token, expected):
            raise AcknowledgementRequiredError("operator_acknowledgement_required")
        if not self._connected:
            start, mark = self._t.now(), len(self._events)
            self._transition(_S.DISCONNECTED)
            self._event("FAULT_RESET")
            return self._result("reset_fault", True, None, None, start, mark)

        def body(deadline: float) -> None:
            self._await_report(deadline)  # refuses while the device e-stop input is asserted
            self._transition(_S.IDLE)
            self._event("FAULT_RESET")

        return self._run("reset_fault", timeout_s, body)

    def status(self, timeout_s: float = 0.5) -> CommandResult:
        """Fresh status report; a silent device faults the driver."""
        if not self._connected:
            return self._result("status", False, "disconnected", None, self._t.now(), None)
        return self._run("status", timeout_s, self._await_report)

    # -- internals ------------------------------------------------------------------
    def _require_idle(self, *, homing: bool = False) -> None:
        if self._state is not _S.IDLE:
            raise MotionRefusedError(f"motion_refused_in_{self._state}")
        if not homing and not self._homed:
            raise NotHomedError("motion_refused_not_homed")

    def _move(self, command: str, target: float, timeout_s: float) -> CommandResult:
        def body(deadline: float) -> SettledAngle | None:
            self._transition(_S.MOVING)
            if target < self._cont:  # counter-clockwise: overshoot, then approach clockwise
                leg = target - self.anti_backlash_deg
                self._await_ack(self._send("MOVE", leg), deadline)
                self._await_position(leg, deadline, settle=False)
            self._await_ack(self._send("MOVE", target), deadline)
            settled = self._await_position(target, deadline, settle=True)
            self._cont = target
            self._transition(_S.IDLE)
            return settled

        return self._run(command, timeout_s, body)

    def _run(
        self, command: str, timeout_s: float, body: Callable[[float], SettledAngle | None]
    ) -> CommandResult:
        start, mark = self._t.now(), len(self._events)
        deadline = start + _timeout(timeout_s)
        try:
            self._check_estop_request()
            settled = body(deadline)
        except _Abort as abort:
            self._fail(abort)
            return self._result(command, False, abort.reason, None, start, mark)
        except TurntableTransportDisconnected:
            self._on_disconnect()
            return self._result(command, False, "transport_disconnected", None, start, mark)
        except Exception as exc:  # any other transport/driver error: halt and fault (P2-1)
            reason = f"transport_error:{type(exc).__name__}"
            self._fail(_Abort(reason))
            return self._result(command, False, reason, None, start, mark)
        return self._result(command, True, None, settled, start, mark)

    def _result(
        self,
        command: str,
        ok: bool,
        reason: str | None,
        settled: SettledAngle | None,
        start: float,
        mark: int | None,
    ) -> CommandResult:
        events = () if mark is None else self._events[mark:]
        return CommandResult(
            command,
            ok,
            reason,
            self._state,
            self._homed,
            self._position,
            settled,
            self._t.now() - start,
            tuple(events),
        )

    def _event(self, kind: str, detail: str | None = None) -> None:
        self._events.append(DriverEvent(self._t.now(), kind, self._state, self._position, detail))

    def _transition(self, new: TurntableState) -> None:
        if new not in _ALLOWED[self._state]:
            raise IllegalTransitionError(f"{self._state}->{new}")
        self._state = new
        self._event("STATE_CHANGED", str(new))

    def _check_estop_request(self) -> None:
        if self._estop_request.is_set():
            self._estop_request.clear()
            raise _Abort("operator_software_estop", estop=True)

    def _latch(self, reason: str) -> None:
        self._homed, self._token = False, None
        if self._state is not _S.ESTOP_LATCHED:
            self._transition(_S.ESTOP_LATCHED)
        self._event("ESTOP_LATCHED", reason)

    def _fail(self, abort: _Abort) -> None:
        self._homed, self._token = False, None
        if self._connecting and not abort.estop:  # failed (re)connect, latched or not
            self._connected = False
            self._t.close()
            self._event("CONNECT_FAILED", abort.reason)
            return
        if abort.estop:
            self._latch(abort.reason)
        elif self._state is not _S.ESTOP_LATCHED:
            if self._state is not _S.FAULT:
                self._transition(_S.FAULT)
            self._event("FAULT", abort.reason)
        try:  # best-effort halt; the result already carries the fault
            self._send("ESTOP" if abort.estop else "STOP")
        except TurntableTransportDisconnected:
            self._on_disconnect()
        except Exception as exc:  # the halt itself failed; the driver is already faulted
            self._event("HALT_SEND_FAILED", type(exc).__name__)

    def _on_disconnect(self) -> None:
        self._connected, self._homed = False, False
        self._t.close()
        if self._state is not _S.ESTOP_LATCHED:
            self._state = _S.DISCONNECTED  # every state may drop to DISCONNECTED
        self._event("DISCONNECTED")

    def _send(
        self, verb: Literal["HOME", "MOVE", "STOP", "ESTOP"], target: float | None = None
    ) -> int:
        command_id, self._next_id = self._next_id, self._next_id + 1
        self._t.send(CommandFrame(command_id, verb, target))
        return command_id

    def _accept(self, message: Message | None) -> StatusReport | None:
        self._check_estop_request()
        if message is None:
            return None
        if isinstance(message, Ack):
            self._event("UNEXPECTED_ACK_IGNORED", str(message.command_id))
            return None
        if message.report_seq <= self._last_seq:
            self._event("STALE_STATUS_DROPPED", str(message.report_seq))
            return None
        self._last_seq, self._position = message.report_seq, message.position_deg
        if message.estop_input:
            raise _Abort("device_estop_input", estop=True)
        return message

    def _await_ack(self, command_id: int, deadline: float) -> None:
        ack_deadline = min(deadline, self._t.now() + self.ack_timeout_s)
        while (remaining := ack_deadline - self._t.now()) > 0:
            message = self._t.receive(remaining)
            if isinstance(message, Ack) and message.command_id == command_id:
                if not message.accepted:
                    raise _Abort("command_rejected_by_device")
                return
            self._accept(message)
        raise _Abort("ack_timeout")

    def _await_report(self, deadline: float) -> None:
        deadline = min(deadline, self._t.now() + self.status_timeout_s)
        while (remaining := deadline - self._t.now()) > 0:
            if self._accept(self._t.receive(remaining)) is not None:
                return
        raise _Abort("status_timeout")

    def _await_position(
        self, target: float, deadline: float, *, settle: bool
    ) -> SettledAngle | None:
        commanded, tol = _norm(target), self.settle_tolerance_deg
        motion_state = self._state  # HOMING or MOVING
        errors: list[float] = []
        progress_pos: float | None = None
        progress_t = last_report = self._t.now()
        last_moving = False
        while True:
            now = self._t.now()
            if now >= deadline:
                raise _Abort("stuck_moving" if last_moving else "settle_timeout")
            silence = last_report + self.status_timeout_s
            if now >= silence:
                raise _Abort("status_timeout")
            report = self._accept(self._t.receive(min(deadline, silence) - now))
            if report is None:
                continue
            last_report, last_moving = self._t.now(), report.moving
            error = _signed(report.position_deg, commanded)
            if report.moving:
                errors.clear()
                if self._state is _S.SETTLING:  # it moved again (review P3-7)
                    self._transition(motion_state)
                if progress_pos is None or abs(_signed(report.position_deg, progress_pos)) > (
                    _STALL_PROGRESS_DEG
                ):
                    progress_pos, progress_t = report.position_deg, last_report
                elif last_report - progress_t >= self.stall_window_s:
                    raise _Abort("stuck_moving" if abs(error) <= tol else "stall_detected")
                continue
            progress_pos = None
            if not settle:
                if abs(error) <= self.anti_backlash_deg / 2:
                    return None
                continue
            if self._state is not _S.SETTLING:
                self._transition(_S.SETTLING)
            errors = [*errors, error] if abs(error) <= tol else []
            if len(errors) >= self.settle_samples:
                mean = sum(errors) / len(errors)
                settled = SettledAngle(
                    commanded,
                    _norm(commanded + mean),
                    len(errors),
                    max(abs(e) for e in errors),
                    last_report,
                )
                self._event("SETTLED", f"{settled.measured_angle_deg:.4f}")
                return settled


# -- simulator ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SimulatedTurntableConfig:
    """Plausible small stepper turntable; values are illustrative, not a real product."""

    max_speed_deg_s: float = 90.0
    max_accel_deg_s2: float = 360.0
    step_deg: float = 360.0 / 6400.0  # 200-step motor, 1/16 microstep, 2:1 reduction
    backlash_deg: float = 0.3
    jitter_sigma_deg: float = 0.02
    ring_amplitude_deg: float = 0.5
    ring_decay_s: float = 0.06
    ring_frequency_hz: float = 7.0
    report_period_s: float = 0.02
    ack_latency_s: float = 0.015


@dataclass(frozen=True, slots=True)
class SimulatedFaults:
    disconnect_at_s: float | None = None  # link drops once; device halts
    silent_after_s: float | None = None  # device stops sending acks and reports
    drop_ack_frames: frozenset[int] = frozenset()  # 1-based frame indices
    duplicate_acks: bool = False
    out_of_order_status: bool = False  # every report pair arrives swapped
    stall_on_move: int | None = None  # 1-based MOVE count; platter jams halfway
    stuck_moving_on_move: int | None = None  # arrives but keeps reporting moving
    encoder_drift_deg_per_s: float = 0.0
    estop_input_at_s: float | None = None  # device e-stop input asserted (software model)
    estop_input_release_s: float | None = None


class SimulatedTurntableTransport:
    """Deterministic device model on a virtual clock; ``receive`` advances time."""

    def __init__(
        self,
        *,
        seed: int,
        config: SimulatedTurntableConfig = SimulatedTurntableConfig(),
        faults: SimulatedFaults = SimulatedFaults(),
    ) -> None:
        self._rng = random.Random(seed)
        self._cfg, self._faults = config, faults
        self._now, self._ticks = 0.0, 0
        self._link, self._dropped = False, False
        self._outbox: list[tuple[float, int, Message]] = []
        self._order = self._report_seq = self._moves = 0
        self._held: StatusReport | None = None
        self._offset = self._rng.uniform(0.0, 360.0)  # unknown power-on angle
        self._motor = self._platter = self._speed = 0.0
        self._target: float | None = None
        self._stall_at: float | None = None
        self._homing = self._stuck = self._moving = False
        self._ring_start: float | None = None
        self.frames: list[CommandFrame] = []

    def now(self) -> float:
        return self._now

    def open(self, timeout_s: float) -> None:
        self._link, self._outbox, self._held = True, [], None

    def close(self) -> None:
        self._link = False

    def send(self, frame: CommandFrame) -> None:
        self._check_link()
        self.frames.append(frame)
        accepted = not (self._estop_input() and frame.verb in ("MOVE", "HOME"))
        if accepted:
            self._apply(frame)
        if not self._silent() and len(self.frames) not in self._faults.drop_ack_frames:
            for _ in range(2 if self._faults.duplicate_acks else 1):
                self._queue(self._now + self._cfg.ack_latency_s, Ack(frame.command_id, accepted))

    def receive(self, timeout_s: float) -> Message | None:
        deadline = self._now + max(timeout_s, 0.0)
        while True:
            self._check_link()
            if self._outbox and self._outbox[0][0] <= self._now + 1e-12:
                return heapq.heappop(self._outbox)[2]
            tick = (self._ticks + 1) * self._cfg.report_period_s
            upcoming = min(tick, self._outbox[0][0]) if self._outbox else tick
            if upcoming > deadline:
                self._now = deadline
                return None
            self._now = upcoming
            if self._now >= tick - 1e-12:
                self._ticks += 1
                self._step()

    # -- device model ---------------------------------------------------------------
    def _check_link(self) -> None:
        at = self._faults.disconnect_at_s
        if not self._dropped and at is not None and self._now >= at:
            self._dropped, self._link = True, False
            self._halt()
        if not self._link:
            raise TurntableTransportDisconnected("link_down")

    def _silent(self) -> bool:
        at = self._faults.silent_after_s
        return at is not None and self._now >= at

    def _estop_input(self) -> bool:
        at, release = self._faults.estop_input_at_s, self._faults.estop_input_release_s
        return at is not None and self._now >= at and (release is None or self._now < release)

    def _queue(self, due: float, message: Message) -> None:
        self._order += 1
        heapq.heappush(self._outbox, (due, self._order, message))

    def _halt(self) -> None:
        if self._moving:
            self._ring_start = self._now
        self._target, self._speed, self._moving, self._stuck, self._homing = (
            None,
            0.0,
            False,
            False,
            False,
        )

    def _apply(self, frame: CommandFrame) -> None:
        step = self._cfg.step_deg
        if frame.verb in ("STOP", "ESTOP"):
            self._halt()
            return
        if frame.verb == "HOME":
            target = self._motor + (-(self._motor + self._offset)) % 360.0
            self._homing, self._stall_at, self._stuck = True, None, False
        else:
            assert frame.target_deg is not None
            target = frame.target_deg - self._offset
            self._moves += 1
            self._stuck = self._moves == self._faults.stuck_moving_on_move
            self._stall_at = (
                self._motor + 0.5 * (target - self._motor)
                if self._moves == self._faults.stall_on_move
                else None
            )
        self._target = round(target / step) * step
        self._moving, self._ring_start = True, None

    def _step(self) -> None:
        cfg, dt = self._cfg, self._cfg.report_period_s
        if self._target is not None:
            remaining = self._target - self._motor
            if abs(remaining) < 1e-9:
                self._arrive()
            else:
                a = cfg.max_accel_deg_s2
                if self._speed * self._speed / (2 * a) >= abs(remaining):
                    speed = max(self._speed - a * dt, a * dt)
                else:
                    speed = min(self._speed + a * dt, cfg.max_speed_deg_s)
                new = self._motor + math.copysign(min(speed * dt, abs(remaining)), remaining)
                if self._stall_at is not None:  # jammed platter: motor cannot pass this point
                    new = min(new, self._stall_at) if remaining > 0 else max(new, self._stall_at)
                self._motor, self._speed = new, speed
                if abs(self._target - new) < 1e-9:
                    self._arrive()
        # Backlash: the platter lies in [motor, motor + backlash]; clockwise motion pushes it.
        self._platter = min(max(self._platter, self._motor), self._motor + cfg.backlash_deg)
        if self._estop_input():
            self._halt()
        if self._silent():
            return
        ring = 0.0
        if not self._moving and self._ring_start is not None:
            age = self._now - self._ring_start
            ring = (
                cfg.ring_amplitude_deg
                * math.exp(-age / cfg.ring_decay_s)
                * math.cos(2 * math.pi * cfg.ring_frequency_hz * age)
            )
        measured = (
            self._platter
            + self._offset
            + ring
            + self._rng.gauss(0.0, cfg.jitter_sigma_deg)
            + self._faults.encoder_drift_deg_per_s * self._now
        )
        self._report_seq += 1
        report = StatusReport(self._report_seq, _norm(measured), self._moving, self._estop_input())
        if not self._faults.out_of_order_status:
            self._queue(self._now, report)
        elif self._held is None:
            self._held = report
        else:
            self._queue(self._now, report)
            self._queue(self._now, self._held)
            self._held = None

    def _arrive(self) -> None:
        assert self._target is not None
        self._motor, self._speed, self._target = self._target, 0.0, None
        self._platter = min(max(self._platter, self._motor), self._motor + self._cfg.backlash_deg)
        if self._homing:
            self._offset, self._homing = -self._motor, False
        self._moving = self._stuck  # a stuck controller keeps reporting "moving"
        self._ring_start = self._now


# -- capture plan -------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TurntableCapturePlanResult:
    mode: Literal["TURNTABLE_DEVICE_REPORTED_ANGLES", "MANUAL_CAPTURE_NO_ANGLE_AUTHORITY"]
    stop_count: int
    angle_events: tuple[TurntableAngleEvent, ...]  # settled stops only, before any fault
    fallback_reason: str | None
    limitations: tuple[str, ...] = LIMITATIONS


def run_turntable_capture_plan(
    driver: TurntableDriver,
    *,
    stop_count: int,
    first_sequence: int,
    capture: Callable[[int], object],
    source_id: str,
    enabled: bool | None = None,
) -> TurntableCapturePlanResult:
    """Stop at ``360 * i / stop_count``; after each settle call ``capture(sequence)``.

    ``enabled=None`` reads the feature flag (default off); otherwise it must be a bool.
    Disabled or any refusal/fault: return manual-capture fallback with no angle
    authority for the remaining stops; events already settled stay valid and bound by
    sequence. Frames captured manually get no event, so PL-0426 leaves them unbound.
    """
    if isinstance(stop_count, bool) or not isinstance(stop_count, int):
        raise TurntableCommandError("stop_count_invalid")
    if not 1 <= stop_count <= 720:
        raise TurntableCommandError("stop_count_invalid")
    if (
        not isinstance(first_sequence, int)
        or isinstance(first_sequence, bool)
        or first_sequence < 0
    ):
        raise TurntableCommandError("first_sequence_invalid")
    if enabled is None:
        enabled = turntable_driver_enabled()
    if type(enabled) is not bool:
        raise TurntableCommandError("enabled_invalid")
    events: list[TurntableAngleEvent] = []

    def fallback(reason: str) -> TurntableCapturePlanResult:
        return TurntableCapturePlanResult(
            "MANUAL_CAPTURE_NO_ANGLE_AUTHORITY", stop_count, tuple(events), reason
        )

    if not enabled:
        return fallback("feature_disabled")
    if driver.state is _S.DISCONNECTED and not (result := driver.connect()).ok:
        return fallback(f"connect_failed:{result.reason_code}")
    if driver.state is not _S.IDLE:
        return fallback(f"driver_not_ready:{driver.state}")
    if not driver.homed and not (result := driver.home()).ok:
        return fallback(f"home_failed:{result.reason_code}")
    for index in range(stop_count):
        result = driver.rotate_to(360.0 * index / stop_count)
        if not result.ok or result.settled is None:
            return fallback(f"stop_{index}_failed:{result.reason_code}")
        sequence = first_sequence + index
        capture(sequence)
        events.append(result.settled.to_angle_event(sequence, source_id))
    return TurntableCapturePlanResult(
        "TURNTABLE_DEVICE_REPORTED_ANGLES", stop_count, tuple(events), None
    )


__all__ = [
    "LIMITATIONS",
    "TURNTABLE_DRIVER_CONTRACT",
    "TURNTABLE_DRIVER_FLAG_ENV",
    "Ack",
    "AcknowledgementRequiredError",
    "CommandFrame",
    "CommandResult",
    "DriverEvent",
    "IllegalTransitionError",
    "MotionRefusedError",
    "NotHomedError",
    "SettledAngle",
    "SimulatedFaults",
    "SimulatedTurntableConfig",
    "SimulatedTurntableTransport",
    "StatusReport",
    "TurntableCapturePlanResult",
    "TurntableCommandError",
    "TurntableDriver",
    "TurntableDriverError",
    "TurntableState",
    "TurntableTransport",
    "TurntableTransportDisconnected",
    "run_turntable_capture_plan",
]
