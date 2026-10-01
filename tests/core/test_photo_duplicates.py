from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QColor, QImage

from packlab_core.packscan import PackScanReport
from packlab_core.photo_duplicates import (
    PerceptualSamples,
    PhotoDuplicateError,
    build_photo_duplicate_report,
)
from packlab_core.pre_reconstruction_qa import GrayImageSamples, ImageDecodeFailure
from packlab_studio.photo_duplicates import build_packscan_photo_duplicate_report


def _metadata(paths: list[str]) -> bytes:
    return json.dumps(
        {
            "schema_version": "1.0.0",
            "photos": [
                {
                    "photo_id": f"photo-{index}",
                    "image_path": path,
                    "sequence": index,
                    "pixel_dimensions": {"width": 9, "height": 8},
                }
                for index, path in enumerate(paths)
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _report(images: dict[str, bytes], *, metadata_bytes: bytes | None = None) -> PackScanReport:
    metadata = metadata_bytes or _metadata(list(images))
    image_declarations = []
    checksums = {"metadata/photos.json": hashlib.sha256(metadata).hexdigest()}
    payloads = {"metadata/photos.json": metadata}
    for path, data in images.items():
        digest = hashlib.sha256(data).hexdigest()
        checksums[path] = digest
        payloads[path] = data
        image_declarations.append(
            {
                "path": path,
                "kind": "image",
                "sha256": digest,
                "size_bytes": len(data),
                "required": True,
                "authority": "source",
            }
        )
    image_declarations.append(
        {
            "path": "metadata/photos.json",
            "kind": "photo_metadata",
            "sha256": checksums["metadata/photos.json"],
            "size_bytes": len(metadata),
            "required": True,
            "authority": "source",
        }
    )
    manifest = {
        "capture_id": "synthetic-duplicate-fixture",
        "payloads": image_declarations,
    }
    return PackScanReport(Path("synthetic.packscan"), manifest, checksums, payloads)


def _samples(*, changed_rows: int = 0, reverse: bool = False) -> GrayImageSamples:
    rows = []
    for y in range(8):
        row = [value * 28 for value in range(9)]
        if y < changed_rows:
            row[0], row[1] = row[1], row[0]
        if reverse:
            row.reverse()
        rows.extend(row)
    return GrayImageSamples(9, 8, bytes(rows), "synthetic-gray", "1", 9, 8)


def _decoded(data_by_path: dict[str, bytes], samples: dict[str, GrayImageSamples]):
    return {
        path: PerceptualSamples(samples[path], hashlib.sha256(data).hexdigest())
        for path, data in data_by_path.items()
        if path in samples
    }


def test_exact_duplicate_groups_survive_missing_decoder_and_order_by_metadata_sequence() -> None:
    images = {"images/b.jpg": b"same bytes", "images/a.jpg": b"same bytes"}
    report = _report(images)
    result = build_photo_duplicate_report(report, {}).as_dict()
    assert result["source_images"] == [
        {
            "image_path": "images/b.jpg",
            "sha256": hashlib.sha256(b"same bytes").hexdigest(),
            "size_bytes": 10,
        },
        {
            "image_path": "images/a.jpg",
            "sha256": hashlib.sha256(b"same bytes").hexdigest(),
            "size_bytes": 10,
        },
    ]
    assert result["perceptual"]["image_ordering"]["status"] == "verified"
    assert result["exact_duplicate_groups"] == [
        {
            "source_sha256": hashlib.sha256(b"same bytes").hexdigest(),
            "image_paths": ["images/a.jpg", "images/b.jpg"],
        }
    ]
    assert result["perceptual_unavailable_images"][0]["reason_code"] == "decoded_samples_missing"
    assert "automatic_photo_deletion" in result["claim_limit"]


def test_near_duplicate_hamming_threshold_is_inclusive_and_explainable() -> None:
    images = {"images/base.jpg": b"base", "images/near.jpg": b"near", "images/far.jpg": b"far"}
    decoded = _decoded(
        images,
        {
            "images/base.jpg": _samples(),
            "images/near.jpg": _samples(changed_rows=4),
            "images/far.jpg": _samples(reverse=True),
        },
    )
    report = _report(images)
    inclusive = build_photo_duplicate_report(report, decoded, max_hamming_distance=4).as_dict()
    assert len(inclusive["near_duplicate_pairs"]) == 1
    pair = inclusive["near_duplicate_pairs"][0]
    assert {pair["image_path_a"], pair["image_path_b"]} == {
        "images/base.jpg",
        "images/near.jpg",
    }
    assert pair["hamming_distance"] == 4
    assert pair["max_hamming_distance_inclusive"] == 4
    below = build_photo_duplicate_report(report, decoded, max_hamming_distance=3).as_dict()
    assert below["near_duplicate_pairs"] == []


def test_low_contrast_and_unsupported_images_are_unavailable_but_exact_identity_remains() -> None:
    images = {"images/flat.jpg": b"flat", "images/other.jpg": b"other"}
    decoded = {
        "images/flat.jpg": PerceptualSamples(
            GrayImageSamples(9, 8, bytes([80] * 72), "test", "1", 9, 8),
            hashlib.sha256(b"flat").hexdigest(),
        ),
        "images/other.jpg": ImageDecodeFailure("unsupported_image_format"),
    }
    result = build_photo_duplicate_report(_report(images), decoded).as_dict()
    reasons = {
        item["image_path"]: item["reason_code"] for item in result["perceptual_unavailable_images"]
    }
    assert reasons == {
        "images/flat.jpg": "low_contrast_image",
        "images/other.jpg": "unsupported_image_format",
    }
    assert result["near_duplicate_pairs"] == []


def test_missing_metadata_order_uses_stable_path_fallback() -> None:
    images = {"images/z.jpg": b"z", "images/a.jpg": b"a"}
    metadata = b"not json"
    report = _report(images, metadata_bytes=metadata)
    # Keep test checksums consistent so only metadata parsing/order is unavailable.
    result = build_photo_duplicate_report(report, {}).as_dict()
    assert [item["image_path"] for item in result["source_images"]] == [
        "images/a.jpg",
        "images/z.jpg",
    ]
    assert result["perceptual"]["image_ordering"]["status"] == "metadata_order_unavailable"
    reordered = build_photo_duplicate_report(
        _report(dict(reversed(list(images.items()))), metadata_bytes=metadata), {}
    )
    assert reordered.canonical_json == build_photo_duplicate_report(report, {}).canonical_json


@pytest.mark.parametrize("threshold", [-1, 17, True, 1.5])
def test_invalid_thresholds_fail_closed(threshold: object) -> None:
    with pytest.raises(PhotoDuplicateError, match="max_hamming_distance"):
        build_photo_duplicate_report(
            _report({"images/a.jpg": b"a"}), {}, max_hamming_distance=threshold
        )  # type: ignore[arg-type]


def test_payload_integrity_and_sample_source_binding_are_enforced() -> None:
    images = {"images/a.jpg": b"a"}
    report = _report(images)
    original = dict(report.payloads)
    build_photo_duplicate_report(report, {})
    assert report.payloads == original
    with pytest.raises(PhotoDuplicateError, match="perceptual samples are bound"):
        build_photo_duplicate_report(
            report,
            {
                "images/a.jpg": PerceptualSamples(
                    _samples(), hashlib.sha256(b"other source").hexdigest()
                )
            },
        )
    report.payloads["images/a.jpg"] = b"changed bytes"
    with pytest.raises(PhotoDuplicateError, match="payload integrity"):
        build_photo_duplicate_report(report, {})
    assert report.payloads["images/a.jpg"] == b"changed bytes"


def test_decoded_mapping_rejects_unknown_paths_and_wrong_result_types() -> None:
    report = _report({"images/a.jpg": b"a"})
    with pytest.raises(PhotoDuplicateError, match="result contracts"):
        build_photo_duplicate_report(report, {"images/a.jpg": object()})  # type: ignore[dict-item]
    with pytest.raises(PhotoDuplicateError, match="undeclared source paths"):
        build_photo_duplicate_report(
            report,
            {"images/not-declared.jpg": ImageDecodeFailure("decode_failed")},
        )


def test_decoded_dimensions_must_match_source_metadata() -> None:
    images = {"images/a.jpg": b"a"}
    decoded = {
        "images/a.jpg": PerceptualSamples(
            GrayImageSamples(9, 8, bytes(range(72)), "test", "1", 10, 8),
            hashlib.sha256(b"a").hexdigest(),
        )
    }
    result = build_photo_duplicate_report(_report(images), decoded).as_dict()
    assert result["perceptual_unavailable_images"][0]["reason_code"] == "dimension_mismatch"


def test_image_count_bound_is_enforced_before_pair_generation() -> None:
    images = {f"images/{index:04d}.jpg": b"x" for index in range(513)}
    with pytest.raises(PhotoDuplicateError, match="limited to 512 images"):
        build_photo_duplicate_report(_report(images), {})


def test_qt_adapter_decodes_verified_image_without_changing_packscan_bytes() -> None:
    image = QImage(9, 8, QImage.Format.Format_RGB32)
    for y in range(8):
        for x in range(9):
            value = x * 28
            image.setPixelColor(x, y, QColor(value, value, value))
    buffer = QBuffer()
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    data = bytes(buffer.data())
    report = _report({"images/one.jpg": data})
    original = report.payloads["images/one.jpg"]
    result = build_packscan_photo_duplicate_report(report).as_dict()
    assert result["perceptual_signatures"][0]["algorithm"] == "difference_hash_9x8_luma_v1"
    assert "hash_hex" in result["perceptual_signatures"][0]
    assert report.payloads["images/one.jpg"] == original
