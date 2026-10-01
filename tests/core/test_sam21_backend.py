from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from types import ModuleType

from packlab_core.sam21_backend import (
    SAM21_CHECKPOINT_ID,
    SAM21_CHECKPOINT_SHA256,
    SAM21_CONFIG_ID,
    SAM21_UPSTREAM_REVISION,
    CheckpointVerification,
    PyTorchSAM21Runtime,
    SAM21BasePlusBackend,
    SAM21Prediction,
    SAM21RuntimeIdentity,
    SAM21RuntimeReport,
    observe_sam21_identity,
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
    def __init__(
        self,
        *,
        device: str = "cpu",
        mask: object | None = None,
        identity: SAM21RuntimeIdentity | None = None,
    ) -> None:
        self.device = device
        self.mask = mask or [[0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 1, 0]]
        self.prompts: list[PromptEvidence] = []
        self.identity = identity or _approved_identity()

    def probe(self) -> SAM21RuntimeReport:
        return SAM21RuntimeReport(
            import_available=True,
            executable=self.identity.identity_matches_approved and self.identity.config_verified,
            python_version="3.12.10",
            torch_version="2.5.1+cpu",
            torchvision_version="0.20.1+cpu",
            identity=self.identity,
            device=self.device,
            cuda_available=self.device == "cuda",
            cuda_version="12.4" if self.device == "cuda" else "unavailable",
            environment="native-windows",
            limitations=()
            if self.identity.identity_matches_approved
            else (self.identity.verification_reason,),
        )

    def predict(
        self, image: object, *, prompt: PromptEvidence, transform: CoordinateTransform
    ) -> SAM21Prediction:
        self.prompts.append(prompt)
        return SAM21Prediction(self.mask, 0.91, transform)


def _approved_identity() -> SAM21RuntimeIdentity:
    return SAM21RuntimeIdentity(
        observed_available=True,
        observed_package_version="source-checkout",
        observed_source_form="clean-git-source-checkout",
        observed_module_path="<test-fixture>/sam2/__init__.py",
        observed_source_revision=SAM21_UPSTREAM_REVISION,
        identity_matches_approved=True,
        verification_reason="verified clean approved SAM 2 source checkout and Hydra config",
        config_id=SAM21_CONFIG_ID,
        config_sha256="37d6c56b07a7f8d08baaa314315c60dc3aabe2edc66cd92bac6d1ed50038e788",
        config_verified=True,
        config_path="<test-fixture>/sam2/configs/sam2.1/sam2.1_hiera_b+.yaml",
    )


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
    return SAM21BasePlusBackend(
        checkpoint,
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
    identity = provenance["runtime_details"]["sam2_identity"]
    assert identity["expected_revision"] == SAM21_UPSTREAM_REVISION
    assert identity["observed_source_revision"] == SAM21_UPSTREAM_REVISION
    assert identity["identity_matches_approved"] is True
    assert provenance["runtime_details"]["executed_config_id"] == SAM21_CONFIG_ID
    assert (
        provenance["runtime_details"]["executed_config_sha256"]
        == _approved_identity().config_sha256
    )


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
        image_provider=lambda request: object(),
        runtime=FakeRuntime(
            identity=SAM21RuntimeIdentity(
                observed_available=True,
                observed_package_version="unverifiable",
                observed_source_form="unverifiable",
                observed_module_path="<fixture>/sam2/__init__.py",
                observed_source_revision=None,
                identity_matches_approved=False,
                verification_reason="SAM 2 source checkout could not be verified",
                config_id=None,
                config_sha256=None,
                config_verified=False,
            )
        ),
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


def test_sam2_unavailable_has_no_fabricated_observed_revision(monkeypatch) -> None:
    def fake_import(name: str):
        if name == "sam2":
            raise ModuleNotFoundError("sam2 unavailable")
        raise ModuleNotFoundError(f"{name} unavailable")

    monkeypatch.setattr("packlab_core.sam21_backend.importlib.import_module", fake_import)
    report = PyTorchSAM21Runtime(Path("unused-checkpoint.pt")).probe()
    assert report.identity.observed_available is False
    assert report.identity.observed_source_revision is None
    assert report.identity.observed_source_form == "unavailable"
    assert report.identity.identity_matches_approved is False
    assert report.identity.verification_reason


def test_runtime_identity_requires_approved_clean_source_and_config(tmp_path: Path) -> None:
    source_root = tmp_path / "sam2-checkout"
    package = source_root / "sam2"
    config = package / SAM21_CONFIG_ID
    config.parent.mkdir(parents=True)
    config.write_bytes(b"verified hydra config")
    module = ModuleType("sam2")
    module.__file__ = str(package / "__init__.py")
    config_digest = hashlib.sha256(config.read_bytes()).hexdigest()

    def command_runner(args, **kwargs):
        if "get-url" in args:
            command = "get-url"
        elif "status" in args:
            command = "--untracked-files=all"
        else:
            command = args[-1]
        responses = {
            "--show-toplevel": str(source_root),
            "HEAD": SAM21_UPSTREAM_REVISION,
            "get-url": "https://github.com/facebookresearch/sam2.git",
            "--untracked-files=all": "",
        }
        return subprocess.CompletedProcess(args, 0, responses[command], "")

    identity = observe_sam21_identity(
        module,
        command_runner=command_runner,
        package_version="test-source",
        expected_config_sha256=config_digest,
    )
    assert identity.identity_matches_approved
    assert identity.config_verified
    assert identity.config_id == SAM21_CONFIG_ID
    assert identity.config_sha256 == config_digest

    wrong_digest = observe_sam21_identity(module, command_runner=command_runner)
    assert not wrong_digest.identity_matches_approved
    assert not wrong_digest.config_verified

    def mismatched_commit_runner(args, **kwargs):
        result = command_runner(args, **kwargs)
        if args[-1] == "HEAD":
            return subprocess.CompletedProcess(args, 0, "0" * 40, "")
        return result

    mismatched = observe_sam21_identity(
        module,
        command_runner=mismatched_commit_runner,
        expected_config_sha256=config_digest,
    )
    assert not mismatched.identity_matches_approved
    assert mismatched.observed_source_revision == "0" * 40
    assert not mismatched.config_verified

    def unverifiable_runner(args, **kwargs):
        raise subprocess.CalledProcessError(128, args, stderr="not a git checkout")

    unverifiable = observe_sam21_identity(
        module,
        command_runner=unverifiable_runner,
        expected_config_sha256=config_digest,
    )
    assert unverifiable.observed_available
    assert unverifiable.observed_source_revision is None
    assert unverifiable.observed_source_form == "unverifiable"
    assert not unverifiable.identity_matches_approved
    assert not unverifiable.config_verified


def test_external_lookalike_config_cannot_authorize_runtime(tmp_path: Path) -> None:
    lookalike = tmp_path / "sam2.1_hiera_b+.yaml"
    lookalike.write_text("dummy", encoding="utf-8")
    identity = SAM21RuntimeIdentity(
        observed_available=True,
        observed_package_version="unknown",
        observed_source_form="unverifiable",
        observed_module_path="<external>/sam2/__init__.py",
        observed_source_revision=None,
        identity_matches_approved=False,
        verification_reason="installed source revision cannot be verified",
        config_id=None,
        config_sha256=None,
        config_verified=False,
        config_path=str(lookalike),
    )
    backend = _backend(tmp_path / "backend", FakeRuntime(identity=identity))
    assert backend.probe().available is False
    assert backend.provenance().as_dict()["runtime_details"]["executed_config_id"] is None


def test_source_bytes_remain_unchanged_through_backend_boundary(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"immutable RAW_CAPTURE")
    before = source.read_bytes()
    backend = _backend(tmp_path / "backend")
    result = backend.segment(_request(PromptEvidence(PromptKind.BOX, {"box": [0, 0, 2, 2]})))
    assert result.status is SegmentationStatus.SUCCEEDED
    assert source.read_bytes() == before
