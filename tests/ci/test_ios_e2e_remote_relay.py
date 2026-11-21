"""PL-0429 CI harness: request-file relay and control-log verification used by capture-e2e."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from packlab_studio.receiver_session import ReceiverSession

_SPEC = importlib.util.spec_from_file_location(
    "ios_e2e_receiver", Path(__file__).resolve().parents[2] / "tools/ci/ios_e2e_receiver.py"
)
assert _SPEC is not None and _SPEC.loader is not None
harness = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(harness)


def _result(command: dict[str, object], outcome: str, reasons: list[str]) -> dict[str, object]:
    return {
        "scan_active": True,
        "control_enabled": True,
        "last_result": {
            "command_id": command["command_id"],
            "action": command["action"],
            "outcome": outcome,
            "reasons": reasons,
            "message": "",
        },
    }


def test_relay_issues_to_the_polling_phone_and_verify_reads_its_outcomes(tmp_path: Path) -> None:
    session = ReceiverSession(tmp_path / "root", lan_host_provider=lambda: "127.0.0.1")
    control_dir = tmp_path / "control"
    control_dir.mkdir()
    device, _ = session.receiver.devices.register("iPhone")
    hub = session.receiver.control

    # Not polling yet: the request waits, then fails once it is old.
    stale = control_dir / "a.request"
    stale.write_text("capture", "utf-8")
    harness._relay_remote_requests(session, control_dir)
    assert stale.exists()
    os.utime(stale, (0, 0))
    harness._relay_remote_requests(session, control_dir)
    assert (control_dir / "a.failed").read_text("utf-8") == "device_not_connected"

    hub.next_command(device.device_id, timeout=0)
    for name, action, outcome, reasons in (
        ("b", "capture", "refused", ["object_center_unset"]),
        ("c", "capture", "captured", []),
        ("d", "finish", "finished", []),
    ):
        (control_dir / f"{name}.request").write_text(action, "utf-8")
        harness._relay_remote_requests(session, control_dir)
        issued = (control_dir / f"{name}.issued").read_text("utf-8")
        command = hub.next_command(device.device_id, timeout=0)
        assert command is not None and command["command_id"] == issued
        hub.report(device.device_id, _result(command, outcome, reasons))

    root = tmp_path / "root"
    assert harness._verify_remote(root, 1) == []
    assert harness._verify_remote(root, 2) == [
        "expected 2 remote captures, log shows "
        "[('capture', 'refused'), ('capture', 'captured'), ('finish', 'finished')]"
    ]
