# PL-0074 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and all previously accepted M03 children remain unregressed.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M04.
4. Batch-004 passing behavior is preserved.
5. PL-0074_CHATGPT_AUDIT_V04.md is fully addressed.
6. Use the same production AVFoundationCameraControlComposition as PL-0073 and bind its exposure state into CaptureRuntimeViewModel.
7. On accepted capture, obtain the observed ExposureCaptureReading from that selected coordinator and feed it through AcceptedPhotoMetadataFactory into the metadata that is actually persisted for the photo.
8. Add integrated tests for wrong-device rejection, bias clamp/lock, runtime UI propagation and persisted exposure/ISO source values.
9. Preserve schema-safe PackScan mapping and selected-device serialization.
10. Tests exercise the actual production-used seam or its injected driver, not a disconnected helper.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations, uses GitHub URLs for user-facing links, and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
