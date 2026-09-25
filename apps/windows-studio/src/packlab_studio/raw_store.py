"""Content-addressed immutable raw PackScan evidence store."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


class RawStoreError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RawIngestRecord:
    package_sha256: str
    capture_id: str
    source_channel: str
    ingested_at: str
    raw_filename: str


class RawEvidenceStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _package(self, digest: str) -> Path:
        return self.root / f"{digest}.packscan"

    def _metadata(self, digest: str) -> Path:
        return self.root / f"{digest}.json"

    @staticmethod
    def _atomic_write_bytes(target: Path, data: bytes) -> None:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}-", suffix=".part", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    def store(self, source: str | Path, *, capture_id: str, source_channel: str) -> RawIngestRecord:
        path = Path(source)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        package = self._package(digest)
        metadata = self._metadata(digest)
        if package.exists():
            if hashlib.sha256(package.read_bytes()).hexdigest() != digest:
                raise RawStoreError("raw_digest_mismatch")
            if metadata.exists():
                existing = json.loads(metadata.read_text(encoding="utf-8"))
                if existing.get("capture_id") != capture_id:
                    raise RawStoreError("raw_identity_conflict")
                return RawIngestRecord(**existing)
        else:
            self._atomic_write_bytes(package, data)
        record = RawIngestRecord(
            package_sha256=digest, capture_id=capture_id, source_channel=source_channel,
            ingested_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"), raw_filename=package.name,
        )
        self._atomic_write_bytes(metadata, (json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
        try:
            package.chmod(0o444)
        except OSError:
            pass
        return record

    def verify(self, digest: str) -> bool:
        package = self._package(digest)
        return package.is_file() and hashlib.sha256(package.read_bytes()).hexdigest() == digest
