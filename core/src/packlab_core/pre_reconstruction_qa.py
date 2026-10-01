"""Deterministic, non-authoritative QA evidence for validated PackScan inputs."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from .packscan.container import PackScanReport

QA_PROFILE_ID: Final = "packlab.pre-reconstruction-capture-qa.v1"
SHARPNESS_ALGORITHM: Final = "laplacian_variance_8bit_grayscale_v1"
SHARPNESS_MIN_VARIANCE: Final = 20.0
EXPOSURE_ALGORITHM: Final = "mean_luma_and_clipped_fraction_8bit_grayscale_v1"
EXPOSURE_MIN_MEAN: Final = 40.0
EXPOSURE_MAX_MEAN: Final = 215.0
EXPOSURE_CLIPPED_LIMIT: Final = 0.05
MAX_SAMPLES_PER_IMAGE: Final = 1_000_000
MAX_QA_IMAGES: Final = 512
MAX_TOTAL_QA_SAMPLES: Final = 64_000_000
MAX_IMAGE_DIMENSION: Final = 100_000


class PreReconstructionQAError(ValueError):
    """Raised for invalid caller inputs at the QA report boundary."""


@dataclass(frozen=True, slots=True)
class GrayImageSamples:
    """Bounded, row-major 8-bit luma samples decoded by a named adapter."""

    width: int
    height: int
    pixels: bytes
    decoder_id: str
    decoder_version: str
    source_width: int
    source_height: int

    def __post_init__(self) -> None:
        if not isinstance(self.width, int) or isinstance(self.width, bool) or self.width < 1:
            raise PreReconstructionQAError("sample width must be a positive integer")
        if not isinstance(self.height, int) or isinstance(self.height, bool) or self.height < 1:
            raise PreReconstructionQAError("sample height must be a positive integer")
        if self.width > MAX_IMAGE_DIMENSION or self.height > MAX_IMAGE_DIMENSION:
            raise PreReconstructionQAError("sample dimensions exceed the profile limit")
        if self.width * self.height > MAX_SAMPLES_PER_IMAGE:
            raise PreReconstructionQAError("sample count exceeds the profile limit")
        for name in ("source_width", "source_height"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise PreReconstructionQAError(f"{name} must be a positive integer")
            if value > MAX_IMAGE_DIMENSION:
                raise PreReconstructionQAError("source dimensions exceed the profile limit")
        if self.width > self.source_width or self.height > self.source_height:
            raise PreReconstructionQAError("sample dimensions cannot exceed source dimensions")
        if not isinstance(self.pixels, bytes) or len(self.pixels) != self.width * self.height:
            raise PreReconstructionQAError("luma bytes must match sample dimensions")
        for name in ("decoder_id", "decoder_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 64:
                raise PreReconstructionQAError(f"{name} must be bounded non-empty text")


@dataclass(frozen=True, slots=True)
class ImageDecodeFailure:
    """Safe normalized disposition for an image that could not be decoded."""

    reason_code: str

    def __post_init__(self) -> None:
        if self.reason_code not in {
            "unsupported_image_format",
            "decode_failed",
            "dimension_mismatch",
        }:
            raise PreReconstructionQAError("decode failure reason code is not allow-listed")


DecodedImage = GrayImageSamples | ImageDecodeFailure


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _component(status: str, evidence: Mapping[str, object]) -> dict[str, object]:
    return {"status": status, "evidence": dict(evidence)}


def _measure_pixels(samples: GrayImageSamples) -> dict[str, object]:
    pixels = samples.pixels
    count = len(pixels)
    mean = sum(pixels) / count
    under = sum(value < 16 for value in pixels)
    over = sum(value > 239 for value in pixels)
    if samples.width < 3 or samples.height < 3:
        sharpness = None
    else:
        laplacian_sum = 0
        laplacian_squared_sum = 0
        laplacian_count = 0
        width = samples.width
        for y in range(1, samples.height - 1):
            row_offset = y * width
            for x in range(1, width - 1):
                index = row_offset + x
                value = (
                    4 * pixels[index]
                    - pixels[index - 1]
                    - pixels[index + 1]
                    - pixels[index - width]
                    - pixels[index + width]
                )
                laplacian_sum += value
                laplacian_squared_sum += value * value
                laplacian_count += 1
        laplacian_mean = laplacian_sum / laplacian_count
        sharpness = laplacian_squared_sum / laplacian_count - laplacian_mean * laplacian_mean
    return {
        "sample_dimensions": {"width": samples.width, "height": samples.height},
        "sample_count": count,
        "mean_luma_8bit": mean,
        "underexposed_pixel_fraction_below_16": under / count,
        "overexposed_pixel_fraction_above_239": over / count,
        "sharpness_laplacian_variance": sharpness,
        "decoder": {"id": samples.decoder_id, "version": samples.decoder_version},
    }


def _metadata_component(
    report: PackScanReport,
) -> tuple[str, dict[str, object], list[dict[str, object]]]:
    declared_payloads = report.manifest.get("payloads")
    if not isinstance(declared_payloads, list):
        return "failed", {"reason_code": "manifest_payloads_missing_or_invalid"}, []
    images = [
        item for item in declared_payloads if isinstance(item, dict) and item.get("kind") == "image"
    ]
    image_paths = [item.get("path") for item in images]
    metadata_bytes = report.payloads.get("metadata/photos.json")
    if not isinstance(metadata_bytes, bytes):
        return "unavailable", {"reason_code": "photo_metadata_missing"}, []
    try:
        document = json.loads(metadata_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "failed", {"reason_code": "photo_metadata_malformed_json"}, []
    if not isinstance(document, dict) or document.get("schema_version") != "1.0.0":
        return "failed", {"reason_code": "photo_metadata_schema_version_invalid"}, []
    photos = document.get("photos")
    if not isinstance(photos, list):
        return "failed", {"reason_code": "photo_records_missing_or_invalid"}, []
    if not images:
        return "failed", {"reason_code": "manifest_images_missing"}, []
    reasons: list[str] = []
    source_evidence = report.manifest.get("source_evidence")
    if (
        not isinstance(source_evidence, dict)
        or source_evidence.get("immutable") is not True
        or source_evidence.get("authority") != "original_capture"
    ):
        reasons.append("source_immutability_evidence_missing")
    records = [photo for photo in photos if isinstance(photo, dict)]
    if len(records) != len(photos):
        reasons.append("photo_record_not_object")
    ids = [item.get("photo_id") for item in records]
    paths = [item.get("image_path") for item in records]
    sequences = [item.get("sequence") for item in records]
    if len(ids) != len(set(value for value in ids if isinstance(value, str))):
        reasons.append("duplicate_photo_id")
    if len(paths) != len(set(value for value in paths if isinstance(value, str))):
        reasons.append("duplicate_image_path")
    if len(sequences) != len(set(value for value in sequences if isinstance(value, int))):
        reasons.append("duplicate_sequence")
    if any(
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value) is None
        for value in ids
    ):
        reasons.append("photo_id_missing_or_invalid")
    if any(not isinstance(value, str) or value not in image_paths for value in paths):
        reasons.append("photo_image_path_missing_or_invalid")
    valid_sequences = all(
        isinstance(value, int) and not isinstance(value, bool) for value in sequences
    ) and sequences == list(range(len(records)))
    if not valid_sequences:
        reasons.append("sequence_numbers_not_contiguous_zero_based")
    ordered = sorted(
        records,
        key=lambda item: item.get("sequence", -1) if isinstance(item.get("sequence"), int) else -1,
    )
    ordered_paths = [item.get("image_path") for item in ordered]
    if not valid_sequences or ordered_paths != image_paths:
        reasons.append("photo_sequence_does_not_match_manifest_images")
    for photo, image in zip(ordered, images, strict=False):
        dims = photo.get("pixel_dimensions")
        declared_path = image.get("path")
        if not isinstance(dims, dict) or any(
            not isinstance(dims.get(key), int)
            or isinstance(dims.get(key), bool)
            or dims.get(key, 0) <= 0
            for key in ("width", "height")
        ):
            reasons.append("photo_dimensions_missing_or_invalid")
        if photo.get("image_path") != declared_path:
            reasons.append("photo_path_mismatch")
        original_filename = photo.get("original_filename")
        if (
            not isinstance(original_filename, str)
            or not original_filename
            or len(original_filename) > 255
            or any(character in original_filename for character in "/\\")
            or any(ord(character) < 0x20 for character in original_filename)
        ):
            reasons.append("original_filename_invalid")
        for field, unit in (
            ("focal_length_mm", "mm"),
            ("exposure", "s"),
            ("iso", "iso"),
            ("white_balance_kelvin", "K"),
        ):
            if _safe_measurement(photo.get(field), unit).get("status") == "invalid":
                reasons.append(f"{field}_invalid")
        orientation = photo.get("orientation")
        if (
            not isinstance(orientation, dict)
            or not isinstance(orientation.get("value"), str)
            or orientation.get("value") not in {"portrait", "landscape", "square", "unknown"}
            or not isinstance(orientation.get("source"), str)
            or orientation.get("source") not in {"exif", "device_api", "derived", "unknown"}
            or (
                "rotation_degrees" in orientation
                and (
                    isinstance(orientation.get("rotation_degrees"), bool)
                    or orientation.get("rotation_degrees") not in {0, 90, 180, 270}
                )
            )
        ):
            reasons.append("orientation_metadata_invalid")
    report_records = []
    for photo in ordered:
        path = photo.get("image_path")
        declared = next((item for item in images if item.get("path") == path), None)
        if declared is None or not isinstance(path, str):
            continue
        dimensions = photo.get("pixel_dimensions")
        dimensions_map = dimensions if isinstance(dimensions, dict) else {}
        report_records.append(
            {
                "image_path": path,
                "source_sha256": declared.get("sha256"),
                "sequence": photo.get("sequence"),
                "width": dimensions_map.get("width"),
                "height": dimensions_map.get("height"),
                "exposure": _safe_measurement(photo.get("exposure"), "s"),
                "iso": _safe_measurement(photo.get("iso"), "iso"),
            }
        )
    evidence = {
        "photo_record_count": len(photos),
        "manifest_image_count": len(images),
        "matched_image_count": sum(path in image_paths for path in ordered_paths),
        "reason_codes": sorted(set(reasons)),
    }
    return ("pass" if not reasons else "failed"), evidence, report_records


def _safe_measurement(value: object, expected_unit: str) -> dict[str, object]:
    if not isinstance(value, dict):
        return {"status": "invalid"}
    status = value.get("status")
    if not isinstance(status, str) or status not in {
        "available",
        "estimated",
        "unavailable",
        "not_recorded",
    }:
        return {"status": "invalid"}
    result: dict[str, object] = {"status": status}
    amount = value.get("value")
    if status in {"available", "estimated"}:
        lower_bound = {"mm": 0.0, "s": 0.0, "iso": 1.0, "K": 1000.0}[expected_unit]
        upper_bound = (
            1_000_000 if expected_unit == "iso" else 100_000 if expected_unit == "K" else None
        )
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            valid_number = False
        else:
            try:
                finite = math.isfinite(amount)
            except OverflowError:
                finite = False
            valid_number = (
                finite
                and (expected_unit != "iso" or isinstance(amount, int))
                and amount >= lower_bound
                and (upper_bound is None or amount <= upper_bound)
            )
        source = value.get("source")
        if (
            valid_number
            and value.get("unit") == expected_unit
            and isinstance(source, str)
            and source in {"exif", "device_api", "operator", "derived", "unknown"}
        ):
            result.update({"value": amount, "unit": expected_unit})
        else:
            result["status"] = "invalid"
    else:
        source = value.get("source")
        if (
            "value" in value
            or ("unit" in value and value.get("unit") != expected_unit)
            or (
                "source" in value
                and (
                    not isinstance(source, str)
                    or source not in {"exif", "device_api", "operator", "derived", "unknown"}
                )
            )
        ):
            result["status"] = "invalid"
    return result


def _coverage_component(
    report: PackScanReport, records: list[dict[str, object]]
) -> dict[str, object]:
    capture_mode = report.manifest.get("capture_mode")
    if not isinstance(capture_mode, dict):
        return _component("unavailable", {"reason_code": "capture_mode_missing"})
    mode = capture_mode.get("mode")
    parameters = capture_mode.get("parameters")
    parameters = parameters if isinstance(parameters, dict) else {}
    if mode == "turntable":
        expected = parameters.get("frame_count")
        frame_index = parameters.get("frame_index")
        angle = parameters.get("angle_deg")
        valid = (
            isinstance(expected, int)
            and not isinstance(expected, bool)
            and expected > 0
            and isinstance(frame_index, int)
            and not isinstance(frame_index, bool)
            and isinstance(angle, (int, float))
            and not isinstance(angle, bool)
            and math.isfinite(angle)
            and 0 <= angle < 360
        )
        if not valid:
            return _component("unavailable", {"reason_code": "turntable_frame_evidence_missing"})
        assert isinstance(expected, int) and not isinstance(expected, bool)
        assert isinstance(frame_index, int) and not isinstance(frame_index, bool)
        in_range = 0 <= frame_index < expected
        return _component(
            "pass" if expected == 1 and in_range else "warning",
            {
                "mode": "turntable",
                "observed_frame_count": 1 if in_range else 0,
                "unique_frame_count": 1 if in_range else 0,
                "expected_frame_count": expected,
                "frame_coverage_fraction": 1 / expected if in_range else 0.0,
                "observed_15_degree_sector_count": 1 if in_range else 0,
                "frame_index": frame_index,
                "angle_deg": angle,
                "frame_indices_in_range": in_range,
                "reason_code": "manifest_records_one_turntable_frame_only",
            },
        )
    if mode == "guided_orbit":
        coverage = parameters.get("coverage")
        coverage = coverage if isinstance(coverage, dict) else {}
        minimum = coverage.get("minimum_view_count")
        if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
            return _component("unavailable", {"reason_code": "guided_orbit_target_missing"})
        observed = len(records)
        return _component(
            "pass" if observed >= minimum else "warning",
            {
                "mode": "guided_orbit",
                "observed_view_count": observed,
                "minimum_view_count": minimum,
                "target_sector_deg": coverage.get("target_sector_deg"),
                "view_count_coverage_fraction": min(1.0, observed / minimum),
                "sector_angle_evidence": "not_recorded_per_photo",
            },
        )
    return _component(
        "unavailable", {"reason_code": "capture_mode_has_no_declared_coverage_target"}
    )


@dataclass(frozen=True, slots=True)
class PreReconstructionQAReport:
    """Deterministic, explainable report that never claims capture authority."""

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
        return _sha256(self.canonical_json)


def build_pre_reconstruction_qa(
    report: PackScanReport, decoded_images: Mapping[str, DecodedImage]
) -> PreReconstructionQAReport:
    """Build source-digest-bound QA evidence from a validated PackScan report."""
    if not isinstance(report, PackScanReport):
        raise PreReconstructionQAError("a validated PackScanReport is required")
    if not isinstance(decoded_images, Mapping):
        raise PreReconstructionQAError("decoded_images must be a path-keyed mapping")
    image_payloads = report.manifest.get("payloads")
    if not isinstance(image_payloads, list):
        raise PreReconstructionQAError("validated manifest payload declarations are required")
    for declaration in image_payloads:
        if not isinstance(declaration, dict) or declaration.get("kind") not in {
            "image",
            "photo_metadata",
        }:
            continue
        path = declaration.get("path")
        data = report.payloads.get(path) if isinstance(path, str) else None
        expected_digest = declaration.get("sha256")
        expected_size = declaration.get("size_bytes")
        if (
            not isinstance(data, bytes)
            or not isinstance(expected_digest, str)
            or not isinstance(expected_size, int)
            or isinstance(expected_size, bool)
            or not isinstance(path, str)
            or _sha256(data) != expected_digest
            or len(data) != expected_size
            or report.checksums.get(path) != expected_digest
        ):
            raise PreReconstructionQAError("authoritative PackScan payload integrity check failed")
    metadata_status, metadata_evidence, records = _metadata_component(report)
    payloads = report.manifest.get("payloads")
    image_declarations = (
        [item for item in payloads if isinstance(item, dict) and item.get("kind") == "image"]
        if isinstance(payloads, list)
        else []
    )
    if len(image_declarations) > MAX_QA_IMAGES:
        raise PreReconstructionQAError("image count exceeds the QA profile limit")
    total_samples = sum(
        image.width * image.height
        for image in decoded_images.values()
        if isinstance(image, GrayImageSamples)
    )
    if total_samples > MAX_TOTAL_QA_SAMPLES:
        raise PreReconstructionQAError("total decoded sample count exceeds the QA profile limit")
    dimension_mismatches: list[str] = []
    for record in records:
        path = record.get("image_path")
        if not isinstance(path, str):
            continue
        decoded = decoded_images.get(path)
        if isinstance(decoded, GrayImageSamples) and (
            decoded.source_width != record.get("width")
            or decoded.source_height != record.get("height")
        ):
            dimension_mismatches.append(path)
    if dimension_mismatches:
        metadata_status = "failed"
        codes = metadata_evidence.get("reason_codes", [])
        metadata_evidence["reason_codes"] = (
            sorted({*codes, "decoded_dimensions_do_not_match_photo_metadata"})
            if isinstance(codes, list)
            else ["decoded_dimensions_do_not_match_photo_metadata"]
        )
        metadata_evidence["dimension_mismatch_count"] = len(dimension_mismatches)
    photo_reports: list[dict[str, object]] = []
    sharpness_statuses: list[str] = []
    exposure_statuses: list[str] = []
    for record in records:
        path = record["image_path"]
        if not isinstance(path, str):
            continue
        decoded = decoded_images.get(path)
        if isinstance(decoded, GrayImageSamples):
            width, height = record["width"], record["height"]
            dimensions_match = (
                isinstance(width, int)
                and not isinstance(width, bool)
                and isinstance(height, int)
                and not isinstance(height, bool)
                and decoded.source_width == width
                and decoded.source_height == height
            )
            if not dimensions_match:
                decoded = ImageDecodeFailure("dimension_mismatch")
            else:
                measurements = _measure_pixels(decoded)
                sharpness = measurements["sharpness_laplacian_variance"]
                assert sharpness is None or isinstance(sharpness, (int, float))
                sharpness_state = (
                    "unavailable"
                    if sharpness is None
                    else "warning"
                    if sharpness < SHARPNESS_MIN_VARIANCE
                    else "pass"
                )
                mean = measurements["mean_luma_8bit"]
                assert isinstance(mean, (int, float))
                under_fraction = measurements["underexposed_pixel_fraction_below_16"]
                over_fraction = measurements["overexposed_pixel_fraction_above_239"]
                assert isinstance(under_fraction, (int, float))
                assert isinstance(over_fraction, (int, float))
                clipped = under_fraction + over_fraction
                exposure_state = (
                    "warning"
                    if mean < EXPOSURE_MIN_MEAN
                    or mean > EXPOSURE_MAX_MEAN
                    or clipped > EXPOSURE_CLIPPED_LIMIT
                    else "pass"
                )
                sharpness_statuses.append(sharpness_state)
                exposure_statuses.append(exposure_state)
                photo_reports.append(
                    {
                        **record,
                        "sharpness": {
                            "status": sharpness_state,
                            "algorithm": SHARPNESS_ALGORITHM,
                            "minimum_variance": SHARPNESS_MIN_VARIANCE,
                            "value": sharpness,
                        },
                        "pixel_exposure": {
                            "status": exposure_state,
                            "algorithm": EXPOSURE_ALGORITHM,
                            "mean_luma_acceptable_range": [
                                EXPOSURE_MIN_MEAN,
                                EXPOSURE_MAX_MEAN,
                            ],
                            "max_clipped_pixel_fraction": EXPOSURE_CLIPPED_LIMIT,
                            "value": measurements,
                        },
                        "decode_status": "decoded",
                    }
                )
                continue
        reason = (
            decoded.reason_code
            if isinstance(decoded, ImageDecodeFailure)
            else "decoded_samples_missing"
        )
        photo_reports.append(
            {
                **record,
                "sharpness": {"status": "unavailable", "reason_code": reason},
                "pixel_exposure": {"status": "unavailable", "reason_code": reason},
                "decode_status": "unavailable",
            }
        )
        sharpness_statuses.append("unavailable")
        exposure_statuses.append("unavailable")
    metadata_measurements = [item["exposure"] for item in records]
    metadata_recorded = sum(
        isinstance(value, dict) and value.get("status") in {"available", "estimated"}
        for value in metadata_measurements
    )
    components = {
        "sharpness": _component(
            "warning"
            if "warning" in sharpness_statuses
            else "unavailable"
            if not sharpness_statuses or "unavailable" in sharpness_statuses
            else "pass",
            {
                "algorithm": SHARPNESS_ALGORITHM,
                "minimum_laplacian_variance": SHARPNESS_MIN_VARIANCE,
                "assessed_image_count": sum(
                    status != "unavailable" for status in sharpness_statuses
                ),
                "unavailable_image_count": sharpness_statuses.count("unavailable"),
            },
        ),
        "pixel_exposure": _component(
            "warning"
            if "warning" in exposure_statuses
            else "unavailable"
            if not exposure_statuses or "unavailable" in exposure_statuses
            else "pass",
            {
                "algorithm": EXPOSURE_ALGORITHM,
                "mean_luma_acceptable_range": [EXPOSURE_MIN_MEAN, EXPOSURE_MAX_MEAN],
                "max_clipped_pixel_fraction": EXPOSURE_CLIPPED_LIMIT,
                "assessed_image_count": sum(
                    status != "unavailable" for status in exposure_statuses
                ),
                "unavailable_image_count": exposure_statuses.count("unavailable"),
                "metadata_exposure_recorded_count": metadata_recorded,
            },
        ),
        "coverage": _coverage_component(report, records),
        "metadata_consistency": _component(metadata_status, metadata_evidence),
    }
    statuses = [component["status"] for component in components.values()]
    overall = (
        "review_required"
        if any(status in {"failed", "warning"} for status in statuses)
        else "incomplete"
        if "unavailable" in statuses
        else "no_automated_concern"
    )
    source_manifest = report.manifest
    capture_id = source_manifest.get("capture_id")
    source_evidence = source_manifest.get("source_evidence")
    payload: dict[str, object] = {
        "schema": "packlab.pre-reconstruction-qa.v1",
        "profile_id": QA_PROFILE_ID,
        "authority": "non_authoritative_capture_qa",
        "claim_limit": "diagnostic_evidence_only_not_geometry_or_physical_accuracy",
        "capture_id": capture_id,
        "source_evidence": {
            "immutable": source_evidence.get("immutable")
            if isinstance(source_evidence, dict)
            else None,
            "photo_metadata_sha256": report.checksums.get("metadata/photos.json"),
            "image_sources": [
                {"image_path": item.get("path"), "source_sha256": item.get("sha256")}
                for item in image_declarations
            ],
        },
        "thresholds": {
            "sharpness_minimum_laplacian_variance": SHARPNESS_MIN_VARIANCE,
            "exposure_mean_luma_acceptable_range": [EXPOSURE_MIN_MEAN, EXPOSURE_MAX_MEAN],
            "exposure_max_clipped_fraction": EXPOSURE_CLIPPED_LIMIT,
        },
        "components": components,
        "photos": photo_reports,
        "overall": {
            "status": overall,
            "next_action": "human_review"
            if overall != "no_automated_concern"
            else "continue_workflow_review",
        },
    }
    return PreReconstructionQAReport(payload)
