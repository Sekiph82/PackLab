"""Capture Inbox view: receive scans from the iPhone app or import .packscan files."""

from __future__ import annotations

import html
import io
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import segno
from PySide6.QtCore import QDateTime, QLocale, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QGuiApplication, QPixmap, QShowEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from packlab_core.pairing import PairingOffer

from .i18n import language, tr
from .receiver_session import InboxEntry, ReceiverSession
from .remote_control import RemoteControlError

QR_SIZE_PX = 260  # logical pixels; whole-module scaling keeps it crisp at any DPI
_SOURCES = {"network": "iPhone Wi-Fi", "picker": "File", "drop": "File"}


def qr_pixmap(payload: str, *, scale: int | None = None, target: int = QR_SIZE_PX) -> QPixmap:
    qr = segno.make(payload, error="m")
    ratio = QGuiApplication.primaryScreen().devicePixelRatio() if scale is None else 1.0
    if scale is None:
        modules = qr.symbol_size(scale=1, border=4)[0]
        scale = max(2, int(int(target * ratio) // modules))
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=scale, border=4)
    pixmap = QPixmap()
    pixmap.loadFromData(buffer.getvalue())
    pixmap.setDevicePixelRatio(ratio)
    return pixmap


def local_time(epoch: float | None) -> str:
    """Short local date/time; Turkish format when the UI language is Turkish."""
    if epoch is None:
        return tr("never")
    locale = QLocale(QLocale.Language.Turkish) if language() == "tr" else QLocale()
    stamp = QDateTime.fromSecsSinceEpoch(int(epoch))
    return locale.toString(stamp, locale.dateTimeFormat(QLocale.FormatType.ShortFormat))


def inbox_row(entry: InboxEntry) -> tuple[str, str]:
    """Plain-language row text and a tooltip carrying the technical audit identifiers."""
    name = (
        tr("Scan from {model}").format(model=entry.device_model)
        if entry.device_model
        else (tr("Scan"))
    )
    parts = [name]
    if entry.imported_at is not None:
        parts.append(local_time(entry.imported_at))
    if entry.image_count is not None:
        parts.append(tr("Photos: {count}").format(count=entry.image_count))
    parts.append(tr(_SOURCES.get(entry.source_channel, entry.source_channel or "?")))
    if entry.status != "imported":
        parts.append(entry.status)
    details = [
        f"capture_id: {entry.capture_id}",
        f"status: {entry.status}",
        f"source_channel: {entry.source_channel or '?'}",
        f"capture_mode: {entry.capture_mode or '?'}",
        f"sha256: {entry.package_sha256}",
    ]
    return "   ·   ".join(parts), "<br>".join(html.escape(line) for line in details)


class CaptureInboxView(QWidget):
    """Presentation-only view composed with accepted M05 services."""

    scan_imported = Signal(str, str)  # capture_id, package_sha256 of a newly imported scan
    build_requested = Signal(str, str)  # capture_id, package_sha256 chosen by the owner

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
        # Test seam: Finish scan closes the phone's scan, so it asks first.
        self._confirm: Callable[[QWidget, str], bool] = lambda parent, text: (
            QMessageBox.question(parent, "Finish scan", text) == QMessageBox.StandardButton.Yes
        )
        self.offer: PairingOffer | None = None
        self._shown_records: list[object] | None = None
        self._shown_entries: list[InboxEntry] = []
        self._known_imports: set[str] | None = None

        self.receive_button = QPushButton(tr("Receive from iPhone"), self)
        self.new_code_button = QPushButton("New code", self)
        self.stop_button = QPushButton("Stop receiving", self)
        self.stop_button.setEnabled(False)
        self.new_code_button.setEnabled(False)
        self.import_button = QPushButton("Import .packscan file…", self)
        self.qr_label = QLabel(self)
        self.qr_label.setObjectName("packlab.capture-inbox.qr")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.qr_label.setFixedSize(QR_SIZE_PX + 8, QR_SIZE_PX + 8)
        self.qr_label.hide()
        # Explicit receiving state instead of only a greyed-out button (PL-0464).
        self.receiving_label = QLabel("", self)
        self.receiving_label.setObjectName("packlab.capture-inbox.receiving")
        self.receiving_label.setWordWrap(True)
        self.receiving_label.setTextFormat(Qt.TextFormat.PlainText)
        bold = QFont(self.receiving_label.font())
        bold.setBold(True)
        self.receiving_label.setFont(bold)
        self.receiving_label.hide()
        self.code_refresh = QProgressBar(self)
        self.code_refresh.setObjectName("packlab.capture-inbox.code-refresh")
        self.code_refresh.setTextVisible(False)
        self.code_refresh.setMaximumHeight(8)
        self.code_refresh.setFixedWidth(260)
        self.code_refresh.hide()
        self.pairing_label = QLabel(
            "Press Receive from iPhone, then in the iPhone app choose Send to PackLab > "
            "Scan QR offer. The phone and this PC must be on the same Wi-Fi.",
            self,
        )
        self.pairing_label.setWordWrap(True)
        self.status_label = QLabel("", self)
        self.status_label.setWordWrap(True)
        # Shows phone-supplied device names: never interpret them as rich text.
        self.status_label.setTextFormat(Qt.TextFormat.PlainText)
        self.inbox_list = QListWidget(self)
        self.inbox_list.setObjectName("packlab.capture-inbox.list")
        self.inbox_list.setMinimumHeight(140)
        # Phones paired once send later scans automatically; Revoke unpairs one.
        self.devices_list = QListWidget(self)
        self.devices_list.setObjectName("packlab.capture-inbox.devices")
        self.devices_list.setMaximumHeight(90)
        self.revoke_button = QPushButton(tr("Revoke"), self)
        self.revoke_button.clicked.connect(self.revoke_selected_device)
        # PL-0429: a connected paired phone can be asked to capture / finish its scan.
        self.remote_label = QLabel("", self)
        self.remote_label.setObjectName("packlab.capture-inbox.remote")
        self.remote_label.setWordWrap(True)
        self.remote_label.setTextFormat(Qt.TextFormat.PlainText)
        self.capture_now_button = QPushButton("Capture now", self)
        self.finish_scan_button = QPushButton("Finish scan", self)
        self.capture_now_button.setEnabled(False)
        self.finish_scan_button.setEnabled(False)
        self.capture_now_button.clicked.connect(lambda: self.remote_command("capture"))
        self.finish_scan_button.clicked.connect(lambda: self.remote_command("finish"))
        self._remote_device: str | None = None
        self.build_button = QPushButton("Build model", self)
        self.build_button.setObjectName("packlab.capture-inbox.build")
        self.build_button.setEnabled(False)

        # Grouped sections inside a scroll area so nothing is cut off on small windows.
        content = QWidget(self)
        content.setObjectName("packlab.capture-inbox.content")
        buttons = QHBoxLayout()
        for button in (
            self.receive_button,
            self.new_code_button,
            self.stop_button,
            self.import_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch(1)
        pairing_text = QVBoxLayout()
        pairing_text.addWidget(self.receiving_label)
        pairing_text.addWidget(self.pairing_label)
        pairing_text.addWidget(self.code_refresh, 0, Qt.AlignmentFlag.AlignLeft)
        pairing_text.addWidget(self.status_label)
        pairing_text.addStretch(1)
        pairing_row = QHBoxLayout()
        pairing_row.addWidget(
            self.qr_label, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        pairing_row.addLayout(pairing_text, 1)
        receive_box = QGroupBox(tr("Receive scans"), content)
        receive_layout = QVBoxLayout(receive_box)
        receive_layout.addLayout(buttons)
        receive_layout.addLayout(pairing_row)
        devices_box = QGroupBox(tr("Paired devices"), content)
        devices_row = QHBoxLayout(devices_box)
        devices_row.addWidget(self.devices_list, 1)
        devices_row.addWidget(self.revoke_button, 0, Qt.AlignmentFlag.AlignTop)
        remote_box = QGroupBox(tr("Remote capture"), content)
        remote_row = QHBoxLayout(remote_box)
        remote_row.addWidget(self.remote_label, 1)
        remote_row.addWidget(self.capture_now_button, 0, Qt.AlignmentFlag.AlignTop)
        remote_row.addWidget(self.finish_scan_button, 0, Qt.AlignmentFlag.AlignTop)
        scans_box = QGroupBox(tr("Received scans"), content)
        scans_layout = QVBoxLayout(scans_box)
        scans_layout.addWidget(self.inbox_list, 1)
        build_row = QHBoxLayout()
        build_row.addWidget(self.build_button)
        build_row.addStretch(1)
        scans_layout.addLayout(build_row)
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(receive_box)
        content_layout.addWidget(devices_box)
        content_layout.addWidget(remote_box)
        content_layout.addWidget(scans_box, 1)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("packlab.capture-inbox.scroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setWidget(content)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)

        self._shut_down = False
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.receive_button.clicked.connect(lambda: self.start_receiving())
        self.new_code_button.clicked.connect(self.new_code)
        self.stop_button.clicked.connect(self.stop_receiving)
        self.import_button.clicked.connect(self.import_file)
        self.build_button.clicked.connect(self._request_build)
        self.inbox_list.currentRowChanged.connect(
            lambda row: self.build_button.setEnabled(
                0 <= row < len(self._shown_entries)
                and self._shown_entries[row].status == "imported"
            )
        )
        for button in (self.receive_button, self.import_button):
            button.setEnabled(session_factory is not None)

    @property
    def session(self) -> ReceiverSession | None:
        if self._session is None and self._session_factory is not None:
            self._session = self._session_factory()
            # Scans already in the inbox at startup are not "new imports". If the index
            # cannot be read now, the first successful refresh becomes the baseline
            # instead (fail closed: old scans never auto-build).
            try:
                self._known_imports = {
                    entry.package_sha256
                    for entry in self._session.entries()
                    if entry.status == "imported"
                }
            except Exception:
                self._known_imports = None
        return self._session

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self._session_factory is not None:
            self.refresh_inbox()

    def resume_for_paired_devices(self) -> None:
        """Start listening at launch when a phone already paired (no page visit needed)."""
        if self._shut_down or self._session_factory is None or self.timer.isActive():
            return
        try:
            session = self.session
            paired = session is not None and bool(session.paired_devices())
        except Exception:
            return  # unreadable device store: stay stopped, the page still offers Receive
        if paired:
            self.start_receiving(issue_code=False)

    def start_receiving(self, issue_code: bool = True) -> None:
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
        self.stop_button.setEnabled(True)
        self.receive_button.setText(tr("Receiving…"))
        self.receiving_label.setText(
            tr("Receiving on {address} — scan the QR code in the iPhone app.").format(
                address=f"{session.lan_host}:{session.port}"
            )
        )
        self.receiving_label.show()
        self.status_label.setText(tr("If Windows asks, allow PackLab on private networks."))
        if issue_code:
            self.new_code()
        else:  # auto-start for paired phones: no pairing code until the owner asks
            self.pairing_label.setText(
                tr("Paired phones can send now. Press New code to pair another.")
            )
        self.timer.start()

    def stop_receiving(self) -> None:
        """Close the LAN listener; pairing codes stop being issued."""
        self.timer.stop()
        if self._session is not None:
            self._session.stop()
        self.offer = None
        self.qr_label.clear()
        self.qr_label.hide()
        self.code_refresh.hide()
        self.receiving_label.hide()
        self.receive_button.setText(tr("Receive from iPhone"))
        self.pairing_label.setText(tr("Not receiving."))
        self.status_label.setText(tr("Receiver stopped."))
        self.receive_button.setEnabled(True)
        self.new_code_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.refresh_remote()

    def new_code(self) -> None:
        session = self.session
        if session is None or not session.running:
            return
        self.offer = session.new_offer()
        self.qr_label.setPixmap(qr_pixmap(self.offer.qr_payload()))
        self.qr_label.show()
        lifetime = max(1, int(self.offer.expires_at - time.time()))
        self.code_refresh.setRange(0, lifetime)
        self.code_refresh.show()
        self._update_pairing_text()

    def _update_pairing_text(self) -> None:
        if self.offer is None:
            return
        remaining = max(0, int(self.offer.expires_at - time.time()))
        code = self.offer.pairing_code
        # A calm countdown bar instead of "expires in 2 s"; a new code appears by itself.
        self.code_refresh.setValue(min(remaining, self.code_refresh.maximum()))
        self.pairing_label.setText(
            tr("Pairing code: {code}").format(code=f"{code[:4]}-{code[4:]}")
            + "\n"
            + tr("Address: {address}").format(address=f"{self.offer.host}:{self.offer.port}")
            + "\n"
            + tr("The code refreshes automatically.")
        )

    def _tick(self) -> None:
        if self.offer is not None and self.offer.expires_at <= time.time():
            self.new_code()  # one-time offers expire; keep a fresh one on screen
        else:
            self._update_pairing_text()
        self.refresh_inbox()

    def refresh_devices(self) -> None:
        session = self.session
        if session is None:
            return
        devices = session.paired_devices()
        shown = [
            self.devices_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.devices_list.count())
        ]
        if shown == [device.device_id for device in devices]:
            return
        self.devices_list.clear()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        for device in devices:
            item = QListWidgetItem(
                icon,
                f"{device.device_name}  —  "
                + tr("paired {when}").format(when=local_time(device.paired_at))
                + "  —  "
                + tr("last seen {when}").format(when=local_time(device.last_seen_at)),
            )
            item.setData(Qt.ItemDataRole.UserRole, device.device_id)
            self.devices_list.addItem(item)

    def refresh_remote(self) -> None:
        """Live status the selected (or only) paired phone pushes while it polls."""
        session = self.session
        item = self.devices_list.currentItem()
        if item is None and self.devices_list.count() == 1:
            item = self.devices_list.item(0)
        self._remote_device = None if item is None else str(item.data(Qt.ItemDataRole.UserRole))
        ready = False
        if session is None or not session.running or self._remote_device is None:
            text = tr("Start receiving and select a paired phone to control its capture.")
        elif not session.receiver.control.connected(self._remote_device):
            text = tr(
                "Phone not connected. On the iPhone start a scan and turn on "
                "Allow PackLab to trigger captures."
            )
        else:
            status = session.receiver.control.status(self._remote_device)
            if status is None or not status.scan_active:
                text = tr("Phone connected, no active scan.")
            elif not status.control_enabled:
                text = f"{status.scan_name}: remote capture is turned off on the phone."
            else:
                ready = True
                text = (
                    f"{status.scan_name}  |  coverage {status.coverage_captured}/"
                    f"{status.coverage_total}  |  {status.instruction}"
                )
            last = None if status is None else status.last_result
            if last is not None:
                reasons = f" ({', '.join(last.reasons)})" if last.reasons else ""
                text += f"\nLast {last.action}: {last.outcome}{reasons} {last.message}".rstrip()
        self.remote_label.setText(text)
        self.capture_now_button.setEnabled(ready)
        self.finish_scan_button.setEnabled(ready)

    def remote_command(self, action: str) -> None:
        session = self.session
        if session is None or self._remote_device is None:
            return
        if action == "finish" and not self._confirm(
            self, "Finish the scan on the phone now? It is finalized and sent to PackLab."
        ):
            return
        try:
            session.receiver.control.issue(self._remote_device, action)
        except RemoteControlError as error:
            self.status_label.setText(f"Remote {action} not sent: {error.code}")
            return
        self.status_label.setText(
            "Capture request sent; the phone still checks every capture gate."
            if action == "capture"
            else "Finish request sent to the phone."
        )

    def revoke_selected_device(self) -> None:
        session = self.session
        item = self.devices_list.currentItem()
        if session is None or item is None:
            return
        if session.revoke_device(str(item.data(Qt.ItemDataRole.UserRole))):
            self.status_label.setText(f"Revoked {item.text().split('  ')[0]}; it must pair again.")
        self.refresh_devices()

    def refresh_inbox(self) -> None:
        session = self.session
        if session is None:
            return
        self.refresh_devices()
        self.refresh_remote()
        try:
            records: list[object] = list(session.index_records())
        except Exception as error:
            self.status_label.setText(f"Inbox index unavailable: {error}")
            return
        if records == self._shown_records:
            return
        self._shown_records = records
        self._shown_entries = session.entries()
        self.inbox_list.clear()
        style = self.style()
        for entry in self._shown_entries:
            text, details = inbox_row(entry)
            icon = style.standardIcon(
                QStyle.StandardPixmap.SP_DialogApplyButton
                if entry.status == "imported"
                else QStyle.StandardPixmap.SP_MessageBoxWarning
            )
            item = QListWidgetItem(icon, text)
            item.setToolTip(details)  # technical identifiers stay available for audit
            self.inbox_list.addItem(item)
        imported = {e.package_sha256 for e in self._shown_entries if e.status == "imported"}
        if self._known_imports is None:
            self._known_imports = imported
            return
        known = self._known_imports
        for entry in self._shown_entries:
            if entry.status == "imported" and entry.package_sha256 not in known:
                known.add(entry.package_sha256)
                self.scan_imported.emit(entry.capture_id, entry.package_sha256)
        self._known_imports = known

    def _request_build(self) -> None:
        row = self.inbox_list.currentRow()
        if 0 <= row < len(self._shown_entries):
            entry = self._shown_entries[row]
            self.build_requested.emit(entry.capture_id, entry.package_sha256)

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
        self._shut_down = True
        self.timer.stop()
        if self._session is not None:
            self._session.stop()
