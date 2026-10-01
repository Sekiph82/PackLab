"""Fail-closed, read-only quality gate before downstream parametric fitting."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from .object_geometry_coverage import (
    OBJECT_GEOMETRY_COVERAGE_POLICY_VERSION,
    ObjectGeometryCoveragePolicy,
    build_object_geometry_coverage_report,
)
from .object_mask_lifting import ObjectCaptureGeometry
from .reconstruction import ScaleState

CAPTURED_GEOMETRY_FIT_GATE_CONTRACT: Final = "packlab.captured-geometry-fit-gate.v1"
CAPTURED_GEOMETRY_FIT_GATE_POLICY_VERSION: Final = "packlab.captured-geometry-fit-gate-policy.v1"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMPONENT_IDS = (
    "registration",
    "sparse_connectivity",
    "object_coverage",
    "artifact_review",
)
_COMPONENT_CONTRACTS = {
    "registration": "packlab.registered-photo-ratio.v1",
    "sparse_connectivity": "packlab.sparse-connectivity.v1",
    "object_coverage": "packlab.object-geometry-coverage.v1",
    "artifact_review": "packlab.reconstruction-artifact-diagnostics.v1",
}


class CapturedGeometryFitGateError(ValueError):
    """Raised when downstream gate thresholds are invalid."""


@dataclass(frozen=True, slots=True)
class CapturedGeometryFitGatePolicy:
    """Minimum captured-geometry and explainable QA thresholds for fit eligibility."""

    profile_id: str = "captured-geometry-fit-gate-v1"
    minimum_confidence_score: float = 0.75
    minimum_registration_score: float = 0.70
    minimum_sparse_connectivity_score: float = 0.70
    minimum_object_coverage_score: float = 0.50
    minimum_artifact_review_score: float = 0.90
    minimum_selected_point_ratio: float = 0.50
    minimum_mean_support_ratio: float = 0.70
    minimum_projected_occupancy_ratio: float = 0.10

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not re.fullmatch(
            r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", self.profile_id
        ):
            raise CapturedGeometryFitGateError("profile_id must be a safe identifier")
        for name in (
            "minimum_confidence_score",
            "minimum_registration_score",
            "minimum_sparse_connectivity_score",
            "minimum_object_coverage_score",
            "minimum_artifact_review_score",
            "minimum_selected_point_ratio",
            "minimum_mean_support_ratio",
            "minimum_projected_occupancy_ratio",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or not 0 <= value <= 1
            ):
                raise CapturedGeometryFitGateError(f"{name} must be finite and within 0..1")
            object.__setattr__(self, name, float(value))

    def as_dict(self) -> dict[str, object]:
        return {
            "version": CAPTURED_GEOMETRY_FIT_GATE_POLICY_VERSION,
            "profile_id": self.profile_id,
            "minimum_confidence_score": self.minimum_confidence_score,
            "minimum_component_scores": {
                "registration": self.minimum_registration_score,
                "sparse_connectivity": self.minimum_sparse_connectivity_score,
                "object_coverage": self.minimum_object_coverage_score,
                "artifact_review": self.minimum_artifact_review_score,
            },
            "minimum_object_geometry_metrics": {
                "selected_point_ratio": self.minimum_selected_point_ratio,
                "mean_support_ratio": self.minimum_mean_support_ratio,
                "mean_projected_occupancy_ratio": self.minimum_projected_occupancy_ratio,
            },
            "boundaries_inclusive": True,
        }


@dataclass(frozen=True, slots=True)
class CapturedGeometryFitGateReport:
    """Gate decision and actionable diagnostics; no fitting or geometry mutation occurs."""

    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.payload, sort_keys=True, allow_nan=False))

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


def _sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _finite_ratio(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) and 0 <= result <= 1 else None


def _nonnegative_count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _explained_component_score(component_id: str, metrics: object) -> tuple[str, float | None]:
    if not isinstance(metrics, dict):
        return "", None
    if component_id == "registration":
        formula = "registered_photos / total_input_photos"
        registered = _nonnegative_count(metrics.get("registered_photos"))
        total = _nonnegative_count(metrics.get("total_input_photos"))
        if total is None or total == 0 or registered is None or registered > total:
            return formula, None
        return formula, registered / total
    if component_id == "sparse_connectivity":
        formula = "(largest_component_ratio + (1 - isolated_node_ratio)) / 2"
        largest = _finite_ratio(metrics.get("largest_component_ratio"))
        isolated = _finite_ratio(metrics.get("isolated_node_ratio"))
        if largest is None or isolated is None:
            return formula, None
        return formula, (largest + 1 - isolated) / 2
    if component_id == "object_coverage":
        formula = "(selected_point_ratio + mean_selected_support_ratio + mean_projected_occupancy_ratio) / 3"
        selected = _finite_ratio(metrics.get("selected_point_ratio"))
        support = _finite_ratio(metrics.get("mean_selected_support_ratio"))
        projected = _finite_ratio(metrics.get("mean_projected_occupancy_ratio"))
        if selected is None or support is None or projected is None:
            return formula, None
        return formula, (selected + support + projected) / 3
    formula = "1 - review_candidate_component_count / component_count"
    candidates = _nonnegative_count(metrics.get("review_candidate_component_count"))
    count = _nonnegative_count(metrics.get("component_count"))
    if candidates is None or count is None or count == 0 or candidates > count:
        return formula, None
    return formula, 1 - candidates / count


def _report_payload(value: object) -> dict[str, object] | None:
    if isinstance(value, Mapping):
        try:
            result = json.loads(json.dumps(dict(value), sort_keys=True, allow_nan=False))
        except (TypeError, ValueError):
            return None
        return result if isinstance(result, dict) else None
    as_dict = getattr(value, "as_dict", None)
    if callable(as_dict):
        try:
            result = as_dict()
            if isinstance(result, Mapping):
                normalized = json.loads(json.dumps(dict(result), sort_keys=True, allow_nan=False))
                return normalized if isinstance(normalized, dict) else None
        except (AttributeError, TypeError, ValueError):
            return None
    return None


def _coverage_policy(payload: dict[str, object]) -> ObjectGeometryCoveragePolicy | None:
    policy = payload.get("policy")
    if (
        not isinstance(policy, dict)
        or policy.get("version") != OBJECT_GEOMETRY_COVERAGE_POLICY_VERSION
    ):
        return None
    try:
        return ObjectGeometryCoveragePolicy(
            profile_id=policy["profile_id"],
            grid_resolution=policy["grid_resolution"],
            minimum_selected_point_ratio=policy["minimum_selected_point_ratio"],
            minimum_mean_support_ratio=policy["minimum_mean_support_ratio"],
            minimum_projected_coverage_ratio=policy["minimum_projected_coverage_ratio"],
        )
    except (KeyError, TypeError, ValueError):
        return None


def _confidence_decision(
    payload: dict[str, object],
    coverage_digest: str,
    coverage_metrics: dict[str, float],
    policy: CapturedGeometryFitGatePolicy,
) -> tuple[list[dict[str, str]], float | None]:
    diagnostics: list[dict[str, str]] = []
    if payload.get("contract") != "packlab.reconstruction-confidence.v1":
        return [
            {
                "code": "confidence_contract_invalid",
                "action": "Regenerate PL-0199 confidence evidence.",
            }
        ], None
    if (
        payload.get("observation_status") != "observed"
        or payload.get("threshold_status") != "meets_profile"
        or payload.get("acceptance_status") != "not_evaluated"
        or payload.get("provenance_status") != "verified"
        or payload.get("component_thresholds_met") is not True
        or payload.get("missing_component_ids") != []
        or payload.get("invalid_component_ids") != []
    ):
        diagnostics.append(
            {
                "code": "confidence_evidence_incomplete",
                "action": "Resolve missing or below-profile QA evidence.",
            }
        )
    source_digests = payload.get("source_report_digests")
    components = payload.get("components")
    if not isinstance(source_digests, dict) or not isinstance(components, list):
        return diagnostics + [
            {
                "code": "confidence_components_missing",
                "action": "Regenerate complete PL-0199 component evidence.",
            }
        ], None
    component_map = {
        item["component_id"]: item
        for item in components
        if isinstance(item, dict) and isinstance(item.get("component_id"), str)
    }
    if set(component_map) != set(_COMPONENT_IDS) or len(components) != len(_COMPONENT_IDS):
        diagnostics.append(
            {
                "code": "confidence_component_set_invalid",
                "action": "Provide all four required QA component reports.",
            }
        )
        return diagnostics, None
    if source_digests.get("object_coverage") != coverage_digest:
        diagnostics.append(
            {
                "code": "coverage_report_identity_mismatch",
                "action": "Regenerate confidence from this exact coverage report.",
            }
        )
    profile = payload.get("threshold_profile")
    profile_components = profile.get("components") if isinstance(profile, dict) else None
    if (
        not isinstance(profile, dict)
        or profile.get("version") != "packlab.reconstruction-confidence-profile.v1"
        or profile.get("required_component_ids") != list(_COMPONENT_IDS)
        or profile.get("missing_data_disposition") != "withhold_overall_score_and_threshold_result"
        or not isinstance(profile_components, list)
        or len(profile_components) != len(_COMPONENT_IDS)
    ):
        diagnostics.append(
            {
                "code": "confidence_threshold_profile_invalid",
                "action": "Use the versioned four-component confidence profile.",
            }
        )
        profile_component_map: dict[str, dict[str, object]] = {}
    else:
        profile_component_map = {
            item["component_id"]: item
            for item in profile_components
            if isinstance(item, dict) and isinstance(item.get("component_id"), str)
        }
        if set(profile_component_map) != set(_COMPONENT_IDS):
            diagnostics.append(
                {
                    "code": "confidence_threshold_profile_invalid",
                    "action": "Use the versioned four-component confidence profile.",
                }
            )
    component_minimums = {
        "registration": policy.minimum_registration_score,
        "sparse_connectivity": policy.minimum_sparse_connectivity_score,
        "object_coverage": policy.minimum_object_coverage_score,
        "artifact_review": policy.minimum_artifact_review_score,
    }
    normalized_weight_total = 0.0
    calculated_total = 0.0
    for component_id in _COMPONENT_IDS:
        item = component_map[component_id]
        score = _finite_ratio(item.get("score"))
        weight = _finite_ratio(item.get("normalized_weight"))
        contribution = _finite_ratio(item.get("weighted_contribution"))
        profile_item = profile_component_map.get(component_id)
        profile_minimum = (
            _finite_ratio(profile_item.get("minimum_component_score"))
            if profile_item is not None
            else None
        )
        formula = item.get("score_formula")
        input_metrics = item.get("input_metrics")
        expected_formula, explained_score = _explained_component_score(component_id, input_metrics)
        if (
            item.get("observation_status") != "observed"
            or item.get("contract") != _COMPONENT_CONTRACTS[component_id]
            or score is None
            or weight is None
            or weight == 0
            or contribution is None
            or not math.isclose(contribution, score * weight, rel_tol=1e-12, abs_tol=1e-12)
            or not _sha256(item.get("source_report_sha256"))
            or source_digests.get(component_id) != item.get("source_report_sha256")
            or not isinstance(formula, str)
            or formula != expected_formula
            or not isinstance(input_metrics, dict)
            or explained_score is None
            or score is None
            or not math.isclose(score, explained_score, rel_tol=1e-12, abs_tol=1e-12)
            or profile_item is None
            or profile_item.get("contract") != _COMPONENT_CONTRACTS[component_id]
            or profile_minimum is None
            or item.get("minimum_component_score") != profile_minimum
            or item.get("threshold_met") is not (score is not None and score >= profile_minimum)
            or not math.isclose(
                weight,
                _finite_ratio(profile_item.get("normalized_weight")) or 0.0,
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        ):
            diagnostics.append(
                {
                    "code": f"{component_id}_component_invalid",
                    "action": "Regenerate this versioned QA component.",
                }
            )
            continue
        normalized_weight_total += weight
        calculated_total += contribution
        if score < component_minimums[component_id]:
            diagnostics.append(
                {
                    "code": f"{component_id}_below_fit_threshold",
                    "action": "Improve captured geometry quality before fitting.",
                }
            )
    if not math.isclose(normalized_weight_total, 1.0, rel_tol=1e-12, abs_tol=1e-12):
        diagnostics.append(
            {
                "code": "confidence_weights_invalid",
                "action": "Regenerate confidence with normalized component weights.",
            }
        )
    confidence_score = _finite_ratio(payload.get("confidence_score"))
    if confidence_score is None or not math.isclose(
        confidence_score, calculated_total, rel_tol=1e-12, abs_tol=1e-12
    ):
        diagnostics.append(
            {
                "code": "confidence_score_inconsistent",
                "action": "Regenerate internally consistent confidence evidence.",
            }
        )
        confidence_score = None
    if confidence_score is not None and confidence_score < policy.minimum_confidence_score:
        diagnostics.append(
            {
                "code": "confidence_below_fit_threshold",
                "action": "Meet the fit gate confidence threshold.",
            }
        )
    profile_minimum_confidence = (
        _finite_ratio(profile.get("minimum_confidence_score"))
        if isinstance(profile, dict)
        else None
    )
    if (
        profile_minimum_confidence is None
        or confidence_score is None
        or confidence_score < profile_minimum_confidence
    ):
        diagnostics.append(
            {
                "code": "confidence_profile_threshold_not_met",
                "action": "Meet the reported PL-0199 overall confidence threshold.",
            }
        )
    coverage_component = component_map["object_coverage"]
    metrics = coverage_component.get("input_metrics")
    if not isinstance(metrics, dict) or any(
        _finite_ratio(metrics.get(metric_name)) != expected
        for metric_name, expected in (
            ("selected_point_ratio", coverage_metrics["selected_point_ratio"]),
            ("mean_selected_support_ratio", coverage_metrics["mean_support_ratio"]),
            ("mean_projected_occupancy_ratio", coverage_metrics["mean_projected_occupancy_ratio"]),
        )
    ):
        diagnostics.append(
            {
                "code": "coverage_component_metrics_mismatch",
                "action": "Regenerate confidence from the current geometry coverage report.",
            }
        )
    return diagnostics, confidence_score


def build_captured_geometry_fit_gate_report(
    geometry: object,
    coverage_report: object,
    confidence_report: object,
    *,
    policy: CapturedGeometryFitGatePolicy = CapturedGeometryFitGatePolicy(),
) -> CapturedGeometryFitGateReport:
    """Require current captured geometry and explainable QA before downstream fit use."""
    if not isinstance(policy, CapturedGeometryFitGatePolicy):
        raise CapturedGeometryFitGateError("an explicit CapturedGeometryFitGatePolicy is required")
    diagnostics: list[dict[str, str]] = []
    authority = getattr(geometry, "authority_class", None)
    if isinstance(geometry, Mapping):
        authority = geometry.get("authority_class")
    if authority == "AI_VISUAL_REFERENCE":
        diagnostics.append(
            {
                "code": "ai_visual_reference_rejected",
                "action": "Use captured OBJECT_CAPTURE_GEOMETRY for downstream fitting.",
            }
        )
    if not isinstance(geometry, ObjectCaptureGeometry):
        diagnostics.append(
            {
                "code": "captured_geometry_missing",
                "action": "Provide a revision-bound ObjectCaptureGeometry.",
            }
        )
        return _gate_report(geometry, None, None, diagnostics, policy, None)
    if geometry.generated is not False:
        diagnostics.append(
            {
                "code": "generated_geometry_rejected",
                "action": "Use captured geometry with generated=false.",
            }
        )
    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY":
        diagnostics.append(
            {
                "code": "geometry_authority_invalid",
                "action": "Only OBJECT_CAPTURE_GEOMETRY can pass this gate.",
            }
        )
    if not isinstance(geometry.scale_state, ScaleState):
        diagnostics.append(
            {
                "code": "geometry_scale_state_missing",
                "action": "Restore a declared RELATIVE or METRIC_UNVERIFIED scale state.",
            }
        )
    elif geometry.scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        diagnostics.append(
            {
                "code": "geometry_scale_state_invalid",
                "action": "Use a non-promoted M08 scale state.",
            }
        )
    try:
        parent_identity_valid = (
            all(
                isinstance(value, str) and value.strip()
                for value in (
                    geometry.project_id,
                    geometry.source_revision,
                    geometry.reconstruction_revision,
                    geometry.camera_solution_revision,
                    geometry.mask_set_revision_id,
                )
            )
            and _sha256(geometry.source_input_digest)
            and _sha256(geometry.mask_set_revision_digest)
            and isinstance(geometry.geometry_id, str)
            and re.fullmatch(r"object-geometry:[0-9a-f]{64}", geometry.geometry_id) is not None
            and isinstance(geometry.point_count, int)
            and not isinstance(geometry.point_count, bool)
            and geometry.point_count > 0
            and geometry.point_count == len(geometry.filtered_points)
            and geometry.point_count == len(geometry.unfiltered_points)
            and geometry.filtered_points == geometry.unfiltered_points
        )
    except (AttributeError, TypeError, ValueError):
        parent_identity_valid = False
    if not parent_identity_valid:
        diagnostics.append(
            {
                "code": "geometry_parent_identity_invalid",
                "action": "Regenerate geometry from valid current source, reconstruction, camera, and mask revisions.",
            }
        )
    coverage = _report_payload(coverage_report)
    coverage_policy = _coverage_policy(coverage) if coverage is not None else None
    if coverage is None or coverage_policy is None:
        diagnostics.append(
            {
                "code": "coverage_evidence_missing",
                "action": "Provide a versioned PL-0197 object coverage report.",
            }
        )
        coverage_metrics = None
        coverage_sha = None
    else:
        try:
            reproduced_coverage = build_object_geometry_coverage_report(
                geometry, policy=coverage_policy
            ).as_dict()
        except (AttributeError, TypeError, ValueError, OverflowError):
            reproduced_coverage = None
        if reproduced_coverage != coverage:
            diagnostics.append(
                {
                    "code": "coverage_parent_identity_mismatch",
                    "action": "Regenerate the coverage report from the current geometry object.",
                }
            )
        statistics = coverage.get("statistics")
        coverage_status = coverage.get("observation_status")
        if coverage_status != "observed" or not isinstance(statistics, dict):
            diagnostics.append(
                {
                    "code": "coverage_observation_unavailable",
                    "action": "Produce non-empty valid object coverage evidence.",
                }
            )
            coverage_metrics = None
        else:
            multiview = statistics.get("multiview_support")
            projected = statistics.get("coverage")
            selected_ratio = _finite_ratio(statistics.get("selected_point_ratio"))
            mean_support = _finite_ratio(
                multiview.get("mean_support_ratio_per_selected_point")
                if isinstance(multiview, dict)
                else None
            )
            projected_occupancy = _finite_ratio(
                projected.get("mean_projected_occupancy_ratio")
                if isinstance(projected, dict)
                else None
            )
            if selected_ratio is None or mean_support is None or projected_occupancy is None:
                diagnostics.append(
                    {
                        "code": "coverage_metrics_invalid",
                        "action": "Regenerate valid PL-0197 coverage statistics.",
                    }
                )
                coverage_metrics = None
            else:
                coverage_metrics = {
                    "selected_point_ratio": selected_ratio,
                    "mean_support_ratio": mean_support,
                    "mean_projected_occupancy_ratio": projected_occupancy,
                }
                if selected_ratio < policy.minimum_selected_point_ratio:
                    diagnostics.append(
                        {
                            "code": "coverage_selected_point_ratio_below_threshold",
                            "action": "Increase the selected captured-point ratio.",
                        }
                    )
                if mean_support < policy.minimum_mean_support_ratio:
                    diagnostics.append(
                        {
                            "code": "coverage_multiview_support_below_threshold",
                            "action": "Capture stronger multiview support.",
                        }
                    )
                if projected_occupancy < policy.minimum_projected_occupancy_ratio:
                    diagnostics.append(
                        {
                            "code": "coverage_projected_occupancy_below_threshold",
                            "action": "Improve projected object coverage.",
                        }
                    )
        coverage_sha = hashlib.sha256(
            json.dumps(coverage, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        ).hexdigest()
    confidence = _report_payload(confidence_report)
    if confidence is None or coverage_metrics is None or coverage_sha is None:
        diagnostics.append(
            {
                "code": "confidence_evidence_missing",
                "action": "Provide PL-0199 confidence derived from the current coverage report.",
            }
        )
        confidence_score = None
    else:
        confidence_diagnostics, confidence_score = _confidence_decision(
            confidence, coverage_sha, coverage_metrics, policy
        )
        diagnostics.extend(confidence_diagnostics)
    return _gate_report(geometry, coverage_sha, confidence, diagnostics, policy, confidence_score)


def _gate_report(
    geometry: object,
    coverage_digest: str | None,
    confidence: dict[str, object] | None,
    diagnostics: list[dict[str, str]],
    policy: CapturedGeometryFitGatePolicy,
    confidence_score: float | None,
) -> CapturedGeometryFitGateReport:
    geometry_id = getattr(geometry, "geometry_id", None)
    parents: dict[str, object] | None = None
    if isinstance(geometry, ObjectCaptureGeometry):
        parents = {
            "project_id": geometry.project_id,
            "source_revision": geometry.source_revision,
            "source_input_digest": geometry.source_input_digest,
            "reconstruction_revision": geometry.reconstruction_revision,
            "camera_solution_revision": geometry.camera_solution_revision,
            "mask_set_revision_id": geometry.mask_set_revision_id,
            "mask_set_revision_digest": geometry.mask_set_revision_digest,
        }
    return CapturedGeometryFitGateReport(
        {
            "contract": CAPTURED_GEOMETRY_FIT_GATE_CONTRACT,
            "authority": "diagnostic_gate_only_no_fit_or_geometry_mutation",
            "decision": "eligible_for_downstream_parametric_fit" if not diagnostics else "blocked",
            "acceptance_status": "not_evaluated",
            "confidence_score": confidence_score,
            "geometry_id": geometry_id if isinstance(geometry_id, str) else None,
            "parents": parents,
            "coverage_report_sha256": coverage_digest,
            "confidence_report_sha256": None
            if confidence is None
            else hashlib.sha256(
                json.dumps(
                    confidence, sort_keys=True, separators=(",", ":"), ensure_ascii=True
                ).encode()
            ).hexdigest(),
            "policy": policy.as_dict(),
            "diagnostics": diagnostics,
            "parametric_fit_executed": False,
            "metric_accuracy_claimed": False,
        }
    )
