"""Deterministic, provenance-bound focal-length consistency diagnostics."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Final

from .packscan.container import PackScanReport

FOCAL_LENS_PROFILE_ID: Final = "packlab.focal-lens-consistency.v1"
DEFAULT_ABSOLUTE_TOLERANCE_MM: Final = 0.5
DEFAULT_RELATIVE_TOLERANCE: Final = 0.02
MAX_ABSOLUTE_TOLERANCE_MM: Final = 100.0
MAX_RELATIVE_TOLERANCE: Final = 1.0
MAX_FOCAL_PHOTOS: Final = 512
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FOCAL_SOURCES = frozenset({"exif", "device_api", "operator", "derived", "unknown"})


class FocalLensConsistencyError(ValueError):
    """Raised when source identity or analyzer inputs are ambiguous."""


@dataclass(frozen=True, slots=True)
class FocalLensConsistencyReport:
    """Canonical, read-only focal/lens diagnostics for one PackScan capture."""

    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.payload, sort_keys=True, allow_nan=False))

    @property
    def canonical_json(self) -> bytes:
        return json.dumps(
            self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json).hexdigest()


def _require_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise FocalLensConsistencyError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _finite_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        converted = float(value)
    except OverflowError:
        return None
    return converted if math.isfinite(converted) else None


def _verified_photo_inputs(
    report: PackScanReport,
) -> tuple[str, str, list[dict[str, object]], list[dict[str, object]]]:
    if not isinstance(report, PackScanReport):
        raise FocalLensConsistencyError("a validated PackScanReport is required")
    capture_id = report.manifest.get("capture_id")
    if not isinstance(capture_id, str) or not capture_id:
        raise FocalLensConsistencyError("capture identity is unavailable")
    declarations = report.manifest.get("payloads")
    if not isinstance(declarations, list):
        raise FocalLensConsistencyError("manifest payload declarations are unavailable")
    image_declarations = [
        item for item in declarations if isinstance(item, dict) and item.get("kind") == "image"
    ]
    metadata_declarations = [
        item
        for item in declarations
        if isinstance(item, dict) and item.get("path") == "metadata/photos.json"
    ]
    if not image_declarations or len(image_declarations) > MAX_FOCAL_PHOTOS:
        raise FocalLensConsistencyError("image count is outside the focal profile limit")
    if len(metadata_declarations) != 1:
        raise FocalLensConsistencyError("photo metadata declaration is missing or ambiguous")

    image_sources: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    folded_paths: set[str] = set()
    for declaration in image_declarations:
        path = declaration.get("path")
        if (
            not isinstance(path, str)
            or not path
            or path in seen_paths
            or path.casefold() in folded_paths
        ):
            raise FocalLensConsistencyError("manifest image paths are ambiguous")
        digest = _require_digest(declaration.get("sha256"), "image digest")
        size = declaration.get("size_bytes")
        data = report.payloads.get(path)
        if (
            not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or not isinstance(data, bytes)
            or len(data) != size
            or hashlib.sha256(data).hexdigest() != digest
            or report.checksums.get(path) != digest
        ):
            raise FocalLensConsistencyError(
                "manifest image identity or payload integrity check failed"
            )
        seen_paths.add(path)
        folded_paths.add(path.casefold())
        image_sources.append({"image_path": path, "source_sha256": digest})

    metadata_declaration = metadata_declarations[0]
    metadata_digest = _require_digest(metadata_declaration.get("sha256"), "photo metadata digest")
    metadata_size = metadata_declaration.get("size_bytes")
    metadata_bytes = report.payloads.get("metadata/photos.json")
    if (
        not isinstance(metadata_size, int)
        or isinstance(metadata_size, bool)
        or metadata_size < 0
        or not isinstance(metadata_bytes, bytes)
        or len(metadata_bytes) != metadata_size
        or hashlib.sha256(metadata_bytes).hexdigest() != metadata_digest
        or report.checksums.get("metadata/photos.json") != metadata_digest
    ):
        raise FocalLensConsistencyError("photo metadata payload integrity check failed")
    try:
        metadata = json.loads(metadata_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FocalLensConsistencyError("photo metadata is not valid UTF-8 JSON") from error
    if not isinstance(metadata, dict) or not isinstance(metadata.get("photos"), list):
        raise FocalLensConsistencyError("photo metadata records are unavailable")
    photos = metadata["photos"]
    if len(photos) != len(image_sources) or len(photos) > MAX_FOCAL_PHOTOS:
        raise FocalLensConsistencyError("photo metadata and manifest image counts do not match")
    source_paths = [source["image_path"] for source in image_sources]
    ordered_photos: list[dict[str, object]] = []
    seen_photo_ids: set[str] = set()
    for expected_sequence, photo in enumerate(photos):
        if not isinstance(photo, dict):
            raise FocalLensConsistencyError("photo metadata record is malformed")
        path = photo.get("image_path")
        photo_id = photo.get("photo_id")
        sequence = photo.get("sequence")
        if (
            not isinstance(path, str)
            or path != source_paths[expected_sequence]
            or not isinstance(photo_id, str)
            or not photo_id
            or photo_id in seen_photo_ids
            or not isinstance(sequence, int)
            or isinstance(sequence, bool)
            or sequence != expected_sequence
        ):
            raise FocalLensConsistencyError("photo metadata identity or sequence is ambiguous")
        seen_photo_ids.add(photo_id)
        ordered_photos.append(photo)
    return capture_id, metadata_digest, image_sources, ordered_photos


def _measurement(photo: dict[str, object]) -> tuple[dict[str, object], float | None, str | None]:
    path = photo.get("image_path")
    photo_id = photo.get("photo_id")
    sequence = photo.get("sequence")
    raw = photo.get("focal_length_mm")
    base: dict[str, object] = {
        "photo_id": photo_id,
        "image_path": path,
        "sequence": sequence,
    }
    if raw is None:
        base.update({"status": "missing", "normalized_value_mm": None, "source": None})
        return base, None, "focal_length_metadata_missing"
    if not isinstance(raw, dict):
        base.update({"status": "invalid", "normalized_value_mm": None, "source": None})
        return base, None, "focal_length_measurement_invalid"
    status = raw.get("status")
    source = raw.get("source")
    unit = raw.get("unit")
    base["source"] = source if isinstance(source, str) else None
    if isinstance(status, str) and status in {"unavailable", "not_recorded"}:
        base.update({"status": status, "normalized_value_mm": None})
        return base, None, None
    value = raw.get("value")
    normalized = _finite_number(value)
    if (
        not isinstance(status, str)
        or status not in {"available", "estimated"}
        or unit != "mm"
        or not isinstance(source, str)
        or source not in _FOCAL_SOURCES
        or normalized is None
        or normalized <= 0
    ):
        base.update({"status": "invalid", "normalized_value_mm": None})
        return base, None, "focal_length_measurement_invalid"
    base.update({"status": status, "normalized_value_mm": normalized, "unit": "mm"})
    return base, normalized, None


def _is_outlier(value: object, median: float, tolerance: float) -> bool:
    if not isinstance(value, float):
        return False
    deviation = abs(value - median)
    return deviation > tolerance and not math.isclose(
        deviation, tolerance, rel_tol=1e-12, abs_tol=1e-12
    )


def build_focal_lens_consistency_report(
    report: PackScanReport,
    *,
    absolute_tolerance_mm: float = DEFAULT_ABSOLUTE_TOLERANCE_MM,
    relative_tolerance: float = DEFAULT_RELATIVE_TOLERANCE,
) -> FocalLensConsistencyReport:
    """Analyze focal values without modifying source bytes or making geometry claims.

    Measurements are normalized to millimeters. The inclusive tolerance is the
    larger of the configured absolute floor and the configured fraction of the
    median valid focal value. Lens text is capture-level PackScan metadata only.
    """
    for tolerance_value, label, maximum in (
        (absolute_tolerance_mm, "absolute_tolerance_mm", MAX_ABSOLUTE_TOLERANCE_MM),
        (relative_tolerance, "relative_tolerance", MAX_RELATIVE_TOLERANCE),
    ):
        if (
            isinstance(tolerance_value, bool)
            or not isinstance(tolerance_value, (int, float))
            or tolerance_value > maximum
            or not math.isfinite(float(tolerance_value))
            or float(tolerance_value) < 0
        ):
            raise FocalLensConsistencyError(f"{label} must be finite and within 0..{maximum}")

    capture_id, metadata_digest, image_sources, photos = _verified_photo_inputs(report)
    measurements: list[dict[str, object]] = []
    valid_values: list[float] = []
    diagnostics: list[dict[str, object]] = []
    for photo in photos:
        measurement, focal_value, issue = _measurement(photo)
        measurements.append(measurement)
        if focal_value is not None:
            valid_values.append(focal_value)
        if issue is not None:
            diagnostics.append(
                {
                    "code": issue,
                    "severity": "info" if issue == "focal_length_metadata_missing" else "warning",
                    "photo_id": photo.get("photo_id"),
                    "image_path": photo.get("image_path"),
                }
            )

    median: float | None
    if valid_values:
        sorted_values = sorted(valid_values)
        count = len(sorted_values)
        median_value = (
            sorted_values[count // 2]
            if count % 2
            else (sorted_values[count // 2 - 1] + sorted_values[count // 2]) / 2.0
        )
        median = median_value
        tolerance = max(float(absolute_tolerance_mm), abs(median_value) * float(relative_tolerance))
        outliers = [
            item
            for item in measurements
            if _is_outlier(item.get("normalized_value_mm"), median_value, tolerance)
        ]
        if len(valid_values) < 2:
            status = "insufficient_measurements"
            diagnostics.append(
                {"code": "focal_length_insufficient_measurements", "severity": "info"}
            )
        elif outliers:
            status = "inconsistent"
            diagnostics.append(
                {
                    "code": "focal_length_spread_exceeds_tolerance",
                    "severity": "warning",
                    "median_mm": median,
                    "tolerance_mm": tolerance,
                    "outlier_photo_ids": [item["photo_id"] for item in outliers],
                }
            )
        else:
            status = "consistent"
    else:
        median = None
        tolerance = max(float(absolute_tolerance_mm), 0.0)
        outliers = []
        status = "unavailable"
        diagnostics.append({"code": "focal_length_data_unavailable", "severity": "info"})

    device = report.manifest.get("device")
    lens_value = device.get("lens") if isinstance(device, dict) else None
    lens = (
        {"status": "reported", "capture_level_value": lens_value}
        if isinstance(lens_value, str) and lens_value.strip()
        else {"status": "not_recorded", "capture_level_value": None}
    )
    payload: dict[str, object] = {
        "schema_version": "1.0.0",
        "profile_id": FOCAL_LENS_PROFILE_ID,
        "authority": "non_authoritative_capture_diagnostic",
        "claim_limit": "no_camera_pose_or_metric_claim",
        "capture_id": capture_id,
        "source_evidence": {
            "photo_metadata_path": "metadata/photos.json",
            "photo_metadata_sha256": metadata_digest,
            "image_sources": image_sources,
        },
        "focal_length": {
            "status": status,
            "unit": "mm",
            "measurement_count": len(valid_values),
            "unknown_count": len(photos) - len(valid_values),
            "median_mm": median,
            "absolute_tolerance_mm": float(absolute_tolerance_mm),
            "relative_tolerance": float(relative_tolerance),
            "effective_tolerance_mm": tolerance,
            "measurements": measurements,
        },
        "lens_identity": {
            "capture_level": lens,
            "per_photo_status": "not_recorded_by_packscan_schema",
        },
        "diagnostics": diagnostics,
        "decision": "review_required"
        if any(item["severity"] == "warning" for item in diagnostics)
        else "informational",
        "reconstruction_gate": "diagnostic_only_no_automatic_rejection",
    }
    return FocalLensConsistencyReport(payload)
