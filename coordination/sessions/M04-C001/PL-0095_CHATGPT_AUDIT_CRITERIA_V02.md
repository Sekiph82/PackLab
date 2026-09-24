# PL-0095 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorization exists.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits by Codex and no M05 work.
4. V01 correct behavior is preserved.
5. Previous V01 audit is fully addressed.
6. Correct the motion status reason interpolation so stale/unavailable reason codes are stable and truthful.
7. Compose MotionBlurAnalyzer into the same production candidate runtime using the existing timestamp-aligned MotionCaptureBinding/MotionService evidence.
8. Publish motion-blur warnings/reasons through the live quality state/UI; unavailable motion alone must not hard reject a sharp frame.
9. Add tests for aligned/stale/missing motion, low/high rotation, sharp/blurred combinations and exact warning/high-risk thresholds at the runtime seam.
10. Tests drive the production-used M04 candidate runtime, not only a pure helper.
11. Relevant regression/project checks and git diff --check pass truthfully.
12. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.
