# PL-0089 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0089_CHATGPT_AUDIT_V03.md is fully addressed.
6. Wire AcceptedFrameGalleryView Retake to an actual retake callback/capture workflow instead of message-only behavior.
7. Make delete and retake use a recoverable transaction that atomically coordinates files, PersistedSessionState and gallery audit history.
8. On any mutation failure, recover to either the complete old state or complete new state with no orphan files/records and no false acceptedIDs.
9. Add filesystem/UI-action tests for delete confirmation, retake execution, transaction failures, ordering, missing source/preview and corrupt records.
10. Filesystem/UI tests cover both success and injected partial/crash failure at the real production seam.
11. Relevant regressions and git diff --check are clean/truthful.
12. Child log records exact evidence and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
