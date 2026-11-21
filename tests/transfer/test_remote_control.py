"""PL-0429 remote capture control: protocol and security over the real HTTPS receiver."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from tests.transfer.test_loopback_receiver import _context, _identity_or_skip, _pair

import packlab_studio.receiver as receiver_module
from packlab_studio.receiver import PackLabReceiver
from packlab_studio.remote_control import (
    COMMAND_TTL_SECONDS,
    MAX_STATUS_BYTES,
    RemoteControlError,
    RemoteControlHub,
)


def _call(receiver, identity, path, *, token=None, body=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    request = urllib.request.Request(
        f"https://127.0.0.1:{receiver.port}{path}",
        data=data,
        method="POST" if data is not None else "GET",
        headers={"Content-Type": "application/json"},
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, context=_context(identity), timeout=10) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else None
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def _status(**overrides):
    value = {
        "scan_active": True,
        "control_enabled": True,
        "scan_name": "Bottle 1",
        "coverage_captured": 3,
        "coverage_total": 16,
        "instruction": "Hold here — tap Manual Capture",
        "last_result": None,
    }
    value.update(overrides)
    return value


@pytest.fixture
def running(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(receiver_module, "POLL_TIMEOUT_SECONDS", 0.3)
    identity = _identity_or_skip(tmp_path)
    receiver = PackLabReceiver(tmp_path / "root", receiver_id="r1", tls_identity=identity)
    receiver.start()
    try:
        token, _ = _pair(receiver, identity)
        device_id = receiver.devices.devices()[0].device_id
        yield receiver, identity, token, device_id
    finally:
        receiver.stop()


def test_unauthenticated_and_wrong_token_polls_are_refused(running) -> None:
    receiver, identity, _token, _ = running
    assert _call(receiver, identity, "/v1/control/next")[1]["error_code"] == "unpaired"
    code, value = _call(receiver, identity, "/v1/control/next", token="not-a-token")
    assert code == 400 and value["error_code"] == "unpaired"
    code, value = _call(receiver, identity, "/v1/control/status", body=_status())
    assert code == 400 and value["error_code"] == "unpaired"


def test_capture_command_is_delivered_once_and_result_logged(running) -> None:
    receiver, identity, token, device_id = running
    # Studio cannot reach a phone that is not polling (it never connects to the phone).
    with pytest.raises(RemoteControlError, match="device_not_connected"):
        receiver.control.issue(device_id, "capture")
    assert _call(receiver, identity, "/v1/control/next", token=token) == (204, None)
    command = receiver.control.issue(device_id, "capture")
    with pytest.raises(RemoteControlError, match="command_pending"):
        receiver.control.issue(device_id, "capture")  # double click is not two captures
    code, value = _call(receiver, identity, "/v1/control/next", token=token)
    assert code == 200 and value["command_id"] == command.command_id
    assert value["action"] == "capture" and 0 < value["expires_in_ms"] <= 10_000
    # One-shot: a second poll does not see it again.
    assert _call(receiver, identity, "/v1/control/next", token=token) == (204, None)
    result = {
        "command_id": command.command_id,
        "action": "capture",
        "outcome": "refused",
        "reasons": ["object_not_in_view"],
        "message": "point the camera\x07 at the package",
    }
    assert (
        _call(
            receiver, identity, "/v1/control/status", token=token, body=_status(last_result=result)
        )[0]
        == 200
    )
    status = receiver.control.status(device_id)
    assert status is not None and status.coverage_captured == 3
    assert status.last_result is not None and status.last_result.reasons == ("object_not_in_view",)
    assert status.last_result.message == "point the camera at the package"  # control char gone
    # Repeating the same status does not log the result twice.
    _call(receiver, identity, "/v1/control/status", token=token, body=_status(last_result=result))
    log = [json.loads(line) for line in (receiver.root / "remote-control-log.jsonl").open()]
    assert [entry["event"] for entry in log] == ["issued", "delivered", "result"]
    assert log[2]["outcome"] == "refused" and "token" not in json.dumps(log)


def test_result_for_unknown_or_foreign_command_is_refused(running) -> None:
    receiver, identity, token, _ = running
    result = {
        "command_id": "0" * 32,
        "action": "capture",
        "outcome": "captured",
        "reasons": [],
        "message": "",
    }
    code, value = _call(
        receiver, identity, "/v1/control/status", token=token, body=_status(last_result=result)
    )
    assert code == 400 and value["error_code"] == "unknown_command"


@pytest.mark.parametrize(
    "body",
    [
        _status(extra=1),
        _status(coverage_captured=1.5),
        _status(coverage_total=True),
        _status(scan_name="x" * 129),
        _status(instruction=None),
        {"scan_active": True},
        _status(last_result={"command_id": "a" * 32}),
        _status(
            last_result={
                "command_id": "a" * 32,
                "action": "capture",
                "outcome": "captured",
                "reasons": ["Bad Reason"],
                "message": "",
            }
        ),
    ],
)
def test_malformed_status_is_refused(running, body) -> None:
    receiver, identity, token, _ = running
    code, value = _call(receiver, identity, "/v1/control/status", token=token, body=body)
    assert code == 400 and value["error_code"] == "bad_request"


def test_oversized_status_is_refused(running) -> None:
    receiver, identity, token, _ = running
    raw = json.dumps(_status(instruction="x" * MAX_STATUS_BYTES)).encode()
    code, value = _call(receiver, identity, "/v1/control/status", token=token, raw=raw)
    assert code == 400 and value["error_code"] == "bad_request"


def test_revoke_kills_control(running) -> None:
    receiver, identity, token, device_id = running
    receiver.control.next_command(device_id, timeout=0)
    receiver.control.issue(device_id, "finish")
    receiver.revoke_device(device_id)
    code, value = _call(receiver, identity, "/v1/control/next", token=token)
    assert code == 400 and value["error_code"] in {"device_revoked", "unpaired"}
    with pytest.raises(RemoteControlError, match="device_revoked"):
        receiver.control.issue(device_id, "capture")


def test_revoke_wakes_a_waiting_poll(tmp_path: Path) -> None:
    active = {"d": True}
    hub = RemoteControlHub(is_active=lambda device: active.get(device, False))
    errors: list[str] = []

    def poll() -> None:
        try:
            hub.next_command("d", timeout=20)
        except RemoteControlError as error:
            errors.append(error.code)

    thread = threading.Thread(target=poll)
    thread.start()
    active["d"] = False
    hub.forget("d")
    thread.join(timeout=5)
    assert not thread.is_alive() and errors == ["device_revoked"]


def test_command_expires_after_ten_seconds(tmp_path: Path) -> None:
    now = [100.0]
    hub = RemoteControlHub(
        is_active=lambda _: True, log_path=tmp_path / "log.jsonl", clock=lambda: now[0]
    )
    hub.next_command("d", timeout=0)
    hub.issue("d", "capture")
    now[0] += COMMAND_TTL_SECONDS
    assert hub.next_command("d", timeout=0) is None
    assert [entry["event"] for entry in hub.log] == ["issued", "expired"]
    # An expired command no longer blocks a new one.
    assert hub.issue("d", "capture").action == "capture"
    with pytest.raises(RemoteControlError, match="bad_request"):
        hub.issue("d", "shutdown")
