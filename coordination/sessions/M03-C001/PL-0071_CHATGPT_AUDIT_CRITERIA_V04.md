# PL-0071 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and PL-0070 remains accepted.
3. TASKS.md and ChatGPT audits are untouched by Codex; M04 is not started.
4. Prior Batch-003 passing behavior is preserved.
5. Previous audit PL-0071_CHATGPT_AUDIT_V03.md is fully addressed.
6. Create the production composition that constructs NextLevelStillCaptureAdapter from the deterministic PL-0070 main-wide CameraLensIdentity and the active NextLevel/session lens identity source.
7. Bind the adapter to CameraRecoveryOwner so interruption/session stop cancels the exact in-flight continuation once.
8. Add an injectable NextLevel photo-driver/delegate seam used by the adapter and behavior tests for success, missing data, duplicate callback, overlap, cancellation, selected-lens mismatch and session stop.
9. Preserve high-resolution original bytes/dimensions and exact-once completion.
10. Behavior tests drive the actual production seam or an injected driver used by that seam, not a disconnected helper.
11. Relevant regressions/project checks and git diff --check are truthful and clean.
12. Child log records exact commits/files/results/limitations and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final main source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
