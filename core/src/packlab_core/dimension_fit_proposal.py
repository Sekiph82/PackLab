"""Bounded numeric fit proposals; explicit acceptance remains unvalidated geometry."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol, runtime_checkable

from .design_model import (
    DesignModelError,
    DesignModelParameter,
    DesignModelRevision,
    ParameterType,
    revise_design_model_revision,
)

DIMENSION_FIT_PROPOSAL_CONTRACT = "packlab.dimension-fit-proposal.v1"
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$", re.ASCII)
_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.ASCII)


_PROVENANCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+:@-]{0,159}", re.ASCII)


class DimensionFitProposalError(ValueError):
    """Raised when a fit proposal or explicit acceptance violates its contract."""


@dataclass(frozen=True, slots=True)
class MeasuredParameterConstraint:
    parameter_id: str
    measurement_id: str
    measurement_sha256: str
    target_value: float
    tolerance: float
    unit: str
    actor_id: str
    measured_at_utc: str

    def __post_init__(self) -> None:
        for field in ("parameter_id", "measurement_id", "actor_id"):
            _identifier(getattr(self, field), field)
        _digest(self.measurement_sha256, "measurement_sha256")
        object.__setattr__(self, "target_value", _finite(self.target_value, "target_value"))
        object.__setattr__(self, "tolerance", _finite(self.tolerance, "tolerance"))
        if self.target_value <= 0:
            raise DimensionFitProposalError("measurement_target_must_be_positive")
        if self.tolerance <= 0:
            raise DimensionFitProposalError("measurement_tolerance_must_be_positive")
        if self.tolerance >= self.target_value:
            raise DimensionFitProposalError("measurement_tolerance_exceeds_positive_target")
        if not isinstance(self.unit, str) or self.unit not in {
            "reconstruction_units",
            "mm_unverified",
        }:
            raise DimensionFitProposalError("measurement_unit_invalid")
        _utc_timestamp(self.measured_at_utc)

    def as_dict(self) -> dict[str, object]:
        return {
            "parameter_id": self.parameter_id,
            "measurement_id": self.measurement_id,
            "measurement_sha256": self.measurement_sha256,
            "target_value": self.target_value,
            "tolerance": self.tolerance,
            "unit": self.unit,
            "actor_id": self.actor_id,
            "measured_at_utc": self.measured_at_utc,
            "authority_class": "USER_DECLARED_MEASURED_DIMENSION",
        }


@dataclass(frozen=True, slots=True)
class DimensionFitOptimizationRequest:
    model_revision_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    deviation_evidence_sha256: str
    maximum_deviation: float
    constraints: tuple[MeasuredParameterConstraint, ...]

    def __post_init__(self) -> None:
        _identifier(self.model_revision_id, "model_revision_id")
        _identifier(self.scan_master_revision_id, "scan_master_revision_id")
        _digest(self.scan_master_geometry_sha256, "scan_master_geometry_sha256")
        _digest(self.deviation_evidence_sha256, "deviation_evidence_sha256")
        object.__setattr__(
            self, "maximum_deviation", _finite(self.maximum_deviation, "maximum_deviation")
        )
        if self.maximum_deviation < 0:
            raise DimensionFitProposalError("maximum_deviation_must_be_nonnegative")
        if (
            not isinstance(self.constraints, tuple)
            or not 1 <= len(self.constraints) <= 128
            or any(not isinstance(item, MeasuredParameterConstraint) for item in self.constraints)
        ):
            raise DimensionFitProposalError("measured_constraints_required")
        ids = tuple(item.parameter_id for item in self.constraints)
        if len(ids) != len(set(ids)):
            raise DimensionFitProposalError("measured_constraint_parameter_duplicate")
        if ids != tuple(sorted(ids)):
            raise DimensionFitProposalError("measured_constraints_not_canonical")

    def as_dict(self) -> dict[str, object]:
        return {
            "model_revision_id": self.model_revision_id,
            "scan_master_revision_id": self.scan_master_revision_id,
            "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            "deviation_evidence_sha256": self.deviation_evidence_sha256,
            "maximum_deviation": self.maximum_deviation,
            "deviation_is_manufacturing_tolerance": False,
            "constraints": [item.as_dict() for item in self.constraints],
        }


@dataclass(frozen=True, slots=True)
class NumericParameterValue:
    parameter_id: str
    value: float

    def __post_init__(self) -> None:
        _identifier(self.parameter_id, "parameter_id")
        object.__setattr__(self, "value", _finite(self.value, "candidate_value"))

    def as_dict(self) -> dict[str, object]:
        return {"parameter_id": self.parameter_id, "value": self.value}


@dataclass(frozen=True, slots=True)
class DimensionFitCandidate:
    candidate_id: str
    parameter_values: tuple[NumericParameterValue, ...]
    estimated_maximum_deviation: float
    evaluation_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.candidate_id, "candidate_id")
        if (
            not isinstance(self.parameter_values, tuple)
            or not self.parameter_values
            or any(not isinstance(item, NumericParameterValue) for item in self.parameter_values)
        ):
            raise DimensionFitProposalError("candidate_parameter_values_required")
        ids = tuple(item.parameter_id for item in self.parameter_values)
        if len(ids) != len(set(ids)):
            raise DimensionFitProposalError("candidate_parameter_duplicate")
        if ids != tuple(sorted(ids)):
            raise DimensionFitProposalError("candidate_parameters_not_canonical")
        object.__setattr__(
            self,
            "estimated_maximum_deviation",
            _finite(self.estimated_maximum_deviation, "estimated_maximum_deviation"),
        )
        if self.estimated_maximum_deviation < 0:
            raise DimensionFitProposalError("estimated_deviation_must_be_nonnegative")
        _digest(self.evaluation_sha256, "evaluation_sha256")

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "parameter_values": [item.as_dict() for item in self.parameter_values],
            "estimated_maximum_deviation": self.estimated_maximum_deviation,
            "evaluation_sha256": self.evaluation_sha256,
            "deviation_is_manufacturing_tolerance": False,
        }


@dataclass(frozen=True, slots=True)
class DimensionFitProposalProvenance:
    backend_id: str
    model_id: str
    checkpoint_id: str
    version: str
    checkpoint_sha256: str | None = None

    def __post_init__(self) -> None:
        for field in ("backend_id", "model_id", "checkpoint_id", "version"):
            value = getattr(self, field)
            # Opaque identifiers only: no paths, whitespace or control characters (F-3).
            if not isinstance(value, str) or not _PROVENANCE_ID.fullmatch(value):
                raise DimensionFitProposalError(f"{field}_invalid")
        if self.checkpoint_sha256 is not None:
            _digest(self.checkpoint_sha256, "checkpoint_sha256")

    def as_dict(self) -> dict[str, str | None]:
        return {
            "backend_id": self.backend_id,
            "model_id": self.model_id,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_sha256": self.checkpoint_sha256,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class DimensionFitProposal:
    proposal_id: str
    request: DimensionFitOptimizationRequest
    candidates: tuple[DimensionFitCandidate, ...]
    provenance: DimensionFitProposalProvenance

    def __post_init__(self) -> None:
        _identifier(self.proposal_id, "proposal_id")
        if not isinstance(self.request, DimensionFitOptimizationRequest):
            raise DimensionFitProposalError("request_required")
        if not isinstance(self.provenance, DimensionFitProposalProvenance):
            raise DimensionFitProposalError("provenance_required")
        if (
            not isinstance(self.candidates, tuple)
            or not 1 <= len(self.candidates) <= 64
            or any(not isinstance(item, DimensionFitCandidate) for item in self.candidates)
        ):
            raise DimensionFitProposalError("candidates_invalid")
        ids = tuple(item.candidate_id for item in self.candidates)
        if len(ids) != len(set(ids)):
            raise DimensionFitProposalError("candidate_id_duplicate")
        if self.candidates != tuple(
            sorted(
                self.candidates,
                key=lambda item: (item.estimated_maximum_deviation, item.candidate_id),
            )
        ):
            raise DimensionFitProposalError("candidates_not_canonically_ordered")

    @property
    def digest(self) -> str:
        return _canonical_digest(self.as_dict())

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": DIMENSION_FIT_PROPOSAL_CONTRACT,
            "proposal_id": self.proposal_id,
            "request": self.request.as_dict(),
            "candidates": [item.as_dict() for item in self.candidates],
            "provenance": self.provenance.as_dict(),
            "authority_class": "AI_DIMENSION_FIT_PROPOSAL",
            "generated": True,
            "accepted": False,
            "model_mutated": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


@runtime_checkable
class DimensionFitOptimizerBackend(Protocol):
    def optimize(self, request: DimensionFitOptimizationRequest) -> DimensionFitProposal: ...


DeviationEvaluator = Callable[[tuple[NumericParameterValue, ...]], tuple[float, str]]
_GRID_STEPS = 5
_MAX_EVALUATIONS = 625


@dataclass(frozen=True, slots=True)
class BoundedGridFitOptimizer:
    """Deterministic reference optimizer: a bounded grid inside each measured tolerance.

    ``evaluate`` maps candidate parameter values to ``(maximum_scan_deviation,
    evaluation_sha256)``, for example by regenerating the Design Model and comparing it with
    the bound Scan Master. Only candidates within the request's deviation budget are kept,
    best first. Stdlib only, no randomness, no model weights.
    """

    evaluate: DeviationEvaluator
    maximum_candidates: int = 8

    def optimize(self, request: DimensionFitOptimizationRequest) -> DimensionFitProposal:
        if not isinstance(request, DimensionFitOptimizationRequest):
            raise DimensionFitProposalError("request_required")
        if (
            isinstance(self.maximum_candidates, bool)
            or not isinstance(self.maximum_candidates, int)
            or not 1 <= self.maximum_candidates <= 64
        ):
            raise DimensionFitProposalError("maximum_candidates_invalid")
        axes = [
            [
                _within_tolerance(
                    item.target_value + item.tolerance * (2 * step / (_GRID_STEPS - 1) - 1),
                    item.target_value,
                    item.tolerance,
                )
                for step in range(_GRID_STEPS)
            ]
            for item in request.constraints
        ]
        if _GRID_STEPS ** len(axes) > _MAX_EVALUATIONS:
            raise DimensionFitProposalError("grid_search_exceeds_evaluation_bound")
        ids = [item.parameter_id for item in request.constraints]
        scored: list[DimensionFitCandidate] = []
        for index, values in enumerate(itertools.product(*axes)):
            parameters = tuple(
                NumericParameterValue(parameter_id, value)
                for parameter_id, value in zip(ids, values, strict=True)
            )
            result = self.evaluate(parameters)
            if not isinstance(result, tuple) or len(result) != 2:
                raise DimensionFitProposalError("evaluator_result_invalid")
            deviation, evaluation_sha256 = result
            candidate = DimensionFitCandidate(
                f"grid-{index:04d}", parameters, deviation, evaluation_sha256
            )
            if candidate.estimated_maximum_deviation <= request.maximum_deviation:
                scored.append(candidate)
        if not scored:
            raise DimensionFitProposalError("no_candidate_within_deviation_budget")
        scored.sort(key=lambda item: (item.estimated_maximum_deviation, item.candidate_id))
        kept = tuple(scored[: self.maximum_candidates])
        body = {"request": request.as_dict(), "candidates": [item.as_dict() for item in kept]}
        return DimensionFitProposal(
            "dimension-fit-proposal:" + _canonical_digest(body)[:32],
            request,
            kept,
            DimensionFitProposalProvenance(
                "packlab-bounded-grid", "none", "none", f"grid{_GRID_STEPS}-v1"
            ),
        )


@dataclass(frozen=True, slots=True)
class DimensionFitProposalAcceptance:
    acceptance_id: str
    proposal_id: str
    proposal_sha256: str
    source_model_revision_id: str
    accepted_model_revision_id: str
    candidate_id: str
    actor_id: str
    reason: str
    created_at_utc: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.dimension-fit-proposal-acceptance.v1",
            "acceptance_id": self.acceptance_id,
            "proposal_id": self.proposal_id,
            "proposal_sha256": self.proposal_sha256,
            "source_model_revision_id": self.source_model_revision_id,
            "accepted_model_revision_id": self.accepted_model_revision_id,
            "candidate_id": self.candidate_id,
            "authority_class": "USER_CONFIRMED_DESIGN_MODEL_REVISION",
            "actor_id": self.actor_id,
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


@dataclass(frozen=True, slots=True)
class AcceptedDimensionFitProposal:
    model: DesignModelRevision
    acceptance: DimensionFitProposalAcceptance


def create_dimension_fit_request(
    model: DesignModelRevision,
    *,
    deviation_evidence_sha256: str,
    maximum_deviation: float,
    constraints: tuple[MeasuredParameterConstraint, ...],
) -> DimensionFitOptimizationRequest:
    if not isinstance(model, DesignModelRevision):
        raise DimensionFitProposalError("design_model_required")
    if model.fitted_to_scan_master_revision_id is None or model.scan_master_geometry_sha256 is None:
        raise DimensionFitProposalError("captured_scan_master_binding_required")
    request = DimensionFitOptimizationRequest(
        model.revision_id,
        model.fitted_to_scan_master_revision_id,
        model.scan_master_geometry_sha256,
        deviation_evidence_sha256,
        maximum_deviation,
        constraints,
    )
    if any(item.unit != model.coordinate_unit for item in constraints):
        raise DimensionFitProposalError("measurement_unit_model_mismatch")
    parameter_map = {item.parameter_id: item for item in model.parameters}
    for constraint in constraints:
        parameter = parameter_map.get(constraint.parameter_id)
        if (
            parameter is None
            or parameter.value_type is not ParameterType.NUMBER
            or parameter.unit != model.coordinate_unit
        ):
            raise DimensionFitProposalError("constrained_numeric_model_parameter_required")
    return request


def accept_dimension_fit_proposal(
    model: DesignModelRevision,
    proposal: DimensionFitProposal,
    *,
    request: DimensionFitOptimizationRequest,
    candidate_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> AcceptedDimensionFitProposal:
    """Accept one candidate against the request the user created, never the backend's echo."""
    if not isinstance(model, DesignModelRevision) or not isinstance(proposal, DimensionFitProposal):
        raise DimensionFitProposalError("model_and_proposal_required")
    if not isinstance(request, DimensionFitOptimizationRequest):
        raise DimensionFitProposalError("user_request_required")
    # Targets, tolerances, deviation budget and deviation evidence must be exactly what the
    # user requested; a backend cannot widen bounds by echoing a different request.
    if (
        type(proposal.request) is not DimensionFitOptimizationRequest
        or type(request) is not DimensionFitOptimizationRequest
        or proposal.request.as_dict() != request.as_dict()
    ):
        raise DimensionFitProposalError("proposal_request_mismatch")
    if (
        request.model_revision_id != model.revision_id
        or request.scan_master_revision_id != model.fitted_to_scan_master_revision_id
        or request.scan_master_geometry_sha256 != model.scan_master_geometry_sha256
    ):
        raise DimensionFitProposalError("proposal_source_revision_stale")
    candidate = next(
        (item for item in proposal.candidates if item.candidate_id == candidate_id), None
    )
    if candidate is None:
        raise DimensionFitProposalError("candidate_not_in_proposal")
    if candidate.estimated_maximum_deviation > request.maximum_deviation:
        raise DimensionFitProposalError("candidate_exceeds_deviation_budget")
    constraints = {item.parameter_id: item for item in request.constraints}
    changes = {item.parameter_id: item.value for item in candidate.parameter_values}
    if set(changes) != set(constraints):
        raise DimensionFitProposalError("candidate_constraint_set_mismatch")
    existing = {item.parameter_id: item for item in model.parameters}
    updated: list[DesignModelParameter] = []
    for parameter_id, value in changes.items():
        constraint = constraints[parameter_id]
        parameter = existing.get(parameter_id)
        if (
            parameter is None
            or parameter.value_type is not ParameterType.NUMBER
            or parameter.unit != constraint.unit
        ):
            raise DimensionFitProposalError("constrained_numeric_model_parameter_required")
        if abs(value - constraint.target_value) > constraint.tolerance:
            raise DimensionFitProposalError("candidate_outside_measured_dimension_tolerance")
        updated.append(replace(parameter, value=value))
    actor = _bounded_text(actor_id, "actor_id", 128)
    why = _bounded_text(reason, "reason", 512)
    timestamp = _utc_timestamp(created_at_utc)
    updated_by_id = {item.parameter_id: item for item in updated}
    parameters = tuple(updated_by_id.get(item.parameter_id, item) for item in model.parameters)
    try:
        successor = revise_design_model_revision(
            model,
            parameters=parameters,
            features=model.features,
            actor_id=actor,
            reason=why,
            created_at_utc=timestamp,
        )
    except DesignModelError as error:
        raise DimensionFitProposalError(f"design_model_revision_rejected:{error}") from error
    body = {
        "proposal_id": proposal.proposal_id,
        "proposal_sha256": proposal.digest,
        "source_model_revision_id": model.revision_id,
        "accepted_model_revision_id": successor.revision_id,
        "candidate_id": candidate.candidate_id,
        "actor_id": actor,
        "reason": why,
        "created_at_utc": timestamp,
    }
    record = DimensionFitProposalAcceptance(
        acceptance_id="dimension-fit-acceptance:" + _canonical_digest(body),
        proposal_id=proposal.proposal_id,
        proposal_sha256=proposal.digest,
        source_model_revision_id=model.revision_id,
        accepted_model_revision_id=successor.revision_id,
        candidate_id=candidate.candidate_id,
        actor_id=actor,
        reason=why,
        created_at_utc=timestamp,
    )
    return AcceptedDimensionFitProposal(successor, record)


def _within_tolerance(value: float, target: float, tolerance: float) -> float:
    """Step a grid endpoint toward the target until the acceptance check holds exactly.

    Float rounding can place target +/- tolerance a hair outside ``abs(v - t) <= tol``
    (e.g. 31.0 +/- 0.3); proposing such a point would only be rejected at acceptance.
    """
    while abs(value - target) > tolerance:
        value = math.nextafter(value, target)
    return value


def _identifier(value: object, name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise DimensionFitProposalError(f"{name}_invalid")


def _digest(value: object, name: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise DimensionFitProposalError(f"{name}_invalid")


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DimensionFitProposalError(f"{name}_invalid")
    try:
        normalized = float(value)
    except OverflowError as error:
        raise DimensionFitProposalError(f"{name}_invalid") from error
    if not math.isfinite(normalized):
        raise DimensionFitProposalError(f"{name}_invalid")
    return normalized


def _canonical_digest(value: object) -> str:
    try:
        canonical = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
    except (TypeError, ValueError) as error:
        raise DimensionFitProposalError("canonical_serialization_failed") from error
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _bounded_text(value: object, name: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise DimensionFitProposalError(f"{name}_invalid")
    return value


def _utc_timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DimensionFitProposalError("timestamp_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise DimensionFitProposalError("timestamp_invalid") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise DimensionFitProposalError("timestamp_must_be_utc_z")
    return value


__all__ = [
    "AcceptedDimensionFitProposal",
    "BoundedGridFitOptimizer",
    "DeviationEvaluator",
    "DIMENSION_FIT_PROPOSAL_CONTRACT",
    "DimensionFitCandidate",
    "DimensionFitOptimizationRequest",
    "DimensionFitProposal",
    "DimensionFitProposalAcceptance",
    "DimensionFitProposalError",
    "DimensionFitProposalProvenance",
    "DimensionFitOptimizerBackend",
    "MeasuredParameterConstraint",
    "NumericParameterValue",
    "accept_dimension_fit_proposal",
    "create_dimension_fit_request",
]
