"""Portable, deterministic report generation for validated PackScan ingest."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from packlab_core.packscan import PackScanReport


@dataclass(frozen=True, slots=True)
class ImportReport:
    capture_id: str
    schema_version: str
    source_channel: str
    package_sha256: str
    image_count: int
    image_bytes: int
    photo_metadata_count: int
    capture_mode: str
    device_summary: dict[str, str]
    calibration_profile_reference: str | None
    calibration_status: str
    optional_payload_counts: dict[str, int]
    warnings: list[dict[str, str]]
    raw_location: str | None
    transfer_provenance: dict[str, str] | None

    def to_dict(self) -> dict[str, object]:
        return {
            "capture_id": self.capture_id, "schema_version": self.schema_version, "source_channel": self.source_channel,
            "package_sha256": self.package_sha256, "image_count": self.image_count, "image_bytes": self.image_bytes,
            "photo_metadata_count": self.photo_metadata_count, "capture_mode": self.capture_mode,
            "device_summary": self.device_summary, "calibration_profile_reference": self.calibration_profile_reference,
            "calibration_status": self.calibration_status, "optional_payload_counts": self.optional_payload_counts,
            "warnings": self.warnings, "raw_location": self.raw_location, "transfer_provenance": self.transfer_provenance,
        }


def build_import_report(report: PackScanReport, *, package_sha256: str, source_channel: str, raw_location: str | None = None, transfer_provenance: dict[str, str] | None = None) -> ImportReport:
    manifest = report.manifest
    payloads = list(manifest.get("payloads", []))
    images = [item for item in payloads if item.get("kind") == "image"]
    metadata_bytes = report.payloads.get("metadata/photos.json", b"{}")
    try:
        photo_document = json.loads(metadata_bytes.decode("utf-8"))
        photo_count = len(photo_document.get("photos", [])) if isinstance(photo_document, dict) and isinstance(photo_document.get("photos"), list) else 0
    except (UnicodeDecodeError, json.JSONDecodeError):
        photo_count = 0
    calibration_ref = manifest.get("calibration_profile_ref") if isinstance(manifest.get("calibration_profile_ref"), str) else None
    warnings: list[dict[str, str]] = []
    if calibration_ref is None:
        warnings.append({"code": "calibration_owner_required", "severity": "owner_required", "message": "calibration reference is not present"})
    optional_counts: dict[str, int] = {}
    for item in payloads:
        if isinstance(item, dict) and item.get("required") is False:
            kind = str(item.get("kind", "other"))
            optional_counts[kind] = optional_counts.get(kind, 0) + 1
    for kind in ("mask", "diagnostics", "calibration"):
        if kind not in optional_counts:
            warnings.append({"code": f"optional_{kind}_missing", "severity": "optional", "message": f"optional {kind} payload is absent"})
    return ImportReport(
        capture_id=str(manifest["capture_id"]), schema_version=str(manifest["schema_version"]), source_channel=source_channel,
        package_sha256=package_sha256, image_count=len(images), image_bytes=sum(int(item.get("size_bytes", 0)) for item in images),
        photo_metadata_count=photo_count, capture_mode=str(manifest.get("capture_mode", {}).get("mode", "unknown")),
        device_summary={key: str(manifest.get("device", {}).get(key, "")) for key in ("platform", "model", "os_version")},
        calibration_profile_reference=calibration_ref, calibration_status="available" if calibration_ref else "owner_required",
        optional_payload_counts=dict(sorted(optional_counts.items())), warnings=warnings, raw_location=raw_location,
        transfer_provenance=transfer_provenance,
    )


class ImportReportStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, report: ImportReport) -> str:
        filename = f"{report.package_sha256}.json"
        target = self.root / filename
        fd, temporary_name = tempfile.mkstemp(prefix=f".{filename}-", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(report.to_dict(), handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            Path(temporary_name).unlink(missing_ok=True)
        return f"reports/{filename}"
