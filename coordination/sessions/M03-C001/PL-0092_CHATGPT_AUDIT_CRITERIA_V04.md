# PL-0092 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0092_CHATGPT_AUDIT_V03.md is fully addressed.
6. Validate SessionFinalizationRecord.sessionID against the containing session and restrict state to a closed enum/known values.
7. For exported/finalized records, verify the referenced packagePath exists and is a valid file before reporting exported; otherwise retain a degraded row.
8. Add tests for actual in_progress→exported transition produced by SessionFinalizer, missing exported package, corrupt/foreign-session finalization record, corrupt metadata, missing preview and deterministic multi-session ordering.
9. Keep history preview-only and authoritative-state derived.
10. Filesystem/UI tests cover both success and injected partial/crash failure at the real production seam.
11. Relevant regressions and git diff --check are clean/truthful.
12. Child log records exact evidence and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
