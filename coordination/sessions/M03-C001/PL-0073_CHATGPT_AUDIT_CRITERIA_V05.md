# PL-0073 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and all previously accepted M03 children remain unregressed.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M04.
4. Batch-004 passing behavior is preserved.
5. PL-0073_CHATGPT_AUDIT_V04.md is fully addressed.
6. Create the production camera-control composition at the same selected main-wide device used by capture and call CaptureRuntimeViewModel.bindCameraControls with AVFoundationCameraControlComposition.controls.
7. Ensure focus configure/observe/lock commands used by the app flow operate only through that selected coordinator and publish their real state into the runtime UI.
8. Add injected/conditional tests for wrong-device rejection, adjusting→stable observation, lock-before-stable failure, lock-after-stable success and CaptureRuntimeViewModel state propagation.
9. Do not add a parallel focus owner or bypass the shared coordinator.
10. Tests exercise the actual production-used seam or its injected driver, not a disconnected helper.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations, uses GitHub URLs for user-facing links, and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
