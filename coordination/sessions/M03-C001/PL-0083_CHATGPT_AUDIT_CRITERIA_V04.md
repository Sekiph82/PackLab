# PL-0083 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. No TASKS/audit edits by Codex and no M04 work.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0083_CHATGPT_AUDIT_V03.md is fully closed.
6. Preserve CaptureRuntimeViewModel's live 100 ms tracking refresh and TrackingRecoveryPolicy integration.
7. Add an injected ARTrackingService sequence/fake and tests against CaptureRuntimeViewModel proving limited/normal flapping requires the configured stable-frame hysteresis before pose eligibility/UI warning clears.
8. Prove tracking diagnostics accumulate across those real runtime refreshes and stop changing after runtime stop.
9. Keep production UI driven from the stabilized snapshot.
10. Tests hit the actual production-used seam or authoritative contract source.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log is complete and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
