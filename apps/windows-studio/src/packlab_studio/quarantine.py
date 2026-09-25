"""Dedicated quarantine storage for invalid PackScan inputs."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    quarantine_id: str
    package_sha256: str | None
    source_channel: str
    capture_id: str | None
    error_code: str
    diagnostic: str
    package_preserved: bool
    quarantined_at: str


class QuarantineStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.packages = self.root / "packages"
        self.records = self.root / "records"
        self.packages.mkdir(parents=True, exist_ok=True)
        self.records.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_capture_id(source: Path) -> str | None:
        try:
            with zipfile.ZipFile(source) as archive:
                value = json.loads(archive.read("manifest.json").decode("utf-8"))
            capture_id = value.get("capture_id") if isinstance(value, dict) else None
            return capture_id if isinstance(capture_id, str) and 0 < len(capture_id) <= 128 else None
        except (OSError, KeyError, ValueError, zipfile.BadZipFile):
            return None

    def preserve(self, source: str | Path, *, source_channel: str, error_code: str, diagnostic: str) -> QuarantineRecord:
        path = Path(source)
        digest: str | None = None
        preserved = False
        if path.is_file():
            try:
                data = path.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                target = self.packages / f"{digest}.packscan"
                if not target.exists():
                    fd, temporary_name = tempfile.mkstemp(prefix=f".{digest}-", suffix=".part", dir=self.packages)
                    try:
                        with os.fdopen(fd, "wb") as handle:
                            handle.write(data)
                            handle.flush()
                            os.fsync(handle.fileno())
                        os.replace(temporary_name, target)
                    finally:
                        Path(temporary_name).unlink(missing_ok=True)
                preserved = True
            except OSError:
                digest = None
        quarantine_id = digest or hashlib.sha256(path.name.encode("utf-8", errors="replace")).hexdigest()
        record = QuarantineRecord(
            quarantine_id=quarantine_id, package_sha256=digest, source_channel=source_channel,
            capture_id=self._safe_capture_id(path) if digest else None, error_code=error_code,
            diagnostic=error_code, package_preserved=preserved,
            quarantined_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        )
        record_path = self.records / f"{quarantine_id}.json"
        events: list[dict[str, object]] = []
        if record_path.exists():
            try:
                existing = json.loads(record_path.read_text(encoding="utf-8"))
                events = existing.get("events", []) if isinstance(existing, dict) and isinstance(existing.get("events"), list) else []
            except (OSError, ValueError):
                events = []
        events.append({"source_channel": record.source_channel, "capture_id": record.capture_id, "error_code": record.error_code, "diagnostic": record.diagnostic, "package_preserved": record.package_preserved, "quarantined_at": record.quarantined_at})
        fd, temporary_name = tempfile.mkstemp(prefix=f".{quarantine_id}-", suffix=".json", dir=self.records)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump({"quarantine_id": quarantine_id, "package_sha256": digest, "events": events}, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, record_path)
        finally:
            Path(temporary_name).unlink(missing_ok=True)
        return record
