from __future__ import annotations

import hashlib
import json
from pathlib import Path

from packlab_core.packscan import write_packscan
from packlab_studio.import_report import ImportReportStore
from packlab_studio.ingest import ImportService
from packlab_studio.raw_store import RawEvidenceStore


def _package(path: Path, repo_root: Path, *, calibration: bool = False) -> Path:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = "report-capture"
    if calibration:
        manifest["calibration_profile_ref"] = "profiles/test"
    manifest["payloads"][0]["size_bytes"] = 3
    manifest["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})


def test_import_report_is_portable_ordered_and_redacted(tmp_path: Path, repo_root: Path) -> None:
    package = _package(tmp_path / "capture.packscan", repo_root)
    service = ImportService().with_raw_store(RawEvidenceStore(tmp_path / "raw")).with_report_store(ImportReportStore(tmp_path / "reports"))
    result = service.import_path(package, source_channel="network", transfer_provenance={"receiver_id": "receiver", "transfer_id": "transfer"})
    assert result.state == "reported"
    report = json.loads((tmp_path / "reports" / f"{result.package_sha256}.json").read_text(encoding="utf-8"))
    assert report["capture_id"] == "report-capture"
    assert report["image_count"] == 1 and report["image_bytes"] == 3
    assert report["photo_metadata_count"] == 0
    assert report["calibration_status"] == "owner_required"
    assert [warning["code"] for warning in report["warnings"]] == ["calibration_owner_required", "optional_mask_missing", "optional_diagnostics_missing", "optional_calibration_missing"]
    assert report["transfer_provenance"] == {"receiver_id": "receiver", "transfer_id": "transfer"}
    assert str(tmp_path) not in json.dumps(report)
