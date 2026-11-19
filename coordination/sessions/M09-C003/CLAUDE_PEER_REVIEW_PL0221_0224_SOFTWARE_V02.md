# CLAUDE_PEER_REVIEW — PL-0221 / PL-0224 software halves (V02 re-review)

Reviewer: independent Claude Code peer reviewer (not the implementer). Supersedes V01 verdicts.
Base: HEAD d1ab06187dade39409c684be803edd8a09c6ee98 (main); files under review are untracked.
Files: core/src/packlab_core/acceptance_thresholds.py, core/src/packlab_core/mold_use_eligibility.py,
tests/core/test_acceptance_thresholds.py, tests/core/test_mold_use_eligibility.py,
tests/core/threshold_fixtures.py, docs/development/PL-0224_MOLD_USE_EXCLUSION_CONDITIONS.md.
Scope: software only; PL-0220 physical benchmark owner-deferred, both tasks stay PHYSICAL_EVIDENCE_PENDING.

## Verdicts
- PL-0221: **SOFTWARE_PASS**
- PL-0224: **SOFTWARE_PASS_WITH_NOTES** (P2-A must be fixed before the PL-0220 gate constant is ever lifted)

No P1. Today nothing reaches ACCEPTED or ELIGIBLE: the module constant blocks acceptance and adds
`physical_validation_deferred`; real `promote_scan_master` output is never METRIC_VERIFIED and always
DEFERRED. `mold_use_authorized` is False in every output (mutants killed). Gate lifts exist only through
scoped pytest monkeypatch.

## Commands (reviewer-run, .venv, Windows)
- Two target test files: 57 passed.
- Plus test_physical_accuracy_benchmark, ci/test_v1_limitations_freeze, test_print_scale_sensitivity,
  test_repeat_scan_reproducibility, test_flexible_pack_authority, test_scan_master: 122 passed.
- `ruff check core apps tools tests`: all passed. `ruff format --check` (line-ending auto) on 5 files: formatted.
- `mypy` on both modules: no issues.
- Mutation (fresh scratch copy, repo untouched): 44 mutants, 35 killed, 9 survived (P3-3).
- Probes (scratch script, in-process constant flip to simulate the future reviewed change).

## V01 finding disposition
- P2-1 authority deny-list: FIXED. Allow-list `{"SCAN_MASTER": no model, "DESIGN_MODEL": model required}`
  (mold_use_eligibility.py:39,174-176) plus manifest `authority_class == SCAN_MASTER` and fitted-revision
  id match (181-192). All V01 probe strings now give `authority_not_allow_listed`.
- P2-2 missing exclusions: FIXED. Package family allow-list + `is_flexible_pack_model` (194-198),
  material HDPE/PP only (62,199-200), backend must be COLMAP_OPENMVS (201-202), surface QA uses real
  `pre_reconstruction_qa` statuses, any non-`pass` or empty fails (234-236).
- P2-3 forged accepted dict / doc overclaim: FIXED. Eligibility re-runs `accept_threshold_proposal`
  (258-268); a plain dict is not `ThresholdAcceptanceInputs` and is refused even with gate lifted (probe).
  Doc lines 69-91 now name the constant as the only hard blocker and state digests are integrity only and
  that a hand-built ScanMasterRevision can carry any manifest. Honest.
- P2-4 rule-term discrimination: FIXED. `test_each_rule_term_can_dominate` kills max|e|, floor, factor-2
  and abs(mean) mutants.
- P3-1 tolerance_factor: FIXED (n<10 and non-int refused, acceptance_thresholds.py:172-173).
- P3-2 negative paths: mostly FIXED (A13/A14 killed); residual survivors below.
- P3-3 MeasurementToleranceCheck validation: FIXED (104-120).
- P3-4 ruler record: FIXED (digest + contract + owner refs, 290-301).
- P3-5 test coupling: FIXED (tests/core/threshold_fixtures.py).

## Statistics (re-verified)
k(10)=3.3869, k(30)=2.5498, k(100)=2.2328 vs table 3.379/2.549/2.233; conservative, < +0.01.
Rule at acceptance_thresholds.py:354 matches doc.

## New findings
### P2-A (latent, gate-protected) Measurement material/category not tied to the subject
mold_use_eligibility.py:199-200 and 221-229. The PET exclusion checks `evidence.material`, but each
`MeasurementToleranceCheck` carries its own material/category and is looked up in the accepted groups
independently. Probe (gate lifted): subject material HDPE + measurement `("glossy_bottle", PET,
overall_height, 0.01)` -> ELIGIBLE; subject family BOTTLE + `jerrycan` category measurement -> ELIGIBLE.
So the PET/category exclusion can be sidestepped via the measurement record. Fix: require
`item.material == evidence.material` (and in MATERIALS_WITH_BENCHMARK_BASIS) and category consistent with
the package family. Not exploitable today (constant), must be fixed before the gate is lifted.

### P3-1 Missing manifest field fails open
mold_use_eligibility.py:168-171. A Scan Master manifest without `physical_accuracy_validation_status`
does not add `physical_validation_deferred` (probe: ELIGIBLE with gate lifted). Real promoted manifests
always carry DEFERRED, and the doc says "every input defaults to the failing value"; require an explicit
non-deferred value instead.

### P3-2 Fixture validation status literal
tests/core/threshold_fixtures.py: hand-built manifests use `OWNER_VALIDATED_TEST_ONLY`, which any
non-DEFERRED value passes (ties to P3-1). Acceptable for tests; no production allow-list of accepted
validation statuses exists.

### P3-3 Surviving mutants (untested defense-in-depth)
E4 `generated` check removed (no test; probe confirms check itself works); E8b `is_flexible_pack_model`
removed (only TUBE/FLEXIBLE_PACK families tested, not a BOTTLE model with `pouch_*` parameters);
E11/E12 Design Model scale/provenance agreement; E14 ruler record_reference; E15 ruler contract;
E16 inner proposal status (unreachable: accept always emits PROPOSED inner); E22 repeatability digest and
E23 contract (tamper test is also caught by field checks).

## Confirmed
- Physical threshold path refuses non-physical labels and non-METRIC_VERIFIED/provenance-less scale;
  10-sample minimum; digest-bound PROPOSED; acceptance re-derives, binds digest, refuses TEST_ONLY and is
  refused while PL0220 is DEFERRED.
- 20 ordered reason codes; doc table matches the code and cites real fields.
- Limits section honestly lists caller-asserted labels (evidence_kind, simulation_only, coverage, surface QA,
  material, family, backend) and the independence/absolute-mm limits.

## Limits of this review
Other builders' files not reviewed. No CI run (uncommitted). Implementer's 57/104 counts were not relied
on; reviewer counts above.
