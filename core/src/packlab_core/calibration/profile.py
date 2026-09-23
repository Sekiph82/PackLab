"""Versioned calibration-profile storage and deterministic reuse checks."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

PROFILE_SCHEMA_VERSION = "1.0.0"
PROFILE_COMPATIBILITY_VERSION = "calibration_profile_compatibility_v1"
_PROFILE_ID_RE = re.compile(r"^[A-Za-z0-9._/-]{1,128}$")


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
    errors.extend(_schema_contract_errors(profile))
    if not _PROFILE_ID_RE.fullmatch(profile.profile_id):
        errors.append("profile_id_invalid")
    if profile.schema_version != PROFILE_SCHEMA_VERSION:
        errors.append("profile_schema_version_changed")
    if profile.resolution_policy not in {"exact_reference_only", "uniform_scale_about_origin"}:
        errors.append("unknown_resolution_policy")
    errors.extend(_key_structural_errors(profile.key))
    if profile.provenance.get("source") != "owner_physical_session":
        errors.append("provenance_source_not_owner_physical_session")
    if profile.provenance.get("native_capture_evidence") != "owner_device":
        errors.append("native_capture_evidence_unavailable")
    if profile.provenance.get("physical_measurement_evidence") != "owner_completed":
        errors.append("physical_measurement_evidence_unavailable")
    if profile.quality.confidence_status not in {"accepted", "warning"}:
        errors.append("profile_quality_not_reusable")
    if not 0 <= profile.quality.confidence_score <= 1:
        errors.append("confidence_score_out_of_range")
    if profile.quality.reprojection_rmse_px < 0:
        errors.append("reprojection_rmse_px_invalid")
    if profile.quality.accepted_view_count < 1:
        errors.append("accepted_view_count_invalid")
    if not _valid_utc_timestamp(profile.created_at_utc) or not _valid_utc_timestamp(
        profile.quality.verified_at_utc
    ):
        errors.append("timestamps_not_rfc3339_utc")
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


def _schema_contract_errors(profile: CalibrationProfile) -> tuple[str, ...]:
    try:
        errors = sorted(
            _profile_schema_validator().iter_errors(_profile_document(profile)),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
    except (OSError, ValueError, SchemaError):
        return ("profile_schema_resource_unavailable",)
    reasons: list[str] = []
    for error in errors:
        path = ".".join(str(part) for part in error.absolute_path) or "root"
        reasons.append(f"profile_schema_contract_invalid:{path}")
    return tuple(reasons)


@cache
def _profile_schema_validator() -> Draft202012Validator:
    schema_path = (
        Path(__file__).resolve().parents[4]
        / "schemas"
        / "packscan"
        / "calibration-profile.schema.json"
    )
    import json

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _profile_document(profile: CalibrationProfile) -> dict[str, object]:
    return {
        "schema_version": profile.schema_version,
        "profile_id": profile.profile_id,
        "profile_key": asdict(profile.key),
        "resolution_policy": profile.resolution_policy,
        "created_at": profile.created_at_utc,
        "verified_at": profile.quality.verified_at_utc,
        "units": dict(profile.units),
        "provenance": dict(profile.provenance),
        "quality": {
            "confidence_status": profile.quality.confidence_status,
            "confidence_score": profile.quality.confidence_score,
            "reprojection_rmse_px": profile.quality.reprojection_rmse_px,
            "accepted_view_count": profile.quality.accepted_view_count,
        },
    }


def _key_structural_errors(key: CalibrationProfileKey) -> tuple[str, ...]:
    errors: list[str] = []
    required_strings = (
        "device_model",
        "lens_identity",
        "camera_position",
        "orientation",
        "focus_mode",
        "capture_app_version",
        "calibration_model_version",
        "calibration_policy_version",
    )
    for field_name in required_strings:
        value = getattr(key, field_name)
        if not isinstance(value, str) or not value:
            errors.append(f"profile_key_{field_name}_empty")
    if key.camera_position not in {"back", "front"}:
        errors.append("profile_key_camera_position_invalid")
    if key.orientation not in {"portrait", "landscape_left", "landscape_right"}:
        errors.append("profile_key_orientation_invalid")
    if key.focus_mode not in {"locked", "continuous_with_recorded_distance"}:
        errors.append("profile_key_focus_mode_invalid")
    if key.image_width_px < 1 or key.image_height_px < 1:
        errors.append("resolution_dimensions_invalid")
    if not math.isfinite(key.zoom_factor) or key.zoom_factor <= 0:
        errors.append("zoom_factor_invalid")
    return tuple(errors)


def _valid_utc_timestamp(value: str) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo == UTC


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
