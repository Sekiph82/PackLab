"""PL-0451/PL-0452 CI harness: a real Studio receiver for the iOS Simulator UI test.

``serve`` runs the production ``ReceiverSession`` (HTTPS, temporary TLS identity,
loopback only) and keeps a fresh one-time pairing offer in ``--offer-file`` for
the XCUITest to type into the app's manual pairing form. ``verify`` checks what
arrived: every received package passes ``validate_packscan``, the import reports
show the expected image count, and exactly one device was paired (the second
scan therefore travelled on the long-lived device credential, not a new code).
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


def serve(root: Path, offer_file: Path, port: int) -> int:
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
            time.sleep(1)
    finally:
        session.stop()
    return 0


def verify(root: Path, expected_scans: int, expected_images: int) -> int:
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
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--root", type=Path, required=True)
    verify_parser.add_argument("--expected-scans", type=int, required=True)
    verify_parser.add_argument("--expected-images", type=int, required=True)
    args = parser.parse_args()
    if args.command == "serve":
        return serve(args.root, args.offer_file, args.port)
    return verify(args.root, args.expected_scans, args.expected_images)


if __name__ == "__main__":
    raise SystemExit(main())
