"""Versioned calibration-profile storage and deterministic reuse checks."""

from __future__ import annotations

import math
from dataclasses import dataclass

PROFILE_SCHEMA_VERSION = "1.0.0"
PROFILE_COMPATIBILITY_VERSION = "calibration_profile_compatibility_v1"


@dataclass(frozen=True)
class CalibrationProfileKey:
    """Dimensions that bind a calibration profile to a capture configuration."""

    device_model: str
    lens_identity: str
    camera_position: str
    image_width_px: int
    image_height_px: int
    orientation: str
    zoom_factor: float
    focus_mode: str
    capture_app_version: str
    calibration_model_version: str
    calibration_policy_version: str


@dataclass(frozen=True)
class CalibrationQualityEvidence:
    """Quality evidence stored with the profile; units are explicit in field names."""

    confidence_status: str
    confidence_score: float
    reprojection_rmse_px: float
    accepted_view_count: int
    verified_at_utc: str


@dataclass(frozen=True)
class CalibrationProfile:
    """Stored profile metadata; does not include private source images."""

    profile_id: str
    schema_version: str
    key: CalibrationProfileKey
    resolution_policy: str
    created_at_utc: str
    provenance: dict[str, str]
    quality: CalibrationQualityEvidence
    units: dict[str, str]


@dataclass(frozen=True)
class CaptureProfileRequest:
    """Capture-side key used to decide whether a stored profile may be reused."""

    key: CalibrationProfileKey


@dataclass(frozen=True)
class ProfileCompatibilityResult:
    status: str
    reusable: bool
    compatibility_reasons: tuple[str, ...]
    invalidation_reasons: tuple[str, ...]
    compatibility_version: str = PROFILE_COMPATIBILITY_VERSION


def check_profile_compatibility(
    profile: CalibrationProfile, request: CaptureProfileRequest
) -> ProfileCompatibilityResult:
    """Return a deterministic decision; unknown or incompatible state is never reusable."""

    structural_errors = _profile_structural_errors(profile)
    if structural_errors:
        return ProfileCompatibilityResult("invalid", False, (), structural_errors)

    invalidation_reasons = list(_key_invalidation_reasons(profile.key, request.key))
    compatibility_reasons: list[str] = []
    if _same_resolution(profile.key, request.key):
        compatibility_reasons.append("exact_resolution_match")
    elif profile.resolution_policy == "uniform_scale_about_origin" and _same_aspect_ratio(
        profile.key, request.key
    ):
        compatibility_reasons.append("compatible_uniform_resolution_scale")
    else:
        invalidation_reasons.append("resolution_changed")

    if invalidation_reasons:
        return ProfileCompatibilityResult("invalid", False, (), tuple(invalidation_reasons))
    compatibility_reasons.append("all_required_profile_key_dimensions_match")
    return ProfileCompatibilityResult("compatible", True, tuple(compatibility_reasons), ())


def _profile_structural_errors(profile: CalibrationProfile) -> tuple[str, ...]:
    errors: list[str] = []
    if profile.schema_version != PROFILE_SCHEMA_VERSION:
        errors.append("profile_schema_version_changed")
    if profile.resolution_policy not in {"exact_reference_only", "uniform_scale_about_origin"}:
        errors.append("unknown_resolution_policy")
    if profile.quality.confidence_status not in {"accepted", "warning"}:
        errors.append("profile_quality_not_reusable")
    if not 0 <= profile.quality.confidence_score <= 1:
        errors.append("confidence_score_out_of_range")
    if profile.quality.reprojection_rmse_px < 0:
        errors.append("reprojection_rmse_px_invalid")
    if profile.quality.accepted_view_count < 1:
        errors.append("accepted_view_count_invalid")
    if not profile.created_at_utc.endswith("Z") or not profile.quality.verified_at_utc.endswith(
        "Z"
    ):
        errors.append("timestamps_not_utc_z")
    required_units = {
        "image_width": "px",
        "image_height": "px",
        "zoom_factor": "unitless",
        "reprojection_rmse": "px",
    }
    for key, expected in required_units.items():
        if profile.units.get(key) != expected:
            errors.append(f"unit_{key}_not_{expected}")
    return tuple(errors)


def _key_invalidation_reasons(
    stored: CalibrationProfileKey, requested: CalibrationProfileKey
) -> tuple[str, ...]:
    checks = (
        ("device_model_changed", stored.device_model, requested.device_model),
        ("lens_identity_changed", stored.lens_identity, requested.lens_identity),
        ("camera_position_changed", stored.camera_position, requested.camera_position),
        ("orientation_changed", stored.orientation, requested.orientation),
        ("zoom_factor_changed", stored.zoom_factor, requested.zoom_factor),
        ("focus_mode_changed", stored.focus_mode, requested.focus_mode),
        ("capture_app_version_changed", stored.capture_app_version, requested.capture_app_version),
        (
            "calibration_model_version_changed",
            stored.calibration_model_version,
            requested.calibration_model_version,
        ),
        (
            "calibration_policy_version_changed",
            stored.calibration_policy_version,
            requested.calibration_policy_version,
        ),
    )
    reasons: list[str] = []
    for reason, stored_value, requested_value in checks:
        if stored_value != requested_value:
            reasons.append(reason)
    return tuple(reasons)


def _same_resolution(stored: CalibrationProfileKey, requested: CalibrationProfileKey) -> bool:
    return (
        stored.image_width_px == requested.image_width_px
        and stored.image_height_px == requested.image_height_px
    )


def _same_aspect_ratio(stored: CalibrationProfileKey, requested: CalibrationProfileKey) -> bool:
    if (
        min(
            stored.image_width_px,
            stored.image_height_px,
            requested.image_width_px,
            requested.image_height_px,
        )
        <= 0
    ):
        return False
    return math.isclose(
        stored.image_width_px / stored.image_height_px,
        requested.image_width_px / requested.image_height_px,
        rel_tol=0.0,
        abs_tol=1e-12,
    )
