from __future__ import annotations

import hashlib
import json
import ssl
import urllib.request
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from tests.transfer.test_loopback_receiver import _package

from packlab_core.pairing import PairingOffer
from packlab_studio.app import create_application
from packlab_studio.capture_inbox import CaptureInboxView
from packlab_studio.navigation import Route
from packlab_studio.receiver_session import ReceiverSession
from packlab_studio.shell import StudioMainWindow


def _insecure_pinned_context() -> ssl.SSLContext:
    # Mirrors iOS: no CA trust; the leaf is pinned by fingerprint (checked in transfer tests).
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _call(
    url: str,
    *,
    body: bytes | None = None,
    token: str | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, object]:
    request = urllib.request.Request(url, data=body, method="POST", headers=headers or {})
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, context=_insecure_pinned_context()) as response:
        return json.loads(response.read())


def _window(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **view_kwargs: object):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-capture-inbox-test"])
    window = StudioMainWindow(
        receiver_session_factory=lambda: ReceiverSession(
            tmp_path / "inbox",
            tls_root=tmp_path / "tls",
            port=0,
            bind_host="127.0.0.1",
            lan_host_provider=lambda: "127.0.0.1",
        ),
        diagnostics_root=tmp_path / "diagnostics",
        packaging_library_root=tmp_path / "library",
    )
    view = window.route_stack.views[Route.CAPTURE_INBOX]
    assert isinstance(view, CaptureInboxView)
    for key, value in view_kwargs.items():
        setattr(view, key, value)
    return app, window, view


def test_capture_inbox_is_reachable_without_a_project(monkeypatch, tmp_path) -> None:
    app, window, view = _window(monkeypatch, tmp_path)
    item = window.navigation_panel.list.item(1)
    assert item.data(0x0100) == Route.CAPTURE_INBOX.value
    assert item.flags() & Qt.ItemFlag.ItemIsEnabled
    assert view.isEnabled() and view.receive_button.isEnabled()
    window.close()
    app.processEvents()


def test_receive_from_iphone_pairs_uploads_and_lists_scan(monkeypatch, tmp_path, repo_root) -> None:
    app, window, view = _window(monkeypatch, tmp_path)
    try:
        view.receive_button.click()
        session = view.session
        assert session is not None and session.running
        assert view.offer is not None and not view.qr_label.pixmap().isNull()
        # The phone only sees the QR text.
        offer = PairingOffer.from_qr_payload(view.offer.qr_payload())
        assert offer == view.offer
        code = offer.pairing_code
        assert f"{code[:4]}-{code[4:]}" in view.pairing_label.text()
        assert f"127.0.0.1:{session.port}" in view.pairing_label.text()
        base = f"https://{offer.host}:{offer.port}"
        paired = _call(
            f"{base}/v1/pair",
            body=json.dumps(
                {
                    "offer": json.loads(view.offer.qr_payload()),
                    "pairing_code": offer.pairing_code,
                    "tls_certificate_fingerprint": offer.tls_certificate_fingerprint,
                }
            ).encode(),
        )
        token = str(paired["session_token"])
        data = _package(tmp_path / "capture.packscan", repo_root).read_bytes()
        create = {
            "message": "create_transfer",
            "protocol": "packlab-transfer",
            "protocol_version": "1",
            "transport": "https",
            "receiver_id": offer.receiver_instance_id,
            "transfer_id": "ui-transfer",
            "capture_id": "loopback-capture",
            "package_name": "capture.packscan",
            "total_bytes": len(data),
            "package_sha256": hashlib.sha256(data).hexdigest(),
        }
        _call(f"{base}/v1/transfers", body=json.dumps(create).encode(), token=token)
        _call(
            f"{base}/v1/transfers/ui-transfer/chunks",
            body=data,
            token=token,
            headers={
                "X-PackLab-Offset": "0",
                "X-PackLab-Chunk-SHA256": hashlib.sha256(data).hexdigest(),
            },
        )
        ack = _call(f"{base}/v1/transfers/ui-transfer/complete", token=token)
        assert ack["verified"] is True
        view._tick()
        rows = [view.inbox_list.item(i).text() for i in range(view.inbox_list.count())]
        tips = [view.inbox_list.item(i).toolTip() for i in range(view.inbox_list.count())]
        # PL-0464: plain-language row; technical identifiers move to the tooltip.
        assert len(rows) == 1 and "iPhone Wi-Fi" in rows[0] and "Photos: " in rows[0]
        assert "loopback-capture" in tips[0] and "status: imported" in tips[0]
        assert "source_channel: network" in tips[0]
        previous = view.offer
        view.new_code_button.click()
        assert view.offer is not None and view.offer.pairing_id != previous.pairing_id
        # Review MEDIUM 3: the owner can stop listening on the LAN.
        view.stop_button.click()
        assert not session.running and view.offer is None
        assert view.receive_button.isEnabled() and not view.stop_button.isEnabled()
    finally:
        window.close()
        app.processEvents()
    assert not session.running


def test_import_packscan_file_uses_same_inbox(monkeypatch, tmp_path, repo_root) -> None:
    package = _package(tmp_path / "whatsapp.packscan", repo_root)
    app, window, view = _window(monkeypatch, tmp_path, _choose_file=lambda _parent: str(package))
    try:
        view.import_button.click()
        assert "reported" in view.status_label.text()
        rows = [view.inbox_list.item(i).text() for i in range(view.inbox_list.count())]
        tips = [view.inbox_list.item(i).toolTip() for i in range(view.inbox_list.count())]
        assert len(rows) == 1 and "File" in rows[0]
        assert "loopback-capture" in tips[0] and "source_channel: picker" in tips[0]
        view.import_button.click()
        assert "duplicate" in view.status_label.text()
        assert view.session is not None and not view.session.running
    finally:
        window.close()
        app.processEvents()


def test_paired_devices_are_listed_and_revoke_unpairs(monkeypatch, tmp_path) -> None:
    app, window, view = _window(monkeypatch, tmp_path)
    try:
        view.receive_button.click()
        assert view.offer is not None and view.devices_list.count() == 0
        offer = view.offer
        paired = _call(
            f"https://{offer.host}:{offer.port}/v1/pair",
            body=json.dumps(
                {
                    "offer": json.loads(offer.qr_payload()),
                    "pairing_code": offer.pairing_code,
                    "tls_certificate_fingerprint": offer.tls_certificate_fingerprint,
                    "device_name": "iPhone17,3",
                }
            ).encode(),
        )
        view._tick()
        assert view.devices_list.count() == 1
        assert view.devices_list.item(0).text().startswith("iPhone17,3")
        view.devices_list.setCurrentRow(0)
        view.revoke_button.click()
        assert view.devices_list.count() == 0 and "Revoked iPhone17,3" in view.status_label.text()
        # Phone-supplied names must never be rendered as rich text.
        assert view.status_label.textFormat() == Qt.TextFormat.PlainText
        session = view.session
        assert session is not None
        assert not session.receiver.devices.is_active(str(paired["device_id"]))
    finally:
        window.close()
        app.processEvents()


def test_remote_capture_panel_sends_commands_and_shows_phone_status(monkeypatch, tmp_path) -> None:
    """PL-0429: Studio queues Capture now / Finish scan for a polling phone; revoke ends it."""
    app, window, view = _window(monkeypatch, tmp_path)
    try:
        view.receive_button.click()
        offer = view.offer
        assert offer is not None
        assert not view.capture_now_button.isEnabled()
        base = f"https://{offer.host}:{offer.port}"
        paired = _call(
            f"{base}/v1/pair",
            body=json.dumps(
                {
                    "offer": json.loads(offer.qr_payload()),
                    "pairing_code": offer.pairing_code,
                    "tls_certificate_fingerprint": offer.tls_certificate_fingerprint,
                    "device_name": "iPhone17,3",
                }
            ).encode(),
        )
        device_id = str(paired["device_id"])
        token = str(paired["session_token"])
        view._tick()
        assert "not connected" in view.remote_label.text()
        session = view.session
        assert session is not None
        control = session.receiver.control
        control.next_command(device_id, timeout=0)  # the phone polled once
        status = {
            "scan_active": True,
            "control_enabled": True,
            "scan_name": "Bottle <b>1</b>",
            "coverage_captured": 2,
            "coverage_total": 16,
            "instruction": "Hold here — tap Manual Capture",
            "last_result": None,
        }
        _call(f"{base}/v1/control/status", token=token, body=json.dumps(status).encode())
        view._tick()
        assert "Bottle <b>1</b>  |  coverage 2/16  |  Hold here" in view.remote_label.text()
        assert view.remote_label.textFormat() == Qt.TextFormat.PlainText
        assert view.capture_now_button.isEnabled() and view.finish_scan_button.isEnabled()
        view.capture_now_button.click()
        assert "still checks every capture gate" in view.status_label.text()
        view.capture_now_button.click()  # a second click while the first is pending
        assert "command_pending" in view.status_label.text()
        command = control.next_command(device_id, timeout=0)
        assert command is not None and command["action"] == "capture"
        status["last_result"] = {
            "command_id": command["command_id"],
            "action": "capture",
            "outcome": "refused",
            "reasons": ["object_not_in_view"],
            "message": "point the camera at the package",
        }
        control.report(device_id, status)
        view._tick()
        assert "Last capture: refused (object_not_in_view)" in view.remote_label.text()
        asked: list[str] = []
        view._confirm = lambda _parent, text: asked.append(text) or False
        view.finish_scan_button.click()  # declined: nothing is sent
        assert len(asked) == 1 and "Finish the scan" in asked[0]
        assert control.next_command(device_id, timeout=0) is None
        view._confirm = lambda _parent, _text: True
        view.finish_scan_button.click()
        finish = control.next_command(device_id, timeout=0)
        assert finish is not None and finish["action"] == "finish"
        view.devices_list.setCurrentRow(0)
        view.revoke_button.click()
        view._tick()
        assert not view.capture_now_button.isEnabled()
        assert control.status(device_id) is None
    finally:
        window.close()
        app.processEvents()


def test_receiver_starts_at_launch_only_when_a_phone_is_paired(monkeypatch, tmp_path) -> None:
    """Pair once: after a restart the paired phone can send without visiting the page."""
    app, window, view = _window(monkeypatch, tmp_path)
    try:
        app.processEvents()
        assert view._session is None  # a plain window never creates the receiver session
        window.resume_paired_receiver()
        assert not view.timer.isActive() and view.receive_button.isEnabled()  # nobody paired
        view.receive_button.click()
        offer = view.offer
        assert offer is not None
        _call(
            f"https://{offer.host}:{offer.port}/v1/pair",
            body=json.dumps(
                {
                    "offer": json.loads(offer.qr_payload()),
                    "pairing_code": offer.pairing_code,
                    "tls_certificate_fingerprint": offer.tls_certificate_fingerprint,
                    "device_name": "iPhone17,3",
                }
            ).encode(),
        )
    finally:
        window.close()
        app.processEvents()
    app, window, view = _window(monkeypatch, tmp_path)
    try:
        app.processEvents()
        assert view._session is None  # still nothing until the launch path asks
        window.resume_paired_receiver()
        assert view.timer.isActive() and not view.receive_button.isEnabled()
        assert view.session is not None and view.session.running
        assert view.offer is None  # no pairing code is issued unless the owner asks
        view._tick()
        assert view.offer is None
    finally:
        window.close()
        app.processEvents()
    view.resume_for_paired_devices()  # after shutdown: never restarts
    assert view.session is not None and not view.session.running
