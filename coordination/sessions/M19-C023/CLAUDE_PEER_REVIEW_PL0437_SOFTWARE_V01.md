# CLAUDE_PEER_REVIEW - PL-0437 software half - V01

Reviewer: independent Claude Code source reviewer (non-implementing). This is not a CHATGPT_AUDIT or CODEX_PEER_REVIEW.
Base: HEAD d1ab06187dade39409c684be803edd8a09c6ee98 (main). The reviewed files are untracked working-tree files:
core/src/packlab_core/backend_benchmark.py, tests/core/test_backend_benchmark.py, docs/development/PL-0437_BENCHMARK_OPERATOR_PROCEDURE.md.
Spec: docs/implementation/PL-0437_RECONSTRUCTION_BACKEND_BENCHMARK.md.
Scope: SOFTWARE COMPLETE / PHYSICAL VALIDATION PENDING only. No physical evidence exists or was assessed.

## Verdict: FAIL (CHANGES_REQUIRED). Physical half: NOT_VERIFIED (no evidence exists).

## Reviewer-run commands
- pytest tests/core/test_backend_benchmark.py tests/core/test_physical_accuracy_benchmark.py tests/core/test_neural_reconstruction_backend.py: 38 passed.
- ruff check core apps tools tests: all checks passed.
- ruff format --check with format.line-ending=auto: both reviewed files are already formatted. Local ruff 0.16.8 flags 59 pre-existing tracked apps files, which are unrelated.
- mypy (pyproject config, 300 files): no issues.
- Golden digest on Linux (WSL Ubuntu, Python 3.14.4): b7ad3551...f6d9. This is identical to the Windows/3.12.10 value. macOS was not verified.
- t-table checked against numerically integrated Student-t quantiles for df 1..30: every value is within 0.001.
- Mutation testing on scratch copies, run outside the repo pytest pythonpath. Results are below.

## P1
P1-1 backend_benchmark.py:402-404 and :535-539. A candidate can switch off a pre-registered deciding metric by omitting it.
- If any case in a class has surface_deviation_rms_mm=None, from either backend, the whole class metric becomes NOT_MEASURED.
- NOT_MEASURED adds no rule reason.
- Probe: the candidate was 5.0 mm RMS worse in every case but omitted the value in one case per class. The decision was RECOMMEND_DEFAULT_CHANGE_PENDING_ADR.

Fix: when the baseline reported the value, treat a missing candidate value as FAIL or as an evidence gap. Otherwise remove the metric from the margins.

## P2
P2-1 backend_benchmark.py:322-324, :352-383, :466-487. "Minimum 3 cases per class" counts rows, not independent objects or capture sets.
- Neither physical_sample_id nor capture_set_id has to be unique.
- Probe: 30 cases bound to only 3 physical samples, all sharing capture_set_id "same-capture", gave RECOMMEND.
- This pseudo-replication shrinks sd/sqrt(n) and breaks the independence assumption behind the t bound.

Fix: require a distinct capture_set_id per case. Also report and gate the number of distinct physical samples per class.

P2-2 Relabelling to RECOMMEND can be reproduced from public inputs alone, using the CLI.
- Steps: take the synthetic_proxy_inputs() runs, set ground_truth_authority to PHYSICAL_CALIPER in the JSON, and build a READY_FOR_AUDIT record with invented caliper values. The record_digest is an unkeyed sha256 that anyone can recompute.
- The CLI (--input/--physical-record) then gives RECOMMEND_DEFAULT_CHANGE_PENDING_ADR.
- In that run the backend version is still "synthetic-proxy", the licence is "proxy-license" and the case IDs are SYN-*.
- The claim that synthetic or proxy input can only ever yield NO_CHANGE_INSUFFICIENT_PHYSICAL_EVIDENCE (module docstring :8-9, doc :34-36) depends only on the label. It is not a provenance guarantee.
- The test helper _physical() (test :26-60) follows exactly this reproducible path.

Fix: add a precondition failure for synthetic_proxy_provenance identities, for version "synthetic-proxy", and for SYN-/synthetic- case and capture IDs. Also state in the doc that physical binding is self-attested and that an independent reviewer must check it against real evidence.

P2-3 Spec, Decision rule: "equal or better PackLab acceptance metrics".
- The implementation is a margin-based non-inferiority rule. The candidate may be worse by up to 0.5 mm MAE, 0.002 scale ratio, 0.02 coverage and 0.5 mm repeatability.
- The margins are not tied to the PackLab acceptance thresholds.
- This is a defensible reading of the spec, but the doc does not flag it as an interpretation. Doc :135-136 only calls them engineering choices.

Fix: record the interpretation for owner or ADR sign-off.

P2-4 The doc overclaims what the report contains. Doc :59-61 says runtime, RAM, VRAM and point/triangle counts are "reported".
- The report JSON contains none of: runtime_seconds, peak RAM or VRAM, point or triangle counts, hole_count, floating_component_count, failure_diagnostic.
- These values reach the report only through runs_digest (:434). The case aggregates (:542-547) leave them out.
- The spec "Record" list is therefore met only by the archived input file.

Fix: add per-case aggregates to the report, or correct the doc.

P2-5 Test discrimination. These mutants survive the whole test file:
- removing the physical_record_digest check (:475);
- removing the candidate band-failure rule reason (:375);
- removing the record_status check (:473; the test only catches it indirectly, through the digest change);
- removing the sample category check (:480);
- removing the ground_truth_id check (:483);
- treating a failed baseline case as comparable (:372);
- removing the loader content-equality check (:721);
- removing the ACCEPTED/ground_truth check (:478).

Two more mutants are killed only by the golden-digest test:
- deleting the synthetic-authority gate (:469). The synthetic-only test still passes because record=None blocks it anyway; no test pairs a synthetic label with a valid record.
- replacing the t upper bound with the mean (:406).

Fix: add one targeted negative test per binding gate, plus a borderline case where the mean passes but the upper bound fails.

## P3
- P3-1 :255. operator_interventions=None passes validation, then evaluate crashes with TypeError at :540.
- P3-2 :73. An integer value such as 10**400 raises OverflowError instead of BackendBenchmarkError.
- P3-3 :657. A non-object payload such as [] raises a raw AttributeError outside the try block.
- P3-4 :717. PhysicalBenchmarkError is not wrapped. Input size is unbounded and the case-by-run loop at :359 is O(cases x runs). This is fail-closed and acceptable for a local owner tool.
- P3-5 :56-60. The 3-decimal t-table is anti-conservative by at most 0.0004 for some df. This is negligible. Using the df=30 value for df>30 is conservative.
- P3-6 :304-308. "Pinned" only means hash-shaped values plus a single identity. The fake proxy tags qualify. This is acceptable as a declared pin, but the doc should say that nothing is verified against binaries.
- P3-7 Baseline runs are not band-checked, so a degenerate baseline inflates the candidate deltas. The candidate absolute bands still apply.
- P3-8 license_clearance_ref is only a token and is not cross-checked against license_record. The ADR and Scan Master review are static reminder strings, not evidence.

## Verified OK
- The classes equal the PL-0221 categories. All six spec dimensions are present, with body_diameter optional.
- Speed and size metrics never decide.
- No path changes the default: production_default_changed is the literal False and the CLI writes only to --out or stdout.
- METRIC_VERIFIED runs are rejected.
- The output is deterministic and does not depend on input order.
- The t upper bound formula and its indexing are correct.
- The loader re-validates the physical record digest and full content equality.
