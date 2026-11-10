# Claude Peer Re-Review: PL-0423 Bounded Fit Optimizer Fix, V03

Date: 2026-11-10
Reviewer: independent Claude peer reviewer. I did not write the fix.
Mode: read-only. No edits to source, tests, docs or `TASKS.md`; no commit, push, stash, reset or branch switch. Probes and mutants ran from scratchpad scripts and a temporary copy (`core/src`, `schemas`, `tests/core`, `tests/fixtures`, `pyproject.toml`) that was deleted afterwards. This file is the only repository write and is left uncommitted.

## Scope

- Commit `451aa5f9` (local; `main` is ahead of `origin/main` by 2 at review time), responding to V02 (`coordination/sessions/M19-C002/CLAUDE_PEER_REVIEW_M19_AI_ASSIST_V02.md`): V2-1 (P2), V2-2, V2-3 (partial), V2-4.
- Read in full: `core/src/packlab_core/dimension_fit_proposal.py`, `tests/core/test_dimension_fit_proposal.py`, the V02 review, and the frozen criteria `coordination/sessions/M19-C005/PL-0423_VALIDATION_CRITERIA_V01.md`.
- Only importers of the module: its own test and `tests/core/test_m19_provenance_ids.py`.

## Commands and results

| Command | Result |
| --- | --- |
| `PYTHONPATH=core/src .venv/Scripts/python.exe -B -m pytest -q tests/core/test_dimension_fit_proposal.py` (criterion 9) | **15 passed** |
| same, plus `test_m19_provenance_ids.py` and `test_design_history.py` | **130 passed** |
| `ruff check core tests` | All checks passed |
| `ruff format --check --config "format.line-ending = 'auto'"` on the 2 changed .py files | Already formatted |
| `mypy core` | Success, 184 source files |
| `git diff --check 451aa5f9~1 451aa5f9` | Clean |
| Probe `probe_v03.py` (scratchpad) | Results below |
| Mutation `mutate_v03.py` (scratchpad, temp copy; unmutated copy passes) | **23 mutants: 14 killed (2 by timeout), 9 survived**. Of the survivors, 2 are equivalent and 7 are test gaps. |

## V2-1: closed

`_within_tolerance` (`dimension_fit_proposal.py:490-498`) steps each grid value toward the target with `math.nextafter` until `abs(v - t) <= tol`. This is the same predicate that acceptance uses at `:447`. The grid is built through it at `:283-293`.

Sweep over **26,426 (target, tolerance) pairs**: targets from 0.5 to 500, tolerances from 0.01 to 0.49 × target, with 1 to 4 decimals, seeded RNG plus a deterministic decimal grid.

| Check | Pre-fix formula | Fixed code |
| --- | --- | --- |
| Pairs with at least one grid value failing `abs(v - t) <= tol` | 11,616 | **0** |
| Values moved to the other side of the target | – | **0** |
| Pairs where values collapsed, became non-distinct or became unsorted | – | **0** (5 distinct, ordered values per axis) |
| Maximum `nextafter` steps taken | – | **1 ulp** |

**Termination.** Termination is guaranteed. `tolerance` is finite and greater than 0, and `nextafter` moves strictly toward `target`, where the difference is 0. Extreme inputs all terminate with finite, in-tolerance, positive values:

- `1e300 ± 0.99e300`
- `1.79e308 ± 1.7e308`: the sum overflows to `inf`, and one step brings it back to the largest float
- subnormals
- `tol = 1e-300`
- `tol = 0.9999999999999999 × target`

**End-to-end acceptance.** All of these used the real `_model()`, `create_dimension_fit_request`, the optimizer with `maximum_candidates=64`, and `accept_dimension_fit_proposal`:

- All 5 candidates for each of 3,000 sampled single-constraint pairs (**15,000 acceptances, 0 failures**). The successor parameter equals the candidate value.
- 300 two-constraint requests with the optimum at a corner of the endpoints (**7,500 acceptances, 0 failures**).
- The V02 reproduction, `1.0 ± 0.1` with the optimum at the upper bound: the best candidate is `1.0999999999999999` and is now accepted.

## V2-2: closed

| Input | Result |
| --- | --- |
| `maximum_candidates` set to `True`, `False`, `0`, `65`, `2.5`, `"8"`, `None` or `-1` | `maximum_candidates_invalid` |
| An evaluator returning a non-tuple, `None`, a 1-tuple, a 3-tuple or a list | `evaluator_result_invalid` |
| NaN, string or bool deviation, or an uppercase or `None` digest | Contract errors raised from `DimensionFitCandidate` |
| An evaluator returning a tuple subclass | Accepted. This is benign. |

Output is deterministic: identical digests across runs.

Evaluator exceptions still propagate without wrapping. That is acceptable, because they come from the caller's own callable.

## V2-3: partly closed

The new tests kill these mutants, which survived in V02:

- 625-bound removal, and raising the bound to 3125 (5 constraints, 0 evaluator calls asserted)
- the budget filter changed from `<=` to `<`
- keeping only 1 candidate
- the `maximum_candidates` range check

The optimizer's `isinstance(request)` check still survives (M21, below).

## V2-4: closed for the request

Acceptance at `:413-418` now requires both requests to be exactly `DimensionFitOptimizationRequest` and their `as_dict()` outputs to be equal. Probe results:

| Attempt | Result |
| --- | --- |
| Request subclass that overrides `__eq__`/`__ne__`, widened, returned by the backend | Rejected: `proposal_request_mismatch` |
| User passes a subclass request | Rejected |
| Request subclass that overrides `as_dict` to mimic the user's request | Rejected |
| Swapped evidence digest | Rejected |
| Echo of the proposal's request mutated after construction with `object.__setattr__` | Rejected. `as_dict` reflects the real fields. |
| Identical echoed copy | Accepted. The recorded `proposal_sha256` equals the genuine digest. |
| Proposal subclass combined with an eq-override request | Rejected |

**Can the recorded `proposal_sha256` reflect a forged request?** No. The digest is computed over `proposal.as_dict()`, whose `"request"` member is the exact-type request's `as_dict()`, and that output is now required to equal the user's. Every bound is still read from the user's object.

The residual edges are in P3 V3-2.

## Findings

### P0, P1 and P2

None.

### P3

**V3-1: no test runs an endpoint candidate through acceptance.**

- Where: `tests/core/test_dimension_fit_proposal.py:362-382`.
- The new regression test checks `abs(v - t) <= tol` inline. It never calls `accept_dimension_fit_proposal` on an endpoint candidate, which is the regression test V02 recommended.
- As a result, mutant M22 survives. M22 changes the acceptance predicate at `dimension_fit_proposal.py:447` from `>` to `>=`, so acceptance would reject every exact endpoint such as `107.0` for `102 ± 5`. If the acceptance predicate drifts like this, the optimizer and acceptance can disagree again with no failing test. That is the V2-1 class of problem.
- The code is correct: 22,500 end-to-end acceptances passed in the probe.
- Recommendation: in the parametrized test, accept the minimum and maximum grid candidates through `accept_dimension_fit_proposal`.

**V3-2: the V2-4 hardening is untested, and some binding edges remain.**

- Untested hardening (`:413-418`): mutants M13, M14, M15 (each or both exact-type checks dropped) and M16 (reverted to `proposal.request != request`) all survive. No test uses a request subclass that overrides `__eq__`. Recommendation: add one test that uses an eq-override subclass.
- Constraint subclasses: constraints are checked with `isinstance` only (`:98-103`). An exact-type request can therefore carry a `MeasuredParameterConstraint` subclass whose `as_dict` hides a widened tolerance.
  - The optimizer then proposes 50, 75, 100, 125 and 150 for `100 ± 1`.
  - Acceptance rejects every candidate except 100.0, because the bounds come from the user's request.
  - No widening is possible, but the hashed proposal holds out-of-tolerance candidates under a request serialization identical to the user's.
- Proposal subclasses (`:468`, `:479`): `proposal_sha256` is taken from `proposal.digest`. A `DimensionFitProposal` subclass that overrides `digest` was accepted with a recorded `proposal_sha256` of `"f"*64`.
- Negative zero: `maximum_deviation=-0.0` echoed against the user's `0.0` passes the `as_dict` comparison. The recorded digest then serialises `-0.0` and differs from the user-request proposal's digest. The two are semantically identical.
- All of these are in-process trust limits with no bound widening. Optional hardening:
  - compute the recorded digest as `_canonical_digest(DimensionFitProposal.as_dict(proposal))`, or require `type(proposal) is DimensionFitProposal`
  - require exact-type constraints
  - compare canonical digests rather than dicts
  - normalise `-0.0` in `_finite`

**V3-3: minor mutant survivors.**

- M11: changing `len(result) != 2` to `< 2` survives. A 3-tuple would then raise a raw `ValueError`, and no test uses a 3-tuple result.
- M21 (carried over from V02): the optimizer's `isinstance(request)` check (`:275`) is still untested.
- The code is correct in both cases (probed).

**V3-4: grid values can collapse at representational extremes (informational).**

- Grid points can coincide, giving distinct candidate IDs with identical values, in these cases:
  - when `tol` is below one ulp of the target (`1.0 ± 1e-300`)
  - at the float overflow edge (`1.79e308 ± 1.7e308`, which gives 4 distinct values)
  - for subnormal targets
- This is not caused by `_within_tolerance`, which never reduced distinctness in the realistic sweep.
- None of these are realistic for millimetre or reconstruction-unit dimensions.

**Carried over and unchanged:**

- V2-8 / criterion 7: the evaluator is supplied by the caller, and its deviation values are untrusted estimates.
- V2-5: the flag is declared but not consumed.

### Equivalent mutants (no action)

- M2: the loop test changed from `>` to `>=`. This is stricter but still correct.
- M6: `while` changed to `if`. The sweep never needs more than 1 ulp step. The `while` loop is the safer form.

## Mutation detail

| Status | Mutants |
| --- | --- |
| Killed | M1 (raw grid), M3 (step toward 0, timeout), M4 (step toward +inf, timeout), M5 (collapse to the target), M7 (bool check), M8 (int check), M9 (range up to 65), M10 (result check dropped), M12 (tuple isinstance check), M17 (`as_dict` comparison dropped), M18 (budget `<`), M19 (625 bound dropped), M20 (keep 1 candidate), M23 (bound raised to 3125) |
| Survived | M2 and M6 (equivalent); M11, M13, M14, M15, M16, M21 and M22 (test gaps, V3-1 to V3-3) |

## Frozen PL-0423 criteria, at prototype tier

| # | Status | Evidence |
| --- | --- | --- |
| 1 | Met | The request binds the model and Scan Master revisions plus geometry and deviation-evidence digests. Acceptance binds the exact-type user request through `as_dict` equality and checks for stale ancestry at `:419-424`. |
| 2 | Met | Unchanged: positive finite target and tolerance, tolerance less than the target, safe IDs. |
| 3 | **Now met** | The reference optimizer's values are finite, deterministic and distinct over the realistic range, and all lie within target ± tolerance under the acceptance predicate: 0 of 26,426 pairs fail. The deviation is finite, nonnegative, and no greater than the budget (inclusive, tested). |
| 4 | Met | Serialization unchanged: non-authoritative flags, no paths or raw geometry. |
| 5 | Met | Stale ancestry, missing or non-numeric parameters, out-of-bound candidates, budget breaches and unproposed candidates are all rejected (existing tests). |
| 6 | Met | The successor is created through `revise_design_model_revision`, with the same Scan Master binding, `DEFERRED_OWNER_VALIDATION` and `mold_use_authorized=False` (`test_acceptance_creates_immutable_deferred_successor_and_bound_record`). |
| 7 | Met | Deviation values are untrusted estimates (V2-8 disclosure). No claim of geometric validation. |
| 8 | Met | Stdlib only. No model, checkpoint or runtime. The commit touches 3 files and no dependencies. |
| 9 | Met | 15 passed. |
| 10 | Met | `git diff --check` is clean. The commit is local and makes no Actions, release or native-build claim. |

## Verdict

**PL-0423: PASS.** It is eligible for CLAUDE_PEER_AUDITED_PASS at prototype tier, with external gates pending. V2-1 is fixed and verified by a 26k-pair sweep and 22.5k end-to-end acceptances. V2-2 and V2-4 are closed in code. There are no P0, P1 or P2 findings. The P3 items (V3-1 to V3-4) are recommended follow-ups and do not block acceptance. V3-1, the test that runs an endpoint candidate through acceptance, is the most valuable of them.

**Still pending externally:**
- a real learned optimizer, model or checkpoint (licence review, pinned hash)
- a PackLab deviation-evaluator adapter
- physical and metric validation of accepted fits
- UI or pipeline wiring of `ai_assist_enabled`
