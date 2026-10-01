"""Deterministic, pixel-domain manual mask revisions."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .segmentation import InvalidMaskArtifact, MaskArtifact, MaskRaster

MANUAL_MASK_CORRECTION_PIPELINE = "packlab.manual-mask-correction"
MANUAL_MASK_CORRECTION_VERSION = "1.0.0"
_EDITOR_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class ManualMaskCorrectionError(ValueError):
    """Raised when an edit cannot produce a valid manual mask revision."""


class ManualMaskEditAction(StrEnum):
    PAINT = "paint-foreground"
    ERASE = "erase-background"


@dataclass(frozen=True, slots=True)
class ManualMaskEdit:
    """Set one zero-based mask-grid pixel to foreground or background."""

    x: int
    y: int
    action: ManualMaskEditAction

    def __post_init__(self) -> None:
        if not isinstance(self.x, int) or isinstance(self.x, bool):
            raise ManualMaskCorrectionError("x must be an integer pixel coordinate")
        if not isinstance(self.y, int) or isinstance(self.y, bool):
            raise ManualMaskCorrectionError("y must be an integer pixel coordinate")
        try:
            action = ManualMaskEditAction(self.action)
        except (ValueError, TypeError) as error:
            raise ManualMaskCorrectionError("unsupported manual mask edit action") from error
        object.__setattr__(self, "action", action)

    def as_dict(self) -> dict[str, object]:
        return {"x": self.x, "y": self.y, "action": self.action.value}


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _editor_id(value: str) -> str:
    if not isinstance(value, str) or not _EDITOR_ID.fullmatch(value):
        raise ManualMaskCorrectionError(
            "editor_id must be an explicit safe label (1-128 ASCII letters, digits, . _ : -)"
        )
    return value


def _timestamp(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManualMaskCorrectionError("created_at must be explicit timezone-aware ISO-8601 text")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ManualMaskCorrectionError("created_at must be ISO-8601") from error
    if parsed.tzinfo is None:
        raise ManualMaskCorrectionError("created_at must include a timezone")
    return value


class ManualMaskCorrectionService:
    """Create immutable child artifacts; this service has no UI dependency."""

    def correct(
        self,
        parent: MaskArtifact,
        *,
        editor_id: str,
        operations: Sequence[ManualMaskEdit],
        created_at: str,
        pipeline_version: str = MANUAL_MASK_CORRECTION_VERSION,
    ) -> MaskArtifact:
        editor = _editor_id(editor_id)
        timestamp = _timestamp(created_at)
        if not isinstance(pipeline_version, str) or not pipeline_version.strip():
            raise ManualMaskCorrectionError("pipeline_version must be non-empty text")
        if isinstance(operations, (str, bytes, bytearray)) or not isinstance(operations, Sequence):
            raise ManualMaskCorrectionError("operations must be a bounded sequence of edits")
        if not operations:
            raise ManualMaskCorrectionError("at least one edit operation is required")

        # Verify before copying, indexing, or otherwise consuming the parent raster values.
        raster = parent.raster
        if raster is None:
            raise InvalidMaskArtifact("manual correction requires an in-memory parent raster")
        if raster.digest != parent.mask_digest:
            raise InvalidMaskArtifact(
                "parent raster digest does not match the declared mask digest"
            )

        edits = tuple(operations)
        if len(edits) > raster.width * raster.height * 16:
            raise ManualMaskCorrectionError("operation sequence exceeds the bounded edit limit")
        values = list(raster.values)
        for edit in edits:
            if not isinstance(edit, ManualMaskEdit):
                raise ManualMaskCorrectionError("every operation must be a ManualMaskEdit")
            if not (0 <= edit.x < raster.width and 0 <= edit.y < raster.height):
                raise ManualMaskCorrectionError("manual mask edit coordinate is out of bounds")
            values[edit.y * raster.width + edit.x] = edit.action is ManualMaskEditAction.PAINT

        corrected_raster = MaskRaster(raster.width, raster.height, tuple(values))
        if corrected_raster.values == raster.values:
            raise ManualMaskCorrectionError("submitted manual mask edits are a canonical no-op")

        normalized_operations = [edit.as_dict() for edit in edits]
        identity_inputs: dict[str, object] = {
            "parent_artifact_id": parent.artifact_id,
            "parent_revision": parent.mask_revision,
            "parent_digest": parent.mask_digest,
            "source_image_asset_id": parent.source_image_asset_id,
            "source_digest": parent.source_digest,
            "source_dimensions": {"width": parent.source_width, "height": parent.source_height},
            "transform": parent.transform.as_dict(),
            "pipeline_id": MANUAL_MASK_CORRECTION_PIPELINE,
            "pipeline_version": pipeline_version,
            "editor_id": editor,
            "operations": normalized_operations,
            "output_mask_digest": corrected_raster.digest,
        }
        revision_digest = _digest(identity_inputs)
        revision = f"manual:{revision_digest}"
        ancestry_entry = f"{revision}|parent={parent.mask_revision}|editor={editor}"
        evidence: dict[str, object] = {
            "pipeline_id": MANUAL_MASK_CORRECTION_PIPELINE,
            "pipeline_version": pipeline_version,
            "editor_id": editor,
            "parent_artifact_id": parent.artifact_id,
            "parent_revision": parent.mask_revision,
            "parent_digest": parent.mask_digest,
            "revision_identity_sha256": revision_digest,
            "operations": normalized_operations,
        }
        return MaskArtifact(
            artifact_id=f"manual-mask-{revision_digest}",
            source_image_asset_id=parent.source_image_asset_id,
            source_digest=parent.source_digest,
            source_width=parent.source_width,
            source_height=parent.source_height,
            mask_asset_id=f"working/masks/manual/{revision_digest}/mask.mask",
            mask_digest=corrected_raster.digest,
            mask_width=parent.mask_width,
            mask_height=parent.mask_height,
            transform=parent.transform,
            provenance=parent.provenance,
            prompt=parent.prompt,
            mask_revision=revision,
            created_at=timestamp,
            post_processing_version=parent.post_processing_version,
            confidence=parent.confidence,
            parent_mask_revision=parent.mask_revision,
            manual_edit_ancestry=parent.manual_edit_ancestry + (ancestry_entry,),
            quality_flags=parent.quality_flags,
            raster=corrected_raster,
            authority_class=parent.authority_class,
            post_processing_evidence=parent.post_processing_evidence,
            manual_edit_evidence=evidence,
        )
