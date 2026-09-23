# PL-0087 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. No TASKS/audit edits by Codex and no M04 work.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0087_CHATGPT_AUDIT_V03.md is fully closed.
6. Preserve NewScanWizard's use of NewScanWorkflowModel and ContentView's real ScanSessionStore/ActiveScanSession handoff.
7. Extract the Start/Cancel action into a small testable coordinator used by the view, or otherwise make the actual callback seam directly testable.
8. Prove one valid Start calls onStart exactly once with normalized values, invalid Start calls it zero times and keeps visible validation state, and Cancel calls Start zero times.
9. Preserve all M02 capture-mode IDs and real session creation on successful Start.
10. Tests hit the actual production-used seam or authoritative contract source.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log is complete and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
