"""PL-0451/PL-0452 CI harness: a real Studio receiver for the iOS Simulator UI test.

``serve`` runs the production ``ReceiverSession`` (HTTPS, temporary TLS identity,
loopback only) and keeps a fresh one-time pairing offer in ``--offer-file`` for
the XCUITest to type into the app's manual pairing form. ``verify`` checks what
arrived: every received package passes ``validate_packscan``, the import reports
show the expected image count, and exactly one device was paired (the second
scan therefore travelled on the long-lived device credential, not a new code).
PL-0429: with ``--control-dir`` it also stands in for Studio's Remote capture buttons, and
``verify --expected-remote-captures`` checks the receiver's remote-control log.
Runner-temp data only; nothing here is written to the repository.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "core/src"), str(REPO / "apps/windows-studio/src")]

from packlab_core.packscan import validate_packscan  # noqa: E402
from packlab_studio.receiver_session import ReceiverSession  # noqa: E402
from packlab_studio.remote_control import RemoteControlError  # noqa: E402

OFFER_TTL_SECONDS = 900
REFRESH_BELOW_SECONDS = 300


def _write_offer(session: ReceiverSession, path: Path) -> float:
    offer = session.new_offer(ttl_seconds=OFFER_TTL_SECONDS)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(offer.public_dict(), indent=2), encoding="utf-8")
    os.replace(temporary, path)
    print(
        f"offer {offer.pairing_id} on {offer.host}:{offer.port} expires {offer.expires_at:.0f}",
        flush=True,
    )
    return offer.expires_at


REMOTE_REQUEST_WAIT_SECONDS = 30


def _relay_remote_requests(session: ReceiverSession, control_dir: Path) -> None:
    """PL-0429 Studio stand-in: the XCUITest drops ``<id>.request`` (an action name) when it
    wants PackLab to press Capture now / Finish scan; this issues it exactly as the Studio
    button does (``RemoteControlHub.issue``) and answers ``<id>.issued`` or ``<id>.failed``."""
    for request in sorted(control_dir.glob("*.request")):
        action = request.read_text("utf-8").strip()
        connected = [
            device.device_id
            for device in session.paired_devices()
            if session.receiver.control.connected(device.device_id)
        ]
        error = "device_not_connected"
        if len(connected) == 1:
            try:
                command = session.receiver.control.issue(connected[0], action)
            except RemoteControlError as failure:
                error = failure.code
            else:
                request.with_suffix(".issued").write_text(command.command_id, "utf-8")
                request.unlink()
                print(f"remote {action} issued as {command.command_id}", flush=True)
                continue
        # The phone may still be opening its session; retry until the request is old.
        if time.time() - request.stat().st_mtime > REMOTE_REQUEST_WAIT_SECONDS:
            request.with_suffix(".failed").write_text(error, "utf-8")
            request.unlink()
            print(f"remote {action} failed: {error}", flush=True)


def serve(root: Path, offer_file: Path, port: int, control_dir: Path | None = None) -> int:
    session = ReceiverSession(
        root,
        tls_root=root / "tls",
        port=port,
        bind_host="127.0.0.1",
        lan_host_provider=lambda: "127.0.0.1",
    )
    session.start()
    stop = False

    def _stop(*_: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    expires_at = _write_offer(session, offer_file)
    try:
        while not stop:
            if expires_at - time.time() < REFRESH_BELOW_SECONDS:
                expires_at = _write_offer(session, offer_file)
            if control_dir is not None:
                _relay_remote_requests(session, control_dir)
            time.sleep(0.2)
    finally:
        session.stop()
    return 0


def _verify_remote(root: Path, captures: int) -> list[str]:
    """PL-0429: the receiver's control log must show the phone's own outcomes for every
    remote request: ``captures`` accepted captures, one gate refusal and one finish."""
    path = root / "remote-control-log.jsonl"
    log = (
        [json.loads(line) for line in path.read_text("utf-8").splitlines()] if path.exists() else []
    )
    results = [entry for entry in log if entry["event"] == "result"]
    for entry in results:
        print(f"remote result: {entry['action']} -> {entry['outcome']} {entry.get('reasons', [])}")
    issued = {entry["command_id"] for entry in log if entry["event"] == "issued"}
    delivered = {entry["command_id"] for entry in log if entry["event"] == "delivered"}
    failures = []
    if not {entry["command_id"] for entry in results} <= delivered <= issued:
        failures.append("a remote result does not belong to a command Studio issued")
    outcomes = [(entry["action"], entry["outcome"]) for entry in results]
    if outcomes.count(("capture", "captured")) != captures:
        failures.append(f"expected {captures} remote captures, log shows {outcomes}")
    refused = [entry for entry in results if entry["outcome"] == "refused"]
    if len(refused) != 1 or not refused[0].get("reasons"):
        failures.append(f"expected exactly one gate refusal with its reasons, got {refused}")
    if outcomes.count(("finish", "finished")) != 1:
        failures.append(f"expected one remote finish, log shows {outcomes}")
    return failures


def verify(root: Path, expected_scans: int, expected_images: int, remote_captures: int = 0) -> int:
    failures: list[str] = []
    packages = sorted((root / "capture_inbox").glob("*.packscan"))
    for package in packages:
        report = validate_packscan(package)
        images = [name for name in report.payloads if name.startswith("images/")]
        print(
            f"validate_packscan PASS {package.name}: {len(images)} images, capture_id {report.manifest.get('capture_id')}"
        )
        if len(images) != expected_images:
            failures.append(
                f"{package.name} carries {len(images)} images, expected {expected_images}"
            )
    if len(packages) != expected_scans:
        failures.append(f"expected {expected_scans} received packages, found {len(packages)}")
    reports = [
        json.loads(path.read_text("utf-8")) for path in sorted((root / "reports").glob("*.json"))
    ]
    for report in reports:
        print(
            "import report:",
            json.dumps(
                {
                    key: report.get(key)
                    for key in (
                        "capture_id",
                        "source_channel",
                        "image_count",
                        "photo_metadata_count",
                        "capture_mode",
                        "device_summary",
                    )
                }
            ),
        )
    counts = [report.get("image_count") for report in reports]
    if len(reports) != expected_scans or any(count != expected_images for count in counts):
        failures.append(
            f"expected {expected_scans} import reports with {expected_images} images, got {counts}"
        )
    devices = json.loads((root / "paired-devices.json").read_text("utf-8"))["devices"]
    active = [device for device in devices if device.get("revoked_at") is None]
    print(
        f"paired devices: {len(devices)} ({len(active)} active); last_seen_at set: {[d.get('last_seen_at') is not None for d in devices]}"
    )
    if len(devices) != 1:
        failures.append(
            f"expected exactly one pairing for {expected_scans} scans, found {len(devices)}"
        )
    elif devices[0].get("last_seen_at") is None:
        failures.append(
            "the paired device never opened a device session (second scan did not use it)"
        )
    if remote_captures:
        failures.extend(_verify_remote(root, remote_captures))
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    serve_parser = commands.add_parser("serve")
    serve_parser.add_argument("--root", type=Path, required=True)
    serve_parser.add_argument("--offer-file", type=Path, required=True)
    serve_parser.add_argument("--port", type=int, default=8443)
    serve_parser.add_argument("--control-dir", type=Path)
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--root", type=Path, required=True)
    verify_parser.add_argument("--expected-scans", type=int, required=True)
    verify_parser.add_argument("--expected-images", type=int, required=True)
    verify_parser.add_argument("--expected-remote-captures", type=int, default=0)
    args = parser.parse_args()
    if args.command == "serve":
        return serve(args.root, args.offer_file, args.port, args.control_dir)
    return verify(
        args.root, args.expected_scans, args.expected_images, args.expected_remote_captures
    )


if __name__ == "__main__":
    raise SystemExit(main())
