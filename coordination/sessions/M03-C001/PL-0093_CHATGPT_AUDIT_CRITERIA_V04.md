# PL-0093 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0093_CHATGPT_AUDIT_V03.md is fully addressed.
6. Make SafeSessionDeleter.delete(plan:confirmed:) inspect DeletionReport and throw/report partialFailure whenever failures are non-empty; no deletion API may silently return success on partial failure.
7. Preserve authoritative candidate requirement and real UI detailed failure reporting/history cleanup.
8. Add real temporary-filesystem symlink-escape tests plus missing-session, cancellation, traversal, injected session failure and injected history-index failure tests.
9. Ensure destructive behavior never follows or deletes outside-root symlink targets.
10. Filesystem/UI tests cover both success and injected partial/crash failure at the real production seam.
11. Relevant regressions and git diff --check are clean/truthful.
12. Child log records exact evidence and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
