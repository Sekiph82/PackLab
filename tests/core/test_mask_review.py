from __future__ import annotations

import hashlib
import json
import struct
import zlib
from dataclasses import replace

import pytest

from packlab_core.mask_review import (
    OVERLAY_ALPHA,
    OVERLAY_COLOR,
    MaskReviewError,
    build_mask_review_bundle,
)
from packlab_core.mask_revisions import MaskRevisionService
from packlab_core.segmentation import (
    CoordinateTransform,
    MaskArtifact,
    MaskRaster,
    MaskSetRevision,
    PromptEvidence,
    PromptKind,
    SegmentationProvenance,
)

CREATED_AT = "2026-10-02T00:00:00Z"


def _mask(artifact_id: str, values: tuple[bool, ...], *, source_width: int = 2) -> MaskArtifact:
    raster = MaskRaster(2, 1, values)
    return MaskArtifact(
        artifact_id=artifact_id,
        source_image_asset_id=f"raw/images/{artifact_id}.png",
        source_digest=hashlib.sha256(b"synthetic-source-bytes-not-provided").hexdigest(),
        source_width=source_width,
        source_height=1,
        mask_asset_id=f"working/masks/{artifact_id}.mask",
        mask_digest=raster.digest,
        mask_width=2,
        mask_height=1,
        transform=CoordinateTransform(source_width, 1, 2, 1, 2 / source_width, 1),
        provenance=SegmentationProvenance(
            "fixture-backend",
            "1",
            "fixture-model",
            "1",
            "fixture-checkpoint",
            hashlib.sha256(b"fixture-checkpoint").hexdigest(),
            "fixture-runtime",
            "1",
            "tests/fixtures/licenses/fixture.txt",
        ),
        prompt=PromptEvidence(PromptKind.POINT, {"sensitive_prompt_text": "must-not-leak"}),
        mask_revision=f"revision-{artifact_id}",
        created_at=CREATED_AT,
        post_processing_version="fixture-v1",
        confidence=0.75,
        quality_flags=("raw_model_output",),
        raster=raster,
    )


def _revision(masks: tuple[MaskArtifact, ...]):
    return MaskRevisionService().publish_initial(
        project_id="project-fixture",
        source_revision="capture-fixture-r1",
        masks=masks,
        created_at=CREATED_AT,
    )


def _decode_png(data: bytes) -> tuple[int, int, bytes]:
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    offset = 8
    compressed = bytearray()
    width = height = 0
    while offset < len(data):
        size = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + size]
        if kind == b"IHDR":
            width, height, depth, color, *_ = struct.unpack(">IIBBBBB", payload)
            assert (depth, color) == (8, 6)
        elif kind == b"IDAT":
            compressed.extend(payload)
        offset += size + 12
        if kind == b"IEND":
            break
    decoded = zlib.decompress(compressed)
    stride = width * 4
    rows = []
    for y in range(height):
        start = y * (stride + 1)
        assert decoded[start] == 0
        rows.append(decoded[start + 1 : start + 1 + stride])
    return width, height, b"".join(rows)


def test_overlay_has_source_geometry_and_fixed_rgba_with_transform_sampling() -> None:
    bundle = build_mask_review_bundle(
        _revision((_mask("object-a", (False, True), source_width=4),))
    )
    artifact_id, png = bundle.overlays[0]
    width, height, pixels = _decode_png(png)
    assert artifact_id == "object-a"
    assert (width, height) == (4, 1)
    assert [pixels[index : index + 4] for index in range(0, len(pixels), 4)] == [
        bytes((0, 0, 0, 0)),
        bytes((*OVERLAY_COLOR, OVERLAY_ALPHA)),
        bytes((*OVERLAY_COLOR, OVERLAY_ALPHA)),
        bytes((0, 0, 0, 0)),
    ]


def test_manifest_and_png_outputs_are_canonical_and_omit_private_prompt_text() -> None:
    masks = (_mask("object-b", (True, False)), _mask("object-a", (False, True)))
    first = build_mask_review_bundle(_revision(masks))
    second = build_mask_review_bundle(_revision(tuple(reversed(masks))))
    assert first == second
    manifest = json.loads(first.manifest_json)
    assert [entry["artifact_id"] for entry in manifest["masks"]] == ["object-a", "object-b"]
    assert "must-not-leak" not in first.manifest_json.decode()
    assert hashlib.sha256(first.manifest_json).hexdigest() == first.manifest_sha256
    contact_width, contact_height, _ = _decode_png(first.contact_sheet_png)
    assert (contact_width, contact_height) == (256, 128)
    assert manifest["contact_sheet"]["tile_order"] == ["object-a", "object-b"]


def test_revision_identity_and_confidence_are_linked_without_authority_change() -> None:
    mask = _mask("object-a", (True, False))
    revision = _revision((mask,))
    manifest = json.loads(build_mask_review_bundle(revision).manifest_json)
    assert manifest["mask_set_revision_id"] == revision.revision_id
    assert manifest["mask_set_revision_sha256"] == revision.revision_digest
    assert manifest["masks"][0]["mask_revision"] == mask.mask_revision
    assert manifest["masks"][0]["confidence"] == 0.75
    assert manifest["rendering"]["source_pixels_included"] is False
    assert mask.authority_class == "DERIVED_MASK"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda mask: replace(mask, raster=None), "no in-memory raster"),
        (lambda mask: replace(mask, raster=MaskRaster(2, 1, (False, False))), "digest"),
    ],
)
def test_review_fails_closed_for_missing_or_ambiguous_raster(mutation, message: str) -> None:
    mask = _mask("object-a", (True, False))
    with pytest.raises(MaskReviewError, match=message):
        build_mask_review_bundle(_revision((mutation(mask),)))


def test_review_rejects_empty_revision() -> None:
    revision = MaskSetRevision(
        project_id="project-fixture",
        revision_id="empty-revision",
        source_revision="capture-fixture-r1",
        masks=(),
        created_at=CREATED_AT,
    )
    with pytest.raises(MaskReviewError, match="at least one mask"):
        build_mask_review_bundle(revision)


def test_review_rejects_source_dimension_over_output_bound() -> None:
    mask = _mask("object-a", (False, False))
    oversized = replace(
        mask,
        source_width=16_385,
        transform=CoordinateTransform(16_385, 1, 2, 1, 2 / 16_385, 1),
    )
    with pytest.raises(MaskReviewError, match="dimensions exceed the limit"):
        build_mask_review_bundle(_revision((oversized,)))
