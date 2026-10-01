from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from packlab_core.focal_lens_consistency import (
    FocalLensConsistencyError,
    build_focal_lens_consistency_report,
)
from packlab_core.packscan import PackScanReport


def _report(
    measurements: list[dict[str, object] | None], *, lens: str | None = None
) -> PackScanReport:
    image_payloads = {
        f"images/{index:03}.jpg": f"synthetic image {index}".encode()
        for index in range(len(measurements))
    }
    photos: list[dict[str, object]] = []
    for index, (path, measurement) in enumerate(zip(image_payloads, measurements, strict=True)):
        photo: dict[str, object] = {
            "photo_id": f"photo-{index}",
            "image_path": path,
            "sequence": index,
        }
        if measurement is not None:
            photo["focal_length_mm"] = measurement
        photos.append(photo)
    metadata_bytes = json.dumps(
        {"schema_version": "1.0.0", "photos": photos}, sort_keys=True, separators=(",", ":")
    ).encode()
    payloads = {**image_payloads, "metadata/photos.json": metadata_bytes}
    checksums = {path: hashlib.sha256(data).hexdigest() for path, data in payloads.items()}
    declarations: list[dict[str, object]] = [
        {
            "path": path,
            "kind": "image",
            "sha256": checksums[path],
            "size_bytes": len(data),
        }
        for path, data in image_payloads.items()
    ]
    declarations.append(
        {
            "path": "metadata/photos.json",
            "kind": "photo_metadata",
            "sha256": checksums["metadata/photos.json"],
            "size_bytes": len(metadata_bytes),
        }
    )
    device: dict[str, object] = {"platform": "iOS", "model": "synthetic", "os_version": "1.0"}
    if lens is not None:
        device["lens"] = lens
    return PackScanReport(
        Path("synthetic.packscan"),
        {"capture_id": "capture-focal-test", "device": device, "payloads": declarations},
        checksums,
        payloads,
    )


def _available(
    value: float, *, source: str = "exif", status: str = "available"
) -> dict[str, object]:
    return {"status": status, "value": value, "unit": "mm", "source": source}


def _focal(result: object) -> dict[str, Any]:
    return result.as_dict()["focal_length"]  # type: ignore[attr-defined,no-any-return]


def test_consistent_measurements_are_normalized_and_lens_is_capture_level_only() -> None:
    report = _report([_available(35), _available(35.4, status="estimated")], lens="wide camera")
    payload = build_focal_lens_consistency_report(report).as_dict()

    assert payload["focal_length"]["status"] == "consistent"  # type: ignore[index]
    assert payload["focal_length"]["unit"] == "mm"  # type: ignore[index]
    assert payload["focal_length"]["measurements"][0]["normalized_value_mm"] == 35.0  # type: ignore[index]
    assert payload["lens_identity"] == {  # type: ignore[comparison-overlap]
        "capture_level": {"status": "reported", "capture_level_value": "wide camera"},
        "per_photo_status": "not_recorded_by_packscan_schema",
    }
    assert payload["reconstruction_gate"] == "diagnostic_only_no_automatic_rejection"


def test_inclusive_tolerance_boundary_passes_and_value_just_outside_warns() -> None:
    boundary = build_focal_lens_consistency_report(
        _report([_available(35), _available(35), _available(35.7)])
    )
    outside = build_focal_lens_consistency_report(
        _report([_available(35), _available(35), _available(35.7001)])
    )

    assert _focal(boundary)["status"] == "consistent"
    assert _focal(boundary)["effective_tolerance_mm"] == pytest.approx(0.7)
    assert _focal(outside)["status"] == "inconsistent"
    assert outside.as_dict()["decision"] == "review_required"
    assert outside.as_dict()["diagnostics"][-1]["code"] == "focal_length_spread_exceeds_tolerance"  # type: ignore[index]


def test_missing_unknown_and_unavailable_values_remain_non_rejecting() -> None:
    report = _report(
        [
            None,
            {"status": "unavailable"},
            {"status": "not_recorded"},
            {"status": "available", "value": 40, "unit": "mm", "source": "operator"},
        ]
    )
    payload = build_focal_lens_consistency_report(report).as_dict()

    assert payload["focal_length"]["status"] == "insufficient_measurements"  # type: ignore[index]
    assert payload["focal_length"]["measurement_count"] == 1  # type: ignore[index]
    assert payload["focal_length"]["unknown_count"] == 3  # type: ignore[index]
    assert payload["decision"] == "informational"
    assert [item["status"] for item in payload["focal_length"]["measurements"]] == [  # type: ignore[index]
        "missing",
        "unavailable",
        "not_recorded",
        "available",
    ]


def test_all_unknown_values_do_not_create_a_focal_mismatch_warning() -> None:
    payload = build_focal_lens_consistency_report(
        _report([{"status": "unavailable"}, {"status": "not_recorded"}])
    ).as_dict()
    assert payload["focal_length"]["status"] == "unavailable"  # type: ignore[index]
    assert payload["decision"] == "informational"
    assert all(item["severity"] == "info" for item in payload["diagnostics"])  # type: ignore[index]


def test_invalid_unit_is_reported_without_using_the_reading() -> None:
    payload = build_focal_lens_consistency_report(
        _report(
            [_available(35), {"status": "available", "value": 35, "unit": "cm", "source": "exif"}]
        )
    ).as_dict()
    assert payload["focal_length"]["status"] == "insufficient_measurements"  # type: ignore[index]
    assert payload["focal_length"]["measurements"][1]["status"] == "invalid"  # type: ignore[index]
    assert payload["diagnostics"][0]["code"] == "focal_length_measurement_invalid"  # type: ignore[index]


def test_numeric_overflow_is_reported_as_invalid_measurement() -> None:
    payload = build_focal_lens_consistency_report(
        _report([_available(35), _available(10**1000)])
    ).as_dict()
    assert payload["focal_length"]["status"] == "insufficient_measurements"  # type: ignore[index]
    assert payload["focal_length"]["measurements"][1]["status"] == "invalid"  # type: ignore[index]


def test_report_is_deterministic_and_source_payloads_are_immutable() -> None:
    report = _report([_available(24), _available(24.1)])
    payloads_before = dict(report.payloads)
    first = build_focal_lens_consistency_report(report)
    second = build_focal_lens_consistency_report(report)

    assert first.canonical_json == second.canonical_json
    assert first.sha256 == second.sha256
    assert report.payloads == payloads_before


def test_metadata_and_image_tampering_fail_closed() -> None:
    metadata_tampered = _report([_available(35), _available(35)])
    metadata_tampered.payloads["metadata/photos.json"] += b" "
    with pytest.raises(FocalLensConsistencyError, match="photo metadata payload integrity"):
        build_focal_lens_consistency_report(metadata_tampered)

    image_tampered = _report([_available(35), _available(35)])
    image_tampered.payloads["images/000.jpg"] = b"different"
    with pytest.raises(FocalLensConsistencyError, match="image identity or payload integrity"):
        build_focal_lens_consistency_report(image_tampered)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"absolute_tolerance_mm": -0.1}, "absolute_tolerance_mm"),
        ({"relative_tolerance": 1.1}, "relative_tolerance"),
        ({"relative_tolerance": float("nan")}, "relative_tolerance"),
        ({"absolute_tolerance_mm": True}, "absolute_tolerance_mm"),
    ],
)
def test_tolerance_profile_rejects_invalid_values(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(FocalLensConsistencyError, match=message):
        build_focal_lens_consistency_report(_report([_available(35)]), **kwargs)  # type: ignore[arg-type]
