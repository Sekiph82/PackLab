"""PackLab-owned OpenMVS dense point-cloud stage boundary.

This module deliberately stops at one bounded ``DensifyPointCloud`` stage.  It
does not discover or install OpenMVS, materialize an ``.mvs`` file, parse
engine output as geometry, or grant Scan Master/metric authority.
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
from .openmvs_conversion import OpenMVSSceneConversionPlan
from .reconstruction import ReconstructionStageResult, RunStatus, ScaleState, StageStatus
from .reconstruction_process import run_reconstruction_stage

OPENMVS_ENGINE_ID = "openmvs"
OPENMVS_ENGINE_VERSION = "2.4.0"
DENSE_RECONSTRUCTION_CONTRACT = "packlab.dense-reconstruction.v1"
DENSE_POINT_CLOUD_STAGE_ID = "dense-point-cloud"
DENSE_RECONSTRUCTION_STAGE_ID = DENSE_POINT_CLOUD_STAGE_ID
DEFAULT_DENSE_OUTPUT_ASSET_ID = "working/reconstruction/openmvs/dense"
RECONSTRUCTION_AUTHORITY_CLASS = "RECONSTRUCTION_OBSERVATION"

_HEX_DIGEST = re.compile(r"[0-9a-f]{64}\\Z")
_CONTROL = re.compile(r"[\\x00-\\x1f\\x7f]")
_SAFE_REVISION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\\Z")
_DENSE_PROBE_IDS = frozenset({OPENMVS_ENGINE_ID, "openmvs.DensifyPointCloud"})


class DenseReconstructionError(ValueError):
    """Base error for invalid or unsafe dense-stage values."""


class InvalidDenseReconstructionRequest(DenseReconstructionError):
    """Raised when a dense-stage request is incomplete or unsafe."""


class UnsupportedDenseReconstructionOption(DenseReconstructionError):
    """Raised when a value is outside the PackLab dense-stage contract."""


class DenseReconstructionStageStatus(StrEnum):
    """Status names exposed by the dense-stage result boundary."""

    SUCCEEDED = StageStatus.SUCCEEDED.value
    FAILED = StageStatus.FAILED.value
    CANCELLED = StageStatus.CANCELLED.value


def _asset_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise InvalidDenseReconstructionRequest(
            f"{field_name} must be a non-empty relative PackLab asset ID"
        )
    if _CONTROL.search(value) or "\\" in value or value.startswith("/"):
        raise InvalidDenseReconstructionRequest(f"{field_name} must use safe relative syntax")
    if re.match(r"^[A-Za-z]:", value) or value.startswith("//"):
        raise InvalidDenseReconstructionRequest(f"{field_name} must be repository-relative")
    if any(part in {"", ".", ".."} for part in value.split("/")) or ":" in value:
        raise InvalidDenseReconstructionRequest(f"{field_name} contains an unsafe path component")
    return value


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _HEX_DIGEST.fullmatch(value) is None:
        raise InvalidDenseReconstructionRequest(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InvalidDenseReconstructionRequest(
            f"{field_name} must be an integer greater than or equal to {minimum}"
        )
    return value


def _finite_float(value: object, field_name: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidDenseReconstructionRequest(f"{field_name} must be a finite number")
    converted = float(value)
    if not math.isfinite(converted) or converted < minimum:
        raise InvalidDenseReconstructionRequest(
            f"{field_name} must be a finite number greater than or equal to {minimum}"
        )
    return converted


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DensePointCloudConfig:
    """PackLab-owned semantic settings mapped at the OpenMVS boundary.

    These fields are the supported, typed subset of the pinned
    ``DensifyPointCloud`` command.  Raw CLI options, config-file paths and
    arbitrary engine settings are intentionally not representable here.
    """

    dense_output_asset_id: str = DEFAULT_DENSE_OUTPUT_ASSET_ID
    resolution_level: int = 1
    max_resolution: int = 2560
    min_resolution: int = 640
    sub_resolution_levels: int = 2
    number_views: int = 5
    number_views_fuse: int = 2
    iters: int = 3
    geometric_iters: int = 2
    estimate_colors: int = 2
    estimate_normals: int = 2
    fusion_filter: int = 2
    fusion_depth_diff_threshold: float = 0.01
    fusion_reprojection_threshold: float = 1.2
    postprocess_dmaps: int = 0
    scale_state: ScaleState = ScaleState.RELATIVE

    def __post_init__(self) -> None:
        _asset_id(self.dense_output_asset_id, "dense_output_asset_id")
        _integer(self.resolution_level, "resolution_level")
        _integer(self.max_resolution, "max_resolution", minimum=1)
        _integer(self.min_resolution, "min_resolution", minimum=1)
        if self.min_resolution > self.max_resolution:
            raise InvalidDenseReconstructionRequest("min_resolution cannot exceed max_resolution")
        for field_name in (
            "sub_resolution_levels",
            "number_views",
            "number_views_fuse",
            "iters",
            "geometric_iters",
            "estimate_colors",
            "estimate_normals",
            "fusion_filter",
            "postprocess_dmaps",
        ):
            _integer(getattr(self, field_name), field_name)
        _finite_float(
            self.fusion_depth_diff_threshold,
            "fusion_depth_diff_threshold",
        )
        _finite_float(
            self.fusion_reprojection_threshold,
            "fusion_reprojection_threshold",
        )
        if self.scale_state is ScaleState.METRIC_VERIFIED:
            raise UnsupportedDenseReconstructionOption(
                "dense reconstruction cannot claim METRIC_VERIFIED"
            )
        if not isinstance(self.scale_state, ScaleState):
            raise InvalidDenseReconstructionRequest("scale_state must be a ScaleState")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": DENSE_RECONSTRUCTION_CONTRACT,
            "dense_output_asset_id": self.dense_output_asset_id,
            "resolution_level": self.resolution_level,
            "max_resolution": self.max_resolution,
            "min_resolution": self.min_resolution,
            "sub_resolution_levels": self.sub_resolution_levels,
            "number_views": self.number_views,
            "number_views_fuse": self.number_views_fuse,
            "iters": self.iters,
            "geometric_iters": self.geometric_iters,
            "estimate_colors": self.estimate_colors,
            "estimate_normals": self.estimate_normals,
            "fusion_filter": self.fusion_filter,
            "fusion_depth_diff_threshold": self.fusion_depth_diff_threshold,
            "fusion_reprojection_threshold": self.fusion_reprojection_threshold,
            "postprocess_dmaps": self.postprocess_dmaps,
            "scale_state": self.scale_state.value,
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
    def from_overrides(cls, overrides: Mapping[str, object] | None = None) -> DensePointCloudConfig:
        if overrides is None:
            return cls()
        if not isinstance(overrides, Mapping):
            raise InvalidDenseReconstructionRequest(
                "dense configuration overrides must be a mapping"
            )
        allowed = frozenset(cls.__dataclass_fields__)
        unknown = [key for key in overrides if key not in allowed]
        if unknown:
            raise UnsupportedDenseReconstructionOption(
                f"unsupported dense configuration option: {unknown[0]!r}"
            )
        return cls(**cast(dict[str, Any], dict(overrides)))

    def with_overrides(
        self, overrides: Mapping[str, object] | None = None
    ) -> DensePointCloudConfig:
        if overrides is None:
            return self
        if not isinstance(overrides, Mapping):
            raise InvalidDenseReconstructionRequest(
                "dense configuration overrides must be a mapping"
            )
        allowed = frozenset(self.__dataclass_fields__)
        unknown = [key for key in overrides if key not in allowed]
        if unknown:
            raise UnsupportedDenseReconstructionOption(
                f"unsupported dense configuration option: {unknown[0]!r}"
            )
        return replace(self, **cast(dict[str, Any], dict(overrides)))


@dataclass(frozen=True, slots=True)
class DensePointCloudRequest:
    """Immutable dense-stage request derived from one conversion plan."""

    conversion_plan: OpenMVSSceneConversionPlan
    configuration: DensePointCloudConfig = DensePointCloudConfig()
    engine_id: str = OPENMVS_ENGINE_ID
    engine_version: str = OPENMVS_ENGINE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.conversion_plan, OpenMVSSceneConversionPlan):
            raise InvalidDenseReconstructionRequest(
                "conversion_plan must be an OpenMVSSceneConversionPlan"
            )
        if not isinstance(self.configuration, DensePointCloudConfig):
            raise InvalidDenseReconstructionRequest("configuration must be DensePointCloudConfig")
        if self.engine_id != OPENMVS_ENGINE_ID:
            raise UnsupportedDenseReconstructionOption(
                f"only the PackLab OpenMVS adapter is supported, not {self.engine_id!r}"
            )
        if self.engine_version != OPENMVS_ENGINE_VERSION:
            raise UnsupportedDenseReconstructionOption(
                f"only OpenMVS {OPENMVS_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )
        if self.input_scene_asset_id == self.configuration.dense_output_asset_id:
            raise InvalidDenseReconstructionRequest(
                "dense output asset must differ from the conversion-plan scene asset"
            )

    @classmethod
    def from_conversion_plan(
        cls,
        conversion_plan: OpenMVSSceneConversionPlan,
        configuration: DensePointCloudConfig | None = None,
    ) -> DensePointCloudRequest:
        return cls(
            conversion_plan, DensePointCloudConfig() if configuration is None else configuration
        )

    @property
    def input_scene_asset_id(self) -> str:
        return self.conversion_plan.output_scene_asset_id

    @property
    def source_revision(self) -> str:
        return self.conversion_plan.source_revision

    @property
    def source_digest(self) -> str:
        return self.conversion_plan.source_digest

    @property
    def conversion_plan_digest(self) -> str:
        return self.conversion_plan.digest

    @property
    def plan_digest(self) -> str:
        return self.conversion_plan_digest

    @property
    def configuration_digest(self) -> str:
        return self.configuration.configuration_digest

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": DENSE_RECONSTRUCTION_CONTRACT,
            "input_scene_asset_id": self.input_scene_asset_id,
            "dense_output_asset_id": self.configuration.dense_output_asset_id,
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "conversion_plan_digest": self.conversion_plan_digest,
            "configuration_digest": self.configuration_digest,
            "configuration": self.configuration.as_dict(),
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
            "authority_class": RECONSTRUCTION_AUTHORITY_CLASS,
            "scale_state": self.configuration.scale_state.value,
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


def _portable_executable(value: str | Path) -> str:
    executable = str(value)
    if not executable.strip() or "\x00" in executable:
        raise InvalidDenseReconstructionRequest("an explicit OpenMVS dense executable is required")
    return executable


def _probe_matches(executable: str, probe: EngineProbeResult) -> None:
    if not isinstance(probe, EngineProbeResult):
        raise UnsupportedDenseReconstructionOption("an explicit OpenMVS dense probe is required")
    if probe.engine_id not in _DENSE_PROBE_IDS:
        raise UnsupportedDenseReconstructionOption(
            "the supplied probe is not for OpenMVS DensifyPointCloud"
        )
    if probe.status is not EngineProbeStatus.VALID:
        raise UnsupportedDenseReconstructionOption(
            "OpenMVS DensifyPointCloud must be explicitly probed and version-valid"
        )
    if probe.version is None or probe.version.text != OPENMVS_ENGINE_VERSION:
        raise UnsupportedDenseReconstructionOption(
            f"only probed OpenMVS {OPENMVS_ENGINE_VERSION} is supported"
        )
    if probe.executable is None:
        raise UnsupportedDenseReconstructionOption("the OpenMVS probe has no executable identity")
    if Path(probe.executable).as_posix().lower() != Path(executable).as_posix().lower():
        raise UnsupportedDenseReconstructionOption(
            "probed OpenMVS dense executable does not match request"
        )


@dataclass(frozen=True, slots=True)
class OpenMVSDensePointCloudAdapter:
    """Command and execution adapter for pinned OpenMVS densification."""

    engine_version: str = OPENMVS_ENGINE_VERSION

    def build_command(
        self,
        request: DensePointCloudRequest,
        executable: str | Path,
    ) -> tuple[str, ...]:
        if not isinstance(request, DensePointCloudRequest):
            raise InvalidDenseReconstructionRequest("request must be DensePointCloudRequest")
        if self.engine_version != OPENMVS_ENGINE_VERSION:
            raise UnsupportedDenseReconstructionOption(
                f"only OpenMVS {OPENMVS_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )
        if request.engine_version != self.engine_version:
            raise UnsupportedDenseReconstructionOption("request and adapter engine versions differ")
        command = _portable_executable(executable)
        config = request.configuration
        return (
            command,
            "--input-file",
            request.input_scene_asset_id,
            "--output-file",
            config.dense_output_asset_id,
            "--resolution-level",
            str(config.resolution_level),
            "--max-resolution",
            str(config.max_resolution),
            "--min-resolution",
            str(config.min_resolution),
            "--sub-resolution-levels",
            str(config.sub_resolution_levels),
            "--number-views",
            str(config.number_views),
            "--number-views-fuse",
            str(config.number_views_fuse),
            "--iters",
            str(config.iters),
            "--geometric-iters",
            str(config.geometric_iters),
            "--estimate-colors",
            str(config.estimate_colors),
            "--estimate-normals",
            str(config.estimate_normals),
            "--fusion-filter",
            str(config.fusion_filter),
            "--fusion-depth-diff-threshold",
            str(config.fusion_depth_diff_threshold),
            "--fusion-reprojection-threshold",
            str(config.fusion_reprojection_threshold),
            "--postprocess-dmaps",
            str(config.postprocess_dmaps),
        )

    def execute(
        self,
        request: DensePointCloudRequest,
        executable: str | Path,
        probe: EngineProbeResult,
        *,
        timeout: float | None = None,
        cancel_event: threading.Event | None = None,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
    ) -> DensePointCloudRun:
        command = self.build_command(request, executable)
        _probe_matches(command[0], probe)
        stage_result = stage_runner(
            DENSE_POINT_CLOUD_STAGE_ID,
            command,
            timeout=timeout,
            cancel_event=cancel_event,
            cwd=cwd,
            env=env,
        )
        if not isinstance(stage_result, ReconstructionStageResult):
            raise DenseReconstructionError("stage runner must return ReconstructionStageResult")
        return normalize_dense_reconstruction_result(request, stage_result)


def _stage_result_contract_error(stage_result: ReconstructionStageResult) -> str | None:
    if stage_result.stage_id != DENSE_POINT_CLOUD_STAGE_ID:
        return "dense point-cloud stage result has an unexpected stage ID"
    if stage_result.status is StageStatus.SUCCEEDED:
        if stage_result.cancelled:
            return "a successful dense stage cannot be cancelled"
        if stage_result.exit_code != 0:
            return "a successful dense stage requires exit code zero"
    elif stage_result.status is StageStatus.FAILED:
        if stage_result.cancelled:
            return "a failed dense stage cannot be marked cancelled"
    elif stage_result.status is StageStatus.CANCELLED:
        if not stage_result.cancelled:
            return "a cancelled dense stage must be marked cancelled"
    else:
        return "unknown reconstruction stage status"
    return None


def _failed_stage_result(
    result: ReconstructionStageResult, reason: str
) -> ReconstructionStageResult:
    return ReconstructionStageResult(
        stage_id=DENSE_POINT_CLOUD_STAGE_ID,
        status=StageStatus.FAILED,
        exit_code=result.exit_code,
        duration_seconds=result.duration_seconds,
        stdout=result.stdout,
        stderr=result.stderr,
        cancelled=False,
        failure_reason=reason,
    )


@dataclass(frozen=True, slots=True)
class DensePointCloudRun:
    """Immutable dense-stage result with output only on a valid success."""

    request: DensePointCloudRequest
    status: RunStatus
    stage_result: ReconstructionStageResult
    dense_output_asset_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, DensePointCloudRequest):
            raise DenseReconstructionError("dense run requires a DensePointCloudRequest")
        if not isinstance(self.stage_result, ReconstructionStageResult):
            raise DenseReconstructionError("dense run requires a reconstruction stage result")
        if not isinstance(self.status, RunStatus):
            raise DenseReconstructionError("dense run has an unknown run status")
        stage_error = _stage_result_contract_error(self.stage_result)
        if stage_error is not None:
            raise DenseReconstructionError(stage_error)
        if self.status is RunStatus.SUCCEEDED:
            if self.stage_result.status is not StageStatus.SUCCEEDED:
                raise DenseReconstructionError("successful dense run requires a successful stage")
            if self.dense_output_asset_id is None:
                raise DenseReconstructionError("successful dense run requires an output identity")
            if _asset_id(self.dense_output_asset_id, "dense_output_asset_id") != (
                self.request.configuration.dense_output_asset_id
            ):
                raise DenseReconstructionError(
                    "successful dense output identity does not match request"
                )
        elif self.status is RunStatus.FAILED:
            if self.stage_result.status is not StageStatus.FAILED:
                raise DenseReconstructionError("failed dense run requires a failed stage")
            if self.dense_output_asset_id is not None:
                raise DenseReconstructionError("failed dense run cannot expose output")
        elif self.status is RunStatus.CANCELLED:
            if self.stage_result.status is not StageStatus.CANCELLED:
                raise DenseReconstructionError("cancelled dense run requires a cancelled stage")
            if self.dense_output_asset_id is not None:
                raise DenseReconstructionError("cancelled dense run cannot expose output")

    @property
    def source_digest(self) -> str:
        return self.request.source_digest

    @property
    def plan_digest(self) -> str:
        return self.request.plan_digest

    @property
    def configuration_digest(self) -> str:
        return self.request.configuration_digest

    @property
    def authority_class(self) -> str:
        return RECONSTRUCTION_AUTHORITY_CLASS

    @property
    def scale_state(self) -> ScaleState:
        return self.request.configuration.scale_state

    @property
    def limitations(self) -> tuple[str, ...]:
        return (
            "Dense output is RECONSTRUCTION_OBSERVATION derived from captured evidence.",
            "Dense output is not Scan Master, CAD, measurement, or engineering authority.",
            "Metric verification remains a later M09 contract.",
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": DENSE_RECONSTRUCTION_CONTRACT,
            "request": self.request.as_dict(),
            "status": self.status.value,
            "stage_result": self.stage_result.as_dict(),
            "dense_output_asset_id": self.dense_output_asset_id,
            "source_digest": self.source_digest,
            "plan_digest": self.plan_digest,
            "configuration_digest": self.configuration_digest,
            "authority_class": self.authority_class,
            "scale_state": self.scale_state.value,
            "limitations": list(self.limitations),
        }


def normalize_dense_reconstruction_result(
    request: DensePointCloudRequest,
    stage_result: ReconstructionStageResult,
) -> DensePointCloudRun:
    """Normalize one stage result without inferring geometry from its output."""

    if not isinstance(stage_result, ReconstructionStageResult):
        raise DenseReconstructionError("stage runner must return ReconstructionStageResult")
    stage_error = _stage_result_contract_error(stage_result)
    if stage_error is not None:
        return DensePointCloudRun(
            request,
            RunStatus.FAILED,
            _failed_stage_result(stage_result, stage_error),
        )
    if stage_result.status is StageStatus.CANCELLED:
        return DensePointCloudRun(request, RunStatus.CANCELLED, stage_result)
    if stage_result.status is StageStatus.FAILED:
        return DensePointCloudRun(request, RunStatus.FAILED, stage_result)
    return DensePointCloudRun(
        request,
        RunStatus.SUCCEEDED,
        stage_result,
        request.configuration.dense_output_asset_id,
    )


def build_openmvs_dense_command(
    request: DensePointCloudRequest,
    executable: str | Path,
) -> tuple[str, ...]:
    """Build the pinned DensifyPointCloud argv without executing it."""

    return OpenMVSDensePointCloudAdapter().build_command(request, executable)


def execute_openmvs_dense(
    request: DensePointCloudRequest,
    executable: str | Path,
    probe: EngineProbeResult,
    *,
    timeout: float | None = None,
    cancel_event: threading.Event | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
) -> DensePointCloudRun:
    """Execute only an explicitly supplied, already-probed dense executable."""

    return OpenMVSDensePointCloudAdapter().execute(
        request,
        executable,
        probe,
        timeout=timeout,
        cancel_event=cancel_event,
        cwd=cwd,
        env=env,
        stage_runner=stage_runner,
    )


run_dense_reconstruction = execute_openmvs_dense
build_dense_point_cloud_command = build_openmvs_dense_command
DenseReconstructionConfig = DensePointCloudConfig
DenseReconstructionRequest = DensePointCloudRequest
DenseReconstructionRun = DensePointCloudRun
OpenMVSDenseAdapter = OpenMVSDensePointCloudAdapter


__all__ = [
    "DEFAULT_DENSE_OUTPUT_ASSET_ID",
    "DENSE_POINT_CLOUD_STAGE_ID",
    "DENSE_RECONSTRUCTION_CONTRACT",
    "DENSE_RECONSTRUCTION_STAGE_ID",
    "DensePointCloudConfig",
    "DensePointCloudRequest",
    "DensePointCloudRun",
    "DenseReconstructionConfig",
    "DenseReconstructionError",
    "DenseReconstructionRequest",
    "DenseReconstructionRun",
    "DenseReconstructionStageStatus",
    "InvalidDenseReconstructionRequest",
    "OPENMVS_ENGINE_ID",
    "OPENMVS_ENGINE_VERSION",
    "OpenMVSDenseAdapter",
    "OpenMVSDensePointCloudAdapter",
    "UnsupportedDenseReconstructionOption",
    "build_dense_point_cloud_command",
    "build_openmvs_dense_command",
    "execute_openmvs_dense",
    "normalize_dense_reconstruction_result",
    "run_dense_reconstruction",
]
