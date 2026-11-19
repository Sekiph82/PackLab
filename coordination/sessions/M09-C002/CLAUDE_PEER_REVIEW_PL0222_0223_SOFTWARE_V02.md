# CLAUDE_PEER_REVIEW PL-0222 / PL-0223 software proxy, V02 (re-review of V01 findings)

Reviewer: independent Claude Code reviewer subagent. It did not implement this work, made no source edits and made no git writes.

Base: HEAD 934d2d35e806c1795f14861a245240446a32d450. The 5 files under review are still untracked.

All results below are my own reruns. The implementer counts (127 passed, 4 skipped; 35 focused) were independently reproduced here.

## Commands run (reviewer)
- The 2 focused test files: 35 passed.
- The 2 focused files plus tests/calibration and tests/core/test_repeat_scan_registration.py: 127 passed, 4 skipped. All 4 skips are calibration tests that need cv2, which is not installed.
- `ruff check` and `ruff format --check` on the 4 py files: clean.
- `mypy` on the 2 modules: no issues.
- Mutation testing on in-memory module copies, with the tree untouched:
  - PL-0223: 19 mutants including a no-op control. 15 killed; the 4 survivors are below.
  - PL-0222: 25 mutants including a no-op control. 23 killed; the 2 survivors are below.

## Disposition of the V01 findings
| V01 finding | Fix in source | Mutant result | Status |
|---|---|---|---|
| P2-1 NaN fail-open in ruler gate | `check_printed_mat_spacing` validates both tolerances and any non-None reading with `_positive_finite`, which rejects bool, non-finite and non-positive values (print_scale_sensitivity.py:278-290, :565-571) | reading-validation, tolerance-validation and bool-acceptance mutants all killed | CLOSED |
| P2-2 forgeable `simulation_only` | `simulation_only` is the literal True (repeat_scan_reproducibility.py:210). The caller label moved to `scale_evidence_class_claimed_physical`, with `scale_evidence_class_basis` set to `caller_asserted_label_not_owner_record_bound` (:211-212, :262-277). Docs :62-64 and :126-127 updated | a mutant deriving `simulation_only` from the label and a mutant forcing the label to always False are both killed | CLOSED |
| P2-3 end-to-end REJECTED_SCALING | A new test runs a rejected measurement through `run_print_scale_sensitivity` | blocker-drop mutant killed | CLOSED |
| P3-1 p95 truncated by correspondence gate | Statistic renamed to `p95_distance`. A run fails with `correspondence_gate_must_exceed_surface_threshold` unless the gate is strictly greater than the threshold (:91-93). The report records `surface_residuals_truncated_at_correspondence_distance` | gate-removal and `<=`-to-`<` mutants both killed | CLOSED |
| P3-2 pass/exceed and outlier pool untested | New tests cover these | RC95-ignored, surface-ignored, outlier-in-pool, `int(0.9n)` and off-by-one p95 mutants all killed | CLOSED |
| P3-3 ZeroDivisionError | `degenerate_zero_extent` raised when a consensus extent is 0 or less (:164-165) | killed | CLOSED |
| P3-4 shared provenance | `scale_provenance_shared_between_scans` (:247-248) | killed | CLOSED |
| P3-5 PL-0223 weak tests and SVG drops | Loader fails closed on transforms and size mismatches (:86-99). Strict analytic-field test, boundary test and owner-tolerance test added | analytic, `>=`, owner-tolerance, `detected_by_image_spacing`, reference-distance, four-marker, group-transform and rect-width mutants all killed | CLOSED, with residual notes N1/N2 |
| P3-6 small items | PL-0222 `report_digest_valid` (:280-282), duplicate-id test, bool scale values rejected | digest, unique-id and bool mutants killed | CLOSED |

## Re-verified unchanged behaviour
- **Real estimator paths.** PL-0223 still feeds the nominal side length through the real `estimate_scale` and `estimate_reconstruction_scale` (nominal-side mutant killed).
- **PL-0222 registration.** It still uses the accepted rigid `register_repeat_scans`, measures coverage by reverse registration (forward-coverage mutant killed), and reports RC95 = 1.96*sqrt(2)*sample std (factor and pstdev mutants killed).
- **Physical flags stay hard-coded.**
  - PL-0223: `physical_claim_allowed=False`
  - PL-0222: `physical_reproducibility_claim=False` and `mold_use_authorized=False`
  - Both: `physical_validation_status=PHYSICAL_EVIDENCE_PENDING`

## Residual notes (P3, non-blocking)
- **N1.** Two SVG guards in the loader are not pinned by any test. The mutants removing them survive:
  - the per-marker `data-side-length-mm` comparison (print_scale_sensitivity.py:95)
  - the `transform` check on the rect itself (:94)

  Both guards are present and correct in the source. Each needs one negative fixture.
- **N2.** Two survivors are inherent and need no fix:
  - Replacing the estimator output with the closed form survives because the tests are built around that formula. I confirmed by reading the code that the real estimator is used.
  - Replacing the reverse-registration seed `_invert_rigid` with identity survives because the synthetic poses converge from either seed.
- **N3.** repeat_scan_reproducibility.py:312-313 has two consecutive comments that contradict each other. The first still calls the p95 "the 95 % coefficient". It is cosmetic; delete line 312.

## Overclaim check
- The docs and both reports keep PHYSICAL_EVIDENCE_PENDING.
- The caller label is now explicitly marked as a claim, not proof.
- Neither report allows a physical claim.
- Both tasks remain physically gated on PL-0220.

## Verdict
SOFTWARE_PASS_WITH_NOTES

- All V01 P2 and P3 findings are closed in source and pinned by tests.
- The remaining notes are cosmetic or untested-but-present guards (N1, N3), plus two inherent mutant survivors (N2).
- PL-0222 and PL-0223 must stay `[ ]` PHYSICAL_EVIDENCE_PENDING on PL-0220. This software verdict is not a physical PASS.
