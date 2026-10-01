from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QColor, QImage

from packlab_core.packscan import PackScanReport
from packlab_core.pre_reconstruction_qa import (
    GrayImageSamples,
    ImageDecodeFailure,
    PreReconstructionQAError,
    build_pre_reconstruction_qa,
)
from packlab_studio.pre_reconstruction_qa import build_packscan_pre_reconstruction_qa


def _report(
    *,
    image_bytes: bytes = b"synthetic-image",
    metadata_bytes: bytes | None = None,
    width: int = 3,
    height: int = 3,
):
    metadata = (
        metadata_bytes
        or json.dumps(
            {
                "schema_version": "1.0.0",
                "photos": [
                    {
                        "photo_id": "photo-0",
                        "image_path": "images/000.jpg",
                        "sequence": 0,
                        "original_filename": "000.jpg",
                        "pixel_dimensions": {"width": width, "height": height},
                        "orientation": {"value": "square", "source": "derived"},
                        "focal_length_mm": {"status": "unavailable"},
                        "exposure": {
                            "status": "available",
                            "value": 0.01,
                            "unit": "s",
                            "source": "exif",
                        },
                        "iso": {
                            "status": "available",
                            "value": 100,
                            "unit": "iso",
                            "source": "exif",
                        },
                        "white_balance_kelvin": {"status": "unavailable"},
                    }
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )
    image_digest = hashlib.sha256(image_bytes).hexdigest()
    metadata_digest = hashlib.sha256(metadata).hexdigest()
    manifest = {
        "schema_version": "1.0.0",
        "capture_id": "capture-qa-test",
        "source_evidence": {"immutable": True, "authority": "original_capture"},
        "capture_mode": {
            "mode": "guided_orbit",
            "version": 1,
            "parameters": {
                "orbit_axis": "subject_vertical",
                "coverage": {"target_sector_deg": 180, "minimum_view_count": 1},
            },
        },
        "payloads": [
            {
                "path": "images/000.jpg",
                "kind": "image",
                "sha256": image_digest,
                "size_bytes": len(image_bytes),
            },
            {
                "path": "metadata/photos.json",
                "kind": "photo_metadata",
                "sha256": metadata_digest,
                "size_bytes": len(metadata),
            },
        ],
    }
    return PackScanReport(
        Path("synthetic.packscan"),
        manifest,
        {"images/000.jpg": image_digest, "metadata/photos.json": metadata_digest},
        {"images/000.jpg": image_bytes, "metadata/photos.json": metadata},
    )


def _sharp_samples() -> GrayImageSamples:
    values = bytes(215 if (x + y) % 2 else 40 for y in range(8) for x in range(8))
    return GrayImageSamples(8, 8, values, "test-decoder", "1", 8, 8)


def test_report_is_deterministic_versioned_explainable_and_source_bound() -> None:
    report = _report(width=8, height=8)
    pixels = {"images/000.jpg": _sharp_samples()}
    first = build_pre_reconstruction_qa(report, pixels)
    second = build_pre_reconstruction_qa(report, pixels)
    payload = first.as_dict()
    assert first.canonical_json == second.canonical_json
    assert first.sha256 == second.sha256
    assert payload["profile_id"] == "packlab.pre-reconstruction-capture-qa.v1"
    assert payload["authority"] == "non_authoritative_capture_qa"
    assert (
        payload["source_evidence"]["image_sources"][0]["source_sha256"]
        == report.manifest["payloads"][0]["sha256"]
    )
    assert (
        payload["source_evidence"]["photo_metadata_sha256"]
        == report.checksums["metadata/photos.json"]
    )
    assert payload["photos"][0]["sharpness"]["algorithm"] == "laplacian_variance_8bit_grayscale_v1"
    assert payload["photos"][0]["pixel_exposure"]["value"]["decoder"]["id"] == "test-decoder"
    assert payload["components"]["metadata_consistency"]["status"] == "pass"
    assert payload["components"]["coverage"]["status"] == "pass"
    assert payload["overall"]["status"] == "no_automated_concern"


def test_low_sharpness_and_exposure_boundary_values_are_explainable() -> None:
    report = _report(width=4, height=4)
    dark = GrayImageSamples(4, 4, bytes([0] * 16), "test-decoder", "1", 4, 4)
    result = build_pre_reconstruction_qa(report, {"images/000.jpg": dark}).as_dict()
    photo = result["photos"][0]
    assert photo["sharpness"]["status"] == "warning"
    assert photo["sharpness"]["value"] == 0
    assert photo["pixel_exposure"]["status"] == "warning"
    assert photo["pixel_exposure"]["value"]["mean_luma_8bit"] == 0
    assert result["overall"]["status"] == "review_required"

    threshold_pixels = bytearray([100] * 25)
    threshold_pixels[12] = 103
    threshold_samples = GrayImageSamples(5, 5, bytes(threshold_pixels), "test-decoder", "1", 5, 5)
    threshold_result = build_pre_reconstruction_qa(
        _report(width=5, height=5), {"images/000.jpg": threshold_samples}
    ).as_dict()
    assert threshold_result["photos"][0]["sharpness"]["value"] == 20
    assert threshold_result["photos"][0]["sharpness"]["status"] == "pass"
    below_threshold_pixels = bytearray([100] * 25)
    below_threshold_pixels[12] = 102
    below_result = build_pre_reconstruction_qa(
        _report(width=5, height=5),
        {
            "images/000.jpg": GrayImageSamples(
                5, 5, bytes(below_threshold_pixels), "test-decoder", "1", 5, 5
            )
        },
    ).as_dict()
    assert below_result["photos"][0]["sharpness"]["status"] == "warning"

    at_exposure_floor = GrayImageSamples(4, 4, bytes([40] * 16), "test-decoder", "1", 4, 4)
    floor_result = build_pre_reconstruction_qa(
        report, {"images/000.jpg": at_exposure_floor}
    ).as_dict()
    assert floor_result["photos"][0]["pixel_exposure"]["status"] == "pass"
    at_ceiling = GrayImageSamples(4, 4, bytes([215] * 16), "test-decoder", "1", 4, 4)
    ceiling_result = build_pre_reconstruction_qa(report, {"images/000.jpg": at_ceiling}).as_dict()
    assert ceiling_result["photos"][0]["pixel_exposure"]["status"] == "pass"

    clip_report = _report(width=5, height=4)
    clipped_at_limit = bytes([0] + [100] * 19)
    clip_result = build_pre_reconstruction_qa(
        clip_report,
        {"images/000.jpg": GrayImageSamples(5, 4, clipped_at_limit, "test-decoder", "1", 5, 4)},
    ).as_dict()
    assert clip_result["photos"][0]["pixel_exposure"]["status"] == "pass"
    split_clipped = bytes([0, 255] + [100] * 18)
    split_result = build_pre_reconstruction_qa(
        clip_report,
        {"images/000.jpg": GrayImageSamples(5, 4, split_clipped, "test-decoder", "1", 5, 4)},
    ).as_dict()
    assert split_result["photos"][0]["pixel_exposure"]["status"] == "warning"
    clipped_over_limit = bytes([0, 0] + [100] * 18)
    over_result = build_pre_reconstruction_qa(
        clip_report,
        {"images/000.jpg": GrayImageSamples(5, 4, clipped_over_limit, "test-decoder", "1", 5, 4)},
    ).as_dict()
    assert over_result["photos"][0]["pixel_exposure"]["status"] == "warning"


def test_missing_decoder_and_freehand_coverage_have_explicit_unavailable_disposition() -> None:
    report = _report()
    result = build_pre_reconstruction_qa(
        report, {"images/000.jpg": ImageDecodeFailure("unsupported_image_format")}
    ).as_dict()
    assert result["photos"][0]["sharpness"] == {
        "status": "unavailable",
        "reason_code": "unsupported_image_format",
    }
    freehand_manifest = dict(report.manifest)
    freehand_manifest["capture_mode"] = {"mode": "freehand", "version": 1}
    freehand_report = PackScanReport(
        report.source, freehand_manifest, report.checksums, report.payloads
    )
    freehand = build_pre_reconstruction_qa(freehand_report, {}).as_dict()
    assert freehand["components"]["coverage"]["status"] == "unavailable"
    assert freehand["overall"]["status"] == "incomplete"


def test_malformed_and_misaligned_photo_metadata_fail_component() -> None:
    report = _report(metadata_bytes=b"not json")
    # Fixture reconstruction updates all checksum declarations consistently so
    # metadata failure is attributed to content validation, not byte integrity.
    metadata_digest = hashlib.sha256(report.payloads["metadata/photos.json"]).hexdigest()
    for item in report.manifest["payloads"]:
        if item["path"] == "metadata/photos.json":
            item["sha256"] = metadata_digest
            item["size_bytes"] = len(report.payloads["metadata/photos.json"])
    report.checksums["metadata/photos.json"] = metadata_digest
    result = build_pre_reconstruction_qa(report, {}).as_dict()
    assert result["components"]["metadata_consistency"]["status"] == "failed"
    assert (
        result["components"]["metadata_consistency"]["evidence"]["reason_code"]
        == "photo_metadata_malformed_json"
    )

    valid = _report()
    document = json.loads(valid.payloads["metadata/photos.json"])
    document["photos"][0]["image_path"] = "images/other.jpg"
    content = json.dumps(document, separators=(",", ":")).encode()
    misaligned = _report(metadata_bytes=content)
    digest = hashlib.sha256(content).hexdigest()
    misaligned.manifest["payloads"][1]["sha256"] = digest
    misaligned.manifest["payloads"][1]["size_bytes"] = len(content)
    misaligned.checksums["metadata/photos.json"] = digest
    result = build_pre_reconstruction_qa(misaligned, {}).as_dict()
    assert result["components"]["metadata_consistency"]["status"] == "failed"
    assert (
        "photo_sequence_does_not_match_manifest_images"
        in result["components"]["metadata_consistency"]["evidence"]["reason_codes"]
    )

    invalid_measurement = _report()
    document = json.loads(invalid_measurement.payloads["metadata/photos.json"])
    document["photos"][0]["exposure"]["unit"] = "ms"
    content = json.dumps(document, separators=(",", ":")).encode()
    invalid_measurement = _report(metadata_bytes=content)
    digest = hashlib.sha256(content).hexdigest()
    invalid_measurement.manifest["payloads"][1]["sha256"] = digest
    invalid_measurement.manifest["payloads"][1]["size_bytes"] = len(content)
    invalid_measurement.checksums["metadata/photos.json"] = digest
    result = build_pre_reconstruction_qa(invalid_measurement, {}).as_dict()
    assert (
        "exposure_invalid"
        in result["components"]["metadata_consistency"]["evidence"]["reason_codes"]
    )


def test_authoritative_payload_digest_mismatch_is_rejected_without_mutation() -> None:
    report = _report()
    original = dict(report.payloads)
    build_pre_reconstruction_qa(report, {})
    assert report.payloads == original
    report.payloads["images/000.jpg"] = b"changed source bytes"
    with pytest.raises(PreReconstructionQAError, match="payload integrity"):
        build_pre_reconstruction_qa(report, {})
    assert report.payloads["images/000.jpg"] == b"changed source bytes"
    assert original["images/000.jpg"] != report.payloads["images/000.jpg"]


def test_decoded_sample_dimensions_must_match_authoritative_photo_dimensions() -> None:
    report = _report()
    sample = GrayImageSamples(3, 3, bytes([100] * 9), "test-decoder", "1", 4, 3)
    result = build_pre_reconstruction_qa(report, {"images/000.jpg": sample}).as_dict()
    assert result["photos"][0]["decode_status"] == "unavailable"
    assert result["photos"][0]["sharpness"]["reason_code"] == "dimension_mismatch"
    assert result["components"]["metadata_consistency"]["status"] == "failed"


def test_qt_adapter_decodes_source_bytes_read_only_into_bounded_samples() -> None:
    image = QImage(3, 3, QImage.Format.Format_RGB32)
    for y in range(3):
        for x in range(3):
            value = 255 if (x + y) % 2 else 0
            image.setPixelColor(x, y, QColor(value, value, value))
    buffer = QBuffer()
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    image_bytes = bytes(buffer.data())
    report = _report(image_bytes=image_bytes)
    original = report.payloads["images/000.jpg"]
    result = build_packscan_pre_reconstruction_qa(report).as_dict()
    assert result["photos"][0]["decode_status"] == "decoded"
    assert result["photos"][0]["pixel_exposure"]["value"]["decoder"]["id"].startswith(
        "qt-qimagereader-grayscale8/"
    )
    assert report.payloads["images/000.jpg"] == original
