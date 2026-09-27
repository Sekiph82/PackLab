"""Portable diagnostics for the normalized sparse-mapping result.

This module is a PackLab-owned, backend-neutral boundary over the accepted
``SparseMappingRun`` contract.  A diagnostic policy is explicit and immutable:
zero registered images are always empty, all images registered are complete,
and a partial registration is complete only when it meets both configured
inclusive thresholds.  A threshold that is exactly met therefore passes, and
one just below it is fragmented.

The report contains registration facts and stable remediation text only.  It
does not expose stage stdout/stderr, paths, timestamps, engine discovery, or a
claim that an output asset was materialized on disk.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum

from .reconstruction import ReconstructionStageResult, RunStatus, StageStatus
from .sparse_mapping import (
    MAX_STAGE_IMAGE_COUNT,
    SPARSE_MAPPING_STAGE_ID,
    RegisteredImageStatistics,
    SparseMappingConfig,
    SparseMappingRequest,
    SparseMappingRun,
)

SPARSE_DIAGNOSTICS_CONTRACT = "packlab.sparse-mapping-diagnostics.v1"
SPARSE_DIAGNOSTICS_POLICY_VERSION = "packlab.sparse-mapping-diagnostic-policy.v1"

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class SparseDiagnosticError(ValueError):
    """Base error for invalid diagnostic configuration."""


class InvalidSparseDiagnosticPolicy(SparseDiagnosticError):
    """Raised when diagnostic thresholds are missing, unsafe, or ambiguous."""


class SparseDiagnosticSeverity(StrEnum):
    """Stable report severity, independent of any reconstruction engine."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SparseDiagnosticCode(StrEnum):
    """Stable machine-readable sparse-mapping diagnostic codes."""

    RESULT_INVALID = "sparse_mapping.result_invalid"
    RUN_FAILED = "sparse_mapping.failed"
    RUN_CANCELLED = "sparse_mapping.cancelled"
    REGISTRATION_EMPTY = "sparse_mapping.registration_empty"
    REGISTRATION_FRAGMENTED = "sparse_mapping.registration_fragmented"
    REGISTRATION_COMPLETE = "sparse_mapping.registration_complete"


@dataclass(frozen=True, slots=True)
class SparseDiagnosticPolicy:
    """Explicit inclusive thresholds for partial sparse registration.

    ``minimum_registered_images`` must be at least one and
    ``minimum_registration_ratio`` must be finite and in ``(0, 1]``.  The
    zero-image and all-registered classifications take precedence, so a
    complete registration remains healthy even when a configured count
    threshold is larger than a particular complete input set.
    """

    minimum_registered_images: int
    minimum_registration_ratio: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.minimum_registered_images, bool)
            or not isinstance(self.minimum_registered_images, int)
            or not 1 <= self.minimum_registered_images <= MAX_STAGE_IMAGE_COUNT
        ):
            raise InvalidSparseDiagnosticPolicy(
                "minimum_registered_images must be an integer from 1 to the bounded stage limit"
            )
        if isinstance(self.minimum_registration_ratio, bool) or not isinstance(
            self.minimum_registration_ratio, (int, float)
        ):
            raise InvalidSparseDiagnosticPolicy(
                "minimum_registration_ratio must be a finite number in (0, 1]"
            )
        ratio = float(self.minimum_registration_ratio)
        if not math.isfinite(ratio) or not 0.0 < ratio <= 1.0:
            raise InvalidSparseDiagnosticPolicy(
                "minimum_registration_ratio must be a finite number in (0, 1]"
            )
        object.__setattr__(self, "minimum_registration_ratio", ratio)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": SPARSE_DIAGNOSTICS_POLICY_VERSION,
            "minimum_registered_images": self.minimum_registered_images,
            "minimum_registration_ratio": self.minimum_registration_ratio,
        }

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SparseDiagnosticReport:
    """Stable, portable diagnostic output with no materialization claim."""

    policy: SparseDiagnosticPolicy
    code: SparseDiagnosticCode
    severity: SparseDiagnosticSeverity
    healthy: bool
    message: str
    remediation: str
    status: RunStatus | None = None
    statistics: RegisteredImageStatistics | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.policy, SparseDiagnosticPolicy):
            raise SparseDiagnosticError("diagnostic report requires a diagnostic policy")
        if not isinstance(self.code, SparseDiagnosticCode):
            raise SparseDiagnosticError("diagnostic report has an unknown code")
        if not isinstance(self.severity, SparseDiagnosticSeverity):
            raise SparseDiagnosticError("diagnostic report has an unknown severity")
        if not isinstance(self.healthy, bool):
            raise SparseDiagnosticError("diagnostic report healthy flag must be boolean")
        if not isinstance(self.message, str) or not self.message.strip():
            raise SparseDiagnosticError("diagnostic report message must be non-empty")
        if not isinstance(self.remediation, str) or not self.remediation.strip():
            raise SparseDiagnosticError("diagnostic report remediation must be non-empty")
        if self.status is not None and not isinstance(self.status, RunStatus):
            raise SparseDiagnosticError("diagnostic report has an unknown run status")
        if self.statistics is not None and not isinstance(
            self.statistics, RegisteredImageStatistics
        ):
            raise SparseDiagnosticError("diagnostic report has invalid statistics")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": SPARSE_DIAGNOSTICS_CONTRACT,
            "code": self.code.value,
            "healthy": self.healthy,
            "message": self.message,
            "policy": self.policy.as_dict(),
            "remediation": self.remediation,
            "severity": self.severity.value,
            "statistics": None if self.statistics is None else self.statistics.as_dict(),
            "status": None if self.status is None else self.status.value,
        }

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


def _portable_asset_id(value: object) -> bool:
    if not isinstance(value, str) or not value or _CONTROL.search(value) or "\\" in value:
        return False
    if value.startswith("/") or value.startswith("//") or re.match(r"^[A-Za-z]:", value):
        return False
    parts = value.split("/")
    return ":" not in value and not any(part in {"", ".", ".."} for part in parts)


def _valid_statistics(
    run: SparseMappingRun,
) -> RegisteredImageStatistics | None:
    if not isinstance(run.statistics, RegisteredImageStatistics):
        return None
    try:
        statistics = RegisteredImageStatistics(
            run.statistics.total_images,
            run.statistics.registered_images,
            run.statistics.unregistered_images,
        )
    except (TypeError, ValueError, OverflowError):
        return None
    if not isinstance(run.request, SparseMappingRequest):
        return None
    try:
        if statistics.total_images != len(run.request.image_asset_ids):
            return None
    except (TypeError, ValueError):
        return None
    return statistics


def _valid_run(run: object) -> tuple[bool, RunStatus | None, RegisteredImageStatistics | None]:
    """Recheck the public result invariants and never expose their raw errors."""

    if not isinstance(run, SparseMappingRun):
        return False, None, None
    if not isinstance(run.request, SparseMappingRequest):
        return False, None, None
    if not isinstance(run.stage_result, ReconstructionStageResult):
        return False, None, None
    if not isinstance(run.status, RunStatus):
        return False, None, None
    try:
        if not isinstance(run.request.configuration, SparseMappingConfig):
            return False, None, None
        stage = run.stage_result
        if stage.stage_id != SPARSE_MAPPING_STAGE_ID:
            return False, None, None
        if run.status is RunStatus.SUCCEEDED:
            if stage.status is not StageStatus.SUCCEEDED or stage.cancelled or stage.exit_code != 0:
                return False, None, None
            statistics = _valid_statistics(run)
            if statistics is None or not _portable_asset_id(run.sparse_model_asset_id):
                return False, None, None
            if run.sparse_model_asset_id != run.request.configuration.sparse_output_asset_id:
                return False, None, None
            return True, run.status, statistics
        if run.status is RunStatus.FAILED:
            if stage.status is not StageStatus.FAILED or stage.cancelled:
                return False, None, None
        elif run.status is RunStatus.CANCELLED:
            if stage.status is not StageStatus.CANCELLED or not stage.cancelled:
                return False, None, None
        else:
            return False, None, None
        if run.statistics is not None or run.sparse_model_asset_id is not None:
            return False, None, None
        return True, run.status, None
    except (AttributeError, TypeError, ValueError, OverflowError):
        return False, None, None


def _report(
    policy: SparseDiagnosticPolicy,
    code: SparseDiagnosticCode,
    severity: SparseDiagnosticSeverity,
    healthy: bool,
    message: str,
    remediation: str,
    status: RunStatus | None = None,
    statistics: RegisteredImageStatistics | None = None,
) -> SparseDiagnosticReport:
    return SparseDiagnosticReport(
        policy,
        code,
        severity,
        healthy,
        message,
        remediation,
        status,
        statistics,
    )


def diagnose_sparse_mapping(
    run: SparseMappingRun,
    policy: SparseDiagnosticPolicy,
) -> SparseDiagnosticReport:
    """Classify one normalized sparse-mapping result without probing storage.

    The policy thresholds are inclusive for partial registrations.  The
    function intentionally returns a fail-closed report for an invalid result
    rather than surfacing stage details or treating an output identity as
    proof that a sparse model exists on disk.
    """

    if not isinstance(policy, SparseDiagnosticPolicy):
        raise InvalidSparseDiagnosticPolicy(
            "diagnostics require an explicit SparseDiagnosticPolicy"
        )
    valid, status, statistics = _valid_run(run)
    if not valid:
        return _report(
            policy,
            SparseDiagnosticCode.RESULT_INVALID,
            SparseDiagnosticSeverity.ERROR,
            False,
            "Sparse-mapping result is invalid; no registration health claim was made.",
            "Re-run the sparse-mapping stage and inspect its bounded diagnostics before retrying.",
        )
    if status is RunStatus.FAILED:
        return _report(
            policy,
            SparseDiagnosticCode.RUN_FAILED,
            SparseDiagnosticSeverity.ERROR,
            False,
            "Sparse mapping failed; no registered sparse model is available.",
            "Review the bounded stage diagnostics, correct the capture or mapper inputs, and retry.",
            status,
        )
    if status is RunStatus.CANCELLED:
        return _report(
            policy,
            SparseDiagnosticCode.RUN_CANCELLED,
            SparseDiagnosticSeverity.WARNING,
            False,
            "Sparse mapping was cancelled; no registered sparse model is available.",
            "Run the sparse-mapping stage again after confirming the inputs and available execution time.",
            status,
        )
    if statistics is None:
        return _report(
            policy,
            SparseDiagnosticCode.RESULT_INVALID,
            SparseDiagnosticSeverity.ERROR,
            False,
            "Sparse-mapping result has no usable registration statistics.",
            "Re-run the sparse-mapping stage and require a complete machine-readable summary.",
            status,
        )
    if statistics.registered_images == 0:
        return _report(
            policy,
            SparseDiagnosticCode.REGISTRATION_EMPTY,
            SparseDiagnosticSeverity.ERROR,
            False,
            "Sparse mapping registered no input images.",
            "Capture more overlapping, well-lit views and retry the sparse-mapping stage.",
            status,
            statistics,
        )
    meets_threshold = (
        statistics.registered_images >= policy.minimum_registered_images
        and statistics.registration_ratio >= policy.minimum_registration_ratio
    )
    if statistics.registered_images != statistics.total_images and not meets_threshold:
        return _report(
            policy,
            SparseDiagnosticCode.REGISTRATION_FRAGMENTED,
            SparseDiagnosticSeverity.ERROR,
            False,
            "Sparse mapping registration is fragmented or below the configured thresholds.",
            "Capture targeted views for the unregistered areas, then rerun sparse mapping.",
            status,
            statistics,
        )
    return _report(
        policy,
        SparseDiagnosticCode.REGISTRATION_COMPLETE,
        SparseDiagnosticSeverity.INFO,
        True,
        "Sparse mapping registration meets the configured diagnostic policy.",
        "Continue only after the downstream workflow independently verifies the output asset.",
        status,
        statistics,
    )


diagnose_sparse_mapping_run = diagnose_sparse_mapping


__all__ = [
    "InvalidSparseDiagnosticPolicy",
    "SPARSE_DIAGNOSTICS_CONTRACT",
    "SPARSE_DIAGNOSTICS_POLICY_VERSION",
    "SparseDiagnosticCode",
    "SparseDiagnosticError",
    "SparseDiagnosticPolicy",
    "SparseDiagnosticReport",
    "SparseDiagnosticSeverity",
    "diagnose_sparse_mapping",
    "diagnose_sparse_mapping_run",
]
