"""Backend-neutral reconstruction domain contract owned by PackLab."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, runtime_checkable


class ReconstructionBackendId(StrEnum):
    COLMAP_OPENMVS = "colmap-openmvs"


class ReconstructionCapability(StrEnum):
    CAMERA_PRIORS = "camera-priors"
    SPARSE = "sparse"
    DENSE = "dense"
    MESH = "mesh"
    TEXTURE = "texture"


class ScaleState(StrEnum):
    RELATIVE = "relative"
    METRIC_UNVERIFIED = "metric-unverified"
    METRIC_VERIFIED = "metric-verified"


class CameraPriorUse(StrEnum):
    IGNORED = "ignored"
    INITIALIZATION_ONLY = "initialization-only"
    FIXED = "fixed"
    REFINED = "refined"
    REJECTED = "rejected"


class StageStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _relative_asset_id(value: str) -> str:
    normalized = value.replace("\\", "/")
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:/", normalized)
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise ValueError("portable asset IDs must be non-empty relative paths")
    return normalized


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class CameraPrior:
    image_asset_id: str
    width: int | None = None
    height: int | None = None
    intrinsics: tuple[float, ...] | None = None
    pose: tuple[float, ...] | None = None
    use: CameraPriorUse = CameraPriorUse.INITIALIZATION_ONLY
    reason: str = ""

    @classmethod
    def missing(cls, image_asset_id: str, reason: str = "camera prior unavailable") -> CameraPrior:
        return cls(image_asset_id, use=CameraPriorUse.REJECTED, reason=reason)

    @property
    def valid(self) -> bool:
        return (
            bool(self.image_asset_id)
            and (self.width is None or self.width > 0)
            and (self.height is None or self.height > 0)
            and (self.intrinsics is None or all(value > 0 for value in self.intrinsics))
            and (self.pose is None or len(self.pose) in {7, 12, 16})
            and self.use is not CameraPriorUse.REJECTED
        )

    def rejected(self, reason: str) -> CameraPrior:
        return CameraPrior(
            self.image_asset_id,
            self.width,
            self.height,
            self.intrinsics,
            self.pose,
            CameraPriorUse.REJECTED,
            reason,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "image_asset_id": self.image_asset_id,
            "width": self.width,
            "height": self.height,
            "intrinsics": None if self.intrinsics is None else list(self.intrinsics),
            "pose": None if self.pose is None else list(self.pose),
            "use": self.use.value,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ReconstructionInputSet:
    project_id: str
    raw_capture_asset_id: str
    source_revision: str
    source_digest: str
    image_asset_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _relative_asset_id(self.raw_capture_asset_id)
        if not self.project_id or not self.source_revision or not re.fullmatch(r"[0-9a-f]{64}", self.source_digest):
            raise ValueError("reconstruction input identity is invalid")
        if not self.image_asset_ids:
            raise ValueError("at least one source image is required")
        for image in self.image_asset_ids:
            _relative_asset_id(image)

    def as_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "raw_capture_asset_id": self.raw_capture_asset_id,
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "image_asset_ids": list(self.image_asset_ids),
        }


@dataclass(frozen=True, slots=True)
class CameraPriorAssessment:
    priors: tuple[CameraPrior, ...]
    warnings: tuple[str, ...]


def assess_camera_priors(
    inputs: ReconstructionInputSet,
    provided: Mapping[str, CameraPrior] | Sequence[CameraPrior],
) -> CameraPriorAssessment:
    supplied = (
        dict(provided)
        if isinstance(provided, Mapping)
        else {prior.image_asset_id: prior for prior in provided}
    )
    resolved: list[CameraPrior] = []
    warnings: list[str] = []
    for image in inputs.image_asset_ids:
        prior = supplied.get(image)
        if prior is None:
            resolved.append(CameraPrior.missing(image))
            warnings.append(f"missing camera prior: {image}")
        elif not prior.valid:
            resolved.append(prior.rejected("camera prior invalid; backend must solve without it"))
            warnings.append(f"invalid camera prior rejected: {image}")
        else:
            resolved.append(prior)
    return CameraPriorAssessment(tuple(resolved), tuple(warnings))


@dataclass(frozen=True, slots=True)
class ReconstructionJobSpec:
    job_id: str
    project_id: str
    project_revision: int
    inputs: ReconstructionInputSet
    backend_id: ReconstructionBackendId
    configuration: Mapping[str, object] = field(default_factory=dict)
    camera_priors: tuple[CameraPrior, ...] = ()
    requested_capabilities: tuple[ReconstructionCapability, ...] = (
        ReconstructionCapability.SPARSE,
        ReconstructionCapability.DENSE,
        ReconstructionCapability.MESH,
    )

    def __post_init__(self) -> None:
        if not self.job_id or self.project_revision < 0 or self.project_id != self.inputs.project_id:
            raise ValueError("reconstruction job identity is invalid")
        object.__setattr__(self, "configuration", dict(self.configuration))
        object.__setattr__(self, "camera_priors", tuple(self.camera_priors))
        object.__setattr__(self, "requested_capabilities", tuple(self.requested_capabilities))

    def assess_camera_priors(self) -> CameraPriorAssessment:
        return assess_camera_priors(self.inputs, self.camera_priors)

    @property
    def configuration_digest(self) -> str:
        return _digest(self.configuration)


@dataclass(frozen=True, slots=True)
class CapabilityReport:
    backend_id: ReconstructionBackendId
    available: bool
    capabilities: tuple[ReconstructionCapability, ...]
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BackendProvenance:
    backend_id: ReconstructionBackendId
    version: str
    build: str
    license_record: str
    executable_hashes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "executable_hashes", dict(self.executable_hashes))


@dataclass(frozen=True, slots=True)
class PreparedJob:
    spec: ReconstructionJobSpec
    camera_priors: CameraPriorAssessment


class CancelToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True, slots=True)
class ReconstructionStageResult:
    stage_id: str
    status: StageStatus
    exit_code: int | None
    duration_seconds: float
    stdout: str = ""
    stderr: str = ""
    cancelled: bool = False
    failure_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "stage_id": self.stage_id,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "cancelled": self.cancelled,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True, slots=True)
class CameraSolution:
    image_asset_id: str
    registered: bool
    convention: str
    rotation: tuple[float, ...] = ()
    translation: tuple[float, ...] = ()
    reprojection_error: float | None = None
    prior_use: CameraPriorUse = CameraPriorUse.REJECTED

    def as_dict(self) -> dict[str, object]:
        return {
            "image_asset_id": self.image_asset_id,
            "registered": self.registered,
            "convention": self.convention,
            "rotation": list(self.rotation),
            "translation": list(self.translation),
            "reprojection_error": self.reprojection_error,
            "prior_use": self.prior_use.value,
        }


@dataclass(frozen=True, slots=True)
class ReconstructionOutputManifest:
    project_id: str
    reconstruction_revision: str
    backend_id: ReconstructionBackendId
    backend_version: str
    backend_build: str
    backend_license: str
    configuration_digest: str
    source_input_digest: str
    camera_convention: str
    cameras: tuple[CameraSolution, ...] = ()
    asset_paths: Mapping[str, str] = field(default_factory=dict)
    point_count: int = 0
    triangle_count: int = 0
    scale_state: ScaleState = ScaleState.RELATIVE
    limitations: tuple[str, ...] = ()
    stage_results: tuple[ReconstructionStageResult, ...] = ()
    authority_class: str = "RECONSTRUCTION_OBSERVATION"

    def __post_init__(self) -> None:
        if self.scale_state is ScaleState.METRIC_VERIFIED:
            raise ValueError("M07 cannot produce METRIC_VERIFIED; M09 owns metric promotion")
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_input_digest):
            raise ValueError("manifest source digest is invalid")
        if self.point_count < 0 or self.triangle_count < 0:
            raise ValueError("geometry counts cannot be negative")
        for value in self.asset_paths.values():
            _relative_asset_id(value)
        object.__setattr__(self, "asset_paths", dict(self.asset_paths))
        object.__setattr__(self, "cameras", tuple(self.cameras))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        object.__setattr__(self, "stage_results", tuple(self.stage_results))

    def as_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "reconstruction_revision": self.reconstruction_revision,
            "backend_id": self.backend_id.value,
            "backend_version": self.backend_version,
            "backend_build": self.backend_build,
            "backend_license": self.backend_license,
            "configuration_digest": self.configuration_digest,
            "source_input_digest": self.source_input_digest,
            "camera_convention": self.camera_convention,
            "cameras": [camera.as_dict() for camera in self.cameras],
            "asset_paths": self.asset_paths,
            "point_count": self.point_count,
            "triangle_count": self.triangle_count,
            "scale_state": self.scale_state.value,
            "limitations": list(self.limitations),
            "stage_results": [stage.as_dict() for stage in self.stage_results],
            "authority_class": self.authority_class,
        }


@dataclass(frozen=True, slots=True)
class ReconstructionRun:
    prepared: PreparedJob
    status: RunStatus
    stage_results: tuple[ReconstructionStageResult, ...]
    output: ReconstructionOutputManifest | None = None


@runtime_checkable
class ReconstructionBackend(Protocol):
    def probe(self) -> CapabilityReport: ...

    def prepare(self, job: ReconstructionJobSpec) -> PreparedJob: ...

    def execute(self, prepared: PreparedJob, cancel: CancelToken) -> ReconstructionRun: ...

    def collect(self, run: ReconstructionRun) -> ReconstructionOutputManifest: ...

    def provenance(self) -> BackendProvenance: ...
