# PL-0093 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and all accepted M03 children preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Preserve authoritative candidate checks, partial-failure throwing and symlink/root protection.
7. Add public-API tests for deleting an already-missing session and define the exact expected failure/report semantics.
8. Add injected history-index write/read failure tests proving delete()/deleteDetailed() never report full success when history cleanup fails.
9. Retain cancellation, traversal, session failure and real symlink escape coverage.
10. Filesystem/UI tests cover the actual production mutation/recovery/destructive boundary.
11. Validation and git diff --check clean/truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
