# CLAUDE_PEER_REVIEW PL-0222 / PL-0223 software proxy, V01

Reviewer: independent Claude Code reviewer subagent. It did not implement this work and made no source edits.
Base: HEAD 4ee6bb0937c668458f44afe27c7d3de1e6b399aa. The files under review are untracked working-tree files:
- core/src/packlab_core/print_scale_sensitivity.py
- core/src/packlab_core/repeat_scan_reproducibility.py
- tests/core/test_print_scale_sensitivity.py
- tests/core/test_repeat_scan_reproducibility.py
- docs/development/PL-0222_0223_REPRODUCIBILITY_AND_PRINT_SCALE_PROCEDURE.md

The findings below belong to this reviewer. They are not copied from the builder or tester reports.

## Commands run (reviewer)
- `.venv/Scripts/python.exe -m pytest -q tests/core/test_print_scale_sensitivity.py tests/core/test_repeat_scan_reproducibility.py tests/calibration tests/core/test_repeat_scan_registration.py`
  - Result: 110 passed, 4 skipped.
  - All 4 skips are cv2-absent tests in tests/calibration (test_marker_detection, test_synthetic_ground_truth). They are unrelated to these files.
- The two focused files on their own: 18 passed.
- `ruff check` and `ruff format --check` on the 4 py files: clean.
- `mypy` on the 2 modules: no issues.
- Mutation testing on in-memory module copies, with the tree untouched:
  - PL-0223: 14 mutants (incl. a no-op control), 5 killed. Survivors are listed under P2/P3.
  - PL-0222: 17 mutants (incl. a no-op control), 11 killed.

## Verified correct
- **Real code paths.** `_simulate` (print_scale_sensitivity.py:470-475) calls the real `estimate_scale` and `estimate_reconstruction_scale`. Both estimators use the mean of the 4 edges (reconstruction_scale.py:163-170, scale_estimation.py:60-62). The software side is nominal (:405, :424).
  - With mean edge = (sx+sy)/2 * side, the factor error is exactly 2/(sx+sy)-1. The noise-free test matches this to 1e-12.
  - Mutating the nominal side is killed by the tests.
- **Fit-to-page values.** A4 same-media gives 200/210 and a +5.0 % error. US Letter gives min(205.9/210, 269.4/297) and a +10.2 % error. Both match the docs.
- **Uniform errors need a ruler.** Uniform errors are invisible to image spacing and caught only by the ruler (test :79-94). The report gives the undetected limit as tol/ref_distance (:368-371).
- **PL-0223 `simulation_only`.** It is the literal True (:334), and `physical_claim_allowed` is the literal False (:336).
  - A caller cannot override either through an argument.
  - Tampering with the stored report breaks `report_digest_valid`.
- **RC95.** The value 1.96*sqrt(2)*sample stdev (repeat_scan_reproducibility.py:38, :278) is the correct Bland-Altman / ISO 5725 repeatability limit. Mutants using 2.0 or pstdev are killed.
- **Nearest-rank p95.** `ordered[ceil(0.95 n) - 1]` (:294) is the correct nearest-rank definition.
- **PL-0222 uses the accepted registration path.** It registers through `register_repeat_scans`, which is rigid with no scale. Coverage comes from reverse-registration fitness, which is `count / len(reference points)`. The forward-ratio mutant is killed.
- **Fail-closed paths** are tested and kill their mutants:
  - mixed state
  - RELATIVE input
  - missing, mismatched or factorless provenance
  - fewer than 3 revisions
  - reference not found
  - fewer than 2 usable scans
- **Private helpers.** `_hash` and `_transform_point` from repeat_scan_registration (:24-30) are same-package internals, and `_hash` uses the same canonical JSON (allow_nan=False).
  - Reusing them is better than re-implementing them, so it is acceptable.
  - Promoting them to a public name later would reduce coupling (P3-6).

## Findings

### P2-1 `check_printed_mat_spacing` fails open on NaN (print_scale_sensitivity.py:260-290)
This function is the public, exported owner-ruler gate. It does not validate readings or tolerances.

`abs(nan) > tol` is False, so the following inputs return `WITHIN_PROVISIONAL_PRINT_TOLERANCE`:
- `spacing_x_mm=nan` (reproduced by the reviewer)
- a NaN tolerance combined with a negative reading (reproduced by the reviewer)

`run_print_scale_sensitivity` is shielded, for two reasons:
- `PrintedMatRulerMeasurement.__post_init__` validates the readings.
- `spacing_tolerance_mm` is validated at :303.

The public function itself is not shielded. `marker_side_tolerance_mm` is never validated anywhere.

Fix: validate that readings and tolerances are finite and positive (and reject bool) inside `check_printed_mat_spacing`, then add a negative test.

### P2-2 A caller can force PL-0222 `simulation_only` to false (repeat_scan_reproducibility.py:248-263)
`simulation_only` comes from the `evidence_class` label on `PhysicalMarkerReference`. That label is a caller-chosen string (reconstruction_scale.py:57), with no binding to a retained owner record or digest.

The test at test_repeat_scan_reproducibility.py:278-285 builds wholly synthetic data with `"accepted_owner_physical"` and asserts `simulation_only is False`.

`physical_validation_status` stays PENDING and `physical_reproducibility_claim` stays False, so there is no physical PASS overclaim. However:
- The docs (:47-48 and :102-103) present `simulation_only=false` as part of the closing evidence.
- The coordinator brief requires that a caller cannot force `simulation_only` false.

Fix: either
- rename the field to something like `scale_references_labelled_owner_physical`, or
- state in the docs and the report that it is caller-asserted, necessary but not sufficient, and must be checked against the retained owner record.

The test name should also say that the flag is label-derived.

### P2-3 The test for a rejected owner reading does not check the blocker list (test_print_scale_sensitivity.py:139-160)
The rejected-reading case calls only `check_printed_mat_spacing` directly. No test runs a REJECTED owner measurement through `run_print_scale_sensitivity` and asserts that `owner_ruler_measurement_of_printed_mat_required` stays in `physical_claim_blockers`.

A mutant that removes the blocker on `REJECTED_SCALING` (:342) survives.

The current code is correct, but this blocker list is the security-relevant output and nothing pins it.

### P3-1 The surface p95 cannot exceed the correspondence gate
The surface "repeatability_coefficient_95" is computed only from ICP inlier residuals. `register_repeat_scans` drops anything beyond `maximum_correspondence_distance`, so the p95 can never exceed that gate.

If a caller sets the correspondence gate at or below `maximum_surface_deviation_p95`, the surface threshold cannot fail.

The docs (:117-119) mention nearest-neighbour correspondences but not this truncation. Fix: record the gate in the report, or require gate > threshold.

The name `repeatability_coefficient_95` for an unsigned-distance p95 is also misleading next to the dimension RC95. Consider renaming it `p95`.

### P3-2 The pass/exceed logic and outlier exclusion are not fully tested (repeat_scan_reproducibility.py:184-198)
These mutants survive:
- `within` ignoring the dimension RC95
- pooled surface residuals including scale-outlier scans
- a p95 index shifted to `int(0.9 n)`

Fix: add a dimension-RC-exceeded case, an assertion on surface stats in the outlier test, and an exact p95 check on a known vector.

### P3-3 Inputs with a zero extent raise the wrong error type (:161-163)
If an input has zero extent on an axis (for example a planar scan), the consensus extent is 0 and the code raises ZeroDivisionError instead of ReproducibilityError.

This still fails closed, but with the wrong exception type.

### P3-4 One scale provenance can be shared by every scan (:235-245)
Nothing enforces one scale provenance per scan. All scans may reference the same provenance, and nothing ties `provenance.input_reconstruction_revision` to the scan revision. Doc step 2 says each scan needs its own provenance.

Either enforce this or note that it is not enforced.

### P3-5 Weak tests and silent marker drops in PL-0223
- **The `analytic_relative_scale_error` report field is weakly tested.** The noise-free test recomputes the analytic value locally. The 3-sigma band of the seeded test (sigma up to about 0.006 for the 2 % cases) is too wide to tell 2/(sx+sy)-1 from 1/sx-1, and that mutant survives.
- **Untested aggregates and SVG guards.** These mutants survive:
  - `detected_by_image_spacing` hard-wired to False
  - the reference-distance mismatch guard removed (:117-121)
  - the four-marker guard removed (:113-114)
  - `>` changed to `>=` at the tolerance boundary
  - the owner check ignoring the configured `spacing_tolerance_mm` (:319)
- **The SVG loader can silently drop markers.** It drops any marker whose rect width or height is not exactly float-equal to the side (:96-97). It also ignores any group transform and the per-marker `data-side-length-mm`. The current A4 and A3 SVGs have no transforms, so this is OK today.
- **Re-implementation is not detectable by tests.** Replacing the estimator output with the closed form also survives, because the tests are built around that formula. The reviewer checked by reading the code that the real estimator is used.

### P3-6 Remaining small items
- PL-0222 has no `report_digest_valid` counterpart.
- The unique-revision-id guard (:88-89) is untested (its mutant survives).
- Reaching into the private `_hash` and `_transform_point` is acceptable within the package, but promoting them to a public name would be preferable.
- `PrintScaleScenario` accepts bool scale values.

## Overclaim check
- **Docs** say PHYSICAL_EVIDENCE_PENDING, "not a physical PASS", and say that simulation never closes either task. The only issue is P2-2.
- **Reports** mark the ground truth as synthetic or nominal (`geometry_class`, `ground_truth_class`, `tolerance_status` PROVISIONAL_PENDING_PL-0221). Each report hard-codes its physical-claim flag to False:
  - PL-0223: `physical_claim_allowed=False`
  - PL-0222: `physical_reproducibility_claim=False`
- **PL-0222** also hard-codes `mold_use_authorized=False`.
- **Paper shrink:** the docs label the shrink values illustrative, not measured.

No physical-accuracy claim is drawn from invented ground truth.

## Verdict
SOFTWARE_PASS_WITH_NOTES

- The math, the use of the real estimator and registration paths, and the main fail-closed paths are correct.
- P2-1 (NaN fail-open in the public ruler gate) and P2-2 (forgeable `simulation_only` semantics) should be fixed or documented before these proxies are cited as accepted software evidence.
- Both tasks must stay `[ ]` PHYSICAL_EVIDENCE_PENDING, blocked on PL-0220.
