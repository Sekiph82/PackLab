# CLAUDE_PEER_REVIEW — PL-0221 / PL-0224 software halves (V03 confirmation)

Reviewer: independent Claude Code peer reviewer (not the implementer). Confirms V02 follow-ups.
Base: HEAD d1ab06187dade39409c684be803edd8a09c6ee98 (main); files under review untracked.
Scope: software only; both tasks stay PHYSICAL_EVIDENCE_PENDING (PL-0220 owner-deferred).

## Verdicts
- PL-0221: **SOFTWARE_PASS** (unchanged from V02)
- PL-0224: **SOFTWARE_PASS**

## Reviewer-run evidence
- Target tests: 68 passed. With related suites (physical_accuracy_benchmark, v1_limitations_freeze,
  print_scale_sensitivity, repeat_scan_reproducibility, flexible_pack_authority, scan_master): 133 passed.
- ruff check core apps tools tests: clean; ruff format --check (line-ending auto) on 5 files: clean;
  mypy on both modules: clean.

## V02 findings
- P2-A FIXED: mold_use_eligibility.py:69-72, 233-241 add `measurement_subject_mismatch`
  (material identity + FAMILY_BENCHMARK_CATEGORIES). Gate-lifted probes: HDPE subject + PET glossy
  measurement -> NOT_ELIGIBLE [measurement_subject_mismatch]; BOTTLE + jerrycan measurement -> same;
  JAR family -> same.
- P3-1 FIXED: mold_use_eligibility.py:67,176-183 allow-list `ACCEPTED_PHYSICAL_VALIDATION_STATUSES`.
  Gate-lifted probes: missing key, empty string, unknown value -> physical_validation_deferred.
  No production code under core/tools/apps emits OWNER_PHYSICAL_VALIDATION_ACCEPTED (grep).
- P3-2 FIXED: fixture now uses the allow-listed value; doc line 40 states it is owner-only.
- P3-3 FIXED: all 9 V02 surviving mutants (generated, is_flexible_pack_model, model scale, provenance
  agreement, ruler record_reference, ruler contract, inner proposal status, repeatability digest and
  contract) are now KILLED on a fresh scratch copy. New mutants for material mismatch, category mismatch,
  manifest status check and BOTTLE-allows-jerrycan are KILLED.

## Residual notes (P3, non-blocking)
- Mutant removing the Design Model status check (line 181) survives. Redundant today: DesignModelRevision
  enforces DEFERRED at construction (design_model.py:299), and the scan-manifest check also fires.
- Adding a JAR entry to FAMILY_BENCHMARK_CATEGORIES survives (no JAR-measurement test); the probe confirms
  current behaviour fails closed.

Today: best-case evidence -> NOT_ELIGIBLE [physical_validation_deferred, thresholds_not_accepted,
measurement_tolerance_unavailable]; mold_use_authorized False in every probe. Gate lifts only via scoped
monkeypatch in tests. No edits or git writes by reviewer.
