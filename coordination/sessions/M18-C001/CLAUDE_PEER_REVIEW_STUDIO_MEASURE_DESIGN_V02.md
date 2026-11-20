# CLAUDE_PEER_REVIEW — Studio Measure & Design (PR #14) V02

- Reviewer: independent Claude peer reviewer (not the author)
- Fix diff reviewed: `904d3aa0..2c5cdc0e` (7 files, +201/-15)
- CI: `PackLab Windows Python Quality` run 44818099934, headSha 2c5cdc0e, conclusion success (checked with `gh run view`). Frozen build: not run, NOT_VERIFIED. Redistribution stays BLOCKED by the registry.
- Re-run evidence: all 51 `evidence_class` entries in the real test-333 Scan Master manifest are now `owner_unverified_print`.

## Verdict: PASS_WITH_NOTES

## V01 findings
- **M1 RESOLVED.** `core/.../calibration/reconstruction_scale.py:57-63` adds the `owner_unverified_print` class, and `measure_design.py:535-537` makes it the default. `promote_scale_provenance` still requires `accepted_owner_physical` references, and the new studio test asserts that promoting marker-scale and manual provenance is refused.
- **M2 RESOLVED for development use.** The register row and section now show SELECTED 5.1.0.95 with the wheel SHA, the FFmpeg DLL and LICENSE-3RD-PARTY hashes, and the LGPL note. The registry adds `supplemental_evidence` and `native_review` entries with status `UNRESOLVED_IF_NATIVE_FILES_STAGED`. The CI test asserts that the component inventories as UNRESOLVED and that the wheel SHA appears in `uv.lock`. Distribution still needs legal review; this PR does not approve it.
- **M3 RESOLVED.** Fixed constants: coverage >= 0.60, section CV <= 0.45, axis radial CV <= 0.05 (`measure_design.py:1144-1149,1258-1261`). The policy is hashed into the recommendation id. Tests cover refusal of an oval and of a quarter ring.
- LOW items: MANUAL_OVERRIDE negatives now cover missing actor, reason and previous revision. The digit-leading UUID project id is exercised end to end through `fit_design_model`. Design Model revisions are still not in project authority state; this stays open for PL-0447.

## Remaining notes (LOW)
- N1 A half ring of a truly round jar passes (coverage 0.68, CV 0.36). I accept this as an owner-reviewed assumption: axis roundness is still enforced, the assumption is recorded in notes, the policy hash and the zone-override reason, and everything stays METRIC_UNVERIFIED / DEFERRED. The 0.45 section-CV ceiling is loose, so coverage >= 0.60 is the effective guard.
- N2 `tests/studio/test_measure_design.py`: the promotion-refusal test uses `pytest.raises(ScaleProvenanceError)` without `match=`. The refusal could therefore come from another check, such as the placeholder `"a"*64` digest, rather than the evidence class. Add `match="..._accepted_owner_physical_evidence"`.
- N3 In the same test, the variable named `half` builds a quarter ring (cosmetic).
- V01 L1-L3, L6 and L7 still apply: UI-thread blocking, lineage digest taken from the built model, Design Model revisions outside authority state, print correction stored per machine, and the fit-vs-measurement gap.

## Limits
PL-0446 physical accuracy stays open until the mat is reprinted and the owner's caliper measurements exist. The synthetic tests are not physical evidence. This review is not an `AUDITED_PASS`.
