"""Local SAM 2.1 Hiera Base+ adapter for the PackLab segmentation contract.

The optional PyTorch/SAM runtime is deliberately loaded behind this module.
PackLab domain consumers depend only on :mod:`packlab_core.segmentation`; this
adapter never downloads code, checkpoints, or other runtime assets.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import math
import platform
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

from .segmentation import (
    CoordinateTransform,
    InvalidSegmentationRequest,
    MaskArtifact,
    MaskRaster,
    PromptEvidence,
    PromptKind,
    SegmentationBackend,
    SegmentationCapability,
    SegmentationCapabilityReport,
    SegmentationProvenance,
    SegmentationRequest,
    SegmentationResult,
    SegmentationStatus,
)

SAM21_BACKEND_ID = "packlab.sam2.1-hiera-base-plus"
SAM21_BACKEND_VERSION = "pl-0186-v2"
SAM21_MODEL_ID = "sam2.1-hiera-base-plus"
SAM21_MODEL_VERSION = "2.1"
SAM21_UPSTREAM_REPOSITORY = "https://github.com/facebookresearch/sam2"
SAM21_UPSTREAM_REVISION = "2b90b9f5ceec907a1c18123530e92e794ad901a4"
SAM21_REPOSITORY_LICENSE = "Apache-2.0"
SAM21_CHECKPOINT_ID = "sam2.1_hiera_base_plus.pt"
SAM21_CONFIG_ID = "configs/sam2.1/sam2.1_hiera_b+.yaml"
SAM21_CHECKPOINT_URL = (
    "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt"
)
SAM21_CHECKPOINT_BYTES = 323_606_802
SAM21_CHECKPOINT_SHA256 = "a2345aede8715ab1d5d31b4a509fb160c5a4af1970f199d9054ccfb746c004c5"
SAM21_CONFIG_SHA256 = "37d6c56b07a7f8d08baaa314315c60dc3aabe2edc66cd92bac6d1ed50038e788"
SAM21_LICENSE_RECORD = "docs/architecture/DEPENDENCY_LICENSE_REGISTER.md#sam-2--sam-21-base"


class SAM21BackendError(RuntimeError):
    """Base error for local SAM adapter failures."""


class SAM21CheckpointError(SAM21BackendError):
    """Raised when the explicitly configured checkpoint cannot be trusted."""


class SAM21RuntimeError(SAM21BackendError):
    """Raised when the local runtime cannot execute a prediction."""


@dataclass(frozen=True, slots=True)
class CheckpointVerification:
    """Portable checkpoint provenance after a local, explicit hash check."""

    filename: str
    source_url: str
    byte_size: int
    sha256: str
    verified: bool
    reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "filename": self.filename,
            "source_url": self.source_url,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
            "verified": self.verified,
            "reason": self.reason,
        }


def verify_sam21_checkpoint(
    checkpoint_path: str | Path,
    *,
    expected_sha256: str = SAM21_CHECKPOINT_SHA256,
    expected_bytes: int = SAM21_CHECKPOINT_BYTES,
) -> CheckpointVerification:
    """Verify the exact official SAM 2.1 Base+ artifact without downloading it."""

    path = Path(checkpoint_path)
    if path.name != SAM21_CHECKPOINT_ID:
        return CheckpointVerification(
            path.name,
            SAM21_CHECKPOINT_URL,
            0,
            "",
            False,
            f"checkpoint filename must be exactly {SAM21_CHECKPOINT_ID}",
        )
    if not path.is_file():
        return CheckpointVerification(
            path.name, SAM21_CHECKPOINT_URL, 0, "", False, "checkpoint is missing"
        )
    byte_size = path.stat().st_size
    digest = hashlib.sha256()
    with path.open("rb") as checkpoint:
        for block in iter(lambda: checkpoint.read(1024 * 1024), b""):
            digest.update(block)
    sha256 = digest.hexdigest()
    if byte_size != expected_bytes:
        return CheckpointVerification(
            path.name,
            SAM21_CHECKPOINT_URL,
            byte_size,
            sha256,
            False,
            f"checkpoint byte size {byte_size} does not match expected {expected_bytes}",
        )
    if sha256 != expected_sha256:
        return CheckpointVerification(
            path.name,
            SAM21_CHECKPOINT_URL,
            byte_size,
            sha256,
            False,
            "checkpoint SHA-256 does not match the configured expected digest",
        )
    return CheckpointVerification(path.name, SAM21_CHECKPOINT_URL, byte_size, sha256, True)


@dataclass(frozen=True, slots=True)
class SAM21RuntimeIdentity:
    """Expected versus independently observed SAM 2 source identity."""

    observed_available: bool
    observed_package_version: str
    observed_source_form: str
    observed_module_path: str | None
    observed_source_revision: str | None
    identity_matches_approved: bool
    verification_reason: str
    config_id: str | None
    config_sha256: str | None
    config_verified: bool
    config_path: str | None = None

    def portable_dict(self) -> dict[str, object]:
        return {
            "expected_repository": SAM21_UPSTREAM_REPOSITORY,
            "expected_revision": SAM21_UPSTREAM_REVISION,
            "observed_available": self.observed_available,
            "observed_package_version": self.observed_package_version,
            "observed_source_form": self.observed_source_form,
            "observed_source_revision": self.observed_source_revision,
            "identity_matches_approved": self.identity_matches_approved,
            "verification_reason": self.verification_reason,
            "config_id": self.config_id,
            "config_sha256": self.config_sha256,
            "config_verified": self.config_verified,
        }

    def diagnostic_dict(self) -> dict[str, object]:
        return {
            **self.portable_dict(),
            "observed_module_path": self.observed_module_path,
            "config_path": self.config_path,
        }


@dataclass(frozen=True, slots=True)
class SAM21RuntimeReport:
    """Explicit local runtime, installed-source and executed-config facts."""

    import_available: bool
    executable: bool
    python_version: str
    torch_version: str
    torchvision_version: str
    identity: SAM21RuntimeIdentity
    device: str
    cuda_available: bool
    cuda_version: str
    environment: str
    limitations: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "python_version": self.python_version,
            "torch_version": self.torch_version,
            "torchvision_version": self.torchvision_version,
            "identity": self.identity.diagnostic_dict(),
            "device": self.device,
            "cuda_available": self.cuda_available,
            "cuda_version": self.cuda_version,
            "environment": self.environment,
            "import_available": self.import_available,
            "executable": self.executable,
            "limitations": list(self.limitations),
        }


def _unavailable_identity(reason: str) -> SAM21RuntimeIdentity:
    return SAM21RuntimeIdentity(
        observed_available=False,
        observed_package_version="unavailable",
        observed_source_form="unavailable",
        observed_module_path=None,
        observed_source_revision=None,
        identity_matches_approved=False,
        verification_reason=reason,
        config_id=None,
        config_sha256=None,
        config_verified=False,
    )


def observe_sam21_identity(
    sam2_module: ModuleType,
    *,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    package_version: str | None = None,
    expected_config_sha256: str = SAM21_CONFIG_SHA256,
) -> SAM21RuntimeIdentity:
    """Verify a clean SAM 2 source checkout and the Hydra config it will resolve."""

    module_file_value = getattr(sam2_module, "__file__", None)
    if not isinstance(module_file_value, str) or not module_file_value:
        return SAM21RuntimeIdentity(
            True,
            "unknown",
            "unverifiable",
            None,
            None,
            False,
            "SAM 2 module has no filesystem source path",
            None,
            None,
            False,
        )
    module_file = Path(module_file_value).resolve()
    try:
        root_result = command_runner(
            ["git", "-C", str(module_file.parent), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        source_root = Path(root_result.stdout.strip()).resolve()
        revision_result = command_runner(
            ["git", "-C", str(source_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        observed_revision = revision_result.stdout.strip().lower()
        remote_result = command_runner(
            ["git", "-C", str(source_root), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        remote = remote_result.stdout.strip().lower().removesuffix(".git")
        clean_result = command_runner(
            [
                "git",
                "-C",
                str(source_root),
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                "sam2",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        package_root = (source_root / "sam2").resolve()
        if not module_file.is_relative_to(package_root):
            raise ValueError("imported SAM 2 module is outside the source checkout package")
        config_path = source_root / "sam2" / SAM21_CONFIG_ID
        config_sha256 = _file_sha256(config_path) if config_path.is_file() else None
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        return SAM21RuntimeIdentity(
            True,
            package_version or _sam2_package_version(),
            "unverifiable",
            str(module_file),
            None,
            False,
            f"SAM 2 source checkout could not be verified: {type(error).__name__}",
            None,
            None,
            False,
        )

    expected_remote_names = {
        "https://github.com/facebookresearch/sam2",
        "git@github.com:facebookresearch/sam2",
        "ssh://git@github.com/facebookresearch/sam2",
    }
    repository_matches = remote in expected_remote_names
    revision_matches = observed_revision == SAM21_UPSTREAM_REVISION
    clean = not clean_result.stdout.strip()
    config_matches = config_sha256 == expected_config_sha256
    matches = repository_matches and revision_matches and clean and config_matches
    reasons = []
    if not repository_matches:
        reasons.append("origin is not the approved facebookresearch/sam2 repository")
    if not revision_matches:
        reasons.append("installed SAM 2 Git commit does not match the approved revision")
    if not clean:
        reasons.append("SAM 2 source checkout has modified or untracked files")
    if not config_matches:
        reasons.append("installed Hydra config is missing or its SHA-256 is not approved")
    reason = (
        "verified clean approved SAM 2 source checkout and Hydra config"
        if matches
        else "; ".join(reasons)
    )
    return SAM21RuntimeIdentity(
        observed_available=True,
        observed_package_version=package_version or _sam2_package_version(),
        observed_source_form="clean-git-source-checkout",
        observed_module_path=str(module_file),
        observed_source_revision=observed_revision,
        identity_matches_approved=matches,
        verification_reason=reason,
        config_id=SAM21_CONFIG_ID if config_path.is_file() else None,
        config_sha256=config_sha256,
        config_verified=repository_matches and revision_matches and clean and config_matches,
        config_path=str(config_path) if config_path.is_file() else None,
    )


def _sam2_package_version() -> str:
    for distribution in ("sam-2", "sam2", "SAM-2"):
        try:
            return importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            continue
    return "unknown"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class SAM21Prediction:
    """Runtime-neutral prediction returned by the SAM adapter seam."""

    mask: object
    score: float
    transform: CoordinateTransform


class SAM21Runtime(Protocol):
    """Small local seam implemented by PyTorch or a deterministic test double."""

    def probe(self) -> SAM21RuntimeReport: ...

    def predict(
        self,
        image: object,
        *,
        prompt: PromptEvidence,
        transform: CoordinateTransform,
    ) -> SAM21Prediction: ...


ImageProvider = Callable[[SegmentationRequest], object]


class PyTorchSAM21Runtime:
    """Lazy local PyTorch/SAM 2.1 runtime; imports never trigger network I/O."""

    def __init__(self, checkpoint_path: Path, *, device: str = "auto") -> None:
        self._checkpoint_path = checkpoint_path
        self._device_preference = device
        self._predictor: Any | None = None
        self._torch: ModuleType | None = None

    def _sam2_module(self) -> ModuleType | None:
        try:
            return importlib.import_module("sam2")
        except (ImportError, OSError):
            return None

    def probe(self) -> SAM21RuntimeReport:
        sam2 = self._sam2_module()
        identity = (
            observe_sam21_identity(sam2)
            if sam2 is not None
            else _unavailable_identity("SAM 2 is not importable")
        )
        try:
            torch = importlib.import_module("torch")
            torchvision = importlib.import_module("torchvision")
        except (ImportError, OSError):
            return SAM21RuntimeReport(
                import_available=False,
                executable=False,
                python_version=platform.python_version(),
                torch_version=(
                    "unavailable"
                    if "torch" not in locals()
                    else str(getattr(torch, "__version__", "unknown"))
                ),
                torchvision_version="unavailable",
                identity=identity,
                device="unavailable",
                cuda_available=False,
                cuda_version="unavailable",
                environment=_environment_name(),
                limitations=("PyTorch or torchvision is not importable",),
            )
        cuda_available = bool(torch.cuda.is_available())
        device = "cuda" if self._device_preference == "auto" and cuda_available else "cpu"
        if self._device_preference not in {"auto", "cpu", "cuda"}:
            return SAM21RuntimeReport(
                import_available=True,
                executable=False,
                python_version=platform.python_version(),
                torch_version=str(getattr(torch, "__version__", "unknown")),
                torchvision_version=str(getattr(torchvision, "__version__", "unknown")),
                identity=identity,
                device="invalid",
                cuda_available=cuda_available,
                cuda_version=str(getattr(torch.version, "cuda", "unavailable")),
                environment=_environment_name(),
                limitations=("device must be auto, cpu, or cuda",),
            )
        if self._device_preference == "cuda" and not cuda_available:
            return SAM21RuntimeReport(
                import_available=True,
                executable=False,
                python_version=platform.python_version(),
                torch_version=str(getattr(torch, "__version__", "unknown")),
                torchvision_version=str(getattr(torchvision, "__version__", "unknown")),
                identity=identity,
                device="cuda",
                cuda_available=False,
                cuda_version=str(getattr(torch.version, "cuda", "unavailable")),
                environment=_environment_name(),
                limitations=("CUDA was requested but is unavailable",),
            )
        self._torch = torch
        executable = identity.identity_matches_approved and identity.config_verified
        limitations = () if executable else (identity.verification_reason,)
        return SAM21RuntimeReport(
            import_available=True,
            executable=executable,
            python_version=platform.python_version(),
            torch_version=str(getattr(torch, "__version__", "unknown")),
            torchvision_version=str(getattr(torchvision, "__version__", "unknown")),
            identity=identity,
            device=device,
            cuda_available=cuda_available,
            cuda_version=str(getattr(torch.version, "cuda", "unavailable")),
            environment=_environment_name(),
            limitations=limitations,
        )

    def _ensure_predictor(self) -> Any:
        if self._predictor is not None:
            return self._predictor
        report = self.probe()
        if not report.executable or not report.identity.config_verified:
            raise SAM21RuntimeError("approved SAM 2 source/config identity is unavailable")
        sam2 = self._sam2_module()
        if sam2 is None:
            raise SAM21RuntimeError("local SAM 2 runtime is unavailable")
        torch = importlib.import_module("torch")
        try:
            build_module = importlib.import_module("sam2.build_sam")
            predictor_module = importlib.import_module("sam2.sam2_image_predictor")
            build_sam2 = getattr(build_module, "build_sam2")
            predictor_type = getattr(predictor_module, "SAM2ImagePredictor")
            device = report.device
            model = build_sam2(SAM21_CONFIG_ID, str(self._checkpoint_path), device=device)
            self._predictor = predictor_type(model)
            self._torch = torch
            return self._predictor
        except (AttributeError, ImportError, OSError, RuntimeError) as error:
            raise SAM21RuntimeError(f"SAM 2 predictor initialization failed: {error}") from error

    def predict(
        self,
        image: object,
        *,
        prompt: PromptEvidence,
        transform: CoordinateTransform,
    ) -> SAM21Prediction:
        predictor = self._ensure_predictor()
        try:
            predictor.set_image(image)
            numpy = importlib.import_module("numpy")
            if prompt.kind is PromptKind.POINT:
                points = prompt.data["points"]
                labels = prompt.data["labels"]
                raw_masks, scores, _logits = predictor.predict(
                    point_coords=numpy.asarray(points, dtype=float),
                    point_labels=numpy.asarray(labels, dtype=int),
                    multimask_output=False,
                )
            elif prompt.kind is PromptKind.BOX:
                box = prompt.data["box"]
                raw_masks, scores, _logits = predictor.predict(
                    box=numpy.asarray(box, dtype=float), multimask_output=False
                )
            else:
                raise SAM21RuntimeError(f"unsupported SAM prompt: {prompt.kind.value}")
            return SAM21Prediction(raw_masks, _single_score(scores), transform)
        except (
            AttributeError,
            ImportError,
            IndexError,
            KeyError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as error:
            raise SAM21RuntimeError(f"SAM 2 prediction failed: {error}") from error


class SAM21BasePlusBackend(SegmentationBackend):
    """PackLab-owned SAM 2.1 Hiera Base+ backend with fail-closed execution."""

    def __init__(
        self,
        checkpoint_path: str | Path,
        *,
        image_provider: ImageProvider,
        runtime: SAM21Runtime | None = None,
        expected_checkpoint_sha256: str = SAM21_CHECKPOINT_SHA256,
        expected_checkpoint_bytes: int = SAM21_CHECKPOINT_BYTES,
    ) -> None:
        self._checkpoint_path = Path(checkpoint_path)
        self._image_provider = image_provider
        self._runtime = runtime or PyTorchSAM21Runtime(self._checkpoint_path)
        self._expected_checkpoint_sha256 = expected_checkpoint_sha256
        self._expected_checkpoint_bytes = expected_checkpoint_bytes

    def _checkpoint(self) -> CheckpointVerification:
        return verify_sam21_checkpoint(
            self._checkpoint_path,
            expected_sha256=self._expected_checkpoint_sha256,
            expected_bytes=self._expected_checkpoint_bytes,
        )

    def _runtime_report(self) -> SAM21RuntimeReport:
        try:
            return self._runtime.probe()
        except Exception as error:  # capability probing must return unavailable, never crash
            return SAM21RuntimeReport(
                import_available=False,
                executable=False,
                python_version=platform.python_version(),
                torch_version="unavailable",
                torchvision_version="unavailable",
                identity=_unavailable_identity(f"runtime probe failed: {type(error).__name__}"),
                device="unavailable",
                cuda_available=False,
                cuda_version="unavailable",
                environment=_environment_name(),
                limitations=(f"runtime probe failed: {type(error).__name__}",),
            )

    def provenance(self) -> SegmentationProvenance:
        runtime = self._runtime_report()
        checkpoint = self._checkpoint()
        return SegmentationProvenance(
            SAM21_BACKEND_ID,
            SAM21_BACKEND_VERSION,
            SAM21_MODEL_ID,
            SAM21_MODEL_VERSION,
            SAM21_CHECKPOINT_ID,
            checkpoint.sha256 or self._expected_checkpoint_sha256,
            "pytorch-local",
            runtime.torch_version,
            SAM21_LICENSE_RECORD,
            {
                "upstream_repository": SAM21_UPSTREAM_REPOSITORY,
                "upstream_revision": SAM21_UPSTREAM_REVISION,
                "repository_license": SAM21_REPOSITORY_LICENSE,
                "checkpoint_source": SAM21_CHECKPOINT_URL,
                "checkpoint_filename": SAM21_CHECKPOINT_ID,
                "checkpoint_bytes": checkpoint.byte_size,
                "checkpoint_verified": checkpoint.verified,
                "sam2_identity": runtime.identity.portable_dict(),
                "executed_config_id": runtime.identity.config_id,
                "executed_config_sha256": runtime.identity.config_sha256,
                "executed_config_verified": runtime.identity.config_verified,
                "python_version": runtime.python_version,
                "torch_version": runtime.torch_version,
                "torchvision_version": runtime.torchvision_version,
                "device": runtime.device,
                "cuda_available": runtime.cuda_available,
                "cuda_version": runtime.cuda_version,
                "environment": runtime.environment,
            },
        )

    def probe(self) -> SegmentationCapabilityReport:
        checkpoint = self._checkpoint()
        runtime = self._runtime_report()
        config_ok = runtime.identity.config_verified
        available = (
            checkpoint.verified
            and runtime.executable
            and runtime.identity.identity_matches_approved
            and config_ok
        )
        limitations = list(runtime.limitations)
        if not checkpoint.verified:
            limitations.append(checkpoint.reason or "checkpoint verification failed")
        if not config_ok:
            limitations.append("approved Hydra config is not verified in the approved SAM 2 source")
        details = {
            "backend_configured": True,
            "runtime_import_available": runtime.import_available,
            "runtime_executable": runtime.executable,
            "model_present": checkpoint.verified,
            "config_present": runtime.identity.config_id == SAM21_CONFIG_ID,
            "checkpoint_hash_verified": checkpoint.verified,
            "checkpoint": checkpoint.as_dict(),
            "runtime": runtime.as_dict(),
            "runtime_identity": runtime.identity.diagnostic_dict(),
            "executed_config_id": runtime.identity.config_id,
            "executed_config_sha256": runtime.identity.config_sha256,
            "executed_config_verified": runtime.identity.config_verified,
            "cuda": {"available": runtime.cuda_available, "version": runtime.cuda_version},
            "native_or_wsl": runtime.environment,
            "network_fallback": False,
        }
        return SegmentationCapabilityReport(
            SAM21_BACKEND_ID,
            available,
            (
                SegmentationCapability.POINT_PROMPT,
                SegmentationCapability.BOX_PROMPT,
            )
            if available
            else (),
            tuple(limitations),
            details,
        )

    def segment(self, request: SegmentationRequest) -> SegmentationResult:
        provenance = self.provenance()
        report = self.probe()
        if not report.available:
            return SegmentationResult(
                request,
                SegmentationStatus.UNAVAILABLE,
                provenance,
                failure_reason="; ".join(report.limitations) or "SAM 2.1 backend unavailable",
            )
        if request.prompt.kind not in {PromptKind.POINT, PromptKind.BOX}:
            return self._failed(request, provenance, "unsupported prompt mode")
        try:
            prompt = _normalize_prompt(request)
            image = self._image_provider(request)
            transform = CoordinateTransform(
                request.source_width,
                request.source_height,
                request.source_width,
                request.source_height,
            )
            prediction = self._runtime.predict(image, prompt=prompt, transform=transform)
            raster, output_transform = _normalize_prediction(prediction, request)
            mask_digest = raster.digest
            revision = hashlib.sha256(
                f"{request.source_digest}:{mask_digest}:{prompt.as_dict()}".encode()
            ).hexdigest()
            artifact = MaskArtifact(
                artifact_id=f"sam21-{revision[:16]}",
                source_image_asset_id=request.source_image_asset_id,
                source_digest=request.source_digest,
                source_width=request.source_width,
                source_height=request.source_height,
                mask_asset_id=request.output_asset_id,
                mask_digest=mask_digest,
                mask_width=raster.width,
                mask_height=raster.height,
                transform=output_transform,
                provenance=provenance,
                prompt=prompt,
                mask_revision=revision,
                created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                post_processing_version="none:sam21-raw-output",
                confidence=prediction.score,
                quality_flags=("raw_model_output",),
                raster=raster,
            )
            return SegmentationResult(
                request, SegmentationStatus.SUCCEEDED, provenance, (artifact,)
            )
        except (
            InvalidSegmentationRequest,
            OSError,
            RuntimeError,
            SAM21BackendError,
            TypeError,
            ValueError,
        ) as error:
            return self._failed(request, provenance, str(error))

    def batch_segment(
        self, requests: Sequence[SegmentationRequest]
    ) -> tuple[SegmentationResult, ...]:
        return tuple(self.segment(request) for request in requests)

    def _failed(
        self, request: SegmentationRequest, provenance: SegmentationProvenance, reason: str
    ) -> SegmentationResult:
        return SegmentationResult(
            request,
            SegmentationStatus.FAILED,
            provenance,
            failure_reason=reason or "SAM 2.1 execution failed",
        )


def _environment_name() -> str:
    return "WSL" if "microsoft-standard" in platform.release().lower() else "native-windows"


def _normalize_prompt(request: SegmentationRequest) -> PromptEvidence:
    data = request.prompt.data
    if request.prompt.kind is PromptKind.POINT:
        points = data.get("points")
        labels = data.get("labels")
        if not isinstance(points, Sequence) or isinstance(points, (str, bytes)):
            raise InvalidSegmentationRequest("point prompt requires points")
        if not isinstance(labels, Sequence) or isinstance(labels, (str, bytes)):
            raise InvalidSegmentationRequest("point prompt requires labels")
        if not points or len(points) != len(labels):
            raise InvalidSegmentationRequest(
                "point prompt points and labels must be non-empty and paired"
            )
        normalized_points: list[list[float]] = []
        normalized_labels: list[int] = []
        for point, label in zip(points, labels, strict=True):
            if not isinstance(point, Sequence) or len(point) != 2:
                raise InvalidSegmentationRequest("each point must contain x and y")
            x, y = _finite(point[0], "point.x"), _finite(point[1], "point.y")
            if not 0 <= x < request.source_width or not 0 <= y < request.source_height:
                raise InvalidSegmentationRequest(
                    "point prompt coordinate is outside the source image"
                )
            if isinstance(label, bool) or not isinstance(label, int) or label not in {0, 1}:
                raise InvalidSegmentationRequest("point labels must be 0 or 1")
            normalized_points.append([x, y])
            normalized_labels.append(label)
        return PromptEvidence(
            PromptKind.POINT, {"points": normalized_points, "labels": normalized_labels}
        )
    if request.prompt.kind is PromptKind.BOX:
        raw_box = data.get("box")
        if not isinstance(raw_box, Sequence) or isinstance(raw_box, (str, bytes)):
            values = [data.get(name) for name in ("x", "y", "width", "height")]
        else:
            values = list(raw_box)
        if len(values) != 4:
            raise InvalidSegmentationRequest("box prompt requires x, y, width and height")
        x, y, width, height = (
            _finite(value, f"box.{name}")
            for value, name in zip(values, ("x", "y", "width", "height"), strict=True)
        )
        if (
            width <= 0
            or height <= 0
            or x < 0
            or y < 0
            or x + width > request.source_width
            or y + height > request.source_height
        ):
            raise InvalidSegmentationRequest("box prompt is outside the source image")
        return PromptEvidence(
            PromptKind.BOX,
            {"box": [x, y, x + width, y + height], "format": "xyxy"},
        )
    raise InvalidSegmentationRequest("unsupported prompt mode")


def _normalize_prediction(
    prediction: SAM21Prediction, request: SegmentationRequest
) -> tuple[MaskRaster, CoordinateTransform]:
    score = _finite(prediction.score, "confidence")
    if not 0 <= score <= 1:
        raise SAM21RuntimeError("confidence must be between 0 and 1")
    values = _to_nested_values(prediction.mask)
    if not values:
        raise SAM21RuntimeError("model returned an empty mask")
    if values and not isinstance(values[0], Sequence):
        raise SAM21RuntimeError("model returned a non-matrix mask")
    if values and values[0] and isinstance(values[0][0], Sequence):
        values = values[0]
    height = len(values)
    width = len(values[0]) if height else 0
    if width <= 0 or any(not isinstance(row, Sequence) or len(row) != width for row in values):
        raise SAM21RuntimeError("model returned a malformed mask")
    transform = prediction.transform
    if (transform.source_width, transform.source_height) != (
        request.source_width,
        request.source_height,
    ):
        raise SAM21RuntimeError("prediction transform source dimensions do not match request")
    if (width, height) != (transform.model_width, transform.model_height):
        raise SAM21RuntimeError("model output dimensions do not match its transform")
    if (width, height) != (request.source_width, request.source_height):
        raise SAM21RuntimeError("resized model output requires an explicit source-grid transform")
    flattened: list[bool] = []
    for row in values:
        for value in row:
            number = _mask_value(value)
            flattened.append(number > 0.5)
    return MaskRaster(width, height, tuple(flattened)), transform


def _to_nested_values(value: object) -> list[Any]:
    current = value
    for method in ("detach", "cpu", "numpy", "tolist"):
        candidate = getattr(current, method, None)
        if callable(candidate):
            current = candidate()
    if isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
        return list(current)
    raise SAM21RuntimeError("model output is not a sequence")


def _single_score(scores: object) -> float:
    values = _to_nested_values(scores)
    if not values:
        raise SAM21RuntimeError("model returned no confidence score")
    return _finite(values[0], "confidence")


def _finite(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InvalidSegmentationRequest(f"{field_name} must be finite")
    return float(value)


def _mask_value(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    return _finite(value, "mask value")
