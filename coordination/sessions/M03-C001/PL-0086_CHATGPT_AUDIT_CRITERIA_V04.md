# PL-0086 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. No TASKS/audit edits by Codex and no M04 work.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0086_CHATGPT_AUDIT_V03.md is fully closed.
6. Preserve explicit units, basis_conversion and malformed-data rejection.
7. Add golden tests using realistic Windows/macOS user paths, bearer/API-token-like strings and user-identifying path fragments through the same DiagnosticsSanitizer boundary used by PoseDiagnosticsExporter.
8. Add exact maximumRecords and maximumRecords+1 tests proving bounded export behavior.
9. Verify sanitized output contains no original private path/user/token fragments while valid capture IDs and deterministic ordering remain stable.
10. Tests hit the actual production-used seam or authoritative contract source.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log is complete and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
