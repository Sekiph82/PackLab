"""VGGT integration boundary for experimental PackLab reconstruction.

This module contains no VGGT import, checkpoint loader, network access, or
model runtime. A separately reviewed runtime may be injected only after its
checkpoint and licensing/deployment record is complete.
"""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from .neural_reconstruction_io import (
    NeuralReconstructionIOError,
    VGGTImagePreprocessTransform,
    VGGTOutputArtifact,
    VGGTResolvedImage,
    normalize_vggt_camera,
    publish_vggt_artifacts,
    resolve_vggt_image_assets,
)
from .reconstruction import (
    PACKSCAN_CAMERA_CONVENTION,
    BackendProvenance,
    CameraSolution,
    CancelToken,
    CapabilityReport,
    PreparedJob,
    ReconstructionBackend,
    ReconstructionBackendId,
    ReconstructionCapability,
    ReconstructionJobSpec,
    ReconstructionOutputManifest,
    ReconstructionRun,
    ReconstructionStageResult,
    RunStatus,
    ScaleState,
    StageStatus,
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_EVIDENCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
_LICENSE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+_-]{0,63}\Z")
VGGT_COMMERCIAL_CHECKPOINT = "facebook/VGGT-1B-Commercial"
VGGT_COMMERCIAL_REPOSITORY_REVISION = "ebb29a532abe92960eeb6903a5530f16990ef4ab"
VGGT_COMMERCIAL_CHECKPOINT_SIZE_BYTES = 5_026_367_224
VGGT_COMMERCIAL_CHECKPOINT_SHA256 = (
    "2b766b284359bc47ce26be107254621f685b758a0282082ff109f3ff02788b53"
)
_AUTHORITY_CLASS = "RECONSTRUCTION_OBSERVATION"
_ADAPTER_VERSION = "vggt-adapter-contract-v1"


@dataclass(frozen=True, slots=True)
class VGGTActivationRecord:
    """Portable evidence needed before a real VGGT runtime can be activated."""

    checkpoint_id: str
    checkpoint_revision: str
    checkpoint_sha256: str
    checkpoint_license_id: str
    owner_terms_accepted: bool
    owner_acceptance_ref: str
    acceptable_use_review_ref: str
    runtime_license_review_ref: str
    deployment_review_ref: str

    @property
    def complete(self) -> bool:
        refs = (
            self.checkpoint_license_id,
            self.owner_acceptance_ref,
            self.acceptable_use_review_ref,
            self.runtime_license_review_ref,
            self.deployment_review_ref,
        )
        return (
            self.checkpoint_id == VGGT_COMMERCIAL_CHECKPOINT
            and self.checkpoint_revision == VGGT_COMMERCIAL_REPOSITORY_REVISION
            and bool(_SHA256.fullmatch(self.checkpoint_sha256))
            and self.checkpoint_sha256 == VGGT_COMMERCIAL_CHECKPOINT_SHA256
            and type(self.owner_terms_accepted) is bool
            and self.owner_terms_accepted is True
            and bool(_LICENSE_ID.fullmatch(self.checkpoint_license_id))
            and all(bool(_EVIDENCE_ID.fullmatch(value)) for value in refs[1:])
        )


def _published_identity(activation: VGGTActivationRecord | None) -> tuple[str, str]:
    """Build/licence strings for manifests; placeholders only without an activation."""
    if activation is None:
        return "injected-runtime", "configured-vggt-checkpoint"
    return (
        f"{activation.checkpoint_id}@{activation.checkpoint_revision}"
        f"#sha256:{activation.checkpoint_sha256}",
        activation.checkpoint_license_id,
    )


class VGGTInferenceRuntime(Protocol):
    """Injected adapter; implementations own image decoding and VGGT calls."""

    def available(self) -> bool: ...

    def execute(
        self, prepared: PreparedJob, cancel: CancelToken
    ) -> ReconstructionOutputManifest: ...


@dataclass(frozen=True, slots=True)
class VGGTWorkspaceCamera:
    """Raw camera prediction and the exact image preprocessing transform."""

    image_asset_id: str
    world_to_camera_opencv: tuple[float, ...]
    intrinsics_vggt_pixels: tuple[float, ...]
    transform: VGGTImagePreprocessTransform


@dataclass(frozen=True, slots=True)
class VGGTWorkspaceInference:
    """Small metadata result returned by an injected engine after inference."""

    reconstruction_revision: str
    cameras: tuple[VGGTWorkspaceCamera, ...]
    artifacts: tuple[VGGTOutputArtifact, ...]
    point_count: int
    triangle_count: int = 0
    scale_state: ScaleState = ScaleState.RELATIVE
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cameras", tuple(self.cameras))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "limitations", tuple(self.limitations))


class VGGTWorkspaceEngine(Protocol):
    """Injected runtime engine. This module never imports or constructs VGGT."""

    def available(self) -> bool: ...

    def infer(
        self,
        images: tuple[VGGTResolvedImage, ...],
        cancel: CancelToken,
    ) -> VGGTWorkspaceInference: ...


class VGGTWorkspaceRuntime:
    """Wire verified PackLab inputs and outputs around an injected inference engine."""

    def __init__(
        self,
        project_root: str | Path,
        expected_sha256: Mapping[str, str],
        runtime_output_root: str | Path,
        engine: VGGTWorkspaceEngine,
        *,
        activation: VGGTActivationRecord,
    ) -> None:
        # Required (re-review V02): without it the published manifest.json would carry
        # placeholder identity while the backend reports the real one.
        if not isinstance(activation, VGGTActivationRecord) or not activation.complete:
            raise ValueError("VGGT workspace runtime activation record is incomplete")
        # When supplied, the published manifest.json carries the real checkpoint identity
        # and licence instead of placeholders (review P2, PL-0436).
        self._activation = activation
        self._project_root = Path(project_root)
        self._expected_sha256 = dict(expected_sha256)
        self._runtime_output_root = Path(runtime_output_root)
        self._engine = engine

    @property
    def activation(self) -> VGGTActivationRecord | None:
        return self._activation

    def available(self) -> bool:
        return (
            self._project_root.is_dir()
            and self._runtime_output_root.is_dir()
            and self._engine.available()
        )

    @staticmethod
    def _cancelled_manifest(prepared: PreparedJob) -> ReconstructionOutputManifest:
        return ReconstructionOutputManifest(
            prepared.spec.project_id,
            "cancelled",
            ReconstructionBackendId.NEURAL_EXPERIMENTAL,
            _ADAPTER_VERSION,
            "injected-runtime",
            "configured-vggt-checkpoint",
            prepared.spec.configuration_digest,
            prepared.spec.inputs.source_digest,
            PACKSCAN_CAMERA_CONVENTION,
            scale_state=ScaleState.RELATIVE,
            authority_class=_AUTHORITY_CLASS,
        )

    def execute(self, prepared: PreparedJob, cancel: CancelToken) -> ReconstructionOutputManifest:
        if cancel.cancelled:
            return self._cancelled_manifest(prepared)
        images = resolve_vggt_image_assets(
            prepared.spec.inputs,
            self._project_root,
            self._expected_sha256,
        )
        inference = self._engine.infer(images, cancel)
        try:
            return self._publish_inference(prepared, cancel, images, inference)
        finally:
            self._cleanup_owned_runtime_artifacts(inference)

    def _publish_inference(self, prepared, cancel, images, inference):
        if cancel.cancelled:
            return self._cancelled_manifest(prepared)
        if not isinstance(inference, VGGTWorkspaceInference):
            raise NeuralReconstructionIOError("injected VGGT engine returned an invalid result")
        image_ids = tuple(image.asset_id for image in images)
        camera_ids = tuple(camera.image_asset_id for camera in inference.cameras)
        if camera_ids != image_ids:
            raise NeuralReconstructionIOError(
                "injected VGGT camera records must exactly match ordered input images"
            )
        if (
            isinstance(inference.point_count, bool)
            or not isinstance(inference.point_count, int)
            or inference.point_count < 0
            or isinstance(inference.triangle_count, bool)
            or not isinstance(inference.triangle_count, int)
            or inference.triangle_count < 0
            or not isinstance(inference.scale_state, ScaleState)
            or inference.scale_state is ScaleState.METRIC_VERIFIED
        ):
            raise NeuralReconstructionIOError("injected VGGT geometry metadata is invalid")

        normalized = tuple(
            normalize_vggt_camera(
                camera.image_asset_id,
                camera.world_to_camera_opencv,
                camera.intrinsics_vggt_pixels,
                camera.transform,
            )
            for camera in inference.cameras
        )
        solutions = tuple(
            CameraSolution(
                camera.image_asset_id,
                True,
                camera.camera_convention,
                tuple(camera.camera_to_world[index] for index in (0, 1, 2, 4, 5, 6, 8, 9, 10)),
                tuple(camera.camera_to_world[index] for index in (3, 7, 11)),
            )
            for camera in normalized
        )
        if any(artifact.name == "camera_parameters" for artifact in inference.artifacts):
            raise NeuralReconstructionIOError("runtime artifact collides with camera metadata")
        camera_metadata = {
            "contract": "packlab.vggt-camera-parameters.v1",
            "camera_convention": PACKSCAN_CAMERA_CONVENTION,
            "cameras": [
                {
                    "image_asset_id": camera.image_asset_id,
                    "width": camera.width,
                    "height": camera.height,
                    "intrinsics": list(camera.intrinsics),
                    "camera_to_world": list(camera.camera_to_world),
                }
                for camera in normalized
            ],
        }
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="ascii",
                newline="\n",
                prefix=".packlab-vggt-cameras-",
                suffix=".json",
                dir=self._runtime_output_root,
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                json.dump(
                    camera_metadata,
                    handle,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                    allow_nan=False,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            if cancel.cancelled:
                return self._cancelled_manifest(prepared)
            build, license_id = _published_identity(self._activation)
            base_manifest = ReconstructionOutputManifest(
                prepared.spec.project_id,
                inference.reconstruction_revision,
                ReconstructionBackendId.NEURAL_EXPERIMENTAL,
                _ADAPTER_VERSION,
                build,
                license_id,
                prepared.spec.configuration_digest,
                prepared.spec.inputs.source_digest,
                PACKSCAN_CAMERA_CONVENTION,
                cameras=solutions,
                point_count=inference.point_count,
                triangle_count=inference.triangle_count,
                scale_state=inference.scale_state,
                limitations=inference.limitations,
                authority_class=_AUTHORITY_CLASS,
            )
            publication = publish_vggt_artifacts(
                self._project_root,
                inference.reconstruction_revision,
                base_manifest,
                self._runtime_output_root,
                (
                    *inference.artifacts,
                    VGGTOutputArtifact("camera_parameters", "cameras.json", temp_path),
                ),
            )
            return publication.manifest
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def _cleanup_owned_runtime_artifacts(self, inference) -> None:
        artifacts = getattr(inference, "artifacts", ())
        try:
            root = self._runtime_output_root.resolve(strict=True)
        except (OSError, RuntimeError, TypeError):
            return
        for artifact in artifacts:
            if getattr(artifact, "cleanup_after_publish", False) is not True:
                continue
            path = getattr(artifact, "source_path", None)
            if not isinstance(path, Path) or not path.is_absolute():
                continue
            try:
                relative = path.relative_to(root)
                if any(part in {"", ".", ".."} for part in relative.parts):
                    continue
                current = root
                safe = True
                for part in relative.parts:
                    current = current / part
                    metadata = current.lstat()
                    attributes = getattr(metadata, "st_file_attributes", 0)
                    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
                    if current.is_symlink() or (reparse and attributes & reparse):
                        safe = False
                        break
                if safe and stat.S_ISREG(current.lstat().st_mode):
                    current.unlink()
            except (OSError, RuntimeError, ValueError):
                continue


class VGGTReconstructionBackend(ReconstructionBackend):
    """Fail-closed PackLab adapter contract for the specified VGGT checkpoint."""

    def __init__(
        self,
        activation: VGGTActivationRecord | None = None,
        runtime: VGGTInferenceRuntime | None = None,
    ) -> None:
        self._activation = activation
        self._runtime = runtime

    def probe(self) -> CapabilityReport:
        if not self._activation or not self._activation.complete:
            return CapabilityReport(
                ReconstructionBackendId.NEURAL_EXPERIMENTAL,
                False,
                (),
                ("VGGT checkpoint/license/runtime/deployment activation record incomplete",),
            )
        if self._runtime is None:
            return CapabilityReport(
                ReconstructionBackendId.NEURAL_EXPERIMENTAL,
                False,
                (),
                ("VGGT inference runtime is not installed or injected",),
            )
        try:
            available = self._runtime.available()
        except Exception as error:  # Never expose runtime details or local paths.
            return CapabilityReport(
                ReconstructionBackendId.NEURAL_EXPERIMENTAL,
                False,
                (),
                (f"VGGT runtime probe failed ({type(error).__name__})",),
            )
        return CapabilityReport(
            ReconstructionBackendId.NEURAL_EXPERIMENTAL,
            available,
            (ReconstructionCapability.SPARSE, ReconstructionCapability.DENSE) if available else (),
            () if available else ("VGGT runtime reports required hardware unavailable",),
        )

    def prepare(self, job: ReconstructionJobSpec) -> PreparedJob:
        if job.backend_id is not ReconstructionBackendId.NEURAL_EXPERIMENTAL:
            raise ValueError("VGGT backend cannot prepare a job for another backend")
        return PreparedJob(job, job.assess_camera_priors())

    def execute(self, prepared: PreparedJob, cancel: CancelToken) -> ReconstructionRun:
        if prepared.spec.backend_id is not ReconstructionBackendId.NEURAL_EXPERIMENTAL:
            raise ValueError("VGGT backend cannot execute a job for another backend")
        if cancel.cancelled:
            stage = ReconstructionStageResult(
                "vggt-inference", StageStatus.CANCELLED, None, 0.0, cancelled=True
            )
            return ReconstructionRun(prepared, RunStatus.CANCELLED, (stage,))
        capability = self.probe()
        if not capability.available or self._runtime is None:
            reason = capability.limitations[0] if capability.limitations else "VGGT unavailable"
            stage = ReconstructionStageResult(
                "vggt-inference", StageStatus.FAILED, None, 0.0, failure_reason=reason
            )
            return ReconstructionRun(prepared, RunStatus.FAILED, (stage,))
        try:
            output = self._runtime.execute(prepared, cancel)
            if cancel.cancelled:
                stage = ReconstructionStageResult(
                    "vggt-inference", StageStatus.CANCELLED, None, 0.0, cancelled=True
                )
                return ReconstructionRun(prepared, RunStatus.CANCELLED, (stage,))
            if (
                output.backend_id is not ReconstructionBackendId.NEURAL_EXPERIMENTAL
                or output.source_input_digest != prepared.spec.inputs.source_digest
                or output.project_id != prepared.spec.project_id
                or output.scale_state is ScaleState.METRIC_VERIFIED
            ):
                raise ValueError("runtime output violated normalized reconstruction contract")
            activation = self._activation
            if activation is None or not activation.complete:
                raise ValueError("VGGT activation record became incomplete")
            expected_build, expected_license = _published_identity(activation)
            # The workspace runtime writes manifest.json to disk; with an activation it must
            # have written exactly this identity, so the saved and returned manifests agree.
            # Other injected runtimes report untrusted metadata, which is overwritten below.
            if isinstance(self._runtime, VGGTWorkspaceRuntime) and (
                self._runtime.activation is not None
                and (output.backend_build, output.backend_license)
                != (expected_build, expected_license)
            ):
                raise ValueError("published manifest identity differs from the activation record")
            output = replace(
                output,
                backend_version=_ADAPTER_VERSION,
                backend_build=expected_build,
                backend_license=expected_license,
                authority_class=_AUTHORITY_CLASS,
            )
        except Exception as error:
            stage = ReconstructionStageResult(
                "vggt-inference",
                StageStatus.FAILED,
                None,
                0.0,
                failure_reason=f"VGGT inference failed ({type(error).__name__})",
            )
            return ReconstructionRun(prepared, RunStatus.FAILED, (stage,))
        stage = ReconstructionStageResult("vggt-inference", StageStatus.SUCCEEDED, 0, 0.0)
        return ReconstructionRun(prepared, RunStatus.SUCCEEDED, (stage,), output)

    def collect(self, run: ReconstructionRun) -> ReconstructionOutputManifest:
        if run.prepared.spec.backend_id is not ReconstructionBackendId.NEURAL_EXPERIMENTAL:
            raise ValueError("VGGT backend cannot collect a job for another backend")
        if run.status is not RunStatus.SUCCEEDED or run.output is None:
            raise RuntimeError("VGGT run has no successful normalized output")
        return run.output

    def provenance(self) -> BackendProvenance:
        activation = self._activation
        if activation is None or not activation.complete:
            return BackendProvenance(
                ReconstructionBackendId.NEURAL_EXPERIMENTAL,
                _ADAPTER_VERSION,
                "checkpoint-unconfigured",
                "activation-gate-incomplete",
                {},
            )
        return BackendProvenance(
            ReconstructionBackendId.NEURAL_EXPERIMENTAL,
            _ADAPTER_VERSION,
            f"{activation.checkpoint_id}@{activation.checkpoint_revision}"
            f"#sha256:{activation.checkpoint_sha256}",
            activation.checkpoint_license_id,
            {"checkpoint": activation.checkpoint_sha256},
        )
