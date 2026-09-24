"""Cross-check Swift wire constants against the live PackScan schemas."""

from __future__ import annotations

import json
import re
from pathlib import Path


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

