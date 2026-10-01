from __future__ import annotations

import hashlib
from pathlib import Path

from packlab_core.sam21_backend import (
    SAM21_CHECKPOINT_ID,
    SAM21_CHECKPOINT_SHA256,
    SAM21_CONFIG_ID,
    CheckpointVerification,
    SAM21BasePlusBackend,
    SAM21Prediction,
    SAM21RuntimeReport,
    verify_sam21_checkpoint,
)
from packlab_core.segmentation import (
    CoordinateTransform,
    PromptEvidence,
    PromptKind,
    SegmentationCapability,
    SegmentationRequest,
    SegmentationStatus,
)

SOURCE_DIGEST = hashlib.sha256(b"synthetic-sam-source").hexdigest()


class FakeRuntime:
    def __init__(self, *, device: str = "cpu", mask: object | None = None) -> None:
        self.device = device
        self.mask = mask or [[0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 1, 0]]
        self.prompts: list[PromptEvidence] = []

    def probe(self) -> SAM21RuntimeReport:
        return SAM21RuntimeReport(
            True,
            True,
            "3.12.10",
            "2.5.1+cpu",
            "0.20.1+cpu",
            "2b90b9f5ceec907a1c18123530e92e794ad901a4",
            self.device,
            self.device == "cuda",
            "12.4" if self.device == "cuda" else "unavailable",
            "native-windows",
        )

    def predict(
        self, image: object, *, prompt: PromptEvidence, transform: CoordinateTransform
    ) -> SAM21Prediction:
        self.prompts.append(prompt)
        return SAM21Prediction(self.mask, 0.91, transform)


def _request(prompt: PromptEvidence) -> SegmentationRequest:
    return SegmentationRequest(
        "project-1",
        "raw/images/synthetic.jpg",
        SOURCE_DIGEST,
        4,
        3,
        prompt,
        "working/masks/sam21.mask",
    )


def _backend(tmp_path: Path, runtime: FakeRuntime | None = None) -> SAM21BasePlusBackend:
    tmp_path.mkdir(parents=True, exist_ok=True)
    checkpoint = tmp_path / SAM21_CHECKPOINT_ID
    checkpoint.write_bytes(b"fixture-checkpoint")
    config = tmp_path / Path(SAM21_CONFIG_ID).name
    config.write_text("fixture-config", encoding="utf-8")
    return SAM21BasePlusBackend(
        checkpoint,
        config,
        image_provider=lambda request: {"asset": request.source_image_asset_id},
        runtime=runtime or FakeRuntime(),
        expected_checkpoint_sha256=hashlib.sha256(b"fixture-checkpoint").hexdigest(),
        expected_checkpoint_bytes=len(b"fixture-checkpoint"),
    )


def test_checkpoint_verification_requires_exact_identity_and_hash(tmp_path: Path) -> None:
    wrong = tmp_path / "lookalike.pt"
    wrong.write_bytes(b"fixture")
    result = verify_sam21_checkpoint(wrong, expected_bytes=7, expected_sha256="0" * 64)
    assert not result.verified
    assert "exactly" in (result.reason or "")

    checkpoint = tmp_path / SAM21_CHECKPOINT_ID
    checkpoint.write_bytes(b"fixture")
    result = verify_sam21_checkpoint(
        checkpoint, expected_bytes=7, expected_sha256=hashlib.sha256(b"fixture").hexdigest()
    )
    assert result == CheckpointVerification(
        SAM21_CHECKPOINT_ID,
        "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt",
        7,
        hashlib.sha256(b"fixture").hexdigest(),
        True,
    )

    mismatch = tmp_path / SAM21_CHECKPOINT_ID
    mismatch.write_bytes(b"different")
    mismatch_result = verify_sam21_checkpoint(
        mismatch, expected_bytes=len(b"different"), expected_sha256="0" * 64
    )
    assert not mismatch_result.verified
    assert mismatch_result.sha256 == hashlib.sha256(b"different").hexdigest()
    assert "SHA-256" in (mismatch_result.reason or "")
    assert SAM21_CHECKPOINT_SHA256 == (
        "a2345aede8715ab1d5d31b4a509fb160c5a4af1970f199d9054ccfb746c004c5"
    )


def test_backend_proves_exact_identity_and_cpu_capabilities(tmp_path: Path) -> None:
    backend = _backend(tmp_path)
    report = backend.probe()
    assert report.available
    assert report.capabilities == (
        SegmentationCapability.POINT_PROMPT,
        SegmentationCapability.BOX_PROMPT,
    )
    assert report.details["network_fallback"] is False
    provenance = backend.provenance().as_dict()
    assert provenance["checkpoint_id"] == SAM21_CHECKPOINT_ID
    assert provenance["runtime_details"]["config"] == SAM21_CONFIG_ID


def test_point_and_box_prompts_produce_source_grid_masks(tmp_path: Path) -> None:
    runtime = FakeRuntime()
    backend = _backend(tmp_path, runtime)
    point = _request(PromptEvidence(PromptKind.POINT, {"points": [[1, 1]], "labels": [1]}))
    box = _request(PromptEvidence(PromptKind.BOX, {"box": [0, 0, 3, 2]}))
    point_result = backend.segment(point)
    box_result = backend.segment(box)
    assert point_result.status is SegmentationStatus.SUCCEEDED
    assert box_result.status is SegmentationStatus.SUCCEEDED
    assert runtime.prompts[0].kind is PromptKind.POINT
    assert runtime.prompts[1].kind is PromptKind.BOX
    assert runtime.prompts[1].data["box"] == (0.0, 0.0, 3.0, 2.0)
    assert point_result.masks[0].mask_width == 4
    assert point_result.masks[0].mask_height == 3
    assert point_result.masks[0].transform.model_to_source(1.5, 1.5) == (1.5, 1.5)


def test_invalid_prompt_and_malformed_output_fail_closed(tmp_path: Path) -> None:
    backend = _backend(tmp_path, FakeRuntime(mask=[[1, 0]]))
    invalid = _request(PromptEvidence(PromptKind.POINT, {"points": [[4, 1]], "labels": [1]}))
    assert backend.segment(invalid).status is SegmentationStatus.FAILED

    malformed = _request(PromptEvidence(PromptKind.BOX, {"box": [0, 0, 2, 2]}))
    result = backend.segment(malformed)
    assert result.status is SegmentationStatus.FAILED
    assert not result.masks


def test_boolean_mask_and_nonfinite_confidence_are_normalized_or_rejected(tmp_path: Path) -> None:
    boolean_backend = _backend(
        tmp_path / "boolean", FakeRuntime(mask=[[True, False, False, True]] * 3)
    )
    boolean_result = boolean_backend.segment(
        _request(PromptEvidence(PromptKind.POINT, {"points": [[1, 1]], "labels": [1]}))
    )
    assert boolean_result.status is SegmentationStatus.SUCCEEDED
    assert boolean_result.masks[0].raster is not None
    assert boolean_result.masks[0].raster.sample(0, 0)

    class NonFiniteRuntime(FakeRuntime):
        def predict(
            self, image: object, *, prompt: PromptEvidence, transform: CoordinateTransform
        ) -> SAM21Prediction:
            return SAM21Prediction(self.mask, float("nan"), transform)

    nonfinite_backend = _backend(tmp_path / "nonfinite", NonFiniteRuntime())
    nonfinite_result = nonfinite_backend.segment(
        _request(PromptEvidence(PromptKind.BOX, {"box": [0, 0, 2, 2]}))
    )
    assert nonfinite_result.status is SegmentationStatus.FAILED
    assert "finite" in (nonfinite_result.failure_reason or "")


def test_missing_checkpoint_or_runtime_is_unavailable_without_network(tmp_path: Path) -> None:
    config = tmp_path / Path(SAM21_CONFIG_ID).name
    config.write_text("fixture-config", encoding="utf-8")
    backend = SAM21BasePlusBackend(
        tmp_path / SAM21_CHECKPOINT_ID,
        config,
        image_provider=lambda request: object(),
        runtime=FakeRuntime(),
    )
    result = backend.segment(_request(PromptEvidence(PromptKind.BOX, {"box": [0, 0, 2, 2]})))
    assert result.status is SegmentationStatus.UNAVAILABLE
    assert "missing" in (result.failure_reason or "")


def test_cuda_and_cpu_facts_are_reported_without_assumption(tmp_path: Path) -> None:
    cpu = _backend(tmp_path, FakeRuntime(device="cpu"))
    assert cpu.probe().details["cuda"]["available"] is False

    cuda = _backend(tmp_path / "cuda", FakeRuntime(device="cuda"))
    assert cuda.probe().details["cuda"] == {"available": True, "version": "12.4"}


def test_backend_is_replaceable_without_model_specific_downstream_contract(tmp_path: Path) -> None:
    backend = _backend(tmp_path)
    result = backend.segment(_request(PromptEvidence(PromptKind.BOX, {"box": [0, 0, 2, 2]})))
    assert result.masks[0].authority_class == "DERIVED_MASK"
    assert result.masks[0].provenance.backend_id == "packlab.sam2.1-hiera-base-plus"
