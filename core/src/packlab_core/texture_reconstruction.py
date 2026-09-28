"""PackLab-owned OpenMVS texture-stage boundary.

This module stops at one bounded ``TextureMesh`` stage.  It does not parse
meshes or textures, preserve engine outputs, infer texture quality, discover
or install OpenMVS, or grant Scan Master, metric, CAD, measurement, or
engineering authority.
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
from .mesh_refinement import MeshRefinementRun
from .reconstruction import ReconstructionStageResult, RunStatus, ScaleState, StageStatus
from .reconstruction_process import run_reconstruction_stage

OPENMVS_ENGINE_ID = "openmvs"
OPENMVS_ENGINE_VERSION = "2.4.0"
OPENMVS_TEXTURE_MESH_PROBE_ID = "openmvs.TextureMesh"
TEXTURE_RECONSTRUCTION_CONTRACT = "packlab.texture-reconstruction.v1"
TEXTURE_MESH_STAGE_ID = "texture-mesh"
TEXTURE_RECONSTRUCTION_STAGE_ID = TEXTURE_MESH_STAGE_ID
OPENMVS_TEXTURE_STAGE_ID = TEXTURE_MESH_STAGE_ID
OPENMVS_TEXTURE_MESH_STAGE_ID = TEXTURE_MESH_STAGE_ID
DEFAULT_TEXTURED_MESH_OUTPUT_ASSET_ID = "working/reconstruction/openmvs/mesh-textured"
RECONSTRUCTION_AUTHORITY_CLASS = "RECONSTRUCTION_OBSERVATION"

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_PRIVATE_SEGMENTS = frozenset({"private", "secret", "secrets"})
_ALLOWED_SCALES = frozenset({ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED})
_EXPORT_TYPES = frozenset({"ply", "obj", "glb", "gltf"})


class TextureReconstructionError(ValueError):
    """Base error for invalid or unsafe texture-stage values."""


class InvalidTextureReconstructionRequest(TextureReconstructionError):
    """Raised when a texture request is incomplete or unsafe."""


class UnsupportedTextureReconstructionOption(TextureReconstructionError):
    """Raised when a value is outside the pinned texture contract."""


class TextureMeshStageStatus(StrEnum):
    """Status names exposed by the texture-stage result boundary."""

    SUCCEEDED = StageStatus.SUCCEEDED.value
    FAILED = StageStatus.FAILED.value
    CANCELLED = StageStatus.CANCELLED.value


def _asset_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise InvalidTextureReconstructionRequest(
            f"{field_name} must be a non-empty relative PackLab asset ID"
        )
    if _CONTROL.search(value) or "\\" in value or value.startswith("/"):
        raise InvalidTextureReconstructionRequest(f"{field_name} must use safe relative syntax")
    if re.match(r"^[A-Za-z]:", value) or value.startswith("//") or ":" in value:
        raise InvalidTextureReconstructionRequest(f"{field_name} must be repository-relative")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise InvalidTextureReconstructionRequest(f"{field_name} contains an unsafe path component")
    if any(part.lower() in _PRIVATE_SEGMENTS for part in parts):
        raise InvalidTextureReconstructionRequest(f"{field_name} cannot target a private path")
    return value


def _finite_float(value: object, field_name: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidTextureReconstructionRequest(f"{field_name} must be a finite number")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as exc:
        raise InvalidTextureReconstructionRequest(f"{field_name} must be a finite number") from exc
    if not math.isfinite(converted) or converted < minimum:
        raise InvalidTextureReconstructionRequest(
            f"{field_name} must be finite and greater than or equal to {minimum}"
        )
    return converted


def _bounded_float(value: object, field_name: str) -> float:
    parsed = _finite_float(value, field_name)
    if parsed > 1:
        raise UnsupportedTextureReconstructionOption(
            f"{field_name} must be in the pinned range [0, 1]"
        )
    return parsed


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidTextureReconstructionRequest(
            f"{field_name} must be a non-negative integer excluding booleans"
        )
    return value


def _bounded_integer(value: object, field_name: str) -> int:
    parsed = _integer(value, field_name)
    if parsed > 100:
        raise UnsupportedTextureReconstructionOption(
            f"{field_name} must be in the pinned range [0, 100]"
        )
    return parsed


def _boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidTextureReconstructionRequest(f"{field_name} must be a strict boolean")
    return value


def _empty_color(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
        raise InvalidTextureReconstructionRequest(
            "empty_color must be a uint32 integer excluding booleans"
        )
    return value


def _ignore_mask_label(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < -2:
        raise InvalidTextureReconstructionRequest(
            "ignore_mask_label must be -2, -1, or a non-negative integer excluding booleans"
        )
    return value


def _portable_executable(value: str | Path) -> str:
    executable = str(value)
    if not executable.strip() or "\x00" in executable:
        raise InvalidTextureReconstructionRequest(
            "an explicit OpenMVS TextureMesh executable is required"
        )
    return executable


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TextureReconstructionConfig:
    """Immutable semantic settings for safe pinned TextureMesh options."""

    textured_mesh_output_asset_id: str = DEFAULT_TEXTURED_MESH_OUTPUT_ASSET_ID
    export_type: str = "ply"
    decimate: float = 1.0
    close_holes: int = 30
    resolution_level: int = 0
    min_resolution: int = 640
    virtual_face_images: int = 0
    texture_size_multiple: int = 0
    outlier_threshold: float = 0.06
    cost_smoothness_ratio: float = 0.1
    global_seam_leveling: bool = True
    local_seam_leveling: bool = True
    patch_packing_heuristic: int = 3
    empty_color: int = 0x00FF7F27
    sharpness_weight: float = 0.5
    ignore_mask_label: int = -1
    max_texture_size: int = 8192

    def __post_init__(self) -> None:
        _asset_id(self.textured_mesh_output_asset_id, "textured_mesh_output_asset_id")
        if not isinstance(self.export_type, str) or self.export_type not in _EXPORT_TYPES:
            raise UnsupportedTextureReconstructionOption(
                "export_type must be one of ply, obj, glb, or gltf"
            )
        _bounded_float(self.decimate, "decimate")
        _integer(self.close_holes, "close_holes")
        _integer(self.resolution_level, "resolution_level")
        _integer(self.min_resolution, "min_resolution")
        _integer(self.virtual_face_images, "virtual_face_images")
        _integer(self.texture_size_multiple, "texture_size_multiple")
        _finite_float(self.outlier_threshold, "outlier_threshold")
        _bounded_float(self.cost_smoothness_ratio, "cost_smoothness_ratio")
        _boolean(self.global_seam_leveling, "global_seam_leveling")
        _boolean(self.local_seam_leveling, "local_seam_leveling")
        _bounded_integer(self.patch_packing_heuristic, "patch_packing_heuristic")
        _empty_color(self.empty_color)
        _finite_float(self.sharpness_weight, "sharpness_weight")
        _ignore_mask_label(self.ignore_mask_label)
        _integer(self.max_texture_size, "max_texture_size")

    @property
    def output_asset_id(self) -> str:
        return self.textured_mesh_output_asset_id

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": TEXTURE_RECONSTRUCTION_CONTRACT,
            "textured_mesh_output_asset_id": self.textured_mesh_output_asset_id,
            "export_type": self.export_type,
            "decimate": self.decimate,
            "close_holes": self.close_holes,
            "resolution_level": self.resolution_level,
            "min_resolution": self.min_resolution,
            "virtual_face_images": self.virtual_face_images,
            "texture_size_multiple": self.texture_size_multiple,
            "outlier_threshold": self.outlier_threshold,
            "cost_smoothness_ratio": self.cost_smoothness_ratio,
            "global_seam_leveling": self.global_seam_leveling,
            "local_seam_leveling": self.local_seam_leveling,
            "patch_packing_heuristic": self.patch_packing_heuristic,
            "empty_color": self.empty_color,
            "sharpness_weight": self.sharpness_weight,
            "ignore_mask_label": self.ignore_mask_label,
            "max_texture_size": self.max_texture_size,
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
    ) -> TextureReconstructionConfig:
        if overrides is None:
            return cls()
        if not isinstance(overrides, Mapping):
            raise InvalidTextureReconstructionRequest("texture overrides must be a mapping")
        allowed = frozenset(cls.__dataclass_fields__)
        unknown = [key for key in overrides if key not in allowed]
        if unknown:
            raise UnsupportedTextureReconstructionOption(
                f"unsupported texture option: {unknown[0]!r}"
            )
        return cls(**cast(dict[str, Any], dict(overrides)))

    def with_overrides(
        self, overrides: Mapping[str, object] | None = None
    ) -> TextureReconstructionConfig:
        if overrides is None:
            return self
        if not isinstance(overrides, Mapping):
            raise InvalidTextureReconstructionRequest("texture overrides must be a mapping")
        allowed = frozenset(self.__dataclass_fields__)
        unknown = [key for key in overrides if key not in allowed]
        if unknown:
            raise UnsupportedTextureReconstructionOption(
                f"unsupported texture option: {unknown[0]!r}"
            )
        return replace(self, **cast(dict[str, Any], dict(overrides)))


@dataclass(frozen=True, slots=True)
class TextureReconstructionRequest:
    """Immutable texture request derived from one successful refinement run."""

    refinement_run: MeshRefinementRun
    configuration: TextureReconstructionConfig = TextureReconstructionConfig()
    engine_id: str = OPENMVS_ENGINE_ID
    engine_version: str = OPENMVS_ENGINE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.refinement_run, MeshRefinementRun):
            raise InvalidTextureReconstructionRequest("refinement_run must be a MeshRefinementRun")
        if self.refinement_run.status is not RunStatus.SUCCEEDED:
            raise InvalidTextureReconstructionRequest(
                "texture reconstruction requires one successful refinement run"
            )
        if self.refinement_run.stage_result.status is not StageStatus.SUCCEEDED:
            raise InvalidTextureReconstructionRequest(
                "texture reconstruction requires a successful refinement-stage result"
            )
        if self.refinement_run.refined_mesh_output_asset_id is None:
            raise InvalidTextureReconstructionRequest(
                "successful refinement run must expose a refined mesh identity"
            )
        _asset_id(self.refinement_run.refined_mesh_output_asset_id, "refined_mesh_asset_id")
        _asset_id(self.scene_asset_id, "scene_asset_id")
        if not isinstance(self.configuration, TextureReconstructionConfig):
            raise InvalidTextureReconstructionRequest(
                "configuration must be TextureReconstructionConfig"
            )
        if self.refinement_run.authority_class != RECONSTRUCTION_AUTHORITY_CLASS:
            raise UnsupportedTextureReconstructionOption(
                "texture reconstruction requires RECONSTRUCTION_OBSERVATION authority"
            )
        if self.engine_id != OPENMVS_ENGINE_ID:
            raise UnsupportedTextureReconstructionOption(
                f"only the PackLab OpenMVS adapter is supported, not {self.engine_id!r}"
            )
        if self.engine_version != OPENMVS_ENGINE_VERSION:
            raise UnsupportedTextureReconstructionOption(
                f"only OpenMVS {OPENMVS_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )
        if self.scale_state not in _ALLOWED_SCALES:
            raise UnsupportedTextureReconstructionOption(
                "texture reconstruction cannot claim METRIC_VERIFIED"
            )
        if self.output_asset_id in {self.refined_mesh_asset_id, self.scene_asset_id}:
            raise InvalidTextureReconstructionRequest(
                "textured mesh output asset must differ from predecessor mesh and scene assets"
            )

    @classmethod
    def from_refinement_run(
        cls,
        refinement_run: MeshRefinementRun,
        configuration: TextureReconstructionConfig | None = None,
    ) -> TextureReconstructionRequest:
        return cls(
            refinement_run,
            TextureReconstructionConfig() if configuration is None else configuration,
        )

    from_mesh_refinement_run = from_refinement_run

    @property
    def refined_mesh_asset_id(self) -> str:
        assert self.refinement_run.refined_mesh_output_asset_id is not None
        return self.refinement_run.refined_mesh_output_asset_id

    @property
    def input_mesh_asset_id(self) -> str:
        return self.refined_mesh_asset_id

    @property
    def scene_asset_id(self) -> str:
        return self.refinement_run.request.mesh_run.request.input_scene_asset_id

    @property
    def input_scene_asset_id(self) -> str:
        return self.scene_asset_id

    @property
    def input_asset_id(self) -> str:
        return self.scene_asset_id

    @property
    def output_asset_id(self) -> str:
        return self.configuration.output_asset_id

    @property
    def textured_mesh_output_asset_id(self) -> str:
        return self.output_asset_id

    @property
    def source_revision(self) -> str:
        return self.refinement_run.source_revision

    @property
    def source_digest(self) -> str:
        return self.refinement_run.source_digest

    @property
    def plan_digest(self) -> str:
        return self.refinement_run.plan_digest

    @property
    def dense_request_digest(self) -> str:
        return self.refinement_run.dense_request_digest

    @property
    def mesh_configuration_digest(self) -> str:
        return self.refinement_run.mesh_configuration_digest

    @property
    def mesh_request_digest(self) -> str:
        return self.refinement_run.mesh_request_digest

    @property
    def refinement_configuration_digest(self) -> str:
        return self.refinement_run.configuration_digest

    @property
    def refinement_request_digest(self) -> str:
        return self.refinement_run.request_digest

    @property
    def configuration_digest(self) -> str:
        return self.configuration.configuration_digest

    @property
    def scale_state(self) -> ScaleState:
        return self.refinement_run.scale_state

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": TEXTURE_RECONSTRUCTION_CONTRACT,
            "scene_asset_id": self.scene_asset_id,
            "refined_mesh_asset_id": self.refined_mesh_asset_id,
            "textured_mesh_output_asset_id": self.textured_mesh_output_asset_id,
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "plan_digest": self.plan_digest,
            "dense_request_digest": self.dense_request_digest,
            "mesh_configuration_digest": self.mesh_configuration_digest,
            "mesh_request_digest": self.mesh_request_digest,
            "refinement_configuration_digest": self.refinement_configuration_digest,
            "refinement_request_digest": self.refinement_request_digest,
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
        raise UnsupportedTextureReconstructionOption(
            "an explicit OpenMVS TextureMesh probe is required"
        )
    if probe.engine_id != OPENMVS_TEXTURE_MESH_PROBE_ID:
        raise UnsupportedTextureReconstructionOption(
            "the supplied probe is not for OpenMVS TextureMesh"
        )
    if probe.status is not EngineProbeStatus.VALID:
        raise UnsupportedTextureReconstructionOption(
            "OpenMVS TextureMesh must be explicitly probed and version-valid"
        )
    if probe.version is None or probe.version.text != OPENMVS_ENGINE_VERSION:
        raise UnsupportedTextureReconstructionOption(
            f"only probed OpenMVS {OPENMVS_ENGINE_VERSION} is supported"
        )
    if probe.executable is None:
        raise UnsupportedTextureReconstructionOption(
            "the OpenMVS TextureMesh probe has no executable identity"
        )
    if Path(probe.executable).as_posix().lower() != Path(executable).as_posix().lower():
        raise UnsupportedTextureReconstructionOption(
            "probed OpenMVS TextureMesh executable does not match request"
        )


def _bool_argument(value: bool) -> str:
    return "1" if value else "0"


@dataclass(frozen=True, slots=True)
class OpenMVSTextureMeshAdapter:
    """Command and execution adapter for pinned OpenMVS texture mapping."""

    engine_version: str = OPENMVS_ENGINE_VERSION

    def build_command(
        self,
        request: TextureReconstructionRequest,
        executable: str | Path,
    ) -> tuple[str, ...]:
        if not isinstance(request, TextureReconstructionRequest):
            raise InvalidTextureReconstructionRequest(
                "request must be a TextureReconstructionRequest"
            )
        if self.engine_version != OPENMVS_ENGINE_VERSION:
            raise UnsupportedTextureReconstructionOption(
                f"only OpenMVS {OPENMVS_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )
        if request.engine_version != self.engine_version:
            raise UnsupportedTextureReconstructionOption(
                "request and adapter engine versions differ"
            )
        command = _portable_executable(executable)
        config = request.configuration
        return (
            command,
            "--input-file",
            request.scene_asset_id,
            "--mesh-file",
            request.refined_mesh_asset_id,
            "--output-file",
            config.output_asset_id,
            "--export-type",
            config.export_type,
            "--decimate",
            str(config.decimate),
            "--close-holes",
            str(config.close_holes),
            "--resolution-level",
            str(config.resolution_level),
            "--min-resolution",
            str(config.min_resolution),
            "--outlier-threshold",
            str(config.outlier_threshold),
            "--cost-smoothness-ratio",
            str(config.cost_smoothness_ratio),
            "--virtual-face-images",
            str(config.virtual_face_images),
            "--global-seam-leveling",
            _bool_argument(config.global_seam_leveling),
            "--local-seam-leveling",
            _bool_argument(config.local_seam_leveling),
            "--texture-size-multiple",
            str(config.texture_size_multiple),
            "--patch-packing-heuristic",
            str(config.patch_packing_heuristic),
            "--empty-color",
            str(config.empty_color),
            "--sharpness-weight",
            str(config.sharpness_weight),
            "--ignore-mask-label",
            str(config.ignore_mask_label),
            "--max-texture-size",
            str(config.max_texture_size),
        )

    def execute(
        self,
        request: TextureReconstructionRequest,
        executable: str | Path,
        probe: EngineProbeResult,
        *,
        timeout: float | None = None,
        cancel_event: threading.Event | None = None,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
    ) -> TextureReconstructionRun:
        command = self.build_command(request, executable)
        _probe_matches(command[0], probe)
        stage_result = stage_runner(
            TEXTURE_MESH_STAGE_ID,
            command,
            timeout=timeout,
            cancel_event=cancel_event,
            cwd=cwd,
            env=env,
        )
        if not isinstance(stage_result, ReconstructionStageResult):
            raise TextureReconstructionError("stage runner must return ReconstructionStageResult")
        return normalize_texture_mesh_result(request, stage_result)


def _stage_result_contract_error(stage_result: ReconstructionStageResult) -> str | None:
    if stage_result.stage_id != TEXTURE_MESH_STAGE_ID:
        return "texture stage result has an unexpected stage ID"
    if not isinstance(stage_result.status, StageStatus):
        return "texture stage result has an unknown status"
    if not isinstance(stage_result.cancelled, bool):
        return "texture stage result cancellation flag must be a boolean"
    if isinstance(stage_result.exit_code, bool) or not (
        stage_result.exit_code is None or isinstance(stage_result.exit_code, int)
    ):
        return "texture stage result has an invalid exit code"
    try:
        duration = float(stage_result.duration_seconds)
    except (OverflowError, TypeError, ValueError):
        return "texture stage result has an invalid duration"
    if (
        isinstance(stage_result.duration_seconds, bool)
        or not isinstance(stage_result.duration_seconds, (int, float))
        or not math.isfinite(duration)
        or duration < 0
    ):
        return "texture stage result has an invalid duration"
    if not isinstance(stage_result.stdout, str) or not isinstance(stage_result.stderr, str):
        return "texture stage result output must be text"
    if stage_result.failure_reason is not None and not isinstance(stage_result.failure_reason, str):
        return "texture stage result failure reason must be text"
    if stage_result.status is StageStatus.SUCCEEDED:
        if stage_result.cancelled:
            return "a successful texture stage cannot be cancelled"
        if stage_result.exit_code != 0:
            return "a successful texture stage requires exit code zero"
    elif stage_result.status is StageStatus.FAILED:
        if stage_result.cancelled:
            return "a failed texture stage cannot be marked cancelled"
        if stage_result.exit_code == 0:
            return "a failed texture stage cannot have exit code zero"
    elif stage_result.status is StageStatus.CANCELLED:
        if not stage_result.cancelled:
            return "a cancelled texture stage must be marked cancelled"
        if stage_result.exit_code == 0:
            return "a cancelled texture stage cannot have exit code zero"
    return None


def _failed_stage_result(
    result: ReconstructionStageResult, reason: str
) -> ReconstructionStageResult:
    exit_code = (
        result.exit_code
        if isinstance(result.exit_code, int) and not isinstance(result.exit_code, bool)
        else None
    )
    if exit_code == 0:
        exit_code = None
    try:
        duration = float(result.duration_seconds)
    except (OverflowError, TypeError, ValueError):
        duration = 0.0
    if (
        isinstance(result.duration_seconds, bool)
        or not isinstance(result.duration_seconds, (int, float))
        or not math.isfinite(duration)
        or duration < 0
    ):
        duration = 0.0
    stdout = result.stdout if isinstance(result.stdout, str) else ""
    stderr = result.stderr if isinstance(result.stderr, str) else ""
    return ReconstructionStageResult(
        stage_id=TEXTURE_MESH_STAGE_ID,
        status=StageStatus.FAILED,
        exit_code=exit_code,
        duration_seconds=duration,
        stdout=stdout,
        stderr=stderr,
        cancelled=False,
        failure_reason=reason,
    )


@dataclass(frozen=True, slots=True)
class TextureReconstructionRun:
    """Immutable texture result with output only on coherent success."""

    request: TextureReconstructionRequest
    status: RunStatus
    stage_result: ReconstructionStageResult
    textured_mesh_output_asset_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, TextureReconstructionRequest):
            raise TextureReconstructionError("texture run requires a TextureReconstructionRequest")
        if not isinstance(self.stage_result, ReconstructionStageResult):
            raise TextureReconstructionError("texture run requires a reconstruction stage result")
        if not isinstance(self.status, RunStatus):
            raise TextureReconstructionError("texture run has an unknown run status")
        stage_error = _stage_result_contract_error(self.stage_result)
        if stage_error is not None:
            raise TextureReconstructionError(stage_error)
        if self.status is RunStatus.SUCCEEDED:
            if self.stage_result.status is not StageStatus.SUCCEEDED:
                raise TextureReconstructionError(
                    "successful texture run requires a successful stage"
                )
            if self.textured_mesh_output_asset_id is None:
                raise TextureReconstructionError(
                    "successful texture run requires an output identity"
                )
            if _asset_id(self.textured_mesh_output_asset_id, "textured_mesh_output_asset_id") != (
                self.request.configuration.output_asset_id
            ):
                raise TextureReconstructionError(
                    "successful textured mesh output identity does not match request"
                )
        elif self.status is RunStatus.FAILED:
            if self.stage_result.status is not StageStatus.FAILED:
                raise TextureReconstructionError("failed texture run requires a failed stage")
            if self.textured_mesh_output_asset_id is not None:
                raise TextureReconstructionError("failed texture run cannot expose output")
        elif self.status is RunStatus.CANCELLED:
            if self.stage_result.status is not StageStatus.CANCELLED:
                raise TextureReconstructionError("cancelled texture run requires a cancelled stage")
            if self.textured_mesh_output_asset_id is not None:
                raise TextureReconstructionError("cancelled texture run cannot expose output")

    @property
    def output_asset_id(self) -> str | None:
        return self.textured_mesh_output_asset_id

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
    def refinement_configuration_digest(self) -> str:
        return self.request.refinement_configuration_digest

    @property
    def refinement_request_digest(self) -> str:
        return self.request.refinement_request_digest

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
            "Textured mesh output is RECONSTRUCTION_OBSERVATION derived from a successful refinement observation.",
            "Textured mesh output is not Scan Master, CAD, measurement, or engineering authority.",
            "This boundary does not parse meshes or textures, infer quality, or claim metric verification.",
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": TEXTURE_RECONSTRUCTION_CONTRACT,
            "request": self.request.as_dict(),
            "status": self.status.value,
            "stage_result": self.stage_result.as_dict(),
            "textured_mesh_output_asset_id": self.textured_mesh_output_asset_id,
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "plan_digest": self.plan_digest,
            "dense_request_digest": self.dense_request_digest,
            "mesh_configuration_digest": self.mesh_configuration_digest,
            "mesh_request_digest": self.mesh_request_digest,
            "refinement_configuration_digest": self.refinement_configuration_digest,
            "refinement_request_digest": self.refinement_request_digest,
            "configuration_digest": self.configuration_digest,
            "request_digest": self.request_digest,
            "authority_class": self.authority_class,
            "scale_state": self.scale_state.value,
            "limitations": list(self.limitations),
        }


def normalize_texture_mesh_result(
    request: TextureReconstructionRequest,
    stage_result: ReconstructionStageResult,
) -> TextureReconstructionRun:
    """Normalize one stage result without interpreting engine output."""

    if not isinstance(request, TextureReconstructionRequest):
        raise TextureReconstructionError("request must be a TextureReconstructionRequest")
    if not isinstance(stage_result, ReconstructionStageResult):
        raise TextureReconstructionError("stage runner must return ReconstructionStageResult")
    stage_error = _stage_result_contract_error(stage_result)
    if stage_error is not None:
        return TextureReconstructionRun(
            request,
            RunStatus.FAILED,
            _failed_stage_result(stage_result, stage_error),
        )
    if stage_result.status is StageStatus.CANCELLED:
        return TextureReconstructionRun(request, RunStatus.CANCELLED, stage_result)
    if stage_result.status is StageStatus.FAILED:
        return TextureReconstructionRun(request, RunStatus.FAILED, stage_result)
    return TextureReconstructionRun(
        request,
        RunStatus.SUCCEEDED,
        stage_result,
        request.configuration.output_asset_id,
    )


def build_openmvs_texture_mesh_command(
    request: TextureReconstructionRequest,
    executable: str | Path,
) -> tuple[str, ...]:
    """Build pinned TextureMesh argv without executing it."""

    return OpenMVSTextureMeshAdapter().build_command(request, executable)


def execute_openmvs_texture_mesh(
    request: TextureReconstructionRequest,
    executable: str | Path,
    probe: EngineProbeResult,
    *,
    timeout: float | None = None,
    cancel_event: threading.Event | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
) -> TextureReconstructionRun:
    """Execute only an explicitly supplied, already-probed executable."""

    return OpenMVSTextureMeshAdapter().execute(
        request,
        executable,
        probe,
        timeout=timeout,
        cancel_event=cancel_event,
        cwd=cwd,
        env=env,
        stage_runner=stage_runner,
    )


run_texture_mesh = execute_openmvs_texture_mesh
build_texture_mesh_command = build_openmvs_texture_mesh_command
TextureMeshConfig = TextureReconstructionConfig
TextureMeshRequest = TextureReconstructionRequest
TextureMeshRun = TextureReconstructionRun
TextureReconstructionStageRequest = TextureReconstructionRequest
TextureReconstructionStageRun = TextureReconstructionRun
OpenMVSTextureMeshStageAdapter = OpenMVSTextureMeshAdapter


__all__ = [
    "DEFAULT_TEXTURED_MESH_OUTPUT_ASSET_ID",
    "InvalidTextureReconstructionRequest",
    "OPENMVS_ENGINE_ID",
    "OPENMVS_ENGINE_VERSION",
    "OPENMVS_TEXTURE_MESH_PROBE_ID",
    "OPENMVS_TEXTURE_MESH_STAGE_ID",
    "OPENMVS_TEXTURE_STAGE_ID",
    "OpenMVSTextureMeshAdapter",
    "OpenMVSTextureMeshStageAdapter",
    "TEXTURE_MESH_STAGE_ID",
    "TEXTURE_RECONSTRUCTION_CONTRACT",
    "TEXTURE_RECONSTRUCTION_STAGE_ID",
    "TextureMeshConfig",
    "TextureMeshRequest",
    "TextureMeshRun",
    "TextureMeshStageStatus",
    "TextureReconstructionConfig",
    "TextureReconstructionError",
    "TextureReconstructionRequest",
    "TextureReconstructionRun",
    "TextureReconstructionStageRequest",
    "TextureReconstructionStageRun",
    "UnsupportedTextureReconstructionOption",
    "build_openmvs_texture_mesh_command",
    "build_texture_mesh_command",
    "execute_openmvs_texture_mesh",
    "normalize_texture_mesh_result",
    "run_texture_mesh",
]
