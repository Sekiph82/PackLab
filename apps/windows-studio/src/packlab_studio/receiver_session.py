"""Qt-free owner of the Studio "Receive from iPhone" receiver and capture inbox."""

from __future__ import annotations

import json
import socket
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from packlab_core.packscan.part_roles import DEFAULT_PART_ROLE, is_part_role
from packlab_core.pairing import PairedDevice, PairingOffer
from packlab_core.transfer_security import ensure_receiver_tls_identity

from .ingest import ImportResult
from .ingest_index import IngestIndexRecord
from .receiver import PackLabReceiver

DEFAULT_RECEIVER_PORT = 8443


def detect_lan_ipv4() -> str:
    """Return the IPv4 address of the interface that routes off-host.

    Connecting a UDP socket only selects a route; no packet is sent. Falls back
    to loopback when the PC has no network.
    """

    # Default route first (the Wi-Fi a phone shares), then any private route.
    for target in (("8.8.8.8", 80), ("10.255.255.255", 1)):
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(target)
            address = str(probe.getsockname()[0])
        except OSError:
            continue
        finally:
            probe.close()
        if address != "0.0.0.0":
            return address
    return "127.0.0.1"


@dataclass(frozen=True, slots=True)
class InboxEntry:
    capture_id: str
    package_sha256: str
    status: str
    source_channel: str = ""
    image_count: int | None = None
    capture_mode: str = ""
    device_model: str = ""  # from the import report; display only
    imported_at: float | None = None  # import report write time (epoch seconds)
    part_role: str = DEFAULT_PART_ROLE  # manifest role (PL-0482); old reports = assembled
    role_declared: bool = False  # the manifest itself named the role


class ReceiverSession:
    """One per-user receiver root (outside the repository) shared by network and file import."""

    def __init__(
        self,
        data_root: str | Path,
        *,
        tls_root: str | Path | None = None,
        port: int = DEFAULT_RECEIVER_PORT,
        bind_host: str = "0.0.0.0",
        lan_host_provider: Callable[[], str] = detect_lan_ipv4,
    ) -> None:
        self.data_root = Path(data_root)
        self.tls_root = Path(tls_root) if tls_root is not None else self.data_root / "tls"
        self.data_root.mkdir(parents=True, exist_ok=True)
        id_path = self.data_root / "receiver-id"
        if not id_path.is_file():
            id_path.write_text(uuid.uuid4().hex, encoding="ascii")
        self._preferred_port = port
        self._lan_host_provider = lan_host_provider
        self.lan_host = "127.0.0.1"
        self.receiver = PackLabReceiver(
            self.data_root,
            receiver_id=id_path.read_text(encoding="ascii").strip(),
            host=bind_host,
            port=port,
        )
        self._summaries: dict[str, InboxEntry] = {}

    @property
    def running(self) -> bool:
        return self.receiver.running

    @property
    def port(self) -> int:
        return self.receiver.port

    def start(self) -> None:
        if self.running:
            return
        self.lan_host = self._lan_host_provider()
        hosts = list(dict.fromkeys([self.lan_host, "127.0.0.1"]))
        self.receiver.use_tls_identity(ensure_receiver_tls_identity(self.tls_root, hosts=hosts))
        self.receiver.port = self._preferred_port
        try:
            self.receiver.start()
        except OSError:
            # Preferred port busy: take any free port; the QR carries the real one.
            self.receiver.port = 0
            self.receiver.start()

    def new_offer(self, ttl_seconds: int = 120) -> PairingOffer:
        return self.receiver.pairing_offer(host=self.lan_host, ttl_seconds=ttl_seconds)

    def stop(self) -> None:
        self.receiver.stop()

    def paired_devices(self) -> list[PairedDevice]:
        """Phones that paired once and may send without a new code (revoked ones excluded)."""
        return [device for device in self.receiver.devices.devices() if device.active]

    def revoke_device(self, device_id: str) -> bool:
        return self.receiver.revoke_device(device_id)

    def import_file(self, path: str | Path) -> ImportResult:
        return self.receiver.ingest.import_path(path, source_channel="picker")

    def index_records(self) -> list[IngestIndexRecord]:
        index = self.receiver.ingest.index
        return index.records() if index is not None else []

    def package_path(self, package_sha256: str) -> Path | None:
        """Location of an imported package in this inbox's immutable raw store."""
        for record in self.index_records():
            if record.package_sha256 == package_sha256:
                return self.data_root / record.raw_location
        return None

    def entries(self) -> list[InboxEntry]:
        return [self._entry(record) for record in self.index_records()]

    def _entry(self, record: IngestIndexRecord) -> InboxEntry:
        if record.report_location is None:
            return InboxEntry(record.capture_id, record.package_sha256, "stored (no report)")
        cached = self._summaries.get(record.package_sha256)
        if cached is not None:
            return cached
        try:
            report_path = self.data_root / record.report_location
            report = json.loads(report_path.read_text("utf-8"))
            device = report.get("device_summary")
            role = report.get("part_role")
            entry = InboxEntry(
                record.capture_id,
                record.package_sha256,
                "imported",
                str(report.get("source_channel", "")),
                int(report.get("image_count", 0)),
                str(report.get("capture_mode", "")),
                str(device.get("model", "")) if isinstance(device, dict) else "",
                report_path.stat().st_mtime,
                str(role) if is_part_role(role) else DEFAULT_PART_ROLE,
                is_part_role(role),
            )
        except (OSError, ValueError, TypeError):
            return InboxEntry(record.capture_id, record.package_sha256, "report unreadable")
        self._summaries[record.package_sha256] = entry
        return entry
