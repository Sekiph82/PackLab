# PL-0081 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Prior passing behavior is preserved.
5. Previous audit PL-0081_CHATGPT_AUDIT_V03.md is fully addressed.
6. Remove CoreMotionController or refactor it so it cannot create a second CoreMotionMotionService/CMMotionManager; only one physical MotionService instance may own device motion.
7. Bind accepted stills to MotionService's bounded records using the same capture monotonic timestamp/domain semantics as PL-0080 and persist MotionCaptureBinding.
8. Preserve attitude quaternion and rotation-rate evidence, unavailable/error state, and bounded buffering.
9. Add tests proving one-owner composition and accepted-still motion binding for available/stale/unavailable cases.
10. Tests exercise the actual production seam or its injected driver, not only a neighboring helper.
11. Regressions and git diff --check are clean/truthful.
12. Log records exact commits/files/results and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
