"""PL-0437 controlled COLMAP/OpenMVS vs neural reconstruction backend benchmark.

The harness compares already-collected run records; it never executes a
backend and never changes the production default. A production-default change
can only be *recommended* (pending license clearance and an explicit ADR) when
every case is bound to an owner-recorded physical caliper benchmark record,
every required packaging class meets the pre-registered minimum count of
independent objects, and the pre-registered equal-or-better rule passes.
Cases labelled synthetic/public-proxy, synthetic-looking identifiers and the
synthetic proxy backend identities are refused on the physical path. The
physical binding is owner-attested (an unkeyed digest), not cryptographically
authenticated: a deliberate relabel of invented values cannot be detected here,
so an independent reviewer must check the binding against real evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import statistics
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path

from packlab_core.benchmark_metrics import MetricBand, MetricOutcome, compare_metric_bands
from packlab_core.physical_accuracy_benchmark import (
    REQUIRED_BENCHMARK_CATEGORIES,
    BenchmarkEnvironment,
    CaliperGroundTruth,
    PhysicalAccuracyBenchmarkRecord,
    PhysicalBenchmarkSample,
)
from packlab_core.reconstruction import BackendProvenance, ReconstructionBackendId, ScaleState

BENCHMARK_CONTRACT = "packlab.reconstruction-backend-benchmark.v1"
INPUT_CONTRACT = "packlab.reconstruction-backend-benchmark-input.v1"
PRODUCTION_DEFAULT_BACKEND = ReconstructionBackendId.COLMAP_OPENMVS
BASELINE_BACKEND = ReconstructionBackendId.COLMAP_OPENMVS
CANDIDATE_BACKEND = ReconstructionBackendId.NEURAL_EXPERIMENTAL
PACKAGE_CLASSES = REQUIRED_BENCHMARK_CATEGORIES
DIMENSIONS = (
    "height",
    "max_width",
    "max_depth",
    "body_diameter",
    "neck_finish_diameter",
    "base_diameter_or_footprint",
)
REQUIRED_DIMENSIONS = tuple(d for d in DIMENSIONS if d != "body_diameter")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SYNTHETIC_ID = re.compile(r"(?:^|[-_.:])(?:syn|synthetic|proxy)(?:[-_.:]|$)", re.IGNORECASE)
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_CASES = 10_000
MAX_RUNS = 200_000
# One-sided 95% Student-t quantiles, df 1..30; df > 30 reuses df 30 (conservative).
_T95 = (
    6.314, 2.920, 2.353, 2.132, 2.015, 1.943, 1.895, 1.860, 1.833, 1.812,
    1.796, 1.782, 1.771, 1.761, 1.753, 1.746, 1.740, 1.734, 1.729, 1.725,
    1.721, 1.717, 1.714, 1.711, 1.708, 1.706, 1.703, 1.701, 1.699, 1.697,
)  # fmt: skip


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _token(value: object) -> bool:
    return isinstance(value, str) and _TOKEN.fullmatch(value) is not None


def _nonneg(value: object) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        number = float(value)  # type: ignore[arg-type]
    except OverflowError:
        return False
    return math.isfinite(number) and number >= 0


def _positive(value: object) -> bool:
    return _nonneg(value) and value > 0  # type: ignore[operator]


class BackendBenchmarkError(ValueError):
    """Raised for malformed or authority-violating benchmark input."""


class GroundTruthAuthority(StrEnum):
    PHYSICAL_CALIPER = "PHYSICAL_CALIPER"
    SYNTHETIC_GENERATOR = "SYNTHETIC_GENERATOR"
    PUBLIC_PROXY = "PUBLIC_PROXY"


class RunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class BenchmarkDecision(StrEnum):
    NO_CHANGE_INSUFFICIENT_PHYSICAL_EVIDENCE = "NO_CHANGE_INSUFFICIENT_PHYSICAL_EVIDENCE"
    NO_CHANGE_RULE_NOT_MET = "NO_CHANGE_RULE_NOT_MET"
    RECOMMEND_DEFAULT_CHANGE_PENDING_ADR = "RECOMMEND_DEFAULT_CHANGE_PENDING_ADR"


@dataclass(frozen=True, slots=True)
class DecisionRule:
    """Pre-registered rule. Freeze it (and its digest) before looking at results.

    The spec requires "equal or better", so every default margin is 0: the
    one-sided 95% upper confidence bound of the mean per-object paired delta
    (candidate minus baseline, positive = worse) must be <= 0. Positive
    margins turn this into a non-inferiority rule; that is an interpretation
    of the spec and needs owner/ADR sign-off under a new ``version``.
    """

    version: str = "pl0437-equal-or-better-v1"
    min_cases_per_class: int = 3
    min_repeats_per_backend: int = 2
    margin_dimension_mae_mm: float = 0.0
    margin_scale_error_ratio: float = 0.0
    margin_surface_coverage_loss: float = 0.0
    margin_repeatability_spread_mm: float = 0.0
    margin_surface_deviation_rms_mm: float = 0.0
    margin_operator_interventions: float = 0.0
    min_surface_coverage_ratio: float = 0.90
    min_registered_input_ratio: float = 0.80

    def __post_init__(self) -> None:
        if (
            type(self.min_cases_per_class) is not int
            or type(self.min_repeats_per_backend) is not int
            or self.min_cases_per_class < 2
            or self.min_repeats_per_backend < 2
        ):
            raise BackendBenchmarkError("rule needs >=2 cases per class and >=2 repeats")
        for name, value in asdict(self).items():
            if name != "version" and not _nonneg(value):
                raise BackendBenchmarkError(f"rule_{name}_invalid")

    @property
    def margins(self) -> dict[str, float]:
        return {
            "dimension_mae_mm": self.margin_dimension_mae_mm,
            "scale_error_ratio": self.margin_scale_error_ratio,
            "surface_coverage_loss": self.margin_surface_coverage_loss,
            "repeatability_spread_mm": self.margin_repeatability_spread_mm,
            "surface_deviation_rms_mm": self.margin_surface_deviation_rms_mm,
            "operator_interventions": self.margin_operator_interventions,
        }

    @property
    def digest(self) -> str:
        return _digest(asdict(self))


PREREGISTERED_RULE = DecisionRule()


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    package_class: str
    material: str
    capture_set_id: str
    ground_truth_record_id: str
    ground_truth_authority: GroundTruthAuthority
    ground_truth_dimensions_mm: Mapping[str, float]
    physical_record_digest: str | None = None
    physical_sample_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("case_id", "material", "capture_set_id", "ground_truth_record_id"):
            if not _token(getattr(self, name)):
                raise BackendBenchmarkError(f"case_{name}_invalid")
        if self.package_class not in PACKAGE_CLASSES:
            raise BackendBenchmarkError("case_package_class_unsupported")
        object.__setattr__(
            self, "ground_truth_authority", GroundTruthAuthority(self.ground_truth_authority)
        )
        dims = dict(self.ground_truth_dimensions_mm)
        if not set(REQUIRED_DIMENSIONS) <= set(dims) <= set(DIMENSIONS):
            raise BackendBenchmarkError("case_ground_truth_dimension_set_invalid")
        if not all(_positive(v) for v in dims.values()):
            raise BackendBenchmarkError("case_ground_truth_dimension_value_invalid")
        object.__setattr__(self, "ground_truth_dimensions_mm", dims)
        if self.physical_record_digest is not None and not _DIGEST.fullmatch(
            self.physical_record_digest
        ):
            raise BackendBenchmarkError("case_physical_record_digest_invalid")
        if self.physical_sample_id is not None and not _token(self.physical_sample_id):
            raise BackendBenchmarkError("case_physical_sample_id_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "package_class": self.package_class,
            "material": self.material,
            "capture_set_id": self.capture_set_id,
            "ground_truth_record_id": self.ground_truth_record_id,
            "ground_truth_authority": self.ground_truth_authority.value,
            "ground_truth_dimensions_mm": dict(sorted(self.ground_truth_dimensions_mm.items())),
            "physical_record_digest": self.physical_record_digest,
            "physical_sample_id": self.physical_sample_id,
        }


@dataclass(frozen=True, slots=True)
class BackendRunRecord:
    """One backend execution on one case, measured after the shared M09 scale step."""

    case_id: str
    backend: BackendProvenance
    repeat_index: int
    status: RunStatus
    scale_procedure_id: str
    scale_state: ScaleState
    measured_dimensions_mm: Mapping[str, float] = field(default_factory=dict)
    surface_coverage_ratio: float | None = None
    registered_input_ratio: float | None = None
    surface_deviation_rms_mm: float | None = None
    runtime_seconds: float | None = None
    peak_host_ram_bytes: int | None = None
    peak_vram_bytes: int | None = None
    point_count: int | None = None
    triangle_count: int | None = None
    hole_count: int | None = None
    floating_component_count: int | None = None
    operator_interventions: int = 0
    failure_diagnostic: str | None = None

    def __post_init__(self) -> None:
        if not _token(self.case_id) or not _token(self.scale_procedure_id):
            raise BackendBenchmarkError("run_identifier_invalid")
        if not isinstance(self.backend, BackendProvenance):
            raise BackendBenchmarkError("run_backend_provenance_required")
        if self.backend.backend_id not in (BASELINE_BACKEND, CANDIDATE_BACKEND):
            raise BackendBenchmarkError("run_backend_id_unsupported")
        if type(self.repeat_index) is not int or self.repeat_index < 0:
            raise BackendBenchmarkError("run_repeat_index_invalid")
        object.__setattr__(self, "status", RunStatus(self.status))
        object.__setattr__(self, "scale_state", ScaleState(self.scale_state))
        if self.scale_state is ScaleState.METRIC_VERIFIED:
            # M07 never produces METRIC_VERIFIED; M09/Scan Master own that transition.
            raise BackendBenchmarkError("run_scale_state_must_not_claim_metric_verified")
        dims = dict(self.measured_dimensions_mm)
        if not set(dims) <= set(DIMENSIONS) or not all(_positive(v) for v in dims.values()):
            raise BackendBenchmarkError("run_measured_dimensions_invalid")
        object.__setattr__(self, "measured_dimensions_mm", dims)
        for name in ("surface_coverage_ratio", "registered_input_ratio"):
            value = getattr(self, name)
            if value is not None and not (_nonneg(value) and value <= 1.0):
                raise BackendBenchmarkError(f"run_{name}_invalid")
        for name in ("surface_deviation_rms_mm", "runtime_seconds"):
            value = getattr(self, name)
            if value is not None and not _nonneg(value):
                raise BackendBenchmarkError(f"run_{name}_invalid")
        if type(self.operator_interventions) is not int:
            raise BackendBenchmarkError("run_operator_interventions_invalid")
        for name in (
            "peak_host_ram_bytes",
            "peak_vram_bytes",
            "point_count",
            "triangle_count",
            "hole_count",
            "floating_component_count",
            "operator_interventions",
        ):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or not 0 <= value < 2**63):
                raise BackendBenchmarkError(f"run_{name}_invalid")
        if self.status is RunStatus.FAILED:
            if not isinstance(self.failure_diagnostic, str) or not self.failure_diagnostic.strip():
                raise BackendBenchmarkError("run_failed_requires_diagnostic")
        elif self.failure_diagnostic is not None:
            raise BackendBenchmarkError("run_succeeded_cannot_have_failure_diagnostic")
        elif self.surface_coverage_ratio is None or self.registered_input_ratio is None:
            raise BackendBenchmarkError("run_succeeded_requires_coverage_and_registration")

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "backend_identity_digest": backend_identity_digest(self.backend),
            "backend_id": self.backend.backend_id.value,
            "repeat_index": self.repeat_index,
            "status": self.status.value,
            "scale_procedure_id": self.scale_procedure_id,
            "scale_state": self.scale_state.value,
            "measured_dimensions_mm": dict(sorted(self.measured_dimensions_mm.items())),
            "surface_coverage_ratio": self.surface_coverage_ratio,
            "registered_input_ratio": self.registered_input_ratio,
            "surface_deviation_rms_mm": self.surface_deviation_rms_mm,
            "runtime_seconds": self.runtime_seconds,
            "peak_host_ram_bytes": self.peak_host_ram_bytes,
            "peak_vram_bytes": self.peak_vram_bytes,
            "point_count": self.point_count,
            "triangle_count": self.triangle_count,
            "hole_count": self.hole_count,
            "floating_component_count": self.floating_component_count,
            "operator_interventions": self.operator_interventions,
            "failure_diagnostic": self.failure_diagnostic,
        }


def backend_identity(provenance: BackendProvenance) -> dict[str, object]:
    return {
        "backend_id": provenance.backend_id.value,
        "version": provenance.version,
        "build": provenance.build,
        "license_record": provenance.license_record,
        "executable_hashes": dict(sorted(provenance.executable_hashes.items())),
    }


def backend_identity_digest(provenance: BackendProvenance) -> str:
    return _digest(backend_identity(provenance))


def _identity_is_proxy(provenance: BackendProvenance) -> bool:
    proxy = synthetic_proxy_provenance(provenance.backend_id)
    return (
        backend_identity_digest(provenance) == backend_identity_digest(proxy)
        or provenance.version == proxy.version
        or provenance.license_record == proxy.license_record
        or any(
            _SYNTHETIC_ID.search(value)
            for value in (provenance.version, provenance.build, provenance.license_record)
        )
    )


def _identity_pinned(provenance: BackendProvenance) -> bool:
    hashes = provenance.executable_hashes
    return bool(hashes) and all(
        isinstance(v, str) and _SHA256.fullmatch(v) for v in hashes.values()
    )


def evaluate_backend_benchmark(
    cases: Sequence[BenchmarkCase],
    runs: Sequence[BackendRunRecord],
    *,
    physical_record: PhysicalAccuracyBenchmarkRecord | None = None,
    license_clearance_ref: str | None = None,
    rule: DecisionRule = PREREGISTERED_RULE,
) -> dict[str, object]:
    """Return a digest-bound benchmark report. Never mutates any default."""
    if not cases:
        raise BackendBenchmarkError("benchmark_cases_required")
    if len(cases) > MAX_CASES or len(runs) > MAX_RUNS:
        raise BackendBenchmarkError("benchmark_input_too_large")
    if len({c.capture_set_id for c in cases}) != len(cases):
        # Reusing one capture set across cases is pseudo-replication.
        raise BackendBenchmarkError("benchmark_duplicate_capture_set_id")
    by_case = {case.case_id: case for case in cases}
    if len(by_case) != len(cases):
        raise BackendBenchmarkError("benchmark_duplicate_case_id")
    keys = [(r.case_id, r.backend.backend_id, r.repeat_index) for r in runs]
    if len(set(keys)) != len(keys):
        raise BackendBenchmarkError("benchmark_duplicate_run")
    if any(r.case_id not in by_case for r in runs):
        raise BackendBenchmarkError("benchmark_run_references_unknown_case")
    identities: dict[ReconstructionBackendId, set[str]] = {}
    for run in runs:
        identities.setdefault(run.backend.backend_id, set()).add(
            backend_identity_digest(run.backend)
        )
    if any(len(digests) != 1 for digests in identities.values()):
        raise BackendBenchmarkError("benchmark_backend_identity_must_be_single_pinned_build")
    if len({r.scale_procedure_id for r in runs}) > 1:
        raise BackendBenchmarkError("benchmark_runs_must_share_one_scale_procedure")
    for run in runs:
        if run.status is RunStatus.SUCCEEDED and not set(
            by_case[run.case_id].ground_truth_dimensions_mm
        ) <= set(run.measured_dimensions_mm):
            raise BackendBenchmarkError("run_missing_ground_truth_dimension")
    if license_clearance_ref is not None and not _token(license_clearance_ref):
        raise BackendBenchmarkError("license_clearance_ref_invalid")

    evidence_reasons: list[str] = []
    rule_reasons: list[str] = []
    precondition_reasons: list[str] = []
    case_reports = []
    # Paired deltas are grouped per independent physical object so repeated cases of
    # one object cannot inflate n. Samples sharing a scan_id or measurement_id are
    # one object (one bottle recorded as height/width/depth samples counts once).
    object_of = _physical_object_keys(physical_record)
    paired: dict[str, dict[str, list[dict[str, float | None]]]] = {c: {} for c in PACKAGE_CLASSES}
    runs_by_case: dict[str, list[BackendRunRecord]] = {}
    for run in runs:
        runs_by_case.setdefault(run.case_id, []).append(run)
    for case_id in sorted(by_case):
        case = by_case[case_id]
        physical_ok, physical_reason = _physical_binding(case, physical_record)
        if not physical_ok:
            evidence_reasons.append(f"{case_id}:{physical_reason}")
        per_backend = {}
        for backend_id in (BASELINE_BACKEND, CANDIDATE_BACKEND):
            case_runs = sorted(
                (r for r in runs_by_case.get(case_id, ()) if r.backend.backend_id is backend_id),
                key=lambda r: r.repeat_index,
            )
            per_backend[backend_id] = _aggregate(case, case_runs, rule)
        base, cand = per_backend[BASELINE_BACKEND], per_backend[CANDIDATE_BACKEND]
        comparable = True
        for label, agg in (("baseline", base), ("candidate", cand)):
            if agg["runs"] < rule.min_repeats_per_backend:  # type: ignore[operator]
                evidence_reasons.append(f"{case_id}:{label}_repeats_below_minimum")
                comparable = False
        if base["failed_runs"]:
            evidence_reasons.append(f"{case_id}:baseline_failed_case_not_comparable")
            comparable = False
        if base["band_failures"]:
            # A degenerate baseline would flatter the candidate's paired deltas.
            evidence_reasons.append(f"{case_id}:baseline_quality_band_failed")
            comparable = False
        if cand["failed_runs"]:
            rule_reasons.append(f"{case_id}:candidate_run_failed")
        if cand["band_failures"]:
            rule_reasons.append(f"{case_id}:candidate_quality_band_failed")
        delta: dict[str, float | None] | None = None
        if comparable and not cand["failed_runs"]:
            delta = {
                key: _delta(base["metrics"][key], cand["metrics"][key])  # type: ignore[index]
                for key in rule.margins
            }
            object_key = _object_key(case, object_of)
            paired[case.package_class].setdefault(object_key, []).append(delta)
        case_reports.append(
            {
                "case": case.as_dict(),
                "physical_ground_truth_bound": physical_ok,
                "physical_object_key": _object_key(case, object_of),
                "baseline": base,
                "candidate": cand,
                "candidate_minus_baseline": delta,
            }
        )

    class_reports = {}
    for package_class in PACKAGE_CLASSES:
        objects = paired[package_class]
        if len(objects) < rule.min_cases_per_class:
            evidence_reasons.append(f"{package_class}:independent_objects_below_minimum")
        metrics: dict[str, dict[str, object]] = {}
        for key, margin in rule.margins.items():
            per_object = [[d[key] for d in deltas] for _, deltas in sorted(objects.items())]
            if any(v is None for values in per_object for v in values):
                # A deciding metric missing for any case blocks the rule (fail closed).
                rule_reasons.append(f"{package_class}:{key}_not_measured")
                metrics[key] = {"outcome": "NOT_MEASURED", "n": len(per_object)}
                continue
            stat = _upper_bound([statistics.fmean(v) for v in per_object])  # type: ignore[arg-type]
            outcome = stat is not None and stat["upper_95"] <= margin
            if not outcome:
                rule_reasons.append(f"{package_class}:{key}_equal_or_better_not_shown")
            metrics[key] = {
                "outcome": "PASS" if outcome else "FAIL",
                "margin": margin,
                **(stat or {}),
            }
        class_reports[package_class] = {
            "comparable_cases": sum(len(d) for d in objects.values()),
            "independent_objects": len(objects),
            "metrics": metrics,
        }

    for label, backend_id in (("baseline", BASELINE_BACKEND), ("candidate", CANDIDATE_BACKEND)):
        provenances = [r.backend for r in runs if r.backend.backend_id is backend_id]
        if not provenances or not _identity_pinned(provenances[0]):
            precondition_reasons.append(f"{label}_identity_not_pinned")
        elif _identity_is_proxy(provenances[0]):
            precondition_reasons.append(f"{label}_identity_is_synthetic_proxy")
    if license_clearance_ref is None:
        precondition_reasons.append("candidate_license_clearance_not_recorded")

    if evidence_reasons:
        decision = BenchmarkDecision.NO_CHANGE_INSUFFICIENT_PHYSICAL_EVIDENCE
    elif rule_reasons or precondition_reasons:
        decision = BenchmarkDecision.NO_CHANGE_RULE_NOT_MET
    else:
        decision = BenchmarkDecision.RECOMMEND_DEFAULT_CHANGE_PENDING_ADR
    report: dict[str, object] = {
        "contract": BENCHMARK_CONTRACT,
        "rule": asdict(rule),
        "rule_digest": rule.digest,
        "manifest_digest": _digest([by_case[c].as_dict() for c in sorted(by_case)]),
        "runs_digest": _digest(sorted((r.as_dict() for r in runs), key=_run_sort_key)),
        "physical_record_digest": None
        if physical_record is None
        else physical_record.record_digest,
        "backend_identities": {
            b.value: sorted(identities.get(b, set())) for b in (BASELINE_BACKEND, CANDIDATE_BACKEND)
        },
        "license_clearance_ref": license_clearance_ref,
        "license_clearance_ref_semantics": "owner-attested token; not checked against license_record",
        "backend_pin_semantics": "declared executable hashes; not verified against binaries",
        "physical_binding_semantics": "owner-attested unkeyed digest; reviewer must verify",
        "cases": case_reports,
        "classes": class_reports,
        "rule_outcome": "FAIL" if rule_reasons else "PASS",
        "evidence_reasons": sorted(set(evidence_reasons)),
        "rule_reasons": sorted(set(rule_reasons)),
        "precondition_reasons": sorted(set(precondition_reasons)),
        "decision": decision.value,
        "production_default_backend": PRODUCTION_DEFAULT_BACKEND.value,
        "production_default_changed": False,
        "physical_evidence_status": (
            "PHYSICAL_EVIDENCE_BOUND" if not evidence_reasons else "PHYSICAL_EVIDENCE_PENDING"
        ),
        "synthetic_evidence_is_physical_evidence": False,
        "required_before_any_default_change": [
            "candidate license clearance review",
            "explicit ADR",
            "Scan Master authority regression review",
            "independent reviewer acceptance of this report",
        ],
    }
    report["report_digest"] = _digest(report)
    return report


def _physical_object_keys(record: PhysicalAccuracyBenchmarkRecord | None) -> dict[str, str]:
    """Map sample id -> object key; samples linked by scan_id/measurement_id merge."""
    if record is None:
        return {}
    parent = {s.sample_id: s.sample_id for s in record.samples}

    def find(item: str) -> str:
        while parent[item] != item:
            item = parent[item]
        return item

    first_seen: dict[tuple[str, str], str] = {}
    for sample in record.samples:
        for kind, value in (("scan", sample.scan_id), ("measurement", sample.measurement_id)):
            if value is None:
                continue
            other = first_seen.setdefault((kind, value), sample.sample_id)
            a, b = sorted((find(other), find(sample.sample_id)))
            parent[b] = a
    return {sample_id: "object:" + find(sample_id) for sample_id in parent}


def _object_key(case: BenchmarkCase, object_of: Mapping[str, str]) -> str:
    sample = case.physical_sample_id
    if sample is not None and sample in object_of:
        return object_of[sample]
    return "case:" + (sample or case.case_id)


def _physical_binding(
    case: BenchmarkCase, record: PhysicalAccuracyBenchmarkRecord | None
) -> tuple[bool, str]:
    if case.ground_truth_authority is not GroundTruthAuthority.PHYSICAL_CALIPER:
        return False, f"ground_truth_not_physical:{case.ground_truth_authority.value}"
    if record is None:
        return False, "physical_record_not_supplied"
    identifiers = (
        case.case_id,
        case.capture_set_id,
        case.ground_truth_record_id,
        case.physical_sample_id or "",
        record.record_id,
    )
    if any(_SYNTHETIC_ID.search(value) for value in identifiers):
        return False, "synthetic_identifier_on_physical_path"
    if record.record_status != "READY_FOR_AUDIT":
        return False, "physical_record_not_ready_for_audit"
    if case.physical_record_digest != record.record_digest:
        return False, "physical_record_digest_mismatch"
    sample = next((s for s in record.samples if s.sample_id == case.physical_sample_id), None)
    if sample is None or sample.disposition != "ACCEPTED" or sample.ground_truth is None:
        return False, "physical_sample_not_accepted"
    if sample.category != case.package_class:
        return False, "physical_sample_class_mismatch"
    truth = sample.ground_truth
    if truth.ground_truth_id != case.ground_truth_record_id:
        return False, "physical_ground_truth_id_mismatch"
    if case.ground_truth_dimensions_mm.get(truth.dimension_id) != truth.value_mm:
        return False, "physical_caliper_value_mismatch"
    return True, "bound"


def _aggregate(
    case: BenchmarkCase, runs: Sequence[BackendRunRecord], rule: DecisionRule
) -> dict[str, object]:
    truth = case.ground_truth_dimensions_mm
    ok = [r for r in runs if r.status is RunStatus.SUCCEEDED]
    band_failures = []
    maes, scale_errors = [], []
    for run in ok:
        errors = [abs(run.measured_dimensions_mm[d] - truth[d]) for d in sorted(truth)]
        maes.append(statistics.fmean(errors))
        ratio = statistics.median(run.measured_dimensions_mm[d] / truth[d] for d in sorted(truth))
        scale_errors.append(abs(ratio - 1.0))
        bands = {
            "surface_coverage_ratio": MetricBand(
                "surface_coverage_ratio", rule.min_surface_coverage_ratio, 1.0, "ratio",
                rule.version, "PL0437_PREREGISTERED_RULE",
            ),
            "registered_input_ratio": MetricBand(
                "registered_input_ratio", rule.min_registered_input_ratio, 1.0, "ratio",
                rule.version, "PL0437_PREREGISTERED_RULE",
            ),
        }  # fmt: skip
        comparison = compare_metric_bands(
            bands,
            {
                "surface_coverage_ratio": run.surface_coverage_ratio,
                "registered_input_ratio": run.registered_input_ratio,
            },
        )
        if comparison.outcome is MetricOutcome.FAIL:
            band_failures.append(run.repeat_index)
    metrics: dict[str, float | None] | None = None
    if ok:
        spreads = [
            max(r.measured_dimensions_mm[d] for r in ok)
            - min(r.measured_dimensions_mm[d] for r in ok)
            for d in sorted(truth)
        ]
        deviations = [r.surface_deviation_rms_mm for r in ok]
        metrics = {
            "dimension_mae_mm": statistics.fmean(maes),
            "scale_error_ratio": statistics.fmean(scale_errors),
            "surface_coverage_loss": 1.0
            - statistics.fmean(r.surface_coverage_ratio or 0.0 for r in ok),
            "repeatability_spread_mm": max(spreads),
            "surface_deviation_rms_mm": (
                None
                if any(v is None for v in deviations)
                else statistics.fmean(v for v in deviations if v is not None)
            ),
            "operator_interventions": statistics.fmean(r.operator_interventions for r in ok),
        }
    return {
        "runs": len(runs),
        "failed_runs": [r.repeat_index for r in runs if r.status is RunStatus.FAILED],
        "failure_diagnostics": [r.failure_diagnostic for r in runs if r.failure_diagnostic],
        "band_failures": band_failures,
        "metrics": metrics,
        # Descriptive only; the rule never decides on speed or size.
        "descriptive": {
            "registered_input_ratio_mean": _mean_present(r.registered_input_ratio for r in ok),
            "runtime_seconds_mean": _mean_present(r.runtime_seconds for r in runs),
            "peak_host_ram_bytes_max": _max_present(r.peak_host_ram_bytes for r in runs),
            "peak_vram_bytes_max": _max_present(r.peak_vram_bytes for r in runs),
            "point_count_mean": _mean_present(r.point_count for r in ok),
            "triangle_count_mean": _mean_present(r.triangle_count for r in ok),
            "hole_count_max": _max_present(r.hole_count for r in ok),
            "floating_component_count_max": _max_present(r.floating_component_count for r in ok),
            "operator_interventions_total": sum(r.operator_interventions for r in runs),
        },
    }


def _mean_present(values: Iterable[float | int | None]) -> float | None:
    present = [v for v in values if v is not None]
    return statistics.fmean(present) if present else None


def _max_present(values: Iterable[int | None]) -> int | None:
    present = [v for v in values if v is not None]
    return max(present) if present else None


def _delta(base: float | None, cand: float | None) -> float | None:
    if base is None or cand is None:
        return None
    return cand - base


def _upper_bound(values: Sequence[float]) -> dict[str, float] | None:
    if len(values) < 2:
        return None
    mean = statistics.fmean(values)
    sd = statistics.stdev(values)
    t = _T95[min(len(values) - 1, len(_T95)) - 1]
    return {
        "n": len(values),
        "mean": mean,
        "sd": sd,
        "upper_95": mean + t * sd / math.sqrt(len(values)),
    }


def _run_sort_key(item: dict[str, object]) -> tuple[str, str, int]:
    return (str(item["case_id"]), str(item["backend_id"]), int(item["repeat_index"]))  # type: ignore[call-overload]


# --- Synthetic proxy (software test only; never physical evidence) -----------------

_PROXY_TRUTH = {
    # Height/width/depth follow the PL-0370 generator nominal family sizes; other
    # dimensions are plausible generated values. All are synthetic, not measured.
    "matte_bottle": ("hdpe_matte", {"height": 228.0, "max_width": 72.0, "max_depth": 72.0,
                     "body_diameter": 69.1, "neck_finish_diameter": 24.5,
                     "base_diameter_or_footprint": 67.7}),
    "glossy_bottle": ("pet_gloss", {"height": 228.0, "max_width": 72.0, "max_depth": 72.0,
                      "body_diameter": 69.1, "neck_finish_diameter": 24.5,
                      "base_diameter_or_footprint": 67.7}),
    "jerrycan": ("hdpe_matte", {"height": 286.0, "max_width": 168.0, "max_depth": 92.0,
                 "neck_finish_diameter": 38.0, "base_diameter_or_footprint": 154.0}),
}  # fmt: skip
SYNTHETIC_PROXY_SEED = 4372026


def synthetic_proxy_provenance(backend_id: ReconstructionBackendId) -> BackendProvenance:
    """Fake pinned identities for the proxy; they do not describe real binaries."""
    tag = hashlib.sha256(f"pl0437-proxy-{backend_id.value}".encode()).hexdigest()
    return BackendProvenance(
        backend_id, "synthetic-proxy", f"proxy-{backend_id.value}", "proxy-license", {"proxy": tag}
    )


def synthetic_proxy_inputs(
    *,
    seed: int = SYNTHETIC_PROXY_SEED,
    cases_per_class: int = 3,
    repeats: int = 2,
    candidate_bias_mm: float = 0.0,
    candidate_noise_mm: float = 0.2,
    candidate_fail_case: str | None = None,
    candidate_quality_gain: float = 0.0,
) -> tuple[list[BenchmarkCase], list[BackendRunRecord]]:
    """Deterministic synthetic run records with injected backend errors."""
    rng = random.Random(seed)
    cases, runs = [], []
    for package_class in PACKAGE_CLASSES:
        material, truth = _PROXY_TRUTH[package_class]
        for index in range(cases_per_class):
            case_id = f"SYN-{package_class.upper()}-{index:02d}"
            cases.append(
                BenchmarkCase(
                    case_id, package_class, material, f"synthetic-capture-{case_id.lower()}",
                    f"synthetic-gt-{case_id.lower()}", GroundTruthAuthority.SYNTHETIC_GENERATOR,
                    truth,
                )
            )  # fmt: skip
            for backend_id, bias, noise in (
                (BASELINE_BACKEND, 0.0, 0.2),
                (CANDIDATE_BACKEND, candidate_bias_mm, candidate_noise_mm),
            ):
                for repeat in range(repeats):
                    failed = backend_id is CANDIDATE_BACKEND and case_id == candidate_fail_case
                    gain = candidate_quality_gain if backend_id is CANDIDATE_BACKEND else 0.0
                    measured = {
                        k: max(0.1, v + bias + rng.gauss(0.0, noise)) for k, v in truth.items()
                    }
                    runs.append(
                        BackendRunRecord(
                            case_id=case_id,
                            backend=synthetic_proxy_provenance(backend_id),
                            repeat_index=repeat,
                            status=RunStatus.FAILED if failed else RunStatus.SUCCEEDED,
                            scale_procedure_id="m09-scale-proxy",
                            scale_state=ScaleState.METRIC_UNVERIFIED,
                            measured_dimensions_mm={} if failed else measured,
                            surface_coverage_ratio=None
                            if failed
                            else min(1.0, 0.95 + gain + rng.uniform(0, 0.03)),
                            registered_input_ratio=None if failed else 0.9 + rng.uniform(0, 0.1),
                            surface_deviation_rms_mm=None
                            if failed
                            else max(0.0, 0.3 - gain + rng.uniform(0, 0.1)),
                            runtime_seconds=60.0 + rng.uniform(0, 30),
                            failure_diagnostic="injected synthetic failure" if failed else None,
                        )
                    )
    return cases, runs


# --- JSON input for owner runs ------------------------------------------------------


def load_benchmark_input(
    payload: Mapping[str, object],
) -> tuple[list[BenchmarkCase], list[BackendRunRecord], str | None]:
    """Parse the owner-filled input document (see the PL-0437 operator procedure)."""
    if not isinstance(payload, Mapping):
        raise BackendBenchmarkError("input_must_be_json_object")
    if payload.get("contract") != INPUT_CONTRACT:
        raise BackendBenchmarkError("input_contract_unsupported")
    try:
        backends = {
            alias: BackendProvenance(
                ReconstructionBackendId(raw["backend_id"]),
                raw["version"],
                raw["build"],
                raw["license_record"],
                dict(raw["executable_hashes"]),
            )
            for alias, raw in payload["backends"].items()  # type: ignore[attr-defined]
        }
        cases = [
            BenchmarkCase(**raw)
            for raw in payload["cases"]  # type: ignore[attr-defined]
        ]
        runs = [
            BackendRunRecord(**{**raw, "backend": backends[raw["backend"]]})
            for raw in payload["runs"]  # type: ignore[attr-defined]
        ]
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        if isinstance(exc, BackendBenchmarkError):
            raise
        raise BackendBenchmarkError(f"input_malformed:{type(exc).__name__}") from exc
    clearance = payload.get("license_clearance_ref")
    if clearance is not None and not isinstance(clearance, str):
        raise BackendBenchmarkError("license_clearance_ref_invalid")
    return cases, runs, clearance


def load_physical_record(payload: Mapping[str, object]) -> PhysicalAccuracyBenchmarkRecord:
    """Rebuild a serialized PL-0221-style physical record and verify its digest."""
    if not isinstance(payload, Mapping):
        raise BackendBenchmarkError("physical_record_must_be_json_object")
    try:
        samples = []
        for raw in payload["samples"]:  # type: ignore[attr-defined]
            truth = raw["ground_truth"]
            ground_truth = None
            if truth is not None:
                ground_truth = CaliperGroundTruth(
                    truth["ground_truth_id"], truth["dimension_id"], truth["value_mm"],
                    tuple(truth["repeated_readings_mm"]), truth["uncertainty_mm"],
                    truth["caliper_reference"], truth["calibration_record_reference"],
                    truth["owner_reference"], truth["measured_at_utc"], truth["unit"],
                )  # fmt: skip
            samples.append(
                PhysicalBenchmarkSample(
                    raw["sample_id"], raw["category"], raw["disposition"], raw["scan_id"],
                    raw["scan_revision_id"], raw["measurement_id"], raw["measurement_revision_id"],
                    raw["evidence_reference"], ground_truth, raw["disposition_reason"],
                )
            )  # fmt: skip
        record = PhysicalAccuracyBenchmarkRecord(
            payload["record_id"],  # type: ignore[arg-type]
            payload["record_status"],  # type: ignore[arg-type]
            payload["operator_reference"],  # type: ignore[arg-type]
            payload["created_at_utc"],  # type: ignore[arg-type]
            BenchmarkEnvironment(**payload["environment"]),  # type: ignore[arg-type]
            tuple(samples),
        )
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise BackendBenchmarkError(f"physical_record_malformed:{type(exc).__name__}") from exc
    if payload.get("record_digest") != record.record_digest:
        raise BackendBenchmarkError("physical_record_digest_mismatch")
    if {k: v for k, v in payload.items() if k != "record_digest"} != record.as_dict():
        raise BackendBenchmarkError("physical_record_content_mismatch")
    return record


def _read_json(path: Path) -> Mapping[str, object]:
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise BackendBenchmarkError("input_file_too_large")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise BackendBenchmarkError(f"input_json_invalid:{type(exc).__name__}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PL-0437 backend benchmark (read-only)")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="owner-filled benchmark input JSON")
    source.add_argument("--synthetic-proxy", action="store_true", help="software dry run")
    parser.add_argument("--physical-record", type=Path, help="serialized physical record JSON")
    parser.add_argument("--out", type=Path, help="write report JSON here (default stdout)")
    args = parser.parse_args(argv)
    clearance = None
    if args.synthetic_proxy:
        cases, runs = synthetic_proxy_inputs()
    else:
        cases, runs, clearance = load_benchmark_input(_read_json(args.input))
    record = None
    if args.physical_record is not None:
        record = load_physical_record(_read_json(args.physical_record))
    report = evaluate_backend_benchmark(
        cases, runs, physical_record=record, license_clearance_ref=clearance
    )
    text = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out is None:
        sys.stdout.write(text)
    else:
        args.out.write_text(text, encoding="utf-8")
    print(report["decision"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
