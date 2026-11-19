"""PL-0221 V1 acceptance-threshold derivation from owner-executed physical benchmarks.

Input is the PL-0220 ``PhysicalAccuracyBenchmarkRecord`` contract (caliper ground truth per
ACCEPTED sample) plus one PackLab measurement observation per ACCEPTED sample. Errors
``measured - caliper`` are grouped per (package category, material, feature group) and a
documented statistical rule turns each sufficiently sampled group into a proposed tolerance.

The output is only a digest-bound proposal (``PROPOSED_PENDING_OWNER_ACCEPTANCE``). An owner
acceptance record is the only way to an ACCEPTED threshold set, and acceptance re-derives the
proposal from the physical inputs. While the PL-0220 physical benchmark is owner-deferred,
acceptance is refused outright, so no ACCEPTED threshold can exist today.

Synthetic data can exercise the math only through ``derive_test_only_threshold_proposal``,
whose output status can never be accepted. ``evidence_kind`` is a caller-asserted label; the
owner acceptance step (with the owner's own benchmark records) is the human gate behind it.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .physical_accuracy_benchmark import (
    _SAFE_REFERENCE,
    REQUIRED_BENCHMARK_CATEGORIES,
    PhysicalAccuracyBenchmarkRecord,
    _rfc3339_utc,
    _safe_token,
)
from .reconstruction import ScaleState
from .visual_material_library import MaterialFamily

PROPOSAL_CONTRACT = "packlab.v1-acceptance-threshold-proposal.v1"
ACCEPTANCE_CONTRACT = "packlab.v1-acceptance-threshold-acceptance.v1"
THRESHOLD_VERSION = "v1_acceptance_thresholds_v1"
PROPOSED = "PROPOSED_PENDING_OWNER_ACCEPTANCE"
TEST_ONLY = "TEST_ONLY_SYNTHETIC_NOT_ACCEPTABLE"
ACCEPTED = "ACCEPTED"
PHYSICAL_EVIDENCE_PENDING = "PHYSICAL_EVIDENCE_PENDING"
# PL-0220 owner deferral (M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01). Changing this
# is a reviewed code change made only after real benchmark evidence exists.
PL0220_PHYSICAL_BENCHMARK_STATUS = "DEFERRED_OWNER_VALIDATION"
PHYSICAL_EVIDENCE_KIND = "OWNER_EXECUTED_PHYSICAL"
EVIDENCE_KINDS = (PHYSICAL_EVIDENCE_KIND, "SYNTHETIC", "SIMULATION_ONLY", "PUBLIC_PROXY")

DIMENSION_FEATURE_GROUPS: Mapping[str, str] = {
    "overall_height": "overall_dimension",
    "overall_width": "overall_dimension",
    "overall_depth": "overall_dimension",
    "overall_diameter": "overall_dimension",
    "neck_finish_thread_diameter_t": "neck_finish",
    "neck_finish_root_diameter_e": "neck_finish",
    "neck_finish_bore_diameter_i": "neck_finish",
    "neck_finish_height_h": "neck_finish",
    "wall_thickness": "wall_and_feature",
    "handle_feature": "wall_and_feature",
    "base_feature": "wall_and_feature",
    "shoulder_feature": "wall_and_feature",
}
FEATURE_GROUPS = ("overall_dimension", "neck_finish", "wall_and_feature")

MIN_SAMPLES_PER_GROUP = 10
COVERAGE_PROPORTION = 0.95
CONFIDENCE_LEVEL = 0.95
CALIPER_COVERAGE_FACTOR = 2.0
RULE = {
    "rule_id": "max(two_sided_normal_tolerance_bound, max_abs_error, caliper_floor)",
    "two_sided_normal_tolerance_bound": "abs(mean_error) + k * sample_std_error",
    "k_factor": "Howe (1969) with Wilson-Hilferty chi-square quantile",
    "coverage_proportion": COVERAGE_PROPORTION,
    "confidence_level": CONFIDENCE_LEVEL,
    "caliper_floor": "CALIPER_COVERAGE_FACTOR * max(caliper uncertainty_mm in group)",
    "caliper_coverage_factor": CALIPER_COVERAGE_FACTOR,
    "rounding": "ceil to 0.01 mm",
    "minimum_samples_per_group": MIN_SAMPLES_PER_GROUP,
    "group_key": "(benchmark category, material family, feature group)",
    "error_definition": "packlab_measured_mm - caliper_value_mm",
}


class AcceptanceThresholdError(ValueError):
    """Raised when inputs cannot support a threshold proposal or acceptance."""


@dataclass(frozen=True, slots=True)
class BenchmarkMeasurementObservation:
    """PackLab's measured value for exactly one ACCEPTED benchmark sample."""

    record_id: str
    sample_id: str
    measurement_id: str
    measurement_revision_id: str
    dimension_id: str
    dimension_kind: str
    material: MaterialFamily
    measured_value_mm: float
    scale_state: ScaleState
    scale_provenance_id: str | None
    evidence_kind: str

    def __post_init__(self) -> None:
        for name in (
            "record_id",
            "sample_id",
            "measurement_id",
            "measurement_revision_id",
            "dimension_id",
        ):
            if not _safe_token(getattr(self, name)):
                raise AcceptanceThresholdError(f"observation_{name}_invalid")
        if self.dimension_kind not in DIMENSION_FEATURE_GROUPS:
            raise AcceptanceThresholdError("observation_dimension_kind_unsupported")
        if not isinstance(self.material, MaterialFamily):
            raise AcceptanceThresholdError("observation_material_invalid")
        if not isinstance(self.scale_state, ScaleState):
            raise AcceptanceThresholdError("observation_scale_state_invalid")
        value = self.measured_value_mm
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise AcceptanceThresholdError("observation_measured_value_invalid")
        if not math.isfinite(value) or value <= 0.0:
            raise AcceptanceThresholdError("observation_measured_value_invalid")
        if self.scale_provenance_id is not None and not _safe_token(self.scale_provenance_id):
            raise AcceptanceThresholdError("observation_scale_provenance_id_invalid")
        if self.evidence_kind not in EVIDENCE_KINDS:
            raise AcceptanceThresholdError("observation_evidence_kind_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "sample_id": self.sample_id,
            "measurement_id": self.measurement_id,
            "measurement_revision_id": self.measurement_revision_id,
            "dimension_id": self.dimension_id,
            "dimension_kind": self.dimension_kind,
            "material": self.material.value,
            "measured_value_mm": float(self.measured_value_mm),
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "evidence_kind": self.evidence_kind,
        }


@dataclass(frozen=True, slots=True)
class OwnerThresholdAcceptance:
    """The owner's explicit decision; software never fills this in."""

    proposal_sha256: str
    actor_reference: str
    accepted_at_utc: str
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.proposal_sha256, str) or len(self.proposal_sha256) != 64:
            raise AcceptanceThresholdError("acceptance_proposal_digest_invalid")
        if not isinstance(self.actor_reference, str) or not _SAFE_REFERENCE.fullmatch(
            self.actor_reference
        ):
            raise AcceptanceThresholdError("acceptance_actor_reference_invalid")
        if not _rfc3339_utc(self.accepted_at_utc):
            raise AcceptanceThresholdError("acceptance_timestamp_invalid")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 500:
            raise AcceptanceThresholdError("acceptance_reason_required")


def tolerance_factor(n: int) -> float:
    """Two-sided normal tolerance factor k (Howe) for COVERAGE_PROPORTION/CONFIDENCE_LEVEL."""

    # Wilson-Hilferty is only accurate (conservative, < +0.01) from n = 10; it diverges at
    # small n (k(2) ~ 2e4 vs exact ~38), so smaller n is refused, matching the sample minimum.
    if isinstance(n, bool) or not isinstance(n, int) or n < MIN_SAMPLES_PER_GROUP:
        raise AcceptanceThresholdError("tolerance_factor_requires_minimum_samples")
    normal = statistics.NormalDist()
    z_p = normal.inv_cdf((1.0 + COVERAGE_PROPORTION) / 2.0)
    nu = n - 1
    # Wilson-Hilferty lower (1 - confidence) chi-square quantile with nu degrees of freedom.
    z_a = normal.inv_cdf(1.0 - CONFIDENCE_LEVEL)
    chi2 = nu * (1.0 - 2.0 / (9.0 * nu) + z_a * math.sqrt(2.0 / (9.0 * nu))) ** 3
    return math.sqrt(nu * (1.0 + 1.0 / n) * z_p * z_p / chi2)


def derive_threshold_proposal(
    records: Sequence[PhysicalAccuracyBenchmarkRecord],
    observations: Sequence[BenchmarkMeasurementObservation],
) -> dict[str, object]:
    """Physical path: refuses synthetic/simulation inputs; output is only a proposal."""

    for item in observations:
        if item.evidence_kind != PHYSICAL_EVIDENCE_KIND:
            raise AcceptanceThresholdError("synthetic_or_simulation_input_refused")
        if item.scale_state is not ScaleState.METRIC_VERIFIED or item.scale_provenance_id is None:
            raise AcceptanceThresholdError("observation_scale_not_metric_verified")
    return _derive(records, observations, PROPOSED)


def derive_test_only_threshold_proposal(
    records: Sequence[PhysicalAccuracyBenchmarkRecord],
    observations: Sequence[BenchmarkMeasurementObservation],
) -> dict[str, object]:
    """TEST ONLY: exercises the math on synthetic fixtures; the status is never acceptable."""

    return _derive(records, observations, TEST_ONLY)


def proposal_digest_valid(proposal: Mapping[str, object]) -> bool:
    return _digest_valid(proposal, "proposal_sha256")


def accepted_thresholds_digest_valid(accepted: Mapping[str, object]) -> bool:
    return _digest_valid(accepted, "accepted_sha256")


def accept_threshold_proposal(
    records: Sequence[PhysicalAccuracyBenchmarkRecord],
    observations: Sequence[BenchmarkMeasurementObservation],
    proposal: Mapping[str, object],
    acceptance: OwnerThresholdAcceptance,
) -> dict[str, object]:
    """The only route to ACCEPTED: owner record + re-derivation from physical inputs."""

    if PL0220_PHYSICAL_BENCHMARK_STATUS != "OWNER_BENCHMARK_EVIDENCE_ACCEPTED":
        raise AcceptanceThresholdError("pl0220_physical_benchmark_deferred_acceptance_blocked")
    if not isinstance(acceptance, OwnerThresholdAcceptance):
        raise AcceptanceThresholdError("owner_acceptance_record_required")
    if proposal.get("status") != PROPOSED or not proposal_digest_valid(proposal):
        raise AcceptanceThresholdError("proposal_not_acceptable")
    rederived = derive_threshold_proposal(records, observations)
    if rederived != dict(proposal):
        raise AcceptanceThresholdError("proposal_does_not_match_physical_inputs")
    if acceptance.proposal_sha256 != proposal["proposal_sha256"]:
        raise AcceptanceThresholdError("acceptance_bound_to_different_proposal")
    body: dict[str, object] = {
        "contract": ACCEPTANCE_CONTRACT,
        "version": THRESHOLD_VERSION,
        "status": ACCEPTED,
        "simulation_only": False,
        "proposal": rederived,
        "owner_acceptance": {
            "proposal_sha256": acceptance.proposal_sha256,
            "actor_reference": acceptance.actor_reference,
            "accepted_at_utc": acceptance.accepted_at_utc,
            "reason": acceptance.reason,
        },
        "mold_use_authorized": False,
    }
    return body | {"accepted_sha256": _digest(body)}


def _derive(
    records: Sequence[PhysicalAccuracyBenchmarkRecord],
    observations: Sequence[BenchmarkMeasurementObservation],
    status: str,
) -> dict[str, object]:
    if not records or not observations:
        raise AcceptanceThresholdError("records_and_observations_required")
    by_record: dict[str, PhysicalAccuracyBenchmarkRecord] = {}
    for record in records:
        if not isinstance(record, PhysicalAccuracyBenchmarkRecord):
            raise AcceptanceThresholdError("benchmark_record_invalid")
        if record.record_status != "READY_FOR_AUDIT":
            raise AcceptanceThresholdError("benchmark_record_not_ready_for_audit")
        if record.record_id in by_record:
            raise AcceptanceThresholdError("duplicate_benchmark_record_id")
        by_record[record.record_id] = record
    paired: dict[tuple[str, str], BenchmarkMeasurementObservation] = {}
    for item in observations:
        if not isinstance(item, BenchmarkMeasurementObservation):
            raise AcceptanceThresholdError("observation_invalid")
        key = (item.record_id, item.sample_id)
        if key in paired:
            raise AcceptanceThresholdError("duplicate_observation_for_sample")
        paired[key] = item
    groups: dict[tuple[str, str, str], list[tuple[float, float]]] = {}
    for record in by_record.values():
        for sample in record.samples:
            key = (record.record_id, sample.sample_id)
            found = paired.pop(key, None)
            if sample.disposition != "ACCEPTED":
                if found is not None:
                    raise AcceptanceThresholdError("observation_sample_not_accepted")
                continue
            if found is None:
                # Dropping an accepted sample silently would bias the threshold.
                raise AcceptanceThresholdError("accepted_sample_without_observation")
            truth = sample.ground_truth
            if truth is None or not truth.complete or truth.value_mm is None:
                raise AcceptanceThresholdError("caliper_ground_truth_missing")
            if (
                found.measurement_id != sample.measurement_id
                or found.measurement_revision_id != sample.measurement_revision_id
                or found.dimension_id != truth.dimension_id
            ):
                raise AcceptanceThresholdError("observation_sample_link_mismatch")
            group = (
                sample.category,
                found.material.value,
                DIMENSION_FEATURE_GROUPS[found.dimension_kind],
            )
            groups.setdefault(group, []).append(
                (
                    float(found.measured_value_mm) - truth.value_mm,
                    float(truth.uncertainty_mm or 0.0),
                )
            )
    if paired:
        raise AcceptanceThresholdError("observation_without_benchmark_sample")
    results = [_group_result(key, values) for key, values in sorted(groups.items())]
    for category in REQUIRED_BENCHMARK_CATEGORIES:
        if not any(
            item["category"] == category
            and item["feature_group"] == "overall_dimension"
            and item["status"] == "THRESHOLD_PROPOSED"
            for item in results
        ):
            raise AcceptanceThresholdError(f"insufficient_samples_for_required_category:{category}")
    body: dict[str, object] = {
        "contract": PROPOSAL_CONTRACT,
        "version": THRESHOLD_VERSION,
        "status": status,
        "simulation_only": status == TEST_ONLY,
        "physical_benchmark_gate": PL0220_PHYSICAL_BENCHMARK_STATUS,
        "physical_validation_status": PHYSICAL_EVIDENCE_PENDING,
        "rule": dict(RULE),
        "benchmark_record_digests": sorted(record.record_digest for record in by_record.values()),
        "observations_sha256": _digest(
            sorted((item.as_dict() for item in observations), key=lambda d: json.dumps(d))
        ),
        "groups": results,
        "mold_use_authorized": False,
    }
    return body | {"proposal_sha256": _digest(body)}


def _group_result(
    key: tuple[str, str, str], values: list[tuple[float, float]]
) -> dict[str, object]:
    category, material, feature_group = key
    errors = [error for error, _u in values]
    result: dict[str, object] = {
        "category": category,
        "material": material,
        "feature_group": feature_group,
        "sample_count": len(errors),
    }
    if len(errors) < MIN_SAMPLES_PER_GROUP:
        return result | {"status": "INSUFFICIENT_SAMPLES", "proposed_tolerance_mm": None}
    mean = statistics.fmean(errors)
    std = statistics.stdev(errors)
    k = tolerance_factor(len(errors))
    parametric = abs(mean) + k * std
    max_abs = max(abs(error) for error in errors)
    floor = CALIPER_COVERAGE_FACTOR * max(u for _e, u in values)
    tolerance = math.ceil(max(parametric, max_abs, floor) * 100.0 - 1e-9) / 100.0
    return result | {
        "status": "THRESHOLD_PROPOSED",
        "mean_error_mm": mean,
        "std_error_mm": std,
        "k_factor": k,
        "tolerance_bound_mm": parametric,
        "max_abs_error_mm": max_abs,
        "caliper_floor_mm": floor,
        "proposed_tolerance_mm": tolerance,
    }


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _digest_valid(value: Mapping[str, object], field: str) -> bool:
    body = {key: item for key, item in value.items() if key != field}
    try:
        return value.get(field) == _digest(body)
    except (TypeError, ValueError):
        return False
