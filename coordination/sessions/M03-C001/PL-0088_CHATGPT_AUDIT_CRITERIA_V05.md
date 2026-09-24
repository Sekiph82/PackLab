# PL-0088 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and all accepted M03 children preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Preserve the current previous-state rollback and partial-final-move recovery algorithm.
7. Add failure-injection tests for transaction.prepare, sourceStage, recordStage, stateStage, sourceCommit, recordCommit and stateCommit.
8. For every stage, reopen must yield either the fully accepted capture or the exact clean pre-capture state with no orphan source/record and consistent state.
9. Add malformed/missing transaction-marker recovery evidence and keep the canonical record format.
10. Tests cover actual production-used service/persistence/failure boundaries.
11. Validation and git diff --check clean/truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
