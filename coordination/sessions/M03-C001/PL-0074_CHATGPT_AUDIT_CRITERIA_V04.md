# PL-0074 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and PL-0070 remains accepted.
3. TASKS.md and ChatGPT audits are untouched by Codex; M04 is not started.
4. Prior Batch-003 passing behavior is preserved.
5. Previous audit PL-0074_CHATGPT_AUDIT_V03.md is fully addressed.
6. Connect physical exposure adapter state to CaptureRuntimeViewModel controls using the selected CameraDeviceConfigurationCoordinator.
7. On accepted still, propagate observed ExposureCaptureReading through AcceptedPhotoMetadataFactory and persist the resulting exposure/ISO source values in the actual accepted-photo metadata transaction.
8. Add integrated tests for wrong-device rejection, clamp/lock state, UI propagation and accepted-photo metadata persistence.
9. Preserve actual device readings only and the existing schema-safe metadata mapper.
10. Behavior tests drive the actual production seam or an injected driver used by that seam, not a disconnected helper.
11. Relevant regressions/project checks and git diff --check are truthful and clean.
12. Child log records exact commits/files/results/limitations and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final main source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
