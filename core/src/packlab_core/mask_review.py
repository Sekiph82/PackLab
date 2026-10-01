"""Deterministic, source-free visual review artifacts for published mask sets."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import zlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from .segmentation import MaskArtifact, MaskSetRevision, SegmentationContractError

MASK_REVIEW_VERSION: Final = "packlab.mask-review.v1"
OVERLAY_COLOR: Final = (0, 210, 255)
OVERLAY_ALPHA: Final = 144
OVERLAY_MAX_DIMENSION: Final = 16_384
OVERLAY_MAX_TOTAL_PIXELS: Final = 50_000_000
MAX_REVIEW_MASKS: Final = 64
CONTACT_CELL_SIZE: Final = 128
CONTACT_INSET: Final = 8
CONTACT_MAX_COLUMNS: Final = 4


class MaskReviewError(ValueError):
    """Raised when a published revision cannot produce a safe review bundle."""


@dataclass(frozen=True, slots=True)
class MaskReviewBundle:
    """In-memory derived review evidence; it carries no source image pixels."""

    overlays: tuple[tuple[str, bytes], ...]
    contact_sheet_png: bytes
    manifest_json: bytes
    manifest_sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _chunk(kind: bytes, data: bytes) -> bytes:
    payload = kind + data
    return (
        struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
    )


def _encode_rgba_png(width: int, height: int, rows: Iterable[bytes]) -> bytes:
    """Encode RGBA scanlines using only the Python standard library."""
    compressor = zlib.compressobj(level=9)
    compressed_parts: list[bytes] = []
    for row in rows:
        if len(row) != width * 4:
            raise MaskReviewError("PNG row length does not match its dimensions")
        compressed_parts.append(compressor.compress(b"\x00" + row))
    compressed_parts.append(compressor.flush())
    return b"\x89PNG\r\n\x1a\n" + b"".join(
        (
            _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)),
            _chunk(b"IDAT", b"".join(compressed_parts)),
            _chunk(b"IEND", b""),
        )
    )


def _mask_sample(mask: MaskArtifact, source_x: int, source_y: int) -> bool:
    raster = mask.raster
    if raster is None:
        raise MaskReviewError(f"mask {mask.artifact_id!r} has no in-memory raster")
    model_x, model_y = mask.transform.source_to_model(source_x, source_y)
    pixel_x = math.floor(model_x + 0.5)
    pixel_y = math.floor(model_y + 0.5)
    if not (0 <= pixel_x < raster.width and 0 <= pixel_y < raster.height):
        return False
    return raster.sample(pixel_x, pixel_y)


def _overlay(mask: MaskArtifact) -> bytes:
    def rows() -> Iterable[bytes]:
        for y in range(mask.source_height):
            row = bytearray(mask.source_width * 4)
            for x in range(mask.source_width):
                if _mask_sample(mask, x, y):
                    offset = x * 4
                    row[offset : offset + 4] = bytes((*OVERLAY_COLOR, OVERLAY_ALPHA))
            yield bytes(row)

    return _encode_rgba_png(mask.source_width, mask.source_height, rows())


def _contact_sheet(masks: tuple[MaskArtifact, ...]) -> bytes:
    columns = min(CONTACT_MAX_COLUMNS, len(masks))
    rows_count = math.ceil(len(masks) / columns)
    width = columns * CONTACT_CELL_SIZE
    height = rows_count * CONTACT_CELL_SIZE
    rows: list[bytes] = []
    for sheet_y in range(height):
        row = bytearray(width * 4)
        cell_y = sheet_y // CONTACT_CELL_SIZE
        local_y = sheet_y % CONTACT_CELL_SIZE
        for cell_x in range(columns):
            index = cell_y * columns + cell_x
            if (
                index >= len(masks)
                or not CONTACT_INSET <= local_y < CONTACT_CELL_SIZE - CONTACT_INSET
            ):
                continue
            mask = masks[index]
            target_w = CONTACT_CELL_SIZE - 2 * CONTACT_INSET
            target_h = target_w
            scale = min(target_w / mask.source_width, target_h / mask.source_height)
            thumb_w = max(1, round(mask.source_width * scale))
            thumb_h = max(1, round(mask.source_height * scale))
            top = (CONTACT_CELL_SIZE - thumb_h) // 2
            if not top <= local_y < top + thumb_h:
                continue
            source_y = min(
                mask.source_height - 1, int((local_y - top) * mask.source_height / thumb_h)
            )
            left = (CONTACT_CELL_SIZE - thumb_w) // 2
            for local_x in range(left, left + thumb_w):
                source_x = min(
                    mask.source_width - 1, int((local_x - left) * mask.source_width / thumb_w)
                )
                if _mask_sample(mask, source_x, source_y):
                    offset = (cell_x * CONTACT_CELL_SIZE + local_x) * 4
                    row[offset : offset + 4] = bytes((*OVERLAY_COLOR, OVERLAY_ALPHA))
        rows.append(bytes(row))
    return _encode_rgba_png(width, height, rows)


def build_mask_review_bundle(revision: MaskSetRevision) -> MaskReviewBundle:
    """Render deterministic mask-only overlays and a bounded contact sheet.

    Output sizes are capped before allocating pixels. Raster digests are checked
    against declared mask digests before any output is produced. No source image
    bytes, prompt text, backend details, or timestamps enter this bundle.
    """
    if not isinstance(revision, MaskSetRevision):
        raise MaskReviewError("a published MaskSetRevision is required")
    masks = tuple(sorted(revision.masks, key=lambda item: (item.artifact_id, item.mask_revision)))
    if not masks:
        raise MaskReviewError("mask review requires at least one mask")
    if len(masks) > MAX_REVIEW_MASKS:
        raise MaskReviewError(f"mask review is limited to {MAX_REVIEW_MASKS} masks")
    if len({mask.artifact_id for mask in masks}) != len(masks):
        raise MaskReviewError("mask review contains ambiguous duplicate artifact IDs")
    if len({mask.mask_revision for mask in masks}) != len(masks):
        raise MaskReviewError("mask review contains ambiguous duplicate mask revisions")
    total_pixels = 0
    for mask in masks:
        if mask.raster is None:
            raise MaskReviewError(f"mask {mask.artifact_id!r} has no in-memory raster")
        if mask.raster.digest != mask.mask_digest:
            raise MaskReviewError(f"mask {mask.artifact_id!r} raster digest does not match")
        if (mask.raster.width, mask.raster.height) != (mask.mask_width, mask.mask_height):
            raise MaskReviewError(f"mask {mask.artifact_id!r} raster dimensions do not match")
        if max(mask.source_width, mask.source_height) > OVERLAY_MAX_DIMENSION:
            raise MaskReviewError(f"mask {mask.artifact_id!r} source dimensions exceed the limit")
        total_pixels += mask.source_width * mask.source_height
    if total_pixels > OVERLAY_MAX_TOTAL_PIXELS:
        raise MaskReviewError("mask review source pixel total exceeds the limit")

    overlays = tuple((mask.artifact_id, _overlay(mask)) for mask in masks)
    contact = _contact_sheet(masks)
    entries: list[dict[str, object]] = []
    for mask, (_, overlay_png) in zip(masks, overlays, strict=True):
        entries.append(
            {
                "artifact_id": mask.artifact_id,
                "mask_revision": mask.mask_revision,
                "parent_mask_revision": mask.parent_mask_revision,
                "manual_edit_ancestry_count": len(mask.manual_edit_ancestry),
                "source_asset_id": mask.source_image_asset_id,
                "source_sha256": mask.source_digest,
                "source_dimensions": {"width": mask.source_width, "height": mask.source_height},
                "mask_asset_id": mask.mask_asset_id,
                "mask_sha256": mask.mask_digest,
                "mask_dimensions": {"width": mask.mask_width, "height": mask.mask_height},
                "coordinate_transform": mask.transform.as_dict(),
                "confidence": mask.confidence,
                "has_quality_flags": bool(mask.quality_flags),
                "quality_flag_count": len(mask.quality_flags),
                "overlay": {
                    "sha256": _sha256(overlay_png),
                    "width": mask.source_width,
                    "height": mask.source_height,
                },
            }
        )
    manifest: dict[str, object] = {
        "schema": MASK_REVIEW_VERSION,
        "project_id": revision.project_id,
        "source_revision": revision.source_revision,
        "mask_set_revision_id": revision.revision_id,
        "mask_set_revision_sha256": revision.revision_digest,
        "rendering": {
            "format": "png_rgba_8bit",
            "pixel_origin": "top_left_pixel_center",
            "sampling": "source_to_model_nearest_pixel_center",
            "background_rgba": [0, 0, 0, 0],
            "foreground_rgba": [*OVERLAY_COLOR, OVERLAY_ALPHA],
            "source_pixels_included": False,
        },
        "masks": entries,
        "contact_sheet": {
            "sha256": _sha256(contact),
            "width": min(CONTACT_MAX_COLUMNS, len(masks)) * CONTACT_CELL_SIZE,
            "height": math.ceil(len(masks) / CONTACT_MAX_COLUMNS) * CONTACT_CELL_SIZE,
            "cell_size": CONTACT_CELL_SIZE,
            "tile_order": [mask.artifact_id for mask in masks],
        },
    }
    try:
        manifest_json = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise SegmentationContractError("mask review manifest is not deterministic JSON") from error
    return MaskReviewBundle(overlays, contact, manifest_json, _sha256(manifest_json))
