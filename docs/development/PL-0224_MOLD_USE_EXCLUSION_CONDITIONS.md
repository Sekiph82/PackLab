# PL-0224 Mould-use exclusion conditions (with the PL-0221 threshold procedure)

Status: software half implemented. Physical evidence is **PHYSICAL_EVIDENCE_PENDING**.

PL-0220 (physical benchmark) is owner-deferred (`DEFERRED_OWNER_VALIDATION`). As a result:

- no V1 acceptance threshold can be ACCEPTED;
- no PackLab measurement is eligible for mould use.

This document does not authorize mould manufacture. It adds machine-checkable detail under
the frozen statement in `V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md` ("No direct mold
manufacture") and does not replace it.

Code:

- `core/src/packlab_core/mold_use_eligibility.py` (PL-0224): `evaluate_mold_use_eligibility`
- `core/src/packlab_core/acceptance_thresholds.py` (PL-0221): threshold proposal and owner acceptance
- Tests: `tests/core/test_mold_use_eligibility.py` and `tests/core/test_acceptance_thresholds.py`.
  The shared synthetic fixtures are in `tests/core/threshold_fixtures.py`.

## Exclusion conditions

PackLab measurements **must not** be used for mould, tooling or production-part manufacture
when any of the conditions below applies. `evaluate_mold_use_eligibility` returns
`NOT_ELIGIBLE` and lists every reason code that applies, in this order.

Authority comes from the actual `ScanMasterRevision` and `DesignModelRevision` objects, not
from caller strings. Every input defaults to the failing value:

- a missing object, family, material or backend;
- an empty surface-QA list;
- `partial_coverage=True`;
- `simulation_only=True`.

Unknown authority classes, surface-QA statuses, families, materials and backends also fail.
None of them is ignored.

| Reason code | Condition | Real source field |
| --- | --- | --- |
| `physical_validation_deferred` | Applies if `PL0220_PHYSICAL_BENCHMARK_STATUS` is not lifted. Also applies if the Scan Master manifest or Design Model `physical_accuracy_validation_status` is missing or is not in `ACCEPTED_PHYSICAL_VALIDATION_STATUSES = {OWNER_PHYSICAL_VALIDATION_ACCEPTED}`. That allow-list value is owner-only, and no production code emits it today, because `promote_scan_master` and `DesignModelRevision` always write `DEFERRED_OWNER_VALIDATION` | `acceptance_thresholds.PL0220_PHYSICAL_BENCHMARK_STATUS`; `ScanMasterRevision.manifest`; `DesignModelRevision.physical_accuracy_validation_status` |
| `authority_not_allow_listed` | Declared authority is not `SCAN_MASTER` (with no Design Model) or `DESIGN_MODEL` (with a `DesignModelRevision` object). Every other string fails, including `DESIGN_MODEL_OPERATION_WITH_PREVIEW_PROXY`, `AI_DIMENSION_FIT_PROPOSAL`, a bare `DESIGN_MODEL` and arbitrary text | declared `authority_class` checked against the supplied objects |
| `visual_reference_authority` | Additional explanation for known visual/preview classes: `AI_VISUAL_REFERENCE`, `AI_DIMENSION_FIT_PROPOSAL`, `AR_VISUAL_REFERENCE_ONLY`, `NON_CERTIFIED_VISUAL_REFERENCE`, `PREVIEW_PROXY`, `DESIGN_MODEL_WITH_PREVIEW_PROXY`, `DESIGN_MODEL_OPERATION_WITH_PREVIEW_PROXY`, `VISUAL_PRODUCT_CONTENT_APPEARANCE_ASSIGNMENT` | `authority_class` values used in `ar_preview`, `captured_geometry_fit_gate`, `dimension_fit_proposal`, `jerrycan_body_fit`, `pouch_family`, `tube_family` |
| `generated_asset` | Scan Master manifest has a non-false `generated` value | PL-0233 forbidden ancestry |
| `not_scan_master_authority` | No `ScanMasterRevision`, or manifest `authority_class != SCAN_MASTER` | `ScanMasterRevision.manifest["authority_class"]` (PL-0233) |
| `design_model_not_fitted_to_scan_master` | Design Model is standalone or its `fitted_to_scan_master_revision_id` is not the supplied Scan Master | `DesignModelRevision.parent_kind`, `.fitted_to_scan_master_revision_id` |
| `design_model_parent_binding_not_current` | Binding status is not `CURRENT` | `design_model_binding.ParentBindingStatus` |
| `package_family_flexible_tube_or_unknown` | Family is not bottle, jar, cylindrical-container or jerrycan, or `is_flexible_pack_model` is true (tube, flexible pack, `pouch_*` parameters) | `design_model.PackageFamily`; `flexible_pack_authority` (`no_mold_or_manufacturing_authority`, `flexible_film_deformation_not_measured`) |
| `material_pet_or_unknown` | Material is PET (clear/glossy, the PL-0377 transparent-PET limitation), OTHER or missing | `visual_material_library.MaterialFamily` |
| `reconstruction_backend_experimental_or_unknown` | Backend is not `colmap-openmvs`. Includes `neural-experimental`, described as "not Scan Master, CAD, or engineering authority", and a missing backend | `reconstruction.ReconstructionBackendId`; `neural_reconstruction_io` |
| `scale_not_metric_verified` | Scan Master manifest (and Design Model, if any) `scale_state` is not `metric-verified` | `reconstruction.ScaleState` (PL-0209) |
| `scale_provenance_missing` | No provenance ID, or the Scan Master and Design Model IDs disagree | manifest `scale_provenance_id`; `DesignModelRevision.scale_provenance_id` |
| `printed_mat_ruler_record_missing_or_unverified` | No PL-0223 report with the right contract and a valid `report_sha256` whose `owner_ruler_check.status` is `WITHIN_PROVISIONAL_PRINT_TOLERANCE` with record and instrument references | `print_scale_sensitivity.run_print_scale_sensitivity` output |
| `thresholds_not_accepted` | Re-running `accept_threshold_proposal` on the supplied records, observations, proposal and owner acceptance does not yield ACCEPTED with inner status `PROPOSED_PENDING_OWNER_ACCEPTANCE` and `simulation_only=false` | `acceptance_thresholds` (PL-0221) |
| `measurement_tolerance_unavailable` | No measurement, no accepted tolerance for its (category, material, feature group), or no expanded uncertainty | PL-0221 groups; `MeasurementToleranceCheck` |
| `measurement_subject_mismatch` | A measurement's material differs from the subject material. Also applies if its benchmark category does not match the package family: bottle allows `matte_bottle`/`glossy_bottle`, jerrycan allows `jerrycan`, and other families allow none | `MeasurementToleranceCheck` vs `MoldUseEvidence.material` and package family |
| `measurement_exceeds_accepted_tolerance` | Expanded uncertainty is larger than the accepted group tolerance (equal passes) | PL-0221 `proposed_tolerance_mm` |
| `partial_coverage` | Caller flags partial coverage, or Scan Master manifest `coverage_gaps` is missing or non-empty | `ScanMasterRevision.manifest["coverage_gaps"]` (PL-0233) |
| `surface_texture_qa_not_passed` | No statuses supplied, or any per-photo status is not `pass`. Failing statuses include `warning` (`low_object_surface_texture`), `unavailable`, `not_requested` and unknown values. Clear-PET captures trigger the warning (PL-0377) | `pre_reconstruction_qa` `photo_reports[*]["object_surface_texture"]["status"]` |
| `synthetic_or_simulation_data` | Caller has not stated `simulation_only=False` | `simulation_only` on PL-0221/0222/0223 outputs |
| `repeatability_not_established` | No PL-0222 report with the right contract, a valid digest, `simulation_only=false`, `physical_reproducibility_claim=true` and a within-threshold result | `repeat_scan_reproducibility` (always `simulation_only=true` today) |

`ELIGIBLE` means only that none of these exclusions applies. It is **not** authorization.
The output always carries `mold_use_authorized: false`. The V1 boundary statement requires
the following, and all of it stays outside PackLab:

- qualified tooling engineering review;
- material and process constraints (shrinkage, draft, wall thickness);
- supplier approval;
- compliance review;
- explicit owner authorization.

### What blocks ELIGIBLE today

The **only hard blocker** in this module is the constant `PL0220_PHYSICAL_BENCHMARK_STATUS`
(`DEFERRED_OWNER_VALIDATION`). It has two effects:

- It adds `physical_validation_deferred` to every result.
- It makes `accept_threshold_proposal` raise. Eligibility re-runs that function from the
  physical inputs instead of trusting an "accepted" dict, so `thresholds_not_accepted` also
  applies.

The PL-0222 and PL-0223 report digests are unkeyed SHA-256. They prove **integrity only,
not authenticity**, so a hand-hashed report passes those two checks.

Outside this module, the production promotion paths add further blockers:

- `promote_scan_master` refuses METRIC_VERIFIED.
- A `DesignModelRevision` cannot be METRIC_VERIFIED, so a Design Model is always excluded
  on scale.

A hand-constructed `ScanMasterRevision` can, however, carry any manifest.

These tests cover the blocker:

- `test_eligible_unreachable_today_even_with_most_favourable_evidence`
- `test_forged_accepted_dict_probe_cannot_supply_thresholds`
- the authority allow-list tests
- `test_inner_proposal_status_checked`, which covers the inner-proposal status check. That check is defensive and cannot be reached through the real `accept_threshold_proposal`, which always emits a PROPOSED inner proposal.

The gate can be lifted only by a reviewed code change, made after real PL-0220 evidence is
accepted. Tests lift it with `monkeypatch` only to exercise the logic.

## PL-0221 threshold derivation procedure (operator)

1. Execute PL-0220. Produce `PhysicalAccuracyBenchmarkRecord`s with status
   `READY_FOR_AUDIT` that cover matte bottle, glossy bottle and jerrycan. Each ACCEPTED
   sample needs complete caliper ground truth:
   - value and repeated readings;
   - uncertainty;
   - caliper and calibration-record references;
   - owner reference and timestamp.
2. For each ACCEPTED sample, record one `BenchmarkMeasurementObservation` containing:
   - the same measurement ID, revision and `dimension_id`;
   - a `dimension_kind`: overall height, width, depth or diameter; neck finish T, E, I or H;
     wall thickness; or a handle, base or shoulder feature;
   - the material (HDPE, PET, PP or OTHER);
   - PackLab's measured value in mm;
   - scale state `metric-verified` with a provenance ID;
   - `evidence_kind=OWNER_EXECUTED_PHYSICAL`.
3. Run `derive_threshold_proposal(records, observations)`. It refuses:
   - non-physical evidence kinds (`SYNTHETIC`, `SIMULATION_ONLY`, `PUBLIC_PROXY`);
   - scale that is not metric-verified;
   - `OWNER_REQUIRED` records;
   - an ACCEPTED sample without an observation;
   - an observation for a missing or non-ACCEPTED sample;
   - duplicate observations;
   - link mismatches;
   - any required category whose overall-dimension group has fewer than 10 samples.
4. The output has status `PROPOSED_PENDING_OWNER_ACCEPTANCE`. Its digest binds it to the
   record digests and the observation set.
5. The owner reviews the proposal and signs an `OwnerThresholdAcceptance` with:
   - an actor `ref:` or `sha256:` reference;
   - an RFC 3339 UTC timestamp;
   - a reason;
   - the proposal digest.

   `accept_threshold_proposal` then re-derives the proposal from the physical inputs and
   refuses any mismatch. Only after that does it return `ACCEPTED`. This is the only route
   to ACCEPTED, and it stays blocked until the PL-0220 gate is lifted.

### Statistical rule

The benchmark data is grouped by (benchmark category, material family, feature group). The
feature group is one of `overall_dimension`, `neck_finish` or `wall_and_feature`. The error
is `e = PackLab measured mm - caliper mm`. Each group with at least 10 samples gets this
proposed tolerance:

```
T = ceil_0.01mm( max( |mean(e)| + k * stdev(e),  max|e|,  2 * max(caliper uncertainty_mm) ) )
```

- `k` is the two-sided normal tolerance factor for 95 % coverage at 95 % confidence.
  - It uses Howe's (1969) formula with the Wilson-Hilferty chi-square quantile.
  - Against the published table it is never below the table value and at most 0.01 above:
    k(10)=3.379, k(30)=2.549, k(100)=2.233.
  - `tolerance_factor` refuses n < 10. Below that, the approximation diverges.
- `max|e|` keeps the threshold from being tighter than any observed error.
- The caliper floor keeps the threshold from being tighter than the reference can verify. It
  treats `uncertainty_mm` as a standard uncertainty with coverage factor 2.
- A group with fewer than 10 samples is reported as `INSUFFICIENT_SAMPLES` and gets no
  threshold.

`test_each_rule_term_can_dominate` covers each term with its own group:

- an outlier group, where `max|e|` dominates;
- a large caliper uncertainty group, where the floor dominates;
- a negative-bias group, where `|mean|` dominates.

Synthetic fixtures can exercise the math only through `derive_test_only_threshold_proposal`.
That function returns status `TEST_ONLY_SYNTHETIC_NOT_ACCEPTABLE` with `simulation_only=true`,
and acceptance refuses that status.

## Limits

- The code does not prove these inputs; the caller asserts them:
  - `evidence_kind`, `simulation_only` and `partial_coverage`;
  - the surface-QA statuses;
  - the material, family and backend values.

  Against a mislabelled input, the guard is the owner acceptance step, made against the
  owner's own benchmark records.
- The rule assumes errors in a group are roughly normal and independent. Repeated scans of one
  object are not independent. The record contract has no physical-object ID, so the
  10-sample minimum does not guarantee 10 distinct objects.
- Tolerances are absolute values in mm, not relative to size. Scale verification relies on
  the provisional PL-0223 ruler gate (±1.0 mm spacing, ±0.5 mm marker side).
- The eligibility check compares a measurement's expanded uncertainty with the group
  tolerance. It does not compare against design or nominal tolerances, which need
  engineering input.

## Pending

These items are still pending:

- real PL-0220 benchmark records;
- an owner-accepted V1 threshold set;
- a real printed mat with an owner ruler record;
- real repeat scans (PL-0222);
- tooling engineering review.

PL-0221 and PL-0224 stay `DEFERRED_OWNER_VALIDATION` / **PHYSICAL_EVIDENCE_PENDING**.
