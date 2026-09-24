# PL-0099 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M04-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03 remains accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits or start M05.
4. Existing M03 capture/sensor/session ownership is reused rather than duplicated.
5. PL-0099 implements the frozen task scope.
6. Implement a deterministic background-complexity metric that warns about busy/feature-confusing setups without treating the product itself as background.
7. Use a bounded image-analysis strategy appropriate for live mobile evaluation and avoid heavy reconstruction/segmentation dependencies.
8. Return explainable metrics and warning reason(s); background complexity alone should follow the frozen policy for warning versus reject rather than hidden heuristics.
9. Keep matte/simple background guidance compatible with packaging presets.
10. Add tests for clean matte background, moderate texture, highly cluttered background and unavailable/object-mask cases.
11. Tests exercise the actual production-used quality/runtime/persistence seam, not only a disconnected helper.
12. Thresholds/physical claims are truthful about whether owner/iPhone calibration occurred.
13. Relevant regression/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
