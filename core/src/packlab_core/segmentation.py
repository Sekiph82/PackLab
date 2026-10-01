"""Backend-neutral segmentation contracts owned by PackLab.

This module contains data contracts only.  A concrete model/runtime is an
adapter concern and cannot become a domain dependency by implementing this
protocol.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

SEGMENTATION_CONTRACT_VERSION = "packlab.segmentation.v1"
PIXEL_ORIGIN_TOP_LEFT = "top_left_pixel_center"
PIXEL_INDEX_ZERO_BASED = "zero_based_integer_xy"
MASK_AUTHORITY_CLASS = "DERIVED_MASK"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_SEGMENTS = frozenset({"private", "secret", "secrets"})


class SegmentationContractError(ValueError):
    """Base error for invalid PackLab segmentation data."""


class InvalidSegmentationRequest(SegmentationContractError):
    """Raised when a public segmentation request is not safe to execute."""


class InvalidMaskArtifact(SegmentationContractError):
    """Raised when a derived mask cannot be trusted as a contract artifact."""


class PromptKind(StrEnum):
    AUTOMATIC = "automatic"
    POINT = "point"
    BOX = "box"
    PRIOR_MASK = "prior-mask"


class SegmentationStatus(StrEnum):
    SUCCEEDED = "succeeded"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class SegmentationCapability(StrEnum):
    AUTOMATIC = "automatic"
    POINT_PROMPT = "point-prompt"
    BOX_PROMPT = "box-prompt"
    PRIOR_MASK_REFINEMENT = "prior-mask-refinement"
    BATCH = "batch"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SegmentationContractError(f"{field_name} must be non-empty text")
    return value


def _require_sha256(value: str, field_name: str) -> str:
    _require_text(value, field_name)
    if not _SHA256.fullmatch(value):
        raise SegmentationContractError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _finite(value: float, field_name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise SegmentationContractError(f"{field_name} must be finite")
    return float(value)


def _positive_int(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise SegmentationContractError(f"{field_name} must be a positive integer")
    return value


def _nonnegative_int(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise SegmentationContractError(f"{field_name} must be a non-negative integer")
    return value


def _asset_id(value: str, field_name: str, *, areas: tuple[str, ...] | None = None) -> str:
    normalized = _require_text(value, field_name).replace("\\", "/")
    if (
        normalized.startswith("/")
        or re.fullmatch(r"[A-Za-z]:/.*", normalized)
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise SegmentationContractError(f"{field_name} must be a safe relative asset ID")
    if any(part.lower() in _PRIVATE_SEGMENTS for part in normalized.split("/")):
        raise SegmentationContractError(f"{field_name} cannot target a private path")
    if areas is not None and normalized.split("/", 1)[0] not in areas:
        allowed = ", ".join(areas)
        raise SegmentationContractError(f"{field_name} must be under {allowed}")
    return normalized


def _json_value(value: object, field_name: str = "value") -> object:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return _finite(value, field_name)
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise SegmentationContractError(f"{field_name} mapping keys must be non-empty text")
            result[key] = _json_value(item, f"{field_name}.{key}")
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_value(item, field_name) for item in value]
    raise SegmentationContractError(f"{field_name} must contain JSON-compatible values")


def _freeze_json(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _timestamp(value: str) -> str:
    _require_text(value, "created_at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SegmentationContractError("created_at must be ISO-8601") from error
    if parsed.tzinfo is None:
        raise SegmentationContractError("created_at must include a timezone")
    return value


@dataclass(frozen=True, slots=True)
class SegmentationCapabilityReport:
    """A probe result; availability is never inferred from an import."""

    backend_id: str
    available: bool
    capabilities: tuple[SegmentationCapability, ...] = ()
    limitations: tuple[str, ...] = ()
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.backend_id, "backend_id")
        if not isinstance(self.available, bool):
            raise SegmentationContractError("available must be a boolean")
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        details = _json_value(self.details, "capability_details")
        if not isinstance(details, dict):
            raise SegmentationContractError("capability_details must be a mapping")
        object.__setattr__(self, "details", _freeze_json(details))
        if not self.available and self.capabilities:
            raise SegmentationContractError("unavailable backend cannot advertise capabilities")

    def as_dict(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "available": self.available,
            "capabilities": [item.value for item in self.capabilities],
            "limitations": list(self.limitations),
            "details": _thaw_json(self.details),
        }


@dataclass(frozen=True, slots=True)
class SegmentationProvenance:
    """Explicit backend/model/runtime identity without selecting any model."""

    backend_id: str
    backend_version: str
    model_id: str
    model_version: str
    checkpoint_id: str
    checkpoint_sha256: str
    runtime_id: str
    runtime_version: str
    license_record: str
    runtime_details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "backend_id",
            "backend_version",
            "model_id",
            "model_version",
            "checkpoint_id",
            "runtime_id",
            "runtime_version",
            "license_record",
        ):
            _require_text(getattr(self, name), name)
        if self.checkpoint_sha256 != "not-applicable":
            _require_sha256(self.checkpoint_sha256, "checkpoint_sha256")
        details = _json_value(self.runtime_details, "runtime_details")
        if not isinstance(details, dict):
            raise SegmentationContractError("runtime_details must be a mapping")
        object.__setattr__(self, "runtime_details", _freeze_json(details))

    def as_dict(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "backend_version": self.backend_version,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_sha256": self.checkpoint_sha256,
            "runtime_id": self.runtime_id,
            "runtime_version": self.runtime_version,
            "license_record": self.license_record,
            "runtime_details": _thaw_json(self.runtime_details),
        }


@dataclass(frozen=True, slots=True)
class PromptEvidence:
    kind: PromptKind
    data: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = _json_value(self.data, "prompt_data")
        if not isinstance(normalized, dict):
            raise SegmentationContractError("prompt_data must be a mapping")
        object.__setattr__(self, "data", _freeze_json(normalized))

    def as_dict(self) -> dict[str, object]:
        return {"kind": self.kind.value, "data": _thaw_json(self.data)}


@dataclass(frozen=True, slots=True)
class CoordinateTransform:
    """Mapping between model-input and source-image pixel-center coordinates."""

    source_width: int
    source_height: int
    model_width: int
    model_height: int
    scale_x: float = 1.0
    scale_y: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    interpolation: str = "nearest"

    def __post_init__(self) -> None:
        for name, value in (
            ("source_width", self.source_width),
            ("source_height", self.source_height),
            ("model_width", self.model_width),
            ("model_height", self.model_height),
        ):
            _positive_int(value, name)
        for name in ("scale_x", "scale_y"):
            if _finite(getattr(self, name), name) <= 0:
                raise SegmentationContractError(f"{name} must be positive")
        for name in ("offset_x", "offset_y"):
            _finite(getattr(self, name), name)
        _require_text(self.interpolation, "interpolation")

    @property
    def resized(self) -> bool:
        return (
            self.source_width != self.model_width
            or self.source_height != self.model_height
            or self.scale_x != 1.0
            or self.scale_y != 1.0
            or self.offset_x != 0.0
            or self.offset_y != 0.0
        )

    def model_to_source(self, x: float, y: float) -> tuple[float, float]:
        return (
            (_finite(x, "x") - self.offset_x) / self.scale_x,
            (_finite(y, "y") - self.offset_y) / self.scale_y,
        )

    def source_to_model(self, x: float, y: float) -> tuple[float, float]:
        return (
            _finite(x, "x") * self.scale_x + self.offset_x,
            _finite(y, "y") * self.scale_y + self.offset_y,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "source_dimensions": {"width": self.source_width, "height": self.source_height},
            "model_dimensions": {"width": self.model_width, "height": self.model_height},
            "resized": self.resized,
            "scale": {"x": self.scale_x, "y": self.scale_y},
            "offset": {"x": self.offset_x, "y": self.offset_y},
            "interpolation": self.interpolation,
            "origin": PIXEL_ORIGIN_TOP_LEFT,
            "pixel_index": PIXEL_INDEX_ZERO_BASED,
        }


@dataclass(frozen=True, slots=True)
class MaskRaster:
    """Optional in-memory raster for adapters/tests; persisted masks use asset IDs."""

    width: int
    height: int
    values: tuple[bool, ...]

    def __post_init__(self) -> None:
        _positive_int(self.width, "mask_width")
        _positive_int(self.height, "mask_height")
        values = tuple(self.values)
        if len(values) != self.width * self.height or not all(
            isinstance(item, bool) for item in values
        ):
            raise SegmentationContractError(
                "mask raster values must match dimensions and be boolean"
            )
        object.__setattr__(self, "values", values)

    @property
    def digest(self) -> str:
        return _digest({"width": self.width, "height": self.height, "values": list(self.values)})

    def sample(self, x: int, y: int) -> bool:
        if (
            not isinstance(x, int)
            or not isinstance(y, int)
            or not (0 <= x < self.width and 0 <= y < self.height)
        ):
            raise IndexError("mask coordinate is outside the raster")
        return self.values[y * self.width + x]


@dataclass(frozen=True, slots=True)
class SegmentationRequest:
    project_id: str
    source_image_asset_id: str
    source_digest: str
    source_width: int
    source_height: int
    prompt: PromptEvidence = field(default_factory=lambda: PromptEvidence(PromptKind.AUTOMATIC))
    output_asset_id: str = "working/masks/pending.mask"

    def __post_init__(self) -> None:
        _require_text(self.project_id, "project_id")
        _asset_id(self.source_image_asset_id, "source_image_asset_id")
        _require_sha256(self.source_digest, "source_digest")
        _positive_int(self.source_width, "source_width")
        _positive_int(self.source_height, "source_height")
        _asset_id(self.output_asset_id, "output_asset_id", areas=("working", "derived"))

    def as_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "source_image_asset_id": self.source_image_asset_id,
            "source_digest": self.source_digest,
            "source_dimensions": {"width": self.source_width, "height": self.source_height},
            "prompt": self.prompt.as_dict(),
            "output_asset_id": self.output_asset_id,
        }


@dataclass(frozen=True, slots=True)
class MaskArtifact:
    artifact_id: str
    source_image_asset_id: str
    source_digest: str
    source_width: int
    source_height: int
    mask_asset_id: str
    mask_digest: str
    mask_width: int
    mask_height: int
    transform: CoordinateTransform
    provenance: SegmentationProvenance
    prompt: PromptEvidence
    mask_revision: str
    created_at: str
    post_processing_version: str
    confidence: float | None = None
    parent_mask_revision: str | None = None
    manual_edit_ancestry: tuple[str, ...] = ()
    quality_flags: tuple[str, ...] = ()
    raster: MaskRaster | None = None
    authority_class: str = MASK_AUTHORITY_CLASS
    post_processing_evidence: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        _require_text(self.artifact_id, "artifact_id")
        _asset_id(self.source_image_asset_id, "source_image_asset_id")
        _require_sha256(self.source_digest, "source_digest")
        _positive_int(self.source_width, "source_width")
        _positive_int(self.source_height, "source_height")
        _asset_id(self.mask_asset_id, "mask_asset_id", areas=("working", "derived"))
        _require_sha256(self.mask_digest, "mask_digest")
        _positive_int(self.mask_width, "mask_width")
        _positive_int(self.mask_height, "mask_height")
        if (self.transform.source_width, self.transform.source_height) != (
            self.source_width,
            self.source_height,
        ):
            raise InvalidMaskArtifact("transform source dimensions do not match the source image")
        if (self.transform.model_width, self.transform.model_height) != (
            self.mask_width,
            self.mask_height,
        ):
            raise InvalidMaskArtifact("transform model dimensions do not match the mask")
        _require_text(self.mask_revision, "mask_revision")
        _timestamp(self.created_at)
        _require_text(self.post_processing_version, "post_processing_version")
        if self.confidence is not None and not 0.0 <= _finite(self.confidence, "confidence") <= 1.0:
            raise InvalidMaskArtifact("confidence must be between 0 and 1")
        if self.parent_mask_revision is not None:
            _require_text(self.parent_mask_revision, "parent_mask_revision")
        object.__setattr__(self, "manual_edit_ancestry", tuple(self.manual_edit_ancestry))
        object.__setattr__(self, "quality_flags", tuple(self.quality_flags))
        if self.raster is not None and (self.raster.width, self.raster.height) != (
            self.mask_width,
            self.mask_height,
        ):
            raise InvalidMaskArtifact("raster dimensions do not match the mask artifact")
        if self.post_processing_evidence is not None:
            evidence = _json_value(self.post_processing_evidence, "post_processing_evidence")
            if not isinstance(evidence, dict):
                raise InvalidMaskArtifact("post_processing_evidence must be a mapping")
            object.__setattr__(self, "post_processing_evidence", _freeze_json(evidence))
        if self.authority_class != MASK_AUTHORITY_CLASS:
            raise InvalidMaskArtifact("mask artifacts must remain derived mask authority")

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "contract": SEGMENTATION_CONTRACT_VERSION,
            "artifact_id": self.artifact_id,
            "authority_class": self.authority_class,
            "source": {
                "image_asset_id": self.source_image_asset_id,
                "sha256": self.source_digest,
                "dimensions": {"width": self.source_width, "height": self.source_height},
            },
            "mask": {
                "asset_id": self.mask_asset_id,
                "sha256": self.mask_digest,
                "dimensions": {"width": self.mask_width, "height": self.mask_height},
            },
            "coordinates": self.transform.as_dict(),
            "provenance": self.provenance.as_dict(),
            "prompt": self.prompt.as_dict(),
            "mask_revision": self.mask_revision,
            "created_at": self.created_at,
            "post_processing_version": self.post_processing_version,
            "confidence": self.confidence,
            "parent_mask_revision": self.parent_mask_revision,
            "manual_edit_ancestry": list(self.manual_edit_ancestry),
            "quality_flags": list(self.quality_flags),
        }
        if self.post_processing_evidence is not None:
            result["post_processing_evidence"] = _thaw_json(self.post_processing_evidence)
        return result


@dataclass(frozen=True, slots=True)
class MaskSetRevision:
    project_id: str
    revision_id: str
    source_revision: str
    masks: tuple[MaskArtifact, ...]
    created_at: str
    parent_revision_id: str | None = None
    revision_digest: str = ""

    def __post_init__(self) -> None:
        _require_text(self.project_id, "project_id")
        _require_text(self.revision_id, "revision_id")
        _require_text(self.source_revision, "source_revision")
        _timestamp(self.created_at)
        masks = tuple(self.masks)
        if len({mask.artifact_id for mask in masks}) != len(masks):
            raise SegmentationContractError("mask artifact IDs must be unique within a revision")
        if self.parent_revision_id is not None:
            _require_text(self.parent_revision_id, "parent_revision_id")
        object.__setattr__(self, "masks", masks)
        expected = _digest(
            {
                "project_id": self.project_id,
                "revision_id": self.revision_id,
                "source_revision": self.source_revision,
                "masks": [mask.as_dict() for mask in masks],
                "parent_revision_id": self.parent_revision_id,
            }
        )
        if self.revision_digest and self.revision_digest != expected:
            raise SegmentationContractError("revision_digest does not match revision content")
        object.__setattr__(self, "revision_digest", expected)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": SEGMENTATION_CONTRACT_VERSION,
            "project_id": self.project_id,
            "revision_id": self.revision_id,
            "source_revision": self.source_revision,
            "created_at": self.created_at,
            "parent_revision_id": self.parent_revision_id,
            "revision_digest": self.revision_digest,
            "masks": [mask.as_dict() for mask in self.masks],
        }


@dataclass(frozen=True, slots=True)
class SegmentationResult:
    request: SegmentationRequest
    status: SegmentationStatus
    provenance: SegmentationProvenance
    masks: tuple[MaskArtifact, ...] = ()
    warnings: tuple[str, ...] = ()
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        masks = tuple(self.masks)
        object.__setattr__(self, "masks", masks)
        object.__setattr__(self, "warnings", tuple(self.warnings))
        if self.status is SegmentationStatus.SUCCEEDED and not masks:
            raise SegmentationContractError("successful segmentation must return at least one mask")
        if self.status is not SegmentationStatus.SUCCEEDED and masks:
            raise SegmentationContractError(
                "failed or unavailable segmentation cannot return masks"
            )
        if self.status is not SegmentationStatus.SUCCEEDED and not self.failure_reason:
            raise SegmentationContractError("failed or unavailable segmentation needs a reason")
        for mask in masks:
            if (
                mask.source_image_asset_id != self.request.source_image_asset_id
                or mask.source_digest != self.request.source_digest
            ):
                raise SegmentationContractError("mask source does not match the request")

    def as_dict(self) -> dict[str, object]:
        return {
            "request": self.request.as_dict(),
            "status": self.status.value,
            "provenance": self.provenance.as_dict(),
            "masks": [mask.as_dict() for mask in self.masks],
            "warnings": list(self.warnings),
            "failure_reason": self.failure_reason,
        }


@runtime_checkable
class SegmentationBackend(Protocol):
    def probe(self) -> SegmentationCapabilityReport: ...

    def segment(self, request: SegmentationRequest) -> SegmentationResult: ...

    def batch_segment(
        self, requests: Sequence[SegmentationRequest]
    ) -> tuple[SegmentationResult, ...]: ...

    def provenance(self) -> SegmentationProvenance: ...
