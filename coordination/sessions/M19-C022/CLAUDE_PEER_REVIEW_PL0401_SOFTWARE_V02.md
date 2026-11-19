# CLAUDE_PEER_REVIEW - PL-0401 software half (V02 re-review)

Reviewer: independent Claude source reviewer (non-implementing). I made no edits to the files under review and no git writes. This file is the only one I created.
Base: `main` HEAD `d1ab0618`. The files under review are untracked working-tree files. This V02 re-review supersedes V01 (CLAUDE_PEER_REVIEW_PL0401_SOFTWARE_V01.md, verdict FAIL).

| File | SHA-256 |
| --- | --- |
| core/src/packlab_core/station_session_repeatability.py | 74af1b837c5590f8d412c2b72e304c5a8039d10873753f33a173640f153f52a4 |
| tests/core/test_station_session_repeatability.py | 404ff686590a1beccc1bba60c0e605528196f905b7e984003b9a0b66053bd869 |
| docs/development/PL-0401_STATION_REPEATABILITY_PROCEDURE.md | 05d99010295ac467e9b6dfdced2920f00936829a3285deb77fe3560eafb86955 |

**Verdict: SOFTWARE_PASS_WITH_NOTES.** All V01 findings (P1-1 and P2-1) are fixed in the source, and I verified each fix independently. Only P3 notes remain. This review covers software only. Physical validation stays PHYSICAL_EVIDENCE_PENDING, and the PL-0401 physical half stays open.

## Commands run by the reviewer (Windows, Python 3.12.10, .venv)

- pytest of the new test file plus tests/core/test_repeat_scan_reproducibility.py: 40 passed (28 + 12). This matches the implementer claim.
- ruff check core apps tools tests: all checks passed.
- ruff format --check with line-ending auto on both new .py files: already formatted.
- mypy on the module: no issues.
- Mutation testing: 34 mutants, each applied to a temp copy of the module and injected through a pytest plugin. The repo was not touched. 32 were killed and 2 survived (see N-1 and N-2).
- I ran the in-test reproduction helper `drift_rates()` (about 2 min 50 s). Results: 5 sessions 0.67 % false alarm and 83 % exact detection; 6 sessions 1.0 % and 84 %; 12 sessions 0.67 % and 91.3 %. These match the doc table exactly.
- I wrote my own probes for: registration error with noisy scans, a NaN transform, and the provenance of initial_transforms.

## Closure of V01 findings

- **P1-1 (cross-session frame): CLOSED.**
  - `_bind_scans` (:394-437) binds the supplied RegistrationRevision scans to the report. It checks the revision ID set, the reference revision, the parent digest, scale provenance, project and unit, and that the reported extents are reproduced from points and the report transforms to a relative tolerance of 1e-9. RegistrationRevision itself checks its point-sample digest (repeat_scan_registration.py:129).
  - The reference scan of each session is registered to the canonical reference with the real `register_repeat_scans` (:223-248). That function enforces the same project, scale and unit, and is rigid with no scaling. A registration that is not accepted fails closed (:235-240).
  - Extents are recomputed as T_ref_to_canon * T_scan_to_ref * points (:249-251).
  - The mutants that drop the cross-session transform, drop the within-session transform, accept a non-accepted registration, ignore initial_transforms, or take the canonical reference from the last session are all killed.
  - The V01 yaw probe is now a test (test :482-495): 1 and 3 deg give WITHIN with no drift, and 10 deg is refused with `cross_session_reference_registration_not_accepted`.
  - The determinism test with reversed input order still passes, including the registration step.
- **P2-1 (forgeable status): CLOSED.** `status` uses `field(init=False)` (:100). Passing it raises TypeError, and this is tested at test :704-707.
- **P3 items from V01: CLOSED.**
  - The MSB/N term in the SE has a known-answer test (test :264-269; the mutant is killed).
  - Each gate is tested in isolation (test :355-394; the mutants for the worst_r gate and the worst_R gate are killed).
  - Reuse of a revision_id is tested (test :655-663).
  - Object and session IDs are validated (:187, :194).
  - Thresholds and policy are type-checked (:176-179).
  - The scale error is renamed (:460).
  - SE = 0 is defined through the floor.
  - The doc states the in-sample tuning, seeds 0-299, the injection details and a reproduction command, and the procedure now matches the default of 2 repeats.

## Coordinator questions

### Is the `minimum_drift_shift` floor (0.05) acceptable? Yes, as a provisional value.
- It is an AND gate (:282-285): a session is flagged only if |shift| > 0.05 and also > k*SE. The floor can only suppress drift flags.
- It cannot produce a PASS by itself. A sub-floor shift still enters s_L, and s_L is still gated by maximum_reproducibility_sd (0.3). The configuration-change flags and the s_r gate are unaffected.
- 0.05 is one sixth of the s_R limit and 2.5 times the fixture s_r. It is a reasonable practical-significance floor, and it makes SE = 0 well defined.
- It is validated as finite and > 0 (:113, test :697) and recorded in the report thresholds under the fixed provisional status. The doc tables were re-measured with the floor in place, and my run reproduced them.
- Caveats:
  - It is an absolute value in the coordinate unit (mm_unverified), not relative to object size.
  - It must be confirmed under PL-0221.
  - The floor-only path is not tested (N-1).

### Is registration error feeding into s_L adequately disclosed? Mostly yes; quantification is recommended.
- The doc (:53-54) says that registration error goes into the between-session component and changes the axis-aligned extents to first order. That is correct and honest.
- The direction is conservative: s_L can only be inflated, so this error never produces a false PASS.
- Reviewer probe: real PL-0222 reports, 6 sessions x 3 scans, point noise 0.2 mm, true between-session effect 0, 8 seeds.
  - The cross-session alignments had residual rotations of 0.02-0.09 deg. On the 60 mm lever arm that is up to about 0.06 mm of extent change, which is the same order as the 0.05 floor.
  - Even so, s_L with registration was not systematically larger than with an identity transform: x/y/z s_L per seed differed by about 0-0.04 in both directions. The AABB extreme-value noise dominated.
  - With yaw 0 or 3 deg per session, the results were identical to 4 decimal places.
- The synthetic clouds share identical sample positions (the PL-0222 test GROUND_TRUTH grid). Real scans have independent sampling and partial coverage, so they will register worse. The ICP acceptance gate (inlier RMSE <= 1.0, fitness >= 0.8 under the PL-0222 test POLICY) does not bound the residual rotation tightly. See N-4 for the recommendation.

## Remaining notes (all P3, none blocking)

- **N-1: the floor-only path is untested.** The `floor_off` mutant survived (:282). Replacing the floor with False passes all 28 tests. The noise-free test (test :312-320) uses a 0.2 shift with SE 0, so the k*SE leg already decides the outcome. Suggested test: a noise-free 0.03 shift is not flagged, while a 0.07 shift is flagged.
- **N-2: the revision-ID set check is untested.** The `no_revset_bind` mutant survived (:403-406). With the check removed, supplying a superset of the revisions in the report is accepted silently. A missing revision then surfaces only as a reference lookup failure or a KeyError. Suggested test: one extra RegistrationRevision.
- **N-3: wrong error type for malformed transform values.** A NaN `transform_scan_to_reference` (in a re-hashed report) passes the reproduction check, because comparisons with NaN are False (:430-434). It then fails only at `_hash` with a plain ValueError (out-of-range float). A non-numeric entry raises ValueError from float() at :426. Both still fail closed and no report is produced, but they do not raise StationRepeatabilityError. Suggested fix: require finite values, or use `not (abs(a - b) <= tol)`.
- **N-4: provenance and quantification of the cross-session alignment.**
  - The reference_alignment record (:242-248) has no initial method and no initial transform. The initial transform is only hashed inside registration_id, which cannot be re-verified without the input revisions.
  - Unused or misspelled initial_transforms keys are ignored silently. For example, ("nope","x") is accepted.
  - The injected `adapter` is not recorded. This matches the PL-0222 precedent.
  - Recommendations:
    - Record whether an initial transform was supplied.
    - Reject keys that are not (session_id, object_id) pairs in the run.
    - Record the residual rotation angle of each alignment.
    - Add one doc sentence that registration error on real data is unquantified, and that s_L therefore bounds station drift from above.
- **N-5: binding strength.** Report-to-scan binding uses IDs, parent digests and reproduction of extents to 1e-9. It does not use a point-sample digest, because PL-0222 does not publish one per scan. This is consistent with the documented unkeyed-digest limit, so I accept it for v1.

## Items re-verified correct
- The ANOVA (:489-515) is unchanged from V01 and correct for unbalanced ISO 5725-2 designs.
- The drift SE (:518-533) is reasonable, and its MSB/N term is now pinned by a known-answer test.
- simulation_only true, physical_validation_status PHYSICAL_EVIDENCE_PENDING and physical_repeatability_claim false are hard-coded (:317-319). No input can change them, and mutants that change them are killed.
- Sessions are sorted by a unique UTC timestamp. The canonical reference is the reference scan of the earliest session, and the result does not depend on input order (tested).
- Reuse of the private PL-0222 internals (`_hash`, `_transform_point`, `_ACCEPTED`) is acceptable. `_hash` keeps the digests identical, and `_transform_point` and `_ACCEPTED` reuse the accepted registration semantics. `repeat_scan_reproducibility.py` already imports from the same module. Note: a future rename of `_ACCEPTED` would break this coupling at import time, not silently.
- Doc honesty: the doc calls the tuning in-sample on one synthetic configuration and states that the rates do not predict physical false-alarm rates. It discloses the symmetric-object limit and the canonical-pose dependence, and it makes no physical PASS claim.

## Disposition
SOFTWARE_PASS_WITH_NOTES for the software half of PL-0401. N-1 to N-4 are recommended follow-ups and do not block. Per the CLAUDE.md policy, PL-0401 itself must stay `[ ]` until real multi-session station evidence exists (physical half PHYSICAL_EVIDENCE_PENDING).
