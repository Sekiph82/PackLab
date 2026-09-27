"""Backend-neutral matcher selection for ordered PackLab image datasets.

This module selects a deterministic matching strategy from PackLab-owned
capture metadata.  It does not compute image pairs or inspect image pixels.
COLMAP option names are confined to :func:`to_colmap_matcher_parameters`,
which only returns configuration values and never invokes an external engine.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, cast

COLMAP_ENGINE_VERSION = "3.12.6"
MATCHER_SELECTION_CONTRACT = "packlab.matcher-selection.v1"


class MatcherSelectionError(ValueError):
    """Raised when matcher selection input is invalid or unsafe."""


class InvalidMatcherConfiguration(MatcherSelectionError):
    """Raised when overlap/window configuration is invalid."""


class UnsupportedMatcherOption(MatcherSelectionError):
    """Raised when a requested strategy or engine option is not supported."""


class UnsafeAssetId(MatcherSelectionError):
    """Raised when an image asset ID is not a safe repository-relative ID."""


class UnsupportedCaptureMode(MatcherSelectionError):
    """Raised when the capture mode is unknown or unsupported."""


class TurntableMatcherUnsupported(MatcherSelectionError):
    """Raised because turntable data needs an explicit object-transform adapter."""


class CaptureMode(StrEnum):
    """Capture geometry assumptions relevant to matcher selection."""

    GUIDED_ORBIT = "guided_orbit"
    TURNTABLE = "turntable"


class MatcherStrategy(StrEnum):
    """PackLab-owned matcher strategies."""

    SEQUENTIAL = "sequential"


def _capture_mode(value: CaptureMode | str) -> CaptureMode:
    if isinstance(value, CaptureMode):
        return value
    if isinstance(value, str):
        try:
            return CaptureMode(value)
        except ValueError as error:
            raise UnsupportedCaptureMode(
                "capture_mode must be 'guided_orbit' or 'turntable'"
            ) from error
    raise UnsupportedCaptureMode("capture_mode must be a supported string")


def _strategy(value: MatcherStrategy | str) -> MatcherStrategy:
    if isinstance(value, MatcherStrategy):
        return value
    if isinstance(value, str):
        try:
            return MatcherStrategy(value)
        except ValueError as error:
            raise UnsupportedMatcherOption(
                "only the PackLab 'sequential' matcher strategy is supported"
            ) from error
    raise UnsupportedMatcherOption("matcher strategy must be a supported string")


def _require_int(value: object, field_name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise InvalidMatcherConfiguration(
            f"{field_name} must be an integer from {minimum} to {maximum}"
        )
    return value


def _validate_asset_id(value: object, index: int) -> str:
    if not isinstance(value, str) or not value:
        raise UnsafeAssetId(f"image asset ID at index {index} must be a non-empty string")
    if value != value.strip():
        raise UnsafeAssetId(
            f"image asset ID at index {index} must not contain surrounding whitespace"
        )
    if "\\" in value:
        raise UnsafeAssetId(f"image asset ID at index {index} must use portable '/' separators")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise UnsafeAssetId(
            f"image asset ID at index {index} must be repository-relative, not absolute"
        )
    if ":" in value:
        raise UnsafeAssetId(f"image asset ID at index {index} contains an unsafe ':' character")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise UnsafeAssetId(f"image asset ID at index {index} contains a control character")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise UnsafeAssetId(
            f"image asset ID at index {index} must not contain empty, '.' or '..' path segments"
        )
    return value


def _ordered_asset_ids(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
        raise MatcherSelectionError("image_asset_ids must be an ordered sequence of asset IDs")
    ordered = tuple(_validate_asset_id(value, index) for index, value in enumerate(values))
    if len(ordered) < 2:
        raise MatcherSelectionError("at least two ordered image asset IDs are required")
    first_seen: dict[str, int] = {}
    for index, asset_id in enumerate(ordered):
        if asset_id in first_seen:
            raise UnsafeAssetId(
                f"duplicate image asset ID at index {index}; first seen at index {first_seen[asset_id]}"
            )
        first_seen[asset_id] = index
    return ordered


@dataclass(frozen=True, slots=True)
class MatcherSelectionConfig:
    """Immutable ordered-window policy owned by PackLab.

    ``overlap`` is the number of preceding ordered frames available to the
    sequential matcher.  ``window_size`` is the maximum PackLab window for
    that policy and must be larger than ``overlap``.  The window is validated
    here but is not guessed, sorted, or expanded by this module.
    """

    strategy: MatcherStrategy = MatcherStrategy.SEQUENTIAL
    overlap: int = 2
    window_size: int = 5

    def __post_init__(self) -> None:
        object.__setattr__(self, "strategy", _strategy(self.strategy))
        _require_int(self.overlap, "overlap", 1, 64)
        _require_int(self.window_size, "window_size", 2, 256)
        if self.overlap >= self.window_size:
            raise InvalidMatcherConfiguration("overlap must be smaller than window_size")

    @classmethod
    def from_overrides(
        cls, overrides: Mapping[str, object] | None = None
    ) -> MatcherSelectionConfig:
        return cls().with_overrides(overrides)

    def with_overrides(
        self, overrides: Mapping[str, object] | None = None
    ) -> MatcherSelectionConfig:
        if overrides is None:
            return self
        if not isinstance(overrides, Mapping):
            raise InvalidMatcherConfiguration("matcher configuration overrides must be a mapping")
        allowed = {"strategy", "overlap", "window_size"}
        values: dict[str, object] = {}
        for key, value in overrides.items():
            if not isinstance(key, str) or key not in allowed:
                raise UnsupportedMatcherOption(f"unsupported matcher configuration option: {key!r}")
            values[key] = value
        return replace(self, **cast(dict[str, Any], values))

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": MATCHER_SELECTION_CONTRACT,
            "strategy": self.strategy.value,
            "overlap": self.overlap,
            "window_size": self.window_size,
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def configuration_digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()

    @property
    def digest(self) -> str:
        return self.configuration_digest()


@dataclass(frozen=True, slots=True)
class MatcherSelection:
    """Validated, immutable result of guided-orbit matcher selection."""

    capture_mode: CaptureMode
    image_asset_ids: tuple[str, ...]
    configuration: MatcherSelectionConfig

    def __post_init__(self) -> None:
        mode = _capture_mode(self.capture_mode)
        object.__setattr__(self, "capture_mode", mode)
        object.__setattr__(self, "image_asset_ids", _ordered_asset_ids(self.image_asset_ids))
        if not isinstance(self.configuration, MatcherSelectionConfig):
            raise InvalidMatcherConfiguration("configuration must be a MatcherSelectionConfig")
        if mode is CaptureMode.TURNTABLE:
            raise TurntableMatcherUnsupported(
                "turntable input requires an explicit object-transform-aware matcher adapter"
            )

    @property
    def strategy(self) -> MatcherStrategy:
        return self.configuration.strategy

    @property
    def matcher_strategy(self) -> MatcherStrategy:
        return self.strategy

    @property
    def ordered_image_asset_ids(self) -> tuple[str, ...]:
        return self.image_asset_ids

    @property
    def configuration_digest(self) -> str:
        return self.configuration.configuration_digest()

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": MATCHER_SELECTION_CONTRACT,
            "capture_mode": self.capture_mode.value,
            "strategy": self.strategy.value,
            "ordered_image_asset_ids": list(self.image_asset_ids),
            "configuration": self.configuration.to_dict(),
            "configuration_digest": self.configuration_digest,
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def selection_digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()

    @property
    def digest(self) -> str:
        return self.selection_digest()


def select_matcher(
    image_asset_ids: Sequence[str],
    capture_mode: CaptureMode | str,
    configuration: MatcherSelectionConfig | Mapping[str, object] | None = None,
) -> MatcherSelection:
    """Select the PackLab sequential strategy without computing image pairs."""

    mode = _capture_mode(capture_mode)
    if mode is CaptureMode.TURNTABLE:
        raise TurntableMatcherUnsupported(
            "turntable input requires an explicit object-transform-aware matcher adapter"
        )
    if configuration is None:
        config = MatcherSelectionConfig()
    elif isinstance(configuration, MatcherSelectionConfig):
        config = configuration
    elif isinstance(configuration, Mapping):
        config = MatcherSelectionConfig.from_overrides(configuration)
    else:
        raise InvalidMatcherConfiguration(
            "configuration must be a MatcherSelectionConfig or mapping"
        )
    return MatcherSelection(mode, _ordered_asset_ids(image_asset_ids), config)


def to_colmap_matcher_parameters(
    selection: MatcherSelection,
    *,
    engine_version: str = COLMAP_ENGINE_VERSION,
) -> dict[str, int | bool]:
    """Map a validated selection to COLMAP configuration only.

    PackLab's window policy is enforced before this adapter.  COLMAP exposes
    the sequential overlap value but has no equivalent PackLab provenance
    field for the window bound, so the latter remains in the PackLab digest.
    This function never discovers, installs, launches, or executes COLMAP.
    """

    if not isinstance(selection, MatcherSelection):
        raise MatcherSelectionError("selection must be a MatcherSelection")
    if engine_version != COLMAP_ENGINE_VERSION:
        raise UnsupportedMatcherOption(
            f"only COLMAP {COLMAP_ENGINE_VERSION} is supported, not {engine_version}"
        )
    return {
        "SequentialMatching.overlap": selection.configuration.overlap,
        "SequentialMatching.quadratic": False,
        "SequentialMatching.loop_detection": False,
    }


map_to_colmap = to_colmap_matcher_parameters


__all__ = [
    "COLMAP_ENGINE_VERSION",
    "CaptureMode",
    "InvalidMatcherConfiguration",
    "MATCHER_SELECTION_CONTRACT",
    "MatcherSelection",
    "MatcherSelectionConfig",
    "MatcherSelectionError",
    "MatcherStrategy",
    "TurntableMatcherUnsupported",
    "UnsafeAssetId",
    "UnsupportedCaptureMode",
    "UnsupportedMatcherOption",
    "map_to_colmap",
    "select_matcher",
    "to_colmap_matcher_parameters",
]
