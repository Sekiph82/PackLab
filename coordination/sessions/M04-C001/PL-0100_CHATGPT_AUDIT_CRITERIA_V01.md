# PL-0100 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M04-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03 remains accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits or start M05.
4. Existing M03 capture/sensor/session ownership is reused rather than duplicated.
5. PL-0100 implements the frozen task scope.
6. Create one authoritative quality decision model that combines sharpness, motion blur, highlight clipping, shadow clipping, framing and background metrics.
7. Decision must be deterministic and explainable with stable reason codes plus raw metric values; no black-box AI score.
8. Define policy for unavailable optional metrics, warning-only conditions, hard reject conditions and exact threshold boundaries.
9. Ensure a candidate cannot be marked ACCEPT when any configured hard-reject condition is present.
10. Add table-driven tests spanning combinations, precedence, unavailable metrics and boundary equality.
11. Tests exercise the actual production-used quality/runtime/persistence seam, not only a disconnected helper.
12. Thresholds/physical claims are truthful about whether owner/iPhone calibration occurred.
13. Relevant regression/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
