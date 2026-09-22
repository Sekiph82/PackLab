"""Contract tests for the iPhone 16 Standard main-camera calibration procedure."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest


def _load_schema(repo_root: Path) -> dict[str, object]:
    path = repo_root / "schemas" / "packscan" / "iphone-main-camera-calibration.schema.json"
    with path.open(encoding="utf-8") as schema_file:
        return json.load(schema_file)


def _required_object(schema: dict[str, object], *path: str) -> dict[str, object]:
    value: object = schema
    for part in path:
        assert isinstance(value, dict)
        value = value[part]
    assert isinstance(value, dict)
    return value


def _assert_schema_contract(schema: dict[str, object]) -> None:
    properties = _required_object(schema, "properties")
    baseline = _required_object(properties, "baseline", "properties")
    assert baseline["device_model"] == {"const": "iPhone 16 Standard"}
    assert baseline["lens_identity"] == {"const": "main_wide_camera_1x"}
    assert baseline["lidar_required"] == {"const": False}
    assert baseline["pro_only_feature_required"] == {"const": False}

    binding = _required_object(properties, "profile_binding")
    assert binding["required"] == [
        "device_model",
        "lens_identity",
        "image_width_px",
        "image_height_px",
        "orientation",
        "zoom_factor",
        "focus_mode",
        "capture_app_version",
        "calibration_profile_version",
    ]
    binding_properties = _required_object(binding, "properties")
    assert binding_properties["zoom_factor"] == {"const": 1.0}
    assert binding_properties["calibration_profile_version"] == {
        "type": "string",
        "pattern": "^iphone16-standard-main-v[0-9]+$",
    }

    source_policy = _required_object(properties, "source_policy", "properties")
    assert source_policy["policy_version"] == {"const": "iphone_main_camera_calibration_policy_v1"}
    assert source_policy["intrinsics_source"] == {
        "enum": ["device_api", "dedicated_calibration", "unavailable"]
    }

    capture_run = _required_object(properties, "capture_run", "properties")
    view_set = _required_object(capture_run, "view_set")
    assert view_set["minItems"] == 7
    assert "corner_coverage" in view_set["items"]["enum"]

    validation = _required_object(properties, "validation_outputs")
    assert validation["required"] == [
        "reprojection_rmse_px",
        "accepted_view_count",
        "confidence_status",
    ]

    all_of = schema["allOf"]
    assert isinstance(all_of, list)
    measured_branch = all_of[1]["then"]
    assert measured_branch["required"] == [
        "capture_run",
        "validation_outputs",
        "intrinsics_reference",
        "owner_physical_evidence",
    ]


def test_iphone_main_camera_schema_freezes_baseline_binding_and_evidence(repo_root: Path) -> None:
    _assert_schema_contract(_load_schema(repo_root))


def test_schema_contract_rejects_resolution_binding_drift(repo_root: Path) -> None:
    schema = _load_schema(repo_root)
    binding = _required_object(schema, "properties", "profile_binding")
    mutated = deepcopy(schema)
    mutated_binding = _required_object(mutated, "properties", "profile_binding")
    mutated_required = mutated_binding["required"]
    assert isinstance(mutated_required, list)
    mutated_required.remove("image_height_px")
    with pytest.raises(AssertionError):
        _assert_schema_contract(mutated)
    assert "image_height_px" in binding["required"]


def test_procedure_doc_freezes_exif_policy_and_no_fabricated_profile(repo_root: Path) -> None:
    text = (repo_root / "docs" / "calibration" / "iphone-main-camera-calibration.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(text.split())
    required_fragments = [
        "iPhone 16 Standard back main wide camera at `1.0x`",
        "does not assume LiDAR, Pro-only lenses",
        "No owner-produced iPhone calibration profile is included",
        "Recorded EXIF and device API intrinsics may be used as capture metadata",
        "A dedicated calibration is required",
        "`candidate` and `measured` records require owner-device capture evidence",
        "`unavailable` records must not contain capture-run or validation-output data",
    ]
    for fragment in required_fragments:
        assert fragment in normalized
