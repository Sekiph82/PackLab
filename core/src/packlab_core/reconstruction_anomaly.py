"""Deterministic, review-only anomaly findings over existing reconstruction diagnostics."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .geometry_statistics import GeometryStatistics
from .reconstruction_confidence import (
    RECONSTRUCTION_CONFIDENCE_CONTRACT,
    ReconstructionConfidenceReport,
)

RECONSTRUCTION_ANOMALY_CONTRACT = "packlab.reconstruction-anomaly.v1"
_ANOMALY_CODES = frozenset(
    {
        "diagnostic_statistics_missing",
        "confidence_evidence_missing",
        "confidence_evidence_incomplete",
        "confidence_below_profile",
        "mesh_disconnected_components",
        "mesh_boundary_edges_present",
        "mesh_nonmanifold_edges_present",
        "mesh_hole_report_unresolved_components",
        "mesh_topology_evidence_incomplete",
    }
)
_SAFE_REVISION_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,191}$", re.ASCII)


class ReconstructionAnomalyError(ValueError):
    """Raised when diagnostic evidence cannot be safely represented."""


@dataclass(frozen=True, slots=True)
class ReconstructionAnomalyFinding:
    code: str
    severity: str
    source: str
    evidence: tuple[tuple[str, int | float | str], ...]

    def __post_init__(self) -> None:
        if self.code not in _ANOMALY_CODES:
            raise ReconstructionAnomalyError("anomaly_code_not_allowlisted")
        if self.severity != "REVIEW_REQUIRED":
            raise ReconstructionAnomalyError("anomaly_severity_invalid")
        if self.source not in {"geometry_statistics", "reconstruction_confidence", "evidence"}:
            raise ReconstructionAnomalyError("anomaly_source_invalid")
        if not isinstance(self.evidence, tuple):
            raise ReconstructionAnomalyError("anomaly_evidence_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "source": self.source,
            "evidence": {key: value for key, value in self.evidence},
        }


@dataclass(frozen=True, slots=True)
class ReconstructionAnomalyReport:
    report_id: str
    geometry_revision_id: str | None
    geometry_sha256: str | None
    confidence_report_sha256: str | None
    status: str
    findings: tuple[ReconstructionAnomalyFinding, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": RECONSTRUCTION_ANOMALY_CONTRACT,
            "report_id": self.report_id,
            "geometry_revision_id": self.geometry_revision_id,
            "geometry_sha256": self.geometry_sha256,
            "confidence_report_sha256": self.confidence_report_sha256,
            "status": self.status,
            "findings": [item.as_dict() for item in self.findings],
            "authority_class": "DIAGNOSTIC_REVIEW_SUGGESTIONS_ONLY",
            "geometry_mutated": False,
            "scan_master_replaced": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


def detect_reconstruction_anomalies(
    geometry_statistics: GeometryStatistics | None,
    confidence_report: ReconstructionConfidenceReport | None,
) -> ReconstructionAnomalyReport:
    """Map explicit diagnostics to fixed findings; never modify their source evidence."""

    findings: list[ReconstructionAnomalyFinding] = []
    geometry_revision_id: str | None = None
    geometry_sha256: str | None = None
    confidence_sha256: str | None = None
    if geometry_statistics is None:
        findings.append(_finding("diagnostic_statistics_missing", "evidence", ()))
    elif not isinstance(geometry_statistics, GeometryStatistics):
        raise ReconstructionAnomalyError("geometry_statistics_type_invalid")
    else:
        geometry_revision_id = geometry_statistics.geometry_revision_id
        geometry_sha256 = geometry_statistics.geometry_sha256
        if not isinstance(geometry_revision_id, str) or not _SAFE_REVISION_ID.fullmatch(
            geometry_revision_id
        ):
            raise ReconstructionAnomalyError("geometry_revision_id_invalid")
        if (
            not isinstance(geometry_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", geometry_sha256) is None
        ):
            raise ReconstructionAnomalyError("geometry_digest_invalid")
        if geometry_statistics.interpretation != "DIAGNOSTIC_ONLY_NO_PHYSICAL_ACCURACY_CLAIM":
            raise ReconstructionAnomalyError("geometry_statistics_authority_invalid")
        topology = dict(geometry_statistics.topology_indicators)
        component_count = _count(geometry_statistics.connected_component_count)
        boundary_edges = _count(topology.get("boundary_edge_count"))
        nonmanifold_edges = _count(topology.get("nonmanifold_edge_count"))
        # Review F-2: absent or malformed mesh topology (e.g. point-cloud statistics, bool or
        # float counts) is incomplete evidence, never a clean "no rule triggered" result.
        missing = [
            name
            for name, value in (
                ("connected_component_count", component_count),
                ("boundary_edge_count", boundary_edges),
                ("nonmanifold_edge_count", nonmanifold_edges),
            )
            if value is None
        ]
        if missing:
            findings.append(
                _finding(
                    "mesh_topology_evidence_incomplete",
                    "geometry_statistics",
                    (("missing_or_invalid", ",".join(missing)),),
                )
            )
        if component_count is not None and component_count > 1:
            findings.append(
                _finding(
                    "mesh_disconnected_components",
                    "geometry_statistics",
                    (("component_count", component_count),),
                )
            )
        if boundary_edges:
            findings.append(
                _finding(
                    "mesh_boundary_edges_present",
                    "geometry_statistics",
                    (("edge_count", boundary_edges),),
                )
            )
        if nonmanifold_edges:
            findings.append(
                _finding(
                    "mesh_nonmanifold_edges_present",
                    "geometry_statistics",
                    (("edge_count", nonmanifold_edges),),
                )
            )
        linkage = geometry_statistics.hole_report_linkage
        if linkage is not None and len(linkage) == 4 and linkage[3] > 0:
            findings.append(
                _finding(
                    "mesh_hole_report_unresolved_components",
                    "geometry_statistics",
                    (("unresolved_component_count", linkage[3]),),
                )
            )

    if confidence_report is None:
        findings.append(_finding("confidence_evidence_missing", "evidence", ()))
    elif not isinstance(confidence_report, ReconstructionConfidenceReport):
        raise ReconstructionAnomalyError("confidence_report_type_invalid")
    else:
        payload = confidence_report.as_dict()
        if (
            payload.get("contract") != RECONSTRUCTION_CONFIDENCE_CONTRACT
            or payload.get("authority")
            != "diagnostic_only_no_physical_accuracy_or_acceptance_claim"
            or payload.get("acceptance_status") != "not_evaluated"
        ):
            raise ReconstructionAnomalyError("confidence_report_authority_invalid")
        confidence_sha256 = confidence_report.digest()
        observation = payload.get("observation_status")
        threshold = payload.get("threshold_status")
        if observation != "observed":
            safe_observation = (
                observation if observation in {"invalid", "incomplete"} else "unknown"
            )
            findings.append(
                _finding(
                    "confidence_evidence_incomplete",
                    "reconstruction_confidence",
                    (("observation_status", safe_observation),),
                )
            )
        elif threshold == "below_profile":
            findings.append(
                _finding(
                    "confidence_below_profile",
                    "reconstruction_confidence",
                    (("threshold_status", threshold),),
                )
            )
        elif threshold != "meets_profile":
            safe_threshold = threshold if threshold == "not_evaluated" else "unknown"
            findings.append(
                _finding(
                    "confidence_evidence_incomplete",
                    "reconstruction_confidence",
                    (("threshold_status", safe_threshold),),
                )
            )

    canonical_findings = tuple(sorted(findings, key=lambda item: (item.code, item.source)))
    body = {
        "contract": RECONSTRUCTION_ANOMALY_CONTRACT,
        "geometry_revision_id": geometry_revision_id,
        "geometry_sha256": geometry_sha256,
        "confidence_report_sha256": confidence_sha256,
        "status": "REVIEW_REQUIRED" if canonical_findings else "NO_RULE_TRIGGERED_DIAGNOSTIC_ONLY",
        "findings": [item.as_dict() for item in canonical_findings],
        "authority_class": "DIAGNOSTIC_REVIEW_SUGGESTIONS_ONLY",
        "geometry_mutated": False,
        "scan_master_replaced": False,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
    }
    digest = hashlib.sha256(
        json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        ).encode("ascii")
    ).hexdigest()
    return ReconstructionAnomalyReport(
        "reconstruction-anomaly:" + digest,
        geometry_revision_id,
        geometry_sha256,
        confidence_sha256,
        str(body["status"]),
        canonical_findings,
    )


def _count(value: object) -> int | None:
    """A non-negative integer count, or None when absent or malformed (bools rejected)."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _finding(
    code: str, source: str, evidence: tuple[tuple[str, int | float | str], ...]
) -> ReconstructionAnomalyFinding:
    return ReconstructionAnomalyFinding(code, "REVIEW_REQUIRED", source, evidence)


__all__ = [
    "RECONSTRUCTION_ANOMALY_CONTRACT",
    "ReconstructionAnomalyError",
    "ReconstructionAnomalyFinding",
    "ReconstructionAnomalyReport",
    "detect_reconstruction_anomalies",
]
