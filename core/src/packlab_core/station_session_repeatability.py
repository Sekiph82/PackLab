"""PL-0401 scan-station repeatability across multiple sessions (days or setups).

Each session holds, per reference object, one accepted PL-0222 repeat-scan reproducibility
report plus the exact ``RegistrationRevision`` scans that report was computed from.

Common frame: a PL-0222 report gives extents in the axis frame of its own reference scan,
so an object re-placed on another day would read as a dimension change. Every session's
reference scan is therefore rigidly registered (accepted ``register_repeat_scans``, never
scaling) to one canonical reference per object: the reference scan of the chronologically
first session. Per-scan extents are recomputed as axis-aligned extents of
``T_session_reference_to_canonical * T_scan_to_session_reference * points``. Before that,
the supplied scans are bound to the report: revision ID, parent digest, scale provenance,
project, and the report's own extents must be reproduced from the scan points.

Per object and axis, a one-way random-effects model (ISO 5725-2 style, unbalanced allowed):

    MSW = SS_within / (N - k)            repeatability variance  s_r^2 = MSW
    MSB = SS_between / (k - 1)           between-session         s_L^2 = max(0, (MSB-MSW)/n0)
    n0  = (N - sum(n_i^2)/N) / (k - 1)   reproducibility         s_R^2 = s_r^2 + s_L^2

Drift: a session is flagged when its mean departs from the leave-one-out mean of the other
sessions by more than k standard errors (SE from the other sessions' between-session and
repeatability variance) and by more than a practical minimum shift. Station configuration
changes (layout revision, turntable driver identity, lighting preset, mat print record)
between chronologically adjacent sessions are flagged as well.

Thresholds are provisional pending PL-0221. PL-0222 reports are always simulation/proxy
evidence, so this report is never a physical repeatability PASS.
"""

from __future__ import annotations

import math
import re
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime

from .geometry_adapter import Open3DGeometryAdapter
from .reconstruction import ScaleState
from .repeat_scan_registration import (
    RegistrationError,
    RegistrationPolicy,
    RegistrationRevision,
    _hash,
    _transform_point,
    register_repeat_scans,
)
from .repeat_scan_reproducibility import _ACCEPTED, report_digest_valid
from .repeat_scan_reproducibility import REPORT_CONTRACT as PL0222_CONTRACT
from .repeat_scan_reproducibility import REPORT_VERSION as PL0222_VERSION

REPORT_CONTRACT = "packlab.station-session-repeatability-report.v1"
REPORT_VERSION = "station_session_repeatability_v1"
STATISTICS_VERSION = "one_way_random_effects_axis_extent_common_reference_frame_v1"
PHYSICAL_EVIDENCE_PENDING = "PHYSICAL_EVIDENCE_PENDING"
THRESHOLD_STATUS = "PROVISIONAL_PENDING_PL-0221"
_AXES = ("x", "y", "z")
_CONFIGURATION_FIELDS = (
    "layout_revision",
    "turntable_driver_identity",
    "lighting_preset",
    "mat_print_record",
)
# Pseudonymous references only (no names, e-mail or supplier data in the report).
_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")
_EXTENT_REPRODUCTION_TOLERANCE = 1e-9  # relative; same arithmetic as PL-0222

__all__ = [
    "PHYSICAL_EVIDENCE_PENDING",
    "REPORT_CONTRACT",
    "REPORT_VERSION",
    "THRESHOLD_STATUS",
    "StationRepeatabilityError",
    "StationRepeatabilityThresholds",
    "StationSession",
    "StationSessionMetadata",
    "evaluate_station_session_repeatability",
    "report_digest_valid",
]


class StationRepeatabilityError(ValueError):
    """Raised when multi-session inputs cannot support a repeatability statement."""


@dataclass(frozen=True, slots=True)
class StationRepeatabilityThresholds:
    """Provisional gates in the scans' coordinate unit; replace once PL-0221 is accepted."""

    minimum_sessions: int = 5
    minimum_repeats_per_session: int = 2
    drift_k_standard_errors: float = 5.0
    minimum_drift_shift: float = 0.05
    identity_relative_tolerance: float = 0.05
    maximum_repeatability_sd: float = 0.2
    maximum_reproducibility_sd: float = 0.3
    # Not settable: only PL-0221 acceptance may relabel thresholds, in a new contract.
    status: str = field(default=THRESHOLD_STATUS, init=False)

    def __post_init__(self) -> None:
        # Leave-one-out drift needs two remaining sessions to estimate between-session spread.
        if isinstance(self.minimum_sessions, bool) or self.minimum_sessions < 3:
            raise StationRepeatabilityError("minimum_sessions_must_be_at_least_three")
        if (
            isinstance(self.minimum_repeats_per_session, bool)
            or self.minimum_repeats_per_session < 2
        ):
            raise StationRepeatabilityError("minimum_repeats_must_be_at_least_two")
        for value in (
            self.drift_k_standard_errors,
            self.minimum_drift_shift,
            self.identity_relative_tolerance,
            self.maximum_repeatability_sd,
            self.maximum_reproducibility_sd,
        ):
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0.0:
                raise StationRepeatabilityError("station_threshold_invalid")


@dataclass(frozen=True, slots=True)
class StationSessionMetadata:
    """Station state recorded by the operator at the start of a session."""

    layout_revision: str
    turntable_driver_identity: str
    lighting_preset: str
    mat_print_record: str
    operator_reference: str
    started_at_utc: str

    def __post_init__(self) -> None:
        for name in (*_CONFIGURATION_FIELDS, "operator_reference"):
            if not _safe_reference(getattr(self, name)):
                raise StationRepeatabilityError(f"session_{name}_invalid")
        try:
            moment = datetime.fromisoformat(self.started_at_utc)
        except (TypeError, ValueError):
            raise StationRepeatabilityError("session_started_at_utc_invalid") from None
        offset = moment.utcoffset()
        if offset is None or offset.total_seconds() != 0:
            raise StationRepeatabilityError("session_started_at_utc_must_be_utc")

    @property
    def started_at(self) -> datetime:
        return datetime.fromisoformat(self.started_at_utc)


@dataclass(frozen=True, slots=True)
class StationSession:
    """One session: metadata, one PL-0222 report per object ID and the scans behind it."""

    session_id: str
    metadata: StationSessionMetadata
    object_reports: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    object_scans: Mapping[str, Sequence[RegistrationRevision]] = field(default_factory=dict)


def evaluate_station_session_repeatability(
    sessions: Sequence[StationSession],
    *,
    policy: RegistrationPolicy,
    thresholds: StationRepeatabilityThresholds | None = None,
    initial_transforms: Mapping[tuple[str, str], tuple[float, ...]] | None = None,
    adapter: Open3DGeometryAdapter | None = None,
) -> dict[str, object]:
    """Decompose repeat-scan extents across sessions into a digest-bound report.

    ``initial_transforms[(session_id, object_id)]`` optionally seeds the rigid registration
    of that session's reference scan to the canonical reference (operator coarse alignment);
    registration that is not accepted fails closed.
    """

    gates = StationRepeatabilityThresholds() if thresholds is None else thresholds
    if not isinstance(gates, StationRepeatabilityThresholds):
        raise StationRepeatabilityError("typed_thresholds_required")
    if not isinstance(policy, RegistrationPolicy):
        raise StationRepeatabilityError("registration_policy_required")
    items = tuple(sessions)
    if any(not isinstance(item, StationSession) for item in items):
        raise StationRepeatabilityError("typed_station_sessions_required")
    if any(not isinstance(item.metadata, StationSessionMetadata) for item in items):
        raise StationRepeatabilityError("typed_session_metadata_required")
    if len(items) < gates.minimum_sessions:
        raise StationRepeatabilityError("insufficient_sessions")
    if any(not _safe_reference(item.session_id) for item in items):
        raise StationRepeatabilityError("session_id_invalid")
    if len({item.session_id for item in items}) != len(items):
        raise StationRepeatabilityError("session_ids_must_be_unique")
    if len({item.metadata.started_at for item in items}) != len(items):
        raise StationRepeatabilityError("session_timestamps_must_be_unique")
    ordered = sorted(items, key=lambda item: item.metadata.started_at)
    if any(not _safe_reference(obj) for item in ordered for obj in item.object_reports):
        raise StationRepeatabilityError("object_id_invalid")
    object_ids = sorted(ordered[0].object_reports)
    if not object_ids:
        raise StationRepeatabilityError("no_reference_objects")
    if any(
        sorted(item.object_reports) != object_ids or sorted(item.object_scans) != object_ids
        for item in ordered
    ):
        raise StationRepeatabilityError("object_identities_inconsistent_between_sessions")
    reports = [item.object_reports[obj] for item in ordered for obj in object_ids]
    _check_reports(reports, ordered, object_ids)
    initial = dict(initial_transforms or {})
    usable = {(item.session_id, obj) for item in ordered[1:] for obj in object_ids}
    if any(not isinstance(key, tuple) or key not in usable for key in initial):
        # The first session is the canonical frame, so it can never take a coarse alignment.
        raise StationRepeatabilityError("initial_transform_key_unknown_or_unused")
    adapter = adapter or Open3DGeometryAdapter()
    adapter_identity = f"{type(adapter).__module__}.{type(adapter).__qualname__}"

    # extents[object][session_index] = (x, y, z) per used scan, in the canonical frame.
    extents: dict[str, list[list[tuple[float, float, float]]]] = {}
    alignments: dict[str, dict[str, object]] = {item.session_id: {} for item in ordered}
    for obj in object_ids:
        bound = [_bind_scans(item.object_reports[obj], item.object_scans[obj]) for item in ordered]
        canonical = bound[0][0]
        per_session = []
        for item, (reference, used) in zip(ordered, bound, strict=True):
            if len(used) < gates.minimum_repeats_per_session:
                raise StationRepeatabilityError("insufficient_repeats_in_session")
            if reference is canonical:
                to_canonical = None
                alignments[item.session_id][obj] = {"canonical_reference": True}
            else:
                seed = initial.get((item.session_id, obj))
                try:
                    registration = register_repeat_scans(
                        reference,
                        canonical,
                        policy=policy,
                        initial_transform=seed,
                        adapter=adapter,
                    )
                except RegistrationError as error:
                    raise StationRepeatabilityError(
                        "cross_session_reference_registration_invalid"
                    ) from error
                if registration.convergence_status != _ACCEPTED:
                    # Wrong object, gross re-placement without a coarse alignment, or
                    # partial capture: never pool extents from an unaligned frame.
                    raise StationRepeatabilityError(
                        "cross_session_reference_registration_not_accepted"
                    )
                to_canonical = registration.transform_source_to_target
                alignments[item.session_id][obj] = {
                    "canonical_reference": False,
                    "registration_id": registration.registration_id,
                    "inlier_ratio": registration.inlier_ratio,
                    "inlier_rmse": registration.inlier_rmse,
                    "initial_transform_supplied": seed is not None,
                    "initial_transform": list(registration.initial_transform),
                    "transform_session_reference_to_canonical": list(to_canonical),
                    # Total re-placement rotation, and what ICP changed beyond the seed.
                    "rotation_to_canonical_deg": _rotation_deg(to_canonical),
                    "rotation_beyond_initial_deg": _rotation_deg(
                        to_canonical, registration.initial_transform
                    ),
                }
            per_session.append(
                [_aabb(points, (transform, to_canonical)) for points, transform in used]
            )
        extents[obj] = per_session
        _check_identity(per_session, gates.identity_relative_tolerance)

    session_flags: dict[str, list[str]] = {item.session_id: [] for item in ordered}
    configuration_changes = []
    for previous, current in zip(ordered, ordered[1:], strict=False):
        for name in _CONFIGURATION_FIELDS:
            before, after = getattr(previous.metadata, name), getattr(current.metadata, name)
            if before != after:
                configuration_changes.append(
                    {
                        "session_id": current.session_id,
                        "previous_session_id": previous.session_id,
                        "field": name,
                        "previous": before,
                        "current": after,
                    }
                )
                session_flags[current.session_id].append(f"station_configuration_change:{name}")

    components: dict[str, dict[str, dict[str, float | int | str | bool]]] = {}
    drift: list[dict[str, object]] = []
    for obj in object_ids:
        components[obj] = {}
        for axis, axis_name in enumerate(_AXES):
            groups = [[value[axis] for value in session] for session in extents[obj]]
            components[obj][f"extent_{axis_name}"] = _decompose(groups)
            for index, item in enumerate(ordered):
                shift, standard_error = _leave_one_out_shift(groups, index)
                # The practical floor also makes SE == 0 (noise-free input) well defined.
                if abs(shift) <= gates.minimum_drift_shift or abs(shift) <= (
                    gates.drift_k_standard_errors * standard_error
                ):
                    continue
                drift.append(
                    {
                        "session_id": item.session_id,
                        "object_id": obj,
                        "dimension": f"extent_{axis_name}",
                        "shift": shift,
                        "standard_error": standard_error,
                        "k_standard_errors": (
                            abs(shift) / standard_error if standard_error > 0.0 else None
                        ),
                    }
                )
                if "session_mean_drift" not in session_flags[item.session_id]:
                    session_flags[item.session_id].append("session_mean_drift")

    all_stats = [stats for per_axis in components.values() for stats in per_axis.values()]
    worst_r = max(float(stats["repeatability_sd"]) for stats in all_stats)
    worst_reproducibility = max(float(stats["reproducibility_sd"]) for stats in all_stats)
    within = (
        not drift
        and not configuration_changes
        and worst_r <= gates.maximum_repeatability_sd
        and worst_reproducibility <= gates.maximum_reproducibility_sd
    )
    first = reports[0]
    body: dict[str, object] = {
        "contract": REPORT_CONTRACT,
        "version": REPORT_VERSION,
        "statistics_version": STATISTICS_VERSION,
        # Inputs are PL-0222 reports, which are always simulation/proxy evidence; no
        # owner-signed physical session record can be bound in this version.
        "simulation_only": True,
        "physical_validation_status": PHYSICAL_EVIDENCE_PENDING,
        "physical_repeatability_claim": False,
        "scale_state": first["scale_state"],
        "coordinate_unit": first["coordinate_unit"],
        "scale_evidence_class_claimed_physical": first["scale_evidence_class_claimed_physical"],
        "extent_frame": "axis_aligned_in_canonical_reference_scan_frame_first_session",
        "registration_policy": policy.as_dict(),
        "registration_adapter": adapter_identity,
        "thresholds": asdict(gates),
        "object_ids": object_ids,
        "sessions": [
            {
                "session_id": item.session_id,
                "metadata": asdict(item.metadata),
                "input_report_sha256": {
                    obj: item.object_reports[obj]["report_sha256"] for obj in object_ids
                },
                "reference_alignment": alignments[item.session_id],
                "repeats_used": {obj: len(extents[obj][index]) for obj in object_ids},
                "flags": session_flags[item.session_id],
            }
            for index, item in enumerate(ordered)
        ],
        "variance_components": components,
        "configuration_changes": configuration_changes,
        "drift_detections": drift,
        "worst_repeatability_sd": worst_r,
        "worst_reproducibility_sd": worst_reproducibility,
        "provisional_threshold_result": (
            "WITHIN_PROVISIONAL_THRESHOLDS" if within else "EXCEEDS_PROVISIONAL_THRESHOLDS"
        ),
    }
    return body | {"report_sha256": _hash(body)}


def _safe_reference(value: object) -> bool:
    return isinstance(value, str) and _REFERENCE.fullmatch(value) is not None


def _scans(report: Mapping[str, object]) -> list[Mapping[str, object]]:
    scans = report.get("scans")
    if not isinstance(scans, list) or any(not isinstance(scan, Mapping) for scan in scans):
        raise StationRepeatabilityError("pl0222_report_scans_invalid")
    return scans


def _extent(scan: Mapping[str, object]) -> tuple[float, float, float]:
    raw = scan.get("extents")
    if not isinstance(raw, Mapping):
        raise StationRepeatabilityError("pl0222_scan_extents_invalid")
    values = tuple(raw.get(axis) for axis in _AXES)
    if any(
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(value)
        or value <= 0.0
        for value in values
    ):
        raise StationRepeatabilityError("pl0222_scan_extents_invalid")
    return (float(values[0]), float(values[1]), float(values[2]))  # type: ignore[arg-type]


_Points = tuple[tuple[float, float, float], ...]


def _aabb(
    points: _Points, transforms: tuple[tuple[float, ...] | None, ...]
) -> tuple[float, float, float]:
    moved: list[tuple[float, float, float]] = list(points)
    for transform in transforms:
        if transform is not None:
            moved = [_transform_point(transform, point) for point in moved]
    low = [min(point[axis] for point in moved) for axis in range(3)]
    high = [max(point[axis] for point in moved) for axis in range(3)]
    return (high[0] - low[0], high[1] - low[1], high[2] - low[2])


def _bind_scans(
    report: Mapping[str, object], revisions: Sequence[RegistrationRevision]
) -> tuple[RegistrationRevision, list[tuple[_Points, tuple[float, ...] | None]]]:
    """Prove the supplied scans are the report's scans; return reference and used scans."""

    scans = _scans(report)
    if any(not isinstance(item, RegistrationRevision) for item in revisions):
        raise StationRepeatabilityError("typed_registration_revisions_required")
    by_id = {item.revision_id: item for item in revisions}
    if len(by_id) != len(revisions) or sorted(by_id) != sorted(
        str(scan.get("revision_id")) for scan in scans
    ):
        raise StationRepeatabilityError("pl0222_scan_revisions_mismatch")
    reference = by_id.get(str(report.get("reference_revision_id")))
    if reference is None:
        raise StationRepeatabilityError("pl0222_scan_revisions_mismatch")
    used: list[tuple[_Points, tuple[float, ...] | None]] = []
    for scan in scans:
        revision = by_id[str(scan["revision_id"])]
        if (
            revision.parent_digest != scan.get("parent_digest")
            or revision.scale_provenance_id != scan.get("scale_provenance_id")
            or revision.project_id != report.get("project_id")
            or revision.coordinate_unit != report.get("coordinate_unit")
        ):
            raise StationRepeatabilityError("pl0222_scan_revision_identity_mismatch")
        if revision is reference:
            transform = None
        else:
            raw = scan.get("transform_scan_to_reference")
            if (
                not isinstance(raw, list)
                or len(raw) != 16
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int | float)
                    or not math.isfinite(value)
                    for value in raw
                )
            ):
                raise StationRepeatabilityError("pl0222_scan_transform_invalid")
            transform = tuple(float(value) for value in raw)
        points = revision.point_cloud.points
        reported = _extent(scan)
        recomputed = _aabb(points, (transform,))
        if any(
            not abs(a - b) <= _EXTENT_REPRODUCTION_TOLERANCE * max(1.0, abs(a))
            for a, b in zip(reported, recomputed, strict=True)
        ):
            raise StationRepeatabilityError("pl0222_extents_not_reproducible_from_scans")
        if scan.get("used_in_dimension_statistics") is True:
            used.append((points, transform))
    return reference, used


def _rotation_deg(
    transform: tuple[float, ...], reference: tuple[float, ...] | None = None
) -> float:
    """Rotation angle of ``transform`` (relative to ``reference`` if given), in degrees."""

    rotation = [[transform[row * 4 + col] for col in range(3)] for row in range(3)]
    if reference is not None:
        base = [[reference[row * 4 + col] for col in range(3)] for row in range(3)]
        # trace(B^T R) = sum of elementwise products.
        trace = sum(base[r][c] * rotation[r][c] for r in range(3) for c in range(3))
    else:
        trace = rotation[0][0] + rotation[1][1] + rotation[2][2]
    return math.degrees(math.acos(max(-1.0, min(1.0, (trace - 1.0) / 2.0))))


def _check_reports(
    reports: list[Mapping[str, object]],
    ordered: list[StationSession],
    object_ids: list[str],
) -> None:
    for report in reports:
        try:
            valid = isinstance(report, Mapping) and report_digest_valid(report)
        except (TypeError, ValueError):  # NaN/inf or non-JSON content cannot be digest-bound
            valid = False
        if not valid:
            raise StationRepeatabilityError("pl0222_report_digest_invalid")
        if report.get("contract") != PL0222_CONTRACT or report.get("version") != PL0222_VERSION:
            raise StationRepeatabilityError("pl0222_report_contract_unsupported")
        if (
            report.get("simulation_only") is not True
            or report.get("physical_validation_status") != PHYSICAL_EVIDENCE_PENDING
        ):
            raise StationRepeatabilityError("pl0222_report_physical_status_unexpected")
    for name in ("scale_state", "coordinate_unit", "scale_evidence_class_claimed_physical"):
        if len({repr(report.get(name)) for report in reports}) != 1:
            raise StationRepeatabilityError(f"mixed_{name}_between_reports")
    if reports[0].get("scale_state") != ScaleState.METRIC_UNVERIFIED.value:
        # RELATIVE units are arbitrary per scan; anything else is not a PL-0222 input state.
        raise StationRepeatabilityError("scale_state_must_be_metric_unverified")
    if len({report["report_sha256"] for report in reports}) != len(reports):
        raise StationRepeatabilityError("pl0222_report_reused")
    seen_provenance: set[object] = set()
    seen_revision: set[object] = set()
    for report in reports:
        for scan in _scans(report):
            provenance, revision = scan.get("scale_provenance_id"), scan.get("revision_id")
            if provenance in seen_provenance or revision in seen_revision:
                raise StationRepeatabilityError("scan_provenance_shared_between_reports")
            seen_provenance.add(provenance)
            seen_revision.add(revision)
    for obj in object_ids:
        if len({repr(item.object_reports[obj].get("project_id")) for item in ordered}) != 1:
            raise StationRepeatabilityError("object_project_identity_inconsistent")


def _check_identity(per_session: list[list[tuple[float, float, float]]], tolerance: float) -> None:
    """A gross session-mean extent mismatch means a different object, not station drift."""

    means = [
        tuple(statistics.fmean(v[a] for v in session) for a in range(3)) for session in per_session
    ]
    for axis in range(3):
        median = statistics.median(mean[axis] for mean in means)
        if any(abs(mean[axis] / median - 1.0) > tolerance for mean in means):
            raise StationRepeatabilityError("object_identity_extent_mismatch")


def _decompose(groups: list[list[float]]) -> dict[str, float | int | str | bool]:
    k = len(groups)
    sizes = [len(group) for group in groups]
    total = sum(sizes)
    means = [statistics.fmean(group) for group in groups]
    grand = statistics.fmean(value for group in groups for value in group)
    ss_within = sum(
        (value - mean) ** 2 for group, mean in zip(groups, means, strict=True) for value in group
    )
    ss_between = sum(n * (mean - grand) ** 2 for n, mean in zip(sizes, means, strict=True))
    ms_within = ss_within / (total - k)
    ms_between = ss_between / (k - 1)
    n0 = (total - sum(n * n for n in sizes) / total) / (k - 1)
    between_var = max(0.0, (ms_between - ms_within) / n0)
    return {
        "sessions": k,
        "observations": total,
        "grand_mean": grand,
        "ms_within": ms_within,
        "ms_between": ms_between,
        "n0": n0,
        "repeatability_sd": math.sqrt(ms_within),
        "between_session_sd": math.sqrt(between_var),
        "reproducibility_sd": math.sqrt(ms_within + between_var),
        "between_session_variance_truncated_at_zero": ms_between < ms_within,
        "method": "one_way_random_effects_anova_iso5725_unbalanced",
    }


def _leave_one_out_shift(groups: list[list[float]], index: int) -> tuple[float, float]:
    """Session mean minus the other sessions' grand mean, and its standard error."""

    others = groups[:index] + groups[index + 1 :]
    rest = _decompose(others)
    session = groups[index]
    repeat_var = float(rest["ms_within"])
    between_var = float(rest["between_session_sd"]) ** 2
    # Var(session mean) + Var(other grand mean); MSB/N approximates the latter (exact if balanced).
    variance = (
        between_var
        + repeat_var / len(session)
        + float(rest["ms_between"]) / int(rest["observations"])
    )
    shift = statistics.fmean(session) - float(rest["grand_mean"])
    return shift, math.sqrt(variance)
