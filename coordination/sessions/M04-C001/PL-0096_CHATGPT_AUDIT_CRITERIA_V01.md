# PL-0096 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M04-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03 remains accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits or start M05.
4. Existing M03 capture/sensor/session ownership is reused rather than duplicated.
5. PL-0096 implements the frozen task scope.
6. Implement deterministic luminance/highlight clipping analysis on candidate frames with explicit clipping percentage/statistics.
7. Support glossy packaging where small specular highlights may be tolerated but broad clipping must warn/reject according to configurable thresholds.
8. Keep analysis independent from camera exposure-lock control while consuming existing capture metadata when useful for diagnostics.
9. Expose explainable reasons and raw metrics for later tuning.
10. Add tests for no clipping, localized highlights, broad clipping and exact threshold boundaries.
11. Tests exercise the actual production-used quality/runtime/persistence seam, not only a disconnected helper.
12. Thresholds/physical claims are truthful about whether owner/iPhone calibration occurred.
13. Relevant regression/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
