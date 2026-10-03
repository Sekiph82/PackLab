"""Versioned geometry-fitting presets without captured scan content or parent IDs."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import cast

from .cross_section_measurement import CrossSectionMeasurement
from .design_model import PackageFamily
from .fitting_strategy import (
    FittingStrategyError,
    FittingStrategyPolicy,
    FittingStrategyRecommendation,
    recommend_fitting_strategy,
)
from .scan_master import ScanMasterRevision, mesh_sha256
from .vertical_profile import VerticalProfile

FITTING_PRESET_CONTRACT = "packlab.design-fitting-preset.v1"
FITTING_PRESET_ID = "packaged-consumer-goods-fitting"
FITTING_PRESET_VERSION = 1
MAX_FITTING_PRESET_BYTES = 64_000
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


class FittingPresetError(ValueError):
    """Raised when a preset is malformed, unsupported or applied to a stale parent."""


def _bounded_float(value: object, minimum: float, maximum: float, field: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not minimum <= value <= maximum
    ):
        raise FittingPresetError(f"{field}_out_of_range")


@dataclass(frozen=True, slots=True)
class PackageFamilyFittingDefaults:
    """Reusable fitting controls that contain no scan-specific measurements."""

    package_family: PackageFamily
    profile_smoothing_strength: float = 0.0
    profile_window_radius: int = 2
    maximum_relative_adjustment: float = 0.25
    base_transition_fraction: float = 0.10
    shoulder_transition_fraction: float = 0.72
    section_height_fractions: tuple[float, ...] = (0.15, 0.50, 0.85)
    symmetry_constraints_enabled: bool = True
    maximum_reflection_error_ratio: float = 0.08

    def __post_init__(self) -> None:
        if not isinstance(self.package_family, PackageFamily):
            raise FittingPresetError("package_family_invalid")
        _bounded_float(self.profile_smoothing_strength, 0.0, 0.5, "profile_smoothing_strength")
        if (
            isinstance(self.profile_window_radius, bool)
            or not isinstance(self.profile_window_radius, int)
            or not 1 <= self.profile_window_radius <= 8
        ):
            raise FittingPresetError("profile_window_radius_out_of_range")
        _bounded_float(self.maximum_relative_adjustment, 0.0, 0.25, "maximum_relative_adjustment")
        _bounded_float(self.base_transition_fraction, 0.0, 1.0, "base_transition_fraction")
        _bounded_float(self.shoulder_transition_fraction, 0.0, 1.0, "shoulder_transition_fraction")
        if self.shoulder_transition_fraction <= self.base_transition_fraction:
            raise FittingPresetError("transition_fractions_must_be_ordered")
        if (
            not isinstance(self.section_height_fractions, tuple)
            or not 3 <= len(self.section_height_fractions) <= 9
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0.0 < value < 1.0
                for value in self.section_height_fractions
            )
            or any(
                right <= left
                for left, right in zip(
                    self.section_height_fractions, self.section_height_fractions[1:]
                )
            )
        ):
            raise FittingPresetError("section_height_fractions_invalid")
        if not isinstance(self.symmetry_constraints_enabled, bool):
            raise FittingPresetError("symmetry_constraints_enabled_invalid")
        _bounded_float(
            self.maximum_reflection_error_ratio, 0.0, 0.25, "maximum_reflection_error_ratio"
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "package_family": self.package_family.value,
            "profile_smoothing_strength": self.profile_smoothing_strength,
            "profile_window_radius": self.profile_window_radius,
            "maximum_relative_adjustment": self.maximum_relative_adjustment,
            "base_transition_fraction": self.base_transition_fraction,
            "shoulder_transition_fraction": self.shoulder_transition_fraction,
            "section_height_fractions": list(self.section_height_fractions),
            "symmetry_constraints_enabled": self.symmetry_constraints_enabled,
            "maximum_reflection_error_ratio": self.maximum_reflection_error_ratio,
        }


@dataclass(frozen=True, slots=True)
class DesignFittingPreset:
    """Canonical fitting configuration; it deliberately has no Scan Master fields."""

    preset_id: str = FITTING_PRESET_ID
    version: int = FITTING_PRESET_VERSION
    strategy_policy: FittingStrategyPolicy = FittingStrategyPolicy()
    package_defaults: tuple[PackageFamilyFittingDefaults, ...] = tuple(
        PackageFamilyFittingDefaults(family) for family in PackageFamily
    )
    descriptive_note: str = "Reusable fitting starting values only; not benchmarked, physically validated, or a fit-quality promise."

    def __post_init__(self) -> None:
        if not isinstance(self.preset_id, str) or not _IDENTIFIER.fullmatch(self.preset_id):
            raise FittingPresetError("preset_id_invalid")
        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise FittingPresetError("preset_version_invalid")
        if self.version != FITTING_PRESET_VERSION:
            raise FittingPresetError("unsupported_fitting_preset_version")
        if not isinstance(self.strategy_policy, FittingStrategyPolicy):
            raise FittingPresetError("strategy_policy_invalid")
        if (
            not isinstance(self.package_defaults, tuple)
            or any(
                not isinstance(item, PackageFamilyFittingDefaults) for item in self.package_defaults
            )
            or {item.package_family for item in self.package_defaults} != set(PackageFamily)
            or len(self.package_defaults) != len(PackageFamily)
        ):
            raise FittingPresetError("package_family_defaults_incomplete_or_duplicate")
        object.__setattr__(
            self,
            "package_defaults",
            tuple(sorted(self.package_defaults, key=lambda item: item.package_family.value)),
        )
        if not isinstance(self.descriptive_note, str) or not self.descriptive_note.strip():
            raise FittingPresetError("descriptive_note_invalid")

    @property
    def identity(self) -> str:
        return f"{self.preset_id}:v{self.version}"

    def defaults_for(self, package_family: PackageFamily) -> PackageFamilyFittingDefaults:
        if not isinstance(package_family, PackageFamily):
            raise FittingPresetError("package_family_invalid")
        return next(item for item in self.package_defaults if item.package_family is package_family)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": FITTING_PRESET_CONTRACT,
            "preset_id": self.preset_id,
            "version": self.version,
            "strategy_policy": self.strategy_policy.as_dict(),
            "package_defaults": [
                item.as_dict()
                for item in sorted(
                    self.package_defaults, key=lambda item: item.package_family.value
                )
            ],
            "descriptive_note": self.descriptive_note,
            "scan_master_revision_id": None,
            "scan_master_geometry_sha256": None,
            "raw_scan_embedded": False,
            "fit_quality_claimed": False,
        }

    def canonical_bytes(self) -> bytes:
        try:
            return json.dumps(
                self.as_dict(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError) as error:
            raise FittingPresetError("preset_canonicalization_failed") from error

    def serialize(self) -> str:
        return self.canonical_bytes().decode("utf-8")

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    @classmethod
    def from_json(cls, payload: str | bytes) -> DesignFittingPreset:
        if isinstance(payload, bytes):
            if len(payload) > MAX_FITTING_PRESET_BYTES:
                raise FittingPresetError("preset_payload_too_large")
            try:
                source = payload.decode("utf-8")
            except UnicodeDecodeError as error:
                raise FittingPresetError("preset_payload_not_utf8") from error
        elif isinstance(payload, str):
            source = payload
            if len(source.encode("utf-8")) > MAX_FITTING_PRESET_BYTES:
                raise FittingPresetError("preset_payload_too_large")
        else:
            raise FittingPresetError("preset_payload_type_invalid")
        try:
            value = json.loads(
                source,
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
        except FittingPresetError:
            raise
        except (json.JSONDecodeError, UnicodeEncodeError, ValueError) as error:
            raise FittingPresetError("preset_payload_invalid") from error
        if not isinstance(value, dict):
            raise FittingPresetError("preset_root_must_be_object")
        expected = {
            "contract",
            "preset_id",
            "version",
            "strategy_policy",
            "package_defaults",
            "descriptive_note",
            "scan_master_revision_id",
            "scan_master_geometry_sha256",
            "raw_scan_embedded",
            "fit_quality_claimed",
        }
        if set(value) != expected:
            raise FittingPresetError("preset_fields_unsupported_or_missing")
        if value.get("contract") != FITTING_PRESET_CONTRACT:
            raise FittingPresetError("unsupported_fitting_preset_contract")
        if (
            value.get("scan_master_revision_id") is not None
            or value.get("scan_master_geometry_sha256") is not None
        ):
            raise FittingPresetError("preset_must_not_bind_scan_master")
        if (
            value.get("raw_scan_embedded") is not False
            or value.get("fit_quality_claimed") is not False
        ):
            raise FittingPresetError("preset_authority_flags_invalid")
        return _preset_from_dict(value)


@dataclass(frozen=True, slots=True)
class FittingPresetApplication:
    """Fresh strategy evidence generated from a preset and an exact supplied Scan Master."""

    preset_identity: str
    preset_digest: str
    package_defaults: PackageFamilyFittingDefaults
    recommendation: FittingStrategyRecommendation

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.design-fitting-preset-application.v1",
            "preset_identity": self.preset_identity,
            "preset_digest": self.preset_digest,
            "package_family": self.package_defaults.package_family.value,
            "package_defaults": self.package_defaults.as_dict(),
            "fitting_strategy_recommendation": self.recommendation.as_dict(),
            "fit_quality_claimed": False,
            "raw_scan_embedded": False,
        }


def apply_fitting_preset(
    preset: DesignFittingPreset,
    scan_master: ScanMasterRevision,
    *,
    expected_scan_master_revision_id: str,
    package_family: PackageFamily,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    vertical_profiles: tuple[VerticalProfile, ...] = (),
    cross_section_measurements: tuple[CrossSectionMeasurement, ...] = (),
) -> FittingPresetApplication:
    """Recompute parent-bound strategy evidence; never reuse IDs or fit claims."""
    if not isinstance(preset, DesignFittingPreset):
        raise FittingPresetError("fitting_preset_required")
    if not isinstance(scan_master, ScanMasterRevision):
        raise FittingPresetError("scan_master_revision_required")
    if scan_master.revision_id != expected_scan_master_revision_id:
        raise FittingPresetError("selected_scan_master_parent_stale")
    defaults = preset.defaults_for(package_family)
    try:
        recommendation = recommend_fitting_strategy(
            scan_master,
            expected_scan_master_revision_id=expected_scan_master_revision_id,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
            policy=preset.strategy_policy,
            vertical_profiles=vertical_profiles,
            cross_section_measurements=cross_section_measurements,
        )
    except FittingStrategyError as error:
        raise FittingPresetError(f"fitting_preset_application_rejected:{error}") from error
    if (
        recommendation.scan_master_revision_id != scan_master.revision_id
        or recommendation.scan_master_geometry_sha256 != mesh_sha256(scan_master.mesh)
        or recommendation.parent_binding.fitted_to_scan_master_revision_id
        != scan_master.revision_id
        or recommendation.parent_binding.scan_master_geometry_sha256
        != mesh_sha256(scan_master.mesh)
    ):
        raise FittingPresetError("new_scan_master_binding_invalid")
    return FittingPresetApplication(preset.identity, preset.digest, defaults, recommendation)


def _preset_from_dict(value: dict[str, object]) -> DesignFittingPreset:
    raw_policy = value["strategy_policy"]
    if not isinstance(raw_policy, dict):
        raise FittingPresetError("strategy_policy_must_be_object")
    policy_fields = {
        "minimum_sections",
        "minimum_points_per_section",
        "minimum_axis_elongation_ratio",
        "minimum_angular_coverage",
        "maximum_axisymmetric_radial_cv",
        "maximum_bilateral_reflection_error",
        "maximum_vertices",
        "maximum_triangles",
        "section_sampling_fractions",
        "reflection_sampling_policy",
        "contract",
    }
    if (
        set(raw_policy) != policy_fields
        or raw_policy.get("contract") != "packlab.fitting-strategy-policy.v1"
    ):
        raise FittingPresetError("strategy_policy_fields_invalid")
    try:
        policy = FittingStrategyPolicy(
            minimum_sections=cast(int, raw_policy["minimum_sections"]),
            minimum_points_per_section=cast(int, raw_policy["minimum_points_per_section"]),
            minimum_axis_elongation_ratio=cast(float, raw_policy["minimum_axis_elongation_ratio"]),
            minimum_angular_coverage=cast(float, raw_policy["minimum_angular_coverage"]),
            maximum_axisymmetric_radial_cv=cast(
                float, raw_policy["maximum_axisymmetric_radial_cv"]
            ),
            maximum_bilateral_reflection_error=cast(
                float, raw_policy["maximum_bilateral_reflection_error"]
            ),
            maximum_vertices=cast(int, raw_policy["maximum_vertices"]),
            maximum_triangles=cast(int, raw_policy["maximum_triangles"]),
        )
    except (TypeError, ValueError) as error:
        raise FittingPresetError("strategy_policy_invalid") from error
    if policy.as_dict() != raw_policy:
        raise FittingPresetError("strategy_policy_canonical_fields_mismatch")
    raw_defaults = value["package_defaults"]
    if not isinstance(raw_defaults, list):
        raise FittingPresetError("package_defaults_must_be_array")
    defaults: list[PackageFamilyFittingDefaults] = []
    fields = {
        "package_family",
        "profile_smoothing_strength",
        "profile_window_radius",
        "maximum_relative_adjustment",
        "base_transition_fraction",
        "shoulder_transition_fraction",
        "section_height_fractions",
        "symmetry_constraints_enabled",
        "maximum_reflection_error_ratio",
    }
    for raw in raw_defaults:
        if not isinstance(raw, dict) or set(raw) != fields:
            raise FittingPresetError("package_family_default_fields_invalid")
        try:
            family = PackageFamily(cast(str, raw["package_family"]))
        except (TypeError, ValueError) as error:
            raise FittingPresetError("package_family_invalid") from error
        raw_fractions = raw["section_height_fractions"]
        if not isinstance(raw_fractions, list):
            raise FittingPresetError("section_height_fractions_invalid")
        defaults.append(
            PackageFamilyFittingDefaults(
                family,
                cast(float, raw["profile_smoothing_strength"]),
                cast(int, raw["profile_window_radius"]),
                cast(float, raw["maximum_relative_adjustment"]),
                cast(float, raw["base_transition_fraction"]),
                cast(float, raw["shoulder_transition_fraction"]),
                tuple(cast(float, item) for item in raw_fractions),
                cast(bool, raw["symmetry_constraints_enabled"]),
                cast(float, raw["maximum_reflection_error_ratio"]),
            )
        )
    return DesignFittingPreset(
        preset_id=cast(str, value["preset_id"]),
        version=cast(int, value["version"]),
        strategy_policy=policy,
        package_defaults=tuple(defaults),
        descriptive_note=cast(str, value["descriptive_note"]),
    )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise FittingPresetError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise FittingPresetError(f"non_finite_json_constant:{value}")


PACKAGED_CONSUMER_GOODS_FITTING_PRESET = DesignFittingPreset()


__all__ = [
    "DesignFittingPreset",
    "FITTING_PRESET_CONTRACT",
    "FITTING_PRESET_ID",
    "FITTING_PRESET_VERSION",
    "FittingPresetApplication",
    "FittingPresetError",
    "MAX_FITTING_PRESET_BYTES",
    "PACKAGED_CONSUMER_GOODS_FITTING_PRESET",
    "PackageFamilyFittingDefaults",
    "apply_fitting_preset",
]
