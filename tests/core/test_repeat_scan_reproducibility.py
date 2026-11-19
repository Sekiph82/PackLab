"""PL-0222 repeat-scan reproducibility: synthetic ground truth checks the software math only."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics

import pytest

from packlab_core.calibration import (
    AssociatedMarkerObservation,
    PhysicalMarkerReference,
    ReconstructedMarkerGeometry,
    ReconstructionScaleObservation,
    estimate_reconstruction_scale,
)
from packlab_core.calibration.scale_provenance import ScaleProvenance, create_scale_provenance
from packlab_core.geometry_adapter import PointCloudData
from packlab_core.reconstruction import ScaleState
from packlab_core.repeat_scan_registration import RegistrationPolicy, RegistrationRevision
from packlab_core.repeat_scan_reproducibility import (
    ReproducibilityError,
    ReproducibilityThresholds,
    _surface_statistics,
    evaluate_repeat_scan_reproducibility,
    report_digest_valid,
)

PROJECT = "7c881a57-48c5-4c77-81ac-c79a27a8e469"
BOX_MM = (100.0, 60.0, 40.0)  # synthetic ground-truth extents, not a physical object


def _box_surface(spacing: float = 10.0) -> tuple[tuple[float, float, float], ...]:
    half = [value / 2.0 for value in BOX_MM]
    steps = [round(value / spacing) for value in BOX_MM]
    grid = [[-half[a] + i * spacing for i in range(steps[a] + 1)] for a in range(3)]
    points = {
        (x, y, z)
        for x in grid[0]
        for y in grid[1]
        for z in grid[2]
        if abs(x) == half[0] or abs(y) == half[1] or abs(z) == half[2]
    }
    return tuple(sorted(points))


GROUND_TRUTH = _box_surface()


def _pose(points, *, angle_deg: float, axis=(0.3, 0.5, 0.8), offset=(1.5, -1.0, 0.8)):
    norm = math.sqrt(sum(value * value for value in axis))
    ux, uy, uz = (value / norm for value in axis)
    c, s = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    rotation = (
        (c + ux * ux * (1 - c), ux * uy * (1 - c) - uz * s, ux * uz * (1 - c) + uy * s),
        (uy * ux * (1 - c) + uz * s, c + uy * uy * (1 - c), uy * uz * (1 - c) - ux * s),
        (uz * ux * (1 - c) - uy * s, uz * uy * (1 - c) + ux * s, c + uz * uz * (1 - c)),
    )
    return tuple(
        tuple(sum(rotation[r][k] * point[k] for k in range(3)) + offset[r] for r in range(3))
        for point in points
    )


def _scan_points(index: int, *, scale=1.0, noise=0.0, keep=lambda point: True, seed=7):
    rng = random.Random(seed * 1000 + index)
    points = [
        tuple(scale * value + rng.gauss(0.0, noise) for value in point)
        for point in GROUND_TRUTH
        if keep(point)
    ]
    if index == 0:
        return tuple(points)
    return _pose(points, angle_deg=1.5 * index, offset=(0.6 * index, -0.4 * index, 0.3))


def _provenance(
    index: int, evidence_class: str = "synthetic_test_fixture", markers=(0, 1, 2, 3)
) -> ScaleProvenance:
    reconstruction, camera = f"reconstruction-scan-{index}", f"camera-scan-{index}"
    samples = []
    for marker_id in markers:
        source = f"synthetic/scan-{index}/marker-{marker_id}.png"
        association = AssociatedMarkerObservation(
            marker_id,
            ((0.0, 0.0), (320.0, 0.0), (320.0, 320.0), (0.0, 320.0)),
            {"quality_label": "synthetic_geometry", "quality_score": 1.0},
            {"generator": "synthetic_test_fixture_v1"},
            source,
            hashlib.sha256(source.encode()).hexdigest(),
            4032,
            3024,
            f"camera-{marker_id}",
            camera,
        )
        reference = PhysicalMarkerReference(
            marker_id,
            f"synthetic-marker-{marker_id}",
            hashlib.sha256(f"marker-{marker_id}".encode()).hexdigest(),
            40.0,
            "mm",
            0.1,
            evidence_class,
        )
        geometry = ReconstructedMarkerGeometry(
            association,
            reconstruction,
            "reconstruction_units",
            ((0.0, 0.0, 0.0), (100.0, 0.0, 0.0), (100.0, 100.0, 0.0), (0.0, 100.0, 0.0)),
            0.05,
        )
        samples.append(ReconstructionScaleObservation(reference, geometry))
    observations = tuple(samples)
    estimate = estimate_reconstruction_scale(
        observations, reconstruction_revision=reconstruction, camera_solution_revision=camera
    )
    return create_scale_provenance(
        estimate,
        observations,
        reconstruction_revision=reconstruction,
        camera_solution_revision=camera,
        created_at_utc="2026-11-12T10:00:00Z",
        actor_id="synthetic-fixture",
        process_id="pl0222-test",
    )


def _revision(index: int, points, provenance: ScaleProvenance, *, state=None):
    cloud = PointCloudData(tuple(points))
    state = state or provenance.scale_state
    digest = hashlib.sha256(
        json.dumps(
            {"points": cloud.points, "colors": None, "normals": None},
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    return RegistrationRevision(
        f"scan-{index}",
        PROJECT,
        hashlib.sha256(f"parent-{index}-{digest}".encode()).hexdigest(),
        cloud,
        digest,
        "OBJECT_CAPTURE_GEOMETRY",
        False,
        f"frame-scan-{index}",
        "mm_unverified" if state is ScaleState.METRIC_UNVERIFIED else "reconstruction_units",
        state,
        provenance.provenance_id,
        "DEFERRED_OWNER_VALIDATION",
        False,
    )


POLICY = RegistrationPolicy(
    maximum_correspondence_distance=4.0,
    maximum_iterations=100,
    minimum_inlier_count=6,
    minimum_fitness=0.8,
    maximum_inlier_rmse=1.0,
)


def _run(scan_points, **kwargs):
    provenances = [_provenance(index) for index in range(len(scan_points))]
    revisions = [
        _revision(index, points, provenances[index]) for index, points in enumerate(scan_points)
    ]
    return evaluate_repeat_scan_reproducibility(
        revisions,
        {item.provenance_id: item for item in provenances},
        policy=POLICY,
        **kwargs,
    )


def _scan(report, revision_id):
    return next(item for item in report["scans"] if item["revision_id"] == revision_id)


def test_rigid_pose_changes_recover_ground_truth_with_zero_spread() -> None:
    report = _run([_scan_points(index) for index in range(4)])

    for axis, truth in zip(("x", "y", "z"), BOX_MM, strict=True):
        stats = report["dimension_statistics"][f"extent_{axis}"]
        assert stats["count"] == 4
        assert stats["mean"] == pytest.approx(truth, abs=1e-4)
        assert stats["std"] == pytest.approx(0.0, abs=1e-4)
    assert report["surface_deviation_statistics"]["rms"] == pytest.approx(0.0, abs=1e-4)
    assert all(not item["flags"] for item in report["scans"])
    assert report["provisional_threshold_result"] == "WITHIN_PROVISIONAL_THRESHOLDS"


def test_injected_per_scan_scale_spread_is_recovered_by_dimension_statistics() -> None:
    factors = (0.999, 0.9995, 1.0, 1.0005, 1.001)
    report = _run([_scan_points(i, scale=f) for i, f in enumerate(factors)])

    for axis, truth in zip(("x", "y", "z"), BOX_MM, strict=True):
        stats = report["dimension_statistics"][f"extent_{axis}"]
        expected_std = truth * statistics.stdev(factors)
        assert stats["mean"] == pytest.approx(truth * statistics.fmean(factors), abs=1e-4)
        assert stats["std"] == pytest.approx(expected_std, rel=1e-3)
        assert stats["max_abs_deviation"] == pytest.approx(truth * 0.001, rel=1e-3)
        deviations = [truth * (f - 1.0) for f in factors]
        assert stats["rms_deviation"] == pytest.approx(
            math.sqrt(statistics.fmean(d * d for d in deviations)), rel=1e-3
        )
        assert stats["repeatability_coefficient_95"] == pytest.approx(
            1.96 * math.sqrt(2.0) * expected_std, rel=1e-3
        )
    for index, factor in enumerate(factors):
        deviation = _scan(report, f"scan-{index}")["relative_scale_deviation"]
        assert deviation == pytest.approx(factor - 1.0, abs=2e-5)


def test_seeded_noise_is_recovered_from_surface_residuals() -> None:
    sigma = 0.05
    report = _run([_scan_points(index, noise=sigma) for index in range(5)])

    surface = report["surface_deviation_statistics"]
    # Same sample index on both scans: residual vector ~ N(0, 2 sigma^2 I3), RMS = sigma*sqrt(6).
    assert surface["rms"] / math.sqrt(6.0) == pytest.approx(sigma, rel=0.1)
    assert surface["max"] >= surface["p95_distance"] >= surface["mean"]
    for axis in ("x", "y", "z"):
        assert report["dimension_statistics"][f"extent_{axis}"]["std"] < 3 * sigma


def test_one_percent_scale_outlier_is_flagged_and_excluded() -> None:
    scans = [_scan_points(index, noise=0.02) for index in range(4)]
    scans.append(_scan_points(4, scale=1.01, noise=0.02))
    report = _run(scans)

    outlier = _scan(report, "scan-4")
    assert outlier["flags"] == ["scale_outlier"]
    assert outlier["relative_scale_deviation"] == pytest.approx(0.01, abs=1e-3)
    assert outlier["used_in_dimension_statistics"] is False
    assert outlier["used_in_surface_statistics"] is False
    assert report["dimension_statistics"]["extent_x"]["count"] == 4
    assert report["dimension_statistics"]["extent_x"]["std"] < 0.1
    # Surface pool = the three non-reference, non-outlier scans only.
    assert report["surface_deviation_statistics"]["count"] == 3 * len(GROUND_TRUTH)
    assert all(not _scan(report, f"scan-{i}")["flags"] for i in range(4))


def test_partial_coverage_is_flagged_and_kept_out_of_dimension_statistics() -> None:
    scans = [_scan_points(index) for index in range(4)]
    scans.append(_scan_points(4, keep=lambda point: point[2] <= 10.0))
    report = _run(scans)

    partial = _scan(report, "scan-4")
    assert partial["flags"] == ["partial_coverage"]
    assert partial["coverage_ratio"] < 0.95
    assert partial["used_in_dimension_statistics"] is False
    assert partial["used_in_surface_statistics"] is True
    assert partial["relative_scale_deviation"] is None
    assert report["dimension_statistics"]["extent_z"]["mean"] == pytest.approx(40.0, abs=1e-4)


def test_report_is_versioned_digest_bound_simulation_only_and_deterministic() -> None:
    scans = [_scan_points(index, noise=0.02) for index in range(3)]
    first, second = _run(scans), _run(scans)

    assert first == second
    body = {key: value for key, value in first.items() if key != "report_sha256"}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert first["report_sha256"] == hashlib.sha256(encoded.encode("ascii")).hexdigest()
    assert report_digest_valid(first)
    assert not report_digest_valid(dict(first, simulation_only=False))
    assert first["scale_evidence_class_claimed_physical"] is False
    assert first["contract"] == "packlab.repeat-scan-reproducibility-report.v1"
    assert first["simulation_only"] is True
    assert first["physical_validation_status"] == "PHYSICAL_EVIDENCE_PENDING"
    assert first["physical_reproducibility_claim"] is False
    assert first["mold_use_authorized"] is False
    assert first["thresholds"]["status"] == "PROVISIONAL_PENDING_PL-0221"
    assert first["coordinate_unit"] == "mm_unverified"
    changed = _run([*scans[:2], _scan_points(2, noise=0.03)])
    assert changed["report_sha256"] != first["report_sha256"]


def test_owner_physical_label_is_only_a_caller_claim_and_never_clears_simulation() -> None:
    # Synthetic data labelled "accepted_owner_physical": the label is caller-asserted.
    provenances = [_provenance(i, "accepted_owner_physical") for i in range(3)]
    revisions = [_revision(i, _scan_points(i), provenances[i]) for i in range(3)]
    report = evaluate_repeat_scan_reproducibility(
        revisions, {item.provenance_id: item for item in provenances}, policy=POLICY
    )
    assert report["scale_evidence_class_claimed_physical"] is True
    assert report["scale_evidence_class_basis"] == "caller_asserted_label_not_owner_record_bound"
    assert report["simulation_only"] is True
    assert report["physical_validation_status"] == "PHYSICAL_EVIDENCE_PENDING"
    assert report["physical_reproducibility_claim"] is False


def test_scale_state_and_provenance_failures_fail_closed() -> None:
    provenances = [_provenance(index) for index in range(3)]
    revisions = [_revision(i, _scan_points(i), provenances[i]) for i in range(3)]
    mapping = {item.provenance_id: item for item in provenances}

    with pytest.raises(ReproducibilityError, match="scale_provenance_missing"):
        evaluate_repeat_scan_reproducibility(
            revisions, {k: v for k, v in list(mapping.items())[1:]}, policy=POLICY
        )
    with pytest.raises(ReproducibilityError, match="scale_provenance_identity_mismatch"):
        swapped = dict(mapping)
        swapped[provenances[0].provenance_id] = provenances[1]
        evaluate_repeat_scan_reproducibility(revisions, swapped, policy=POLICY)

    relative = _revision(2, _scan_points(2), provenances[2], state=ScaleState.RELATIVE)
    with pytest.raises(ReproducibilityError, match="scale_state_mismatch"):
        evaluate_repeat_scan_reproducibility([*revisions[:2], relative], mapping, policy=POLICY)
    rejected = _provenance(2, markers=(0,))  # one marker: estimate rejected, state RELATIVE
    assert rejected.scale_state is ScaleState.RELATIVE
    stale = _revision(2, _scan_points(2), rejected, state=ScaleState.METRIC_UNVERIFIED)
    with pytest.raises(ReproducibilityError, match="scale_provenance_state_mismatch"):
        evaluate_repeat_scan_reproducibility(
            [*revisions[:2], stale], mapping | {rejected.provenance_id: rejected}, policy=POLICY
        )
    all_relative = [
        _revision(i, _scan_points(i), provenances[i], state=ScaleState.RELATIVE) for i in range(3)
    ]
    with pytest.raises(ReproducibilityError, match="relative_scale_reproducibility_forbidden"):
        evaluate_repeat_scan_reproducibility(all_relative, mapping, policy=POLICY)
    with pytest.raises(ReproducibilityError, match="insufficient_repeat_scan_revisions"):
        evaluate_repeat_scan_reproducibility(revisions[:2], mapping, policy=POLICY)
    with pytest.raises(ReproducibilityError, match="reference_revision_not_found"):
        evaluate_repeat_scan_reproducibility(
            revisions, mapping, policy=POLICY, reference_revision_id="scan-missing"
        )
    with pytest.raises(ReproducibilityError, match="minimum_revisions_must_be_at_least_three"):
        ReproducibilityThresholds(minimum_revisions=2)


def test_unaccepted_registration_is_excluded_and_thresholds_are_configurable() -> None:
    strict = RegistrationPolicy(
        maximum_correspondence_distance=4.0, minimum_fitness=0.8, maximum_inlier_rmse=1e-3
    )
    provenances = [_provenance(index) for index in range(4)]
    points = [_scan_points(index) for index in range(3)] + [_scan_points(3, noise=0.05)]
    revisions = [_revision(i, points[i], provenances[i]) for i in range(4)]
    mapping = {item.provenance_id: item for item in provenances}

    report = evaluate_repeat_scan_reproducibility(revisions, mapping, policy=strict)
    noisy = _scan(report, "scan-3")
    assert noisy["convergence_status"] == "NON_CONVERGED_RESIDUAL_LIMIT"
    assert noisy["flags"] == ["registration_not_accepted"]
    assert noisy["used_in_dimension_statistics"] is False
    assert noisy["used_in_surface_statistics"] is False
    assert report["dimension_statistics"]["extent_x"]["count"] == 3

    tight = ReproducibilityThresholds(maximum_surface_deviation_p95=0.01)
    exceeded = _run([_scan_points(index, noise=0.05) for index in range(3)], thresholds=tight)
    assert exceeded["provisional_threshold_result"] == "EXCEEDS_PROVISIONAL_THRESHOLDS"
    assert exceeded["thresholds"]["maximum_surface_deviation_p95"] == 0.01


def test_dimension_rc_alone_can_exceed_thresholds() -> None:
    factors = (0.999, 0.9995, 1.0, 1.0005, 1.001)
    scans = [_scan_points(i, scale=f) for i, f in enumerate(factors)]
    tight = ReproducibilityThresholds(maximum_dimension_repeatability_coefficient=0.1)
    report = _run(scans, thresholds=tight)
    # extent_x RC95 = 2.77 * 0.079 = 0.22 > 0.1, while the surface p95 passes its 0.5 gate.
    assert report["dimension_statistics"]["extent_x"]["repeatability_coefficient_95"] > 0.1
    assert report["surface_deviation_statistics"]["p95_distance"] < 0.5
    assert report["provisional_threshold_result"] == "EXCEEDS_PROVISIONAL_THRESHOLDS"
    assert _run(scans)["provisional_threshold_result"] == "WITHIN_PROVISIONAL_THRESHOLDS"


def test_surface_p95_is_nearest_rank() -> None:
    stats = _surface_statistics([float(value) for value in range(100, 0, -1)])
    assert stats is not None
    assert stats["p95_distance"] == 95.0
    assert stats["max"] == 100.0
    assert _surface_statistics([1.0]) is None


def test_structural_input_guards_fail_closed() -> None:
    provenances = [_provenance(index) for index in range(3)]
    mapping = {item.provenance_id: item for item in provenances}
    revisions = [_revision(i, _scan_points(i), provenances[i]) for i in range(3)]

    with pytest.raises(ReproducibilityError, match="revision_ids_must_be_unique"):
        evaluate_repeat_scan_reproducibility([*revisions[:2], revisions[0]], mapping, policy=POLICY)
    shared = [_revision(i, _scan_points(i), provenances[0]) for i in range(3)]
    with pytest.raises(ReproducibilityError, match="scale_provenance_shared_between_scans"):
        evaluate_repeat_scan_reproducibility(shared, mapping, policy=POLICY)
    narrow_gate = RegistrationPolicy(maximum_correspondence_distance=0.5)
    with pytest.raises(ReproducibilityError, match="correspondence_gate_must_exceed"):
        evaluate_repeat_scan_reproducibility(revisions, mapping, policy=narrow_gate)
    face = [(x, y, 0.0) for x, y, z in GROUND_TRUTH if z == -20.0]  # zero z extent
    planar = [_revision(i, face, provenances[i]) for i in range(3)]
    with pytest.raises(ReproducibilityError, match="degenerate_zero_extent"):
        evaluate_repeat_scan_reproducibility(planar, mapping, policy=POLICY)
