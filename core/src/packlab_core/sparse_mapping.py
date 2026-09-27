"""PackLab-owned COLMAP sparse-mapping stage boundary.

This module owns request identity, the configuration-only COLMAP adapter, and
the small machine-readable result contract for the sparse mapper.  It does
not discover or install an engine and does not inspect image pixels.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .engine_probe import EngineProbeResult, EngineProbeStatus
from .reconstruction import (
    ReconstructionStageResult,
    RunStatus,
    StageStatus,
)
from .reconstruction_process import run_reconstruction_stage

COLMAP_ENGINE_ID = "colmap"
COLMAP_ENGINE_VERSION = "3.12.6"
SPARSE_MAPPING_CONTRACT = "packlab.sparse-mapping.v1"
STAGE_SUMMARY_CONTRACT = "packlab.sparse-mapping.stage-summary.v1"
STAGE_SUMMARY_PREFIX = "PACKLAB_SPARSE_MAPPING_SUMMARY_V1 "
SPARSE_MAPPING_STAGE_ID = "sparse-mapping"
MAX_STAGE_IMAGE_COUNT = 10_000_000

_HEX_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_REVISION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class SparseMappingError(ValueError):
    """Base error for invalid or unsafe sparse-mapping values."""


class InvalidSparseMappingRequest(SparseMappingError):
    """Raised when a request is incomplete, inconsistent, or unsafe."""


class UnsupportedSparseMappingOption(SparseMappingError):
    """Raised when the pinned COLMAP adapter cannot represent a value."""


class SparseMappingSummaryError(SparseMappingError):
    """Raised when a stage summary is absent, malformed, or inconsistent."""


class SparseMappingStageStatus(StrEnum):
    """Normalized status names exposed by the sparse-mapping result."""

    SUCCEEDED = StageStatus.SUCCEEDED.value
    FAILED = StageStatus.FAILED.value
    CANCELLED = StageStatus.CANCELLED.value


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _asset_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidSparseMappingRequest(f"{field_name} must be a non-empty string")
    if _CONTROL.search(value) or "\\" in value:
        raise InvalidSparseMappingRequest(f"{field_name} must use safe portable path syntax")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value) or value.startswith("//"):
        raise InvalidSparseMappingRequest(f"{field_name} must be repository-relative")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise InvalidSparseMappingRequest(f"{field_name} contains an unsafe path component")
    if ":" in value:
        raise InvalidSparseMappingRequest(f"{field_name} contains an unsafe path component")
    return value


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _HEX_DIGEST.fullmatch(value) is None:
        raise InvalidSparseMappingRequest(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _revision(value: object) -> str:
    if not isinstance(value, str) or _SAFE_REVISION.fullmatch(value) is None:
        raise InvalidSparseMappingRequest("source revision must be a safe portable identifier")
    return value


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SparseMappingSummaryError(f"{field_name} must be an integer")
    return value


@dataclass(frozen=True, slots=True)
class SparseMappingConfig:
    """Portable COLMAP mapper paths and immutable stage configuration."""

    database_asset_id: str = "working/reconstruction/database.db"
    image_path_asset_id: str = "working/images"
    sparse_output_asset_id: str = "working/reconstruction/sparse"

    def __post_init__(self) -> None:
        for field_name in (
            "database_asset_id",
            "image_path_asset_id",
            "sparse_output_asset_id",
        ):
            _asset_id(getattr(self, field_name), field_name)

    def as_dict(self) -> dict[str, str]:
        return {
            "database_asset_id": self.database_asset_id,
            "image_path_asset_id": self.image_path_asset_id,
            "sparse_output_asset_id": self.sparse_output_asset_id,
        }


@dataclass(frozen=True, slots=True)
class SparseMappingRequest:
    """Immutable, provenance-bound request for one sparse-mapper stage."""

    image_asset_ids: tuple[str, ...]
    source_revision: str
    source_digest: str
    matcher_selection_digest: str
    configuration: SparseMappingConfig = SparseMappingConfig()
    engine_id: str = COLMAP_ENGINE_ID
    engine_version: str = COLMAP_ENGINE_VERSION

    def __post_init__(self) -> None:
        if isinstance(self.image_asset_ids, (str, bytes, bytearray)):
            raise InvalidSparseMappingRequest("image_asset_ids must be an ordered sequence")
        if not isinstance(self.image_asset_ids, Sequence):
            raise InvalidSparseMappingRequest("image_asset_ids must be an ordered sequence")
        values = tuple(
            _asset_id(value, f"image_asset_ids[{index}]")
            for index, value in enumerate(self.image_asset_ids)
        )
        if not values:
            raise InvalidSparseMappingRequest("at least one input image is required")
        if len(set(values)) != len(values):
            raise InvalidSparseMappingRequest("input image asset IDs must be unique")
        object.__setattr__(self, "image_asset_ids", values)
        _revision(self.source_revision)
        _digest(self.source_digest, "source_digest")
        _digest(self.matcher_selection_digest, "matcher_selection_digest")
        if not isinstance(self.configuration, SparseMappingConfig):
            raise InvalidSparseMappingRequest("configuration must be SparseMappingConfig")
        if self.engine_id != COLMAP_ENGINE_ID:
            raise UnsupportedSparseMappingOption(
                f"only the PackLab COLMAP adapter is supported, not {self.engine_id!r}"
            )
        if self.engine_version != COLMAP_ENGINE_VERSION:
            raise UnsupportedSparseMappingOption(
                f"only COLMAP {COLMAP_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": SPARSE_MAPPING_CONTRACT,
            "image_asset_ids": list(self.image_asset_ids),
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "matcher_selection_digest": self.matcher_selection_digest,
            "configuration": self.configuration.as_dict(),
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
        }

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def request_digest(self) -> str:
        return _canonical_digest(self.as_dict())

    def digest(self) -> str:
        return self.request_digest()

    @property
    def input_asset_ids(self) -> tuple[str, ...]:
        """Compatibility name for the ordered source-image binding."""

        return self.image_asset_ids

    @property
    def ordered_image_asset_ids(self) -> tuple[str, ...]:
        return self.image_asset_ids


@dataclass(frozen=True, slots=True)
class RegisteredImageStatistics:
    """Deterministic registration counts returned by a sparse-map stage."""

    total_images: int
    registered_images: int
    unregistered_images: int

    def __post_init__(self) -> None:
        for field_name in ("total_images", "registered_images", "unregistered_images"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise SparseMappingSummaryError(f"{field_name} must be an integer")
        if self.total_images <= 0:
            raise SparseMappingSummaryError("total_images must be greater than zero")
        if self.total_images > MAX_STAGE_IMAGE_COUNT:
            raise SparseMappingSummaryError("total_images exceeds the bounded stage limit")
        if self.registered_images < 0 or self.unregistered_images < 0:
            raise SparseMappingSummaryError("registration counts cannot be negative")
        if self.registered_images > self.total_images:
            raise SparseMappingSummaryError("registered_images cannot exceed total_images")
        if self.registered_images + self.unregistered_images != self.total_images:
            raise SparseMappingSummaryError("registered and unregistered counts must equal total")

    @property
    def total_input_images(self) -> int:
        return self.total_images

    @property
    def registration_ratio(self) -> float:
        return self.registered_images / self.total_images

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": STAGE_SUMMARY_CONTRACT,
            "total_images": self.total_images,
            "registered_images": self.registered_images,
            "unregistered_images": self.unregistered_images,
            "registration_ratio": self.registration_ratio,
        }

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return _canonical_digest(self.as_dict())


def _summary_value(summary: Mapping[str, object], name: str, alias: str | None = None) -> object:
    present = [key for key in (name, alias) if key is not None and key in summary]
    if not present:
        raise SparseMappingSummaryError(f"stage summary is missing {name}")
    if len(present) == 2 and summary[present[0]] != summary[present[1]]:
        raise SparseMappingSummaryError(f"stage summary has conflicting {name} aliases")
    return summary[present[0]]


def _summary_mapping(value: Mapping[str, object] | str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return dict(value)
    if not isinstance(value, str) or not value.startswith(STAGE_SUMMARY_PREFIX):
        raise SparseMappingSummaryError(
            "stage summary must be a documented JSON object or prefixed machine-readable line"
        )
    payload = value[len(STAGE_SUMMARY_PREFIX) :]
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as error:
        raise SparseMappingSummaryError("stage summary JSON is malformed") from error
    if not isinstance(parsed, Mapping):
        raise SparseMappingSummaryError("stage summary JSON must be an object")
    return parsed


def parse_registered_image_statistics(
    summary: Mapping[str, object] | str,
) -> RegisteredImageStatistics:
    """Parse only the explicit sparse-stage summary contract."""

    values = _summary_mapping(summary)
    if values.get("contract") != STAGE_SUMMARY_CONTRACT:
        raise SparseMappingSummaryError("stage summary contract is unsupported")
    total = _integer(_summary_value(values, "total_images", "total_input_images"), "total_images")
    registered = _integer(_summary_value(values, "registered_images"), "registered_images")
    unregistered = _integer(_summary_value(values, "unregistered_images"), "unregistered_images")
    statistics = RegisteredImageStatistics(total, registered, unregistered)
    ratio_value = values.get("registration_ratio")
    if ratio_value is None:
        return statistics
    if isinstance(ratio_value, bool) or not isinstance(ratio_value, (int, float)):
        raise SparseMappingSummaryError("registration_ratio must be a finite number")
    ratio = float(ratio_value)
    if not math.isfinite(ratio) or not math.isclose(
        ratio, statistics.registration_ratio, rel_tol=0.0, abs_tol=1e-12
    ):
        raise SparseMappingSummaryError("registration_ratio does not match registration counts")
    return statistics


def _summary_from_stdout(stdout: str) -> Mapping[str, object] | str:
    matches = [line for line in stdout.splitlines() if line.startswith(STAGE_SUMMARY_PREFIX)]
    if len(matches) != 1:
        raise SparseMappingSummaryError(
            "stage stdout must contain exactly one documented sparse-mapping summary"
        )
    return matches[0]


def _portable_executable(value: str | Path) -> str:
    executable = str(value)
    if not executable.strip() or "\x00" in executable:
        raise InvalidSparseMappingRequest("an explicit COLMAP executable is required")
    return executable


def _probe_matches(executable: str, probe: EngineProbeResult) -> None:
    if probe.engine_id != COLMAP_ENGINE_ID:
        raise UnsupportedSparseMappingOption("the supplied probe is not for COLMAP")
    if probe.status is not EngineProbeStatus.VALID:
        raise UnsupportedSparseMappingOption("COLMAP must be explicitly probed and version-valid")
    if probe.version is None or probe.version.text != COLMAP_ENGINE_VERSION:
        raise UnsupportedSparseMappingOption(
            f"only probed COLMAP {COLMAP_ENGINE_VERSION} is supported"
        )
    if probe.executable is None:
        raise UnsupportedSparseMappingOption("the COLMAP probe has no executable identity")
    if Path(probe.executable).as_posix().lower() != Path(executable).as_posix().lower():
        raise UnsupportedSparseMappingOption("probed COLMAP executable does not match request")


@dataclass(frozen=True, slots=True)
class ColmapSparseMapperAdapter:
    """Configuration and execution adapter for the pinned COLMAP mapper."""

    engine_version: str = COLMAP_ENGINE_VERSION

    def build_command(
        self,
        request: SparseMappingRequest,
        executable: str | Path,
    ) -> tuple[str, ...]:
        if self.engine_version != COLMAP_ENGINE_VERSION:
            raise UnsupportedSparseMappingOption(
                f"only COLMAP {COLMAP_ENGINE_VERSION} is supported, not {self.engine_version!r}"
            )
        if request.engine_version != self.engine_version:
            raise UnsupportedSparseMappingOption("request and adapter engine versions differ")
        command = _portable_executable(executable)
        config = request.configuration
        return (
            command,
            "mapper",
            "--database_path",
            config.database_asset_id,
            "--image_path",
            config.image_path_asset_id,
            "--output_path",
            config.sparse_output_asset_id,
        )

    def execute(
        self,
        request: SparseMappingRequest,
        executable: str | Path,
        probe: EngineProbeResult,
        *,
        timeout: float | None = None,
        cancel_event: threading.Event | None = None,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
    ) -> SparseMappingRun:
        command = self.build_command(request, executable)
        _probe_matches(command[0], probe)
        result = stage_runner(
            SPARSE_MAPPING_STAGE_ID,
            command,
            timeout=timeout,
            cancel_event=cancel_event,
            cwd=cwd,
            env=env,
        )
        if not isinstance(result, ReconstructionStageResult):
            raise SparseMappingError("stage runner must return ReconstructionStageResult")
        return normalize_sparse_mapping_result(request, result)


@dataclass(frozen=True, slots=True)
class SparseMappingRun:
    """Normalized sparse-stage result with output only on a valid success."""

    request: SparseMappingRequest
    status: RunStatus
    stage_result: ReconstructionStageResult
    statistics: RegisteredImageStatistics | None = None
    sparse_model_asset_id: str | None = None

    def __post_init__(self) -> None:
        if self.status is RunStatus.SUCCEEDED:
            if self.stage_result.status is not StageStatus.SUCCEEDED:
                raise SparseMappingError("successful sparse mapping requires a successful stage")
            if self.statistics is None or self.sparse_model_asset_id is None:
                raise SparseMappingError(
                    "successful sparse mapping requires a valid output contract"
                )
            _asset_id(self.sparse_model_asset_id, "sparse_model_asset_id")
        elif self.statistics is not None or self.sparse_model_asset_id is not None:
            raise SparseMappingError("failed or cancelled sparse mapping cannot expose output")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": SPARSE_MAPPING_CONTRACT,
            "request": self.request.as_dict(),
            "status": self.status.value,
            "stage_result": self.stage_result.as_dict(),
            "statistics": None if self.statistics is None else self.statistics.as_dict(),
            "sparse_model_asset_id": self.sparse_model_asset_id,
        }


def _failed_summary_result(
    result: ReconstructionStageResult,
    reason: str,
) -> ReconstructionStageResult:
    return ReconstructionStageResult(
        stage_id=result.stage_id,
        status=StageStatus.FAILED,
        exit_code=result.exit_code,
        duration_seconds=result.duration_seconds,
        stdout=result.stdout,
        stderr=result.stderr,
        cancelled=False,
        failure_reason=reason,
    )


def normalize_sparse_mapping_result(
    request: SparseMappingRequest,
    stage_result: ReconstructionStageResult,
    summary: Mapping[str, object] | str | None = None,
) -> SparseMappingRun:
    """Map a bounded stage result to PackLab run semantics without guessing."""

    if stage_result.status is StageStatus.CANCELLED:
        return SparseMappingRun(request, RunStatus.CANCELLED, stage_result)
    if stage_result.status is StageStatus.FAILED:
        return SparseMappingRun(request, RunStatus.FAILED, stage_result)
    if stage_result.status is not StageStatus.SUCCEEDED:
        raise SparseMappingError("unknown reconstruction stage status")
    try:
        parsed_summary: Mapping[str, object] | str = (
            _summary_from_stdout(stage_result.stdout) if summary is None else summary
        )
        statistics = parse_registered_image_statistics(parsed_summary)
        if statistics.total_images != len(request.image_asset_ids):
            raise SparseMappingSummaryError(
                "stage total_images does not match the ordered request image count"
            )
        values = _summary_mapping(parsed_summary)
        output_value = values.get("sparse_model_asset_id", values.get("output_asset_id"))
        if (
            output_value is not None
            and output_value != request.configuration.sparse_output_asset_id
        ):
            raise SparseMappingSummaryError("stage output asset does not match request")
    except SparseMappingError as error:
        failed = _failed_summary_result(
            stage_result,
            f"sparse-mapping output contract invalid: {error}",
        )
        return SparseMappingRun(request, RunStatus.FAILED, failed)
    return SparseMappingRun(
        request,
        RunStatus.SUCCEEDED,
        stage_result,
        statistics,
        request.configuration.sparse_output_asset_id,
    )


def build_colmap_sparse_mapper_command(
    request: SparseMappingRequest,
    executable: str | Path,
) -> tuple[str, ...]:
    """Build configuration-only COLMAP command arguments without executing."""

    return ColmapSparseMapperAdapter().build_command(request, executable)


def execute_sparse_mapping(
    request: SparseMappingRequest,
    executable: str | Path,
    probe: EngineProbeResult,
    *,
    timeout: float | None = None,
    cancel_event: threading.Event | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    stage_runner: Callable[..., ReconstructionStageResult] = run_reconstruction_stage,
) -> SparseMappingRun:
    """Execute only an explicitly supplied, already-probed COLMAP executable."""

    return ColmapSparseMapperAdapter().execute(
        request,
        executable,
        probe,
        timeout=timeout,
        cancel_event=cancel_event,
        cwd=cwd,
        env=env,
        stage_runner=stage_runner,
    )


run_sparse_mapping = execute_sparse_mapping
map_to_colmap_sparse_mapper = build_colmap_sparse_mapper_command
SparseMapperConfig = SparseMappingConfig
SparseMapperRequest = SparseMappingRequest
RegisteredImageStats = RegisteredImageStatistics


__all__ = [
    "COLMAP_ENGINE_ID",
    "COLMAP_ENGINE_VERSION",
    "MAX_STAGE_IMAGE_COUNT",
    "SPARSE_MAPPING_CONTRACT",
    "SPARSE_MAPPING_STAGE_ID",
    "STAGE_SUMMARY_CONTRACT",
    "STAGE_SUMMARY_PREFIX",
    "ColmapSparseMapperAdapter",
    "InvalidSparseMappingRequest",
    "RegisteredImageStatistics",
    "RegisteredImageStats",
    "SparseMapperConfig",
    "SparseMapperRequest",
    "SparseMappingConfig",
    "SparseMappingError",
    "SparseMappingRun",
    "SparseMappingStageStatus",
    "SparseMappingSummaryError",
    "SparseMappingRequest",
    "UnsupportedSparseMappingOption",
    "build_colmap_sparse_mapper_command",
    "execute_sparse_mapping",
    "map_to_colmap_sparse_mapper",
    "normalize_sparse_mapping_result",
    "parse_registered_image_statistics",
    "run_sparse_mapping",
]
