"""PackLab-owned orchestration for the COLMAP/OpenMVS reconstruction lane.

The orchestrator owns order, identity binding, cancellation normalization and
the final normalized manifest.  Engine command construction and output
parsing remain in the existing stage modules; callers provide stage adapters
that return their existing typed runs plus a small, verified output record.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from .reconstruction import (
    PACKSCAN_CAMERA_CONVENTION,
    BackendProvenance,
    CancelToken,
    ReconstructionBackendId,
    ReconstructionJobSpec,
    ReconstructionOutputManifest,
    ReconstructionStageResult,
    RunStatus,
    ScaleState,
    StageStatus,
)

ORCHESTRATION_CONTRACT = "packlab.reconstruction-orchestration.v1"
RECONSTRUCTION_AUTHORITY_CLASS = "RECONSTRUCTION_OBSERVATION"
_DIGEST = re.compile(r"[0-9a-f]{64}")


class ReconstructionOrchestrationError(ValueError):
    """Raised when an orchestration request is unsafe or incomplete."""


class OrchestrationStageId(StrEnum):
    FEATURE_EXTRACTION = "feature-extraction"
    MATCHING = "matching"
    SPARSE_MAPPING = "sparse-mapping"
    OPENMVS_CONVERSION = "openmvs-conversion"
    DENSE_POINT_CLOUD = "dense-point-cloud"
    MESH_RECONSTRUCTION = "mesh-reconstruction"
    MESH_REFINEMENT = "mesh-refinement"
    TEXTURE_MESH = "texture-mesh"


STAGE_ORDER = tuple(item.value for item in OrchestrationStageId)


def _safe_asset_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ReconstructionOrchestrationError(f"{field_name} must be a non-empty asset ID")
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        raise ReconstructionOrchestrationError(f"{field_name} must be relative")
    if any(part in {"", ".", ".."} for part in normalized.split("/")):
        raise ReconstructionOrchestrationError(f"{field_name} contains an unsafe path component")
    return normalized


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ReconstructionOrchestrationError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _canonical_digest(value: object) -> str:
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError) as error:
        raise ReconstructionOrchestrationError(
            "orchestration configuration is not serializable"
        ) from error
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ReconstructionStageExecution:
    """One verified stage result returned by an existing stage adapter.

    ``payload`` is intentionally opaque here.  It may be a
    ``SparseMappingRun``, ``DensePointCloudRun``, ``TextureReconstructionRun``
    or another accepted stage contract; the orchestrator never re-parses it.
    """

    stage_id: str
    stage_result: ReconstructionStageResult
    output_asset_ids: Mapping[str, str] = field(default_factory=dict)
    outputs_verified: bool = False
    payload: object | None = None

    def __post_init__(self) -> None:
        expected = _safe_asset_id(self.stage_id, "stage_id")
        if not isinstance(self.stage_result, ReconstructionStageResult):
            raise ReconstructionOrchestrationError("stage_result must be ReconstructionStageResult")
        if self.stage_result.stage_id != expected:
            raise ReconstructionOrchestrationError("stage result and execution stage IDs differ")
        if not isinstance(self.outputs_verified, bool):
            raise ReconstructionOrchestrationError("outputs_verified must be a boolean")
        normalized: dict[str, str] = {}
        for key, value in self.output_asset_ids.items():
            normalized[_safe_asset_id(key, "output identity")] = _safe_asset_id(
                value, "output asset"
            )
        object.__setattr__(self, "stage_id", expected)
        object.__setattr__(self, "output_asset_ids", normalized)


@dataclass(frozen=True, slots=True)
class ReconstructionStageContext:
    job: ReconstructionJobSpec
    workspace: str
    configuration: Mapping[str, object]
    previous: tuple[ReconstructionStageExecution, ...]
    cancel: CancelToken


StageExecutor = Callable[[ReconstructionStageContext], ReconstructionStageExecution]


@dataclass(frozen=True, slots=True)
class ReconstructionStageDefinition:
    stage_id: str
    execute: StageExecutor
    dependencies: tuple[str, ...] = ()
    configuration: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        stage_id = _safe_asset_id(self.stage_id, "stage_id")
        if not callable(self.execute):
            raise ReconstructionOrchestrationError("stage execute must be callable")
        object.__setattr__(self, "stage_id", stage_id)
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
        object.__setattr__(self, "configuration", dict(self.configuration))


@dataclass(frozen=True, slots=True)
class ReconstructionOrchestrationRequest:
    job: ReconstructionJobSpec
    workspace: str
    backend_provenance: BackendProvenance
    stages: tuple[ReconstructionStageDefinition, ...]
    configuration: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.job, ReconstructionJobSpec):
            raise ReconstructionOrchestrationError("job must be ReconstructionJobSpec")
        if self.job.backend_id is not ReconstructionBackendId.COLMAP_OPENMVS:
            raise ReconstructionOrchestrationError("only the COLMAP/OpenMVS lane is supported")
        if not isinstance(self.backend_provenance, BackendProvenance):
            raise ReconstructionOrchestrationError("backend provenance is required")
        if self.backend_provenance.backend_id is not self.job.backend_id:
            raise ReconstructionOrchestrationError("backend provenance does not match the job")
        workspace = _safe_asset_id(self.workspace, "workspace")
        if len(self.stages) != len(STAGE_ORDER):
            raise ReconstructionOrchestrationError(
                "the complete COLMAP/OpenMVS stage order is required"
            )
        for index, (definition, expected) in enumerate(zip(self.stages, STAGE_ORDER)):
            if not isinstance(definition, ReconstructionStageDefinition):
                raise ReconstructionOrchestrationError("stages must contain stage definitions")
            if definition.stage_id != expected:
                raise ReconstructionOrchestrationError(
                    f"stage order mismatch at index {index}: expected {expected}"
                )
            expected_dependencies = () if index == 0 else (STAGE_ORDER[index - 1],)
            if definition.dependencies != expected_dependencies:
                raise ReconstructionOrchestrationError(
                    f"invalid dependencies for {expected}; expected {expected_dependencies}"
                )
        object.__setattr__(self, "workspace", workspace)
        object.__setattr__(self, "stages", tuple(self.stages))
        object.__setattr__(self, "configuration", dict(self.configuration))

    @property
    def configuration_digest(self) -> str:
        return _canonical_digest(
            {
                "contract": ORCHESTRATION_CONTRACT,
                "job_configuration": self.job.configuration,
                "orchestration_configuration": self.configuration,
                "stages": [
                    {
                        "stage_id": item.stage_id,
                        "dependencies": list(item.dependencies),
                        "configuration": item.configuration,
                    }
                    for item in self.stages
                ],
                "backend_provenance": {
                    "backend_id": self.backend_provenance.backend_id.value,
                    "version": self.backend_provenance.version,
                    "build": self.backend_provenance.build,
                    "license_record": self.backend_provenance.license_record,
                    "executable_hashes": dict(self.backend_provenance.executable_hashes),
                },
            }
        )


@dataclass(frozen=True, slots=True)
class ReconstructionOrchestrationResult:
    request: ReconstructionOrchestrationRequest
    status: RunStatus
    stage_results: tuple[ReconstructionStageResult, ...]
    output: ReconstructionOutputManifest | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if self.status is RunStatus.SUCCEEDED and self.output is None:
            raise ReconstructionOrchestrationError(
                "successful orchestration requires an output manifest"
            )
        if self.status is not RunStatus.SUCCEEDED and self.output is not None:
            raise ReconstructionOrchestrationError(
                "failed or cancelled orchestration cannot expose output"
            )
        object.__setattr__(self, "stage_results", tuple(self.stage_results))

    @property
    def source_digest(self) -> str:
        return self.request.job.inputs.source_digest

    @property
    def configuration_digest(self) -> str:
        return self.request.configuration_digest

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": ORCHESTRATION_CONTRACT,
            "status": self.status.value,
            "workspace": self.request.workspace,
            "job_id": self.request.job.job_id,
            "project_id": self.request.job.project_id,
            "project_revision": self.request.job.project_revision,
            "source_revision": self.request.job.inputs.source_revision,
            "source_digest": self.source_digest,
            "configuration_digest": self.configuration_digest,
            "stage_results": [item.as_dict() for item in self.stage_results],
            "output": None if self.output is None else self.output.as_dict(),
            "failure_reason": self.failure_reason,
        }


def _terminal_stage(
    stage_id: str,
    status: StageStatus,
    reason: str,
    *,
    previous: ReconstructionStageResult | None = None,
) -> ReconstructionStageResult:
    return ReconstructionStageResult(
        stage_id,
        status,
        None,
        0.0 if previous is None else max(0.0, previous.duration_seconds),
        stdout="" if previous is None else previous.stdout,
        stderr="" if previous is None else previous.stderr,
        cancelled=status is StageStatus.CANCELLED,
        failure_reason=reason,
    )


class ReconstructionOrchestrator:
    """Execute exactly one validated COLMAP/OpenMVS stage plan."""

    def run(
        self,
        request: ReconstructionOrchestrationRequest,
        cancel: CancelToken | None = None,
    ) -> ReconstructionOrchestrationResult:
        if not isinstance(request, ReconstructionOrchestrationRequest):
            raise ReconstructionOrchestrationError(
                "request must be ReconstructionOrchestrationRequest"
            )
        token = CancelToken() if cancel is None else cancel
        executions: list[ReconstructionStageExecution] = []
        results: list[ReconstructionStageResult] = []

        for definition in request.stages:
            if token.cancelled:
                cancelled = _terminal_stage(
                    definition.stage_id,
                    StageStatus.CANCELLED,
                    "orchestration cancelled before stage execution",
                )
                results.append(cancelled)
                return ReconstructionOrchestrationResult(
                    request,
                    RunStatus.CANCELLED,
                    tuple(results),
                    failure_reason=cancelled.failure_reason,
                )
            context = ReconstructionStageContext(
                request.job,
                request.workspace,
                request.configuration,
                tuple(executions),
                token,
            )
            try:
                execution = definition.execute(context)
                if not isinstance(execution, ReconstructionStageExecution):
                    raise ReconstructionOrchestrationError(
                        "stage adapter returned an invalid execution"
                    )
                if execution.stage_id != definition.stage_id:
                    raise ReconstructionOrchestrationError("stage adapter returned the wrong stage")
            except Exception as error:  # adapters must fail closed at this boundary
                reason = f"{type(error).__name__}: {str(error)[:512]}"
                failed = _terminal_stage(definition.stage_id, StageStatus.FAILED, reason)
                results.append(failed)
                return ReconstructionOrchestrationResult(
                    request, RunStatus.FAILED, tuple(results), failure_reason=reason
                )

            stage_result = execution.stage_result
            if token.cancelled and stage_result.status in {
                StageStatus.SUCCEEDED,
                StageStatus.FAILED,
            }:
                stage_result = _terminal_stage(
                    definition.stage_id,
                    StageStatus.CANCELLED,
                    "cancellation won the stage completion race",
                    previous=stage_result,
                )
            if stage_result.status is StageStatus.CANCELLED:
                results.append(stage_result)
                return ReconstructionOrchestrationResult(
                    request,
                    RunStatus.CANCELLED,
                    tuple(results),
                    failure_reason=stage_result.failure_reason,
                )
            if stage_result.status is StageStatus.FAILED:
                results.append(stage_result)
                return ReconstructionOrchestrationResult(
                    request,
                    RunStatus.FAILED,
                    tuple(results),
                    failure_reason=stage_result.failure_reason,
                )
            if stage_result.status is not StageStatus.SUCCEEDED:
                failed = _terminal_stage(
                    definition.stage_id,
                    StageStatus.FAILED,
                    "stage returned an unknown status",
                    previous=stage_result,
                )
                results.append(failed)
                return ReconstructionOrchestrationResult(
                    request, RunStatus.FAILED, tuple(results), failure_reason=failed.failure_reason
                )
            if not execution.outputs_verified or not execution.output_asset_ids:
                failed = _terminal_stage(
                    definition.stage_id,
                    StageStatus.FAILED,
                    "successful stage did not verify and publish an output identity",
                    previous=stage_result,
                )
                results.append(failed)
                return ReconstructionOrchestrationResult(
                    request, RunStatus.FAILED, tuple(results), failure_reason=failed.failure_reason
                )
            executions.append(execution)
            results.append(stage_result)

        if token.cancelled:
            cancelled = _terminal_stage(
                STAGE_ORDER[-1],
                StageStatus.CANCELLED,
                "cancellation won final manifest publication",
                previous=results[-1],
            )
            results[-1] = cancelled
            return ReconstructionOrchestrationResult(
                request,
                RunStatus.CANCELLED,
                tuple(results),
                failure_reason=cancelled.failure_reason,
            )

        asset_paths = {
            f"{execution.stage_id}:{name}": asset
            for execution in executions
            for name, asset in sorted(execution.output_asset_ids.items())
        }
        output = ReconstructionOutputManifest(
            project_id=request.job.project_id,
            reconstruction_revision=request.workspace.rsplit("/", 1)[-1],
            backend_id=request.backend_provenance.backend_id,
            backend_version=request.backend_provenance.version,
            backend_build=request.backend_provenance.build,
            backend_license=request.backend_provenance.license_record,
            configuration_digest=request.configuration_digest,
            source_input_digest=request.job.inputs.source_digest,
            camera_convention=PACKSCAN_CAMERA_CONVENTION,
            asset_paths=asset_paths,
            scale_state=ScaleState.RELATIVE,
            limitations=(
                "Orchestration output is RECONSTRUCTION_OBSERVATION evidence.",
                "Metric promotion belongs to M09; this result is not Scan Master, CAD, or engineering authority.",
            ),
            stage_results=tuple(results),
            authority_class=RECONSTRUCTION_AUTHORITY_CLASS,
        )
        return ReconstructionOrchestrationResult(
            request, RunStatus.SUCCEEDED, tuple(results), output=output
        )


def orchestrate_reconstruction(
    request: ReconstructionOrchestrationRequest,
    cancel: CancelToken | None = None,
) -> ReconstructionOrchestrationResult:
    return ReconstructionOrchestrator().run(request, cancel)


__all__ = [
    "ORCHESTRATION_CONTRACT",
    "OrchestrationStageId",
    "ReconstructionOrchestrationError",
    "ReconstructionOrchestrationRequest",
    "ReconstructionOrchestrationResult",
    "ReconstructionOrchestrator",
    "ReconstructionStageContext",
    "ReconstructionStageDefinition",
    "ReconstructionStageExecution",
    "STAGE_ORDER",
    "orchestrate_reconstruction",
]
