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


def test_import_report_manual_and_network_golden_matrix_with_optional_payloads(tmp_path: Path, repo_root: Path) -> None:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-derived-present.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = "golden-network"
    manifest["calibration_profile_ref"] = "profiles/test"
    manifest["payloads"].append({"path": "masks/0001.png", "kind": "mask", "required": False, "authority": "derived", "size_bytes": 16, "sha256": hashlib.sha256(b"M" * 16).hexdigest(), "media_type": "image/png"})
    payloads = {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}", "previews/0001.png": b"P" * 128, "thumbnails/0001.webp": b"T" * 64, "diagnostics/capture.json": b"D" * 96, "masks/0001.png": b"M" * 16}
    for item in manifest["payloads"]:
        data = payloads[item["path"]]
        item["size_bytes"] = len(data)
        item["sha256"] = hashlib.sha256(data).hexdigest()
    package = write_packscan(tmp_path / "golden.packscan", manifest, payloads)
    reports = tmp_path / "reports"
    service = ImportService().with_raw_store(RawEvidenceStore(tmp_path / "raw")).with_report_store(ImportReportStore(reports))
    manual_package = _package(tmp_path / "manual.packscan", repo_root)
    manual = service.import_path(manual_package, source_channel="drop")
    network = service.import_path(package, source_channel="network", transfer_provenance={"receiver_id": "receiver", "transfer_id": "transfer", "session_token": "SECRET", "absolute_path": str(tmp_path)})
    assert manual.state == "reported" and network.state == "reported"
    manual_report = json.loads((reports / f"{manual.package_sha256}.json").read_text(encoding="utf-8"))
    assert manual_report["source_channel"] == "drop"
    assert manual_report["optional_payload_counts"] == {}
    assert [warning["code"] for warning in manual_report["warnings"]] == ["calibration_owner_required", "optional_mask_missing", "optional_diagnostics_missing", "optional_calibration_missing"]
    network_report = json.loads((reports / f"{network.package_sha256}.json").read_text(encoding="utf-8"))
    assert network_report["source_channel"] == "network"
    assert network_report["calibration_status"] == "available"
    assert network_report["optional_payload_counts"] == {"diagnostics": 1, "mask": 1, "preview": 1, "thumbnail": 1}
    assert [warning["code"] for warning in network_report["warnings"]] == ["optional_calibration_missing"]
    assert network_report["transfer_provenance"] == {"receiver_id": "receiver", "transfer_id": "transfer"}
    assert "SECRET" not in json.dumps(network_report) and str(tmp_path) not in json.dumps(network_report)


def test_invalid_package_creates_no_successful_report_state(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.packscan"
    invalid.write_bytes(b"not-a-packscan")
    reports = tmp_path / "reports"
    service = ImportService().with_raw_store(RawEvidenceStore(tmp_path / "raw")).with_report_store(ImportReportStore(reports))
    result = service.import_path(invalid, source_channel="drop")
    assert result.state == "rejected"
    assert list(reports.glob("*.json")) == []
