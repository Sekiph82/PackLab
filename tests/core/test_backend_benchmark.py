from __future__ import annotations

import json
import random
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from packlab_core import backend_benchmark as bb
from packlab_core.physical_accuracy_benchmark import (
    BenchmarkEnvironment,
    CaliperGroundTruth,
    PhysicalAccuracyBenchmarkRecord,
    PhysicalBenchmarkSample,
    serialize_physical_benchmark_record,
)
from packlab_core.reconstruction import BackendProvenance, ReconstructionBackendId, ScaleState

NO_CHANGE = bb.BenchmarkDecision.NO_CHANGE_INSUFFICIENT_PHYSICAL_EVIDENCE.value
RULE_NOT_MET = bb.BenchmarkDecision.NO_CHANGE_RULE_NOT_MET.value
RECOMMEND = bb.BenchmarkDecision.RECOMMEND_DEFAULT_CHANGE_PENDING_ADR.value
# Golden digest of the default synthetic proxy report; change only with a reviewed reason.
GOLDEN_PROXY_REPORT_DIGEST = (
    "sha256:09a830b1673541ae80aca36dbc5361bd36a323ae39c8c585ed356655c3a5bb84"
)
LICENSE = "ref-license"
Cases = list[bb.BenchmarkCase]
Runs = list[bb.BackendRunRecord]


def _attested(backend_id: ReconstructionBackendId) -> BackendProvenance:
    digest = "ab" * 32 if backend_id is bb.BASELINE_BACKEND else "cd" * 32
    return BackendProvenance(
        backend_id, "attested-1.0", f"build-{backend_id.value}", "lic", {"bin": digest}
    )


def _relabel_as_physical(
    cases: Cases,
    runs: Runs,
    *,
    sample_override: Callable[[bb.BenchmarkCase], dict[str, object]] | None = None,
    record_status: str = "READY_FOR_AUDIT",
    sample_id: Callable[[bb.BenchmarkCase], str] | None = None,
    scan_of: Callable[[bb.BenchmarkCase], str] | None = None,
) -> tuple[Cases, Runs, PhysicalAccuracyBenchmarkRecord]:
    """TEST-ONLY RELABEL. Renames proxy cases, swaps in attested-looking backend
    identities and invents a caliper record, purely to exercise the binding and
    decision logic. It shows exactly why the physical binding is owner-attested
    and must be checked by an independent reviewer against real evidence; the
    values remain invented and are never physical evidence.
    """
    renamed = {c.case_id: c.case_id.replace("SYN-", "OBJ-") for c in cases}
    base_cases = [
        replace(
            c,
            case_id=renamed[c.case_id],
            capture_set_id=f"capture-{renamed[c.case_id].lower()}",
            ground_truth_record_id=f"gt-{renamed[c.case_id].lower()}",
        )
        for c in cases
    ]
    sample_of = sample_id or (lambda c: f"SAMPLE-{c.case_id}")
    samples: dict[str, PhysicalBenchmarkSample] = {}
    for case in base_cases:
        sid = sample_of(case)
        if sid in samples:
            continue
        height = case.ground_truth_dimensions_mm["height"]
        fields: dict[str, object] = {
            "category": case.package_class,
            "disposition": "ACCEPTED",
            "ground_truth_id": case.ground_truth_record_id,
            "disposition_reason": None,
        }
        fields.update(sample_override(case) if sample_override else {})
        samples[sid] = PhysicalBenchmarkSample(
            sid, fields["category"], fields["disposition"], scan_of(case) if scan_of else f"scan-{sid}",  # type: ignore[arg-type]
            "scan-rev-1", f"meas-{sid}", "meas-rev-1", "ref:evidence",
            CaliperGroundTruth(
                fields["ground_truth_id"], "height", height, (height,), 0.02,  # type: ignore[arg-type]
                "ref:caliper", "ref:cal", "ref:owner", "2026-11-19T00:00:00Z",
            ),
            fields["disposition_reason"],  # type: ignore[arg-type]
        )  # fmt: skip
    record = PhysicalAccuracyBenchmarkRecord(
        "BENCH-TEST", record_status, "ref:operator", "2026-11-19T00:00:00Z",
        BenchmarkEnvironment(21.0, 50.0, "diffuse", "grey mat", "turntable", "phone", "main"),
        tuple(samples.values()),
    )  # fmt: skip
    bound = [
        replace(
            c,
            ground_truth_authority=bb.GroundTruthAuthority.PHYSICAL_CALIPER,
            physical_record_digest=record.record_digest,
            physical_sample_id=sample_of(c),
        )
        for c in base_cases
    ]
    new_runs = [
        replace(r, case_id=renamed[r.case_id], backend=_attested(r.backend.backend_id))
        for r in runs
    ]
    return bound, new_runs, record


def _better(**kwargs: object) -> tuple[Cases, Runs]:
    """Proxy where the candidate is clearly better on every deciding metric."""
    options: dict[str, object] = {
        "cases_per_class": 10,
        "candidate_noise_mm": 0.05,
        "candidate_quality_gain": 0.05,
    }
    options.update(kwargs)
    return bb.synthetic_proxy_inputs(**options)  # type: ignore[arg-type]


def _evaluate(cases: Cases, runs: Runs, record: object, **kw: object) -> dict[str, object]:
    kw.setdefault("license_clearance_ref", LICENSE)
    return bb.evaluate_backend_benchmark(cases, runs, physical_record=record, **kw)  # type: ignore[arg-type]


def _reasons(report: dict[str, object], key: str) -> list[str]:
    return list(report[key])  # type: ignore[call-overload]


def test_default_proxy_is_deterministic_and_matches_golden_digest() -> None:
    first = bb.evaluate_backend_benchmark(*bb.synthetic_proxy_inputs())
    second = bb.evaluate_backend_benchmark(*bb.synthetic_proxy_inputs())
    assert first == second
    assert first["report_digest"] == GOLDEN_PROXY_REPORT_DIGEST
    assert first["decision"] == NO_CHANGE
    assert first["production_default_backend"] == "colmap-openmvs"
    assert first["production_default_changed"] is False
    assert first["physical_evidence_status"] == "PHYSICAL_EVIDENCE_PENDING"
    assert first["rule"]["margin_dimension_mae_mm"] == 0.0  # type: ignore[index]


def test_report_is_independent_of_input_order() -> None:
    cases, runs = bb.synthetic_proxy_inputs()
    shuffled = list(runs)
    random.Random(1).shuffle(shuffled)
    assert (
        bb.evaluate_backend_benchmark(cases[::-1], shuffled)["report_digest"]
        == bb.evaluate_backend_benchmark(cases, runs)["report_digest"]
    )


def test_report_includes_descriptive_runtime_resource_and_failure_fields() -> None:
    cases, runs = bb.synthetic_proxy_inputs(candidate_fail_case="SYN-JERRYCAN-00")
    runs = [replace(r, peak_host_ram_bytes=1000, point_count=5, triangle_count=7) for r in runs]
    report = bb.evaluate_backend_benchmark(cases, runs)
    jerrycan = next(c for c in report["cases"] if c["case"]["case_id"] == "SYN-JERRYCAN-00")  # type: ignore[attr-defined]
    described = jerrycan["baseline"]["descriptive"]
    assert described["runtime_seconds_mean"] > 0
    assert described["peak_host_ram_bytes_max"] == 1000
    assert described["point_count_mean"] == 5
    assert described["triangle_count_mean"] == 7
    assert jerrycan["candidate"]["failure_diagnostics"] == ["injected synthetic failure"] * 2


def test_synthetic_inputs_can_only_produce_no_change_even_when_rule_passes() -> None:
    cases, runs = _better()
    report = bb.evaluate_backend_benchmark(cases, runs, license_clearance_ref=LICENSE)
    assert report["rule_outcome"] == "PASS"
    assert report["decision"] == NO_CHANGE
    for seed in range(10):
        cases, runs = _better(seed=seed, candidate_bias_mm=random.Random(seed).uniform(-1.0, 0.0))
        for authority in (
            bb.GroundTruthAuthority.SYNTHETIC_GENERATOR,
            bb.GroundTruthAuthority.PUBLIC_PROXY,
        ):
            relabelled = [replace(c, ground_truth_authority=authority) for c in cases]
            out = bb.evaluate_backend_benchmark(relabelled, runs, license_clearance_ref=LICENSE)
            assert out["decision"] == NO_CHANGE
            assert out["production_default_changed"] is False


def test_synthetic_authority_gate_blocks_even_with_a_valid_record() -> None:
    bound, runs, record = _relabel_as_physical(*_better())
    labelled = [
        replace(bound[0], ground_truth_authority=bb.GroundTruthAuthority.SYNTHETIC_GENERATOR),
        *bound[1:],
    ]
    report = _evaluate(labelled, runs, record)
    assert f"{bound[0].case_id}:ground_truth_not_physical:SYNTHETIC_GENERATOR" in _reasons(
        report, "evidence_reasons"
    )
    assert report["decision"] == NO_CHANGE


def test_proxy_relabel_through_public_inputs_cannot_recommend() -> None:
    """Reviewer P2-2: only relabelling authority + inventing a record must not RECOMMEND."""
    cases, runs = _better()
    bound, _, record = _relabel_as_physical(cases, runs)
    # Keep the SYN- identifiers and the proxy identities, as a CLI relabel would.
    syn_bound = [
        replace(b, case_id=c.case_id, capture_set_id=c.capture_set_id)
        for b, c in zip(bound, cases, strict=True)
    ]
    report = _evaluate(syn_bound, runs, record)
    assert report["decision"] != RECOMMEND
    assert any(
        "synthetic_identifier_on_physical_path" in r for r in _reasons(report, "evidence_reasons")
    )
    # Renamed IDs but proxy backend identities: blocked by the identity guard.
    bound, renamed_runs, record = _relabel_as_physical(cases, runs)
    proxy_runs = [
        replace(r, backend=bb.synthetic_proxy_provenance(r.backend.backend_id))
        for r in renamed_runs
    ]
    report = _evaluate(bound, proxy_runs, record)
    assert report["decision"] == RULE_NOT_MET
    assert "candidate_identity_is_synthetic_proxy" in _reasons(report, "precondition_reasons")
    assert "baseline_identity_is_synthetic_proxy" in _reasons(report, "precondition_reasons")


def test_relabelled_physical_path_recommends_only_pending_adr() -> None:
    bound, runs, record = _relabel_as_physical(*_better())
    report = _evaluate(bound, runs, record)
    assert report["evidence_reasons"] == []
    assert report["decision"] == RECOMMEND
    assert report["production_default_changed"] is False
    assert bb.PRODUCTION_DEFAULT_BACKEND is ReconstructionBackendId.COLMAP_OPENMVS
    assert "explicit ADR" in report["required_before_any_default_change"]  # type: ignore[operator]
    no_license = _evaluate(bound, runs, record, license_clearance_ref=None)
    assert no_license["decision"] == RULE_NOT_MET


def test_equal_quality_candidate_does_not_pass_equal_or_better_rule() -> None:
    bound, runs, record = _relabel_as_physical(*bb.synthetic_proxy_inputs(cases_per_class=10))
    report = _evaluate(bound, runs, record)
    assert report["decision"] == RULE_NOT_MET
    # Kills "upper bound replaced by mean": some metric has mean <= 0 but upper bound > 0.
    borderline = [
        m
        for cls in report["classes"].values()  # type: ignore[attr-defined]
        for m in cls["metrics"].values()
        if "upper_95" in m and m["mean"] <= m["margin"] < m["upper_95"]
    ]
    assert borderline and all(m["outcome"] == "FAIL" for m in borderline)


def test_missing_candidate_deciding_metric_blocks_recommend() -> None:
    """Reviewer P1-1 probe: candidate 5 mm RMS worse but omits it in one case per class."""
    cases, runs = _better()
    omitted = {f"SYN-{c.upper()}-00" for c in bb.PACKAGE_CLASSES}
    probed = [
        replace(
            r,
            surface_deviation_rms_mm=None
            if r.case_id in omitted
            else (r.surface_deviation_rms_mm or 0.0) + 5.0,
        )
        if r.backend.backend_id is bb.CANDIDATE_BACKEND
        else r
        for r in runs
    ]
    bound, probed_runs, record = _relabel_as_physical(cases, probed)
    report = _evaluate(bound, probed_runs, record)
    assert report["decision"] != RECOMMEND
    for cls in bb.PACKAGE_CLASSES:
        assert f"{cls}:surface_deviation_rms_mm_not_measured" in _reasons(report, "rule_reasons")


@pytest.mark.parametrize(
    ("kwargs", "reason_fragment"),
    [
        ({"candidate_bias_mm": 2.0}, "dimension_mae_mm_equal_or_better_not_shown"),
        ({"candidate_noise_mm": 1.5}, "repeatability_spread_mm_equal_or_better_not_shown"),
        ({"candidate_fail_case": "SYN-JERRYCAN-03"}, "OBJ-JERRYCAN-03:candidate_run_failed"),
    ],
)
def test_injected_candidate_errors_fail_the_rule(
    kwargs: dict[str, object], reason_fragment: str
) -> None:
    bound, runs, record = _relabel_as_physical(*_better(**kwargs))
    report = _evaluate(bound, runs, record)
    assert report["rule_outcome"] == "FAIL"
    assert any(reason_fragment in r for r in _reasons(report, "rule_reasons"))
    assert report["decision"] == RULE_NOT_MET


def test_candidate_band_failure_adds_rule_reason() -> None:
    bound, runs, record = _relabel_as_physical(*_better())
    target = bound[0].case_id
    runs = [
        replace(r, surface_coverage_ratio=0.5)
        if r.case_id == target and r.backend.backend_id is bb.CANDIDATE_BACKEND
        else r
        for r in runs
    ]
    report = _evaluate(bound, runs, record)
    assert f"{target}:candidate_quality_band_failed" in _reasons(report, "rule_reasons")
    assert report["decision"] == RULE_NOT_MET


def test_baseline_failure_or_band_failure_is_not_comparable() -> None:
    bound, runs, record = _relabel_as_physical(*_better())
    target = bound[0].case_id
    is_base = lambda r: r.case_id == target and r.backend.backend_id is bb.BASELINE_BACKEND  # noqa: E731
    failed = [
        replace(
            r, status=bb.RunStatus.FAILED, measured_dimensions_mm={}, failure_diagnostic="crash"
        )
        if is_base(r) and r.repeat_index == 0
        else r
        for r in runs
    ]
    report = _evaluate(bound, failed, record)
    assert f"{target}:baseline_failed_case_not_comparable" in _reasons(report, "evidence_reasons")
    assert report["classes"][bound[0].package_class]["independent_objects"] == 9  # type: ignore[index]
    degenerate = [replace(r, surface_coverage_ratio=0.1) if is_base(r) else r for r in runs]
    report = _evaluate(bound, degenerate, record)
    assert f"{target}:baseline_quality_band_failed" in _reasons(report, "evidence_reasons")


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        (
            {"disposition": "REJECTED", "disposition_reason": "damaged"},
            "physical_sample_not_accepted",
        ),
        ({"category": "jerrycan"}, "physical_sample_class_mismatch"),
        ({"ground_truth_id": "gt-other"}, "physical_ground_truth_id_mismatch"),
    ],
)
def test_each_physical_binding_gate_fails_closed(override: dict[str, object], reason: str) -> None:
    cases, runs = _better()
    first = cases[0].case_id.replace("SYN-", "OBJ-")  # a matte_bottle case
    bound, runs, record = _relabel_as_physical(
        cases, runs, sample_override=lambda c: override if c.case_id == first else {}
    )
    report = _evaluate(bound, runs, record)
    assert f"{first}:{reason}" in _reasons(report, "evidence_reasons")
    assert report["decision"] == NO_CHANGE


def test_record_status_and_digest_gates_fail_closed() -> None:
    bound, runs, record = _relabel_as_physical(*_better(), record_status="OWNER_REQUIRED")
    report = _evaluate(bound, runs, record)
    assert f"{bound[0].case_id}:physical_record_not_ready_for_audit" in _reasons(
        report, "evidence_reasons"
    )
    bound, runs, record = _relabel_as_physical(*_better())
    wrong = [replace(bound[0], physical_record_digest="sha256:" + "0" * 64), *bound[1:]]
    report = _evaluate(wrong, runs, record)
    assert _reasons(report, "evidence_reasons") == [
        f"{bound[0].case_id}:physical_record_digest_mismatch"
    ]
    assert _evaluate(bound, runs, None)["decision"] == NO_CHANGE
    wrong_value = [
        replace(
            bound[0],
            ground_truth_dimensions_mm={**bound[0].ground_truth_dimensions_mm, "height": 1.0},
        ),
        *bound[1:],
    ]
    assert f"{bound[0].case_id}:physical_caliper_value_mismatch" in _reasons(
        _evaluate(wrong_value, runs, record), "evidence_reasons"
    )


def test_repeated_objects_are_aggregated_not_counted_as_independent() -> None:
    """Reviewer P2-1 probe: 30 cases bound to 3 physical samples cannot reach the minimum."""
    cases, runs = _better()
    bound, runs, record = _relabel_as_physical(
        cases, runs, sample_id=lambda c: f"SAMPLE-ONE-{c.package_class.upper()}"
    )
    report = _evaluate(bound, runs, record)
    for cls in bb.PACKAGE_CLASSES:
        assert report["classes"][cls]["independent_objects"] == 1  # type: ignore[index]
        assert f"{cls}:independent_objects_below_minimum" in _reasons(report, "evidence_reasons")
    assert report["decision"] == NO_CHANGE
    shared = [replace(c, capture_set_id="same-capture") for c in bound]
    with pytest.raises(bb.BackendBenchmarkError, match="duplicate_capture_set_id"):
        _evaluate(shared, runs, record)


def test_too_few_repeats_or_objects_fail_closed() -> None:
    bound, runs, record = _relabel_as_physical(*_better(cases_per_class=3))
    assert (
        _evaluate(bound, [r for r in runs if r.repeat_index == 0], record)["decision"] == NO_CHANGE
    )
    keep = [c for c in bound if not c.case_id.endswith("-02") or c.package_class != "jerrycan"]
    kept_ids = {c.case_id for c in keep}
    report = _evaluate(keep, [r for r in runs if r.case_id in kept_ids], record)
    assert "jerrycan:independent_objects_below_minimum" in _reasons(report, "evidence_reasons")


def test_samples_sharing_a_scan_count_as_one_physical_object() -> None:
    """Reviewer V02 R2-1 probe: one bottle recorded as several ACCEPTED samples."""
    cases, runs = _better(cases_per_class=9)
    bound, runs, record = _relabel_as_physical(
        cases, runs, scan_of=lambda c: f"scan-object-{c.package_class}"
    )
    report = _evaluate(bound, runs, record)
    for cls in bb.PACKAGE_CLASSES:
        assert report["classes"][cls]["independent_objects"] == 1  # type: ignore[index]
        assert f"{cls}:independent_objects_below_minimum" in _reasons(report, "evidence_reasons")
    assert report["decision"] == NO_CHANGE


def test_statistics_use_one_value_per_object_not_per_case() -> None:
    """Kills a mutant that flattens cases instead of averaging per object."""
    cases, runs = _better(cases_per_class=9)
    bound, runs, record = _relabel_as_physical(
        cases, runs, scan_of=lambda c: f"scan-{c.case_id.lower()[:-1]}{int(c.case_id[-1]) % 3}"
    )
    report = _evaluate(bound, runs, record)
    for cls in bb.PACKAGE_CLASSES:
        summary = report["classes"][cls]  # type: ignore[index]
        assert summary["comparable_cases"] == 9
        assert summary["independent_objects"] == 3
        assert all(m["n"] == 3 for m in summary["metrics"].values())
        deltas: dict[str, list[float]] = {}
        for item in report["cases"]:  # type: ignore[attr-defined]
            if item["case"]["package_class"] == cls:
                key = item["physical_object_key"]
                deltas.setdefault(key, []).append(
                    item["candidate_minus_baseline"]["dimension_mae_mm"]
                )
        per_object = [sum(v) / len(v) for v in deltas.values()]
        assert summary["metrics"]["dimension_mae_mm"]["mean"] == pytest.approx(sum(per_object) / 3)


def test_decision_rule_minimums_must_be_integers() -> None:
    for bad in (2.5, True, 1, 0):
        with pytest.raises(bb.BackendBenchmarkError):
            bb.DecisionRule(min_cases_per_class=bad)  # type: ignore[arg-type]
        with pytest.raises(bb.BackendBenchmarkError):
            bb.DecisionRule(min_repeats_per_backend=bad)  # type: ignore[arg-type]
    with pytest.raises(bb.BackendBenchmarkError):
        bb.DecisionRule(margin_dimension_mae_mm=True)


def test_cli_rejects_oversized_input_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    big = tmp_path / "in.json"
    big.write_text(json.dumps({"contract": bb.INPUT_CONTRACT, "pad": "x" * 64}), encoding="utf-8")
    monkeypatch.setattr(bb, "MAX_INPUT_BYTES", 32)
    with pytest.raises(bb.BackendBenchmarkError, match="input_file_too_large"):
        bb.main(["--input", str(big)])


def test_upper_bound_statistic_matches_hand_computation() -> None:
    stat = bb._upper_bound([0.1, 0.2, 0.3])
    assert stat is not None
    assert stat["mean"] == pytest.approx(0.2)
    assert stat["sd"] == pytest.approx(0.1)
    assert stat["upper_95"] == pytest.approx(0.2 + 2.920 * 0.1 / 3**0.5)
    assert bb._upper_bound([0.1]) is None


def test_unpinned_candidate_identity_blocks_recommendation() -> None:
    bound, runs, record = _relabel_as_physical(*_better())
    unpinned = BackendProvenance(
        ReconstructionBackendId.NEURAL_EXPERIMENTAL, "vggt-adapter-contract-v1",
        "checkpoint-unconfigured", "activation-gate-incomplete", {},
    )  # fmt: skip
    swapped = [
        replace(r, backend=unpinned) if r.backend.backend_id is bb.CANDIDATE_BACKEND else r
        for r in runs
    ]
    report = _evaluate(bound, swapped, record)
    assert "candidate_identity_not_pinned" in _reasons(report, "precondition_reasons")
    assert report["decision"] == RULE_NOT_MET


def test_malformed_and_authority_violating_inputs_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    cases, runs = bb.synthetic_proxy_inputs()
    err = bb.BackendBenchmarkError
    with pytest.raises(err, match="metric_verified"):
        replace(runs[0], scale_state=ScaleState.METRIC_VERIFIED)
    with pytest.raises(err, match="duplicate_run"):
        bb.evaluate_backend_benchmark(cases, [*runs, runs[0]])
    with pytest.raises(err, match="single_pinned_build"):
        other = BackendProvenance(
            ReconstructionBackendId.COLMAP_OPENMVS, "x", "y", "z", {"a": "0" * 64}
        )
        bb.evaluate_backend_benchmark(cases, [replace(runs[0], backend=other), *runs[1:]])
    with pytest.raises(err, match="one_scale_procedure"):
        bb.evaluate_backend_benchmark(
            cases, [replace(runs[0], scale_procedure_id="other"), *runs[1:]]
        )
    with pytest.raises(err, match="missing_ground_truth_dimension"):
        bb.evaluate_backend_benchmark(
            cases, [replace(runs[0], measured_dimensions_mm={"height": 1.0}), *runs[1:]]
        )
    with pytest.raises(err, match="requires_diagnostic"):
        replace(runs[0], status=bb.RunStatus.FAILED)
    with pytest.raises(err, match="dimension_value_invalid"):
        replace(
            cases[0],
            ground_truth_dimensions_mm={
                **cases[0].ground_truth_dimensions_mm,
                "height": float("nan"),
            },
        )
    with pytest.raises(err, match="dimension_value_invalid"):
        replace(
            cases[0],
            ground_truth_dimensions_mm={**cases[0].ground_truth_dimensions_mm, "height": 10**400},
        )
    with pytest.raises(err, match="operator_interventions_invalid"):
        replace(runs[0], operator_interventions=None)  # type: ignore[arg-type]
    with pytest.raises(err, match="point_count_invalid"):
        replace(runs[0], point_count=10**400)
    monkeypatch.setattr(bb, "MAX_CASES", 1)
    with pytest.raises(err, match="too_large"):
        bb.evaluate_backend_benchmark(cases, runs)


def _payload(bound: Cases, runs: Runs) -> dict[str, object]:
    aliases = {bb.BASELINE_BACKEND: "baseline", bb.CANDIDATE_BACKEND: "candidate"}
    backends = {aliases[r.backend.backend_id]: bb.backend_identity(r.backend) for r in runs}
    payload = {
        "contract": bb.INPUT_CONTRACT,
        "license_clearance_ref": LICENSE,
        "backends": backends,
        "cases": [c.as_dict() for c in bound],
        "runs": [
            {
                **{
                    k: v
                    for k, v in r.as_dict().items()
                    if k not in {"backend_identity_digest", "backend_id"}
                },
                "backend": aliases[r.backend.backend_id],
            }
            for r in runs
        ],
    }
    return json.loads(json.dumps(payload))


def test_json_input_and_physical_record_round_trip_and_cli(tmp_path: Path) -> None:
    bound, runs, record = _relabel_as_physical(*_better())
    payload = _payload(bound, runs)
    loaded_cases, loaded_runs, clearance = bb.load_benchmark_input(payload)
    serialized = json.loads(serialize_physical_benchmark_record(record))
    loaded_record = bb.load_physical_record(serialized)
    direct = _evaluate(bound, runs, record)
    via_json = _evaluate(loaded_cases, loaded_runs, loaded_record, license_clearance_ref=clearance)
    assert via_json["report_digest"] == direct["report_digest"]
    (tmp_path / "in.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "rec.json").write_text(json.dumps(serialized), encoding="utf-8")
    out = tmp_path / "report.json"
    argv = ["--input", str(tmp_path / "in.json"), "--physical-record", str(tmp_path / "rec.json")]
    assert bb.main([*argv, "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["report_digest"] == direct["report_digest"]


def test_loaders_fail_closed() -> None:
    bound, runs, record = _relabel_as_physical(*_better(cases_per_class=3))
    payload = _payload(bound, runs)
    serialized = json.loads(serialize_physical_benchmark_record(record))
    err = bb.BackendBenchmarkError
    tampered = json.loads(json.dumps(serialized))
    tampered["samples"][0]["ground_truth"]["value_mm"] = 1.0
    with pytest.raises(err, match="digest_mismatch"):
        bb.load_physical_record(tampered)
    with pytest.raises(err, match="content_mismatch"):
        bb.load_physical_record({**serialized, "extra_unbound_field": 1})
    with pytest.raises(err, match="physical_record_malformed"):
        bb.load_physical_record({**serialized, "record_id": "not a valid id"})
    with pytest.raises(err, match="must_be_json_object"):
        bb.load_physical_record([])  # type: ignore[arg-type]
    with pytest.raises(err, match="must_be_json_object"):
        bb.load_benchmark_input([])  # type: ignore[arg-type]
    with pytest.raises(err, match="contract_unsupported"):
        bb.load_benchmark_input({**payload, "contract": "other"})
    with pytest.raises(err, match="input_malformed"):
        bb.load_benchmark_input({**payload, "runs": [{"case_id": "x"}]})
