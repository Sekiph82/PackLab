# PL-0101 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits; no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Call QualityCandidateLogStore from the real candidate runtime for every analyzed candidate, including rejected candidates and accepted candidates.
7. Bind each log to the active session/capture/sequence and monotonic candidate time without mutating immutable source bytes or accepted session state.
8. Ensure reopen/resume continues a bounded ordered log and rejected-candidate logging cannot corrupt the canonical accepted-capture transaction.
9. Add tests for accepted and rejected entries, ordering, max-record trimming, fresh-store reopen, corrupt-log fail-closed behavior and realistic privacy sanitization.
10. Tests hit the production-used quality/coverage/capture seam.
11. Validation/git diff/privacy checks are truthful and clean.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
