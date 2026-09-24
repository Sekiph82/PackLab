# PL-0092 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and all accepted M03 children preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Replace free-form SessionFinalizationRecord.state with a closed Codable enum or an equivalently closed decoder that rejects unknown states at decode time.
7. Preserve sessionID matching and exported package existence validation.
8. Add tests for a real SessionFinalizer-produced in_progress→exported transition, missing exported package, foreign session ID, unknown/corrupt finalization state, corrupt metadata, missing preview and deterministic ordering across multiple sessions.
9. Keep history derived only from authoritative local state.
10. Filesystem/UI tests cover the actual production mutation/recovery/destructive boundary.
11. Validation and git diff --check clean/truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
