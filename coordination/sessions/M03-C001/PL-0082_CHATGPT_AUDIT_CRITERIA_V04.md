# PL-0082 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. No TASKS/audit edits by Codex and no M04 work.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0082_CHATGPT_AUDIT_V03.md is fully closed.
6. Keep the existing numeric X/Y/Z rotation goldens, inverse/round-trip behavior and basis constant.
7. Add an authoritative contract fixture or mechanically generated test input sourced from schemas/packscan/pose.schema.json and assert coordinate convention, basis_conversion and metre unit constants against it.
8. Fail the test if the schema contract drifts from Swift constants rather than comparing only duplicated literals.
9. Preserve fail-closed invalid matrix behavior.
10. Tests hit the actual production-used seam or authoritative contract source.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log is complete and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
