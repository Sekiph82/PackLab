# PL-0075 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and all previously accepted M03 children remain unregressed.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M04.
4. Batch-004 passing behavior is preserved.
5. PL-0075_CHATGPT_AUDIT_V04.md is fully addressed.
6. Use the same production AVFoundationCameraControlComposition and publish white-balance state into CaptureRuntimeViewModel.
7. Observe adjustingWhiteBalance until stable before lock, then feed only actual observed temperature/readings into AcceptedPhotoMetadataFactory for the accepted photo persistence path.
8. Add integrated tests for wrong-device rejection, unstable-lock rejection, stable-lock success, runtime UI propagation and persisted WB metadata.
9. Do not invent temperature, tint or gain evidence.
10. Tests exercise the actual production-used seam or its injected driver, not a disconnected helper.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations, uses GitHub URLs for user-facing links, and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
