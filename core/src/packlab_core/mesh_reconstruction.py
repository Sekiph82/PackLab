"""PackLab-owned OpenMVS mesh-reconstruction stage boundary.

This module deliberately stops at one bounded ``ReconstructMesh`` stage.  It
does not discover or install OpenMVS, parse engine output as geometry, preserve
engine-side manifests, or grant Scan Master, metric, CAD, or engineering
authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from .dense_reconstruction import DensePointCloudRun
from .engine_probe import EngineProbeResult, EngineProbeStatus
from .reconstruction import ReconstructionStageResult, RunStatus, ScaleState, StageStatus
from .reconstruction_process import run_reconstruction_stage

OPENMVS_ENGINE_ID = "openmvs"
OPENMVS_ENGINE_VERSION = "2.4.0"
OPENMVS_RECONSTRUCT_MESH_PROBE_ID = "openmvs.ReconstructMesh"
MESH_RECONSTRUCTION_CONTRACT = "packlab.mesh-reconstruction.v1"
MESH_RECONSTRUCTION_STAGE_ID = "mesh-reconstruction"
OPENMVS_MESH_STAGE_ID = MESH_RECONSTRUCTION_STAGE_ID
DEFAULT_MESH_OUTPUT_ASSET_ID = "working/reconstruction/openmvs/mesh"
RECONSTRUCTION_AUTHORITY_CLASS = "RECONSTRUCTION_OBSERVATION"

_HEX_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_PRIVATE_SEGMENTS = frozenset({"private", "secret", "secrets"})
_MESH_PROBE_IDS = frozenset({OPENMVS_RECONSTRUCT_MESH_PROBE_ID})
_ALLOWED_SCALES = frozenset({ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED})


class MeshReconstructionError(ValueError):
    """Base error for invalid or unsafe mesh-stage values."""


class InvalidMeshReconstructionRequest(MeshReconstructionError):
    """Raised when a mesh-stage request is incomplete or unsafe."""


class UnsupportedMeshReconstructionOption(MeshReconstructionError):
    """Raised when a value is outside the PackLab mesh-stage contract."""


class MeshReconstructionStageStatus(StrEnum):
    """Status names exposed by the mesh-stage result boundary."""

    SUCCEEDED = StageStatus.SUCCEEDED.value
    FAILED = StageStatus.FAILED.value
    CANCELLED = StageStatus.CANCELLED.value


def _asset_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise InvalidMeshReconstructionRequest(
            f"{field_name} must be a non-empty relative PackLab asset ID"
        )
    if _CONTROL.search(value) or "\\" in value or value.startswith("/"):
        raise InvalidMeshReconstructionRequest(f"{field_name} must use safe relative syntax")
    if re.match(r"^[A-Za-z]:", value) or value.startswith("//") or ":" in value:
        raise InvalidMeshReconstructionRequest(f"{field_name} must be repository-relative")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise InvalidMeshReconstructionRequest(f"{field_name} contains an unsafe path component")
    if any(part.lower() in _PRIVATE_SEGMENTS for part in parts):
        raise InvalidMeshReconstructionRequest(f"{field_name} cannot target a private path")
    return value


def _finite_float(value: object, field_name: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidMeshReconstructionRequest(f"{field_name} must be a finite number")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as exc:
        raise InvalidMeshReconstructionRequest(
            f"{field_name} must be a finite number greater than or equal to {minimum}"
        ) from exc
    if not math.isfinite(converted) or converted < minimum:
        raise InvalidMeshReconstructionRequest(
            f"{field_name} must be a finite number greater than or equal to {minimum}"
        )
    return converted


def _boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidMeshReconstructionRequest(f"{field_name} must be a boolean")
    return value


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _HEX_DIGEST.fullmatch(value) is None:
        raise InvalidMeshReconstructionRequest(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _portable_executable(value: str | Path) -> str:
    executable = str(value)
    if not executable.strip() or "\x00" in executable:
        raise InvalidMeshReconstructionRequest(
            "an explicit OpenMVS ReconstructMesh executable is required"
        )
    return executable


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class MeshReconstructionConfig:
    """PackLab-owned semantic settings mapped at the OpenMVS mesh boundary."""

    mesh_output_asset_id: str = DEFAULT_MESH_OUTPUT_ASSET_ID
    min_point_distance: float = 1.5
    integrate_only_roi: bool = False
    constant_weight: bool = True
    free_space_support: bool = False
    thickness_factor: float = 1.0
    quality_factor: float = 1.0

    def __post_init__(self) -> None:
        _asset_id(self.mesh_output_asset_id, "mesh_output_asset_id")
        _finite_float(self.min_point_distance, "min_point_distance")
        _boolean(self.integrate_only_roi, "integrate_only_roi")
        _boolean(self.constant_weight, "constant_weight")
        _boolean(self.free_space_support, "free_space_support")
        _finite_float(self.thickness_factor, "thickness_factor")
        _finite_float(self.quality_factor, "quality_factor")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": MESH_RECONSTRUCTION_CONTRACT,
            "mesh_output_asset_id": self.mesh_output_asset_id,
            "min_point_distance": self.min_point_distance,
            "integrate_only_roi": self.integrate_only_roi,
            "constant_weight": self.constant_weight,
            "free_space_support": self.free_space_support,
            "thickness_factor": self.thickness_factor,
            "quality_factor": self.quality_factor,
        }

    to_dict = as_dict

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    @property
    def configuration_digest(self) -> str:
        return _canonical_digest(self.as_dict())

    @property
    def digest(self) -> str:
        return self.configuration_digest

    @classmethod
    def from_overrides(
        cls, overrides: Mapping[str, object] | None = None
    ) -> MeshReconstructionConfig:
        if overrides is None:
            return cls()
        if not isinstance(overrides, Mapping):
            raise InvalidMeshReconstructionRequest("mesh configuration overrides must be a mapping")
        allowed = frozenset(cls.__dataclass_fields__)
        unknown = [key for key in overrides if key not in allowed]
        if unknown:
            raise UnsupportedMeshReconstructionOption(
                f"unsupported mesh configuration option: {unknown[0]!r}"
            )
        return cls(**cast(dict[str, Any], dict(overrides)))

    def with_overrides(
        self, overrides: Mapping[str, object] | None = None
    ) -> MeshReconstructionConfig:
        if overrides is None:
            return self
        if not isinstance(overrides, Mapping):
            raise InvalidMeshReconstructionRequest("mesh configuration overrides must be a mapping")
        allowed = frozenset(self.__dataclass_fields__)
        unknown = [key for key in overrides if key not in allowed]
        if unknown:
            raise UnsupportedMeshReconstructionOption(
                f"unsupported mesh configuration option: {unknown[0]!r}"
            )
        return replace(self, **cast(dict[str, Any], dict(overrides)))


@dataclass(frozen=True, slots=True)
class MeshReconstructionRequest:
    """Immutable mesh request derived from one successful dense-stage run."""

    dense_run: DensePointCloudRun
    configuration: MeshReconstructionConfig = MeshReconstructionConfig()
    engine_id: str = OPENMVS_ENGINE_ID
    engine_version: str = OPENMVS_ENGINE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.dense_run, DensePointCloudRun):
            raise InvalidMeshReconstructionRequest("dense_run must be a DensePointCloudRun")
        if self.dense_run.status is not RunStatus.SUCCEEDED:
            raise InvalidMeshReconstructionRequest(
                "mesh reconstruction requires one successful dense-stage run"
            )
        if self.dense_run.stage_result.status is not StageStatus.SUCCEEDED:
            raise InvalidMeshReconstructionRequest(
                "mesh reconstruction requires a successful dense-stage result"
            )
        if self.dense_run.dense_output_asset_id is None:
            raise InvalidMeshReconstructionRequest(
                "successful dense-stage run must expose an input asset identity"
            )
        _asset_id(self.dense_run.request.input_scene_asset_id, "input_scene_asset_id")
        _asset_id(self.dense_run.dense_output_asset_id, "dense_output_asset_id")
        if not isinstance(self.configuration, MeshReconstructionConfig):
            raise InvalidMeshReconstructionRequest("configuration must be MeshReconstructionConfig")
        if self.engine_id != OPENMVS_ENGINE_ID:
            raise UnsupportedMeshReconstructionOption(
                f"only the PackLab OpenMVS adapter is supported, not {self.engine_id!r}"
            )
        if self.engine_version != OPENMVS_ENGINE_VERSION:
            raise UnsupportedMeshReconstructionOption(
                f"only OpenMVS {OPENMVS_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )
        if self.scale_state not in _ALLOWED_SCALES:
            raise UnsupportedMeshReconstructionOption(
                "mesh reconstruction cannot claim METRIC_VERIFIED"
            )
        if self.input_scene_asset_id == self.configuration.mesh_output_asset_id:
            raise InvalidMeshReconstructionRequest(
                "mesh output asset must differ from the dense scene asset"
            )
        if self.dense_point_cloud_asset_id == self.configuration.mesh_output_asset_id:
            raise InvalidMeshReconstructionRequest(
                "mesh output asset must differ from the dense point-cloud asset"
            )

    @classmethod
    def from_dense_run(
        cls,
        dense_run: DensePointCloudRun,
        configuration: MeshReconstructionConfig | None = None,
    ) -> MeshReconstructionRequest:
        return cls(
            dense_run,
            MeshReconstructionConfig() if configuration is None else configuration,
        )

    from_dense_result = from_dense_run

    @property
    def input_asset_id(self) -> str:
        return self.input_scene_asset_id

    @property
    def input_scene_asset_id(self) -> str:
        return self.dense_run.request.input_scene_asset_id

    @property
    def dense_point_cloud_asset_id(self) -> str:
        assert self.dense_run.dense_output_asset_id is not None
        return self.dense_run.dense_output_asset_id

    @property
    def dense_input_asset_id(self) -> str:
        return self.dense_point_cloud_asset_id

    @property
    def output_asset_id(self) -> str:
        return self.configuration.mesh_output_asset_id

    @property
    def source_revision(self) -> str:
        return self.dense_run.request.source_revision

    @property
    def source_digest(self) -> str:
        return self.dense_run.source_digest

    @property
    def plan_digest(self) -> str:
        return self.dense_run.plan_digest

    @property
    def dense_configuration_digest(self) -> str:
        return self.dense_run.configuration_digest

    @property
    def dense_request_digest(self) -> str:
        return self.dense_run.request.request_digest

    @property
    def configuration_digest(self) -> str:
        return self.configuration.configuration_digest

    @property
    def scale_state(self) -> ScaleState:
        return self.dense_run.scale_state

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": MESH_RECONSTRUCTION_CONTRACT,
            "input_scene_asset_id": self.input_scene_asset_id,
            "dense_input_asset_id": self.dense_input_asset_id,
            "dense_point_cloud_asset_id": self.dense_point_cloud_asset_id,
            "mesh_output_asset_id": self.output_asset_id,
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "plan_digest": self.plan_digest,
            "dense_configuration_digest": self.dense_configuration_digest,
            "dense_request_digest": self.dense_request_digest,
            "configuration_digest": self.configuration_digest,
            "configuration": self.configuration.as_dict(),
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
            "authority_class": RECONSTRUCTION_AUTHORITY_CLASS,
            "scale_state": self.scale_state.value,
        }

    to_dict = as_dict

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    @property
    def request_digest(self) -> str:
        return _canonical_digest(self.as_dict())

    @property
    def digest(self) -> str:
        return self.request_digest


def _probe_matches(executable: str, probe: EngineProbeResult) -> None:
    if not isinstance(probe, EngineProbeResult):
        raise UnsupportedMeshReconstructionOption(
            "an explicit OpenMVS ReconstructMesh probe is required"
        )
    if probe.engine_id not in _MESH_PROBE_IDS:
        raise UnsupportedMeshReconstructionOption(
            "the supplied probe is not for OpenMVS ReconstructMesh"
        )
    if probe.status is not EngineProbeStatus.VALID:
        raise UnsupportedMeshReconstructionOption(
            "OpenMVS ReconstructMesh must be explicitly probed and version-valid"
        )
    if probe.version is None or probe.version.text != OPENMVS_ENGINE_VERSION:
        raise UnsupportedMeshReconstructionOption(
            f"only probed OpenMVS {OPENMVS_ENGINE_VERSION} is supported"
        )
    if probe.executable is None:
        raise UnsupportedMeshReconstructionOption(
            "the OpenMVS ReconstructMesh probe has no executable identity"
        )
    if Path(probe.executable).as_posix().lower() != Path(executable).as_posix().lower():
        raise UnsupportedMeshReconstructionOption(
            "probed OpenMVS ReconstructMesh executable does not match request"
        )


def _bool_argument(value: bool) -> str:
    return "1" if value else "0"


@dataclass(frozen=True, slots=True)
class OpenMVSMeshReconstructionAdapter:
    """Command and execution adapter for pinned OpenMVS mesh reconstruction."""

    engine_version: str = OPENMVS_ENGINE_VERSION

    def build_command(
        self,
        request: MeshReconstructionRequest,
        executable: str | Path,
    ) -> tuple[str, ...]:
        if not isinstance(request, MeshReconstructionRequest):
            raise InvalidMeshReconstructionRequest("request must be MeshReconstructionRequest")
        if self.engine_version != OPENMVS_ENGINE_VERSION:
            raise UnsupportedMeshReconstructionOption(
                f"only OpenMVS {OPENMVS_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )
        if request.engine_version != self.engine_version:
            raise UnsupportedMeshReconstructionOption("request and adapter engine versions differ")
        command = _portable_executable(executable)
        config = request.configuration
        return (
            command,
            "--input-file",
            request.input_scene_asset_id,
            "--pointcloud-file",
            request.dense_point_cloud_asset_id,
            "--output-file",
            config.mesh_output_asset_id,
            "--min-point-distance",
            str(config.min_point_distance),
            "--integrate-only-roi",
            _bool_argument(config.integrate_only_roi),
            "--constant-weight",
            _bool_argument(config.constant_weight),
            "--free-space-support",
            _bool_argument(config.free_space_support),
            "--thickness-factor",
            str(config.thickness_factor),
            "--quality-factor",
            str(config.quality_factor),
        )

    def execute(
        self,
        request: MeshReconstructionRequest,
        executable: str | Path,
        probe: EngineProbeResult,
        *,
        timeout: float | None = None,
        cancel_event: threading.Event | None = None,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
    ) -> MeshReconstructionRun:
        command = self.build_command(request, executable)
        _probe_matches(command[0], probe)
        stage_result = stage_runner(
            MESH_RECONSTRUCTION_STAGE_ID,
            command,
            timeout=timeout,
            cancel_event=cancel_event,
            cwd=cwd,
            env=env,
        )
        if not isinstance(stage_result, ReconstructionStageResult):
            raise MeshReconstructionError("stage runner must return ReconstructionStageResult")
        return normalize_mesh_reconstruction_result(request, stage_result)


def _stage_result_contract_error(stage_result: ReconstructionStageResult) -> str | None:
    if stage_result.stage_id != MESH_RECONSTRUCTION_STAGE_ID:
        return "mesh stage result has an unexpected stage ID"
    if not isinstance(stage_result.status, StageStatus):
        return "mesh stage result has an unknown status"
    if not isinstance(stage_result.cancelled, bool):
        return "mesh stage result cancellation flag must be a boolean"
    if isinstance(stage_result.exit_code, bool) or not (
        stage_result.exit_code is None or isinstance(stage_result.exit_code, int)
    ):
        return "mesh stage result has an invalid exit code"
    if (
        isinstance(stage_result.duration_seconds, bool)
        or not isinstance(stage_result.duration_seconds, (int, float))
        or not math.isfinite(float(stage_result.duration_seconds))
        or stage_result.duration_seconds < 0
    ):
        return "mesh stage result has an invalid duration"
    if not isinstance(stage_result.stdout, str) or not isinstance(stage_result.stderr, str):
        return "mesh stage result output must be text"
    if stage_result.status is StageStatus.SUCCEEDED:
        if stage_result.cancelled:
            return "a successful mesh stage cannot be cancelled"
        if stage_result.exit_code != 0:
            return "a successful mesh stage requires exit code zero"
    elif stage_result.status is StageStatus.FAILED:
        if stage_result.cancelled:
            return "a failed mesh stage cannot be marked cancelled"
        if stage_result.exit_code == 0:
            return "a failed mesh stage cannot have exit code zero"
    elif stage_result.status is StageStatus.CANCELLED:
        if not stage_result.cancelled:
            return "a cancelled mesh stage must be marked cancelled"
        if stage_result.exit_code == 0:
            return "a cancelled mesh stage cannot have exit code zero"
    return None


def _failed_stage_result(
    result: ReconstructionStageResult, reason: str
) -> ReconstructionStageResult:
    exit_code = None if result.exit_code == 0 else result.exit_code
    duration = result.duration_seconds
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(float(duration))
        or duration < 0
    ):
        duration = 0.0
    stdout = result.stdout if isinstance(result.stdout, str) else ""
    stderr = result.stderr if isinstance(result.stderr, str) else ""
    return ReconstructionStageResult(
        stage_id=MESH_RECONSTRUCTION_STAGE_ID,
        status=StageStatus.FAILED,
        exit_code=exit_code,
        duration_seconds=duration,
        stdout=stdout,
        stderr=stderr,
        cancelled=False,
        failure_reason=reason,
    )


@dataclass(frozen=True, slots=True)
class MeshReconstructionRun:
    """Immutable mesh-stage result with output only on a valid success."""

    request: MeshReconstructionRequest
    status: RunStatus
    stage_result: ReconstructionStageResult
    mesh_output_asset_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, MeshReconstructionRequest):
            raise MeshReconstructionError("mesh run requires a MeshReconstructionRequest")
        if not isinstance(self.stage_result, ReconstructionStageResult):
            raise MeshReconstructionError("mesh run requires a reconstruction stage result")
        if not isinstance(self.status, RunStatus):
            raise MeshReconstructionError("mesh run has an unknown run status")
        stage_error = _stage_result_contract_error(self.stage_result)
        if stage_error is not None:
            raise MeshReconstructionError(stage_error)
        if self.status is RunStatus.SUCCEEDED:
            if self.stage_result.status is not StageStatus.SUCCEEDED:
                raise MeshReconstructionError("successful mesh run requires a successful stage")
            if self.mesh_output_asset_id is None:
                raise MeshReconstructionError("successful mesh run requires an output identity")
            if _asset_id(self.mesh_output_asset_id, "mesh_output_asset_id") != (
                self.request.configuration.mesh_output_asset_id
            ):
                raise MeshReconstructionError(
                    "successful mesh output identity does not match request"
                )
        elif self.status is RunStatus.FAILED:
            if self.stage_result.status is not StageStatus.FAILED:
                raise MeshReconstructionError("failed mesh run requires a failed stage")
            if self.mesh_output_asset_id is not None:
                raise MeshReconstructionError("failed mesh run cannot expose output")
        elif self.status is RunStatus.CANCELLED:
            if self.stage_result.status is not StageStatus.CANCELLED:
                raise MeshReconstructionError("cancelled mesh run requires a cancelled stage")
            if self.mesh_output_asset_id is not None:
                raise MeshReconstructionError("cancelled mesh run cannot expose output")

    @property
    def source_digest(self) -> str:
        return self.request.source_digest

    @property
    def plan_digest(self) -> str:
        return self.request.plan_digest

    @property
    def dense_configuration_digest(self) -> str:
        return self.request.dense_configuration_digest

    @property
    def dense_request_digest(self) -> str:
        return self.request.dense_request_digest

    @property
    def configuration_digest(self) -> str:
        return self.request.configuration_digest

    @property
    def request_digest(self) -> str:
        return self.request.request_digest

    @property
    def authority_class(self) -> str:
        return RECONSTRUCTION_AUTHORITY_CLASS

    @property
    def scale_state(self) -> ScaleState:
        return self.request.scale_state

    @property
    def limitations(self) -> tuple[str, ...]:
        return (
            "Mesh output is RECONSTRUCTION_OBSERVATION derived from a successful dense observation.",
            "Mesh output is not Scan Master, CAD, measurement, or engineering authority.",
            "This boundary does not infer mesh quality, geometry counts, or metric verification.",
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": MESH_RECONSTRUCTION_CONTRACT,
            "request": self.request.as_dict(),
            "status": self.status.value,
            "stage_result": self.stage_result.as_dict(),
            "mesh_output_asset_id": self.mesh_output_asset_id,
            "source_digest": self.source_digest,
            "plan_digest": self.plan_digest,
            "dense_configuration_digest": self.dense_configuration_digest,
            "dense_request_digest": self.dense_request_digest,
            "configuration_digest": self.configuration_digest,
            "request_digest": self.request_digest,
            "authority_class": self.authority_class,
            "scale_state": self.scale_state.value,
            "limitations": list(self.limitations),
        }


def normalize_mesh_reconstruction_result(
    request: MeshReconstructionRequest,
    stage_result: ReconstructionStageResult,
) -> MeshReconstructionRun:
    """Normalize one stage result without interpreting engine output as geometry."""

    if not isinstance(request, MeshReconstructionRequest):
        raise MeshReconstructionError("request must be MeshReconstructionRequest")
    if not isinstance(stage_result, ReconstructionStageResult):
        raise MeshReconstructionError("stage runner must return ReconstructionStageResult")
    stage_error = _stage_result_contract_error(stage_result)
    if stage_error is not None:
        return MeshReconstructionRun(
            request,
            RunStatus.FAILED,
            _failed_stage_result(stage_result, stage_error),
        )
    if stage_result.status is StageStatus.CANCELLED:
        return MeshReconstructionRun(request, RunStatus.CANCELLED, stage_result)
    if stage_result.status is StageStatus.FAILED:
        return MeshReconstructionRun(request, RunStatus.FAILED, stage_result)
    return MeshReconstructionRun(
        request,
        RunStatus.SUCCEEDED,
        stage_result,
        request.configuration.mesh_output_asset_id,
    )


def build_openmvs_mesh_command(
    request: MeshReconstructionRequest,
    executable: str | Path,
) -> tuple[str, ...]:
    """Build the pinned ReconstructMesh argv without executing it."""

    return OpenMVSMeshReconstructionAdapter().build_command(request, executable)


def execute_openmvs_mesh(
    request: MeshReconstructionRequest,
    executable: str | Path,
    probe: EngineProbeResult,
    *,
    timeout: float | None = None,
    cancel_event: threading.Event | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
) -> MeshReconstructionRun:
    """Execute only an explicitly supplied, already-probed mesh executable."""

    return OpenMVSMeshReconstructionAdapter().execute(
        request,
        executable,
        probe,
        timeout=timeout,
        cancel_event=cancel_event,
        cwd=cwd,
        env=env,
        stage_runner=stage_runner,
    )


run_mesh_reconstruction = execute_openmvs_mesh
build_mesh_reconstruction_command = build_openmvs_mesh_command
MeshReconstructionStageRequest = MeshReconstructionRequest
MeshReconstructionStageRun = MeshReconstructionRun
OpenMVSReconstructMeshAdapter = OpenMVSMeshReconstructionAdapter
OpenMVSMeshAdapter = OpenMVSMeshReconstructionAdapter


__all__ = [
    "DEFAULT_MESH_OUTPUT_ASSET_ID",
    "MESH_RECONSTRUCTION_CONTRACT",
    "MESH_RECONSTRUCTION_STAGE_ID",
    "OPENMVS_ENGINE_ID",
    "OPENMVS_ENGINE_VERSION",
    "OPENMVS_MESH_STAGE_ID",
    "OPENMVS_RECONSTRUCT_MESH_PROBE_ID",
    "MeshReconstructionConfig",
    "MeshReconstructionError",
    "MeshReconstructionRequest",
    "MeshReconstructionRun",
    "MeshReconstructionStageRequest",
    "MeshReconstructionStageRun",
    "MeshReconstructionStageStatus",
    "InvalidMeshReconstructionRequest",
    "OpenMVSReconstructMeshAdapter",
    "OpenMVSMeshAdapter",
    "OpenMVSMeshReconstructionAdapter",
    "UnsupportedMeshReconstructionOption",
    "build_mesh_reconstruction_command",
    "build_openmvs_mesh_command",
    "execute_openmvs_mesh",
    "normalize_mesh_reconstruction_result",
    "run_mesh_reconstruction",
]
