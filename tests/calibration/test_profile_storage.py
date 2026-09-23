"""Tests for calibration profile storage and invalidation."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from packlab_core.calibration import (
    CalibrationProfile,
    CalibrationProfileKey,
    CalibrationQualityEvidence,
    CaptureProfileRequest,
    check_profile_compatibility,
)


def _key(**overrides: object) -> CalibrationProfileKey:
    values: dict[str, object] = {
        "device_model": "iPhone 16 Standard",
        "lens_identity": "main_wide_camera_1x",
        "camera_position": "back",
        "image_width_px": 4032,
        "image_height_px": 3024,
        "orientation": "landscape_right",
        "zoom_factor": 1.0,
        "focus_mode": "locked",
        "capture_app_version": "0.1.0",
        "calibration_model_version": "iphone16-standard-main-v1",
        "calibration_policy_version": "iphone_main_camera_calibration_policy_v1",
    }
    values.update(overrides)
    return CalibrationProfileKey(**values)  # type: ignore[arg-type]


def _profile(**overrides: object) -> CalibrationProfile:
    values: dict[str, object] = {
        "profile_id": "iphone16-standard-main-v1",
        "schema_version": "1.0.0",
        "key": _key(),
        "resolution_policy": "exact_reference_only",
        "created_at_utc": "2026-09-22T00:00:00Z",
        "provenance": {
            "source": "owner_physical_session",
            "native_capture_evidence": "owner_device",
            "physical_measurement_evidence": "owner_completed",
        },
        "quality": CalibrationQualityEvidence("accepted", 0.92, 0.4, 9, "2026-09-22T01:00:00Z"),
        "units": {
            "image_width": "px",
            "image_height": "px",
            "zoom_factor": "unitless",
            "reprojection_rmse": "px",
        },
    }
    values.update(overrides)
    return CalibrationProfile(**values)  # type: ignore[arg-type]


def _check(profile: CalibrationProfile, key: CalibrationProfileKey):
    return check_profile_compatibility(profile, CaptureProfileRequest(key))


def _assert_invalid(profile: CalibrationProfile, reason: str) -> None:
    result = _check(profile, _key())
    assert result.status == "invalid"
    assert result.reusable is False
    assert reason in result.invalidation_reasons
    assert result.compatibility_reasons == ()


def test_exact_profile_key_match_is_compatible() -> None:
    result = _check(_profile(), _key())
    assert result.status == "compatible"
    assert result.reusable is True
    assert result.invalidation_reasons == ()
    assert "exact_resolution_match" in result.compatibility_reasons


def test_uniform_resolution_scale_is_compatible_only_when_explicitly_allowed() -> None:
    request_key = _key(image_width_px=2016, image_height_px=1512)
    exact_only = _check(_profile(), request_key)
    assert exact_only.status == "invalid"
    assert exact_only.invalidation_reasons == ("resolution_changed",)

    scalable = _profile(resolution_policy="uniform_scale_about_origin")
    result = _check(scalable, request_key)
    assert result.status == "compatible"
    assert result.reusable is True
    assert "compatible_uniform_resolution_scale" in result.compatibility_reasons


def test_every_key_dimension_invalidates_reuse() -> None:
    cases = {
        "device_model_changed": {"device_model": "iPhone 17 Standard"},
        "lens_identity_changed": {"lens_identity": "ultra_wide_0_5x"},
        "camera_position_changed": {"camera_position": "front"},
        "orientation_changed": {"orientation": "portrait"},
        "zoom_factor_changed": {"zoom_factor": 2.0},
        "focus_mode_changed": {"focus_mode": "continuous_with_recorded_distance"},
        "capture_app_version_changed": {"capture_app_version": "0.2.0"},
        "calibration_model_version_changed": {"calibration_model_version": "iphone16-main-v2"},
        "calibration_policy_version_changed": {"calibration_policy_version": "policy_v2"},
    }
    for reason, override in cases.items():
        result = _check(_profile(), _key(**override))
        assert result.status == "invalid"
        assert reason in result.invalidation_reasons
        assert result.reusable is False


def test_incompatible_aspect_ratio_invalidates_even_with_scaling_policy() -> None:
    result = _check(
        _profile(resolution_policy="uniform_scale_about_origin"),
        _key(image_width_px=2048, image_height_px=1537),
    )
    assert result.status == "invalid"
    assert result.invalidation_reasons == ("resolution_changed",)


def test_unknown_or_malformed_profile_is_not_reused() -> None:
    bad_schema = _profile(schema_version="2.0.0")
    assert "profile_schema_version_changed" in _check(bad_schema, _key()).invalidation_reasons

    bad_units = _profile(units={"image_width": "px"})
    result = _check(bad_units, _key())
    assert result.status == "invalid"
    assert "unit_image_height_not_px" in result.invalidation_reasons

    rejected = _profile(
        quality=dataclasses.replace(_profile().quality, confidence_status="rejected")
    )
    assert "profile_quality_not_reusable" in _check(rejected, _key()).invalidation_reasons


def test_unavailable_or_placeholder_provenance_fails_closed() -> None:
    unavailable = _profile(
        provenance={
            "source": "unavailable_placeholder",
            "native_capture_evidence": "unavailable",
            "physical_measurement_evidence": "unavailable",
        }
    )
    result = _check(unavailable, _key())
    assert result.status == "invalid"
    assert result.reusable is False
    assert "provenance_source_not_owner_physical_session" in result.invalidation_reasons
    assert "native_capture_evidence_unavailable" in result.invalidation_reasons
    assert "physical_measurement_evidence_unavailable" in result.invalidation_reasons
    assert result.compatibility_reasons == ()


def test_malformed_timestamps_fail_rfc3339_validation() -> None:
    _assert_invalid(_profile(created_at_utc="garbageZ"), "timestamps_not_rfc3339_utc")
    bad_verified = _profile(
        quality=dataclasses.replace(_profile().quality, verified_at_utc="2026-99-99T00:00:00Z")
    )
    _assert_invalid(bad_verified, "timestamps_not_rfc3339_utc")


def test_invalid_dimensions_and_empty_key_fields_fail_before_compatibility() -> None:
    _assert_invalid(_profile(key=_key(image_width_px=0)), "resolution_dimensions_invalid")
    _assert_invalid(_profile(key=_key(image_height_px=-1)), "resolution_dimensions_invalid")
    _assert_invalid(_profile(key=_key(device_model="")), "profile_key_device_model_empty")
    _assert_invalid(_profile(key=_key(lens_identity="")), "profile_key_lens_identity_empty")


def test_quality_ranges_fail_before_compatibility() -> None:
    _assert_invalid(
        _profile(quality=dataclasses.replace(_profile().quality, confidence_score=1.1)),
        "confidence_score_out_of_range",
    )
    _assert_invalid(
        _profile(quality=dataclasses.replace(_profile().quality, reprojection_rmse_px=-0.1)),
        "reprojection_rmse_px_invalid",
    )
    _assert_invalid(
        _profile(quality=dataclasses.replace(_profile().quality, accepted_view_count=0)),
        "accepted_view_count_invalid",
    )


def test_unknown_resolution_policy_and_schema_version_fail_closed() -> None:
    _assert_invalid(_profile(resolution_policy="scale_somehow"), "unknown_resolution_policy")
    _assert_invalid(_profile(schema_version="2.0.0"), "profile_schema_version_changed")


def test_calibration_profile_schema_freezes_required_storage_contract(repo_root: Path) -> None:
    path = repo_root / "schemas" / "packscan" / "calibration-profile.schema.json"
    with path.open(encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
    properties = schema["properties"]
    key_required = properties["profile_key"]["required"]
    assert "device_model" in key_required
    assert "lens_identity" in key_required
    assert "image_width_px" in key_required
    assert "image_height_px" in key_required
    assert "calibration_model_version" in key_required
    assert properties["resolution_policy"]["enum"] == [
        "exact_reference_only",
        "uniform_scale_about_origin",
    ]
    assert properties["units"]["properties"]["reprojection_rmse"] == {"const": "px"}
