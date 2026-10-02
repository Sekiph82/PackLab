"""Versioned owner-executed physical accuracy benchmark record contract."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime

PHYSICAL_BENCHMARK_VERSION = "packlab_physical_accuracy_benchmark_v1"
PHYSICAL_BENCHMARK_RECORD_VERSION = "1.0.0"
REQUIRED_BENCHMARK_CATEGORIES = ("matte_bottle", "glossy_bottle", "jerrycan")
SAMPLE_DISPOSITIONS = ("ACCEPTED", "REJECTED", "INVALID", "MISSING_MEASUREMENT")
RECORD_STATUSES = ("OWNER_REQUIRED", "READY_FOR_AUDIT")
_SAFE_REFERENCE = re.compile(r"^(?:sha256:[0-9a-f]{64}|ref:[A-Za-z0-9_-]{1,64})$")
_SAMPLE_ID = re.compile(r"^SAMPLE-[A-Z0-9_-]{1,64}$")
_RECORD_ID = re.compile(r"^(?:UNRECORDED-OWNER-ASSIGNED|BENCH-[A-Z0-9_-]{1,64})$")


class PhysicalBenchmarkError(ValueError):
    """Raised when a physical benchmark record is unsafe or incomplete."""


@dataclass(frozen=True, slots=True)
class BenchmarkEnvironment:
    temperature_c: float | None = None
    relative_humidity_percent: float | None = None
    lighting_description: str | None = None
    background_surface: str | None = None
    camera_to_object_setup: str | None = None
    device_model: str | None = None
    lens_reference: str | None = None

    def __post_init__(self) -> None:
        if self.temperature_c is not None and not _finite(self.temperature_c):
            raise PhysicalBenchmarkError("benchmark_temperature_invalid")
        if self.relative_humidity_percent is not None and (
            not _finite(self.relative_humidity_percent)
            or not 0.0 <= self.relative_humidity_percent <= 100.0
        ):
            raise PhysicalBenchmarkError("benchmark_relative_humidity_invalid")
        for name in (
            "lighting_description",
            "background_surface",
            "camera_to_object_setup",
            "device_model",
            "lens_reference",
        ):
            value = getattr(self, name)
            if value is not None and not _safe_description(value):
                raise PhysicalBenchmarkError(f"benchmark_environment_{name}_invalid")

    @property
    def complete(self) -> bool:
        return all(
            getattr(self, name) is not None
            for name in (
                "temperature_c",
                "relative_humidity_percent",
                "lighting_description",
                "background_surface",
                "camera_to_object_setup",
                "device_model",
                "lens_reference",
            )
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "temperature_c": self.temperature_c,
            "relative_humidity_percent": self.relative_humidity_percent,
            "lighting_description": self.lighting_description,
            "background_surface": self.background_surface,
            "camera_to_object_setup": self.camera_to_object_setup,
            "device_model": self.device_model,
            "lens_reference": self.lens_reference,
        }


@dataclass(frozen=True, slots=True)
class CaliperGroundTruth:
    ground_truth_id: str
    dimension_id: str
    value_mm: float | None
    repeated_readings_mm: tuple[float, ...]
    uncertainty_mm: float | None
    caliper_reference: str | None
    calibration_record_reference: str | None
    owner_reference: str | None
    measured_at_utc: str | None
    unit: str = "mm"

    def __post_init__(self) -> None:
        for name in ("ground_truth_id", "dimension_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not _safe_token(value):
                raise PhysicalBenchmarkError(f"benchmark_ground_truth_{name}_invalid")
        if self.unit != "mm":
            raise PhysicalBenchmarkError("benchmark_ground_truth_unit_must_be_mm")
        if not isinstance(self.repeated_readings_mm, tuple) or any(
            not _positive_finite(value) for value in self.repeated_readings_mm
        ):
            raise PhysicalBenchmarkError("benchmark_ground_truth_readings_invalid")
        if self.value_mm is not None and not _positive_finite(self.value_mm):
            raise PhysicalBenchmarkError("benchmark_ground_truth_value_invalid")
        if self.uncertainty_mm is not None and not _nonnegative_finite(self.uncertainty_mm):
            raise PhysicalBenchmarkError("benchmark_ground_truth_uncertainty_invalid")
        for name in ("caliper_reference", "calibration_record_reference", "owner_reference"):
            value = getattr(self, name)
            if value is not None and not _SAFE_REFERENCE.fullmatch(value):
                raise PhysicalBenchmarkError(f"benchmark_ground_truth_{name}_unsafe")
        if self.measured_at_utc is not None and not _rfc3339_utc(self.measured_at_utc):
            raise PhysicalBenchmarkError("benchmark_ground_truth_timestamp_invalid")

    @property
    def complete(self) -> bool:
        return (
            self.value_mm is not None
            and bool(self.repeated_readings_mm)
            and self.uncertainty_mm is not None
            and self.caliper_reference is not None
            and self.calibration_record_reference is not None
            and self.owner_reference is not None
            and self.measured_at_utc is not None
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "ground_truth_id": self.ground_truth_id,
            "dimension_id": self.dimension_id,
            "instrument_type": "caliper",
            "value_mm": self.value_mm,
            "repeated_readings_mm": list(self.repeated_readings_mm),
            "uncertainty_mm": self.uncertainty_mm,
            "caliper_reference": self.caliper_reference,
            "calibration_record_reference": self.calibration_record_reference,
            "owner_reference": self.owner_reference,
            "measured_at_utc": self.measured_at_utc,
            "unit": self.unit,
        }


@dataclass(frozen=True, slots=True)
class PhysicalBenchmarkSample:
    sample_id: str
    category: str
    disposition: str
    scan_id: str | None
    scan_revision_id: str | None
    measurement_id: str | None
    measurement_revision_id: str | None
    evidence_reference: str | None
    ground_truth: CaliperGroundTruth | None
    disposition_reason: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.sample_id, str) or not _SAMPLE_ID.fullmatch(self.sample_id):
            raise PhysicalBenchmarkError("benchmark_sample_id_invalid_or_unstable")
        if self.category not in REQUIRED_BENCHMARK_CATEGORIES:
            raise PhysicalBenchmarkError("benchmark_sample_category_unsupported")
        if self.disposition not in SAMPLE_DISPOSITIONS:
            raise PhysicalBenchmarkError("benchmark_sample_disposition_invalid")
        for name in ("scan_id", "scan_revision_id", "measurement_id", "measurement_revision_id"):
            value = getattr(self, name)
            if value is not None and not _safe_token(value):
                raise PhysicalBenchmarkError(f"benchmark_sample_{name}_invalid")
        if self.evidence_reference is not None and not _SAFE_REFERENCE.fullmatch(
            self.evidence_reference
        ):
            raise PhysicalBenchmarkError("benchmark_sample_evidence_reference_unsafe")
        if self.disposition in {"REJECTED", "INVALID", "MISSING_MEASUREMENT"}:
            if not isinstance(self.disposition_reason, str) or not self.disposition_reason.strip():
                raise PhysicalBenchmarkError("benchmark_sample_disposition_reason_required")
        elif self.disposition_reason is not None:
            raise PhysicalBenchmarkError("benchmark_accepted_sample_cannot_have_rejection_reason")
        if self.disposition == "ACCEPTED" and (
            self.scan_id is None
            or self.scan_revision_id is None
            or self.measurement_id is None
            or self.measurement_revision_id is None
            or self.evidence_reference is None
            or self.ground_truth is None
            or not self.ground_truth.complete
        ):
            raise PhysicalBenchmarkError("benchmark_accepted_sample_ground_truth_or_links_missing")
        if self.disposition == "MISSING_MEASUREMENT" and (
            self.measurement_id is not None or self.measurement_revision_id is not None
        ):
            raise PhysicalBenchmarkError("benchmark_missing_measurement_must_not_link_estimate")

    def as_dict(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "category": self.category,
            "disposition": self.disposition,
            "scan_id": self.scan_id,
            "scan_revision_id": self.scan_revision_id,
            "measurement_id": self.measurement_id,
            "measurement_revision_id": self.measurement_revision_id,
            "evidence_reference": self.evidence_reference,
            "ground_truth": None if self.ground_truth is None else self.ground_truth.as_dict(),
            "disposition_reason": self.disposition_reason,
        }


@dataclass(frozen=True, slots=True)
class PhysicalAccuracyBenchmarkRecord:
    record_id: str
    record_status: str
    operator_reference: str | None
    created_at_utc: str | None
    environment: BenchmarkEnvironment
    samples: tuple[PhysicalBenchmarkSample, ...]
    protocol_version: str = PHYSICAL_BENCHMARK_VERSION
    record_version: str = PHYSICAL_BENCHMARK_RECORD_VERSION
    privacy_boundary: str = "raw_images_and_unnecessary_device_identity_private"

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or not _RECORD_ID.fullmatch(self.record_id):
            raise PhysicalBenchmarkError("benchmark_record_id_invalid")
        if self.record_status not in RECORD_STATUSES:
            raise PhysicalBenchmarkError("benchmark_record_status_invalid")
        if self.protocol_version != PHYSICAL_BENCHMARK_VERSION:
            raise PhysicalBenchmarkError("benchmark_protocol_version_unsupported")
        if self.record_version != PHYSICAL_BENCHMARK_RECORD_VERSION:
            raise PhysicalBenchmarkError("benchmark_record_version_unsupported")
        if not isinstance(self.environment, BenchmarkEnvironment):
            raise PhysicalBenchmarkError("benchmark_environment_required")
        if not isinstance(self.samples, tuple) or not self.samples:
            raise PhysicalBenchmarkError("benchmark_samples_must_be_nonempty_tuple")
        sample_ids = tuple(sample.sample_id for sample in self.samples)
        if len(set(sample_ids)) != len(sample_ids):
            raise PhysicalBenchmarkError("benchmark_duplicate_sample_id")
        if self.operator_reference is not None and not _SAFE_REFERENCE.fullmatch(
            self.operator_reference
        ):
            raise PhysicalBenchmarkError("benchmark_operator_reference_unsafe")
        if self.created_at_utc is not None and not _rfc3339_utc(self.created_at_utc):
            raise PhysicalBenchmarkError("benchmark_record_timestamp_invalid")
        if self.record_status == "READY_FOR_AUDIT":
            categories = {sample.category for sample in self.samples}
            if not set(REQUIRED_BENCHMARK_CATEGORIES).issubset(categories):
                raise PhysicalBenchmarkError("benchmark_required_categories_missing")
            if any(sample.disposition == "MISSING_MEASUREMENT" for sample in self.samples):
                raise PhysicalBenchmarkError("benchmark_missing_measurement_blocks_ready_status")
            if (
                not self.environment.complete
                or self.operator_reference is None
                or self.created_at_utc is None
            ):
                raise PhysicalBenchmarkError("benchmark_ready_record_metadata_incomplete")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.physical-accuracy-benchmark.v1",
            "protocol_version": self.protocol_version,
            "record_version": self.record_version,
            "record_id": self.record_id,
            "record_status": self.record_status,
            "operator_reference": self.operator_reference,
            "created_at_utc": self.created_at_utc,
            "benchmark_categories_required": list(REQUIRED_BENCHMARK_CATEGORIES),
            "environment": self.environment.as_dict(),
            "samples": [
                sample.as_dict()
                for sample in sorted(
                    self.samples,
                    key=lambda item: (
                        REQUIRED_BENCHMARK_CATEGORIES.index(item.category),
                        item.sample_id,
                    ),
                )
            ],
            "acceptance_thresholds": None,
            "threshold_status": "NOT_DEFINED_BY_PROTOCOL",
            "privacy_boundary": self.privacy_boundary,
            "raw_image_bytes_included": False,
            "ambient_identity_included": False,
            "synthetic_evidence_is_physical_evidence": False,
        }

    @property
    def record_digest(self) -> str:
        encoded = json.dumps(
            self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()


def blank_physical_benchmark_record() -> PhysicalAccuracyBenchmarkRecord:
    """Create a valid owner-required template with no measurements or thresholds."""

    samples = tuple(
        PhysicalBenchmarkSample(
            f"SAMPLE-UNRECORDED-{category.upper().replace('-', '_')}-001",
            category,
            "MISSING_MEASUREMENT",
            None,
            None,
            None,
            None,
            None,
            None,
            "Physical sample and measurement not recorded; owner action required.",
        )
        for category in REQUIRED_BENCHMARK_CATEGORIES
    )
    return PhysicalAccuracyBenchmarkRecord(
        "UNRECORDED-OWNER-ASSIGNED",
        "OWNER_REQUIRED",
        None,
        None,
        BenchmarkEnvironment(),
        samples,
    )


def serialize_physical_benchmark_record(record: PhysicalAccuracyBenchmarkRecord) -> bytes:
    payload = record.as_dict()
    payload["record_digest"] = record.record_digest
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )


def _safe_token(value: str) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and len(value) <= 128
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value) is not None
    )


def _safe_description(value: object) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= 160
        and value.strip() == value
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 .,;:()_+-]{0,159}", value) is not None
    )


def _rfc3339_utc(value: str) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0.0
    )


def _nonnegative_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0.0
    )
