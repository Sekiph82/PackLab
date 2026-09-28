"""PackLab-owned OpenMVS mesh-refinement stage boundary.

This module deliberately stops at one bounded ``ReconstructMesh`` cleaning
stage. It does not materialize or parse meshes, preserve engine output files,
discover or install OpenMVS, or grant Scan Master, metric, CAD, measurement,
or engineering authority.
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

from .engine_probe import EngineProbeResult, EngineProbeStatus
from .mesh_reconstruction import MeshReconstructionRun
from .reconstruction import ReconstructionStageResult, RunStatus, ScaleState, StageStatus
from .reconstruction_process import run_reconstruction_stage

OPENMVS_ENGINE_ID = "openmvs"
OPENMVS_ENGINE_VERSION = "2.4.0"
OPENMVS_RECONSTRUCT_MESH_PROBE_ID = "openmvs.ReconstructMesh"
MESH_REFINEMENT_CONTRACT = "packlab.mesh-refinement.v1"
MESH_REFINEMENT_STAGE_ID = "mesh-refinement"
OPENMVS_MESH_REFINEMENT_STAGE_ID = MESH_REFINEMENT_STAGE_ID
DEFAULT_REFINED_MESH_OUTPUT_ASSET_ID = "working/reconstruction/openmvs/mesh-refined"
RECONSTRUCTION_AUTHORITY_CLASS = "RECONSTRUCTION_OBSERVATION"

_HEX_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_PRIVATE_SEGMENTS = frozenset({"private", "secret", "secrets"})
_ALLOWED_SCALES = frozenset({ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED})


class MeshRefinementError(ValueError):
    """Base error for invalid or unsafe mesh-refinement values."""


class InvalidMeshRefinementRequest(MeshRefinementError):
    """Raised when a refinement request is incomplete or unsafe."""


class UnsupportedMeshRefinementOption(MeshRefinementError):
    """Raised when a value is outside the pinned refinement contract."""


class MeshRefinementStageStatus(StrEnum):
    """Status names exposed by the mesh-refinement result boundary."""

    SUCCEEDED = StageStatus.SUCCEEDED.value
    FAILED = StageStatus.FAILED.value
    CANCELLED = StageStatus.CANCELLED.value


def _asset_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise InvalidMeshRefinementRequest(
            f"{field_name} must be a non-empty relative PackLab asset ID"
        )
    if _CONTROL.search(value) or "\\" in value or value.startswith("/"):
        raise InvalidMeshRefinementRequest(f"{field_name} must use safe relative syntax")
    if re.match(r"^[A-Za-z]:", value) or value.startswith("//") or ":" in value:
        raise InvalidMeshRefinementRequest(f"{field_name} must be repository-relative")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise InvalidMeshRefinementRequest(f"{field_name} contains an unsafe path component")
    if any(part.lower() in _PRIVATE_SEGMENTS for part in parts):
        raise InvalidMeshRefinementRequest(f"{field_name} cannot target a private path")
    return value


def _finite_float(value: object, field_name: str, *, minimum: float | None = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidMeshRefinementRequest(f"{field_name} must be a finite number")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as exc:
        raise InvalidMeshRefinementRequest(f"{field_name} must be a finite number") from exc
    if not math.isfinite(converted) or (minimum is not None and converted < minimum):
        if minimum is None:
            detail = "finite"
        else:
            detail = f"finite and greater than or equal to {minimum}"
        raise InvalidMeshRefinementRequest(f"{field_name} must be {detail}")
    return converted


def _decimate(value: object) -> float:
    parsed = _finite_float(value, "decimate", minimum=None)
    if parsed <= 0 or parsed > 1:
        raise UnsupportedMeshRefinementOption("decimate must be in the pinned OpenMVS range (0, 1]")
    return parsed


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidMeshRefinementRequest(
            f"{field_name} must be a non-negative integer excluding booleans"
        )
    return value


def _boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidMeshRefinementRequest(f"{field_name} must be a strict boolean")
    return value


def _portable_executable(value: str | Path) -> str:
    executable = str(value)
    if not executable.strip() or "\x00" in executable:
        raise InvalidMeshRefinementRequest(
            "an explicit OpenMVS ReconstructMesh executable is required"
        )
    return executable


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class MeshRefinementConfig:
    """Immutable semantic settings for the pinned OpenMVS clean options."""

    refined_mesh_output_asset_id: str = DEFAULT_REFINED_MESH_OUTPUT_ASSET_ID
    decimate: float = 1.0
    target_face_num: int = 0
    remove_spurious: float = 20.0
    remove_spikes: bool = True
    close_holes: int = 30
    smooth: int = 2
    edge_length: float = 0.0
    roi_border: float = 0.0
    crop_to_roi: bool = True

    def __post_init__(self) -> None:
        _asset_id(self.refined_mesh_output_asset_id, "refined_mesh_output_asset_id")
        _decimate(self.decimate)
        _integer(self.target_face_num, "target_face_num")
        _finite_float(self.remove_spurious, "remove_spurious")
        _boolean(self.remove_spikes, "remove_spikes")
        _integer(self.close_holes, "close_holes")
        _integer(self.smooth, "smooth")
        _finite_float(self.edge_length, "edge_length")
        _finite_float(self.roi_border, "roi_border", minimum=None)
        _boolean(self.crop_to_roi, "crop_to_roi")

    @property
    def output_asset_id(self) -> str:
        return self.refined_mesh_output_asset_id

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": MESH_REFINEMENT_CONTRACT,
            "refined_mesh_output_asset_id": self.refined_mesh_output_asset_id,
            "decimate": self.decimate,
            "target_face_num": self.target_face_num,
            "remove_spurious": self.remove_spurious,
            "remove_spikes": self.remove_spikes,
            "close_holes": self.close_holes,
            "smooth": self.smooth,
            "edge_length": self.edge_length,
            "roi_border": self.roi_border,
            "crop_to_roi": self.crop_to_roi,
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
    def from_overrides(cls, overrides: Mapping[str, object] | None = None) -> MeshRefinementConfig:
        if overrides is None:
            return cls()
        if not isinstance(overrides, Mapping):
            raise InvalidMeshRefinementRequest("mesh refinement overrides must be a mapping")
        allowed = frozenset(cls.__dataclass_fields__)
        unknown = [key for key in overrides if key not in allowed]
        if unknown:
            raise UnsupportedMeshRefinementOption(
                f"unsupported mesh refinement option: {unknown[0]!r}"
            )
        return cls(**cast(dict[str, Any], dict(overrides)))

    def with_overrides(self, overrides: Mapping[str, object] | None = None) -> MeshRefinementConfig:
        if overrides is None:
            return self
        if not isinstance(overrides, Mapping):
            raise InvalidMeshRefinementRequest("mesh refinement overrides must be a mapping")
        allowed = frozenset(self.__dataclass_fields__)
        unknown = [key for key in overrides if key not in allowed]
        if unknown:
            raise UnsupportedMeshRefinementOption(
                f"unsupported mesh refinement option: {unknown[0]!r}"
            )
        return replace(self, **cast(dict[str, Any], dict(overrides)))


@dataclass(frozen=True, slots=True)
class MeshRefinementRequest:
    """Immutable refinement request derived from one successful mesh run."""

    mesh_run: MeshReconstructionRun
    configuration: MeshRefinementConfig = MeshRefinementConfig()
    engine_id: str = OPENMVS_ENGINE_ID
    engine_version: str = OPENMVS_ENGINE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.mesh_run, MeshReconstructionRun):
            raise InvalidMeshRefinementRequest("mesh_run must be a MeshReconstructionRun")
        if self.mesh_run.status is not RunStatus.SUCCEEDED:
            raise InvalidMeshRefinementRequest("mesh refinement requires one successful mesh run")
        if self.mesh_run.stage_result.status is not StageStatus.SUCCEEDED:
            raise InvalidMeshRefinementRequest(
                "mesh refinement requires a successful mesh-stage result"
            )
        if self.mesh_run.mesh_output_asset_id is None:
            raise InvalidMeshRefinementRequest(
                "successful mesh run must expose an input asset identity"
            )
        _asset_id(self.mesh_run.mesh_output_asset_id, "mesh_output_asset_id")
        if not isinstance(self.configuration, MeshRefinementConfig):
            raise InvalidMeshRefinementRequest("configuration must be MeshRefinementConfig")
        if self.mesh_run.authority_class != RECONSTRUCTION_AUTHORITY_CLASS:
            raise UnsupportedMeshRefinementOption(
                "mesh refinement requires RECONSTRUCTION_OBSERVATION authority"
            )
        if self.engine_id != OPENMVS_ENGINE_ID:
            raise UnsupportedMeshRefinementOption(
                f"only the PackLab OpenMVS adapter is supported, not {self.engine_id!r}"
            )
        if self.engine_version != OPENMVS_ENGINE_VERSION:
            raise UnsupportedMeshRefinementOption(
                f"only OpenMVS {OPENMVS_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )
        if self.scale_state not in _ALLOWED_SCALES:
            raise UnsupportedMeshRefinementOption("mesh refinement cannot claim METRIC_VERIFIED")
        if self.input_mesh_asset_id == self.configuration.output_asset_id:
            raise InvalidMeshRefinementRequest(
                "refined mesh output asset must differ from the predecessor mesh asset"
            )

    @classmethod
    def from_mesh_run(
        cls,
        mesh_run: MeshReconstructionRun,
        configuration: MeshRefinementConfig | None = None,
    ) -> MeshRefinementRequest:
        return cls(mesh_run, MeshRefinementConfig() if configuration is None else configuration)

    from_mesh_result = from_mesh_run

    @property
    def input_mesh_asset_id(self) -> str:
        assert self.mesh_run.mesh_output_asset_id is not None
        return self.mesh_run.mesh_output_asset_id

    @property
    def input_asset_id(self) -> str:
        return self.input_mesh_asset_id

    @property
    def output_asset_id(self) -> str:
        return self.configuration.output_asset_id

    @property
    def refined_mesh_output_asset_id(self) -> str:
        return self.output_asset_id

    @property
    def source_revision(self) -> str:
        return self.mesh_run.request.source_revision

    @property
    def source_digest(self) -> str:
        return self.mesh_run.source_digest

    @property
    def plan_digest(self) -> str:
        return self.mesh_run.plan_digest

    @property
    def dense_request_digest(self) -> str:
        return self.mesh_run.dense_request_digest

    @property
    def mesh_configuration_digest(self) -> str:
        return self.mesh_run.configuration_digest

    @property
    def mesh_request_digest(self) -> str:
        return self.mesh_run.request_digest

    @property
    def configuration_digest(self) -> str:
        return self.configuration.configuration_digest

    @property
    def scale_state(self) -> ScaleState:
        return self.mesh_run.scale_state

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": MESH_REFINEMENT_CONTRACT,
            "input_mesh_asset_id": self.input_mesh_asset_id,
            "refined_mesh_output_asset_id": self.refined_mesh_output_asset_id,
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "plan_digest": self.plan_digest,
            "dense_request_digest": self.dense_request_digest,
            "mesh_configuration_digest": self.mesh_configuration_digest,
            "mesh_request_digest": self.mesh_request_digest,
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
        raise UnsupportedMeshRefinementOption(
            "an explicit OpenMVS ReconstructMesh probe is required"
        )
    if probe.engine_id != OPENMVS_RECONSTRUCT_MESH_PROBE_ID:
        raise UnsupportedMeshRefinementOption(
            "the supplied probe is not for OpenMVS ReconstructMesh"
        )
    if probe.status is not EngineProbeStatus.VALID:
        raise UnsupportedMeshRefinementOption(
            "OpenMVS ReconstructMesh must be explicitly probed and version-valid"
        )
    if probe.version is None or probe.version.text != OPENMVS_ENGINE_VERSION:
        raise UnsupportedMeshRefinementOption(
            f"only probed OpenMVS {OPENMVS_ENGINE_VERSION} is supported"
        )
    if probe.executable is None:
        raise UnsupportedMeshRefinementOption(
            "the OpenMVS ReconstructMesh probe has no executable identity"
        )
    if Path(probe.executable).as_posix().lower() != Path(executable).as_posix().lower():
        raise UnsupportedMeshRefinementOption(
            "probed OpenMVS ReconstructMesh executable does not match request"
        )


def _bool_argument(value: bool) -> str:
    return "1" if value else "0"


@dataclass(frozen=True, slots=True)
class OpenMVSMeshRefinementAdapter:
    """Command and execution adapter for pinned OpenMVS mesh cleaning."""

    engine_version: str = OPENMVS_ENGINE_VERSION

    def build_command(
        self,
        request: MeshRefinementRequest,
        executable: str | Path,
    ) -> tuple[str, ...]:
        if not isinstance(request, MeshRefinementRequest):
            raise InvalidMeshRefinementRequest("request must be MeshRefinementRequest")
        if self.engine_version != OPENMVS_ENGINE_VERSION:
            raise UnsupportedMeshRefinementOption(
                f"only OpenMVS {OPENMVS_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )
        if request.engine_version != self.engine_version:
            raise UnsupportedMeshRefinementOption("request and adapter engine versions differ")
        command = _portable_executable(executable)
        config = request.configuration
        return (
            command,
            "--mesh-file",
            request.input_mesh_asset_id,
            "--output-file",
            config.output_asset_id,
            "--decimate",
            str(config.decimate),
            "--target-face-num",
            str(config.target_face_num),
            "--remove-spurious",
            str(config.remove_spurious),
            "--remove-spikes",
            _bool_argument(config.remove_spikes),
            "--close-holes",
            str(config.close_holes),
            "--smooth",
            str(config.smooth),
            "--edge-length",
            str(config.edge_length),
            "--roi-border",
            str(config.roi_border),
            "--crop-to-roi",
            _bool_argument(config.crop_to_roi),
        )

    def execute(
        self,
        request: MeshRefinementRequest,
        executable: str | Path,
        probe: EngineProbeResult,
        *,
        timeout: float | None = None,
        cancel_event: threading.Event | None = None,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
    ) -> MeshRefinementRun:
        command = self.build_command(request, executable)
        _probe_matches(command[0], probe)
        stage_result = stage_runner(
            MESH_REFINEMENT_STAGE_ID,
            command,
            timeout=timeout,
            cancel_event=cancel_event,
            cwd=cwd,
            env=env,
        )
        if not isinstance(stage_result, ReconstructionStageResult):
            raise MeshRefinementError("stage runner must return ReconstructionStageResult")
        return normalize_mesh_refinement_result(request, stage_result)


def _stage_result_contract_error(stage_result: ReconstructionStageResult) -> str | None:
    if stage_result.stage_id != MESH_REFINEMENT_STAGE_ID:
        return "mesh refinement stage result has an unexpected stage ID"
    if not isinstance(stage_result.status, StageStatus):
        return "mesh refinement stage result has an unknown status"
    if not isinstance(stage_result.cancelled, bool):
        return "mesh refinement stage result cancellation flag must be a boolean"
    if isinstance(stage_result.exit_code, bool) or not (
        stage_result.exit_code is None or isinstance(stage_result.exit_code, int)
    ):
        return "mesh refinement stage result has an invalid exit code"
    if (
        isinstance(stage_result.duration_seconds, bool)
        or not isinstance(stage_result.duration_seconds, (int, float))
        or not math.isfinite(float(stage_result.duration_seconds))
        or stage_result.duration_seconds < 0
    ):
        return "mesh refinement stage result has an invalid duration"
    if not isinstance(stage_result.stdout, str) or not isinstance(stage_result.stderr, str):
        return "mesh refinement stage result output must be text"
    if stage_result.status is StageStatus.SUCCEEDED:
        if stage_result.cancelled:
            return "a successful mesh refinement stage cannot be cancelled"
        if stage_result.exit_code != 0:
            return "a successful mesh refinement stage requires exit code zero"
    elif stage_result.status is StageStatus.FAILED:
        if stage_result.cancelled:
            return "a failed mesh refinement stage cannot be marked cancelled"
        if stage_result.exit_code == 0:
            return "a failed mesh refinement stage cannot have exit code zero"
    elif stage_result.status is StageStatus.CANCELLED:
        if not stage_result.cancelled:
            return "a cancelled mesh refinement stage must be marked cancelled"
        if stage_result.exit_code == 0:
            return "a cancelled mesh refinement stage cannot have exit code zero"
    return None


def _failed_stage_result(
    result: ReconstructionStageResult, reason: str
) -> ReconstructionStageResult:
    exit_code = result.exit_code if isinstance(result.exit_code, int) else None
    if isinstance(exit_code, bool) or exit_code == 0:
        exit_code = None
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
        stage_id=MESH_REFINEMENT_STAGE_ID,
        status=StageStatus.FAILED,
        exit_code=exit_code,
        duration_seconds=duration,
        stdout=stdout,
        stderr=stderr,
        cancelled=False,
        failure_reason=reason,
    )


@dataclass(frozen=True, slots=True)
class MeshRefinementRun:
    """Immutable refinement result with output only on coherent success."""

    request: MeshRefinementRequest
    status: RunStatus
    stage_result: ReconstructionStageResult
    refined_mesh_output_asset_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, MeshRefinementRequest):
            raise MeshRefinementError("mesh refinement run requires a MeshRefinementRequest")
        if not isinstance(self.stage_result, ReconstructionStageResult):
            raise MeshRefinementError("mesh refinement run requires a reconstruction stage result")
        if not isinstance(self.status, RunStatus):
            raise MeshRefinementError("mesh refinement run has an unknown run status")
        stage_error = _stage_result_contract_error(self.stage_result)
        if stage_error is not None:
            raise MeshRefinementError(stage_error)
        if self.status is RunStatus.SUCCEEDED:
            if self.stage_result.status is not StageStatus.SUCCEEDED:
                raise MeshRefinementError(
                    "successful mesh refinement run requires a successful stage"
                )
            if self.refined_mesh_output_asset_id is None:
                raise MeshRefinementError(
                    "successful mesh refinement run requires an output identity"
                )
            if _asset_id(self.refined_mesh_output_asset_id, "refined_mesh_output_asset_id") != (
                self.request.configuration.output_asset_id
            ):
                raise MeshRefinementError(
                    "successful refined mesh output identity does not match request"
                )
        elif self.status is RunStatus.FAILED:
            if self.stage_result.status is not StageStatus.FAILED:
                raise MeshRefinementError("failed mesh refinement run requires a failed stage")
            if self.refined_mesh_output_asset_id is not None:
                raise MeshRefinementError("failed mesh refinement run cannot expose output")
        elif self.status is RunStatus.CANCELLED:
            if self.stage_result.status is not StageStatus.CANCELLED:
                raise MeshRefinementError(
                    "cancelled mesh refinement run requires a cancelled stage"
                )
            if self.refined_mesh_output_asset_id is not None:
                raise MeshRefinementError("cancelled mesh refinement run cannot expose output")

    @property
    def output_asset_id(self) -> str | None:
        return self.refined_mesh_output_asset_id

    @property
    def source_revision(self) -> str:
        return self.request.source_revision

    @property
    def source_digest(self) -> str:
        return self.request.source_digest

    @property
    def plan_digest(self) -> str:
        return self.request.plan_digest

    @property
    def dense_request_digest(self) -> str:
        return self.request.dense_request_digest

    @property
    def mesh_configuration_digest(self) -> str:
        return self.request.mesh_configuration_digest

    @property
    def mesh_request_digest(self) -> str:
        return self.request.mesh_request_digest

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
            "Refined mesh output is RECONSTRUCTION_OBSERVATION derived from a successful mesh observation.",
            "Refined mesh output is not Scan Master, CAD, measurement, or engineering authority.",
            "This boundary does not parse meshes, infer quality, or claim metric verification.",
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": MESH_REFINEMENT_CONTRACT,
            "request": self.request.as_dict(),
            "status": self.status.value,
            "stage_result": self.stage_result.as_dict(),
            "refined_mesh_output_asset_id": self.refined_mesh_output_asset_id,
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "plan_digest": self.plan_digest,
            "dense_request_digest": self.dense_request_digest,
            "mesh_configuration_digest": self.mesh_configuration_digest,
            "mesh_request_digest": self.mesh_request_digest,
            "configuration_digest": self.configuration_digest,
            "request_digest": self.request_digest,
            "authority_class": self.authority_class,
            "scale_state": self.scale_state.value,
            "limitations": list(self.limitations),
        }


def normalize_mesh_refinement_result(
    request: MeshRefinementRequest,
    stage_result: ReconstructionStageResult,
) -> MeshRefinementRun:
    """Normalize one stage result without interpreting engine output as geometry."""

    if not isinstance(request, MeshRefinementRequest):
        raise MeshRefinementError("request must be MeshRefinementRequest")
    if not isinstance(stage_result, ReconstructionStageResult):
        raise MeshRefinementError("stage runner must return ReconstructionStageResult")
    stage_error = _stage_result_contract_error(stage_result)
    if stage_error is not None:
        return MeshRefinementRun(
            request,
            RunStatus.FAILED,
            _failed_stage_result(stage_result, stage_error),
        )
    if stage_result.status is StageStatus.CANCELLED:
        return MeshRefinementRun(request, RunStatus.CANCELLED, stage_result)
    if stage_result.status is StageStatus.FAILED:
        return MeshRefinementRun(request, RunStatus.FAILED, stage_result)
    return MeshRefinementRun(
        request,
        RunStatus.SUCCEEDED,
        stage_result,
        request.configuration.output_asset_id,
    )


def build_openmvs_mesh_refinement_command(
    request: MeshRefinementRequest,
    executable: str | Path,
) -> tuple[str, ...]:
    """Build pinned OpenMVS refinement argv without executing it."""

    return OpenMVSMeshRefinementAdapter().build_command(request, executable)


def execute_openmvs_mesh_refinement(
    request: MeshRefinementRequest,
    executable: str | Path,
    probe: EngineProbeResult,
    *,
    timeout: float | None = None,
    cancel_event: threading.Event | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
) -> MeshRefinementRun:
    """Execute only an explicitly supplied, already-probed executable."""

    return OpenMVSMeshRefinementAdapter().execute(
        request,
        executable,
        probe,
        timeout=timeout,
        cancel_event=cancel_event,
        cwd=cwd,
        env=env,
        stage_runner=stage_runner,
    )


run_mesh_refinement = execute_openmvs_mesh_refinement
build_mesh_refinement_command = build_openmvs_mesh_refinement_command
MeshRefinementStageRequest = MeshRefinementRequest
MeshRefinementStageRun = MeshRefinementRun
OpenMVSReconstructMeshRefinementAdapter = OpenMVSMeshRefinementAdapter
OpenMVSMeshRefinementStageAdapter = OpenMVSMeshRefinementAdapter


__all__ = [
    "DEFAULT_REFINED_MESH_OUTPUT_ASSET_ID",
    "InvalidMeshRefinementRequest",
    "MESH_REFINEMENT_CONTRACT",
    "MESH_REFINEMENT_STAGE_ID",
    "MeshRefinementConfig",
    "MeshRefinementError",
    "MeshRefinementRequest",
    "MeshRefinementRun",
    "MeshRefinementStageRequest",
    "MeshRefinementStageRun",
    "MeshRefinementStageStatus",
    "OPENMVS_ENGINE_ID",
    "OPENMVS_ENGINE_VERSION",
    "OPENMVS_MESH_REFINEMENT_STAGE_ID",
    "OPENMVS_RECONSTRUCT_MESH_PROBE_ID",
    "OpenMVSReconstructMeshRefinementAdapter",
    "OpenMVSMeshRefinementAdapter",
    "OpenMVSMeshRefinementStageAdapter",
    "UnsupportedMeshRefinementOption",
    "build_mesh_refinement_command",
    "build_openmvs_mesh_refinement_command",
    "execute_openmvs_mesh_refinement",
    "normalize_mesh_refinement_result",
    "run_mesh_refinement",
]
