# PL-0084 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. No TASKS/audit edits by Codex and no M04 work.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0084_CHATGPT_AUDIT_V03.md is fully closed.
6. Preserve the real SharedARSessionOwner reset/degradation/interruption logic.
7. Extract an injectable AR session driver/state callback seam used by the owner and test reset→relocalizing→recovered, reset→failed, repeated reset, degradation-threshold reset and interruption reset.
8. Prove old-epoch pose evidence is rejected after reset and reset diagnostics record reason/epoch/result from the real owner path.
9. Do not add another AR session owner.
10. Tests hit the actual production-used seam or authoritative contract source.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log is complete and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
