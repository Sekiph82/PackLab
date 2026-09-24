# PL-0095 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M04-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03 remains accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits or start M05.
4. Existing M03 capture/sensor/session ownership is reused rather than duplicated.
5. PL-0095 implements the frozen task scope.
6. Combine image-domain blur evidence with existing timestamp-aligned MotionService rotation-rate evidence.
7. Define a deterministic warning decision that distinguishes image blur with low motion, high motion with acceptable sharpness, stale/unavailable motion data and combined high-risk blur.
8. Use accepted M03 timestamp semantics and never align wall-clock values directly to CoreMotion monotonic timestamps.
9. Expose warning reason(s) to capture runtime/UI without silently rejecting on unavailable motion alone.
10. Add tests for aligned/stale/missing motion, high rotation, low/high blur and threshold boundaries.
11. Tests exercise the actual production-used quality/runtime/persistence seam, not only a disconnected helper.
12. Thresholds/physical claims are truthful about whether owner/iPhone calibration occurred.
13. Relevant regression/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
