# PL-0078 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Prior passing behavior is preserved.
5. Previous audit PL-0078_CHATGPT_AUDIT_V03.md is fully addressed.
6. Compose HealthGatedStillPhotoBackend (or equivalent) into the real production still-capture service and feed it the same live CaptureAdmissionController updated by DeviceHealthMonitor.
7. Ensure hardStop prevents the physical capture request before NextLevel capturePhoto is called, warning still allows capture, and recovery to ready re-enables capture.
8. Keep DeviceHealthMonitor start/stop tied to capture runtime lifecycle and preserve simulator unavailable semantics.
9. Add integrated tests proving provider update→runtime admission→physical backend call/no-call behavior.
10. Tests exercise the actual production seam or its injected driver, not only a neighboring helper.
11. Regressions and git diff --check are clean/truthful.
12. Log records exact commits/files/results and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
