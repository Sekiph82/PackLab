"""PL-0224 mould-use eligibility: ELIGIBLE is unreachable while PL-0220 is deferred."""

from __future__ import annotations

from dataclasses import replace
from functools import cache
from pathlib import Path

import pytest
from tests.core.threshold_fixtures import (
    benchmark_fixture,
    design_model,
    owner_acceptance,
    scan_master,
)

from packlab_core import acceptance_thresholds as at
from packlab_core import print_scale_sensitivity as print_scale
from packlab_core.design_model import DesignModelParameter, PackageFamily, ParameterType
from packlab_core.design_model_binding import ParentBindingStatus
from packlab_core.mold_use_eligibility import (
    EXCLUSION_REASONS,
    MeasurementToleranceCheck,
    MoldUseEligibilityError,
    MoldUseEvidence,
    ThresholdAcceptanceInputs,
    evaluate_mold_use_eligibility,
)
from packlab_core.print_scale_sensitivity import (
    PrintedMatRulerMeasurement,
    load_calibration_mat_profile,
    run_print_scale_sensitivity,
)
from packlab_core.reconstruction import ReconstructionBackendId, ScaleState
from packlab_core.repeat_scan_registration import _hash
from packlab_core.repeat_scan_reproducibility import REPORT_CONTRACT as REPEAT_CONTRACT
from packlab_core.visual_material_library import MaterialFamily

A4 = Path(__file__).parents[2] / "assets" / "calibration" / "a4-packlab-calibration-mat.svg"
LIFTED = "OWNER_BENCHMARK_EVIDENCE_ACCEPTED"


def _repeatability(*, simulation_only: bool) -> dict[str, object]:
    """Hand-hashed dict: digests are integrity only, so this also models a forgery."""

    body: dict[str, object] = {
        "contract": REPEAT_CONTRACT,
        "simulation_only": simulation_only,
        "physical_reproducibility_claim": not simulation_only,
        "provisional_threshold_result": "WITHIN_PROVISIONAL_THRESHOLDS",
    }
    return body | {"report_sha256": _hash(body)}


@cache
def _ruler_report() -> dict[str, object]:
    profile = load_calibration_mat_profile(A4)
    ruler = PrintedMatRulerMeasurement(
        "ref:owner-ruler",
        "ref:steel-rule",
        "2026-11-19T00:00:00Z",
        profile.reference_distance_x_mm,
        profile.reference_distance_y_mm,
        profile.marker_side_mm,
    )
    return run_print_scale_sensitivity(profile, owner_ruler_measurement=ruler)


def _threshold_inputs() -> ThresholdAcceptanceInputs:
    """Forged-label 'physical' fixtures; acceptance only succeeds with the gate lifted."""

    record, observations = benchmark_fixture(
        evidence_kind="OWNER_EXECUTED_PHYSICAL", scale_state=ScaleState.METRIC_VERIFIED
    )
    proposal = at.derive_threshold_proposal([record], observations)
    return ThresholdAcceptanceInputs([record], observations, proposal, owner_acceptance(proposal))


def _best_case(**change: object) -> MoldUseEvidence:
    evidence = MoldUseEvidence(
        authority_class="SCAN_MASTER",
        scan_master=scan_master(),
        package_family=PackageFamily.BOTTLE,
        material=MaterialFamily.HDPE,
        reconstruction_backend=ReconstructionBackendId.COLMAP_OPENMVS,
        print_scale_report=_ruler_report(),
        threshold_inputs=_threshold_inputs(),
        measurements=(
            MeasurementToleranceCheck(
                "m1", "matte_bottle", MaterialFamily.HDPE, "overall_height", 0.01
            ),
        ),
        partial_coverage=False,
        object_surface_texture_statuses=("pass", "pass"),
        simulation_only=False,
        repeatability_report=_repeatability(simulation_only=False),
    )
    return replace(evidence, **change)


def _reasons(evidence: MoldUseEvidence) -> list[str]:
    report = evaluate_mold_use_eligibility(evidence)
    assert report["mold_use_authorized"] is False
    reasons = report["reasons"]
    assert isinstance(reasons, list) and set(reasons).issubset(EXCLUSION_REASONS)
    assert (report["status"] == "ELIGIBLE") is (not reasons)
    return reasons


def test_default_evidence_reports_every_applicable_reason() -> None:
    assert _reasons(MoldUseEvidence(authority_class="AI_VISUAL_REFERENCE")) == [
        "physical_validation_deferred",
        "authority_not_allow_listed",
        "visual_reference_authority",
        "not_scan_master_authority",
        "package_family_flexible_tube_or_unknown",
        "material_pet_or_unknown",
        "reconstruction_backend_experimental_or_unknown",
        "scale_not_metric_verified",
        "scale_provenance_missing",
        "printed_mat_ruler_record_missing_or_unverified",
        "thresholds_not_accepted",
        "measurement_tolerance_unavailable",
        "partial_coverage",
        "surface_texture_qa_not_passed",
        "synthetic_or_simulation_data",
        "repeatability_not_established",
    ]


def test_eligible_unreachable_today_even_with_most_favourable_evidence() -> None:
    # Real constants: re-derived acceptance raises, so thresholds are never accepted today.
    reasons = _reasons(_best_case())
    assert reasons == [
        "physical_validation_deferred",
        "thresholds_not_accepted",
        "measurement_tolerance_unavailable",
    ]


def test_forged_accepted_dict_probe_cannot_supply_thresholds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reviewer probe: a hand-built ACCEPTED dict with a TEST_ONLY proposal and 50 mm limits."""

    record, synthetic = benchmark_fixture()
    inner = at.derive_test_only_threshold_proposal([record], synthetic)
    inner = dict(inner, groups=[dict(g, proposed_tolerance_mm=50.0) for g in inner["groups"]])
    inner["proposal_sha256"] = at._digest(
        {k: v for k, v in inner.items() if k != "proposal_sha256"}
    )
    forged = ThresholdAcceptanceInputs([record], synthetic, inner, owner_acceptance(inner))
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    reasons = _reasons(_best_case(threshold_inputs=forged))
    assert "thresholds_not_accepted" in reasons and reasons != []


def test_logic_reaches_eligible_only_with_gate_lifted_and_never_authorizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    assert _reasons(_best_case()) == []


@pytest.mark.parametrize(
    "authority",
    [
        "DESIGN_MODEL_OPERATION_WITH_PREVIEW_PROXY",
        "AI_DIMENSION_FIT_PROPOSAL",
        "DESIGN_MODEL",
        "WHATEVER",
        "PREVIEW_PROXY",
        "",
    ],
)
def test_authority_allow_list_fails_closed(monkeypatch: pytest.MonkeyPatch, authority: str) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    # DESIGN_MODEL without a DesignModelRevision object is not allow-listed either.
    assert "authority_not_allow_listed" in _reasons(_best_case(authority_class=authority))


def test_design_model_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    # DesignModelRevision cannot be METRIC_VERIFIED, so a Design Model stays excluded by scale.
    scan = scan_master(
        scale_state=ScaleState.METRIC_UNVERIFIED, validation_status="DEFERRED_OWNER_VALIDATION"
    )
    model = design_model(scan)
    fitted = _reasons(
        _best_case(
            authority_class="DESIGN_MODEL",
            scan_master=scan,
            design_model=model,
            design_model_parent_binding=ParentBindingStatus.CURRENT,
        )
    )
    assert "authority_not_allow_listed" not in fitted
    assert "design_model_not_fitted_to_scan_master" not in fitted
    assert "scale_not_metric_verified" in fitted
    other_scan = scan_master(scale_state=ScaleState.RELATIVE)
    mismatched = _reasons(
        _best_case(
            authority_class="DESIGN_MODEL",
            scan_master=other_scan,
            design_model=model,
            design_model_parent_binding=ParentBindingStatus.NEWER_SCAN_MASTER_AVAILABLE,
        )
    )
    assert "design_model_not_fitted_to_scan_master" in mismatched
    assert "design_model_parent_binding_not_current" in mismatched
    # Scan Master authority with a Design Model attached is a mismatch, not a pass.
    assert "authority_not_allow_listed" in _reasons(_best_case(design_model=model))
    tube = design_model(scan, PackageFamily.TUBE)
    flexible = _reasons(_best_case(authority_class="DESIGN_MODEL", design_model=tube))
    assert "package_family_flexible_tube_or_unknown" in flexible


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"scan_master": scan_master(authority_class="AI_VISUAL_REFERENCE")}, "not_scan_master"),
        ({"scan_master": scan_master(coverage_gaps=("neck-underside",))}, "partial_coverage"),
        ({"partial_coverage": True}, "partial_coverage"),
        ({"scan_master": scan_master(validation_status="DEFERRED_OWNER_VALIDATION")}, "physical"),
        ({"scan_master": scan_master(scale_state=ScaleState.METRIC_UNVERIFIED)}, "scale_not"),
        ({"package_family": PackageFamily.FLEXIBLE_PACK}, "package_family"),
        ({"package_family": PackageFamily.TUBE}, "package_family"),
        ({"package_family": None}, "package_family"),
        ({"material": MaterialFamily.PET}, "material_pet_or_unknown"),
        ({"material": MaterialFamily.OTHER}, "material_pet_or_unknown"),
        (
            {"reconstruction_backend": ReconstructionBackendId.NEURAL_EXPERIMENTAL},
            "reconstruction_backend",
        ),
        ({"reconstruction_backend": None}, "reconstruction_backend"),
        ({"object_surface_texture_statuses": ("pass", "warning")}, "surface_texture"),
        ({"object_surface_texture_statuses": ("pass", "transparent_surface")}, "surface_texture"),
        ({"object_surface_texture_statuses": ()}, "surface_texture"),
        ({"simulation_only": True}, "synthetic_or_simulation_data"),
        ({"repeatability_report": _repeatability(simulation_only=True)}, "repeatability"),
        ({"repeatability_report": {}}, "repeatability"),
        ({"print_scale_report": None}, "printed_mat_ruler"),
        ({"measurements": ()}, "measurement_tolerance_unavailable"),
        (
            {
                "measurements": (
                    MeasurementToleranceCheck(
                        "m1", "matte_bottle", MaterialFamily.HDPE, "overall_height", None
                    ),
                )
            },
            "measurement_tolerance_unavailable",
        ),
        (
            {
                "measurements": (
                    MeasurementToleranceCheck(
                        "m1", "matte_bottle", MaterialFamily.HDPE, "overall_height", 9.0
                    ),
                )
            },
            "measurement_exceeds_accepted_tolerance",
        ),
    ],
)
def test_each_exclusion_condition_blocks(
    monkeypatch: pytest.MonkeyPatch, change: dict[str, object], reason: str
) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    reasons = _reasons(_best_case(**change))
    assert any(item.startswith(reason) for item in reasons), reasons


def test_tampered_reports_and_tolerance_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    ruler = dict(_ruler_report())
    ruler["spacing_tolerance_mm"] = 99.0  # digest no longer matches
    assert "printed_mat_ruler_record_missing_or_unverified" in _reasons(
        _best_case(print_scale_report=ruler)
    )
    repeat = dict(_repeatability(simulation_only=False), simulation_only=True)
    assert "repeatability_not_established" in _reasons(_best_case(repeatability_report=repeat))
    claim = _repeatability(simulation_only=False)
    body = dict(claim, physical_reproducibility_claim=False)
    body.pop("report_sha256")
    unclaimed = body | {"report_sha256": _hash(body)}
    assert "repeatability_not_established" in _reasons(_best_case(repeatability_report=unclaimed))
    inputs = _threshold_inputs()
    limit = next(
        g["proposed_tolerance_mm"]
        for g in inputs.proposal["groups"]
        if g["category"] == "matte_bottle"
    )
    at_limit = MeasurementToleranceCheck(
        "m1", "matte_bottle", MaterialFamily.HDPE, "overall_height", limit
    )
    assert _reasons(_best_case(threshold_inputs=inputs, measurements=(at_limit,))) == []
    above = replace(at_limit, expanded_uncertainty_mm=limit + 0.001)
    assert _reasons(_best_case(threshold_inputs=inputs, measurements=(above,))) == [
        "measurement_exceeds_accepted_tolerance"
    ]


@pytest.mark.parametrize("value", [-5.0, float("nan"), float("inf"), True])
def test_measurement_check_rejects_invalid_uncertainty(value: float) -> None:
    with pytest.raises(MoldUseEligibilityError, match="expanded_uncertainty_invalid"):
        MeasurementToleranceCheck(
            "m1", "matte_bottle", MaterialFamily.HDPE, "overall_height", value
        )


def test_measurement_check_rejects_unknown_category_material_and_kind() -> None:
    with pytest.raises(MoldUseEligibilityError, match="category"):
        MeasurementToleranceCheck("m1", "pouch", MaterialFamily.HDPE, "overall_height", 0.1)
    with pytest.raises(MoldUseEligibilityError, match="material"):
        MeasurementToleranceCheck("m1", "jerrycan", "HDPE", "overall_height", 0.1)
    with pytest.raises(MoldUseEligibilityError, match="dimension_kind"):
        MeasurementToleranceCheck("m1", "jerrycan", MaterialFamily.HDPE, "volume", 0.1)


def test_measurement_material_and_category_bound_to_subject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reviewer V02 probes: a PET or jerrycan measurement cannot ride on an HDPE bottle."""

    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    pet = MeasurementToleranceCheck(
        "m1", "glossy_bottle", MaterialFamily.PET, "overall_height", 0.01
    )
    assert "measurement_subject_mismatch" in _reasons(_best_case(measurements=(pet,)))
    jerrycan = MeasurementToleranceCheck(
        "m1", "jerrycan", MaterialFamily.HDPE, "overall_height", 0.01
    )
    assert "measurement_subject_mismatch" in _reasons(_best_case(measurements=(jerrycan,)))
    # The same jerrycan measurement is consistent with a jerrycan subject.
    assert (
        _reasons(_best_case(package_family=PackageFamily.JERRYCAN, measurements=(jerrycan,))) == []
    )


@pytest.mark.parametrize("status", [None, "DEFERRED_OWNER_VALIDATION", "VALIDATED", ""])
def test_scan_master_validation_status_allow_list(
    monkeypatch: pytest.MonkeyPatch, status: str | None
) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    reasons = _reasons(_best_case(scan_master=scan_master(validation_status=status)))
    assert reasons == ["physical_validation_deferred"]


def test_generated_scan_master_excluded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    for value in (True, "yes"):
        scan = scan_master(extra={"generated": value})
        assert _reasons(_best_case(scan_master=scan)) == ["generated_asset"]


def test_bottle_with_pouch_parameters_is_flexible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    scan = scan_master(
        scale_state=ScaleState.METRIC_UNVERIFIED, validation_status="DEFERRED_OWNER_VALIDATION"
    )
    pouch = DesignModelParameter("pouch_gusset_depth", 10.0, ParameterType.NUMBER, "mm_unverified")
    plain = design_model(scan, PackageFamily.BOTTLE)
    flexible = design_model(scan, PackageFamily.BOTTLE, (pouch,))
    evidence = {
        "authority_class": "DESIGN_MODEL",
        "scan_master": scan,
        "design_model_parent_binding": ParentBindingStatus.CURRENT,
    }
    assert "package_family_flexible_tube_or_unknown" not in _reasons(
        _best_case(design_model=plain, **evidence)
    )
    assert "package_family_flexible_tube_or_unknown" in _reasons(
        _best_case(design_model=flexible, **evidence)
    )


def test_design_model_scale_and_provenance_must_agree_with_scan_master(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    parent = scan_master(
        scale_state=ScaleState.METRIC_UNVERIFIED, validation_status="DEFERRED_OWNER_VALIDATION"
    )
    model = design_model(parent)
    common = {
        "authority_class": "DESIGN_MODEL",
        "design_model": model,
        "design_model_parent_binding": ParentBindingStatus.CURRENT,
    }
    # Same revision id but a METRIC_VERIFIED manifest: only the model's own scale blocks.
    verified = scan_master(
        revision_id=parent.revision_id,
        scale_provenance_id=str(parent.manifest["scale_provenance_id"]),
    )
    agreed = _reasons(_best_case(scan_master=verified, **common))
    assert "scale_not_metric_verified" in agreed
    assert "scale_provenance_missing" not in agreed
    other = scan_master(
        revision_id=parent.revision_id, scale_provenance_id="scale-provenance:other"
    )
    assert "scale_provenance_missing" in _reasons(_best_case(scan_master=other, **common))


def _rehash_ruler(report: dict[str, object]) -> dict[str, object]:
    body = {key: value for key, value in report.items() if key != "report_sha256"}
    return body | {"report_sha256": print_scale._digest(body)}


def test_ruler_report_requires_contract_and_record_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    reason = "printed_mat_ruler_record_missing_or_unverified"
    wrong_contract = _rehash_ruler(dict(_ruler_report(), contract="packlab.other.v1"))
    assert _reasons(_best_case(print_scale_report=wrong_contract)) == [reason]
    check = dict(_ruler_report()["owner_ruler_check"])  # type: ignore[call-overload]
    check.pop("record_reference")
    no_reference = _rehash_ruler(dict(_ruler_report(), owner_ruler_check=check))
    assert _reasons(_best_case(print_scale_report=no_reference)) == [reason]


def test_repeatability_report_requires_digest_and_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    bad_digest = dict(_repeatability(simulation_only=False), report_sha256="0" * 64)
    assert _reasons(_best_case(repeatability_report=bad_digest)) == [
        "repeatability_not_established"
    ]
    body = dict(_repeatability(simulation_only=False), contract="packlab.other.v1")
    body.pop("report_sha256")
    wrong_contract = body | {"report_sha256": _hash(body)}
    assert _reasons(_best_case(repeatability_report=wrong_contract)) == [
        "repeatability_not_established"
    ]


def test_inner_proposal_status_checked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unreachable via the real accept_threshold_proposal (it always emits a PROPOSED inner
    proposal); exercised by substituting the function to prove the defensive check."""

    monkeypatch.setattr(at, "PL0220_PHYSICAL_BENCHMARK_STATUS", LIFTED)
    real = at.accept_threshold_proposal

    def tampered(*args: object) -> dict[str, object]:
        accepted = real(*args)
        return dict(accepted, proposal=dict(accepted["proposal"], status=at.TEST_ONLY))

    monkeypatch.setattr(at, "accept_threshold_proposal", tampered)
    reasons = _reasons(_best_case())
    assert "thresholds_not_accepted" in reasons
