"""Capture Inbox view: receive scans from the iPhone app or import .packscan files."""

from __future__ import annotations

import io
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import segno
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QShowEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from packlab_core.pairing import PairingOffer

from .receiver_session import ReceiverSession


def qr_pixmap(payload: str, *, scale: int = 5) -> QPixmap:
    buffer = io.BytesIO()
    segno.make(payload, error="m").save(buffer, kind="png", scale=scale, border=4)
    pixmap = QPixmap()
    pixmap.loadFromData(buffer.getvalue())
    return pixmap


class CaptureInboxView(QWidget):
    """Presentation-only view composed with accepted M05 services."""

    def __init__(
        self,
        *,
        ingest_controller: Any = None,
        receiver: Any = None,
        session_factory: Callable[[], ReceiverSession] | None = None,
        file_chooser: Callable[[QWidget], str] | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("packlab.view.capture-inbox")
        self.ingest_controller = ingest_controller
        self.receiver = receiver
        self._session_factory = session_factory
        self._session: ReceiverSession | None = None
        self._choose_file = file_chooser or (
            lambda parent: QFileDialog.getOpenFileName(
                parent, "Import PackScan", "", "PackScan packages (*.packscan)"
            )[0]
        )
        self.offer: PairingOffer | None = None
        self._shown_records: list[object] | None = None

        self.receive_button = QPushButton("Receive from iPhone", self)
        self.new_code_button = QPushButton("New code", self)
        self.new_code_button.setEnabled(False)
        self.import_button = QPushButton("Import .packscan file…", self)
        self.qr_label = QLabel(self)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pairing_label = QLabel(
            "Press Receive from iPhone, then in the iPhone app choose Send to PackLab > "
            "Scan QR offer. The phone and this PC must be on the same Wi-Fi.",
            self,
        )
        self.pairing_label.setWordWrap(True)
        self.status_label = QLabel("", self)
        self.status_label.setWordWrap(True)
        self.inbox_list = QListWidget(self)
        self.inbox_list.setObjectName("packlab.capture-inbox.list")

        buttons = QHBoxLayout()
        for button in (self.receive_button, self.new_code_button, self.import_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Capture Inbox"))
        layout.addLayout(buttons)
        layout.addWidget(self.qr_label)
        layout.addWidget(self.pairing_label)
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("Received scans"))
        layout.addWidget(self.inbox_list, 1)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.receive_button.clicked.connect(self.start_receiving)
        self.new_code_button.clicked.connect(self.new_code)
        self.import_button.clicked.connect(self.import_file)
        for button in (self.receive_button, self.import_button):
            button.setEnabled(session_factory is not None)

    @property
    def session(self) -> ReceiverSession | None:
        if self._session is None and self._session_factory is not None:
            self._session = self._session_factory()
        return self._session

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self._session_factory is not None:
            self.refresh_inbox()

    def start_receiving(self) -> None:
        session = self.session
        if session is None:
            return
        try:
            session.start()
        except Exception as error:  # surfaced to the owner, receiver stays stopped
            self.status_label.setText(f"Receiver could not start: {error}")
            return
        self.receive_button.setEnabled(False)
        self.new_code_button.setEnabled(True)
        self.status_label.setText(
            f"Listening on {session.lan_host}:{session.port}. If Windows asks, allow "
            "PackLab on private networks."
        )
        self.new_code()
        self.timer.start()

    def new_code(self) -> None:
        session = self.session
        if session is None or not session.running:
            return
        self.offer = session.new_offer()
        self.qr_label.setPixmap(qr_pixmap(self.offer.qr_payload()))
        self._update_pairing_text()

    def _update_pairing_text(self) -> None:
        if self.offer is None:
            return
        remaining = max(0, int(self.offer.expires_at - time.time()))
        code = self.offer.pairing_code
        self.pairing_label.setText(
            f"Pairing code {code[:4]}-{code[4:]}  |  {self.offer.host}:{self.offer.port}  |  "
            f"expires in {remaining} s"
        )

    def _tick(self) -> None:
        if self.offer is not None and self.offer.expires_at <= time.time():
            self.new_code()  # one-time offers expire; keep a fresh one on screen
        else:
            self._update_pairing_text()
        self.refresh_inbox()

    def refresh_inbox(self) -> None:
        session = self.session
        if session is None:
            return
        try:
            records: list[object] = list(session.index_records())
        except Exception as error:
            self.status_label.setText(f"Inbox index unavailable: {error}")
            return
        if records == self._shown_records:
            return
        self._shown_records = records
        self.inbox_list.clear()
        for entry in session.entries():
            images = "" if entry.image_count is None else f", {entry.image_count} images"
            self.inbox_list.addItem(
                f"{entry.capture_id}  [{entry.status}{images}, {entry.source_channel or '?'}]  "
                f"sha256 {entry.package_sha256[:12]}"
            )

    def import_file(self) -> None:
        session = self.session
        if session is None:
            return
        chosen = self._choose_file(self)
        if not chosen:
            return
        # ponytail: runs on the UI thread; move to JobManager if large packages stall the UI.
        result = session.import_file(Path(chosen))
        detail = f" ({result.error_code})" if result.error_code else ""
        self.status_label.setText(f"Import {result.source_name}: {result.state}{detail}")
        self.refresh_inbox()

    def shutdown(self) -> None:
        self.timer.stop()
        if self._session is not None:
            self._session.stop()
