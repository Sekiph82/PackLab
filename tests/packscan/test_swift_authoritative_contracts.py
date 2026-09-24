"""Cross-check Swift wire constants against the live PackScan schemas."""

from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_swift_photo_wire_constants_follow_authoritative_schema(repo_root: Path) -> None:
    schema = json.loads((repo_root / "schemas/packscan/photo-metadata.schema.json").read_text(encoding="utf-8"))
    swift = _read(repo_root / "apps/ios-capture/PackLabCapture/Services/CameraFoundation.swift")
    assert re.search(r'case available, unavailable, notRecorded = "not_recorded", estimated', swift)
    assert 'public init(photos: [PackScanPhotoMetadataWire]) { self.schemaVersion = "1.0.0"' in swift
    statuses = schema["$defs"]["source_status"]["enum"]
    for status in statuses:
        assert status in swift
    assert 'case iso' in swift or '"iso"' in swift
    assert 'metadata.iso.status == .available || metadata.iso.status == .estimated' in swift


def test_swift_pose_constants_are_derived_from_live_pose_schema(repo_root: Path) -> None:
    schema = json.loads((repo_root / "schemas/packscan/pose.schema.json").read_text(encoding="utf-8"))
    properties = schema["properties"]
    swift = _read(repo_root / "apps/ios-capture/PackLabCapture/Services/TrackingFoundation.swift")
    for key in ("coordinate_convention", "basis_conversion", "translation_unit"):
        value = properties[key]["const"]
        assert value in swift
    assert "arkit_to_packscan_identity_shared_right_handed_basis_v1" in swift


def test_encoded_photo_wire_json_matches_authoritative_schema_and_rejects_forbidden_values(repo_root: Path) -> None:
    schema = json.loads((repo_root / "schemas/packscan/photo-metadata.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    def measurement(status: str, value: float | int | None, unit: str | None, source: str | None) -> dict:
        result = {"status": status}
        if value is not None:
            result["value"] = value
        if unit is not None:
            result["unit"] = unit
        if source is not None:
            result["source"] = source
        return result

    def encoded(status: str, value: float | int | None, unit: str | None, source: str | None) -> dict:
        return {
            "schema_version": "1.0.0",
            "photos": [{
                "photo_id": "p0",
                "image_path": "images/p0.heic",
                "sequence": 0,
                "original_filename": "p0.heic",
                "pixel_dimensions": {"width": 2, "height": 3},
                "orientation": {"value": "landscape", "source": "unknown"},
                "focal_length_mm": measurement(status, value, unit, source),
                "exposure": measurement(status, value, "s", source),
                "iso": measurement(status, int(value) if value is not None else None, "iso" if value is not None else None, source),
                "white_balance_kelvin": measurement(status, (1000 if value is not None else None), "K", source),
            }],
        }

    for status, value, unit, source in (
        ("available", 35, "mm", "exif"),
        ("estimated", 35, "mm", "derived"),
        ("unavailable", None, None, None),
        ("not_recorded", None, None, None),
    ):
        document = encoded(status, value, unit, source)
        errors = list(validator.iter_errors(document))
        assert not errors, [error.message for error in errors]

    forbidden = encoded("unavailable", 35, "mm", "exif")
    assert list(validator.iter_errors(forbidden))
    wrong_unit = encoded("available", 35, "mm", "exif")
    wrong_unit["photos"][0]["focal_length_mm"]["unit"] = "s"
    assert list(validator.iter_errors(wrong_unit))
    out_of_range = encoded("available", 0, "mm", "exif")
    assert list(validator.iter_errors(out_of_range))

    strict_photo = schema["$defs"]["photo"]["required"]
    app_only = encoded("unavailable", None, None, None)["photos"][0]
    app_only["lens_identity"] = "main"
    assert "lens_identity" not in strict_photo
    assert list(validator.iter_errors({"schema_version": "1.0.0", "photos": [app_only]}))


def test_camera_controls_and_recovery_share_the_production_runtime_composition(repo_root: Path) -> None:
    content = _read(repo_root / "apps/ios-capture/PackLabCapture/ContentView.swift")
    camera = _read(repo_root / "apps/ios-capture/PackLabCapture/Services/CameraFoundation.swift")
    assert "let controls = AVFoundationCameraControlComposition(device: device, selectedLens: lens)" in content
    assert "bindCameraControls(controls.controls)" in content
    assert "captureAndPersistAcceptedPhoto" in content
    assert "NextLevelPreviewBridge(recoveryOwner: runtime.cameraRecoveryOwner)" in content
    assert "recoveryOwner: cameraRecoveryOwner" in content
    assert "recoveryOwner.addStateObserver" in camera
