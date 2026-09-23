# PL-0073 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and PL-0070 remains accepted.
3. TASKS.md and ChatGPT audits are untouched by Codex; M04 is not started.
4. Prior Batch-003 passing behavior is preserved.
5. Previous audit PL-0073_CHATGPT_AUDIT_V03.md is fully addressed.
6. Connect the physical focus adapter's observed state to CaptureRuntimeViewModel.updateControlState so the visible focus UI reflects focusing/continuous/locked/unavailable/failure.
7. Use the selected CameraDeviceConfigurationCoordinator in the production focus-control composition and reject any non-selected device.
8. Add injectable adapter/device-state tests for wrong-device rejection, adjustingFocus→stable observation, lock-before-stable rejection, lock-after-stable success and UI state propagation.
9. Preserve serialized device configuration and current selected-lens rules.
10. Behavior tests drive the actual production seam or an injected driver used by that seam, not a disconnected helper.
11. Relevant regressions/project checks and git diff --check are truthful and clean.
12. Child log records exact commits/files/results/limitations and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final main source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
