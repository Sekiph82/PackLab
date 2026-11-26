"""Drive the real StudioMainWindow offscreen like the owner would and save screenshots.

Phone side is simulated with the exact QR payload the window shows (same JSON the
iPhone scans), then the same /v1/pair + chunk upload the iOS client performs.
"""
import hashlib
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QListWidget, QPushButton

from packlab_studio.app import create_application
from packlab_studio.capture_inbox import CaptureInboxView
from packlab_studio.model_viewer import ModelViewerView
from packlab_studio.shell import StudioMainWindow

OUT = Path(r"<USERPROFILE>\Documents\PackLab-work\studio-e2e")
OUT.mkdir(parents=True, exist_ok=True)
ORIGINAL = Path(r"<USERPROFILE>\Downloads\44D2E8F0-4CCD-42DC-8B3F-DE9B82E4458C.packscan")
REPAIRED = Path(r"<USERPROFILE>\Documents\PackLab-work\test-333\test-333-import.packscan")
MODEL = Path(r"<USERPROFILE>\Documents\PackLab-work\test-333\mvs\scene_dense.ply")

app = create_application(["studio-e2e"])
window = StudioMainWindow()
window.resize(1400, 900)
window.show()


def pump(seconds: float = 0.3) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)


def shot(name: str) -> None:
    pump(0.3)
    window.grab().save(str(OUT / f"{name}.png"))
    print("screenshot", name)


def route(label: str) -> None:
    nav = window.findChild(QListWidget, "packlab.navigation.routes")
    for row in range(nav.count()):
        if nav.item(row).text().lower() == label.lower():
            nav.setCurrentRow(row)
            nav.itemClicked.emit(nav.item(row)) if hasattr(nav, "itemClicked") else None
            pump()
            return
    raise SystemExit(f"route {label} not found: {[nav.item(r).text() for r in range(nav.count())]}")


inbox = window.findChild(CaptureInboxView)
route("Capture Inbox")
shot("01-capture-inbox")

# Owner imports the file exactly as received from the phone (old iOS writer).
inbox._choose_file = lambda parent: str(ORIGINAL)
QTest.mouseClick(inbox.import_button, Qt.MouseButton.LeftButton)
shot("02-import-original-phone-file")
print("status after original:", inbox.status_label.text())

inbox._choose_file = lambda parent: str(REPAIRED)
QTest.mouseClick(inbox.import_button, Qt.MouseButton.LeftButton)
shot("03-import-repaired-file")
print("status after repaired:", inbox.status_label.text())
print("inbox rows:", [inbox.inbox_list.item(i).text() for i in range(inbox.inbox_list.count())])

# Simulated phone: read the QR payload, pair, upload the repaired package over HTTPS.
QTest.mouseClick(inbox.receive_button, Qt.MouseButton.LeftButton)
pump(1.0)
offer = inbox.offer
assert offer is not None, "no pairing offer on screen"
qr = json.loads(offer.qr_payload())
print("QR host/port:", qr["host"], qr["port"])
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE  # pinned below by fingerprint, like the iOS client
base = f"https://127.0.0.1:{qr['port']}"


def call(path, method="POST", body=None, token=None, raw=None, headers=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as error:
        raise SystemExit(f"{method} {path} -> {error.code} {error.read()[:300]!r}")


import socket
with socket.create_connection(("127.0.0.1", qr["port"])) as sock, ctx.wrap_socket(sock) as tls:
    served = hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest()
assert served == qr["tls_certificate_fingerprint"], "served certificate does not match QR pin"
token = call("/v1/pair", body={"offer": qr, "pairing_code": qr["pairing_code"], "tls_certificate_fingerprint": qr["tls_certificate_fingerprint"]})["session_token"]
data = REPAIRED.read_bytes()
digest = hashlib.sha256(data).hexdigest()
print("pair ok; uploading", len(data), "bytes")
from packlab_core.transfer_protocol import TransferCreate  # shape reference
import inspect
print("TransferCreate fields:", list(inspect.signature(TransferCreate).parameters))
sys.stdout.flush()

import uuid
from packlab_core.transfer_protocol import PROTOCOL_VERSION, REQUIRED_TRANSPORT
transfer_id = uuid.uuid4().hex
create = {"receiver_id": qr["receiver_instance_id"], "transfer_id": transfer_id, "capture_id": "44D2E8F0-4CCD-42DC-8B3F-DE9B82E4458C",
          "package_name": "simulated-iphone.packscan", "total_bytes": len(data), "package_sha256": digest,
          "protocol_version": PROTOCOL_VERSION, "transport": REQUIRED_TRANSPORT}
status = call("/v1/transfers", body=TransferCreate(**create).to_dict(), token=token)
offset = status.get("next_offset", 0)
while offset < len(data):
    chunk = data[offset:offset + 256 * 1024]
    status = call(f"/v1/transfers/{transfer_id}/chunks", raw=chunk, token=token,
                  headers={"Content-Type": "application/octet-stream", "X-PackLab-Offset": str(offset), "X-PackLab-Chunk-SHA256": hashlib.sha256(chunk).hexdigest()})
    offset = status.get("next_offset", offset + len(chunk))
ack = call(f"/v1/transfers/{transfer_id}/complete", token=token)
print("completion ack:", {k: ack.get(k) for k in ("state", "verified", "authenticated")})
pump(2.5)
shot("04-received-over-network")
print("inbox rows:", [inbox.inbox_list.item(i).text() for i in range(inbox.inbox_list.count())])

viewer = window.findChild(ModelViewerView)
route("Model Viewer")
viewer._choose_file = lambda parent: str(MODEL)
QTest.mouseClick(viewer.open_button, Qt.MouseButton.LeftButton)
pump(2.0)
shot("05-model-viewer-open")
viewer.orbit(60, 25); pump(1.0); shot("06-model-viewer-orbit")
window.close(); pump(1.0)
print("done")
