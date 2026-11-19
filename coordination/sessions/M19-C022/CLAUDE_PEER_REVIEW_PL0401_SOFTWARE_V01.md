# CLAUDE_PEER_REVIEW - PL-0401 software half (V01)

Reviewer: independent Claude source reviewer (non-implementing; no edits to the files under review, no git writes).
Base: `main` HEAD `d1ab0618`. The files under review are untracked working-tree files:

| File | SHA-256 |
| --- | --- |
| core/src/packlab_core/station_session_repeatability.py | 0aaa0793cf5105ef20f1db69b67172d98ceb10104b365b991375fd487e8594f3 |
| tests/core/test_station_session_repeatability.py | 2a9d16aa34a028a9adf9ccc8da927373adfde6ce1909b614c539c1d6a436b16b |
| docs/development/PL-0401_STATION_REPEATABILITY_PROCEDURE.md | 5a305b29a20e3a502afa7085a864ed470502a2c8d04f1e5ce11559e9e707b5b7 |

**Verdict: FAIL (CHANGES_REQUIRED)**, because of one P1 finding about how the method works. The ANOVA arithmetic, the fail-closed paths and the simulation labelling are correct. This review covers software only. Physical validation stays PHYSICAL_EVIDENCE_PENDING whatever the verdict.

## Commands run by the reviewer (Windows, Python 3.12.10, .venv)

- pytest tests/core/test_station_session_repeatability.py tests/core/test_repeat_scan_reproducibility.py: 26 passed.
- ruff check core apps tools tests: all checks passed.
- ruff format --check with line-ending auto on both new .py files: already formatted.
- mypy core/src/packlab_core/station_session_repeatability.py: no issues.
- I ran 24 mutations, each on a temp copy of the module that was injected through a pytest plugin. The repo was not touched. 20 were killed and 4 survived (see P3-1).
- I wrote my own probes for: forging the threshold status, the false-alarm and detection rates, pose dependence of the reference scan, and PII in object IDs.

## Findings

### P1-1: Cross-session axis extents depend on the pose of the PL-0222 reference scan in each session
station_session_repeatability.py:166-180 and 204. PL-0222 computes `extents` as axis-aligned bounding-box (AABB) extents. It does this after registering each scan to the reference scan of that report, which defaults to `scans[0]` (repeat_scan_reproducibility.py:95, 144-148). Each session therefore reports x/y/z in the frame of its own reference scan. PL-0401 pools these values across sessions as if they shared one axis frame, and nothing registers the frame of one session to that of another.

The end-to-end test (test file :212-226) hides the problem because local scan 0 is axis-aligned in every session. Reviewer probe: real PL-0222 reports, 5 sessions x 3 scans, the same synthetic box with no scale change. The only change is that the reference scan of session s2 is yawed:

| Reference yaw | Result |
| --- | --- |
| 0 deg | WITHIN, s_R 0.000 |
| 1 deg | EXCEEDS: session_mean_drift on s2 with x +1.03 and y +1.74 (unit: mm_unverified), s_R 0.776 |
| 3 deg and 10 deg | raises object_identity_extent_mismatch |

A physical operator cannot re-place an object to better than 1 deg across days, and doc step 2 tells the operator to re-place it. On real data, the between-session component and the drift flags would mostly measure placement pose, not the station. The failure is conservative: it gives false EXCEEDS or a raise, never a false PASS. Still, the only purpose of the tool is to estimate s_L, and the doc does not mention this precondition.

Required fix, choose one:
- (a) Register the reference scan of each session to one canonical per-object reference before taking extents. register_repeat_scans can be reused for this.
- (b) Require and validate a canonical per-object reference pose or fixture, then add a test with a rotated reference.

At minimum, the doc must state the precondition and the test suite needs a rotated-reference case.

### P2-1: The threshold status can be forged by the caller
station_session_repeatability.py:78 and 254. status is a free field that is never validated. StationRepeatabilityThresholds(status="ACCEPTED_PL-0221") is accepted, and the report then carries thresholds.status = "ACCEPTED_PL-0221" with WITHIN_PROVISIONAL_THRESHOLDS (reviewer probe). This contradicts doc line 74, "All thresholds are PROVISIONAL_PENDING_PL-0221". Fix: reject any status other than the constant, or remove the field from init (field(init=False)).

### P3-1: Test discrimination gaps (surviving mutations)
- Removing the MSB/N term from the drift SE (:393): survived. No test pins the SE value.
- Removing only the worst_r gate (:238), or only the worst_reproducibility gate (:239): each survived. test_repeatability_threshold_alone_can_fail (test :189) exceeds both gates at once, so it does not isolate the repeatability gate as its name says. A case where only s_R fails, with s_r inside its threshold and no drift, is missing.
- Removing the revision_id reuse check (:331): survived. Only provenance reuse is tested.

Killed mutations include MSW and MSB degrees of freedom, n0, zero-truncation, the reproducibility formula, between-variance in the SE, drift off, configuration-change detection off, forcing simulation_only and the claim, removing the sort, removing the used-scan filter, and the identity/reuse/project/relative-scale/mixed/physical-status/UTC/timestamp guards.

### P3-2: Object IDs are not validated
:158-162. Session IDs and metadata must match _REFERENCE, but object-report keys do not. An object ID of "Jane Doe <jane@x.com>" was accepted and written to object_ids. Comment :48 says only pseudonymous references are allowed. Non-str keys would also raise TypeError rather than StationRepeatabilityError.

### P3-3: The tuning on fixtures is under-stated, and one figure is slightly optimistic
doc :76-89. I reproduced the false-alarm figures exactly with seeds 0-299: 5 sessions 1.33 %, 6 sessions 3.0 %, 12 sessions 0.67 %. For detection of a 0.1 shift injected into s2, I measured 83 % at 5 sessions, 84 % at 6 and 92 % at 12. The doc says "about 85-93 %", so the 5-session figure is a little high.

The doc does not say three things:
- k=5 and min-sessions=5 were selected on this same single synthetic configuration (s_L/(s_r/sqrt(n)) about 1, Gaussian).
- The rates are in-sample and do not predict physical false-alarm rates.
- The seed range, the shifted session and the harness are not given. No script is committed to reproduce them.

Suggested fix: add one sentence on the in-sample selection, plus the seed range and how the injection was done.

### P3-4: Minor issues
- The thresholds argument is not type-checked (:143). A duck-typed object only fails late, with TypeError from asdict. It still fails closed.
- str(item.session_id) (:151) lets a non-str ID through. For example, the int 5 would end up in the report.
- The error name relative_scale_repeatability_forbidden (:323) is also used for any state that is not METRIC_UNVERIFIED.
- Doc step 2 says "at least 3" scans, but the default minimum_repeats_per_session is 2. The procedure could set the threshold to match.
- When SE = 0, any non-zero shift is flagged and k_standard_errors is None (:208-218). This only matters for degenerate input and is acceptable.

## Items verified correct
- **Variance decomposition:** MSW = SSW/(N-k), MSB = SSB/(k-1), n0 = (N - sum n^2/N)/(k-1), s_L^2 = max(0, (MSB-MSW)/n0), s_R^2 = s_r^2 + s_L^2 (:352-378). These match ISO 5725-2 for unbalanced designs. Known answers were checked independently: balanced data give MSW 1, MSB 27 and n0 3. Division by zero is impossible, because at least 2 repeats are required and at least 3 sessions, so there are at least 2 groups after leaving one out.
- **Drift SE** (:381-396): Var(session mean) = s_L^2 + s_r^2/n_i, plus the variance of the observation-weighted grand mean of the other sessions, approximated by MSB/N. That is exact in expectation for balanced data. The unbalanced approximation and the normal-style k are documented (doc :116-117). The SE is reasonable. The heavy tails with 4 remaining sessions are disclosed.
- **Fail-closed paths:** every listed guard raises, and is exercised by tests or by my mutations. simulation_only True, physical_validation_status and physical_repeatability_claim False are hard-coded (:248-250). No input can change them. The inputs themselves must be simulation_only and PENDING (:313-317).
- **Determinism and order independence:** sessions are sorted by a unique UTC timestamp and objects by ID, and the test with reversed input passes. Drift and flag order is deterministic.
- **Reuse of private _hash and PL-0222 internals:** acceptable. repeat_scan_reproducibility.py:27 already imports _hash from the same module, so this follows existing precedent and keeps digests identical. Note that report_digest_valid is generic: it checks the digest, not the contract. Consumers must check contract themselves.
- **Doc honesty, apart from P1 and P3-3:** the doc clearly states that this is simulation only, that thresholds are provisional, that unkeyed digests are used, that only extents are decomposed, and that drifted sessions are not removed. It does not claim a physical PASS.

## Disposition
FAIL / CHANGES_REQUIRED for the software half. The blocking item is P1-1. P2-1 should be fixed in the same pass. The P3 items are recommended. Re-review is needed after the fixes. PL-0401 must stay unchecked, with physical validation PHYSICAL_EVIDENCE_PENDING.
