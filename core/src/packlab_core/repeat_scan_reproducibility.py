"""PL-0222 repeat-scan reproducibility statistics for N scans of the same object.

Every scan is rigidly registered to one reference scan with the accepted PL-0219
``register_repeat_scans`` path (scaling is never enabled). Reproducibility is then
summarised per overall dimension (axis extents in the reference frame) and for the
surface deviation (registration residual distances). Scans are fail-closed on scale
state/provenance, flagged for partial coverage (reverse-registration fitness) and for a
scale outlier (relative extent deviation from the consensus of fully covered scans).

Thresholds are provisional pending PL-0221. Statistics on synthetic inputs only verify
the software math; the report is never a physical repeatability PASS.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from .calibration.scale_provenance import ScaleProvenance
from .geometry_adapter import Open3DGeometryAdapter
from .reconstruction import ScaleState
from .repeat_scan_registration import (
    RegistrationPolicy,
    RegistrationRevision,
    _hash,
    _transform_point,
    register_repeat_scans,
)

REPORT_CONTRACT = "packlab.repeat-scan-reproducibility-report.v1"
REPORT_VERSION = "repeat_scan_reproducibility_v1"
STATISTICS_VERSION = "axis_extent_and_residual_repeatability_v1"
PHYSICAL_EVIDENCE_PENDING = "PHYSICAL_EVIDENCE_PENDING"
_ACCEPTED = "QUALITY_ACCEPTED_STOP_REASON_UNAVAILABLE"
_AXES = ("x", "y", "z")
_RC_FACTOR = 1.96 * math.sqrt(2.0)  # Bland-Altman / ISO 5725 repeatability limit = 2.77 s


class ReproducibilityError(ValueError):
    """Raised when repeat-scan inputs cannot support a reproducibility statement."""


@dataclass(frozen=True, slots=True)
class ReproducibilityThresholds:
    """Provisional gates in the scans' coordinate unit; replace once PL-0221 is accepted."""

    minimum_revisions: int = 3
    minimum_coverage_ratio: float = 0.95
    scale_outlier_relative_tolerance: float = 0.005
    maximum_dimension_repeatability_coefficient: float = 0.5
    maximum_surface_deviation_p95: float = 0.5
    status: str = "PROVISIONAL_PENDING_PL-0221"

    def __post_init__(self) -> None:
        if isinstance(self.minimum_revisions, bool) or self.minimum_revisions < 3:
            raise ReproducibilityError("minimum_revisions_must_be_at_least_three")
        if not 0.0 < self.minimum_coverage_ratio <= 1.0:
            raise ReproducibilityError("minimum_coverage_ratio_invalid")
        for value in (
            self.scale_outlier_relative_tolerance,
            self.maximum_dimension_repeatability_coefficient,
            self.maximum_surface_deviation_p95,
        ):
            if not math.isfinite(value) or value <= 0.0:
                raise ReproducibilityError("reproducibility_threshold_invalid")


def evaluate_repeat_scan_reproducibility(
    revisions: Sequence[RegistrationRevision],
    scale_provenances: Mapping[str, ScaleProvenance],
    *,
    policy: RegistrationPolicy,
    thresholds: ReproducibilityThresholds | None = None,
    reference_revision_id: str | None = None,
    initial_transforms: Mapping[str, tuple[float, ...]] | None = None,
    adapter: Open3DGeometryAdapter | None = None,
) -> dict[str, object]:
    """Register every scan to the reference and return a digest-bound statistics report."""

    gates = thresholds or ReproducibilityThresholds()
    scans = tuple(revisions)
    if any(not isinstance(item, RegistrationRevision) for item in scans):
        raise ReproducibilityError("typed_registration_revisions_required")
    if len(scans) < gates.minimum_revisions:
        raise ReproducibilityError("insufficient_repeat_scan_revisions")
    if len({item.revision_id for item in scans}) != len(scans):
        raise ReproducibilityError("repeat_scan_revision_ids_must_be_unique")
    _check_scale(scans, scale_provenances)
    if policy.maximum_correspondence_distance <= gates.maximum_surface_deviation_p95:
        # Residuals are gate-truncated inliers, so p95 could never exceed such a threshold.
        raise ReproducibilityError("correspondence_gate_must_exceed_surface_threshold")
    by_id = {item.revision_id: item for item in scans}
    reference = scans[0] if reference_revision_id is None else by_id.get(reference_revision_id)
    if reference is None:
        raise ReproducibilityError("reference_revision_not_found")
    adapter = adapter or Open3DGeometryAdapter()
    initial = dict(initial_transforms or {})

    records: list[dict[str, object]] = []
    flags: dict[str, list[str]] = {}
    extents: dict[str, tuple[float, float, float]] = {}
    residuals: dict[str, tuple[float, ...]] = {}
    for scan in scans:
        record: dict[str, object] = {
            "revision_id": scan.revision_id,
            "parent_digest": scan.parent_digest,
            "scale_provenance_id": scan.scale_provenance_id,
            "is_reference": scan is reference,
        }
        if scan is reference:
            points = scan.point_cloud.points
            record |= {"convergence_status": "REFERENCE", "coverage_ratio": 1.0}
        else:
            forward = register_repeat_scans(
                scan,
                reference,
                policy=policy,
                initial_transform=initial.get(scan.revision_id),
                adapter=adapter,
            )
            # Coverage = share of reference points that find this scan within the gate.
            reverse = register_repeat_scans(
                reference,
                scan,
                policy=policy,
                initial_transform=_invert_rigid(forward.transform_source_to_target),
                adapter=adapter,
            )
            transform = forward.transform_source_to_target
            points = tuple(_transform_point(transform, point) for point in scan.point_cloud.points)
            record |= {
                "registration_id": forward.registration_id,
                "convergence_status": forward.convergence_status,
                "inlier_ratio": forward.inlier_ratio,
                "inlier_rmse": forward.inlier_rmse,
                "coverage_registration_id": reverse.registration_id,
                "coverage_ratio": reverse.inlier_ratio,
                "transform_scan_to_reference": list(transform),
            }
            if forward.convergence_status == _ACCEPTED:
                residuals[scan.revision_id] = forward.residuals
        extent = tuple(
            max(point[axis] for point in points) - min(point[axis] for point in points)
            for axis in range(3)
        )
        record["extents"] = dict(zip(_AXES, extent, strict=True))
        status, coverage = record["convergence_status"], record["coverage_ratio"]
        scan_flags = flags[scan.revision_id] = []
        if status not in {"REFERENCE", _ACCEPTED}:
            scan_flags.append("registration_not_accepted")
        elif isinstance(coverage, float) and coverage < gates.minimum_coverage_ratio:
            scan_flags.append("partial_coverage")
        else:
            extents[scan.revision_id] = (extent[0], extent[1], extent[2])
        records.append(record)

    if len(extents) < 2:
        raise ReproducibilityError("insufficient_fully_covered_registered_scans")
    consensus = tuple(
        statistics.median(item[axis] for item in extents.values()) for axis in range(3)
    )
    if any(value <= 0.0 for value in consensus):
        raise ReproducibilityError("degenerate_zero_extent")
    deviations = {
        revision_id: statistics.fmean(extent[axis] / consensus[axis] for axis in range(3)) - 1.0
        for revision_id, extent in extents.items()
    }
    for revision_id, deviation in deviations.items():
        if abs(deviation) > gates.scale_outlier_relative_tolerance:
            flags[revision_id].append("scale_outlier")
            extents.pop(revision_id)
    for record in records:
        revision_id = str(record["revision_id"])
        record["relative_scale_deviation"] = deviations.get(revision_id)
        record["flags"] = flags[revision_id]
        record["used_in_dimension_statistics"] = revision_id in extents
        record["used_in_surface_statistics"] = (
            revision_id in residuals and "scale_outlier" not in flags[revision_id]
        )
    if len(extents) < 2:
        raise ReproducibilityError("insufficient_scans_after_outlier_rejection")

    dimensions = {
        f"extent_{axis_name}": _dimension_statistics([item[axis] for item in extents.values()])
        for axis, axis_name in enumerate(_AXES)
    }
    pooled = [
        value
        for revision_id, values in residuals.items()
        if "scale_outlier" not in flags[revision_id]
        for value in values
    ]
    surface = _surface_statistics(pooled)
    worst_dimension_rc = max(
        float(item["repeatability_coefficient_95"]) for item in dimensions.values()
    )
    within = (
        worst_dimension_rc <= gates.maximum_dimension_repeatability_coefficient
        and surface is not None
        and float(surface["p95_distance"]) <= gates.maximum_surface_deviation_p95
    )
    body: dict[str, object] = {
        "contract": REPORT_CONTRACT,
        "version": REPORT_VERSION,
        "statistics_version": STATISTICS_VERSION,
        # No owner-signed record can be bound here (RegistrationRevision forbids
        # METRIC_VERIFIED), so the report is always simulation/proxy evidence.
        "simulation_only": True,
        "scale_evidence_class_claimed_physical": _claimed_physical(scans, scale_provenances),
        "scale_evidence_class_basis": "caller_asserted_label_not_owner_record_bound",
        "physical_validation_status": PHYSICAL_EVIDENCE_PENDING,
        "physical_reproducibility_claim": False,
        "mold_use_authorized": False,
        "project_id": reference.project_id,
        "reference_revision_id": reference.revision_id,
        "scale_state": reference.scale_state.value,
        "coordinate_unit": reference.coordinate_unit,
        "registration_policy": policy.as_dict(),
        "surface_residuals_truncated_at_correspondence_distance": (
            policy.maximum_correspondence_distance
        ),
        "thresholds": asdict(gates),
        "scans": records,
        "consensus_extents": dict(zip(_AXES, consensus, strict=True)),
        "dimension_statistics": dimensions,
        "surface_deviation_statistics": surface,
        "provisional_threshold_result": (
            "WITHIN_PROVISIONAL_THRESHOLDS" if within else "EXCEEDS_PROVISIONAL_THRESHOLDS"
        ),
    }
    return body | {"report_sha256": _hash(body)}


def _check_scale(
    scans: tuple[RegistrationRevision, ...], provenances: Mapping[str, ScaleProvenance]
) -> None:
    if (
        len({item.scale_state for item in scans}) != 1
        or len({item.coordinate_unit for item in scans}) != 1
    ):
        raise ReproducibilityError("scale_state_mismatch")
    if scans[0].scale_state is not ScaleState.METRIC_UNVERIFIED:
        # Each relative reconstruction has its own arbitrary unit; comparing them is meaningless.
        raise ReproducibilityError("relative_scale_reproducibility_forbidden")
    if len({scan.scale_provenance_id for scan in scans}) != len(scans):
        raise ReproducibilityError("scale_provenance_shared_between_scans")
    for scan in scans:
        provenance = provenances.get(scan.scale_provenance_id)
        if not isinstance(provenance, ScaleProvenance):
            raise ReproducibilityError("scale_provenance_missing")
        if provenance.provenance_id != scan.scale_provenance_id:
            raise ReproducibilityError("scale_provenance_identity_mismatch")
        if (
            provenance.scale_state is not scan.scale_state
            or provenance.estimated_scale_factor_mm_per_reconstruction_unit is None
        ):
            raise ReproducibilityError("scale_provenance_state_mismatch")


def _claimed_physical(
    scans: tuple[RegistrationRevision, ...], provenances: Mapping[str, ScaleProvenance]
) -> bool:
    """Caller-asserted label only: every used marker reference says owner-physical."""

    for scan in scans:
        used = [
            item
            for item in provenances[scan.scale_provenance_id].physical_references
            if item.get("used_in_estimate") is True
        ]
        if not used or any(
            item.get("evidence_class") != "accepted_owner_physical" for item in used
        ):
            return False
    return True


def report_digest_valid(report: Mapping[str, object]) -> bool:
    body = {key: value for key, value in report.items() if key != "report_sha256"}
    return report.get("report_sha256") == _hash(body)


def _dimension_statistics(values: list[float]) -> dict[str, float | str]:
    mean = statistics.fmean(values)
    std = statistics.stdev(values)
    deviations = [value - mean for value in values]
    return {
        "count": len(values),
        "mean": mean,
        "std": std,
        "min": min(values),
        "max": max(values),
        "max_abs_deviation": max(abs(value) for value in deviations),
        "rms_deviation": math.sqrt(statistics.fmean(value * value for value in deviations)),
        "repeatability_coefficient_95": _RC_FACTOR * std,
        "repeatability_coefficient_definition": "1.96*sqrt(2)*sample_std",
    }


def _surface_statistics(values: list[float]) -> dict[str, float | str] | None:
    if len(values) < 2:
        return None
    ordered = sorted(values)
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "std": statistics.stdev(values),
        "max": ordered[-1],
        "rms": math.sqrt(statistics.fmean(value * value for value in values)),
        # Unsigned distances: nearest-rank 95th percentile, not a Bland-Altman coefficient.
        "p95_distance": ordered[math.ceil(0.95 * len(ordered)) - 1],
        "p95_definition": "nearest_rank_p95_scan_to_reference_inlier_distance",
    }


def _invert_rigid(transform: tuple[float, ...]) -> tuple[float, ...]:
    rotation_t = [[transform[col * 4 + row] for col in range(3)] for row in range(3)]
    translation = [transform[row * 4 + 3] for row in range(3)]
    inverse_t = [
        -sum(rotation_t[row][col] * translation[col] for col in range(3)) for row in range(3)
    ]
    return (
        *rotation_t[0],
        inverse_t[0],
        *rotation_t[1],
        inverse_t[1],
        *rotation_t[2],
        inverse_t[2],
        0.0,
        0.0,
        0.0,
        1.0,
    )
