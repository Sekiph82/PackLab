"""PackLab-owned, backend-neutral reconstruction preset configuration.

This module composes the accepted feature-extraction, matcher-selection, and
sparse-mapping configuration contracts.  It does not execute an engine or
translate PackLab fields into engine-specific options; those responsibilities
remain in the existing adapter functions.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from .feature_extraction import (
    PACKAGED_CONSUMER_GOODS_PRESET as PACKAGED_FEATURE_EXTRACTION_PRESET,
)
from .feature_extraction import (
    FeatureExtractionConfig,
)
from .matching import MatcherSelectionConfig
from .sparse_mapping import SparseMappingConfig

RECONSTRUCTION_PRESET_CONTRACT = "packlab.reconstruction-preset.v1"
PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_ID = "packaged-consumer-goods-reconstruction"
PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_VERSION = "1"

_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_WINDOWS_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")
_ENGINE_OPTION_PREFIXES = (
    "SiftExtraction.",
    "SequentialMatching.",
    "Mapper.",
    "FeatureExtraction.",
    "FeatureMatching.",
)
_OVERRIDE_FIELDS = frozenset(
    {
        "preset_id",
        "preset_version",
        "feature_extraction",
        "matcher",
        "sparse_mapping",
    }
)
_SPARSE_MAPPING_FIELDS = frozenset(
    {"database_asset_id", "image_path_asset_id", "sparse_output_asset_id"}
)


class ReconstructionPresetError(ValueError):
    """Raised when a reconstruction preset is invalid or unsafe."""


class UnsupportedReconstructionPresetOption(ReconstructionPresetError):
    """Raised when an override is outside the PackLab preset contract."""


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


def _contains_engine_option(value: object) -> bool:
    if isinstance(value, str):
        return value.startswith("--") or value.startswith(_ENGINE_OPTION_PREFIXES)
    if isinstance(value, Mapping):
        return any(
            _contains_engine_option(key) or _contains_engine_option(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return any(_contains_engine_option(item) for item in value)
    return False


def _validate_override_mapping(overrides: Mapping[str, object]) -> None:
    if not isinstance(overrides, Mapping):
        raise ReconstructionPresetError("preset overrides must be a mapping")
    if any(not isinstance(key, str) for key in overrides):
        raise ReconstructionPresetError("preset override keys must be strings")
    if _contains_absolute_path(overrides):
        raise ReconstructionPresetError("preset overrides cannot contain absolute paths")
    if _contains_engine_option(overrides):
        raise UnsupportedReconstructionPresetOption(
            "engine-specific CLI options are outside the PackLab preset contract"
        )


def _safe_identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ReconstructionPresetError(f"{field_name} must be a safe lowercase identifier")
    return value


def _validated_notes(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ReconstructionPresetError(f"{field_name} must be a sequence of strings")
    notes = tuple(value)
    if any(not isinstance(note, str) or not note.strip() for note in notes):
        raise ReconstructionPresetError(f"{field_name} must contain non-empty strings")
    if _contains_absolute_path(notes) or _contains_engine_option(notes):
        raise ReconstructionPresetError(f"{field_name} contains an unsafe value")
    return notes


def _immutable_view(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _immutable_view(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_immutable_view(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_immutable_view(item) for item in value)
    return value


def _sparse_mapping_with_overrides(
    configuration: SparseMappingConfig,
    overrides: Mapping[str, object],
) -> SparseMappingConfig:
    if not isinstance(overrides, Mapping):
        raise ReconstructionPresetError("sparse_mapping overrides must be a mapping")
    values: dict[str, object] = {}
    for key, value in overrides.items():
        if not isinstance(key, str) or key not in _SPARSE_MAPPING_FIELDS:
            raise UnsupportedReconstructionPresetOption(
                f"unsupported sparse-mapping option: {key!r}"
            )
        if _contains_absolute_path(value):
            raise ReconstructionPresetError(f"absolute paths are not allowed: {key}")
        values[key] = value
    try:
        return replace(configuration, **cast(dict[str, Any], values))
    except (TypeError, ValueError) as error:
        raise ReconstructionPresetError(f"invalid sparse-mapping override: {error}") from error


@dataclass(frozen=True, slots=True)
class ReconstructionPreset:
    """Immutable versioned composition of PackLab reconstruction settings.

    The initial packaged-consumer-goods values are a configuration starting
    point only.  They are not physical benchmark evidence or a universal
    optimum, and this type never represents materialized reconstruction output.
    """

    preset_id: str = PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_ID
    preset_version: str = PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_VERSION
    feature_extraction: FeatureExtractionConfig = PACKAGED_FEATURE_EXTRACTION_PRESET
    matcher: MatcherSelectionConfig = field(default_factory=MatcherSelectionConfig)
    sparse_mapping: SparseMappingConfig = field(default_factory=SparseMappingConfig)
    tradeoff_notes: tuple[str, ...] = (
        "Initial packaged-consumer-goods configuration starting point; not physical benchmark evidence or a universal optimum.",
        "Component settings remain PackLab-owned and are translated to engine options only by existing adapter boundaries.",
    )
    limitations: tuple[str, ...] = (
        "Configuration only; it does not execute or install COLMAP/OpenMVS.",
        "It does not claim filesystem materialization, dense reconstruction, CAD authority, metric calibration, or METRIC_VERIFIED output.",
        "Relative reconstruction state and metric verification remain downstream contracts owned by later stages.",
    )

    def __post_init__(self) -> None:
        _safe_identifier(self.preset_id, "preset_id")
        _safe_identifier(self.preset_version, "preset_version")
        if not isinstance(self.feature_extraction, FeatureExtractionConfig):
            raise ReconstructionPresetError("feature_extraction must be a FeatureExtractionConfig")
        if not isinstance(self.matcher, MatcherSelectionConfig):
            raise ReconstructionPresetError("matcher must be a MatcherSelectionConfig")
        if not isinstance(self.sparse_mapping, SparseMappingConfig):
            raise ReconstructionPresetError("sparse_mapping must be a SparseMappingConfig")
        object.__setattr__(
            self, "tradeoff_notes", _validated_notes(self.tradeoff_notes, "tradeoff_notes")
        )
        object.__setattr__(self, "limitations", _validated_notes(self.limitations, "limitations"))
        if _contains_absolute_path(self.to_dict()) or _contains_engine_option(self.to_dict()):
            raise ReconstructionPresetError("preset contains an unsafe path or engine option")

    @property
    def preset_identity(self) -> str:
        return f"{self.preset_id}:{self.preset_version}"

    @classmethod
    def from_overrides(cls, overrides: Mapping[str, object] | None = None) -> ReconstructionPreset:
        """Build the named initial preset with validated non-mutating overrides."""

        return PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET.with_overrides(overrides)

    def with_overrides(self, overrides: Mapping[str, object] | None = None) -> ReconstructionPreset:
        if overrides is None:
            return self
        _validate_override_mapping(overrides)
        values: dict[str, object] = {}
        for key, value in overrides.items():
            if key not in _OVERRIDE_FIELDS:
                raise UnsupportedReconstructionPresetOption(
                    f"unsupported reconstruction-preset option: {key!r}"
                )
            if key in {"preset_id", "preset_version"}:
                values[key] = _safe_identifier(value, key)
            elif key == "feature_extraction":
                if not isinstance(value, Mapping):
                    raise ReconstructionPresetError(
                        "feature_extraction overrides must be a mapping"
                    )
                values[key] = self.feature_extraction.with_overrides(value)
            elif key == "matcher":
                if not isinstance(value, Mapping):
                    raise ReconstructionPresetError("matcher overrides must be a mapping")
                values[key] = self.matcher.with_overrides(value)
            elif key == "sparse_mapping":
                if not isinstance(value, Mapping):
                    raise ReconstructionPresetError("sparse_mapping overrides must be a mapping")
                values[key] = _sparse_mapping_with_overrides(self.sparse_mapping, value)
        return replace(self, **cast(dict[str, Any], values))

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": RECONSTRUCTION_PRESET_CONTRACT,
            "preset_id": self.preset_id,
            "preset_version": self.preset_version,
            "preset_identity": self.preset_identity,
            "feature_extraction": self.feature_extraction.to_dict(),
            "matcher": self.matcher.to_dict(),
            "sparse_mapping": self.sparse_mapping.as_dict(),
            "tradeoff_notes": list(self.tradeoff_notes),
            "limitations": list(self.limitations),
        }

    as_dict = to_dict

    def serialize(self) -> str:
        """Return canonical UTF-8-safe JSON for durable preset provenance."""

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def configuration_digest(self) -> str:
        """Return the stable SHA-256 digest of canonical preset JSON."""

        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()

    @property
    def digest(self) -> str:
        return self.configuration_digest()

    def configuration_view(self) -> Mapping[str, object]:
        """Return an immutable PackLab-owned view suitable for a job spec."""

        value = self.to_dict()
        value["configuration_digest"] = self.configuration_digest()
        return cast(Mapping[str, object], _immutable_view(value))

    def to_configuration_view(self) -> Mapping[str, object]:
        """Compatibility alias for consumers that use an explicit conversion name."""

        return self.configuration_view()

    @property
    def configuration(self) -> Mapping[str, object]:
        """PackLab-owned immutable configuration view for ReconstructionJobSpec."""

        return self.configuration_view()


PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET = ReconstructionPreset()
DEFAULT_RECONSTRUCTION_PRESET = PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET
CONSUMER_GOODS_RECONSTRUCTION_PRESET = PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET


__all__ = [
    "CONSUMER_GOODS_RECONSTRUCTION_PRESET",
    "DEFAULT_RECONSTRUCTION_PRESET",
    "PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET",
    "PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_ID",
    "PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_VERSION",
    "RECONSTRUCTION_PRESET_CONTRACT",
    "ReconstructionPreset",
    "ReconstructionPresetError",
    "UnsupportedReconstructionPresetOption",
]
