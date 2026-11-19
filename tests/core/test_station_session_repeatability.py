"""PL-0401 multi-session station repeatability: seeded synthetic sessions check the math only.

Synthetic sessions are axis-aligned box surface samples with injected per-axis extents
(truth + session effect + repeat noise), so the ground-truth variance components are known.
They are not physical scans and prove nothing about a physical station.
"""

from __future__ import annotations

import hashlib
import math
import random
from datetime import UTC, datetime, timedelta

import pytest
from tests.core.test_repeat_scan_reproducibility import (
    BOX_MM,
    POLICY,
    _provenance,
    _revision,
    _scan_points,
)

from packlab_core.geometry_adapter import PointCloudData
from packlab_core.reconstruction import ScaleState
from packlab_core.repeat_scan_registration import (
    RegistrationRevision,
    _hash,
    _point_cloud_digest,
)
from packlab_core.repeat_scan_reproducibility import REPORT_CONTRACT as PL0222_CONTRACT
from packlab_core.repeat_scan_reproducibility import REPORT_VERSION as PL0222_VERSION
from packlab_core.repeat_scan_reproducibility import evaluate_repeat_scan_reproducibility
from packlab_core.station_session_repeatability import (
    PHYSICAL_EVIDENCE_PENDING,
    THRESHOLD_STATUS,
    StationRepeatabilityError,
    StationRepeatabilityThresholds,
    StationSession,
    StationSessionMetadata,
    _bind_scans,
    _decompose,
    _leave_one_out_shift,
    evaluate_station_session_repeatability,
    report_digest_valid,
)

OBJECTS = {"hdpe-bottle-proxy": BOX_MM, "pp-cap-proxy": (30.0, 30.0, 18.0)}
_IDENTITY = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def _yaw(points, degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return tuple((c * x - s * y, s * x + c * y, z) for x, y, z in points)


def _yaw_transform(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return (c, -s, 0.0, 0.0, s, c, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)


def _box(extent, steps=4):
    grid = [[-e / 2 + e * i / steps for i in range(steps + 1)] for e in extent]
    return tuple(
        (x, y, z)
        for i, x in enumerate(grid[0])
        for j, y in enumerate(grid[1])
        for k, z in enumerate(grid[2])
        if i in (0, steps) or j in (0, steps) or k in (0, steps)
    )


def _registration_revision(revision_id, project, points, provenance_id):
    cloud = PointCloudData(tuple(points))
    return RegistrationRevision(
        revision_id,
        project,
        hashlib.sha256(f"parent-{revision_id}".encode()).hexdigest(),
        cloud,
        _point_cloud_digest(cloud),
        "OBJECT_CAPTURE_GEOMETRY",
        False,
        f"frame-{revision_id}",
        "mm_unverified",
        ScaleState.METRIC_UNVERIFIED,
        provenance_id,
        "DEFERRED_OWNER_VALIDATION",
        False,
    )


def _aabb(points):
    return {
        axis: max(p[i] for p in points) - min(p[i] for p in points) for i, axis in enumerate("xyz")
    }


def _object_session(obj, session_id, extents, *, yaw=0.0, project=None, **overrides):
    """PL-0222-shaped report plus the RegistrationRevisions it was computed from."""

    project = project or f"project-{obj}"
    revisions = [
        _registration_revision(
            f"{session_id}-{obj}-scan-{index}",
            project,
            _yaw(_box(extent), yaw),
            f"prov-{session_id}-{obj}-{index}",
        )
        for index, extent in enumerate(extents)
    ]
    scans = [
        {
            "revision_id": rev.revision_id,
            "parent_digest": rev.parent_digest,
            "scale_provenance_id": rev.scale_provenance_id,
            "is_reference": index == 0,
            "extents": _aabb(rev.point_cloud.points),
            "used_in_dimension_statistics": True,
            "flags": [],
        }
        | ({} if index == 0 else {"transform_scan_to_reference": list(_IDENTITY)})
        for index, rev in enumerate(revisions)
    ]
    body = {
        "contract": PL0222_CONTRACT,
        "version": PL0222_VERSION,
        "simulation_only": True,
        "physical_validation_status": PHYSICAL_EVIDENCE_PENDING,
        "project_id": project,
        "reference_revision_id": revisions[0].revision_id,
        "scale_state": "metric-unverified",
        "coordinate_unit": "mm_unverified",
        "scale_evidence_class_claimed_physical": False,
        "scans": scans,
    } | overrides
    return body | {"report_sha256": _hash(body)}, revisions


def _metadata(day: int, **overrides) -> StationSessionMetadata:
    values = {
        "layout_revision": "pl0397-v02",
        "turntable_driver_identity": "sim-turntable-r1",
        "lighting_preset": "overhead-5000k",
        "mat_print_record": "mat-a4-v1.0.1-print-01",
        "operator_reference": f"op-{day % 2}",
        "started_at_utc": (datetime(2026, 11, 1, 8, tzinfo=UTC) + timedelta(days=day)).isoformat(),
    } | overrides
    return StationSessionMetadata(**values)


def _session(session_id, metadata, pairs):
    return StationSession(
        session_id,
        metadata,
        {obj: pair[0] for obj, pair in pairs.items()},
        {obj: pair[1] for obj, pair in pairs.items()},
    )


def _sessions(
    *,
    count=6,
    repeats=4,
    repeat_sd=0.02,
    between_sd=0.01,
    seed=401,
    shift=None,
    metadata=None,
    yaw=None,
):
    """Seeded sessions: truth + session effect N(0, between_sd) + repeat noise N(0, repeat_sd).

    ``shift=(day, object, delta)`` adds delta to that session's x extent; ``yaw={day: deg}``
    re-places every scan of that session rotated about the vertical axis.
    """

    rng = random.Random(seed)
    sessions = []
    for day in range(count):
        pairs = {}
        for obj, truth in OBJECTS.items():
            effect = [rng.gauss(0.0, between_sd) for _ in truth]
            if shift and shift[0] == day and shift[1] == obj:
                effect[0] += shift[2]
            extents = [
                tuple(t + e + rng.gauss(0.0, repeat_sd) for t, e in zip(truth, effect, strict=True))
                for _ in range(repeats)
            ]
            pairs[obj] = _object_session(obj, f"s{day}", extents, yaw=(yaw or {}).get(day, 0.0))
        meta = (metadata or {}).get(day, {})
        sessions.append(_session(f"s{day}", _metadata(day, **meta), pairs))
    return sessions


def _evaluate(sessions, **kwargs):
    return evaluate_station_session_repeatability(sessions, policy=POLICY, **kwargs)


def _replace(sessions, day, obj, report=None, revisions=None):
    old = sessions[day]
    reports = dict(old.object_reports) | ({obj: report} if report is not None else {})
    scans = dict(old.object_scans) | ({obj: revisions} if revisions is not None else {})
    sessions[day] = StationSession(old.session_id, old.metadata, reports, scans)
    return sessions


def _rehash(report, **changes):
    body = {k: v for k, v in report.items() if k != "report_sha256"} | changes
    return body | {"report_sha256": _hash(body)}


def _extents_of(sessions, day, obj):
    return [
        tuple(scan["extents"][a] for a in "xyz")
        for scan in sessions[day].object_reports[obj]["scans"]
    ]


def _fail(sessions, reason, **kwargs):
    with pytest.raises(StationRepeatabilityError, match=reason):
        _evaluate(sessions, **kwargs)


def drift_rates(seeds=range(300), counts=(5, 6, 12), shift=0.1, shifted_day=2):
    """Reproduce the doc's in-sample drift figures (slow; not run by the test suite)."""

    rates = {}
    for count in counts:
        false = sum(
            bool(_evaluate(_sessions(seed=s, count=count))["drift_detections"]) for s in seeds
        )
        exact = sum(
            {
                d["session_id"]
                for d in _evaluate(
                    _sessions(seed=s, count=count, shift=(shifted_day, "pp-cap-proxy", shift))
                )["drift_detections"]
            }
            == {f"s{shifted_day}"}
            for s in seeds
        )
        rates[count] = {"false_alarm": false / len(seeds), "exact_detection": exact / len(seeds)}
    return rates


# --- decomposition math -----------------------------------------------------------------


def test_known_answer_balanced_decomposition() -> None:
    stats = _decompose([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    assert stats["ms_within"] == pytest.approx(1.0)
    assert stats["ms_between"] == pytest.approx(27.0)
    assert stats["n0"] == pytest.approx(3.0)
    assert stats["between_session_sd"] == pytest.approx((26.0 / 3.0) ** 0.5)
    assert stats["reproducibility_sd"] == pytest.approx((1.0 + 26.0 / 3.0) ** 0.5)


def test_unbalanced_n0_and_zero_truncation() -> None:
    stats = _decompose([[1.0, 3.0], [1.0, 3.0, 2.0], [2.0, 2.0, 1.0, 3.0]])
    assert stats["n0"] == pytest.approx((9 - 29 / 9) / 2)
    assert stats["between_session_sd"] == 0.0
    assert stats["between_session_variance_truncated_at_zero"] is True


def test_leave_one_out_standard_error_includes_msb_over_n() -> None:
    groups = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]
    shift, standard_error = _leave_one_out_shift(groups, 0)
    # Others: MSW 1, MSB 27, N 9, s_L^2 26/3 -> 26/3 + 1/3 + 27/9 = 12.
    assert shift == pytest.approx(-6.0)
    assert standard_error == pytest.approx(math.sqrt(12.0))


def test_injected_variance_components_are_recovered() -> None:
    report = _evaluate(_sessions(count=60, repeats=6, repeat_sd=0.05, between_sd=0.08))

    for per_axis in report["variance_components"].values():
        for stats in per_axis.values():
            assert stats["repeatability_sd"] == pytest.approx(0.05, rel=0.15)
            assert stats["between_session_sd"] == pytest.approx(0.08, rel=0.3)
            assert stats["reproducibility_sd"] == pytest.approx(
                (0.05**2 + 0.08**2) ** 0.5, rel=0.25
            )
    assert report["drift_detections"] == []
    assert report["configuration_changes"] == []


# --- flags and gates ----------------------------------------------------------------------


def test_stable_station_is_within_provisional_thresholds() -> None:
    report = _evaluate(_sessions())

    assert report["provisional_threshold_result"] == "WITHIN_PROVISIONAL_THRESHOLDS"
    assert all(item["flags"] == [] for item in report["sessions"])
    assert report["simulation_only"] is True
    assert report["physical_validation_status"] == PHYSICAL_EVIDENCE_PENDING
    assert report["physical_repeatability_claim"] is False
    assert report["thresholds"]["status"] == THRESHOLD_STATUS == "PROVISIONAL_PENDING_PL-0221"


def test_injected_drifted_session_is_flagged() -> None:
    report = _evaluate(_sessions(shift=(3, "pp-cap-proxy", 0.4)))

    assert {item["session_id"] for item in report["drift_detections"]} == {"s3"}
    hit = report["drift_detections"][0]
    assert (hit["object_id"], hit["dimension"]) == ("pp-cap-proxy", "extent_x")
    assert hit["shift"] == pytest.approx(0.4, abs=0.1)
    flags = {item["session_id"]: item["flags"] for item in report["sessions"]}
    assert flags["s3"] == ["session_mean_drift"]
    assert report["provisional_threshold_result"] == "EXCEEDS_PROVISIONAL_THRESHOLDS"


def test_noise_free_sessions_handle_zero_standard_error() -> None:
    clean = _evaluate(_sessions(repeat_sd=0.0, between_sd=0.0))
    assert clean["drift_detections"] == []
    assert clean["provisional_threshold_result"] == "WITHIN_PROVISIONAL_THRESHOLDS"

    shifted = _evaluate(_sessions(repeat_sd=0.0, between_sd=0.0, shift=(2, "pp-cap-proxy", 0.2)))
    hits = [d for d in shifted["drift_detections"] if d["session_id"] == "s2"]
    assert len(hits) == 1
    assert hits[0]["standard_error"] == pytest.approx(0.0, abs=1e-9)


def test_layout_revision_change_is_flagged() -> None:
    changed = {day: {"layout_revision": "pl0397-v03"} for day in (4, 5)}
    report = _evaluate(_sessions(metadata=changed))

    assert report["configuration_changes"] == [
        {
            "session_id": "s4",
            "previous_session_id": "s3",
            "field": "layout_revision",
            "previous": "pl0397-v02",
            "current": "pl0397-v03",
        }
    ]
    flags = {item["session_id"]: item["flags"] for item in report["sessions"]}
    assert flags["s4"] == ["station_configuration_change:layout_revision"]
    assert flags["s5"] == []
    assert report["provisional_threshold_result"] == "EXCEEDS_PROVISIONAL_THRESHOLDS"


def test_mat_and_lighting_changes_flagged_operator_change_is_not() -> None:
    report = _evaluate(
        _sessions(metadata={2: {"mat_print_record": "mat-a4-print-02", "lighting_preset": "x"}})
    )
    flags = {item["session_id"]: item["flags"] for item in report["sessions"]}
    assert flags["s2"] == [
        "station_configuration_change:lighting_preset",
        "station_configuration_change:mat_print_record",
    ]
    # Sessions alternate op-0/op-1: operator change alone is reproducibility, not a flag.
    assert flags["s1"] == []


def _gate_split():
    sessions = _sessions(repeat_sd=0.02, between_sd=0.05, seed=7)
    loose = _evaluate(
        sessions, thresholds=StationRepeatabilityThresholds(drift_k_standard_errors=50.0)
    )
    r, big_r = loose["worst_repeatability_sd"], loose["worst_reproducibility_sd"]
    assert loose["drift_detections"] == [] and r < big_r
    return sessions, r, big_r


def test_repeatability_gate_alone_can_fail() -> None:
    sessions, r, big_r = _gate_split()
    gates = StationRepeatabilityThresholds(
        drift_k_standard_errors=50.0,
        maximum_repeatability_sd=r * 0.9,
        maximum_reproducibility_sd=big_r * 2.0,
    )
    assert _evaluate(sessions, thresholds=gates)["provisional_threshold_result"] == (
        "EXCEEDS_PROVISIONAL_THRESHOLDS"
    )
    relaxed = StationRepeatabilityThresholds(
        drift_k_standard_errors=50.0,
        maximum_repeatability_sd=r * 1.1,
        maximum_reproducibility_sd=big_r * 2.0,
    )
    assert _evaluate(sessions, thresholds=relaxed)["provisional_threshold_result"] == (
        "WITHIN_PROVISIONAL_THRESHOLDS"
    )


def test_reproducibility_gate_alone_can_fail() -> None:
    sessions, r, big_r = _gate_split()
    gates = StationRepeatabilityThresholds(
        drift_k_standard_errors=50.0,
        maximum_repeatability_sd=(r + big_r) / 2,
        maximum_reproducibility_sd=(r + big_r) / 2,
    )
    report = _evaluate(sessions, thresholds=gates)
    assert report["worst_repeatability_sd"] <= gates.maximum_repeatability_sd
    assert report["provisional_threshold_result"] == "EXCEEDS_PROVISIONAL_THRESHOLDS"


def test_report_is_digest_bound_and_deterministic_regardless_of_input_order() -> None:
    first = _evaluate(_sessions())
    second = _evaluate(list(reversed(_sessions())))

    assert first == second
    assert report_digest_valid(first)
    assert [item["session_id"] for item in first["sessions"]] == [f"s{i}" for i in range(6)]
    tampered = dict(first) | {"worst_reproducibility_sd": 0.0}
    assert not report_digest_valid(tampered)


# --- P1: re-placed objects are compared in one canonical frame ---------------------------


@pytest.mark.parametrize("degrees", [1.0, 3.0])
def test_small_replacement_yaw_is_not_drift(degrees) -> None:
    report = _evaluate(_sessions(yaw={2: degrees}))

    assert report["drift_detections"] == []
    assert report["provisional_threshold_result"] == "WITHIN_PROVISIONAL_THRESHOLDS"
    alignment = report["sessions"][2]["reference_alignment"]["hdpe-bottle-proxy"]
    assert alignment["canonical_reference"] is False
    assert report["sessions"][0]["reference_alignment"]["hdpe-bottle-proxy"] == {
        "canonical_reference": True
    }


@pytest.mark.parametrize("degrees", [10.0, 90.0])
def test_large_replacement_yaw_is_refused_or_aligned_never_drift(degrees) -> None:
    try:
        report = _evaluate(_sessions(yaw={2: degrees}))
    except StationRepeatabilityError as error:
        assert "cross_session_reference_registration" in str(error) or (
            "object_identity_extent_mismatch" in str(error)
        )
    else:
        assert report["drift_detections"] == []
    # An operator coarse alignment makes the large re-placement comparable again.
    initial = {("s2", obj): _yaw_transform(-degrees + 0.5) for obj in OBJECTS}
    report = _evaluate(_sessions(yaw={2: degrees}), initial_transforms=initial)
    assert report["drift_detections"] == []
    assert report["provisional_threshold_result"] == "WITHIN_PROVISIONAL_THRESHOLDS"


def _real_pl0222_sessions(yaws, *, reference_only=False):
    factors = (
        (1.0, 1.0002, 0.9999),
        (1.0004, 1.0005, 1.0003),
        (0.9998, 0.9997, 1.0),
        (1.0001, 1.0, 1.0002),
        (0.9999, 1.0001, 1.0),
    )
    sessions, expected = [], []
    for day, session_factors in enumerate(factors):
        provenances, revisions = [], []
        for local, factor in enumerate(session_factors):
            global_index = day * 10 + local
            provenance = _provenance(global_index)
            yaw = 0.0 if reference_only and local else yaws.get(day, 0.0)
            points = _yaw(_scan_points(local, scale=factor), yaw)
            provenances.append(provenance)
            revisions.append(_revision(global_index, points, provenance))
        report = evaluate_repeat_scan_reproducibility(
            revisions, {item.provenance_id: item for item in provenances}, policy=POLICY
        )
        sessions.append(
            StationSession(f"s{day}", _metadata(day), {"box": report}, {"box": revisions})
        )
        expected.append([BOX_MM[0] * factor for factor in session_factors])
    return sessions, expected


@pytest.mark.parametrize("degrees", [0.0, 1.0])
def test_end_to_end_with_real_pl0222_reports_and_replaced_reference(degrees) -> None:
    sessions, expected = _real_pl0222_sessions({2: degrees})

    result = _evaluate(sessions)
    stats = result["variance_components"]["box"]["extent_x"]
    truth = _decompose(expected)
    assert stats["repeatability_sd"] == pytest.approx(truth["repeatability_sd"], abs=2e-3)
    assert stats["between_session_sd"] == pytest.approx(truth["between_session_sd"], abs=2e-3)
    assert result["drift_detections"] == []
    assert result["simulation_only"] is True


@pytest.mark.parametrize("degrees", [1.0, 3.0, 10.0])
def test_reviewer_probe_yawed_reference_scan_only(degrees) -> None:
    """V01 review probe: only session s2's PL-0222 reference scan is yawed."""

    sessions, _expected = _real_pl0222_sessions({2: degrees}, reference_only=True)
    try:
        result = _evaluate(sessions)
    except StationRepeatabilityError as error:
        assert degrees >= 10.0
        assert "cross_session_reference_registration_not_accepted" in str(error)
    else:
        assert degrees < 10.0
        assert result["drift_detections"] == []
        assert result["provisional_threshold_result"] == "WITHIN_PROVISIONAL_THRESHOLDS"


# --- fail-closed paths ------------------------------------------------------------------


def test_fail_closed_on_too_few_sessions_or_repeats() -> None:
    _fail(_sessions(count=4), "insufficient_sessions")
    _fail(_sessions(repeats=1), "insufficient_repeats_in_session")
    sessions = _sessions()
    report = sessions[1].object_reports["pp-cap-proxy"]
    scans = [dict(scan) for scan in report["scans"]]
    for scan in scans[1:]:
        scan["used_in_dimension_statistics"] = False  # PL-0222 excluded them (outliers)
    _fail(
        _replace(sessions, 1, "pp-cap-proxy", _rehash(report, scans=scans)), "insufficient_repeats"
    )
    _fail(
        _sessions(count=5),
        "insufficient_sessions",
        thresholds=StationRepeatabilityThresholds(minimum_sessions=6),
    )


def test_fail_closed_on_inconsistent_object_identities() -> None:
    sessions = _sessions()
    old = sessions[2]
    sessions[2] = StationSession(
        "s2",
        old.metadata,
        {k: v for k, v in old.object_reports.items() if k != "pp-cap-proxy"},
        {k: v for k, v in old.object_scans.items() if k != "pp-cap-proxy"},
    )
    _fail(sessions, "object_identities_inconsistent")
    sessions = _sessions()
    old = sessions[2]
    sessions[2] = StationSession("s2", old.metadata, old.object_reports, {})
    _fail(sessions, "object_identities_inconsistent")

    sessions = _sessions()
    _fail(
        _replace(
            sessions,
            2,
            "pp-cap-proxy",
            *_object_session(
                "pp-cap-proxy", "s2", _extents_of(sessions, 2, "pp-cap-proxy"), project="other"
            ),
        ),
        "object_project_identity_inconsistent",
    )

    sessions = _sessions()
    bigger = [tuple(1.06 * v for v in e) for e in _extents_of(sessions, 3, "pp-cap-proxy")]
    _fail(
        _replace(sessions, 3, "pp-cap-proxy", *_object_session("pp-cap-proxy", "s3", bigger)),
        "cross_session_reference_registration_not_accepted",
    )
    sessions = _sessions()
    bigger = [tuple(1.03 * v for v in e) for e in _extents_of(sessions, 3, "pp-cap-proxy")]
    _fail(
        _replace(sessions, 3, "pp-cap-proxy", *_object_session("pp-cap-proxy", "s3", bigger)),
        "object_identity_extent_mismatch",
        thresholds=StationRepeatabilityThresholds(identity_relative_tolerance=0.01),
    )
    _fail([StationSession("s0", _metadata(0), {})] * 5, "session_ids_must_be_unique")
    _fail([StationSession(f"s{d}", _metadata(d), {}) for d in range(5)], "no_reference_objects")


def test_fail_closed_on_unsafe_or_untyped_identifiers() -> None:
    sessions = _sessions()
    old = sessions[1]
    leak = "Jane Doe <jane@example.com>"
    sessions[1] = StationSession(
        "s1",
        old.metadata,
        dict(old.object_reports) | {leak: old.object_reports["pp-cap-proxy"]},
        old.object_scans,
    )
    _fail(sessions, "object_id_invalid")
    sessions = _sessions()
    old = sessions[1]
    sessions[1] = StationSession("s1", old.metadata, dict(old.object_reports) | {5: {}}, {})
    _fail(sessions, "object_id_invalid")
    sessions = _sessions()
    sessions[0] = StationSession(5, sessions[0].metadata, sessions[0].object_reports)  # type: ignore[arg-type]
    _fail(sessions, "session_id_invalid")


def test_fail_closed_when_scans_do_not_match_the_report() -> None:
    sessions = _sessions()
    other = sessions[0].object_scans["pp-cap-proxy"]
    _fail(_replace(sessions, 1, "pp-cap-proxy", revisions=other), "pl0222_scan_revisions_mismatch")

    sessions = _sessions()
    revisions = list(sessions[1].object_scans["pp-cap-proxy"])
    moved = revisions[1]
    revisions[1] = _registration_revision(
        moved.revision_id,
        moved.project_id,
        _box((31.0, 30.0, 18.0)),
        moved.scale_provenance_id,
    )
    _fail(
        _replace(sessions, 1, "pp-cap-proxy", revisions=revisions),
        "pl0222_extents_not_reproducible_from_scans",
    )

    sessions = _sessions()
    report = sessions[1].object_reports["pp-cap-proxy"]
    scans = [dict(scan) for scan in report["scans"]]
    scans[1]["parent_digest"] = "0" * 64
    _fail(
        _replace(sessions, 1, "pp-cap-proxy", _rehash(report, scans=scans)),
        "pl0222_scan_revision_identity_mismatch",
    )
    scans = [dict(scan) for scan in report["scans"]]
    scans[1]["transform_scan_to_reference"] = [1.0]
    _fail(
        _replace(_sessions(), 1, "pp-cap-proxy", _rehash(report, scans=scans)),
        "pl0222_scan_transform_invalid",
    )


def test_fail_closed_on_scale_state_and_provenance_problems() -> None:
    def rebuilt(**overrides):
        sessions = _sessions()
        report = sessions[1].object_reports["pp-cap-proxy"]
        return _replace(sessions, 1, "pp-cap-proxy", _rehash(report, **overrides))

    _fail(rebuilt(scale_state="relative"), "mixed_scale_state")
    _fail(rebuilt(coordinate_unit="mm"), "mixed_coordinate_unit")
    _fail(
        rebuilt(scale_evidence_class_claimed_physical=True),
        "mixed_scale_evidence_class_claimed_physical",
    )
    sessions = _sessions()
    for day in range(len(sessions)):
        for obj in OBJECTS:
            report = sessions[day].object_reports[obj]
            _replace(
                sessions,
                day,
                obj,
                _rehash(report, scale_state="relative", coordinate_unit="reconstruction_units"),
            )
    _fail(sessions, "scale_state_must_be_metric_unverified")

    sessions = _sessions()
    tampered = dict(sessions[0].object_reports["pp-cap-proxy"]) | {"project_id": "x"}
    _fail(_replace(sessions, 0, "pp-cap-proxy", tampered), "pl0222_report_digest_invalid")
    _fail(rebuilt(contract="other.v1"), "contract_unsupported")
    _fail(rebuilt(simulation_only=False), "physical_status")
    _fail(rebuilt(physical_validation_status="PASS"), "physical_status")

    sessions = _sessions()
    _fail(
        _replace(sessions, 1, "pp-cap-proxy", sessions[0].object_reports["pp-cap-proxy"]),
        "pl0222_report_reused",
    )
    for key in ("scale_provenance_id", "revision_id"):
        sessions = _sessions()
        report = sessions[1].object_reports["pp-cap-proxy"]
        scans = [dict(scan) for scan in report["scans"]]
        scans[0][key] = sessions[0].object_reports["pp-cap-proxy"]["scans"][0][key]
        _fail(
            _replace(sessions, 1, "pp-cap-proxy", _rehash(report, scans=scans)),
            "scan_provenance_shared_between_reports",
        )
    sessions = _sessions()
    report = sessions[1].object_reports["pp-cap-proxy"]
    scans = [dict(scan) for scan in report["scans"]]
    scans[0]["extents"] = {"x": -1.0, "y": 1.0, "z": 1.0}
    _fail(
        _replace(sessions, 1, "pp-cap-proxy", _rehash(report, scans=scans)),
        "pl0222_scan_extents_invalid",
    )


def test_fail_closed_on_session_metadata_thresholds_and_arguments() -> None:
    with pytest.raises(StationRepeatabilityError, match="operator_reference_invalid"):
        _metadata(0, operator_reference="Jane Doe <jane@example.com>")
    with pytest.raises(StationRepeatabilityError, match="must_be_utc"):
        _metadata(0, started_at_utc="2026-11-01T08:00:00+03:00")
    with pytest.raises(StationRepeatabilityError, match="must_be_utc"):
        _metadata(0, started_at_utc="2026-11-01T08:00:00")
    with pytest.raises(StationRepeatabilityError, match="started_at_utc_invalid"):
        _metadata(0, started_at_utc="yesterday")
    sessions = _sessions()
    sessions[1] = StationSession(
        "s1", _metadata(0), sessions[1].object_reports, sessions[1].object_scans
    )
    _fail(sessions, "session_timestamps_must_be_unique")
    _fail([object()] * 5, "typed_station_sessions_required")
    _fail(_sessions(), "typed_thresholds_required", thresholds=object())
    with pytest.raises(StationRepeatabilityError, match="registration_policy_required"):
        evaluate_station_session_repeatability(_sessions(), policy=object())  # type: ignore[arg-type]
    for bad in (
        {"minimum_sessions": 2},
        {"minimum_repeats_per_session": 1},
        {"minimum_sessions": True},
        {"drift_k_standard_errors": 0.0},
        {"minimum_drift_shift": -1.0},
        {"maximum_reproducibility_sd": float("nan")},
    ):
        with pytest.raises(StationRepeatabilityError):
            StationRepeatabilityThresholds(**bad)


def test_threshold_status_cannot_be_forged() -> None:
    with pytest.raises(TypeError):
        StationRepeatabilityThresholds(status="ACCEPTED_PL-0221")  # type: ignore[call-arg]
    assert StationRepeatabilityThresholds().status == "PROVISIONAL_PENDING_PL-0221"


# --- V02 review notes -------------------------------------------------------------------


@pytest.mark.parametrize(("delta", "flagged"), [(0.03, False), (0.07, True)])
def test_minimum_drift_shift_floor_alone_decides_noise_free_shift(delta, flagged) -> None:
    report = _evaluate(_sessions(repeat_sd=0.0, between_sd=0.0, shift=(2, "pp-cap-proxy", delta)))
    hits = report["drift_detections"]
    assert [(d["session_id"], d["object_id"], d["dimension"]) for d in hits] == (
        [("s2", "pp-cap-proxy", "extent_x")] if flagged else []
    )
    if flagged:
        assert hits[0]["standard_error"] == pytest.approx(0.0, abs=1e-9)
        assert hits[0]["k_standard_errors"] is None


def test_extra_revisions_beyond_the_report_fail_closed() -> None:
    sessions = _sessions()
    extra = _registration_revision(
        "s1-pp-cap-proxy-scan-extra", "project-pp-cap-proxy", _box((30.0, 30.0, 18.0)), "prov-x"
    )
    revisions = [*sessions[1].object_scans["pp-cap-proxy"], extra]
    _fail(
        _replace(sessions, 1, "pp-cap-proxy", revisions=revisions), "pl0222_scan_revisions_mismatch"
    )


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), "a", None, True])
def test_malformed_transform_values_raise_station_error(bad) -> None:
    sessions = _sessions()
    report = sessions[1].object_reports["pp-cap-proxy"]
    scans = [dict(scan) for scan in report["scans"]]
    scans[1]["transform_scan_to_reference"] = [bad, *_IDENTITY[1:]]
    body = {k: v for k, v in report.items() if k != "report_sha256"} | {"scans": scans}
    with pytest.raises(StationRepeatabilityError, match="pl0222_scan_transform_invalid"):
        _bind_scans(body, sessions[1].object_scans["pp-cap-proxy"])
    # Through the public path the report cannot even be digest-bound (NaN/inf) or is rejected.
    unhashable = body | {"report_sha256": "0" * 64}
    _fail(_replace(sessions, 1, "pp-cap-proxy", unhashable), "pl0222_report_digest_invalid")
    if not (isinstance(bad, float) and not math.isfinite(bad)):
        _fail(
            _replace(_sessions(), 1, "pp-cap-proxy", _rehash(report, scans=scans)),
            "pl0222_scan_transform_invalid",
        )


def test_alignment_provenance_is_recorded() -> None:
    initial = {("s2", obj): _yaw_transform(-9.5) for obj in OBJECTS}
    report = _evaluate(_sessions(yaw={2: 10.0, 3: 2.0}), initial_transforms=initial)
    assert report["registration_adapter"] == "packlab_core.geometry_adapter.Open3DGeometryAdapter"
    seeded = report["sessions"][2]["reference_alignment"]["hdpe-bottle-proxy"]
    assert seeded["initial_transform_supplied"] is True
    assert seeded["initial_transform"] == pytest.approx(list(_yaw_transform(-9.5)))
    assert seeded["rotation_to_canonical_deg"] == pytest.approx(10.0, abs=0.05)
    assert seeded["rotation_beyond_initial_deg"] == pytest.approx(0.5, abs=0.05)
    unseeded = report["sessions"][3]["reference_alignment"]["hdpe-bottle-proxy"]
    assert unseeded["initial_transform_supplied"] is False
    assert unseeded["rotation_to_canonical_deg"] == pytest.approx(2.0, abs=0.05)
    assert unseeded["rotation_beyond_initial_deg"] == pytest.approx(2.0, abs=0.05)


@pytest.mark.parametrize(
    "key", [("nope", "x"), ("s2", "unknown-object"), ("s0", "pp-cap-proxy"), "s2"]
)
def test_unknown_or_unused_initial_transform_keys_are_rejected(key) -> None:
    _fail(
        _sessions(),
        "initial_transform_key_unknown_or_unused",
        initial_transforms={key: _yaw_transform(0.0)},
    )
