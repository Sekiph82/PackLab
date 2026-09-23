# PL-0075 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and PL-0070 remains accepted.
3. TASKS.md and ChatGPT audits are untouched by Codex; M04 is not started.
4. Prior Batch-003 passing behavior is preserved.
5. Previous audit PL-0075_CHATGPT_AUDIT_V03.md is fully addressed.
6. Connect physical white-balance adapter state to CaptureRuntimeViewModel controls using the selected CameraDeviceConfigurationCoordinator.
7. Observe adjustingWhiteBalance until stable before lock; on accepted still propagate observed temperature through AcceptedPhotoMetadataFactory into persisted photo metadata.
8. Add integrated tests for wrong-device rejection, unstable-lock rejection, stable-lock success, UI propagation and accepted-photo metadata persistence.
9. Do not invent temperature/tint/gain values.
10. Behavior tests drive the actual production seam or an injected driver used by that seam, not a disconnected helper.
11. Relevant regressions/project checks and git diff --check are truthful and clean.
12. Child log records exact commits/files/results/limitations and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final main source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
