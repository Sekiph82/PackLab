"""Backend-neutral feature-extraction configuration for PackLab reconstruction.

The configuration in this module is PackLab-owned provenance.  COLMAP option
names appear only in :func:`to_colmap_feature_extraction_parameters`, which is
the adapter boundary for the pinned COLMAP 3.12.6 engine.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

COLMAP_ENGINE_VERSION = "3.12.6"
PACKAGED_CONSUMER_GOODS_PRESET_ID = "packaged-consumer-goods-v1"
PACKAGED_CONSUMER_GOODS_PRESET_VERSION = "1"


class FeatureExtractionConfigError(ValueError):
    """Raised when a feature-extraction configuration is unsafe or invalid."""


class UnsupportedFeatureExtractionOption(FeatureExtractionConfigError):
    """Raised when a backend option is outside the PackLab contract."""


class OrientationPolicy(StrEnum):
    """How local feature orientation is assigned to packaged-goods views."""

    ROTATION_INVARIANT = "rotation-invariant"
    UPRIGHT = "upright"


_OVERRIDE_FIELDS = frozenset(
    {
        "image_size_limit",
        "feature_count_limit",
        "first_octave",
        "octave_count",
        "octave_resolution",
        "contrast_peak_threshold",
        "peak_threshold",
        "contrast_threshold",
        "edge_threshold",
        "orientation_policy",
    }
)
_UNSUPPORTED_BACKEND_OPTIONS = frozenset(
    {
        "use_gpu",
        "gpu_index",
        "num_threads",
        "estimate_affine_shape",
        "max_num_orientations",
        "domain_size_pooling",
        "dsp_min_scale",
        "dsp_num_scales",
        "dsp_num_octaves",
        "mask_path",
    }
)
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_WINDOWS_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")


def _contains_absolute_path(value: object) -> bool:
    if isinstance(value, Path):
        return value.is_absolute()
    if isinstance(value, str):
        return value.startswith(("/", "\\")) or bool(_WINDOWS_ABSOLUTE.match(value))
    if isinstance(value, Mapping):
        return any(
            _contains_absolute_path(key) or _contains_absolute_path(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return any(_contains_absolute_path(item) for item in value)
    return False


def _require_finite_number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FeatureExtractionConfigError(f"{field_name} must be a finite number")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise FeatureExtractionConfigError(f"{field_name} must be finite")
    return numeric


def _require_integer(value: object, field_name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise FeatureExtractionConfigError(
            f"{field_name} must be an integer from {minimum} to {maximum}"
        )
    return value


def _orientation(value: object) -> OrientationPolicy:
    if isinstance(value, OrientationPolicy):
        return value
    if isinstance(value, str):
        try:
            return OrientationPolicy(value)
        except ValueError as exc:
            raise FeatureExtractionConfigError(
                f"orientation_policy must be one of {[item.value for item in OrientationPolicy]}"
            ) from exc
    raise FeatureExtractionConfigError("orientation_policy must be a supported string")


@dataclass(frozen=True, slots=True)
class FeatureExtractionConfig:
    """Immutable PackLab feature-extraction settings and preset provenance.

    The defaults are a first packaged-consumer-goods preset.  They are not a
    physical benchmark result or a universal optimum.  All public override
    keys are backend-neutral; COLMAP names are produced only by the adapter
    function below.
    """

    preset_id: str = PACKAGED_CONSUMER_GOODS_PRESET_ID
    preset_version: str = PACKAGED_CONSUMER_GOODS_PRESET_VERSION
    image_size_limit: int = 4096
    feature_count_limit: int = 12_000
    first_octave: int = -1
    octave_count: int = 4
    octave_resolution: int = 3
    contrast_peak_threshold: float = 0.004
    edge_threshold: float = 10.0
    orientation_policy: OrientationPolicy = OrientationPolicy.ROTATION_INVARIANT
    tradeoff_notes: tuple[str, ...] = (
        "Retains a larger image window for small label and closure details.",
        "Raises the feature budget and lowers the peak threshold for low-texture or glossy packaging.",
        "Uses rotation-invariant orientation for guided-orbit views of rotating package faces.",
    )
    limitations: tuple[str, ...] = (
        "First explicit PackLab preset; not physically benchmarked or universally optimal.",
        "COLMAP execution, installation, and image processing are outside this configuration boundary.",
    )

    def __post_init__(self) -> None:
        if not isinstance(self.preset_id, str) or not _IDENTIFIER.fullmatch(self.preset_id):
            raise FeatureExtractionConfigError("preset_id must be a safe lowercase identifier")
        if not isinstance(self.preset_version, str) or not _IDENTIFIER.fullmatch(self.preset_version):
            raise FeatureExtractionConfigError("preset_version must be a safe lowercase identifier")
        _require_integer(self.image_size_limit, "image_size_limit", 256, 16_384)
        _require_integer(self.feature_count_limit, "feature_count_limit", 128, 100_000)
        _require_integer(self.first_octave, "first_octave", -2, 0)
        _require_integer(self.octave_count, "octave_count", 1, 8)
        _require_integer(self.octave_resolution, "octave_resolution", 1, 8)
        contrast = _require_finite_number(self.contrast_peak_threshold, "contrast_peak_threshold")
        if not 0.0001 <= contrast <= 1.0:
            raise FeatureExtractionConfigError(
                "contrast_peak_threshold must be from 0.0001 to 1.0"
            )
        edge = _require_finite_number(self.edge_threshold, "edge_threshold")
        if not 1.0 <= edge <= 100.0:
            raise FeatureExtractionConfigError("edge_threshold must be from 1.0 to 100.0")
        object.__setattr__(self, "orientation_policy", _orientation(self.orientation_policy))
        object.__setattr__(self, "tradeoff_notes", tuple(self.tradeoff_notes))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        if any(not isinstance(item, str) or not item.strip() for item in self.tradeoff_notes):
            raise FeatureExtractionConfigError("tradeoff_notes must contain non-empty strings")
        if any(not isinstance(item, str) or not item.strip() for item in self.limitations):
            raise FeatureExtractionConfigError("limitations must contain non-empty strings")
        if _contains_absolute_path(self.to_dict()):
            raise FeatureExtractionConfigError("feature-extraction configuration cannot contain absolute paths")

    @property
    def max_image_size(self) -> int:
        """Compatibility view of the backend-neutral image-size limit."""

        return self.image_size_limit

    @property
    def max_num_features(self) -> int:
        """Compatibility view of the backend-neutral feature-count limit."""

        return self.feature_count_limit

    @property
    def num_octaves(self) -> int:
        """Compatibility view of the backend-neutral octave count."""

        return self.octave_count

    @property
    def peak_threshold(self) -> float:
        """Compatibility view of the contrast/peak threshold."""

        return self.contrast_peak_threshold

    @property
    def contrast_threshold(self) -> float:
        """Compatibility view using the generic contrast terminology."""

        return self.contrast_peak_threshold

    @property
    def preset_identity(self) -> str:
        return f"{self.preset_id}:{self.preset_version}"

    @classmethod
    def from_overrides(
        cls, overrides: Mapping[str, object] | None = None
    ) -> FeatureExtractionConfig:
        """Build the first preset with validated, non-mutating overrides."""

        return PACKAGED_CONSUMER_GOODS_PRESET.with_overrides(overrides)

    def with_overrides(
        self, overrides: Mapping[str, object] | None = None
    ) -> FeatureExtractionConfig:
        if overrides is None:
            return self
        if not isinstance(overrides, Mapping):
            raise FeatureExtractionConfigError("overrides must be a mapping")
        values: dict[str, object] = {}
        normalized_inputs: dict[str, list[tuple[str, object]]] = {}
        for key, value in overrides.items():
            if not isinstance(key, str):
                raise FeatureExtractionConfigError("override keys must be strings")
            if key not in _OVERRIDE_FIELDS:
                if key in _UNSUPPORTED_BACKEND_OPTIONS or "." in key or "path" in key.lower():
                    raise UnsupportedFeatureExtractionOption(
                        f"backend option is not supported by the PackLab contract: {key}"
                    )
                raise FeatureExtractionConfigError(f"unknown feature-extraction option: {key}")
            if _contains_absolute_path(value):
                raise FeatureExtractionConfigError(f"absolute paths are not allowed: {key}")
            canonical_key = {
                "peak_threshold": "contrast_peak_threshold",
                "contrast_threshold": "contrast_peak_threshold",
            }.get(key, key)
            normalized_inputs.setdefault(canonical_key, []).append((key, value))
        for canonical_key, entries in normalized_inputs.items():
            _, first_value = entries[0]
            if any(value != first_value for _, value in entries[1:]):
                conflicting_keys = ", ".join(key for key, _ in entries)
                raise FeatureExtractionConfigError(
                    f"conflicting override values for {canonical_key}: {conflicting_keys}"
                )
            values[canonical_key] = first_value
        return replace(self, **cast(dict[str, Any], values))

    def to_dict_without_notes(self) -> dict[str, object]:
        return {
            "contract": "packlab.feature-extraction.v1",
            "preset_id": self.preset_id,
            "preset_version": self.preset_version,
            "image_size_limit": self.image_size_limit,
            "feature_count_limit": self.feature_count_limit,
            "first_octave": self.first_octave,
            "octave_count": self.octave_count,
            "octave_resolution": self.octave_resolution,
            "contrast_peak_threshold": self.contrast_peak_threshold,
            "edge_threshold": self.edge_threshold,
            "orientation_policy": self.orientation_policy.value,
        }

    def to_dict(self) -> dict[str, object]:
        value = self.to_dict_without_notes()
        value["tradeoff_notes"] = list(self.tradeoff_notes)
        value["limitations"] = list(self.limitations)
        return value

    as_dict = to_dict

    def serialize(self) -> str:
        """Return canonical JSON suitable for durable provenance."""

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def configuration_digest(self) -> str:
        """Return the SHA-256 digest of canonical serialized configuration."""

        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()

    @property
    def digest(self) -> str:
        return self.configuration_digest()

    def to_colmap_parameters(self, *, engine_version: str = COLMAP_ENGINE_VERSION) -> dict[str, int | float | bool]:
        return to_colmap_feature_extraction_parameters(self, engine_version=engine_version)


PACKAGED_CONSUMER_GOODS_PRESET = FeatureExtractionConfig()
FeatureExtractionPreset = FeatureExtractionConfig
DEFAULT_FEATURE_EXTRACTION_PRESET = PACKAGED_CONSUMER_GOODS_PRESET
DEFAULT_FEATURE_EXTRACTION_CONFIG = PACKAGED_CONSUMER_GOODS_PRESET
CONSUMER_GOODS_PRESET = PACKAGED_CONSUMER_GOODS_PRESET


def to_colmap_feature_extraction_parameters(
    config: FeatureExtractionConfig,
    *,
    engine_version: str = COLMAP_ENGINE_VERSION,
) -> dict[str, int | float | bool]:
    """Map PackLab fields to the selected COLMAP adapter parameter names.

    This function only creates an argument/configuration mapping.  It never
    discovers, installs, launches, or otherwise invokes COLMAP.
    """

    if not isinstance(config, FeatureExtractionConfig):
        raise FeatureExtractionConfigError("config must be a FeatureExtractionConfig")
    if engine_version != COLMAP_ENGINE_VERSION:
        raise UnsupportedFeatureExtractionOption(
            f"only COLMAP {COLMAP_ENGINE_VERSION} is supported, not {engine_version}"
        )
    return {
        "SiftExtraction.max_image_size": config.image_size_limit,
        "SiftExtraction.max_num_features": config.feature_count_limit,
        "SiftExtraction.first_octave": config.first_octave,
        "SiftExtraction.num_octaves": config.octave_count,
        "SiftExtraction.octave_resolution": config.octave_resolution,
        "SiftExtraction.peak_threshold": config.contrast_peak_threshold,
        "SiftExtraction.edge_threshold": config.edge_threshold,
        "SiftExtraction.upright": config.orientation_policy is OrientationPolicy.UPRIGHT,
    }


map_to_colmap = to_colmap_feature_extraction_parameters


def unsupported_colmap_options() -> tuple[str, ...]:
    """Return explicitly unsupported COLMAP options in stable order."""

    return tuple(sorted(_UNSUPPORTED_BACKEND_OPTIONS))


__all__ = [
    "COLMAP_ENGINE_VERSION",
    "CONSUMER_GOODS_PRESET",
    "DEFAULT_FEATURE_EXTRACTION_CONFIG",
    "DEFAULT_FEATURE_EXTRACTION_PRESET",
    "FeatureExtractionConfig",
    "FeatureExtractionConfigError",
    "FeatureExtractionPreset",
    "OrientationPolicy",
    "PACKAGED_CONSUMER_GOODS_PRESET",
    "PACKAGED_CONSUMER_GOODS_PRESET_ID",
    "PACKAGED_CONSUMER_GOODS_PRESET_VERSION",
    "UnsupportedFeatureExtractionOption",
    "map_to_colmap",
    "to_colmap_feature_extraction_parameters",
    "unsupported_colmap_options",
]
