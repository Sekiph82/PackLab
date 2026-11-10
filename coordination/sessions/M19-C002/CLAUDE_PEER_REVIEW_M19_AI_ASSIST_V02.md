# Claude Peer Re-Review: M19 AI-Assist Fixes (PL-0421 to PL-0424), V02

Date: 2026-11-10
Reviewer: independent Claude peer reviewer. I did not write the fixes.
Mode: read-only. I made no edits to source, tests, docs or `TASKS.md`, and no commit, push, stash, reset or branch switch. All probes and mutants ran against scratchpad scripts or a temporary copy that was deleted afterwards.

## Scope

- Reviewed commit `4aaa8cc8`, which responds to `CLAUDE_PEER_REVIEW_M19_AI_ASSIST_V01.md` (F-1..F-11).
- HEAD at review time was `731262fa`. `git diff 4aaa8cc8 HEAD -- core tests` touches only unrelated scan-copy, texture and signing tests, so the reviewed files are identical at HEAD.
- Files read in full:
  - `core/src/packlab_core/dimension_fit_proposal.py`
  - `core/src/packlab_core/reconstruction_anomaly.py`
  - the acceptance path of `package_family_suggestion.py`
  - the provenance and ordering guards of `profile_zone_proposal.py`
  - the `config.py` diff
  - every new or changed test
  - the implementation log `CLAUDE_IMPLEMENTATION_LOG_M19_AI_ASSIST_FIXES_V01.md`
  - the frozen criteria in M19-C003..C006
  - TASKS lines 830-833

## Commands and results

| Command | Result |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen PYTHONPATH=core/src .venv/Scripts/python.exe -B -m pytest -q` on the 4 M19 test files plus `test_config.py` and `test_m19_provenance_ids.py` | **154 passed** |
| `ruff check core apps tools tests` | All checks passed |
| `ruff format --check --config "format.line-ending = 'auto'"` on the 11 changed files | Already formatted |
| `git diff --check 4aaa8cc8~1 4aaa8cc8` | Clean |
| `mypy core apps tools` | Success, 288 source files |
| `gh run list --branch main` (read-only) | Windows Python Quality `42889760029` on `731262fa` (which contains `4aaa8cc8`) **succeeded: 2832 passed, 16 skipped**. Signing guard `42889760013` succeeded. |
| Probe script (scratchpad `probe_v02.py`) | Results below |
| Mutation script (scratchpad `mutate_v02.py`, temp copy of `core/src`, `schemas` and `tests/core`; the unmutated copy passes 154) | **38 mutants: 31 killed, 7 survived** |

## Status of the prior findings

| Prior finding | Status | Evidence |
| --- | --- | --- |
| **F-1 P1** PL-0423 acceptance trusted the request echoed by the backend | **Closed** | See below. |
| **F-2** PL-0424 incomplete topology was reported as clean | **Closed** | See below. |
| **F-3** provenance IDs accepted paths and control characters | **Closed** | See below. |
| **F-4** OTHER→X acceptance failed | **Closed** | `package_family_suggestion.py:261` sets `updated_other_label = None`. The new test passes, the source asset is unchanged, and the mutant that removes the clear is killed. |
| **F-5** no feature flag or fallback | **Acceptable at prototype tier**, with a disclosure condition (V2-5) | See the F-5 judgement section. |
| **F-6** no actual optimizer | **Substantively addressed**, but the new optimizer has a correctness bug (V2-1) | See the F-6 judgement section. |
| **F-7** 8 surviving mutants | **Closed** | All 6 non-redundant survivors from V01 are now killed. The 2 redundant ones (zone digest, scan-master ancestry) were accepted in V01. New survivors are listed in V2-3. |
| **F-8, F-9, F-10** (P3) | Open, disclosed in the log as not addressed | Acceptable at prototype tier. |

**F-1 detail.** `dimension_fit_proposal.py:398-403` now requires the user's request and enforces `proposal.request == request`. All of the bounds that follow (budget at 415, constraint set at 417-420, tolerance at 432) read the user's `request`, not `proposal.request`. Adversarial probes:
- A plain widened echo is rejected with `proposal_request_mismatch`.
- `request=None` and a dict are both rejected with `user_request_required`.
- An equal copy built with `replace(user)` is accepted, which is correct.
- `maximum_deviation` of -0.0 versus 0.0 compares equal. That is semantically identical, so nothing is widened.
- A **request subclass overriding `__ne__`/`__eq__`**, or a constraint subclass with `__eq__ = True`, does bypass the equality check. A widened candidate is still rejected (`candidate_outside_measured_dimension_tolerance`), because the bounds come from the user's object (see V2-4).
- Mutating the user's own request object in place with `object.__setattr__` is accepted. That is an inherent limit of in-process trust, not a regression (V2-4).
- Mutants that remove the equality check, or remove it and read bounds from `proposal.request`, are both killed.

**F-2 detail.**
- Real point-cloud statistics from `compute_geometry_statistics` now give `REVIEW_REQUIRED` with `mesh_topology_evidence_incomplete` (evidence `connected_component_count,boundary_edge_count,nonmanifold_edge_count`).
- Empty topology, a None component count, bool counts, float counts, negative counts and string counts are all incomplete.
- `IntEnum` counts are handled as ints, which is correct.
- Inputs are not mutated.
- Mutants that accept bool, negative or float, drop the finding, or drop a missing key are killed, except the nonmanifold-missing key (V2-3).

**F-3 detail.**
- The pattern is `_PROVENANCE_ID` with `fullmatch` and ASCII (`dimension_fit_proposal.py:28`, `package_family_suggestion.py:28`, `profile_zone_proposal.py:25`).
- Probes rejected: `/`, `\`, `..`, tab, newline, NUL, non-ASCII, fullwidth characters, more than 160 characters, empty strings and a leading dash.
- All 6 provenance mutants are killed: the old check in each of the 3 modules, `/` allowed, length 200, and `match` instead of `fullmatch`.
- Residual edge cases are noted in V2-6.

## Findings

### P2

- **V2-1 (PL-0423): the reference optimizer emits grid endpoints that its own acceptance rejects.**
  - Where: `dimension_fit_proposal.py:279-285` against `:432`.
  - The grid values are `target + tol*(2*step/4 - 1)`. At the endpoints, float rounding makes `abs(value - target)` exceed `tol`. Example: `31.0 ± 0.3` gives 30.7 and 31.3, and both fail `abs(v - t) > tol` (31.3 - 31.0 = 0.3000000000000007).
  - Probe across 3848 realistic (target, tol) pairs (targets 1.0-300.0 mm, tolerances 0.05-2.0): **22.3% produce at least one unacceptable grid point**.
  - End to end, `target=1.0, tol=0.1` with the optimum at the upper bound: the optimizer's top candidate `height=1.1` is rejected at acceptance with `candidate_outside_measured_dimension_tolerance`.
  - It fails closed, so there is no authority risk. But the optimizer proposes values outside "each explicit target ± tolerance" by the module's own predicate (criterion 3), and the legitimate path "accept the best proposal" is broken for common inputs. This is the same class of problem as V01 F-4, which was P2.
  - The existing test misses it because 102±5 and 31±3 happen to be exact in binary.
  - Fix: after computing each grid value, keep it only if it passes the same predicate acceptance uses (or clamp it, for example with `math.nextafter` toward the target). Add a regression test with a non-representable case such as 31.0±0.3 or 1.0±0.1 whose best candidate sits at an endpoint and is then accepted.

### P3

- **V2-2 (PL-0423): the optimizer has robustness gaps.**
  - `maximum_candidates=True` is accepted and treated as 1, and `2.5` raises a raw `TypeError` (`:277`, `:304`).
  - An evaluator that returns a non-2-tuple raises a raw `TypeError`/`ValueError` (`:295`).
  - Evaluator exceptions propagate unwrapped.
  - Deviations that are NaN, negative, bool, `10**400` or inf, and digests that are malformed or uppercase, are all correctly rejected through `DimensionFitCandidate` with contract errors.
  - The grid bound behaves correctly: 4 constraints run 625 evaluations, and 5 constraints are rejected **before any evaluation**.
  - The output is deterministic: identical digests across runs.
  - The budget boundary is inclusive and consistent with acceptance: deviation equal to the budget is kept and accepted.
- **V2-3: 7 mutants survived.**
  - These survived:
    - Removing the optimizer's 625-evaluation bound check (`:286`). This is the "bounded" guarantee and has no test.
    - Changing `<=` to `<` in the optimizer budget filter (`:299`). The boundary has no test.
    - Removing the `maximum_candidates` range check (`:277`).
    - Keeping only 1 candidate instead of `maximum_candidates` (`:304`).
    - Removing the optimizer's `isinstance(request)` check (`:275`).
    - Removing the acceptance `user_request_required` isinstance check (`:398`). This one is effectively equivalent, because `proposal.request != None` still rejects.
    - Removing `nonmanifold_edge_count` from the incomplete-evidence list (`reconstruction_anomaly.py:128`).
  - The code is correct in every case (probed). Only the tests are missing. Recommended: a test with 5 constraints that asserts zero evaluator calls, a test with deviation equal to the budget, a candidate-count test, and a test with nonmanifold missing.
- **V2-4 (PL-0423): request binding uses `==` on caller-held objects.**
  - A backend can return a request subclass with an overridden `__eq__`/`__ne__`, or a constraint subclass. Equality then passes, and `acceptance.proposal_sha256` records the digest of the forged request.
  - The bounds are still enforced from the user's object, so no widening is possible.
  - In-place mutation of the user's request by in-process code is out of scope for an in-process contract.
  - Hardening options: require `type(proposal.request) is DimensionFitOptimizationRequest` (and the same for constraints), or compare `proposal.request.as_dict()` with `request.as_dict()`. This is the same theme as V01 F-9 (binding by digest).
- **V2-5 (F-5): the feature flag is declared but nothing consumes it.**
  - `AppConfig.ai_assist_enabled` defaults to False. TOML requires a strict bool. The environment variable accepts only case-insensitive `true`/`false`; `" true"`, `on`, `0` and `1` are rejected. The environment overrides TOML.
  - All 5 config mutants are killed.
  - A grep shows no reader outside `config.py` and its test. The four modules do not check the flag, and there are still no callers in `apps/` or the pipeline.
  - Judgement: acceptable at prototype tier. The flag is default-off and validated, there is no wired invocation path, and the fallback (the manual workflow) is untouched because every proposal API is non-mutating until explicit acceptance.
  - Condition: the tracker or acceptance note must state "flag declared, not yet consumed; any future UI or pipeline caller must gate on `ai_assist_enabled` and test the disabled path". PL-0424 "before fitting" wiring into `captured_geometry_fit_gate` also remains future work.
- **V2-6: residual edge cases in the provenance regex.**
  - `C:weights.pt` (a Windows drive-relative path form) and `file:x` (URI-like) are accepted.
  - They contain no directory separators or user names, so the privacy risk is negligible.
  - Optional: reject `^[A-Za-z]:` and `://`-style schemes if strictness matters.
- **V2-7 (PL-0424): residual malformed-input handling. This continues V01 F-8 and was disclosed as not addressed.**
  - Raw `TypeError`/`ValueError` errors:
    - `topology_indicators=None` raises a raw `TypeError` (`:117`).
    - Non-pair indicator tuples raise a raw `ValueError` (`:117`).
    - A string `hole_report_linkage[3]` raises a raw `TypeError` (`:165`).
  - Inputs ignored silently, giving a clean result:
    - `hole_report_linkage` of the wrong length or with a negative count (`:165`).
    - `connected_component_count=0`.
    - `geometry_kind="point_cloud"` carrying mesh-style topology (`geometry_kind` is never checked).
  - `GeometryStatistics` does not validate these fields itself. They are reachable only through hand-built or `replace()`d statistics, not through `compute_geometry_statistics`, so this is P3.
  - Recommend routing the linkage count through `_count`, and treating malformed linkage as incomplete.
- **V2-8 (PL-0423, F-6 scope note): the deviation evaluator comes from the caller.**
  - No PackLab evaluator adapter is shipped, for example one built on `design_deviation_report.calculate_design_deviation_report` plus model regeneration.
  - Deviation values therefore remain untrusted estimates, as criterion 7 already states.
  - This is acceptable at prototype tier if the tracker says so.

## Judgements requested

- **F-5 (feature flag/fallback):** reasonably satisfied at prototype tier, subject to the disclosure condition in V2-5. A default-off validated flag, no registered backend or caller, and an unchanged manual path together form a defensible "flag/fallback" for library-only contracts. It is not a runtime-enforced gate, so the tracker must not claim one.
- **F-6 (optimizer):** `BoundedGridFitOptimizer` is a genuine, bounded, deterministic, stdlib-only optimizer. It searches a 5-step grid inside each measured tolerance, filters by the request's scan-deviation budget, caps evaluations at 625 and candidates at 64, and its result goes through the same user-request-bound acceptance into `revise_design_model_revision`. At prototype tier that satisfies "fit-parameter optimizer constrained by measured dimensions and scan deviation", **once V2-1 is fixed**. Physical and metric validation stays external.

## Per-criterion deltas since V01

- **PL-0421:**
  - Criterion 1 (no paths) now passes (F-3).
  - Criterion 5 now passes, including OTHER→X (F-4).
  - The OTHER label rejection is tested.
  - Weak digest binding (F-9) remains P3.
- **PL-0422:**
  - Criterion 1 now passes (F-3).
  - Criterion 2 ordering is tested and its mutant killed.
- **PL-0423:**
  - Criteria 1, 2, 5 and 7 now pass in substance (F-1). The user request is bound, and the deviation evidence digest is bound through request equality.
  - Criterion 4 now passes (F-3).
  - **Criterion 3 fails for the shipped reference optimizer on about 22% of realistic inputs (V2-1).**
- **PL-0424:**
  - Criteria 2 and 4 now pass for missing or malformed mesh topology produced through the real statistics path (F-2).
  - The nonmanifold, hole-report and `not_evaluated` rules are tested.
  - Residual P3 items are in V2-7.

## Verdicts

| Task | Verdict | Notes |
| --- | --- | --- |
| **PL-0421** | **PASS** (prototype tier; eligible for CLAUDE_PEER_AUDITED_PASS; external gates pending) | Record the V2-5 flag disclosure. P3: V2-6, F-9. |
| **PL-0422** | **PASS** (prototype tier; eligible for CLAUDE_PEER_AUDITED_PASS; external gates pending) | Record the V2-5 flag disclosure. P3: V2-6, F-9. |
| **PL-0423** | **CHANGES_REQUIRED** (narrow) | Fix V2-1: optimizer grid values must satisfy the acceptance tolerance predicate, with a regression test on a non-representable bound. Strongly recommended in the same change: the V2-3 tests for the 625 bound and the budget-equality boundary. P3: V2-2, V2-4, V2-8. |
| **PL-0424** | **PASS** (prototype tier; eligible for CLAUDE_PEER_AUDITED_PASS; external gates pending) | Record V2-5, including that the "before fitting" wiring is future work. P3: V2-7, V01 F-8/F-10. |

**Externally pending regardless of these verdicts:**
- Any real learned model or checkpoint. This needs owner-approved data, code and checkpoint licence review, and a pinned hash.
- Physical or metric validation of accepted fits. Successors stay `DEFERRED_OWNER_VALIDATION`.
- Validation of the anomaly detector on real PackScan captures.
- UI or pipeline wiring of the flag.
