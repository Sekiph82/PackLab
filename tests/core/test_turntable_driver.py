"""PL-0425 tests: simulated turntable driver, safety state machine, PL-0426 integration.

Everything runs on a virtual clock with seeded RNGs; no hardware, no real sleeps.
"""

from __future__ import annotations

import random

import pytest

from packlab_core.config import ConfigError
from packlab_core.turntable_driver import (
    Ack,
    AcknowledgementRequiredError,
    CommandFrame,
    IllegalTransitionError,
    Message,
    MotionRefusedError,
    NotHomedError,
    SimulatedFaults,
    SimulatedTurntableTransport,
    StatusReport,
    TurntableCommandError,
    TurntableDriver,
    TurntableState,
    run_turntable_capture_plan,
    turntable_driver_enabled,
)
from packlab_core.turntable_sync import TurntableAngleEvent, synchronize_turntable_angles

SOURCE = "SYNTHETIC-turntable-sim"
S = TurntableState


def _ready(seed: int = 7, **faults: object) -> tuple[TurntableDriver, SimulatedTurntableTransport]:
    sim = SimulatedTurntableTransport(seed=seed, faults=SimulatedFaults(**faults))  # type: ignore[arg-type]
    driver = TurntableDriver(sim)
    assert driver.connect().ok
    assert driver.home().ok
    return driver, sim


def _motion_frames(sim: SimulatedTurntableTransport) -> int:
    return sum(frame.verb in ("MOVE", "HOME") for frame in sim.frames)


def _advance(sim: SimulatedTurntableTransport, until_s: float) -> None:
    while sim.now() < until_s:
        sim.receive(until_s - sim.now())


class Scripted:
    """Ack every frame; then replay status positions, 20 ms apart."""

    def __init__(self, positions: list[tuple[float, bool]], *, reject: bool = False) -> None:
        self.positions, self.clock, self.seq = list(positions), 0.0, 0
        self.reject = reject
        self.queue: list[Message] = []

    def open(self, timeout_s: float) -> None:
        self.queue.append(StatusReport(0, 123.0, False))

    def close(self) -> None:
        pass

    def send(self, frame: CommandFrame) -> None:
        accepted = not (self.reject and frame.verb in ("HOME", "MOVE"))
        self.queue.append(Ack(frame.command_id, accepted))

    def receive(self, timeout_s: float) -> Message | None:
        if self.queue:
            return self.queue.pop(0)
        self.clock += min(0.02, timeout_s)
        if not self.positions:
            return None
        self.seq += 1
        position, moving = self.positions.pop(0)
        return StatusReport(self.seq, position, moving)

    def now(self) -> float:
        return self.clock


# -- happy path ---------------------------------------------------------------------


def test_happy_path_settles_within_tolerance_and_ccw_moves_finish_clockwise() -> None:
    driver, sim = _ready()
    assert driver.state is S.IDLE and driver.homed
    for angle in (10.0, 20.0, 350.0, 5.0):
        result = driver.rotate_to(angle)
        assert result.ok and result.state is S.IDLE
        assert result.settled is not None
        assert result.settled.commanded_angle_deg == angle
        assert result.settled.sample_count == driver.settle_samples
        assert result.settled.max_abs_error_deg <= driver.settle_tolerance_deg
        kinds = [event.kind for event in result.events]
        assert kinds.count("SETTLED") == 1 and "FAULT" not in kinds
    before = len(sim.frames)
    result = driver.rotate_by(-30.0)
    assert result.ok and result.settled is not None
    assert result.settled.commanded_angle_deg == pytest.approx(335.0)
    legs = [frame.target_deg for frame in sim.frames[before:] if frame.verb == "MOVE"]
    # Continuous device angle is 365 after 350 -> 5 (clockwise). Anti-backlash: overshoot
    # counter-clockwise past the target, then a clockwise final approach.
    assert legs == pytest.approx([335.0 - driver.anti_backlash_deg, 335.0])


def test_settled_requires_n_consecutive_in_tolerance_not_moving_samples() -> None:
    script = [(200.0, True), (300.0, True), (0.1, False), (359.9, False), (0.5, False)]
    script += [(0.1, False), (0.05, False), (359.95, False), (0.0, False)]
    transport = Scripted(script)
    driver = TurntableDriver(transport, settle_samples=3)
    assert driver.connect().ok
    result = driver.home()
    assert result.ok and result.settled is not None
    # The 0.5-degree sample breaks the run; settle needs the 3 samples after it.
    assert result.settled.time_s == pytest.approx(0.02 * 8)
    assert result.settled.measured_angle_deg == pytest.approx((0.1 + 0.05 - 0.05) / 3)
    assert transport.positions == [(0.0, False)]
    # Review P3-4: the PL-0426 event must keep commanded and measured in their own fields.
    event = result.settled.to_angle_event(5, SOURCE)
    assert event == TurntableAngleEvent(5, 0.0, result.settled.measured_angle_deg, SOURCE)
    assert event.commanded_angle_deg == 0.0 and event.measured_angle_deg != 0.0

    flicker = Scripted([(0.1, False), (0.5, False)] * 400)
    driver = TurntableDriver(flicker, settle_samples=3)
    driver.connect()
    result = driver.home(timeout_s=2.0)
    assert not result.ok and result.reason_code == "settle_timeout" and result.settled is None
    assert driver.state is S.FAULT and not driver.homed


# -- fault classes ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("faults", "reason", "state"),
    [
        ({"stall_on_move": 1}, "stall_detected", S.FAULT),
        ({"stuck_moving_on_move": 1}, "stuck_moving", S.FAULT),
        ({"drop_ack_frames": frozenset({2})}, "ack_timeout", S.FAULT),
        ({"silent_after_s": 3.2}, "status_timeout", S.FAULT),
        ({"disconnect_at_s": 3.2}, "transport_disconnected", S.DISCONNECTED),
        ({"estop_input_at_s": 3.2}, "device_estop_input", S.ESTOP_LATCHED),
    ],
)
def test_each_fault_class_halts_and_refuses_motion_until_rehomed(
    faults: dict[str, object], reason: str, state: TurntableState
) -> None:
    driver, sim = _ready(**faults)
    result = driver.rotate_to(90.0)
    assert not result.ok and result.reason_code == reason and result.settled is None
    assert driver.state is state and result.state is state and not driver.homed
    frames = _motion_frames(sim)
    for command in (lambda: driver.rotate_to(10.0), lambda: driver.rotate_by(5.0), driver.home):
        with pytest.raises(MotionRefusedError):
            command()
    assert _motion_frames(sim) == frames
    if state is S.FAULT:
        assert sim.frames[-1].verb == "STOP"  # best-effort halt after the fault
    if reason == "status_timeout":  # a silent device cannot be reset
        refused = driver.reset_fault(driver.acknowledge("operator-1"))
        assert not refused.ok and refused.reason_code == "status_timeout"
        assert driver.state is S.FAULT
    elif state is S.FAULT:
        assert driver.reset_fault(driver.acknowledge("operator-1")).ok
        assert driver.state is S.IDLE
        with pytest.raises(NotHomedError):
            driver.rotate_to(10.0)


def test_disconnect_then_reconnect_requires_rehome() -> None:
    driver, _ = _ready(disconnect_at_s=3.2)
    assert driver.rotate_to(90.0).reason_code == "transport_disconnected"
    assert driver.status().reason_code == "disconnected"
    assert driver.connect().ok and driver.state is S.IDLE
    with pytest.raises(NotHomedError):
        driver.rotate_to(90.0)
    assert driver.home().ok and driver.rotate_to(90.0).ok


def test_encoder_drift_is_caught_by_the_settle_check_and_never_emitted() -> None:
    driver, sim = _ready(encoder_drift_deg_per_s=0.03)
    captured: list[int] = []
    plan = run_turntable_capture_plan(
        driver,
        stop_count=24,
        first_sequence=0,
        capture=captured.append,
        source_id=SOURCE,
        enabled=True,
    )
    assert plan.mode == "MANUAL_CAPTURE_NO_ANGLE_AUTHORITY"
    assert plan.fallback_reason is not None and plan.fallback_reason.endswith("settle_timeout")
    assert 0 < len(plan.angle_events) < 24 and len(captured) == len(plan.angle_events)
    for event in plan.angle_events:
        assert event.measured_angle_deg is not None
        assert abs(event.measured_angle_deg - event.commanded_angle_deg) <= 0.2


def test_duplicate_acks_and_out_of_order_status_are_tolerated_and_logged() -> None:
    driver, _ = _ready(duplicate_acks=True)
    result = driver.rotate_to(45.0)
    assert result.ok and any(e.kind == "UNEXPECTED_ACK_IGNORED" for e in driver.events)
    driver, _ = _ready(out_of_order_status=True)
    result = driver.rotate_to(45.0)
    assert result.ok and any(e.kind == "STALE_STATUS_DROPPED" for e in result.events)


def test_connect_to_a_silent_device_fails_cleanly() -> None:
    sim = SimulatedTurntableTransport(seed=1, faults=SimulatedFaults(silent_after_s=0.0))
    driver = TurntableDriver(sim)
    result = driver.connect()
    assert not result.ok and result.reason_code == "status_timeout"
    assert driver.state is S.DISCONNECTED and sim.frames == []


# -- state machine ------------------------------------------------------------------


def test_illegal_transitions_and_bad_arguments_raise_typed_errors() -> None:
    sim = SimulatedTurntableTransport(seed=3)
    driver = TurntableDriver(sim)
    with pytest.raises(MotionRefusedError):
        driver.rotate_to(10.0)
    with pytest.raises(MotionRefusedError):
        driver.home()
    with pytest.raises(IllegalTransitionError):
        driver.stop()
    with pytest.raises(IllegalTransitionError):
        driver.acknowledge("operator-1")
    with pytest.raises(IllegalTransitionError):
        driver.reset_fault("token")
    driver.connect()
    with pytest.raises(IllegalTransitionError):
        driver.connect()
    with pytest.raises(NotHomedError):
        driver.rotate_by(10.0)
    driver.home()
    for bad in (360.0, -0.1, float("nan"), True):
        with pytest.raises(TurntableCommandError):
            driver.rotate_to(bad)  # type: ignore[arg-type]
    with pytest.raises(TurntableCommandError):
        driver.rotate_by(400.0)
    with pytest.raises(TurntableCommandError):
        driver.rotate_to(10.0, timeout_s=0.0)
    assert sim.frames[-1].verb == "HOME"  # nothing invalid reached the device
    assert driver.stop().ok and driver.state is S.IDLE


def test_estop_latches_until_acknowledged_reset_and_survives_disconnect() -> None:
    driver, sim = _ready(disconnect_at_s=6.0)
    result = driver.emergency_stop()
    assert result.ok and driver.state is S.ESTOP_LATCHED and not driver.homed
    assert sim.frames[-1].verb == "ESTOP"
    assert any("HARDWARE_ESTOP_CIRCUIT_NOT_VALIDATED" in item for item in result.limitations)
    with pytest.raises(MotionRefusedError):
        driver.rotate_to(10.0)
    with pytest.raises(AcknowledgementRequiredError):
        driver.reset_fault("guess")
    token = driver.acknowledge("operator-1")
    with pytest.raises(AcknowledgementRequiredError):
        driver.reset_fault(token + "x")
    with pytest.raises(AcknowledgementRequiredError):
        driver.reset_fault(token)  # a failed attempt consumes the token
    assert driver.stop().ok and driver.state is S.ESTOP_LATCHED  # stop never clears it
    _advance(sim, 5.99)  # the status poll below crosses the 6.0 s link drop
    assert driver.status().reason_code == "transport_disconnected"
    assert driver.state is S.ESTOP_LATCHED  # the latch survives link loss
    assert driver.connect().ok and driver.state is S.ESTOP_LATCHED
    assert driver.reset_fault(driver.acknowledge("operator-1")).ok
    assert driver.state is S.IDLE and not driver.homed
    assert driver.home().ok and driver.rotate_to(30.0).ok


def test_estop_without_a_link_still_latches_and_reset_waits_for_a_released_input() -> None:
    driver = TurntableDriver(SimulatedTurntableTransport(seed=2))
    result = driver.emergency_stop()
    assert not result.ok and result.reason_code == "estop_not_sent_disconnected"
    assert driver.state is S.ESTOP_LATCHED
    assert driver.reset_fault(driver.acknowledge("op")).ok and driver.state is S.DISCONNECTED

    driver, sim = _ready(estop_input_at_s=3.2, estop_input_release_s=6.0)
    assert driver.rotate_to(90.0).reason_code == "device_estop_input"
    refused = driver.reset_fault(driver.acknowledge("op"))
    assert not refused.ok and driver.state is S.ESTOP_LATCHED
    _advance(sim, 6.0)
    assert driver.reset_fault(driver.acknowledge("op")).ok and driver.state is S.IDLE


def test_property_no_motion_command_is_accepted_in_fault_or_estop() -> None:
    rng = random.Random(425)
    for trial in range(40):
        if trial % 2:
            driver, sim = _ready(seed=trial)
            driver.emergency_stop()
            expected = S.ESTOP_LATCHED
        else:
            driver, sim = _ready(seed=trial, drop_ack_frames=frozenset({2}))
            driver.rotate_to(rng.uniform(0.0, 359.0))
            expected = S.FAULT
        assert driver.state is expected
        frames = _motion_frames(sim)
        for _ in range(10):
            choice = rng.randrange(3)
            with pytest.raises(MotionRefusedError):
                if choice == 0:
                    driver.rotate_to(rng.uniform(0.0, 359.999))
                elif choice == 1:
                    driver.rotate_by(rng.uniform(-360.0, 360.0))
                else:
                    driver.home()
            assert driver.state is expected
        assert _motion_frames(sim) == frames


def test_same_seed_gives_identical_events_and_angles() -> None:
    def run(seed: int) -> tuple[object, ...]:
        driver, _ = _ready(seed=seed, out_of_order_status=True)
        settled = [driver.rotate_to(angle).settled for angle in (15.0, 200.0, 90.0)]
        return (driver.events, tuple(settled))

    assert run(11) == run(11)
    assert run(11) != run(12)


# -- feature flag and PL-0426 integration --------------------------------------------


def test_feature_flag_defaults_off_and_parses_strictly() -> None:
    assert turntable_driver_enabled({}) is False
    assert turntable_driver_enabled({"PACKLAB_TURNTABLE_DRIVER_ENABLED": "TRUE"}) is True
    assert turntable_driver_enabled({"PACKLAB_TURNTABLE_DRIVER_ENABLED": "false"}) is False
    with pytest.raises(ConfigError):
        turntable_driver_enabled({"PACKLAB_TURNTABLE_DRIVER_ENABLED": "yes"})


def test_disabled_plan_falls_back_to_manual_capture_without_touching_the_device(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PACKLAB_TURNTABLE_DRIVER_ENABLED", raising=False)
    with pytest.raises(TurntableCommandError):  # review P3-3: a truthy string is not a bool
        run_turntable_capture_plan(
            TurntableDriver(SimulatedTurntableTransport(seed=5)),
            stop_count=4,
            first_sequence=0,
            capture=print,
            source_id=SOURCE,
            enabled="false",  # type: ignore[arg-type]
        )
    sim = SimulatedTurntableTransport(seed=5)
    plan = run_turntable_capture_plan(
        TurntableDriver(sim), stop_count=24, first_sequence=0, capture=print, source_id=SOURCE
    )
    assert plan.mode == "MANUAL_CAPTURE_NO_ANGLE_AUTHORITY"
    assert plan.fallback_reason == "feature_disabled" and plan.angle_events == ()
    assert sim.frames == [] and sim.now() == 0.0
    photos = tuple((f"manual-{index}", index) for index in range(24))
    report = synchronize_turntable_angles(photos, plan.angle_events)
    assert report["bound_photos"] == [] and report["status"] == "INCOMPLETE"


@pytest.mark.parametrize("stop_count", [24, 36])
def test_end_to_end_driver_events_bind_every_photo(stop_count: int) -> None:
    sim = SimulatedTurntableTransport(seed=stop_count)
    photos: list[tuple[str, int]] = []
    plan = run_turntable_capture_plan(
        TurntableDriver(sim),
        stop_count=stop_count,
        first_sequence=100,
        capture=lambda sequence: photos.append((f"photo-{sequence}", sequence)),
        source_id=SOURCE,
        enabled=True,
    )
    assert plan.mode == "TURNTABLE_DEVICE_REPORTED_ANGLES" and plan.fallback_reason is None
    assert all(type(event) is TurntableAngleEvent for event in plan.angle_events)
    report = synchronize_turntable_angles(tuple(photos), plan.angle_events)
    assert report["status"] == "COMPLETE" and report["frame_count"] == stop_count
    bound = report["bound_photos"]
    assert all(item["angle_source"] == "DEVICE_MEASURED" for item in bound)
    assert report["largest_angular_gap_deg"] == pytest.approx(360.0 / stop_count, abs=0.5)
    for index, item in enumerate(bound):
        params = item["capture_mode_parameters"]
        assert params["frame_index"] == index
        assert params["angle_convention"] == "clockwise_from_reference"
        error = (params["angle_deg"] - 360.0 * index / stop_count + 180.0) % 360.0 - 180.0
        assert abs(error) <= 0.2


def test_mid_plan_fault_keeps_settled_events_and_leaves_the_rest_unbound() -> None:
    sim = SimulatedTurntableTransport(seed=9, faults=SimulatedFaults(stall_on_move=5))
    photos: list[tuple[str, int]] = []
    plan = run_turntable_capture_plan(
        TurntableDriver(sim),
        stop_count=24,
        first_sequence=0,
        capture=lambda sequence: photos.append((f"photo-{sequence}", sequence)),
        source_id=SOURCE,
        enabled=True,
    )
    assert plan.mode == "MANUAL_CAPTURE_NO_ANGLE_AUTHORITY"
    assert plan.fallback_reason == "stop_4_failed:stall_detected"
    assert [event.sequence for event in plan.angle_events] == [0, 1, 2, 3]
    photos += [(f"manual-{index}", index) for index in range(4, 24)]  # operator fallback
    report = synchronize_turntable_angles(tuple(photos), plan.angle_events)
    assert len(report["bound_photos"]) == 4
    assert {item["reason_code"] for item in report["unbound_photos"]} == {"no_angle_event"}


# -- review M19-C018 V01 follow-ups -------------------------------------------------


def test_device_rejected_ack_faults_the_driver() -> None:
    driver = TurntableDriver(Scripted([(0.0, False)] * 50, reject=True))
    assert driver.connect().ok
    result = driver.home()
    assert not result.ok and result.reason_code == "command_rejected_by_device"
    assert driver.state is S.FAULT and not driver.homed


def test_settling_returns_to_motion_state_when_the_table_moves_again() -> None:
    script = [(5.0, True), (1.0, False), (0.5, True), (0.0, False), (0.0, False), (0.0, False)]
    driver = TurntableDriver(Scripted(script), settle_samples=3)
    driver.connect()
    result = driver.home()
    assert result.ok
    states = [e.detail for e in result.events if e.kind == "STATE_CHANGED"]
    assert states == ["HOMING", "SETTLING", "HOMING", "SETTLING", "IDLE"]


def test_unexpected_transport_exception_halts_faults_and_clears_homed() -> None:
    class Flaky(SimulatedTurntableTransport):
        def receive(self, timeout_s: float) -> Message | None:
            if self.now() > 3.3:
                raise OSError("usb stack error")
            return super().receive(timeout_s)

    sim = Flaky(seed=7)
    driver = TurntableDriver(sim)
    assert driver.connect().ok and driver.home().ok
    result = driver.rotate_to(120.0)
    assert not result.ok and result.reason_code == "transport_error:OSError"
    assert driver.state is S.FAULT and not driver.homed
    assert sim.frames[-1].verb == "STOP"
    with pytest.raises(MotionRefusedError):
        driver.rotate_to(10.0)


def test_latch_invalidates_a_token_acknowledged_for_an_earlier_fault() -> None:
    driver, _ = _ready(drop_ack_frames=frozenset({2}))
    assert driver.rotate_to(90.0).reason_code == "ack_timeout"
    token = driver.acknowledge("operator-1")
    driver.emergency_stop()
    with pytest.raises(AcknowledgementRequiredError):
        driver.reset_fault(token)
    assert driver.state is S.ESTOP_LATCHED


def test_cross_thread_estop_request_preempts_a_running_move() -> None:
    holder: list[TurntableDriver] = []

    class Operator(SimulatedTurntableTransport):
        def receive(self, timeout_s: float) -> Message | None:
            if 3.5 < self.now() and len(holder) == 1:
                holder.append(holder[0])  # one press only
                holder[0].request_emergency_stop()  # e.g. a UI thread pressing STOP
            return super().receive(timeout_s)

    sim = Operator(seed=7)
    driver = TurntableDriver(sim)
    holder.append(driver)
    assert driver.connect().ok and driver.home().ok
    result = driver.rotate_to(180.0)
    assert not result.ok and result.reason_code == "operator_software_estop"
    assert driver.state is S.ESTOP_LATCHED and sim.frames[-1].verb == "ESTOP"
    assert result.elapsed_s < 1.0  # did not wait for the 180-degree move to finish
    assert driver.reset_fault(driver.acknowledge("operator-1")).ok
    assert driver.home().ok and driver.rotate_to(10.0).ok  # request was consumed once


def test_connect_failures_while_latched_and_device_estop_on_connect() -> None:
    # P3-1: a failed reconnect while latched must leave the driver disconnected.
    sim = SimulatedTurntableTransport(seed=4, faults=SimulatedFaults(silent_after_s=0.0))
    driver = TurntableDriver(sim)
    driver.emergency_stop()
    assert driver.connect().reason_code == "status_timeout"
    assert driver.state is S.ESTOP_LATCHED
    assert driver.connect().reason_code == "status_timeout"  # not "already_connected"
    # P3-2: an asserted device e-stop input during connect latches.
    sim = SimulatedTurntableTransport(seed=4, faults=SimulatedFaults(estop_input_at_s=0.0))
    driver = TurntableDriver(sim)
    result = driver.connect()
    assert not result.ok and result.reason_code == "device_estop_input"
    assert driver.state is S.ESTOP_LATCHED
    assert any("HARDWARE_ESTOP_CIRCUIT_NOT_VALIDATED" in item for item in result.limitations)
    assert any("SINGLE_THREADED_NO_PREEMPTIVE" in item for item in result.limitations)
    assert any("DEVICE_ROTATION_DIRECTION_UNVERIFIED" in item for item in result.limitations)
