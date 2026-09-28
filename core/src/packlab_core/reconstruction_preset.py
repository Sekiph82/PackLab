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
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from .capabilities import Capability, CapabilityStatus
from .feature_extraction import (
    PACKAGED_CONSUMER_GOODS_PRESET as PACKAGED_FEATURE_EXTRACTION_PRESET,
)
from .feature_extraction import (
    FeatureExtractionConfig,
)
from .matching import MatcherSelectionConfig
from .sparse_mapping import SparseMappingConfig

RECONSTRUCTION_PRESET_CONTRACT = "packlab.reconstruction-preset.v1"
RESOURCE_POLICY_CONTRACT = "packlab.reconstruction-resource-policy.v1"
PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_ID = "packaged-consumer-goods-reconstruction"
PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_VERSION = "1"
CPU_SAFE_RESOURCE_PRESET_ID = "cpu-safe"
CPU_SAFE_RESOURCE_PRESET_VERSION = "1"
GPU_AWARE_RESOURCE_PRESET_ID = "gpu-aware"
GPU_AWARE_RESOURCE_PRESET_VERSION = "1"

MAX_INPUT_BYTES = 64 * 1024**3
MAX_WORKING_SET_BYTES = 256 * 1024**3
MAX_RETAINED_OUTPUT_BYTES = 256 * 1024**3
MAX_PARALLEL_WORKERS = 64

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
        "resource_policy",
    }
)
_SPARSE_MAPPING_FIELDS = frozenset(
    {"database_asset_id", "image_path_asset_id", "sparse_output_asset_id"}
)


class ReconstructionPresetError(ValueError):
    """Raised when a reconstruction preset is invalid or unsafe."""


class UnsupportedReconstructionPresetOption(ReconstructionPresetError):
    """Raised when an override is outside the PackLab preset contract."""


class ResourceExecutionMode(StrEnum):
    """PackLab-owned execution requests; values are not engine CLI flags."""

    CPU_ONLY = "cpu-only"
    GPU_PREFERRED = "gpu-preferred"
    GPU_REQUIRED = "gpu-required"


class ResourcePlanOutcome(StrEnum):
    """Deterministic preflight outcomes for a resource plan."""

    CPU_SELECTED = "cpu-selected"
    CPU_FALLBACK = "cpu-fallback"
    GPU_SELECTED = "gpu-selected"
    GPU_UNAVAILABLE = "gpu-unavailable"
    OVER_BUDGET = "over-budget"


def _bounded_positive_integer(value: object, field_name: str, maximum: int) -> int:
    if type(value) is not int or value <= 0 or value > maximum:
        raise ReconstructionPresetError(
            f"{field_name} must be a positive integer no greater than {maximum}"
        )
    return value


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """Immutable upper bounds for one declarative reconstruction preflight."""

    input_bytes: int = 4 * 1024**3
    working_set_bytes: int = 8 * 1024**3
    retained_output_bytes: int = 4 * 1024**3
    parallel_workers: int = 1

    def __post_init__(self) -> None:
        _bounded_positive_integer(self.input_bytes, "input_bytes", MAX_INPUT_BYTES)
        _bounded_positive_integer(
            self.working_set_bytes, "working_set_bytes", MAX_WORKING_SET_BYTES
        )
        _bounded_positive_integer(
            self.retained_output_bytes, "retained_output_bytes", MAX_RETAINED_OUTPUT_BYTES
        )
        _bounded_positive_integer(self.parallel_workers, "parallel_workers", MAX_PARALLEL_WORKERS)
        if self.input_bytes > self.working_set_bytes:
            raise ReconstructionPresetError("input_bytes cannot exceed working_set_bytes")
        if self.retained_output_bytes > self.working_set_bytes:
            raise ReconstructionPresetError("retained_output_bytes cannot exceed working_set_bytes")

    def to_dict(self) -> dict[str, int]:
        return {
            "input_bytes": self.input_bytes,
            "working_set_bytes": self.working_set_bytes,
            "retained_output_bytes": self.retained_output_bytes,
            "parallel_workers": self.parallel_workers,
        }


@dataclass(frozen=True, slots=True)
class ResourceEstimates:
    """Explicit positive estimates checked before any execution boundary."""

    input_bytes: int
    working_set_bytes: int
    retained_output_bytes: int
    parallel_workers: int

    def __post_init__(self) -> None:
        _bounded_positive_integer(self.input_bytes, "input_bytes", MAX_INPUT_BYTES)
        _bounded_positive_integer(
            self.working_set_bytes, "working_set_bytes", MAX_WORKING_SET_BYTES
        )
        _bounded_positive_integer(
            self.retained_output_bytes, "retained_output_bytes", MAX_RETAINED_OUTPUT_BYTES
        )
        _bounded_positive_integer(self.parallel_workers, "parallel_workers", MAX_PARALLEL_WORKERS)
        if self.input_bytes > self.working_set_bytes:
            raise ReconstructionPresetError("input_bytes cannot exceed working_set_bytes")
        if self.retained_output_bytes > self.working_set_bytes:
            raise ReconstructionPresetError("retained_output_bytes cannot exceed working_set_bytes")

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> ResourceEstimates:
        if not isinstance(values, Mapping):
            raise ReconstructionPresetError("resource estimates must be a mapping")
        expected = {"input_bytes", "working_set_bytes", "retained_output_bytes", "parallel_workers"}
        if set(values) != expected:
            raise ReconstructionPresetError(
                "resource estimates must contain exactly the four estimates"
            )
        return cls(
            input_bytes=cast(int, values["input_bytes"]),
            working_set_bytes=cast(int, values["working_set_bytes"]),
            retained_output_bytes=cast(int, values["retained_output_bytes"]),
            parallel_workers=cast(int, values["parallel_workers"]),
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "input_bytes": self.input_bytes,
            "working_set_bytes": self.working_set_bytes,
            "retained_output_bytes": self.retained_output_bytes,
            "parallel_workers": self.parallel_workers,
        }


@dataclass(frozen=True, slots=True)
class ResourceCapabilitySnapshot:
    """Immutable capability records supplied by the caller, never discovered here."""

    records: Mapping[str, Capability] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.records, Mapping):
            raise ReconstructionPresetError("capability records must be a mapping")
        copied: dict[str, Capability] = {}
        for name, capability in self.records.items():
            if not isinstance(name, str) or not isinstance(capability, Capability):
                raise ReconstructionPresetError(
                    "capability records must map names to Capability values"
                )
            if capability.name != name or not isinstance(capability.status, CapabilityStatus):
                raise ReconstructionPresetError("capability record name or status is invalid")
            if not isinstance(capability.provenance, str) or not capability.provenance.strip():
                raise ReconstructionPresetError("capability provenance must be non-empty")
            copied[name] = capability
        object.__setattr__(self, "records", MappingProxyType(copied))

    @property
    def cuda(self) -> Capability:
        return self.records.get(
            "cuda",
            Capability(
                "cuda",
                CapabilityStatus.UNKNOWN,
                None,
                "capability snapshot has no explicit CUDA record",
                "CUDA availability was not supplied",
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {name: capability.as_dict() for name, capability in self.records.items()}

    def serialize(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


class ResourceResolutionError(ReconstructionPresetError):
    """Base class for PackLab-owned resource-plan resolution failures."""

    outcome: ResourcePlanOutcome

    def __init__(self, message: str, outcome: ResourcePlanOutcome) -> None:
        super().__init__(message)
        self.outcome = outcome


class GPUUnavailableError(ResourceResolutionError):
    """Raised when gpu-required has no explicit available CUDA capability."""

    def __init__(self, capability: Capability) -> None:
        self.capability = capability
        super().__init__(
            f"GPU is unavailable: CUDA capability is {capability.status.value}",
            ResourcePlanOutcome.GPU_UNAVAILABLE,
        )


class ResourceBudgetExceededError(ResourceResolutionError):
    """Raised when an explicit estimate exceeds a policy limit."""

    def __init__(self, resource_name: str, estimate: int, limit: int) -> None:
        self.resource_name = resource_name
        self.estimate = estimate
        self.limit = limit
        super().__init__(
            f"{resource_name} estimate {estimate} exceeds limit {limit}",
            ResourcePlanOutcome.OVER_BUDGET,
        )


@dataclass(frozen=True, slots=True)
class ResourcePlan:
    """Immutable, serializable result of resource-policy preflight."""

    policy_identity: str
    policy_digest: str
    requested_mode: ResourceExecutionMode
    selected_mode: ResourceExecutionMode
    capability_status: CapabilityStatus
    capability_provenance: str
    capability_version: str | None
    capability_detail: str
    capability_snapshot_digest: str
    limits: ResourceLimits
    estimates: ResourceEstimates
    outcome: ResourcePlanOutcome
    fallback_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.requested_mode, ResourceExecutionMode):
            raise ReconstructionPresetError("requested_mode is invalid")
        if not isinstance(self.selected_mode, ResourceExecutionMode):
            raise ReconstructionPresetError("selected_mode is invalid")
        if not isinstance(self.capability_status, CapabilityStatus):
            raise ReconstructionPresetError("capability_status is invalid")
        if not isinstance(self.outcome, ResourcePlanOutcome):
            raise ReconstructionPresetError("resource plan outcome is invalid")
        if not self.capability_provenance.strip() or not self.capability_detail.strip():
            raise ReconstructionPresetError("capability provenance and detail are required")

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_identity": self.policy_identity,
            "policy_digest": self.policy_digest,
            "requested_mode": self.requested_mode.value,
            "selected_mode": self.selected_mode.value,
            "capability_status": self.capability_status.value,
            "capability_provenance": self.capability_provenance,
            "capability_version": self.capability_version,
            "capability_detail": self.capability_detail,
            "capability_snapshot_digest": self.capability_snapshot_digest,
            "limits": self.limits.to_dict(),
            "estimates": self.estimates.to_dict(),
            "outcome": self.outcome.value,
            "fallback_reason": self.fallback_reason,
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ReconstructionResourcePolicy:
    """Versioned, backend-neutral resource policy; preflight only."""

    policy_id: str
    policy_version: str
    execution_mode: ResourceExecutionMode
    limits: ResourceLimits
    tradeoff_notes: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _safe_identifier(self.policy_id, "policy_id")
        _safe_identifier(self.policy_version, "policy_version")
        if not isinstance(self.execution_mode, ResourceExecutionMode):
            raise ReconstructionPresetError("execution_mode is invalid")
        if not isinstance(self.limits, ResourceLimits):
            raise ReconstructionPresetError("limits must be ResourceLimits")
        object.__setattr__(
            self, "tradeoff_notes", _validated_notes(self.tradeoff_notes, "tradeoff_notes")
        )
        object.__setattr__(self, "limitations", _validated_notes(self.limitations, "limitations"))

    @property
    def policy_identity(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": RESOURCE_POLICY_CONTRACT,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_identity": self.policy_identity,
            "execution_mode": self.execution_mode.value,
            "limits": self.limits.to_dict(),
            "tradeoff_notes": list(self.tradeoff_notes),
            "limitations": list(self.limitations),
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()

    def resolve(
        self,
        capabilities: ResourceCapabilitySnapshot,
        estimates: ResourceEstimates | Mapping[str, object],
    ) -> ResourcePlan:
        if not isinstance(capabilities, ResourceCapabilitySnapshot):
            raise ReconstructionPresetError(
                "resource resolution requires an explicit capability snapshot"
            )
        if not isinstance(estimates, ResourceEstimates):
            estimates = ResourceEstimates.from_mapping(estimates)
        for field_name in (
            "input_bytes",
            "working_set_bytes",
            "retained_output_bytes",
            "parallel_workers",
        ):
            estimate = getattr(estimates, field_name)
            limit = getattr(self.limits, field_name)
            if estimate > limit:
                raise ResourceBudgetExceededError(field_name, estimate, limit)

        capability = capabilities.cuda
        if self.execution_mode is ResourceExecutionMode.CPU_ONLY:
            outcome = ResourcePlanOutcome.CPU_SELECTED
            selected_mode = ResourceExecutionMode.CPU_ONLY
            fallback_reason = None
        elif capability.status is CapabilityStatus.AVAILABLE:
            outcome = ResourcePlanOutcome.GPU_SELECTED
            selected_mode = self.execution_mode
            fallback_reason = None
        elif self.execution_mode is ResourceExecutionMode.GPU_PREFERRED:
            outcome = ResourcePlanOutcome.CPU_FALLBACK
            selected_mode = ResourceExecutionMode.CPU_ONLY
            fallback_reason = (
                f"explicit CUDA capability is {capability.status.value}: "
                f"{capability.detail or 'no direct CUDA capability available'}"
            )
        else:
            raise GPUUnavailableError(capability)

        return ResourcePlan(
            policy_identity=self.policy_identity,
            policy_digest=self.digest,
            requested_mode=self.execution_mode,
            selected_mode=selected_mode,
            capability_status=capability.status,
            capability_provenance=capability.provenance,
            capability_version=capability.version,
            capability_detail=capability.detail or "no capability detail supplied",
            capability_snapshot_digest=capabilities.digest,
            limits=self.limits,
            estimates=estimates,
            outcome=outcome,
            fallback_reason=fallback_reason,
        )


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


CPU_SAFE_RESOURCE_PRESET = ReconstructionResourcePolicy(
    policy_id=CPU_SAFE_RESOURCE_PRESET_ID,
    policy_version=CPU_SAFE_RESOURCE_PRESET_VERSION,
    execution_mode=ResourceExecutionMode.CPU_ONLY,
    limits=ResourceLimits(),
    tradeoff_notes=(
        "Conservative CPU-only starting point for bounded local preflight.",
        "Values are configuration defaults, not hardware benchmarks or performance guarantees.",
    ),
    limitations=(
        "Does not inspect hardware, launch processes, reserve memory, or execute reconstruction.",
        "Does not claim universal hardware suitability or physical reconstruction accuracy.",
    ),
)

GPU_AWARE_RESOURCE_PRESET = ReconstructionResourcePolicy(
    policy_id=GPU_AWARE_RESOURCE_PRESET_ID,
    policy_version=GPU_AWARE_RESOURCE_PRESET_VERSION,
    execution_mode=ResourceExecutionMode.GPU_PREFERRED,
    limits=ResourceLimits(
        input_bytes=16 * 1024**3,
        working_set_bytes=64 * 1024**3,
        retained_output_bytes=32 * 1024**3,
        parallel_workers=4,
    ),
    tradeoff_notes=(
        "GPU-preferred starting point that falls back to CPU only from explicit CUDA capability evidence.",
        "Values are configuration defaults, not hardware benchmarks or performance guarantees.",
    ),
    limitations=(
        "Does not inspect hardware, launch processes, reserve memory, or execute reconstruction.",
        "A driver label or arbitrary hardware string cannot establish CUDA availability.",
    ),
)


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
    resource_policy: ReconstructionResourcePolicy = CPU_SAFE_RESOURCE_PRESET
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
        if not isinstance(self.resource_policy, ReconstructionResourcePolicy):
            raise ReconstructionPresetError(
                "resource_policy must be a ReconstructionResourcePolicy"
            )
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
            elif key == "resource_policy":
                if not isinstance(value, ReconstructionResourcePolicy):
                    raise ReconstructionPresetError(
                        "resource_policy overrides must be a ReconstructionResourcePolicy"
                    )
                values[key] = value
        return replace(self, **cast(dict[str, Any], values))

    def resolve_resource_plan(
        self,
        capabilities: ResourceCapabilitySnapshot,
        estimates: ResourceEstimates | Mapping[str, object],
    ) -> ResourcePlan:
        """Resolve the immutable policy without probing or launching an engine."""

        return self.resource_policy.resolve(capabilities, estimates)

    resolve_resources = resolve_resource_plan

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": RECONSTRUCTION_PRESET_CONTRACT,
            "preset_id": self.preset_id,
            "preset_version": self.preset_version,
            "preset_identity": self.preset_identity,
            "feature_extraction": self.feature_extraction.to_dict(),
            "matcher": self.matcher.to_dict(),
            "sparse_mapping": self.sparse_mapping.as_dict(),
            "resource_policy": self.resource_policy.to_dict(),
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
    "CPU_SAFE_RESOURCE_PRESET",
    "CPU_SAFE_RESOURCE_PRESET_ID",
    "CPU_SAFE_RESOURCE_PRESET_VERSION",
    "DEFAULT_RECONSTRUCTION_PRESET",
    "GPU_AWARE_RESOURCE_PRESET",
    "GPU_AWARE_RESOURCE_PRESET_ID",
    "GPU_AWARE_RESOURCE_PRESET_VERSION",
    "GPUUnavailableError",
    "MAX_INPUT_BYTES",
    "MAX_PARALLEL_WORKERS",
    "MAX_RETAINED_OUTPUT_BYTES",
    "MAX_WORKING_SET_BYTES",
    "PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET",
    "PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_ID",
    "PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET_VERSION",
    "RECONSTRUCTION_PRESET_CONTRACT",
    "RESOURCE_POLICY_CONTRACT",
    "ResourceBudgetExceededError",
    "ResourceCapabilitySnapshot",
    "ResourceEstimates",
    "ResourceExecutionMode",
    "ResourceLimits",
    "ResourcePlan",
    "ResourcePlanOutcome",
    "ResourceResolutionError",
    "ReconstructionResourcePolicy",
    "ReconstructionPreset",
    "ReconstructionPresetError",
    "UnsupportedReconstructionPresetOption",
]
