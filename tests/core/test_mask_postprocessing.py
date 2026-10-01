from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

import packlab_core.mask_postprocessing as mask_postprocessing
from packlab_core.mask_postprocessing import (
    MASK_POSTPROCESSING_PIPELINE_VERSION,
    MaskPostProcessingError,
    MaskPostProcessingParameters,
    post_process_mask,
)
from packlab_core.segmentation import (
    CoordinateTransform,
    InvalidMaskArtifact,
    MaskArtifact,
    MaskRaster,
    PromptEvidence,
    PromptKind,
    SegmentationProvenance,
)

SOURCE_BYTES = b"public synthetic source image bytes"
SOURCE_DIGEST = hashlib.sha256(SOURCE_BYTES).hexdigest()
CREATED_AT = datetime(2026, 10, 1, tzinfo=UTC).isoformat().replace("+00:00", "Z")


def _parent(values: tuple[bool, ...], width: int, height: int) -> MaskArtifact:
    raster = MaskRaster(width, height, values)
    return MaskArtifact(
        artifact_id="raw-mask-1",
        source_image_asset_id="raw/images/synthetic.png",
        source_digest=SOURCE_DIGEST,
        source_width=width,
        source_height=height,
        mask_asset_id="working/masks/raw/rev-1.mask",
        mask_digest=raster.digest,
        mask_width=width,
        mask_height=height,
        transform=CoordinateTransform(width, height, width, height),
        provenance=SegmentationProvenance(
            "fixture-backend",
            "1.0",
            "fixture-model",
            "1.0",
            "fixture-checkpoint",
            hashlib.sha256(b"fixture-checkpoint").hexdigest(),
            "fixture-runtime",
            "1.0",
            "tests/fixtures/licenses/fixture.txt",
        ),
        prompt=PromptEvidence(PromptKind.AUTOMATIC),
        mask_revision="raw-revision-1",
        created_at=CREATED_AT,
        post_processing_version="none:raw-model-output",
        raster=raster,
    )


def _grid(rows: tuple[str, ...]) -> tuple[bool, ...]:
    return tuple(character == "#" for row in rows for character in row)


def test_same_parent_and_parameters_have_stable_identity_and_digest() -> None:
    parent = _parent(_grid((".......", ".#####.", ".#...#.", ".#####.", ".......")), 7, 5)
    assert parent.raster is not None and parent.raster.digest == parent.mask_digest
    params = MaskPostProcessingParameters(max_hole_area=1)

    first = post_process_mask(parent, params).child
    second = post_process_mask(parent, params).child

    assert first.mask_digest == second.mask_digest
    assert first.mask_revision == second.mask_revision
    assert first.artifact_id == second.artifact_id
    assert first.mask_asset_id == second.mask_asset_id
    assert first.post_processing_version.endswith(MASK_POSTPROCESSING_PIPELINE_VERSION)
    assert first.raster is not None and first.raster.digest == first.mask_digest
    next_revision = post_process_mask(first, params).child
    assert next_revision.parent_mask_revision == first.mask_revision
    assert (
        next_revision.raster is not None
        and next_revision.raster.digest == next_revision.mask_digest
    )


def test_parent_raster_digest_mismatch_fails_before_processing_or_child_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = _parent(_grid((".....", ".###.", ".###.", ".....")), 5, 4)
    assert parent.raster is not None
    mismatched = replace(parent, mask_digest=hashlib.sha256(b"different mask bytes").hexdigest())
    parent_before = mismatched.as_dict()
    raster_before = mismatched.raster

    def processing_must_not_start(*_args: object, **_kwargs: object) -> object:
        pytest.fail("mask processing began before parent digest validation")

    monkeypatch.setattr(mask_postprocessing, "_fill_small_holes", processing_must_not_start)
    monkeypatch.setattr(mask_postprocessing, "_canonical_digest", processing_must_not_start)
    with pytest.raises(MaskPostProcessingError, match="raster digest does not match"):
        post_process_mask(mismatched, MaskPostProcessingParameters(max_hole_area=1))

    assert mismatched.as_dict() == parent_before
    assert mismatched.raster is raster_before
    assert "post_processing_evidence" not in mismatched.as_dict()


def test_different_parameters_change_revision_even_if_output_is_equal() -> None:
    parent = _parent(_grid((".....", ".###.", ".###.", ".....")), 5, 4)
    first = post_process_mask(parent, MaskPostProcessingParameters()).child
    second = post_process_mask(
        parent, MaskPostProcessingParameters(fill_single_pixel_notches=True)
    ).child
    assert first.mask_digest == second.mask_digest
    assert first.mask_revision != second.mask_revision
    assert first.post_processing_evidence != second.post_processing_evidence


def test_parent_and_source_bytes_are_unchanged_and_child_records_ancestry(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.png"
    source.write_bytes(SOURCE_BYTES)
    parent = _parent(_grid((".......", ".#####.", ".#...#.", ".#####.", ".......")), 7, 5)
    parent_before = parent.as_dict()
    raster_before = parent.raster

    child = post_process_mask(parent, MaskPostProcessingParameters(max_hole_area=3)).child
    evidence = child.as_dict()["post_processing_evidence"]

    assert parent.as_dict() == parent_before
    assert parent.raster is raster_before
    assert child is not parent
    assert child.parent_mask_revision == parent.mask_revision
    assert evidence["parent_artifact_id"] == parent.artifact_id  # type: ignore[index]
    assert evidence["parent_mask_digest"] == parent.mask_digest  # type: ignore[index]
    assert evidence["source_image_asset_id"] == parent.source_image_asset_id  # type: ignore[index]
    assert evidence["source_digest"] == parent.source_digest  # type: ignore[index]
    assert evidence["source_transform"] == parent.transform.as_dict()  # type: ignore[index]
    assert child.raster is not parent.raster
    assert source.read_bytes() == SOURCE_BYTES
    assert "post_processing_evidence" not in parent.as_dict()
    assert "post_processing_evidence" in child.as_dict()


def test_holes_at_or_below_threshold_fill_but_larger_and_boundary_regions_do_not() -> None:
    # A 1-pixel hole and a 2-pixel hole are enclosed; the open background reaches the edge.
    rows = ("........", ".######.", ".#.#.##.", ".######.", ".##..##.", ".######.", "........")
    parent = _parent(_grid(rows), 8, 7)
    below = post_process_mask(parent, MaskPostProcessingParameters(max_hole_area=0)).child
    at = post_process_mask(parent, MaskPostProcessingParameters(max_hole_area=1)).child
    above = post_process_mask(parent, MaskPostProcessingParameters(max_hole_area=2)).child

    assert below.raster is not None and not below.raster.sample(2, 2)
    assert at.raster is not None and at.raster.sample(2, 2)
    assert at.raster is not None and not at.raster.sample(3, 4)
    assert above.raster is not None and above.raster.sample(3, 4)
    assert above.raster is not None and not above.raster.sample(0, 0)
    assert at.post_processing_evidence["holes_filled"] == 2  # type: ignore[index]
    assert above.post_processing_evidence["holes_filled"] == 3  # type: ignore[index]


def test_component_threshold_and_4_connectivity_are_explicit() -> None:
    # Diagonal foreground pixels are separate; the connected groups have areas 1, 2, and 3.
    parent = _parent(_grid(("#....##", ".#.....", "...#...", "...#...", "...#...")), 7, 5)
    below = post_process_mask(
        parent, MaskPostProcessingParameters(max_component_area_to_remove=0)
    ).child
    at = post_process_mask(
        parent, MaskPostProcessingParameters(max_component_area_to_remove=1)
    ).child
    above = post_process_mask(
        parent, MaskPostProcessingParameters(max_component_area_to_remove=2)
    ).child
    equal = post_process_mask(
        parent, MaskPostProcessingParameters(max_component_area_to_remove=3)
    ).child

    assert below.raster is not None and below.raster.sample(0, 0)
    assert at.raster is not None and not at.raster.sample(0, 0)
    assert at.raster is not None and at.raster.sample(5, 0) and at.raster.sample(6, 0)
    assert above.raster is not None and not above.raster.sample(5, 0)
    assert above.raster is not None and above.raster.sample(3, 3)
    assert equal.raster is not None and not equal.raster.sample(3, 3)
    assert at.post_processing_evidence["connectivity"] == 4  # type: ignore[index]
    assert at.post_processing_evidence["components_removed"] == 2  # type: ignore[index]
    assert above.post_processing_evidence["components_removed"] == 3  # type: ignore[index]


def test_edge_cleanup_fills_only_single_pixel_interior_notch_and_preserves_thin_features() -> None:
    rows = (".......", "...#...", "..#.#..", ".......", ".......")
    parent = _parent(_grid(rows), 7, 5)
    child = post_process_mask(
        parent, MaskPostProcessingParameters(fill_single_pixel_notches=True)
    ).child
    assert child.raster is not None
    assert child.raster.sample(3, 2)

    thin = _parent(_grid((".......", "...#...", "...#...", "...#...", ".......")), 7, 5)
    thin_child = post_process_mask(
        thin, MaskPostProcessingParameters(fill_single_pixel_notches=True)
    ).child
    assert thin_child.raster is not None
    assert [thin_child.raster.sample(3, y) for y in range(1, 4)] == [True, True, True]
    assert thin_child.raster.values == thin.raster.values


def test_edge_touching_object_is_preserved_by_edge_cleanup() -> None:
    parent = _parent(_grid(("##...", "##...", ".....", ".....")), 5, 4)
    child = post_process_mask(
        parent, MaskPostProcessingParameters(fill_single_pixel_notches=True)
    ).child
    assert child.raster is not None and parent.raster is not None
    assert child.raster.values == parent.raster.values


@pytest.mark.parametrize(
    "rows",
    [
        (".....",) * 5,
        ("#####",) * 5,
    ],
)
def test_empty_and_full_masks_are_stable(rows: tuple[str, ...]) -> None:
    parent = _parent(_grid(rows), 5, 5)
    child = post_process_mask(
        parent,
        MaskPostProcessingParameters(
            max_hole_area=1,
            max_component_area_to_remove=1,
            fill_single_pixel_notches=True,
        ),
    ).child
    assert child.raster is not None and parent.raster is not None
    assert child.raster.values == parent.raster.values


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_hole_area": -1},
        {"max_hole_area": True},
        {"max_hole_area": float("nan")},
        {"max_component_area_to_remove": 1_000_001},
        {"fill_single_pixel_notches": 1},
    ],
)
def test_invalid_parameters_fail_closed(kwargs: dict[str, object]) -> None:
    with pytest.raises(MaskPostProcessingError):
        MaskPostProcessingParameters(**kwargs)  # type: ignore[arg-type]


def test_dimension_incompatible_parameter_and_missing_raster_fail_closed() -> None:
    parent = _parent(_grid(("...", "...")), 3, 2)
    with pytest.raises(MaskPostProcessingError, match="exceeds parent mask dimensions"):
        post_process_mask(parent, MaskPostProcessingParameters(max_hole_area=7))

    no_raster = MaskArtifact(
        artifact_id=parent.artifact_id,
        source_image_asset_id=parent.source_image_asset_id,
        source_digest=parent.source_digest,
        source_width=parent.source_width,
        source_height=parent.source_height,
        mask_asset_id=parent.mask_asset_id,
        mask_digest=parent.mask_digest,
        mask_width=parent.mask_width,
        mask_height=parent.mask_height,
        transform=parent.transform,
        provenance=parent.provenance,
        prompt=parent.prompt,
        mask_revision=parent.mask_revision,
        created_at=parent.created_at,
        post_processing_version=parent.post_processing_version,
    )
    with pytest.raises(MaskPostProcessingError, match="raster is required"):
        post_process_mask(no_raster, MaskPostProcessingParameters())


def test_invalid_transform_dimensions_are_rejected_by_parent_contract() -> None:
    parent = _parent(_grid(("...", "...")), 3, 2)
    with pytest.raises(InvalidMaskArtifact, match="transform model dimensions"):
        MaskArtifact(
            artifact_id=parent.artifact_id,
            source_image_asset_id=parent.source_image_asset_id,
            source_digest=parent.source_digest,
            source_width=parent.source_width,
            source_height=parent.source_height,
            mask_asset_id=parent.mask_asset_id,
            mask_digest=parent.mask_digest,
            mask_width=parent.mask_width,
            mask_height=parent.mask_height,
            transform=CoordinateTransform(3, 2, 2, 2),
            provenance=parent.provenance,
            prompt=parent.prompt,
            mask_revision=parent.mask_revision,
            created_at=parent.created_at,
            post_processing_version=parent.post_processing_version,
        )
