# PL-0101 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M04-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03 remains accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits or start M05.
4. Existing M03 capture/sensor/session ownership is reused rather than duplicated.
5. PL-0101 implements the frozen task scope.
6. Persist quality metrics and decision/reason codes for every candidate frame, including rejected candidates and accepted stills.
7. Bind logs to capture/session identity and monotonic capture timing without modifying immutable source image bytes.
8. Use bounded/structured diagnostics suitable for later Windows tuning and privacy rules; no private path/token leakage.
9. Make logging crash-safe enough that a rejected candidate does not corrupt accepted-session state.
10. Add tests for accepted/rejected candidate logging, ordering, bounded growth, resume/reopen and privacy sanitization.
11. Tests exercise the actual production-used quality/runtime/persistence seam, not only a disconnected helper.
12. Thresholds/physical claims are truthful about whether owner/iPhone calibration occurred.
13. Relevant regression/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
