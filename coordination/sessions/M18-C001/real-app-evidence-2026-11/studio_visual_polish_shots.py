"""PL-0464: screenshots of every Studio route (EN/TR, several sizes) from the real
StudioMainWindow offscreen, plus Capture Inbox in receiving state with one paired device
and one received scan, and a contact sheet. Synthetic loopback data only.

Usage: python studio_visual_polish_shots.py <repo_root> <out_dir> [--before]
"""

import hashlib
import json
import os
import ssl
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
BEFORE = "--before" in sys.argv
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))

from PySide6.QtCore import QSettings, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QPainter  # noqa: E402

from packlab_studio.app import create_application  # noqa: E402
from packlab_studio.navigation import Route  # noqa: E402
from packlab_studio.receiver_session import ReceiverSession  # noqa: E402
from packlab_studio.shell import StudioMainWindow  # noqa: E402
from tests.transfer.test_loopback_receiver import _package  # noqa: E402

app = create_application(["studio-visual-polish"])
WORK = Path(tempfile.mkdtemp(prefix="packlab-polish-"))


def pump(seconds: float = 0.25) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)


def call(url, body=None, token=None, headers=None):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # loopback; leaf pinned by fingerprint in real client
    request = urllib.request.Request(url, data=body, method="POST", headers=headers or {})
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, context=context) as response:
        return json.loads(response.read())


def make_window(lang: str, index: int) -> StudioMainWindow:
    settings = WORK / f"settings-{lang}-{index}.ini"
    QSettings(str(settings), QSettings.Format.IniFormat).setValue("ui/language", lang)
    kwargs = dict(
        receiver_session_factory=lambda: ReceiverSession(
            WORK / f"inbox-{lang}-{index}",
            tls_root=WORK / "tls",
            port=0,
            bind_host="127.0.0.1",
            lan_host_provider=lambda: "127.0.0.1",
        ),
        diagnostics_root=WORK / "diagnostics",
        packaging_library_root=WORK / f"library-{lang}-{index}",
    )
    if not BEFORE:
        kwargs["settings_path"] = settings
    window = StudioMainWindow(**kwargs)
    window.new_project(WORK / f"project-{lang}-{index}", "My scans")
    return window


def receive_state(window: StudioMainWindow) -> None:
    """Receiving, one paired device and one scan received over loopback Wi-Fi."""
    view = window.route_stack.views[Route.CAPTURE_INBOX]
    view.receive_button.click()
    offer = view.offer
    base = f"https://{offer.host}:{offer.port}"
    paired = call(
        f"{base}/v1/pair",
        body=json.dumps(
            {
                "offer": json.loads(offer.qr_payload()),
                "pairing_code": offer.pairing_code,
                "tls_certificate_fingerprint": offer.tls_certificate_fingerprint,
                "device_name": "iPhone 16",
            }
        ).encode(),
    )
    token = str(paired["session_token"])
    data = _package(WORK / f"capture-{id(window)}.packscan", REPO).read_bytes()
    create = {
        "message": "create_transfer",
        "protocol": "packlab-transfer",
        "protocol_version": "1",
        "transport": "https",
        "receiver_id": offer.receiver_instance_id,
        "transfer_id": f"shot-{id(window)}",
        "capture_id": "loopback-capture",
        "package_name": "capture.packscan",
        "total_bytes": len(data),
        "package_sha256": hashlib.sha256(data).hexdigest(),
    }
    tid = create["transfer_id"]
    call(f"{base}/v1/transfers", body=json.dumps(create).encode(), token=token)
    call(
        f"{base}/v1/transfers/{tid}/chunks",
        body=data,
        token=token,
        headers={
            "X-PackLab-Offset": "0",
            "X-PackLab-Chunk-SHA256": hashlib.sha256(data).hexdigest(),
        },
    )
    call(f"{base}/v1/transfers/{tid}/complete", token=token)
    view._tick()
    view.new_code()  # fresh code so the countdown bar is full in the screenshot


shots: list[Path] = []
SIZES = [(1280, 720), (1389, 868), (1920, 1080)]
tag = "before" if BEFORE else "after"
languages = ["en"] if BEFORE else ["en", "tr"]
for index, lang in enumerate(languages):
    window = make_window(lang, index)
    window.show()
    pump(0.5)
    for width, height in SIZES:
        window.resize(width, height)
        pump()
        for number, route in enumerate(Route, 1):
            window.navigation.navigate(route)
            pump(0.2)
            path = OUT / f"{tag}-{lang}-{width}x{height}-{number:02d}-{route.value}.png"
            window.grab().save(str(path))
            shots.append(path)
    receive_state(window)
    window.navigation.navigate(Route.CAPTURE_INBOX)
    for width, height in [(1389, 868), (2000, 1250)]:
        window.resize(width, height)
        pump(0.4)
        path = OUT / f"{tag}-{lang}-{width}x{height}-capture-inbox-receiving.png"
        window.grab().save(str(path))
        shots.append(path)
    # Page-level states (F7/F8/F16), synthetic data only.
    window.resize(1389, 868)

    def state_shot(name: str) -> None:
        pump(0.4)
        path = OUT / f"{tag}-{lang}-1389x868-state-{name}.png"
        window.grab().save(str(path))
        shots.append(path)

    window.navigation.navigate(Route.RECONSTRUCTION)
    state_shot("reconstruction-scan-list")
    viewer = window.route_stack.views[Route.MODEL_VIEWER]
    ply = WORK / f"synthetic-jar-{lang}.ply"
    import math as _m

    rows_ = [
        (40 * _m.cos(a / 40 * 2 * _m.pi) + 300, 40 * _m.sin(a / 40 * 2 * _m.pi) - 120, h * 2.0)
        for h in range(50)
        for a in range(40)
    ] + [(5000.0, 5000.0, 5000.0)]  # far outlier like a sparse SfM point
    ply.write_text(
        "ply\nformat ascii 1.0\nelement vertex %d\nproperty float x\nproperty float y\n"
        "property float z\nend_header\n" % len(rows_)
        + "".join(f"{x} {y} {z}\n" for x, y, z in rows_),
        encoding="ascii",
    )
    viewer.load(ply)
    window.navigation.navigate(Route.MODEL_VIEWER)
    viewer.fit_button.click()
    state_shot("model-viewer-fit")
    if not BEFORE:
        families = window.route_stack.views[Route.PACKAGE_FAMILIES]
        window.navigation.navigate(Route.PACKAGE_FAMILIES)
        families.family.setCurrentIndex(families.family.findData("jerrycan"))
        pump(0.2)
        families.create_button.click()
        state_shot("package-families-jerrycan")
    print(lang, "title:", window.windowTitle())
    window.route_stack.views[Route.CAPTURE_INBOX].stop_receiving()
    window.close()
    pump()

# Contact sheet: thumbnails with captions.
thumb_w, thumb_h, cols = 480, 300, 4
rows = (len(shots) + cols - 1) // cols
sheet = QImage(cols * thumb_w, rows * (thumb_h + 22), QImage.Format.Format_RGB32)
sheet.fill(QColor("white"))
painter = QPainter(sheet)
painter.setFont(QFont("Segoe UI", 8))
for i, path in enumerate(shots):
    image = QImage(str(path)).scaled(
        thumb_w - 8,
        thumb_h - 4,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    x, y = (i % cols) * thumb_w, (i // cols) * (thumb_h + 22)
    painter.drawImage(x + 4, y + 2, image)
    painter.setPen(QColor("black"))
    painter.drawText(x + 4, y + thumb_h + 16, path.stem)
painter.end()
sheet_path = OUT / f"contact-sheet-{tag}.png"
sheet.save(str(sheet_path))
print("shots:", len(shots), "sheet:", sheet_path)
