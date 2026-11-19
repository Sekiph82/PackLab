# CLAUDE_PEER_REVIEW — PL-0221 / PL-0224 software halves (V01)

Reviewer: independent Claude Code peer reviewer (did not author the implementation).
Base: HEAD d1ab06187dade39409c684be803edd8a09c6ee98 (main). Files under review are untracked/new.
Scope: software only. Physical validation (PL-0220) is owner-deferred and stays PHYSICAL_EVIDENCE_PENDING.

## Verdicts
- PL-0221: **SOFTWARE_PASS_WITH_NOTES**
- PL-0224: **FAIL** (changes required, small: see P2-1..P2-3). Not a safety leak today; the deliverable is
  incomplete/overclaimed.

No P1. No path reaches ACCEPTED or ELIGIBLE in production today; `mold_use_authorized` is hard-coded False
in every output (proposal, acceptance, eligibility). Gate lifts exist only via pytest `monkeypatch` (scoped,
auto-undone); no production hook found.

## Commands run (reviewer, Windows, .venv)
- `pytest tests/core/test_acceptance_thresholds.py tests/core/test_mold_use_eligibility.py tests/core/test_physical_accuracy_benchmark.py tests/ci/test_v1_limitations_freeze.py` -> 36 passed
- `ruff check core apps tools tests` -> All checks passed
- `ruff format --check --config "format.line-ending='auto'"` on the 4 files -> already formatted
  (repo-wide: 59 other files would be reformatted; pre-existing, not in scope)
- `mypy` on the two modules -> no issues
- Mutation testing on a scratch copy (repo untouched): 33 mutants, 14 killed-relevant survivors (below).
- Probe script (scratch) for forgery/authority gaps.

## Statistics check
- `tolerance_factor` (acceptance_thresholds.py:169-180) is Howe's k = sqrt(nu(1+1/n) z_{0.975}^2 / chi2_{0.05,nu})
  with Wilson-Hilferty lower-tail quantile. Correct quantile direction (mutating to upper tail is killed).
- Values: k(10)=3.3869, k(30)=2.5498, k(100)=2.2328 vs tabulated exact 3.379/2.549/2.233. n=10 is
  +0.008 (conservative) and passes only because the test tolerance is 0.01.
- Threshold rule (line 354) matches the doc. Caliper floor `2*max(u)` is fine; `uncertainty_mm or 0.0`
  only hits u=0.0 because `CaliperGroundTruth.complete` requires non-None.

## Findings

### P2-1 PL-0224 authority check is a deny-list; any non-listed authority string passes on the Design Model branch
mold_use_eligibility.py:29-38, 134-145. When `design_model_parent_kind` is set, `authority_class` is never
checked positively. Probe with gate lifted (simulating the future reviewed flip) returned ELIGIBLE for
`DESIGN_MODEL_OPERATION_WITH_PREVIEW_PROXY` (jerrycan_body_fit.py:63, symmetric_section_loft.py:100),
`AI_DIMENSION_FIT_PROPOSAL` (dimension_fit_proposal.py:242), `DESIGN_MODEL`, and the arbitrary string `WHATEVER`.
Fix: allow-list (e.g. SCAN_MASTER; explicit Design Model revision classes), fail closed otherwise.

### P2-2 Missing exclusion conditions vs. existing codebase authority
- Flexible pack / tube: flexible_pack_authority.py:8-15 declares `flexible_film_deformation_not_measured`
  and `no_mold_or_manufacturing_authority`; PL-0224 has no package-family exclusion. A CAPTURED_SCAN_MASTER
  parented pouch/tube Design Model is ELIGIBLE once the gate flips (probe).
- Neural/experimental reconstruction: no backend field/exclusion (neural_reconstruction_io.py:421,516 says
  "not Scan Master, CAD, or engineering authority"). Today covered only indirectly by scale state.
- Transparent/glossy PET: `SURFACE_RISK_FLAGS` (lines 40-48) are invented strings; grep finds no producer of
  `transparent_surface`, `glossy_surface`, `specular_highlights`, `translucent_closure`. Only
  `low_object_surface_texture` exists (pre_reconstruction_qa.py:257). Unknown/variant flags are silently
  ignored, and material PET/glossy_bottle is not itself an exclusion. Doc row (PL-0224 doc line 34) cites
  "capture/material flags" that do not exist.

### P2-3 Doc overclaims "why ELIGIBLE is unreachable today"
PL-0224 doc lines 49-61 list three independent blockers. In reality only the constant blocks: accepted
thresholds and the PL-0222 report are verified by unkeyed self-SHA-256 only (mold_use_eligibility.py:164-197),
with no re-derivation/signature. A hand-built dict (TEST_ONLY inner proposal, tolerance 50 mm, recomputed
digests) plus a hand-hashed repeatability report yields reasons == ['physical_validation_deferred'] today and
ELIGIBLE once the constant flips. Also `_accepted_tolerances` does not check inner proposal status ==
PROPOSED or inner simulation_only. Doc must state the digests are integrity, not authenticity, and that the
constant is the sole hard blocker; ideally eligibility should require re-derivation via
`accept_threshold_proposal` inputs or an authenticated record before the gate is lifted.

### P2-4 PL-0221 central rule components not discriminated by tests
Surviving mutants: drop `max_abs` term (A2), caliper factor 2->1 (A3), drop caliper floor (A4),
`abs(mean)`->`mean` (A5). The synthetic fixture (N(0.1,0.2), u=0.02) never makes max|e| or the floor
dominate, nor uses negative bias. Add targeted fixtures (outlier group, large caliper uncertainty,
negative-bias group).

### P3
- P3-1 acceptance_thresholds.py:172 `tolerance_factor` public for n>=2 but W-H breaks at small nu
  (k(2)=20591 vs Howe-exact ~38). Unreachable via MIN_SAMPLES=10; restrict or document.
- P3-2 Untested negative paths (surviving mutants): observation for non-ACCEPTED sample (A13), duplicate
  observation (A14); eligibility: accepted `simulation_only` (E2), accepted digest (E3), proposal digest
  (E4), `<=` boundary (E5), repeatability digest (E6) and physical claim (E13), missing uncertainty (E10),
  status (E11). Several are defense-in-depth layers, but none is individually tested.
- P3-3 `MeasurementToleranceCheck` has no validation: negative `expanded_uncertainty_mm` (-5.0) passes the
  tolerance check (probe). Free-string category/material.
- P3-4 `printed_mat_ruler_check` accepts any mapping with the status string; no digest/owner-reference check
  against print_scale_sensitivity output (which has report_sha256).
- P3-5 tests/core/test_mold_use_eligibility.py:8 imports helpers from another test module (coupling).
- P3-6 Doc limits correctly disclose caller-asserted labels, non-independence of repeat scans and
  absolute-mm tolerances; good.

## Confirmed claims
- Physical path refuses SYNTHETIC/SIMULATION_ONLY/PUBLIC_PROXY and non-METRIC_VERIFIED or provenance-less
  observations (killed mutants A9/A10).
- 10-sample minimum per group and per required category overall-dimension group (A8/A18 killed).
- Proposals digest-bound as PROPOSED_PENDING_OWNER_ACCEPTANCE; acceptance re-derives, binds digest, refuses
  TEST_ONLY, and is refused outright while PL0220_PHYSICAL_BENCHMARK_STATUS is DEFERRED (A11/A12/A15/A19 killed).
- 16 reason codes, ordered output, mold_use_authorized False always (E9/A20 killed).
- V1 limitations freeze test still passes; V1_LIMITATIONS doc unmodified.

## Limits of this review
Did not review backend_benchmark, station_session_repeatability, signing workflow or ios provenance changes.
No CI run inspected (files are uncommitted). Builder/tester claims were verified against source, not trusted.
