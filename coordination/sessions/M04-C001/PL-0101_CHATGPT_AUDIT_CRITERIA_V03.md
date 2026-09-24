# PL-0101 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. M04-BATCH-003 / READY / CODEX authorization exists before material work.
2. All 16 accepted M04 children remain unregressed; M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing production M04 integration is preserved.
5. PL-0101_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve production every-candidate logging and bounded/sanitized JSONL behavior.
7. Add a real filesystem test that writes malformed/corrupt quality-candidates.jsonl and proves snapshot/reopen fails with QualityLogStoreError.corruptLog.
8. Prove corrupt quality diagnostics do not mutate or corrupt canonical accepted-capture/session files.
9. Preserve accepted/rejected ordering and bounded trim behavior.
10. Tests exercise the actual production-used seam/state boundary.
11. Full declared suite, relevant project checks and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
