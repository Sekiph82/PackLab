# CLAUDE_PEER_REVIEW - PL-0437 software half - V02 (re-review of V01)

Reviewer: independent Claude Code source reviewer (non-implementing). Not a CHATGPT_AUDIT or CODEX_PEER_REVIEW.
Base: HEAD d1ab06187dade39409c684be803edd8a09c6ee98 (main). The reviewed files are still untracked:
- core/src/packlab_core/backend_benchmark.py (864 lines)
- tests/core/test_backend_benchmark.py (521 lines)
- docs/development/PL-0437_BENCHMARK_OPERATOR_PROCEDURE.md (187 lines)

Scope: SOFTWARE COMPLETE / PHYSICAL VALIDATION PENDING. I have not taken the implementer's figures on trust; every result below comes from my own runs.

## Verdict: SOFTWARE_PASS_WITH_NOTES. Physical half: NOT_VERIFIED (no evidence exists).
No P1 remains. One residual P2 (R2-1) must be resolved, at minimum in the doc, before any physical benchmark is run or accepted.

## Reviewer-run commands
- pytest on test_backend_benchmark.py, test_physical_accuracy_benchmark.py and test_neural_reconstruction_backend.py: 51 passed.
- ruff check core apps tools tests: clean. ruff format --check (line-ending auto): both files formatted.
- mypy with the project config (core/src, apps, tools; 300 files): clean.
- Golden digest on Linux (WSL Ubuntu, Python 3.14.4): sha256:ee7aa507e382ffc0b09cd2738371acf2286b23e5a0c2b5840fc59c66bfdbc90f. This matches the test constant and the Windows/3.12 value. macOS was not checked.
- probe.py and probe2.py (V01) were re-run unchanged. probe3.py (new) and mut2.py (29 mutants) ran on scratch copies, outside the repo pytest pythonpath, and each mutant was confirmed to import from the scratch copy.

## V01 findings: status

| V01 finding | Status | Evidence |
| --- | --- | --- |
| P1-1 RMS opt-out | RESOLVED | :449-453. A missing deciding metric now gives NOT_MEASURED plus the rule reason `{class}:{metric}_not_measured`. In probe3 B and B2, omitting RMS in one case, or everywhere, gives NO_CHANGE_RULE_NOT_MET. |
| P2-1 pseudo-replication | PARTIAL, see R2-1 | Duplicate capture_set_id raises (:356-358). Deltas are averaged per physical_sample_id (:429-430, :448-454). The minimum counts objects (:444-445). The V01 probe of 3 samples × 10 cases now gives NO_CHANGE_INSUFFICIENT (independent_objects=1). Reusing one capture set raises. |
| P2-2 public relabel | RESOLVED as scoped | The V01 CLI forgery now gives NO_CHANGE_INSUFFICIENT_PHYSICAL_EVIDENCE (synthetic_identifier_on_physical_path). The proxy backend identity is blocked (:323-333, :473-474). A deliberate forgery with renamed IDs and attested-looking identities still gives RECOMMEND (probe3 E). The module docstring (:9-13), the report `physical_binding_semantics` field and the doc trust-boundary section (:27-46) now say this honestly. |
| P2-3 spec "equal or better" | RESOLVED | New rule pl0437-equal-or-better-v1 with every margin 0. The upper bound must be ≤ 0. Positive margins are documented as a non-inferiority reinterpretation that needs owner/ADR sign-off (:119-124; doc :88-94). |
| P2-4 non-deciding metrics missing from report | RESOLVED | Per-case `descriptive` block and `failure_diagnostics` (:612-626). probe3 D confirms the keys are present. |
| P2-5 test discrimination | RESOLVED | 26 of 29 mutants are killed, and those 26 are still killed with the golden-digest test deselected. Every V01 survivor is now killed, including the synthetic-authority gate and mean-vs-upper-bound. Survivors are listed under R2-3. |
| P3-1 interventions None | RESOLVED | :262-263. |
| P3-2 overflow | RESOLVED | :80-87; the bound is < 2**63 at :274. |
| P3-3 non-object payload | RESOLVED | :753-754 and :788-789. |
| P3-4 error wrapping and size | RESOLVED | ValueError/OverflowError are wrapped. Limits: MAX_INPUT_BYTES 16 MiB (:827), MAX_CASES 10k, MAX_RUNS 200k (:354). Runs are grouped by case (:391-393). JSON Recursion/Decode/Unicode errors are wrapped (:831). |
| P3-6 "pinned" semantics | RESOLVED | The `backend_pin_semantics` report field and doc :42-44 say "declared, not verified". |
| P3-7 baseline bands | RESOLVED | A baseline band failure is now an evidence gap (:415-418). probe3 C gives NO_CHANGE_INSUFFICIENT. |
| P3-8 licence/ADR strings | RESOLVED (doc) | The `license_clearance_ref_semantics` field and doc :45-46 and :24-25 cover this. |
| P3-5 t-table rounding | UNCHANGED, acceptable | Every value is within 0.001 of the true quantile. |

## New / residual findings

### P2
R2-1 backend_benchmark.py:429 (object_key) and :444. Independence is still keyed on physical_sample_id, which is not an object identity.
- The PL-0221 record holds one caliper dimension per sample (doc Limits :177-179). So one physical object can legitimately appear as several ACCEPTED samples, for example one for height, one for max_width and one for max_depth.
- Probe3 A2 tested this. Per class, it used one physical object recorded as 3 samples, each with a different caliper dimension_id and the same scan_id "scan", plus 9 cases with distinct capture sets. Each class reported independent_objects=3 and the result was RECOMMEND_DEFAULT_CHANGE_PENDING_ADR.
- This is a plausible honest-owner workflow, not only a forgery. The doc (:67-68) implies "sample = object" but never states it as a requirement.
- Minimum fix: state in the doc that each physical object must have exactly one ACCEPTED sample in the record, and add it to the reviewer checklist.
- Better fix: add an explicit object identity, or reject records in which two ACCEPTED samples of one class share a scan_id or measurement_id.

### P3
- R2-2 :127-128, :139-143. DecisionRule accepts a non-integer min_cases_per_class or min_repeats_per_backend (2.5 is accepted). These should be ints.
- R2-3 Test gaps, from the mutants that survive:
  - Flattening cases instead of averaging them per object (:454) is not detected. The repeated-object test uses one sample per class, so the minimum-object gate fires either way.
  - The MAX_INPUT_BYTES file-size guard (:827) is untested.
  - Removing `version == proxy.version` (:327) survives. That clause is redundant with the other proxy checks, so this is acceptable.
- R2-4 _SYNTHETIC_ID (:59) is a name heuristic. Variants such as SYNTH-01, SYN01, Synthetic1-01 and fake-01 pass it. A legitimate licence string with a "proxy" segment (for example lic:proxy-server) is blocked. Doc :40-41 and :184-185 disclose both, which is acceptable.
- R2-5 A bit-identical candidate (sd=0, mean=0, upper bound 0) gives RECOMMEND. That is consistent with "equal or better". Doc :90-91 ("statistically indistinguishable ... does not pass") is accurate only for candidates with any variance; a short clarification would help.
- R2-6 Running ad hoc `mypy tests/core/test_backend_benchmark.py` reports 10 unused "type: ignore" comments. tests/ is outside the configured and CI mypy scope (CI runs `mypy core apps tools`), so nothing is gating. This is cosmetic.

## Verified OK (re-checked)
- No code path writes a production default. `production_default_changed` is the literal False, and the mutant that makes it conditional is killed. PRODUCTION_DEFAULT_BACKEND is a constant, and the CLI writes only to --out or stdout.
- METRIC_VERIFIED runs are still rejected.
- Synthetic and public-proxy authorities, synthetic-looking IDs, and the proxy identity cannot reach RECOMMEND.
- The output is deterministic and independent of input order. The golden digest is portable across Windows/3.12 and Linux/3.14.
- The t upper bound formula, indexing and per-object aggregation are correct.
- The loader re-validates the physical record digest and full content equality.
