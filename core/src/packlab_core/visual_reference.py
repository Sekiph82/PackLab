"""Non-authoritative records for optional AI visual references.

This module defines provenance and UI/export metadata only. It has no model
SDK, geometry sampling, measurement, calibration, or Scan Master integration.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

AI_VISUAL_REFERENCE_AUTHORITY = "AI_VISUAL_REFERENCE"
AI_VISUAL_REFERENCE_CAVEAT = "Unseen geometry may be invented by the generator."
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.ASCII)


class VisualReferenceError(ValueError):
    """Raised when visual-reference identity or provenance is incomplete."""


@dataclass(frozen=True, slots=True)
class ConditioningInput:
    """Content identity for an input image and optional mask, not the private bytes."""

    image_sha256: str
    mask_sha256: str | None = None

    def __post_init__(self) -> None:
        if not _valid_digest(self.image_sha256):
            raise VisualReferenceError("conditioning_image_sha256_invalid")
        if self.mask_sha256 is not None and not _valid_digest(self.mask_sha256):
            raise VisualReferenceError("conditioning_mask_sha256_invalid")

    def as_dict(self) -> dict[str, str | None]:
        return {"image_sha256": self.image_sha256, "mask_sha256": self.mask_sha256}


@dataclass(frozen=True, slots=True)
class VisualReferenceProvenance:
    generator: str
    model: str
    checkpoint: str
    version: str
    conditioning: tuple[ConditioningInput, ...]
    seed: int
    settings_json: str
    checkpoint_sha256: str | None = None

    def __post_init__(self) -> None:
        for name in ("generator", "model", "checkpoint", "version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise VisualReferenceError(f"{name}_required")
        if not isinstance(self.conditioning, tuple) or not self.conditioning:
            raise VisualReferenceError("conditioning_inputs_required")
        if any(not isinstance(item, ConditioningInput) for item in self.conditioning):
            raise VisualReferenceError("conditioning_input_invalid")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise VisualReferenceError("seed_must_be_nonnegative_integer")
        try:
            settings = json.loads(self.settings_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise VisualReferenceError("settings_json_invalid") from exc
        if not isinstance(settings, dict) or _canonical_json(settings) != self.settings_json:
            raise VisualReferenceError("settings_json_must_be_canonical_object")
        if self.checkpoint_sha256 is not None and not _valid_digest(self.checkpoint_sha256):
            raise VisualReferenceError("checkpoint_sha256_invalid")

    @classmethod
    def create(
        cls,
        *,
        generator: str,
        model: str,
        checkpoint: str,
        version: str,
        conditioning: tuple[ConditioningInput, ...],
        seed: int,
        settings: Mapping[str, object],
        checkpoint_sha256: str | None = None,
    ) -> VisualReferenceProvenance:
        if not isinstance(settings, Mapping):
            raise VisualReferenceError("settings_must_be_mapping")
        return cls(
            generator=generator,
            model=model,
            checkpoint=checkpoint,
            version=version,
            conditioning=conditioning,
            seed=seed,
            settings_json=_canonical_json(dict(settings)),
            checkpoint_sha256=checkpoint_sha256,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "generator": self.generator,
            "model": self.model,
            "checkpoint": self.checkpoint,
            "checkpoint_sha256": self.checkpoint_sha256,
            "version": self.version,
            "conditioning": [item.as_dict() for item in self.conditioning],
            "seed": self.seed,
            "settings": json.loads(self.settings_json),
        }


@dataclass(frozen=True, slots=True)
class VisualReferenceRecord:
    """Display-only reference handle; deliberately contains no geometry samples."""

    reference_id: str
    artifact_sha256: str
    provenance: VisualReferenceProvenance
    visible: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.reference_id, str) or not self.reference_id.strip():
            raise VisualReferenceError("reference_id_required")
        if not _valid_digest(self.artifact_sha256):
            raise VisualReferenceError("artifact_sha256_invalid")
        if not isinstance(self.provenance, VisualReferenceProvenance):
            raise VisualReferenceError("provenance_required")
        if not isinstance(self.visible, bool):
            raise VisualReferenceError("visible_must_be_boolean")

    @property
    def authority_class(self) -> str:
        return AI_VISUAL_REFERENCE_AUTHORITY

    @property
    def generated(self) -> bool:
        return True

    @property
    def caveat(self) -> str:
        return AI_VISUAL_REFERENCE_CAVEAT

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.ai-visual-reference.v1",
            "reference_id": self.reference_id,
            "artifact_sha256": self.artifact_sha256,
            "authority_class": self.authority_class,
            "generated": self.generated,
            "caveat": self.caveat,
            "visible": self.visible,
            "provenance": self.provenance.as_dict(),
        }


class VisualReferenceBackend(Protocol):
    """Replaceable adapter boundary; model SDK objects must not escape it."""

    def generate(self, request: VisualReferenceRequest) -> VisualReferenceRecord:
        """Generate an isolated visual reference from content-addressed inputs."""


@dataclass(frozen=True, slots=True)
class VisualReferenceRequest:
    conditioning: tuple[ConditioningInput, ...]
    seed: int
    settings_json: str

    def __post_init__(self) -> None:
        if not isinstance(self.conditioning, tuple) or not self.conditioning:
            raise VisualReferenceError("conditioning_inputs_required")
        if any(not isinstance(item, ConditioningInput) for item in self.conditioning):
            raise VisualReferenceError("conditioning_input_invalid")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise VisualReferenceError("seed_must_be_nonnegative_integer")
        try:
            settings = json.loads(self.settings_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise VisualReferenceError("settings_json_invalid") from exc
        if not isinstance(settings, dict) or _canonical_json(settings) != self.settings_json:
            raise VisualReferenceError("settings_json_must_be_canonical_object")


def reject_visual_reference_promotion(_record: VisualReferenceRecord) -> None:
    """Fail closed at any attempted promotion to measured/authoritative geometry."""

    if not isinstance(_record, VisualReferenceRecord):
        raise VisualReferenceError("visual_reference_record_required")
    raise VisualReferenceError("ai_visual_reference_cannot_be_promoted")


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise VisualReferenceError("settings_not_json_safe") from exc


def _valid_digest(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def content_sha256(content: bytes) -> str:
    """Return a stable digest without retaining or exposing content bytes."""

    if not isinstance(content, bytes):
        raise VisualReferenceError("content_must_be_bytes")
    return hashlib.sha256(content).hexdigest()
