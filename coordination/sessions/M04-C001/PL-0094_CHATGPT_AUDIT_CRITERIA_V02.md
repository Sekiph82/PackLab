# PL-0094 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorization exists.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits by Codex and no M05 work.
4. V01 correct behavior is preserved.
5. Previous V01 audit is fully addressed.
6. Correct the sharpness reason-code interpolation so produced codes are stable `sharpness_accept`, `sharpness_warn`, `sharpness_reject` rather than the current literal placeholder.
7. Wire SharpnessAnalyzer into the production M04 candidate-frame runtime fed by the existing camera preview/candidate analysis seam; do not create a second camera owner.
8. Keep thresholds configurable/provisional and preserve SharpnessCalibrationHarness truthfulness.
9. Add deterministic tests for sharp, mildly blurred, strongly blurred, unavailable and exact accept/warn boundaries, plus runtime propagation into CandidateQualityMetrics.
10. Tests drive the production-used M04 candidate runtime, not only a pure helper.
11. Relevant regression/project checks and git diff --check pass truthfully.
12. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.
