# PL-0073 — ChatGPT Remediation Audit Criteria V06

Task: **PL-0073 — Focus physical-adapter evidence closure**

All criteria are mandatory.

1. M03-BATCH-006 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and all 22 accepted M03 children remain unregressed.
3. Codex does not edit TASKS.md or ChatGPT audits and does not start M04.
4. Existing Batch-005 production camera composition is preserved.
5. PL-0073_CHATGPT_AUDIT_V05.md is fully addressed.
6. Introduce the minimum production-used injectable camera-device-control driver/protocol beneath AVFoundationFocusAdapter/CameraDeviceConfigurationCoordinator so the same production path can be exercised without a physical iPhone.
7. Preserve the current selected main-wide CameraDeviceConfigurationCoordinator and runtime CameraControlRuntimeBridge composition.
8. Add behavior tests for non-selected-device rejection, configure→adjusting focus, observed stable focus, lock-before-stable failure, lock-after-stable success, serialized configuration use, and CaptureRuntimeViewModel focus-state propagation.
9. The injected fake must exercise the same adapter logic used by the AVFoundation device wrapper; do not create a test-only parallel policy that bypasses the production adapter.
10. Tests drive the production-used injectable device-control seam rather than a disconnected pure helper.
11. Focused/relevant regressions and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations and uses full GitHub URLs in user-facing links.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
