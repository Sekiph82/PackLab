# CLAUDE_PEER_REVIEW - PL-0437 software half - V03 (confirmation of V02 fixes)

Reviewer: an independent Claude Code source reviewer who did not implement this change. This is not a CHATGPT_AUDIT or a CODEX_PEER_REVIEW.
Base: HEAD d1ab06187dade39409c684be803edd8a09c6ee98 (main). The reviewed files are untracked: backend_benchmark.py, test_backend_benchmark.py and the PL-0437 operator procedure.

## Verdict: SOFTWARE_PASS_WITH_NOTES. Physical half: NOT_VERIFIED (no physical evidence exists).
No P1 or P2 findings remain open. The notes below are P3 items and disclosed limits.

## Checks I ran myself
- pytest on the backend-benchmark, physical-accuracy and neural-backend test files: 55 passed.
- ruff check core apps tools tests: clean.
- ruff format --check with line-ending auto: both reviewed files are formatted.
- mypy with the project config (300 files): clean.
- Golden digest on Linux (WSL Ubuntu, Python 3.14.4): sha256:09a830b1673541ae80aca36dbc5361bd36a323ae39c8c585ed356655c3a5bb84. This equals the test constant and the Windows value. macOS was not checked.
- probe3 re-run. Its fixture gives every sample one shared scan_id ("scan"), so all probes now collapse to one object per class and return NO_CHANGE. To check the other gates on their own, I also ran probe3b, a variant with a unique scan_id and measurement_id per sample.
- Mutation testing on scratch copies, run outside the repo pythonpath: 33 mutants (my V02 set plus four new ones).

## V02 findings
- **R2-1: RESOLVED within a disclosed heuristic limit.**
  - What changed: `_physical_object_keys` (:532-551) is a deterministic union-find over shared scan_id or measurement_id. It is used for per-object averaging (:436), for the `independent_objects` count (:452), and it is reported as `physical_object_key` (:442).
  - probe3 A2 and probe3b A3 test one object per class, recorded as 3 dimension samples that share a scan id. Both give NO_CHANGE_INSUFFICIENT with independent_objects=1.
  - Remaining limit: probe3b A2 records one object under unrelated scan and measurement ids. It is still counted as 3 objects and reaches RECOMMEND. This limit is disclosed in doc :215-216, and the reviewer checklist (doc :188-194) requires checking it. I accept that, because the record schema has no object identity field.
- **R2-2: RESOLVED.** DecisionRule minimums must now be strict ints, with a minimum of 2 (:140-143). The value 2.5 is rejected, and mutant M33 is killed.
- **R2-3: RESOLVED.** The per-object vs flattened-statistics test kills M24. The CLI size-guard test kills M25.
- **R2-5: RESOLVED.** Doc :103 now explains the zero-variance, bit-identical case. probe3b K, a bit-identical candidate, gives RECOMMEND, which is consistent with "equal or better" and is documented.
- **Other probe3b results, unchanged from V02:** RMS opt-out → RULE_NOT_MET. Degenerate baseline → NO_CHANGE_INSUFFICIENT. Descriptive keys are present. A deliberate forgery with renamed IDs and attested identities → RECOMMEND, which is the disclosed owner-attested trust boundary.

## Mutation results
31 of 33 mutants are killed, and all 31 stay killed when the golden-digest test is deselected. That includes M30 (no merge), M32 (merge on measurement only) and M33 (non-int rule minimum). Two survive:
- **M29**, the redundant `version == proxy.version` clause. Acceptable; the other proxy-identity checks cover it.
- **M31**, merge on scan_id only (the measurement_id merge path removed). See P3-1.

## Notes (P3)
- **P3-1** No test makes a measurement_id-only link merge two samples into one object (:545). Add one sample pair that shares only a measurement_id.
- **P3-2** The union-find is global across classes. A scan_id reused across classes would merge objects of different classes. This fails closed: it can only lower counts. Harmless.
- **P3-3** Carried over from V02 and unchanged:
  - the synthetic-ID guard is a name heuristic (disclosed);
  - running mypy on the test file alone shows unused-ignore warnings; tests/ is not in the configured or CI mypy scope.

## Still correct
- No code path changes the default: `production_default_changed` is a literal False, and mutant M28 is killed.
- METRIC_VERIFIED runs are rejected.
- Synthetic authorities, synthetic IDs and proxy identities cannot reach RECOMMEND.
- Output is deterministic and portable across Windows and Linux.
- The t upper bound is correct.
- The loaders re-validate the digest and content and fail closed.
