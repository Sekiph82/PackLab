from __future__ import annotations

import hashlib
import json
from pathlib import Path

from packlab_studio.ingest import ImportService
from packlab_studio.quarantine import QuarantineStore


def test_quarantine_preserves_invalid_bytes_and_redacted_record_idempotently(tmp_path: Path) -> None:
    source = tmp_path / ".." / "private-supplier-name.packscan"
    source = source.resolve()
    source.write_bytes(b"corrupt-package")
    store = QuarantineStore(tmp_path / "quarantine")
    service = ImportService(quarantine=store)
    first = service.import_path(source, source_channel="network")
    second = service.import_path(source, source_channel="network")
    digest = hashlib.sha256(b"corrupt-package").hexdigest()
    assert first.state == second.state == "quarantined"
    assert (tmp_path / "quarantine" / "packages" / f"{digest}.packscan").read_bytes() == b"corrupt-package"
    record = json.loads((tmp_path / "quarantine" / "records" / f"{digest}.json").read_text(encoding="utf-8"))
    assert len(record["events"]) == 2
    assert str(tmp_path) not in json.dumps(record)
    assert source.exists()


def test_future_and_unsafe_packages_are_quarantined_without_normal_artifacts(tmp_path: Path) -> None:
    future = tmp_path / "future.packscan"
    future.write_bytes(b"future bytes")
    service = ImportService(quarantine=QuarantineStore(tmp_path / "q"))
    result = service.import_path(future, source_channel="drop")
    assert result.state == "quarantined"
    assert not (tmp_path / "imported").exists()
