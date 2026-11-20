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
        assert len(rows) == 1 and "loopback-capture" in rows[0] and "imported" in rows[0]
        assert "network" in rows[0]
        previous = view.offer
        view.new_code_button.click()
        assert view.offer is not None and view.offer.pairing_id != previous.pairing_id
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
        assert len(rows) == 1 and "loopback-capture" in rows[0] and "picker" in rows[0]
        view.import_button.click()
        assert "duplicate" in view.status_label.text()
        assert view.session is not None and not view.session.running
    finally:
        window.close()
        app.processEvents()
