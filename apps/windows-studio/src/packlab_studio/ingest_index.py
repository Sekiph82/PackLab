"""Crash-safe capture ID/package digest deduplication index."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock


class IngestIdentityConflict(RuntimeError):
    def __init__(self, code: str, *, capture_id: str | None = None, existing_digest: str | None = None, incoming_digest: str | None = None) -> None:
        self.code = code
        self.capture_id = capture_id
        self.existing_digest = existing_digest
        self.incoming_digest = incoming_digest
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class IngestIndexRecord:
    capture_id: str
    package_sha256: str
    raw_location: str
    report_location: str | None = None


class IngestIndex:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _read(self) -> list[IngestIndexRecord]:
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            records = value.get("records", []) if isinstance(value, dict) else []
            return [IngestIndexRecord(**record) for record in records]
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise IngestIdentityConflict("index_corrupt") from error

    def _write(self, records: list[IngestIndexRecord]) -> None:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{self.path.name}-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump({"records": [asdict(record) for record in records]}, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.path)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    def lookup(self, capture_id: str, package_sha256: str) -> IngestIndexRecord | None:
        with self._lock:
            for record in self._read():
                if record.capture_id == capture_id:
                    if record.package_sha256 == package_sha256:
                        return record
                    raise IngestIdentityConflict("capture_id_conflict", capture_id=capture_id, existing_digest=record.package_sha256, incoming_digest=package_sha256)
                if record.package_sha256 == package_sha256:
                    raise IngestIdentityConflict("digest_identity_ambiguity", capture_id=capture_id, existing_digest=record.package_sha256, incoming_digest=package_sha256)
        return None

    def register(self, record: IngestIndexRecord) -> IngestIndexRecord:
        with self._lock:
            records = self._read()
            for existing in records:
                if existing.capture_id == record.capture_id:
                    if existing.package_sha256 == record.package_sha256:
                        if existing.report_location is None and record.report_location is not None:
                            updated = IngestIndexRecord(existing.capture_id, existing.package_sha256, existing.raw_location, record.report_location)
                            records[records.index(existing)] = updated
                            self._write(records)
                            return updated
                        return existing
                    raise IngestIdentityConflict("capture_id_conflict", capture_id=record.capture_id, existing_digest=existing.package_sha256, incoming_digest=record.package_sha256)
                if existing.package_sha256 == record.package_sha256:
                    raise IngestIdentityConflict("digest_identity_ambiguity", capture_id=record.capture_id, existing_digest=existing.package_sha256, incoming_digest=record.package_sha256)
            records.append(record)
            records.sort(key=lambda item: (item.capture_id, item.package_sha256))
            self._write(records)
            return record

    def records(self) -> list[IngestIndexRecord]:
        with self._lock:
            return list(self._read())

    def verify_against_raw_metadata(self, raw_root: str | Path) -> list[IngestIndexRecord]:
        """Verify or reconstruct from immutable raw-store metadata.

        A missing index is rebuilt deterministically. A corrupt index is only
        replaced when every raw metadata record is self-consistent; otherwise
        the authority remains fail-closed.
        """
        root = Path(raw_root)
        authoritative: list[IngestIndexRecord] = []
        for metadata in sorted(root.glob("*.json")):
            try:
                value = json.loads(metadata.read_text(encoding="utf-8"))
                record = IngestIndexRecord(
                    capture_id=value["capture_id"], package_sha256=value["package_sha256"],
                    raw_location=f"raw/{value['raw_filename']}", report_location=None,
                )
            except (OSError, ValueError, TypeError, KeyError) as error:
                raise IngestIdentityConflict("raw_metadata_corrupt") from error
            package = root / record.raw_location.removeprefix("raw/")
            if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != record.package_sha256:
                raise IngestIdentityConflict("raw_metadata_digest_mismatch", capture_id=record.capture_id, incoming_digest=record.package_sha256)
            authoritative.append(record)
        authoritative.sort(key=lambda item: (item.capture_id, item.package_sha256))
        with self._lock:
            try:
                current = self._read() if self.path.exists() else []
            except IngestIdentityConflict as error:
                if error.code != "index_corrupt":
                    raise
                current = []
            if current != authoritative:
                self._write(authoritative)
            return list(authoritative)
