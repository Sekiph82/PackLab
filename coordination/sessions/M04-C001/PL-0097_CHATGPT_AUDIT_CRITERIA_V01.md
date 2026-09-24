# PL-0097 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M04-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03 remains accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits or start M05.
4. Existing M03 capture/sensor/session ownership is reused rather than duplicated.
5. PL-0097 implements the frozen task scope.
6. Implement deterministic dark-pixel/shadow clipping analysis with configurable luminance and affected-area thresholds.
7. Distinguish intentionally dark background from object-region underexposure where possible using the framing/object-region signal available in the quality pipeline.
8. Expose raw metrics plus explainable warning/reject reasons.
9. Do not invent physically calibrated thresholds without labeled owner/device evidence; keep them configurable and fixture-tested.
10. Add tests for normal exposure, localized dark regions, broad underexposure and threshold boundaries.
11. Tests exercise the actual production-used quality/runtime/persistence seam, not only a disconnected helper.
12. Thresholds/physical claims are truthful about whether owner/iPhone calibration occurred.
13. Relevant regression/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
