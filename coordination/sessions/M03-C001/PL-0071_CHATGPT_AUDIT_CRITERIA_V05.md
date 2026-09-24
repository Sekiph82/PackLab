# PL-0071 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and all previously accepted M03 children remain unregressed.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M04.
4. Batch-004 passing behavior is preserved.
5. PL-0071_CHATGPT_AUDIT_V04.md is fully addressed.
6. Keep the current selected-main-wide production composition and exact-once StillPhotoAdapterCore.
7. Add behavior tests against the injected StillPhotoDriver seam for missing-data completion, overlapping adapter requests, Task cancellation and explicit session-stop cancellation in addition to the already-covered success/duplicate/lens-mismatch cases.
8. Prove each terminal path resumes the pending continuation exactly once, clears it, and invokes cancelPhotoCapture only when appropriate.
9. Preserve original full-resolution bytes/dimensions and CameraRecoveryOwner binding.
10. Tests exercise the actual production-used seam or its injected driver, not a disconnected helper.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations, uses GitHub URLs for user-facing links, and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
