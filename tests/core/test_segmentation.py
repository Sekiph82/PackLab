from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from packlab_core.segmentation import (
    PIXEL_ORIGIN_TOP_LEFT,
    CoordinateTransform,
    InvalidMaskArtifact,
    MaskArtifact,
    MaskRaster,
    MaskSetRevision,
    PromptEvidence,
    PromptKind,
    SegmentationBackend,
    SegmentationCapability,
    SegmentationCapabilityReport,
    SegmentationContractError,
    SegmentationProvenance,
    SegmentationRequest,
    SegmentationResult,
    SegmentationStatus,
)

SOURCE_DIGEST = hashlib.sha256(b"synthetic-raw-source").hexdigest()
MASK_DIGEST = hashlib.sha256(b"synthetic-mask").hexdigest()
CREATED_AT = datetime(2026, 9, 28, tzinfo=UTC).isoformat().replace("+00:00", "Z")


def _provenance(model_id: str = "fixture-segmentation") -> SegmentationProvenance:
    return SegmentationProvenance(
        "fixture-backend",
        "1.0",
        model_id,
        "1.2",
        "fixture-checkpoint",
        hashlib.sha256(model_id.encode()).hexdigest(),
        "fixture-runtime",
        "3.12",
        "tests/fixtures/licenses/fixture.txt",
    )


def _request(*, output_asset_id: str = "working/masks/rev-1/photo-1.mask") -> SegmentationRequest:
    return SegmentationRequest(
        "project-1",
        "raw/images/001.jpg",
        SOURCE_DIGEST,
        8,
        6,
        PromptEvidence(PromptKind.BOX, {"x": 1, "y": 1, "width": 4, "height": 3}),
        output_asset_id,
    )


def _mask(
    *, model_id: str = "fixture-segmentation", revision: str = "mask-revision-1"
) -> MaskArtifact:
    return MaskArtifact(
        "mask-1",
        "raw/images/001.jpg",
        SOURCE_DIGEST,
        8,
        6,
        "working/masks/rev-1/photo-1.mask",
        MASK_DIGEST,
        4,
        3,
        CoordinateTransform(8, 6, 4, 3, 0.5, 0.5),
        _provenance(model_id),
        _request().prompt,
        revision,
        CREATED_AT,
        "post-v1",
        confidence=0.875,
        raster=MaskRaster(
            4, 3, (False, True, False, True, True, True, False, True, False, False, True, False)
        ),
    )


class FakeBackend:
    def probe(self) -> SegmentationCapabilityReport:
        return SegmentationCapabilityReport(
            "fixture-backend",
            True,
            (SegmentationCapability.BOX_PROMPT, SegmentationCapability.BATCH),
        )

    def segment(self, request: SegmentationRequest) -> SegmentationResult:
        return SegmentationResult(request, SegmentationStatus.SUCCEEDED, _provenance(), (_mask(),))

    def batch_segment(
        self, requests: tuple[SegmentationRequest, ...]
    ) -> tuple[SegmentationResult, ...]:
        return tuple(self.segment(request) for request in requests)

    def provenance(self) -> SegmentationProvenance:
        return _provenance()


class AlternateBackend(FakeBackend):
    def provenance(self) -> SegmentationProvenance:
        return _provenance("alternate-fixture")


def test_fake_backend_replacement_uses_one_public_contract() -> None:
    assert isinstance(FakeBackend(), SegmentationBackend)
    assert isinstance(AlternateBackend(), SegmentationBackend)
    assert FakeBackend().probe().as_dict()["capabilities"] == ["box-prompt", "batch"]


def test_coordinate_metadata_and_resize_mapping_round_trip() -> None:
    transform = CoordinateTransform(8, 6, 4, 3, 0.5, 0.5)
    source = transform.model_to_source(1.5, 2.0)
    assert source == (3.0, 4.0)
    assert transform.source_to_model(*source) == (1.5, 2.0)
    assert transform.as_dict()["origin"] == PIXEL_ORIGIN_TOP_LEFT
    assert transform.resized


def test_mask_artifact_serialization_preserves_provenance_and_revision_shape() -> None:
    artifact = _mask()
    serialized = artifact.as_dict()
    assert serialized["source"] == {
        "image_asset_id": "raw/images/001.jpg",
        "sha256": SOURCE_DIGEST,
        "dimensions": {"width": 8, "height": 6},
    }
    assert serialized["provenance"]["model_id"] == "fixture-segmentation"
    assert serialized["manual_edit_ancestry"] == []
    revision = MaskSetRevision("project-1", "mask-set-1", "raw-revision-1", (artifact,), CREATED_AT)
    assert revision.as_dict()["revision_digest"] == revision.revision_digest
    assert revision.as_dict()["masks"][0]["mask_revision"] == "mask-revision-1"


def test_source_bytes_are_not_touched_by_segmentation(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"immutable-source")
    before = source.read_bytes()
    result = FakeBackend().segment(_request())
    assert result.status is SegmentationStatus.SUCCEEDED
    assert source.read_bytes() == before


def test_output_must_be_working_or_derived_and_raw_is_rejected() -> None:
    with pytest.raises(SegmentationContractError, match="working, derived"):
        _request(output_asset_id="raw/masks/photo.mask")


def test_model_checkpoint_change_changes_artifact_provenance() -> None:
    assert (
        _mask().as_dict()["provenance"]
        != _mask(model_id="alternate-fixture").as_dict()["provenance"]
    )


def test_invalid_mask_identity_and_transform_fail_closed() -> None:
    with pytest.raises(InvalidMaskArtifact, match="transform model dimensions"):
        MaskArtifact(
            "mask-1",
            "raw/images/001.jpg",
            SOURCE_DIGEST,
            8,
            6,
            "working/masks/rev-1/photo-1.mask",
            MASK_DIGEST,
            4,
            3,
            CoordinateTransform(8, 6, 5, 3, 0.5, 0.5),
            _provenance(),
            _request().prompt,
            "mask-revision-1",
            CREATED_AT,
            "post-v1",
        )


def test_unavailable_result_cannot_carry_masks() -> None:
    with pytest.raises(SegmentationContractError, match="cannot return masks"):
        SegmentationResult(
            _request(),
            SegmentationStatus.UNAVAILABLE,
            _provenance(),
            (_mask(),),
            failure_reason="runtime unavailable",
        )
