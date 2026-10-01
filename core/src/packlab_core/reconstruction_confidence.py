"""Explainable weighted confidence aggregation for versioned reconstruction diagnostics."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

RECONSTRUCTION_CONFIDENCE_CONTRACT: Final = "packlab.reconstruction-confidence.v1"
RECONSTRUCTION_CONFIDENCE_PROFILE_VERSION: Final = "packlab.reconstruction-confidence-profile.v1"
COMPONENT_IDS: Final = (
    "registration",
    "sparse_connectivity",
    "object_coverage",
    "artifact_review",
)
_COMPONENT_CONTRACTS: Final = {
    "registration": "packlab.registered-photo-ratio.v1",
    "sparse_connectivity": "packlab.sparse-connectivity.v1",
    "object_coverage": "packlab.object-geometry-coverage.v1",
    "artifact_review": "packlab.reconstruction-artifact-diagnostics.v1",
}
_SHA256 = re.compile(r"[0-9a-f]{64}")


class ReconstructionConfidenceError(ValueError):
    """Raised when confidence weights or threshold-profile configuration is invalid."""


@dataclass(frozen=True, slots=True)
class ReconstructionConfidenceProfile:
    """Versioned, auditable weights and inclusive minimums for four fixed QA signals."""

    profile_id: str = "reconstruction-confidence-v1"
    registration_weight: float = 0.25
    sparse_connectivity_weight: float = 0.25
    object_coverage_weight: float = 0.30
    artifact_review_weight: float = 0.20
    minimum_registration_score: float = 0.70
    minimum_sparse_connectivity_score: float = 0.70
    minimum_object_coverage_score: float = 0.50
    minimum_artifact_review_score: float = 0.90
    minimum_confidence_score: float = 0.75

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not re.fullmatch(
            r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", self.profile_id
        ):
            raise ReconstructionConfidenceError("profile_id must be a safe identifier")
        for name in (
            "registration_weight",
            "sparse_connectivity_weight",
            "object_coverage_weight",
            "artifact_review_weight",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or value <= 0
            ):
                raise ReconstructionConfidenceError(f"{name} must be finite and greater than zero")
            object.__setattr__(self, name, float(value))
        for name in (
            "minimum_registration_score",
            "minimum_sparse_connectivity_score",
            "minimum_object_coverage_score",
            "minimum_artifact_review_score",
            "minimum_confidence_score",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or not 0 <= value <= 1
            ):
                raise ReconstructionConfidenceError(f"{name} must be finite and within 0..1")
            object.__setattr__(self, name, float(value))

    def as_dict(self) -> dict[str, object]:
        weights = {
            "registration": self.registration_weight,
            "sparse_connectivity": self.sparse_connectivity_weight,
            "object_coverage": self.object_coverage_weight,
            "artifact_review": self.artifact_review_weight,
        }
        weight_total = sum(weights.values())
        return {
            "version": RECONSTRUCTION_CONFIDENCE_PROFILE_VERSION,
            "profile_id": self.profile_id,
            "components": [
                {
                    "component_id": component_id,
                    "contract": _COMPONENT_CONTRACTS[component_id],
                    "weight": weights[component_id],
                    "normalized_weight": weights[component_id] / weight_total,
                    "minimum_component_score": getattr(self, f"minimum_{component_id}_score"),
                }
                for component_id in COMPONENT_IDS
            ],
            "minimum_confidence_score": self.minimum_confidence_score,
            "component_boundaries_inclusive": True,
            "overall_boundary_inclusive": True,
            "missing_data_disposition": "withhold_overall_score_and_threshold_result",
            "required_component_ids": list(COMPONENT_IDS),
        }


@dataclass(frozen=True, slots=True)
class ReconstructionConfidenceReport:
    """Canonical component-by-component confidence explanation."""

    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.payload, sort_keys=True, allow_nan=False))

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class _ComponentResult:
    status: str
    score: float | None
    report_digest: str | None
    input_metrics: dict[str, object]
    score_formula: str
    reason: str | None = None


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _report_payload(value: object) -> dict[str, object] | None:
    if isinstance(value, Mapping):
        try:
            normalized = json.loads(json.dumps(dict(value), sort_keys=True, allow_nan=False))
        except (TypeError, ValueError):
            return None
        return normalized if isinstance(normalized, dict) else None
    as_dict = getattr(value, "as_dict", None)
    if callable(as_dict):
        try:
            normalized = as_dict()
            if isinstance(normalized, Mapping):
                result = json.loads(json.dumps(dict(normalized), sort_keys=True, allow_nan=False))
                return result if isinstance(result, dict) else None
        except (AttributeError, TypeError, ValueError):
            return None
    return None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    converted = float(value)
    if not math.isfinite(converted) or not 0 <= converted <= 1:
        return None
    return converted


def _count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _component_result(component_id: str, value: object) -> _ComponentResult:
    formula = {
        "registration": "registered_photos / total_input_photos",
        "sparse_connectivity": "(largest_component_ratio + (1 - isolated_node_ratio)) / 2",
        "object_coverage": "(selected_point_ratio + mean_selected_support_ratio + mean_projected_occupancy_ratio) / 3",
        "artifact_review": "1 - review_candidate_component_count / component_count",
    }[component_id]
    if value is None:
        return _ComponentResult("missing", None, None, {}, formula, "report_not_supplied")
    payload = _report_payload(value)
    if payload is None:
        return _ComponentResult("invalid", None, None, {}, formula, "report_malformed")
    report_digest = _canonical_digest(payload)
    expected_contract = _COMPONENT_CONTRACTS[component_id]
    if payload.get("contract") != expected_contract:
        return _ComponentResult(
            "invalid", None, report_digest, {}, formula, "component_contract_mismatch"
        )
    if payload.get("acceptance_status") != "not_evaluated":
        return _ComponentResult(
            "invalid", None, report_digest, {}, formula, "component_authority_invalid"
        )
    if payload.get("observation_status") != "observed":
        return _ComponentResult(
            "missing",
            None,
            report_digest,
            {},
            formula,
            f"observation_{payload.get('observation_status', 'unknown')}",
        )
    statistics = payload.get("statistics")
    if component_id == "sparse_connectivity":
        statistics = payload.get("graph")
    if not isinstance(statistics, dict):
        return _ComponentResult("invalid", None, report_digest, {}, formula, "statistics_missing")

    if component_id == "registration":
        total = _count(statistics.get("total_input_photos"))
        registered = _count(statistics.get("registered_photos"))
        score = _number(statistics.get("registration_ratio"))
        if total is None or total == 0 or registered is None or registered > total:
            score = None
        elif score is None or not math.isclose(
            score, registered / total, rel_tol=1e-12, abs_tol=1e-12
        ):
            score = None
        metrics: dict[str, object] = {
            "registered_photos": registered,
            "total_input_photos": total,
            "registration_ratio": score,
        }
    elif component_id == "sparse_connectivity":
        node_count = _count(statistics.get("node_count"))
        largest = _number(statistics.get("largest_component_ratio"))
        isolated = _number(statistics.get("isolated_node_ratio"))
        score = (
            (largest + 1 - isolated) / 2
            if node_count and largest is not None and isolated is not None
            else None
        )
        metrics = {
            "node_count": node_count,
            "largest_component_ratio": largest,
            "isolated_node_ratio": isolated,
        }
    elif component_id == "object_coverage":
        candidate_count = _count(statistics.get("candidate_point_count"))
        selected_count = _count(statistics.get("selected_point_count"))
        selected = _number(statistics.get("selected_point_ratio"))
        multiview = statistics.get("multiview_support")
        coverage = statistics.get("coverage")
        support = _number(
            multiview.get("mean_support_ratio_per_selected_point")
            if isinstance(multiview, dict)
            else None
        )
        projected = _number(
            coverage.get("mean_projected_occupancy_ratio") if isinstance(coverage, dict) else None
        )
        if (
            candidate_count is None
            or candidate_count == 0
            or selected_count is None
            or selected_count > candidate_count
            or selected is None
            or not math.isclose(
                selected, selected_count / candidate_count, rel_tol=1e-12, abs_tol=1e-12
            )
            or support is None
            or projected is None
            or selected_count == 0
        ):
            score = None
        else:
            score = (selected + support + projected) / 3
        metrics = {
            "candidate_point_count": candidate_count,
            "selected_point_count": selected_count,
            "selected_point_ratio": selected,
            "mean_selected_support_ratio": support,
            "mean_projected_occupancy_ratio": projected,
        }
    else:
        candidates = _count(statistics.get("candidate_count"))
        component_count = _count(statistics.get("component_count"))
        if (
            candidates is None
            or component_count is None
            or component_count == 0
            or candidates > component_count
        ):
            score = None
        else:
            score = 1 - candidates / component_count
        candidate_fraction = (
            candidates / component_count
            if candidates is not None and component_count is not None and component_count > 0
            else None
        )
        metrics = {
            "review_candidate_component_count": candidates,
            "component_count": component_count,
            "candidate_component_fraction": candidate_fraction,
        }
    if score is None:
        return _ComponentResult(
            "invalid", None, report_digest, metrics, formula, "component_metric_invalid"
        )
    return _ComponentResult("observed", score, report_digest, metrics, formula)


def _provenance_error(reports: Mapping[str, dict[str, object]]) -> str | None:
    ratio_evidence = reports["registration"].get("source_evidence")
    connectivity_evidence = reports["sparse_connectivity"].get("source_evidence")
    coverage_evidence = reports["object_coverage"].get("source_evidence")
    artifact_evidence = reports["artifact_review"].get("source_evidence")
    if not all(
        isinstance(item, dict)
        for item in (ratio_evidence, connectivity_evidence, coverage_evidence, artifact_evidence)
    ):
        return "component_source_evidence_missing"
    assert isinstance(ratio_evidence, dict)
    assert isinstance(connectivity_evidence, dict)
    assert isinstance(coverage_evidence, dict)
    assert isinstance(artifact_evidence, dict)
    parents = coverage_evidence.get("parents")
    if not isinstance(parents, dict):
        return "object_geometry_parent_evidence_missing"
    ratio_digest = ratio_evidence.get("source_sha256")
    request_digest = ratio_evidence.get("request_sha256")
    stage_digest = ratio_evidence.get("stage_evidence_sha256")
    source_revision = ratio_evidence.get("source_revision")
    if not isinstance(ratio_digest, str) or not _SHA256.fullmatch(ratio_digest):
        return "source_digest_invalid"
    if not isinstance(request_digest, str) or not _SHA256.fullmatch(request_digest):
        return "request_digest_invalid"
    if not isinstance(stage_digest, str) or not _SHA256.fullmatch(stage_digest):
        return "stage_digest_invalid"
    if ratio_digest != parents.get("source_input_digest") or ratio_digest != artifact_evidence.get(
        "source_input_digest"
    ):
        return "source_revision_digest_mismatch"
    if not isinstance(source_revision, str) or source_revision != parents.get("source_revision"):
        return "source_revision_identity_mismatch"
    if request_digest != connectivity_evidence.get(
        "request_sha256"
    ) or stage_digest != connectivity_evidence.get("stage_evidence_sha256"):
        return "sparse_stage_provenance_mismatch"
    if (
        parents.get("project_id") != artifact_evidence.get("project_id")
        or parents.get("reconstruction_revision")
        != artifact_evidence.get("reconstruction_revision")
        or coverage_evidence.get("geometry_id") != artifact_evidence.get("geometry_id")
        or parents.get("mask_set_revision_id") != artifact_evidence.get("mask_set_revision_id")
        or parents.get("mask_set_revision_digest")
        != artifact_evidence.get("mask_set_revision_digest")
    ):
        return "object_geometry_provenance_mismatch"
    return None


def build_reconstruction_confidence_report(
    registration_report: object | None,
    sparse_connectivity_report: object | None,
    object_coverage_report: object | None,
    artifact_report: object | None,
    *,
    profile: ReconstructionConfidenceProfile = ReconstructionConfidenceProfile(),
) -> ReconstructionConfidenceReport:
    """Combine fixed versioned diagnostics; withhold the overall score if any are missing."""
    if not isinstance(profile, ReconstructionConfidenceProfile):
        raise ReconstructionConfidenceError(
            "an explicit ReconstructionConfidenceProfile is required"
        )
    values = {
        "registration": registration_report,
        "sparse_connectivity": sparse_connectivity_report,
        "object_coverage": object_coverage_report,
        "artifact_review": artifact_report,
    }
    weights = {
        "registration": profile.registration_weight,
        "sparse_connectivity": profile.sparse_connectivity_weight,
        "object_coverage": profile.object_coverage_weight,
        "artifact_review": profile.artifact_review_weight,
    }
    thresholds = {
        component_id: getattr(profile, f"minimum_{component_id}_score")
        for component_id in COMPONENT_IDS
    }
    results = {
        component_id: _component_result(component_id, values[component_id])
        for component_id in COMPONENT_IDS
    }
    reports = {
        component_id: payload
        for component_id, value in values.items()
        if (payload := _report_payload(value)) is not None
        and payload.get("observation_status") == "observed"
    }
    invalid_components = [
        component_id for component_id, result in results.items() if result.status == "invalid"
    ]
    missing_components = [
        component_id for component_id, result in results.items() if result.status == "missing"
    ]
    provenance_issue = (
        _provenance_error(reports) if not missing_components and not invalid_components else None
    )
    available_weight = sum(
        weights[component_id]
        for component_id, result in results.items()
        if result.status == "observed"
    )
    partial_weighted_score = (
        sum(
            weights[component_id] * result.score
            for component_id, result in results.items()
            if result.status == "observed" and result.score is not None
        )
        / available_weight
        if available_weight
        else None
    )
    complete = not missing_components and not invalid_components and provenance_issue is None
    confidence_score = partial_weighted_score if complete else None
    component_thresholds_met = complete and all(
        results[component_id].score is not None
        and results[component_id].score >= thresholds[component_id]
        for component_id in COMPONENT_IDS
    )
    threshold_status = (
        "not_evaluated"
        if not complete
        else "meets_profile"
        if component_thresholds_met
        and confidence_score is not None
        and confidence_score >= profile.minimum_confidence_score
        else "below_profile"
    )
    observation_status = (
        "invalid"
        if invalid_components or provenance_issue is not None
        else "incomplete"
        if missing_components
        else "observed"
    )
    components: list[dict[str, object]] = []
    report_digests: dict[str, str | None] = {}
    for component_id in COMPONENT_IDS:
        result = results[component_id]
        normalized_weight = weights[component_id] / sum(weights.values())
        contribution = (
            None
            if result.status != "observed" or result.score is None
            else normalized_weight * result.score
        )
        report_digests[component_id] = result.report_digest
        components.append(
            {
                "component_id": component_id,
                "contract": _COMPONENT_CONTRACTS[component_id],
                "observation_status": result.status,
                "score": result.score,
                "weight": weights[component_id],
                "normalized_weight": normalized_weight,
                "weighted_contribution": contribution,
                "minimum_component_score": thresholds[component_id],
                "threshold_met": None
                if result.score is None
                else result.score >= thresholds[component_id],
                "score_formula": result.score_formula,
                "input_metrics": result.input_metrics,
                "source_report_sha256": result.report_digest,
                "reason_code": result.reason,
            }
        )
    return ReconstructionConfidenceReport(
        {
            "contract": RECONSTRUCTION_CONFIDENCE_CONTRACT,
            "authority": "diagnostic_only_no_physical_accuracy_or_acceptance_claim",
            "observation_status": observation_status,
            "threshold_status": threshold_status,
            "acceptance_status": "not_evaluated",
            "confidence_score": confidence_score,
            "partial_weighted_score": partial_weighted_score,
            "component_thresholds_met": component_thresholds_met if complete else None,
            "missing_component_ids": missing_components,
            "invalid_component_ids": invalid_components,
            "missing_data_disposition": "overall_score_withheld_when_any_required_component_missing",
            "provenance_status": "invalid"
            if provenance_issue
            else "verified"
            if complete
            else "partial",
            "provenance_reason_code": provenance_issue,
            "source_report_digests": report_digests,
            "components": components,
            "threshold_profile": profile.as_dict(),
            "aggregation": {
                "method": "normalized_weighted_arithmetic_mean",
                "available_weight": available_weight,
                "total_weight": sum(weights.values()),
                "partial_score_is_not_confidence": True,
                "physical_accuracy_claimed": False,
            },
            "diagnostics": []
            if provenance_issue is None
            else [{"code": provenance_issue, "severity": "error"}],
        }
    )
