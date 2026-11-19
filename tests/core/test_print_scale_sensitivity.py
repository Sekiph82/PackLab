"""PL-0223 print-scale sensitivity: synthetic ground truth checks the software math only."""

from __future__ import annotations

from pathlib import Path

import pytest

from packlab_core.print_scale_sensitivity import (
    PrintedMatRulerMeasurement,
    PrintScaleScenario,
    PrintScaleSensitivityError,
    SimulationSettings,
    check_printed_mat_spacing,
    default_print_scale_scenarios,
    fit_to_page_scale,
    load_calibration_mat_profile,
    report_digest_valid,
    run_print_scale_sensitivity,
)

ROOT = Path(__file__).resolve().parents[2]
A4 = ROOT / "assets" / "calibration" / "a4-packlab-calibration-mat.svg"
A3 = ROOT / "assets" / "calibration" / "a3-packlab-calibration-mat.svg"
NOISE_FREE = SimulationSettings(reconstruction_corner_noise_units=0.0, corner_noise_px=0.0)


def _scenario(report, scenario_id):
    return next(item for item in report["scenarios"] if item["scenario_id"] == scenario_id)


@pytest.mark.parametrize(("path", "spacing"), ((A4, (150.0, 207.0)), (A3, (237.0, 330.0))))
def test_profile_reads_nominal_spacing_from_versioned_svg(path, spacing) -> None:
    profile = load_calibration_mat_profile(path)
    assert profile.marker_side_mm == 40.0
    assert profile.source_version == "1.0.1"
    assert (profile.reference_distance_x_mm, profile.reference_distance_y_mm) == spacing
    pairs = profile.spacing_pairs()
    assert sorted(axis for axis, *_ in pairs) == ["x", "x", "y", "y"]
    assert {nominal for axis, _a, _b, nominal in pairs if axis == "x"} == {spacing[0]}


def test_noise_free_scale_error_matches_analytic_bias_through_both_estimators() -> None:
    profile = load_calibration_mat_profile(A4)
    report = run_print_scale_sensitivity(profile, settings=NOISE_FREE)

    for result in report["scenarios"]:
        sx, sy = result["print_scale_x"], result["print_scale_y"]
        analytic = 2.0 / (sx + sy) - 1.0
        assert result["reconstruction_estimator_status"] == "estimated"
        assert result["metric_state"] == "METRIC_UNVERIFIED"
        assert result["analytic_relative_scale_error"] == pytest.approx(analytic, abs=1e-15)
        assert result["relative_scale_error"] == pytest.approx(analytic, abs=1e-12)
        assert result["image_estimator_relative_scale_error"] == pytest.approx(analytic, abs=1e-12)
        for dimension in result["object_dimension_propagation"]:
            assert dimension["error_mm"] == pytest.approx(dimension["true_mm"] * analytic)
    assert _scenario(report, "nominal_100pct")["relative_scale_error"] == pytest.approx(0.0)
    two_percent = _scenario(report, "anisotropic_x_plus_2.0pct")
    height = next(
        item
        for item in two_percent["object_dimension_propagation"]
        if item["dimension_id"] == "synthetic_bottle_height"
    )
    assert height["error_mm"] == pytest.approx(120.0 * (2.0 / 2.02 - 1.0))


def test_seeded_noise_stays_close_to_analytic_bias_and_is_reproducible() -> None:
    profile = load_calibration_mat_profile(A4)
    first = run_print_scale_sensitivity(profile)
    assert first == run_print_scale_sensitivity(profile)
    other_seed = run_print_scale_sensitivity(profile, settings=SimulationSettings(seed=1))
    assert other_seed["report_sha256"] != first["report_sha256"]
    for result in first["scenarios"]:
        assert result["relative_scale_error"] == pytest.approx(
            result["analytic_relative_scale_error"],
            abs=3 * result["estimator_relative_uncertainty"],
        )


def test_uniform_fit_to_page_error_is_invisible_to_images_but_caught_by_ruler() -> None:
    profile = load_calibration_mat_profile(A4)
    report = run_print_scale_sensitivity(profile)
    fit = _scenario(report, "fit_to_page_same_media_5mm_margin")

    assert fit["print_scale_x"] == pytest.approx(fit_to_page_scale(profile, 210, 297, 5.0))
    assert fit["print_scale_x"] == pytest.approx(200.0 / 210.0)
    assert fit["relative_scale_error"] == pytest.approx(0.05, abs=1e-3)
    # The estimator accepts the biased scale and its own uncertainty does not cover the bias.
    assert fit["metric_scale_usable"] is True
    assert fit["bias_within_estimator_2sigma"] is False
    assert fit["detected_by_image_spacing"] is False
    assert fit["detected_by_simulated_ruler"] is True
    letter = _scenario(report, "fit_to_page_us_letter_5mm_margin")
    assert letter["print_scale_x"] == pytest.approx(min(205.9 / 210.0, 269.4 / 297.0))


def test_spacing_flags_follow_configured_tolerance_exactly() -> None:
    profile = load_calibration_mat_profile(A4)
    tolerance = 1.0
    report = run_print_scale_sensitivity(
        profile, settings=NOISE_FREE, spacing_tolerance_mm=tolerance
    )
    for result in report["scenarios"]:
        sx, sy = result["print_scale_x"], result["print_scale_y"]
        mean = (sx + sy) / 2.0
        for check in result["spacing_checks"]:
            scale = sx if check["axis"] == "x" else sy
            nominal = check["nominal_mm"]
            assert check["simulated_ruler_flagged"] is (abs(nominal * (scale - 1)) > tolerance)
            assert check["image_derived_mm"] == pytest.approx(nominal * scale / mean)
            assert check["image_derived_flagged"] is (abs(nominal * (scale / mean - 1)) > tolerance)
    assert not _scenario(report, "nominal_100pct")["detected_by_simulated_ruler"]
    # 0.5 % along x moves the 150 mm spacing by only 0.75 mm: inside the provisional gate.
    assert not _scenario(report, "anisotropic_x_plus_0.5pct")["detected_by_simulated_ruler"]
    assert _scenario(report, "anisotropic_y_plus_0.5pct")["detected_by_simulated_ruler"]
    assert report["ruler_gate_max_undetected_relative_scale_error"] == {
        "x": pytest.approx(1.0 / 150.0),
        "y": pytest.approx(1.0 / 207.0),
    }
    looser = run_print_scale_sensitivity(profile, settings=NOISE_FREE, spacing_tolerance_mm=5.0)
    assert not _scenario(looser, "anisotropic_y_plus_2.0pct")["detected_by_simulated_ruler"]


def test_report_is_simulation_only_digest_bound_and_requires_owner_ruler_input() -> None:
    profile = load_calibration_mat_profile(A4)
    report = run_print_scale_sensitivity(profile)

    assert report["contract"] == "packlab.print-scale-sensitivity-report.v1"
    assert report["simulation_only"] is True
    assert report["physical_validation_status"] == "PHYSICAL_EVIDENCE_PENDING"
    assert report["physical_claim_allowed"] is False
    assert report["owner_ruler_check"]["status"] == "OWNER_RULER_MEASUREMENT_REQUIRED"
    assert "owner_ruler_measurement_of_printed_mat_required" in report["physical_claim_blockers"]
    assert report["mat_profile"]["geometry_class"] == "nominal_svg_source_not_physical"
    assert report_digest_valid(report)
    tampered = dict(report, simulation_only=False)
    assert not report_digest_valid(tampered)


def test_owner_ruler_measurement_gate_accepts_and_rejects_but_never_allows_physical_claim() -> None:
    profile = load_calibration_mat_profile(A4)
    good = PrintedMatRulerMeasurement(
        "ref:mat-record-1", "ref:ruler-1", "2026-11-12T10:00:00Z", 150.4, 206.7, 40.1
    )
    report = run_print_scale_sensitivity(profile, owner_ruler_measurement=good)
    assert report["owner_ruler_check"]["status"] == "WITHIN_PROVISIONAL_PRINT_TOLERANCE"
    assert report["physical_claim_allowed"] is False
    assert report["physical_validation_status"] == "PHYSICAL_EVIDENCE_PENDING"
    assert (
        "owner_ruler_measurement_of_printed_mat_required" not in report["physical_claim_blockers"]
    )

    shrunk = check_printed_mat_spacing(
        profile, spacing_x_mm=142.9, spacing_y_mm=197.1, marker_side_mm=38.1
    )
    assert shrunk["status"] == "REJECTED_SCALING"
    assert shrunk["failed_readings"] == ["marker_side", "spacing_x", "spacing_y"]
    partial = check_printed_mat_spacing(
        profile, spacing_x_mm=150.0, spacing_y_mm=None, marker_side_mm=40.0
    )
    assert partial["status"] == "OWNER_RULER_MEASUREMENT_REQUIRED"


def test_invalid_inputs_fail_closed() -> None:
    profile = load_calibration_mat_profile(A4)
    with pytest.raises(PrintScaleSensitivityError, match="print_scale_out_of_simulated_range"):
        PrintScaleScenario("bad", 2.0, 1.0, "bad")
    with pytest.raises(PrintScaleSensitivityError, match="ruler_spacing_x_mm_invalid"):
        PrintedMatRulerMeasurement("ref:r", "ref:i", "2026-11-12T10:00:00Z", float("nan"), 1, 1)
    duplicate = default_print_scale_scenarios(profile)[:1] * 2
    with pytest.raises(PrintScaleSensitivityError, match="unique"):
        run_print_scale_sensitivity(profile, scenarios=duplicate)
    with pytest.raises(PrintScaleSensitivityError, match="spacing_tolerance_invalid"):
        run_print_scale_sensitivity(profile, spacing_tolerance_mm=0.0)
    with pytest.raises(PrintScaleSensitivityError, match="mat_svg_metadata_invalid"):
        load_calibration_mat_profile(ROOT / "pyproject.toml")


def test_image_spacing_detects_anisotropy_and_tolerance_boundary_is_exclusive() -> None:
    profile = load_calibration_mat_profile(A4)
    report = run_print_scale_sensitivity(profile, settings=NOISE_FREE)
    assert _scenario(report, "anisotropic_x_plus_2.0pct")["detected_by_image_spacing"] is True
    assert _scenario(report, "nominal_100pct")["detected_by_image_spacing"] is False

    exact = (PrintScaleScenario("exact_quarter", 1.25, 1.0, "exact float boundary"),)
    at_boundary = run_print_scale_sensitivity(
        profile, scenarios=exact, settings=NOISE_FREE, spacing_tolerance_mm=37.5
    )
    assert at_boundary["scenarios"][0]["detected_by_simulated_ruler"] is False
    inside = run_print_scale_sensitivity(
        profile, scenarios=exact, settings=NOISE_FREE, spacing_tolerance_mm=37.4
    )
    assert inside["scenarios"][0]["detected_by_simulated_ruler"] is True
    edge = check_printed_mat_spacing(
        profile, spacing_x_mm=151.0, spacing_y_mm=207.0, marker_side_mm=40.5
    )
    assert edge["status"] == "WITHIN_PROVISIONAL_PRINT_TOLERANCE"


def test_rejected_owner_reading_keeps_blocker_and_uses_configured_tolerance() -> None:
    profile = load_calibration_mat_profile(A4)
    reading = PrintedMatRulerMeasurement(
        "ref:mat-record-2", "ref:ruler-1", "2026-11-12T10:00:00Z", 151.5, 207.0, 40.0
    )
    rejected = run_print_scale_sensitivity(profile, owner_ruler_measurement=reading)
    assert rejected["owner_ruler_check"]["status"] == "REJECTED_SCALING"
    assert rejected["owner_ruler_check"]["failed_readings"] == ["spacing_x"]
    assert "owner_ruler_measurement_of_printed_mat_required" in rejected["physical_claim_blockers"]
    assert rejected["physical_claim_allowed"] is False

    loose = run_print_scale_sensitivity(
        profile, owner_ruler_measurement=reading, spacing_tolerance_mm=2.0
    )
    assert loose["owner_ruler_check"]["status"] == "WITHIN_PROVISIONAL_PRINT_TOLERANCE"
    assert loose["owner_ruler_check"]["tolerances_mm"]["spacing_x"] == 2.0


@pytest.mark.parametrize(
    "kwargs",
    (
        {"spacing_x_mm": float("nan")},
        {"spacing_y_mm": -207.0},
        {"marker_side_mm": True},
        {"spacing_tolerance_mm": float("nan")},
        {"spacing_tolerance_mm": -1.0},
        {"marker_side_tolerance_mm": float("nan")},
        {"marker_side_tolerance_mm": 0.0},
    ),
)
def test_public_ruler_gate_rejects_non_finite_or_non_positive_inputs(kwargs) -> None:
    profile = load_calibration_mat_profile(A4)
    values = {"spacing_x_mm": 150.0, "spacing_y_mm": 207.0, "marker_side_mm": 40.0} | kwargs
    with pytest.raises(PrintScaleSensitivityError, match="_invalid"):
        check_printed_mat_spacing(profile, **values)


@pytest.mark.parametrize(
    ("old", "new", "error"),
    (
        ('x="160" y="20"', 'x="161" y="20"', "mat_svg_reference_distance_mismatch"),
        (
            'width="40" height="40" fill="white"/>',
            'width="39" height="40" fill="white"/>',
            "mat_svg_marker_geometry_mismatch",
        ),
        (
            '<g id="marker-3"',
            '<g transform="scale(0.5)" id="marker-3"',
            "mat_svg_marker_geometry_mismatch",
        ),
        ('data-marker-id="3"', 'data-not-a-marker="3"', "mat_svg_requires_four_markers"),
    ),
)
def test_svg_loader_fails_closed_instead_of_dropping_markers(tmp_path, old, new, error) -> None:
    text = A4.read_text(encoding="utf-8")
    assert old in text
    broken = tmp_path / "broken-mat.svg"
    broken.write_text(text.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(PrintScaleSensitivityError, match=error):
        load_calibration_mat_profile(broken)


def test_scenario_rejects_bool_scale() -> None:
    with pytest.raises(PrintScaleSensitivityError, match="print_scale_invalid"):
        PrintScaleScenario("bool", True, 1.0, "bool is not a scale")
