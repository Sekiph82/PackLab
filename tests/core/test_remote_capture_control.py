"""PL-0429 remote capture control: contract, auth, state machine and fault injection.

Software-only evidence. No iPhone, LAN or device TLS is exercised here.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import itertools
import json
import pickle
import random
import secrets
from typing import Any

import pytest

from packlab_core.pairing import PairingStore
from packlab_core.remote_capture_control import (
    COMMAND_SCHEMA,
    MAX_COMMAND_BYTES,
    MAX_PENDING,
    MAX_PLAN_STEPS,
    MAX_SEQ,
    REJECTION_MEMORY,
    RESPONSE_SCHEMA,
    DeviceState,
    MockIPhoneCaptureEndpoint,
    RemoteCaptureController,
    RemoteCaptureError,
    _strict_loads,
    require_lan_peer,
)
from packlab_core.remote_capture_control import (
    RemoteCaptureErrorCode as Code,
)
from packlab_core.transfer_protocol import canonical_json
from packlab_core.transfer_security import PairingAuthenticator

PIN = "a" * 64
DEVICE = "iphone-16-a"
LAN_PEER = "192.168.1.10"


class Rig:
    """Paired controller + mock device sharing a deterministic clock."""

    def __init__(
        self, *, ttl: int = 300, rate: int = 10, device: str = DEVICE, peer: str = "192.168.1.20"
    ) -> None:
        self.now = [1_000.0]
        clock = lambda: self.now[0]  # noqa: E731
        store = PairingStore(clock=clock)
        self.auth = PairingAuthenticator(store, clock=clock, session_ttl_seconds=ttl)
        offer = store.create_offer(
            receiver_instance_id="studio-1",
            host=LAN_PEER,
            port=8443,
            tls_certificate_fingerprint=PIN,
        )
        self.cred = self.auth.authenticate_pairing(
            offer,
            receiver_instance_id="studio-1",
            pairing_code=offer.pairing_code,
            certificate_fingerprint_value=PIN,
        )
        counter = itertools.count(1)
        self.ctl = RemoteCaptureController(
            self.auth,
            self.cred,
            device_id=device,
            peer_address=peer,
            clock=clock,
            nonce_source=lambda: f"{next(counter):032x}",
            enabled=True,
        )
        self.dev = MockIPhoneCaptureEndpoint(
            self.cred,
            device_id=DEVICE,
            clock=clock,
            monotonic=clock,
            enabled=True,
            max_commands_per_second=rate,
        )

    def deliver(self, wire: bytes) -> bytes:
        return self.dev.handle(wire, peer_address=LAN_PEER)

    def send(self, command: str, args: dict[str, Any] | None = None) -> Any:
        self.now[0] += 0.15  # stay under the default 10 commands/s device rate limit
        return self.ctl.accept_response(self.deliver(self.ctl.build(command, args)))


def _plan(*angles_mdeg: int) -> dict[str, Any]:
    return {"steps": [{"ring_id": "ring-0", "turntable_angle_mdeg": a} for a in angles_mdeg]}


def _edit(wire: bytes, **changes: Any) -> bytes:
    value = json.loads(wire)
    value.update(changes)
    return canonical_json(value)


def _device_code(rig: Rig, response: bytes) -> Code:
    with pytest.raises(RemoteCaptureError) as caught:
        rig.ctl.accept_response(response)
    assert caught.value.code is Code.DEVICE_REJECTED_UNAUTHENTICATED
    assert caught.value.device_code is not None
    return caught.value.device_code


def _wire_code(response: bytes) -> str:
    value = json.loads(response)
    assert set(value) == {"schema", "status", "error_code"}  # unsigned rejection
    return str(value["error_code"])


def _forged(rig: Rig, command: str, mutate: Any) -> bytes:
    """A MAC-valid response from the correctly keyed device whose content is mutated."""
    if command == "capture_frame":
        rig.send("start_session", {"capture_mode": "turntable"})
    value = json.loads(rig.deliver(rig.ctl.build(command)))
    value.pop("mac")
    mutate(value)
    assert rig.dev._keys is not None
    return canonical_json({**value, "mac": rig.dev._keys.mac("device_to_controller", value)})


def test_happy_path_turntable_plan_session() -> None:
    rig = Rig()
    assert (
        rig.send("start_session", {"capture_mode": "turntable"}).state is DeviceState.SESSION_OPEN
    )
    assert rig.send("set_capture_plan", _plan(0, 120_000, 240_000)).result["plan_steps_total"] == 3
    frames = [rig.send("capture_frame").result["frame"] for _ in range(3)]
    assert [f["frame_index"] for f in frames] == [0, 1, 2]
    assert [f["planned_turntable_angle_mdeg"] for f in frames] == [0, 120_000, 240_000]
    assert [f["plan_step"] for f in frames] == [0, 1, 2]
    for frame in frames:
        assert frame["measurement_authority"] is False
        assert frame["scan_master_authority"] is False
        assert frame["capture_metadata_status"] == "placeholder_not_measured"
    done = rig.send("capture_frame")
    assert (done.status, done.error_code) == ("rejected", Code.CAPTURE_PLAN_COMPLETE)
    assert rig.dev.frames_captured == 3
    assert rig.send("pause").state is DeviceState.PAUSED
    assert rig.send("set_capture_plan", _plan(90_000)).result["plan_steps_remaining"] == 1
    assert rig.send("resume").state is DeviceState.CAPTURING
    assert rig.send("capture_frame").result["frame"]["frame_index"] == 3
    status = rig.send("query_status")
    assert status.result["frames_captured"] == 4 and status.result["capture_mode"] == "turntable"
    assert rig.send("end_session").state is DeviceState.CLOSED
    assert rig.send("query_status").state is DeviceState.CLOSED
    assert rig.ctl.last_state is DeviceState.CLOSED and rig.ctl.pending_seqs == ()


def test_free_capture_without_plan_has_no_planned_angle() -> None:
    rig = Rig()
    rig.send("start_session", {"capture_mode": "freehand"})
    frame = rig.send("capture_frame").result["frame"]
    assert frame["plan_step"] is None and frame["planned_turntable_angle_mdeg"] is None


@pytest.mark.parametrize(
    ("setup", "command", "args"),
    [
        ([], "capture_frame", None),
        ([], "pause", None),
        ([], "resume", None),
        ([], "end_session", None),
        ([], "set_capture_plan", _plan(0)),
        (
            [("start_session", {"capture_mode": "turntable"})],
            "start_session",
            {"capture_mode": "turntable"},
        ),
        ([("start_session", {"capture_mode": "turntable"})], "resume", None),
        (
            [("start_session", {"capture_mode": "turntable"}), ("capture_frame", None)],
            "set_capture_plan",
            _plan(0),
        ),
        (
            [("start_session", {"capture_mode": "turntable"}), ("end_session", None)],
            "start_session",
            {"capture_mode": "turntable"},
        ),
        (
            [("start_session", {"capture_mode": "turntable"}), ("end_session", None)],
            "capture_frame",
            None,
        ),
    ],
)
def test_illegal_transitions_are_signed_rejections_without_state_change(
    setup: list[tuple[str, dict[str, Any] | None]], command: str, args: dict[str, Any] | None
) -> None:
    rig = Rig()
    for step, step_args in setup:
        assert rig.send(step, step_args).status == "ok"
    before = rig.dev.state
    response = rig.send(command, args)
    assert (response.status, response.error_code) == ("rejected", Code.ILLEGAL_TRANSITION)
    assert rig.dev.state is before is response.state


def test_feature_flag_defaults_off_on_both_sides() -> None:
    rig = Rig()
    with pytest.raises(RemoteCaptureError, match="feature_disabled"):
        RemoteCaptureController(rig.auth, rig.cred, device_id=DEVICE, peer_address=LAN_PEER)
    off = MockIPhoneCaptureEndpoint(rig.cred, device_id=DEVICE, clock=lambda: rig.now[0])
    assert (
        _device_code(rig, off.handle(rig.ctl.build("query_status"), peer_address=LAN_PEER))
        is Code.FEATURE_DISABLED
    )


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.1.2.3",
        "172.20.10.2",
        "192.168.0.5",
        "169.254.3.4",
        "::1",
        "fd00::1",
        "fe80::1",
        "::ffff:192.168.1.2",
        "169.254.169.254",  # documented: link-local incl. metadata literal is admitted
        "fe80::1%eth0",  # documented: IPv6 zone ids are admitted
    ],
)
def test_lan_policy_accepts_loopback_private_and_link_local(address: str) -> None:
    require_lan_peer(address)


@pytest.mark.parametrize(
    "address",
    [
        "8.8.8.8",
        "100.64.0.1",
        "0.0.0.0",
        "255.255.255.255",
        "224.0.0.1",
        "192.0.2.1",
        "2001:db8::1",
        "::ffff:8.8.8.8",
        "localhost",
        "iphone.local",
        "",
    ],
)
def test_lan_policy_rejects_public_special_and_hostnames(address: str) -> None:
    with pytest.raises(RemoteCaptureError, match="non_lan_peer"):
        require_lan_peer(address)


def test_non_lan_peers_are_rejected_on_both_sides() -> None:
    rig = Rig()
    with pytest.raises(RemoteCaptureError, match="non_lan_peer"):
        RemoteCaptureController(
            rig.auth, rig.cred, device_id=DEVICE, peer_address="8.8.8.8", enabled=True
        )
    response = rig.dev.handle(rig.ctl.build("query_status"), peer_address="203.0.113.9")
    assert _device_code(rig, response) is Code.NON_LAN_PEER


def _tampered_variants(wire: bytes) -> list[tuple[bytes, Code]]:
    value = json.loads(wire)
    flipped = ("0" if value["mac"][0] != "0" else "1") + value["mac"][1:]
    extra = canonical_json({**value, "debug": True})
    return [
        (_edit(wire, args={"capture_mode": "freehand"}), Code.BAD_MAC),
        (_edit(wire, mac=flipped), Code.BAD_MAC),
        (_edit(wire, issued_at_ms=value["issued_at_ms"] + 1), Code.BAD_MAC),
        (_edit(wire, seq=value["seq"] + 5), Code.BAD_MAC),
        (_edit(wire, session_id="f" * 32), Code.UNAUTHENTICATED),
        (_edit(wire, device_id="iphone-other"), Code.UNAUTHENTICATED),
        (_edit(wire, controller_id="studio-evil"), Code.UNAUTHENTICATED),
        (_edit(wire, args={"capture_mode": ["turntable"]}), Code.BAD_ARGS),
        (_edit(wire, args={"capture_mode": {"a": 1}}), Code.BAD_ARGS),
        (wire.replace(b'"studio-1"', rb'"\ud800"'), Code.MALFORMED),  # lone surrogate
        (_edit(wire, mac="é" * 64), Code.MALFORMED),
        (_edit(wire, command="format_disk"), Code.UNKNOWN_COMMAND),
        (_edit(wire, schema="packlab.remote-capture-command.v2"), Code.MALFORMED),
        (_edit(wire, seq=True), Code.MALFORMED),
        (extra, Code.MALFORMED),
        (wire.replace(b",", b", ", 1), Code.NON_CANONICAL),
        (json.dumps(value, sort_keys=False).encode(), Code.NON_CANONICAL),
        (wire.replace(b'"seq":1', b'"seq":1.0'), Code.MALFORMED),
        (wire.replace(b'"seq":1', b'"seq":NaN'), Code.MALFORMED),
        (wire.replace(b'{"args"', b'{"seq":1,"args"'), Code.MALFORMED),
        (b"[]\n", Code.MALFORMED),
        (b"\xff\xfe", Code.MALFORMED),
        (b"[" * 5000, Code.MALFORMED),
        (b" " * (MAX_COMMAND_BYTES + 1), Code.OVERSIZED),
    ]


def test_every_tampered_command_is_rejected_before_execution() -> None:
    rig = Rig()
    wire = rig.ctl.build("start_session", {"capture_mode": "turntable"})
    for variant, expected in _tampered_variants(wire):
        assert _device_code(rig, rig.deliver(variant)) is expected, expected
    assert rig.dev.state is DeviceState.IDLE
    # Rejected forgeries consume nothing: the genuine command still executes once.
    assert rig.ctl.accept_response(rig.deliver(wire)).state is DeviceState.SESSION_OPEN


@pytest.mark.parametrize(
    ("command", "args"),
    [
        ("start_session", {"capture_mode": "lidar_magic"}),
        ("start_session", {}),
        ("start_session", {"capture_mode": "turntable", "exposure": 1}),
        ("capture_frame", {"frame": 1}),
        ("set_capture_plan", {"steps": []}),
        ("set_capture_plan", _plan(*([0] * (MAX_PLAN_STEPS + 1)))),
        ("set_capture_plan", _plan(360_000)),
        ("set_capture_plan", _plan(-1)),
        ("set_capture_plan", {"steps": [{"ring_id": "ring/0", "turntable_angle_mdeg": 0}]}),
        ("set_capture_plan", {"steps": [{"ring_id": "r", "turntable_angle_mdeg": 1.5}]}),
        ("set_capture_plan", {"steps": [{"ring_id": "r", "turntable_angle_mdeg": True}]}),
        ("set_capture_plan", {"steps": [{"ring_id": "r", "turntable_angle_mdeg": 0, "z_mm": 1}]}),
    ],
)
def test_controller_refuses_to_sign_bad_arguments(command: str, args: dict[str, Any]) -> None:
    with pytest.raises(RemoteCaptureError, match="bad_args"):
        Rig().ctl.build(command, args)


def test_unknown_command_is_refused_by_controller() -> None:
    with pytest.raises(RemoteCaptureError, match="unknown_command"):
        Rig().ctl.build("delete_all_scans")


def test_replay_reorder_and_nonce_reuse_are_rejected() -> None:
    rig = Rig()
    first = rig.ctl.build("start_session", {"capture_mode": "turntable"})
    second = rig.ctl.build("query_status")
    third = rig.ctl.build("query_status")
    rig.ctl.accept_response(rig.deliver(first))
    assert _device_code(rig, rig.deliver(first)) is Code.REPLAYED_COMMAND
    rig.ctl.accept_response(rig.deliver(third))
    assert _device_code(rig, rig.deliver(second)) is Code.REPLAYED_COMMAND  # reordered/late
    reuse = Rig()
    reuse.ctl._nonce_source = lambda: "ab" * 16
    reuse.send("query_status")
    assert (
        _device_code(reuse, reuse.deliver(reuse.ctl.build("query_status"))) is Code.REPLAYED_COMMAND
    )


def test_timestamp_window_rejects_delayed_and_future_commands() -> None:
    rig = Rig()
    delayed = rig.ctl.build("query_status")
    rig.now[0] += 30.001
    assert _device_code(rig, rig.deliver(delayed)) is Code.STALE_COMMAND
    future = rig.ctl.build("query_status")
    rig.now[0] -= 30.002
    assert _device_code(rig, rig.deliver(future)) is Code.STALE_COMMAND
    assert rig.send("query_status").status == "ok"


def test_session_expiry_is_enforced_on_both_sides() -> None:
    rig = Rig(ttl=30)
    late = rig.ctl.build("query_status")
    answered = rig.deliver(rig.ctl.build("query_status"))
    rig.now[0] += 30.0
    assert _wire_code(rig.deliver(late)) == "session_expired"
    with pytest.raises(RemoteCaptureError, match="session_expired"):
        rig.ctl.accept_response(answered)  # receipt re-checks expiry, not only build
    # PairingAuthenticator purges an expired credential on first sight.
    with pytest.raises(RemoteCaptureError, match="unpaired_session"):
        rig.ctl.build("query_status")


def test_unpaired_revoked_and_foreign_sessions_are_rejected() -> None:
    rig = Rig()
    rig.auth.revoke(rig.cred)
    with pytest.raises(RemoteCaptureError, match="unpaired_session"):
        rig.ctl.build("query_status")
    rig = Rig()
    wire = rig.ctl.build("query_status")
    rig.dev.revoke()
    assert _device_code(rig, rig.deliver(wire)) is Code.UNAUTHENTICATED
    assert rig.dev.rejections[-1] is Code.UNPAIRED_SESSION  # detail stays local
    rig, foreign = Rig(), Rig()
    assert _device_code(rig, rig.deliver(foreign.ctl.build("query_status"))) is Code.UNAUTHENTICATED
    assert rig.dev.rejections[-1] is Code.UNKNOWN_SESSION


def test_device_identity_is_pinned_on_commands_and_responses() -> None:
    wrong = Rig(device="iphone-other")
    assert (
        _device_code(wrong, wrong.deliver(wrong.ctl.build("query_status"))) is Code.UNAUTHENTICATED
    )
    assert wrong.dev.rejections[-1] is Code.IDENTITY_MISMATCH
    rig = Rig()
    impostor = MockIPhoneCaptureEndpoint(
        rig.cred, device_id="iphone-other", clock=lambda: rig.now[0], enabled=True
    )
    impostor_ctl = RemoteCaptureController(
        rig.auth,
        rig.cred,
        device_id="iphone-other",
        peer_address=LAN_PEER,
        clock=lambda: rig.now[0],
        nonce_source=lambda: "1" * 32,
        enabled=True,
    )
    reply = impostor.handle(impostor_ctl.build("query_status"), peer_address=LAN_PEER)
    rig.ctl.build("query_status")  # pending seq 1 with a different nonce
    with pytest.raises(RemoteCaptureError, match="bad_mac"):
        rig.ctl.accept_response(reply)


def test_rate_limit_is_authenticated_and_recovers() -> None:
    rig = Rig(rate=3)
    assert [rig.send("query_status").status for _ in range(3)] == ["ok"] * 3
    limited = rig.send("query_status")
    assert (limited.status, limited.error_code) == ("rejected", Code.RATE_LIMITED)
    rig.now[0] += 1.0
    assert rig.send("query_status").status == "ok"


def test_tampered_duplicate_and_unsolicited_responses_are_rejected() -> None:
    rig = Rig()
    response = rig.deliver(rig.ctl.build("start_session", {"capture_mode": "turntable"}))
    value = json.loads(response)
    with pytest.raises(RemoteCaptureError, match="bad_mac"):
        rig.ctl.accept_response(_edit(response, state="CLOSED"))
    with pytest.raises(RemoteCaptureError, match="bad_mac"):
        rig.ctl.accept_response(_edit(response, result={**value["result"], "frames_captured": 9}))
    with pytest.raises(RemoteCaptureError, match="non_canonical"):
        rig.ctl.accept_response(response.replace(b":", b": ", 1))
    rig.ctl.accept_response(response)
    with pytest.raises(RemoteCaptureError, match="unexpected_response"):
        rig.ctl.accept_response(response)
    with pytest.raises(RemoteCaptureError, match="malformed"):
        rig.ctl.accept_response(canonical_json({"schema": "packlab.remote-capture-response.v1"}))


class _UpgradingEndpoint(MockIPhoneCaptureEndpoint):
    """Correctly keyed but misbehaving device that claims authority on a frame ack."""

    def __init__(self, *args: Any, field: str, value: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._field, self._value = field, value

    def _apply(self, command: Any) -> dict[str, Any]:
        result = super()._apply(command)
        if "frame" in result:
            result["frame"][self._field] = self._value
        return result


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("measurement_authority", True),
        ("scan_master_authority", True),
        ("measurement_authority", 1),
        ("capture_metadata_status", "measured"),
    ],
)
def test_frame_ack_can_never_upgrade_authority(field: str, value: Any) -> None:
    rig = Rig()
    rig.dev = _UpgradingEndpoint(
        rig.cred, device_id=DEVICE, clock=lambda: rig.now[0], enabled=True, field=field, value=value
    )
    rig.send("start_session", {"capture_mode": "turntable"})
    with pytest.raises(RemoteCaptureError, match="authority_upgrade"):
        rig.send("capture_frame")


def test_network_faults_drop_duplicate_reorder_and_lost_ack() -> None:
    rig = Rig()
    rig.send("start_session", {"capture_mode": "turntable"})
    dropped = rig.ctl.build("capture_frame")  # never delivered
    assert rig.send("query_status").result["frames_captured"] == 0
    assert dropped.decode() and 2 in rig.ctl.pending_seqs
    # Lost acknowledgement: the device captured; reconciliation is via query_status,
    # never by blindly re-sending the same capture.
    rig.deliver(rig.ctl.build("capture_frame"))
    assert rig.send("query_status").result["frames_captured"] == 1
    duplicate = rig.ctl.build("capture_frame")
    first = rig.deliver(duplicate)
    assert _device_code(rig, rig.deliver(duplicate)) is Code.REPLAYED_COMMAND
    assert rig.ctl.accept_response(first).result["frame"]["frame_index"] == 1
    a, b = rig.ctl.build("query_status"), rig.ctl.build("capture_frame")
    reply_a, reply_b = rig.deliver(a), rig.deliver(b)
    assert rig.ctl.accept_response(reply_b).result["frame"]["frame_index"] == 2  # reordered acks
    assert rig.ctl.accept_response(reply_a).result["frames_captured"] == 2
    assert rig.dev.frames_captured == 3


def _chaos_transcript(seed: int) -> tuple[str, dict[str, int]]:
    rng = random.Random(seed)
    rig = Rig(rate=1_000, ttl=900)
    digest = hashlib.sha256()
    held: list[bytes] = []
    outcomes: dict[str, int] = {}
    executed_capture_seqs: list[int] = []
    rig.send("start_session", {"capture_mode": "turntable"})
    for _ in range(150):
        rig.now[0] += rng.choice([0.01, 0.05, 0.2])
        wire = rig.ctl.build(
            rng.choice(["capture_frame", "capture_frame", "query_status", "pause", "resume"])
        )
        fault = rng.choice(["ok", "ok", "drop", "duplicate", "tamper", "hold", "release", "delay"])
        deliveries = {
            "drop": [],
            "duplicate": [wire, wire],
            "tamper": [_edit(wire, nonce="f" * 32)],
            "hold": [],
            "release": [wire, *held],
        }.get(fault, [wire])
        if fault == "hold":
            held.append(wire)
        elif fault == "release":
            held.clear()
        elif fault == "delay":
            rig.now[0] += 31.0
        for delivered in deliveries:
            reply = rig.deliver(delivered)
            digest.update(delivered + reply)
            parsed = json.loads(reply)
            if parsed["status"] == "ok" and parsed["command"] == "capture_frame":
                executed_capture_seqs.append(parsed["in_reply_to_seq"])
            if rng.random() < 0.15:
                outcomes["ack_lost"] = outcomes.get("ack_lost", 0) + 1
                continue
            try:
                response = rig.ctl.accept_response(reply)
            except RemoteCaptureError as error:
                key = (error.device_code or error.code).value
                outcomes[key] = outcomes.get(key, 0) + 1
                continue
            outcomes[response.status] = outcomes.get(response.status, 0) + 1
            if response.status == "ok" and response.command == "capture_frame":
                assert response.result["frame"]["measurement_authority"] is False
                assert response.result["frame"]["scan_master_authority"] is False
    assert len(executed_capture_seqs) == len(set(executed_capture_seqs)) == rig.dev.frames_captured
    assert rig.send("query_status").result["frames_captured"] == rig.dev.frames_captured
    return digest.hexdigest(), outcomes


def test_seeded_fault_injection_is_deterministic_and_never_double_captures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(secrets, "token_urlsafe", lambda nbytes=32: "T" * 43)
    first, outcomes = _chaos_transcript(429)
    assert _chaos_transcript(429) == (first, outcomes)
    assert _chaos_transcript(430)[0] != first
    for expected in ("ok", "replayed_command", "bad_mac", "stale_command", "ack_lost"):
        assert outcomes.get(expected, 0) > 0, (expected, outcomes)


def test_keys_and_tokens_never_leak_or_serialise() -> None:
    rig = Rig()
    token = rig.cred.token
    wires = [rig.ctl.build("start_session", {"capture_mode": "turntable"})]
    wires.append(rig.deliver(wires[0]))
    wires.append(rig.deliver(wires[0]))
    texts = [w.decode() for w in wires] + [repr(rig.ctl), repr(rig.dev), repr(rig.ctl._keys)]
    with pytest.raises(RemoteCaptureError) as caught:
        rig.ctl.accept_response(wires[2])
    texts.append(str(caught.value))
    assert all(token not in text for text in texts)
    assert json.loads(wires[0])["schema"] == COMMAND_SCHEMA
    for secret_holder in (rig.ctl, rig.dev, rig.ctl._keys):
        with pytest.raises(TypeError):
            pickle.dumps(secret_holder)


def test_loopback_socket_round_trip_on_ephemeral_port() -> None:
    rig = Rig(peer="127.0.0.1")
    peers: list[str] = []

    async def scenario() -> list[Any]:
        async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            peer = writer.get_extra_info("peername")[0]
            peers.append(peer)
            while line := await reader.readline():
                writer.write(rig.dev.handle(line, peer_address=peer))
                await writer.drain()
            writer.close()

        server = await asyncio.start_server(serve, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        responses = []
        plan = [
            ("start_session", {"capture_mode": "turntable"}),
            ("set_capture_plan", _plan(0, 180_000)),
            ("capture_frame", None),
            ("capture_frame", None),
            ("end_session", None),
        ]
        for command, args in plan:
            writer.write(rig.ctl.build(command, args))
            await writer.drain()
            responses.append(rig.ctl.accept_response(await asyncio.wait_for(reader.readline(), 2)))
        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()
        return responses

    responses = asyncio.run(scenario())
    assert peers == ["127.0.0.1"]
    assert [r.state for r in responses][-1] is DeviceState.CLOSED
    assert [r.result["frame"]["planned_turntable_angle_mdeg"] for r in responses[2:4]] == [
        0,
        180_000,
    ]


# --- Security review V01 regressions (P2-1, P2-2, P3-1, P3-3) ---------------------


def _set_result(key: str, item: Any) -> Any:
    return lambda value: value["result"].__setitem__(key, item)


def _set_frame(key: str, item: Any) -> Any:
    return lambda value: value["result"]["frame"].__setitem__(key, item)


def _reject_with_frame(value: dict[str, Any]) -> None:
    value.update(status="rejected", error_code="capture_plan_complete")
    value["result"]["frame"] = dict(_AUTHORITY_FRAME)


_AUTHORITY_FRAME = {
    "frame_index": 0,
    "plan_step": None,
    "ring_id": None,
    "planned_turntable_angle_mdeg": None,
    "device_capture_timestamp_ms": 1,
    "capture_metadata_status": "placeholder_not_measured",
    "measurement_authority": True,
    "scan_master_authority": True,
}


@pytest.mark.parametrize(
    ("command", "mutate", "expected"),
    [
        ("query_status", _set_result("scale_mm_per_px", 1), Code.MALFORMED),
        ("query_status", _set_result("measurement_authority", True), Code.MALFORMED),
        ("query_status", _set_result("frame", _AUTHORITY_FRAME), Code.MALFORMED),
        ("query_status", lambda v: v["result"].pop("last_accepted_seq"), Code.MALFORMED),
        ("query_status", _set_result("state", "CLOSED"), Code.MALFORMED),
        ("query_status", _set_result("frames_captured", "lots"), Code.MALFORMED),
        ("query_status", _set_result("frames_captured", True), Code.MALFORMED),
        ("query_status", _set_result("capture_mode", ["turntable"]), Code.MALFORMED),
        ("query_status", _set_result("capture_mode", "lidar"), Code.MALFORMED),
        ("query_status", _set_result("plan_steps_remaining", 1), Code.MALFORMED),
        ("query_status", lambda v: v.update(issued_at_ms="x"), Code.MALFORMED),
        ("query_status", lambda v: v.update(status=["ok"]), Code.MALFORMED),
        ("query_status", lambda v: v.update(status="maybe"), Code.MALFORMED),
        ("query_status", lambda v: v.update(state="EXPLODED"), Code.MALFORMED),
        ("query_status", lambda v: v.update(error_code="rate_limited"), Code.MALFORMED),
        (
            "query_status",
            lambda v: v.update(status="rejected", error_code="bad_mac"),
            Code.MALFORMED,
        ),
        ("query_status", lambda v: v.update(status="rejected", error_code=["x"]), Code.MALFORMED),
        ("query_status", lambda v: v.update(session_id="f" * 32), Code.UNKNOWN_SESSION),
        ("query_status", lambda v: v.update(device_id="iphone-other"), Code.IDENTITY_MISMATCH),
        ("query_status", lambda v: v.update(controller_id="studio-x"), Code.IDENTITY_MISMATCH),
        ("query_status", lambda v: v.update(in_reply_to_nonce="e" * 32), Code.UNEXPECTED_RESPONSE),
        ("query_status", lambda v: v.update(command="pause"), Code.UNEXPECTED_RESPONSE),
        ("query_status", lambda v: v.update(in_reply_to_seq=99), Code.UNEXPECTED_RESPONSE),
        ("capture_frame", _set_frame("scan_master", False), Code.MALFORMED),
        ("capture_frame", lambda v: v["result"]["frame"].pop("ring_id"), Code.MALFORMED),
        ("capture_frame", _set_frame("frame_index", "zero"), Code.MALFORMED),
        ("capture_frame", _set_frame("ring_id", {"x": 1}), Code.MALFORMED),
        ("capture_frame", _set_frame("plan_step", 0), Code.MALFORMED),
        ("capture_frame", _set_frame("device_capture_timestamp_ms", -1), Code.MALFORMED),
        ("capture_frame", _set_frame("scan_master_authority", True), Code.AUTHORITY_UPGRADE),
        (
            "capture_frame",
            lambda v: v.update(status="rejected", error_code="capture_plan_complete"),
            Code.MALFORMED,  # a rejected capture may not carry any frame
        ),
        ("capture_frame", _reject_with_frame, Code.MALFORMED),
    ],
)
def test_mac_valid_responses_must_match_the_exact_contract(
    command: str, mutate: Any, expected: Code
) -> None:
    rig = Rig()
    forged = _forged(rig, command, mutate)
    with pytest.raises(RemoteCaptureError) as caught:
        rig.ctl.accept_response(forged)
    assert caught.value.code is expected


def test_unmutated_forge_baseline_is_accepted() -> None:
    rig = Rig()
    assert rig.ctl.accept_response(_forged(rig, "capture_frame", lambda v: None)).status == "ok"


def test_hostile_responses_never_crash_the_controller(monkeypatch: pytest.MonkeyPatch) -> None:
    rig = Rig()
    response = rig.deliver(rig.ctl.build("query_status"))
    unsigned = {"schema": RESPONSE_SCHEMA, "status": "rejected", "error_code": ["x"]}
    for hostile, expected in [
        (response.replace(b'"studio-1"', rb'"\ud800"'), Code.MALFORMED),
        (_edit(response, mac="é" * 64), Code.BAD_MAC),
        (_edit(response, mac=["a"]), Code.BAD_MAC),
    ]:
        with pytest.raises(RemoteCaptureError) as caught:
            rig.ctl.accept_response(hostile)
        assert caught.value.code is expected
    assert _device_code(rig, canonical_json(unsigned)) is Code.MALFORMED

    def boom(_: object) -> None:
        raise TypeError("unexpected")

    monkeypatch.setattr(rig.ctl, "_validate_signed", boom)
    with pytest.raises(RemoteCaptureError, match="malformed"):
        rig.ctl.accept_response(response)


def test_endpoint_catch_all_returns_unsigned_malformed(monkeypatch: pytest.MonkeyPatch) -> None:
    rig = Rig()

    def boom(*_: object) -> None:
        raise KeyError("unexpected")

    monkeypatch.setattr(rig.dev, "_authenticate", boom)
    assert _wire_code(rig.deliver(rig.ctl.build("query_status"))) == "malformed"
    assert rig.dev.rejections[-1] is Code.MALFORMED


def test_strict_loads_rejects_floats_itself() -> None:
    assert _strict_loads(b'{"a":1}\n', 100) == {"a": 1}
    with pytest.raises(RemoteCaptureError, match="malformed"):
        _strict_loads(b'{"a":1.5}\n', 100)


def test_tls_pin_is_bound_into_the_command_key() -> None:
    rig = Rig()
    other_pin = dataclasses.replace(rig.cred, certificate_fingerprint="b" * 64)
    device = MockIPhoneCaptureEndpoint(
        other_pin, device_id=DEVICE, clock=lambda: rig.now[0], enabled=True
    )
    reply = device.handle(rig.ctl.build("query_status"), peer_address=LAN_PEER)
    assert _wire_code(reply) == "bad_mac"


def test_pending_cap_evicts_oldest_command() -> None:
    rig = Rig()
    oldest = rig.ctl.build("query_status")
    for _ in range(MAX_PENDING):
        rig.ctl.build("query_status")
    assert len(rig.ctl.pending_seqs) == MAX_PENDING and 1 not in rig.ctl.pending_seqs
    with pytest.raises(RemoteCaptureError, match="unexpected_response"):
        rig.ctl.accept_response(rig.deliver(oldest))


def test_sequence_space_exhaustion_stops_signing() -> None:
    rig = Rig()
    rig.ctl._seq = MAX_SEQ - 1
    assert rig.ctl.accept_response(rig.deliver(rig.ctl.build("query_status"))).seq == MAX_SEQ
    with pytest.raises(RemoteCaptureError, match="session_expired"):
        rig.ctl.build("query_status")


def test_rejection_log_is_bounded() -> None:
    rig = Rig()
    for _ in range(REJECTION_MEMORY + 50):
        rig.deliver(b"garbage")
    assert len(rig.dev.rejections) == REJECTION_MEMORY


@pytest.mark.parametrize("rate", [0, -1, 1001, True, 2.5])
def test_rate_limit_parameter_is_validated(rate: Any) -> None:
    with pytest.raises(ValueError, match="max_commands_per_second"):
        MockIPhoneCaptureEndpoint(
            Rig().cred, device_id=DEVICE, enabled=True, max_commands_per_second=rate
        )


def test_rate_limiter_uses_monotonic_time_not_wall_clock() -> None:
    rig = Rig()
    mono = [0.0]
    rig.dev = MockIPhoneCaptureEndpoint(
        rig.cred,
        device_id=DEVICE,
        clock=lambda: rig.now[0],
        monotonic=lambda: mono[0],
        enabled=True,
        max_commands_per_second=1,
    )
    assert rig.send("query_status").status == "ok"
    rig.now[0] += 5.0  # wall clock jumps forward; monotonic does not
    assert rig.send("query_status").error_code is Code.RATE_LIMITED
    rig.now[0] -= 10.0  # wall clock steps backwards
    mono[0] += 1.0
    assert rig.send("query_status").status == "ok"
