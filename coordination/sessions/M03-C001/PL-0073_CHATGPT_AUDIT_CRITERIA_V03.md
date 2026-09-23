# PL-0073 — ChatGPT Remediation Audit Criteria V03

Task: **PL-0073 — Focus selected-device/live-state remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_V02.md

All criteria mandatory.

1. M03-BATCH-003 / READY / CODEX authorization exists before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED.
3. PL-0070 remains accepted and unregressed.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. No M04 work starts.
6. No secrets/signing/private assets/caches enter public Git.
7. Previous passing behavior is preserved.
8. The prior independent audit is fully addressed.
9. Make the selected main-camera identity and shared CameraConfigurationCoordinator mandatory for the physical focus adapter path.
10. Reject arbitrary/non-selected AVCaptureDevice configuration.
11. Observe real autofocus/adjustingFocus stabilization before allowing lock and expose focusing/locked/unavailable/failure state through the real capture UI/view model.
12. Add tests for wrong-device rejection, stabilization-before-lock, serialized configuration and visible state transitions.
13. New tests exercise the actual integrated seam, not a disconnected helper only.
14. Relevant M01/M02/M03 contracts remain unregressed.
15. Available validation is run truthfully.
16. git diff --check and protected-file checks pass.
17. Child log maps each prior failure to code/tests and records exact commits/results.
18. Actual GitHub source/diff/tests/log are consistent and no material finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
