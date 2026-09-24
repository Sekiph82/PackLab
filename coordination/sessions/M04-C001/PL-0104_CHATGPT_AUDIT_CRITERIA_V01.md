# PL-0104 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing M03 camera/sensor/session ownership is reused.
5. PL-0104 satisfies the frozen scope.
6. Implement an auto-capture coordinator that requests a still only when pose eligibility, coverage target, overlap/parallax policy and PL-0100 quality gates are satisfied.
7. Use the existing health-gated production still-capture service and one camera/session owner; do not call NextLevel directly from a new path.
8. Prevent duplicate/in-flight auto-capture requests and define cooldown/rearm behavior after accepted or rejected candidates.
9. Manual capture must remain possible according to PL-0110 without corrupting auto-capture state.
10. Add deterministic tests for each gating reason, exact thresholds, overlap, cooldown, duplicate requests and recovery.
11. Tests exercise the production-used coverage/auto-capture/session seam.
12. No unavailable/synthetic pose is represented as physical coverage.
13. Relevant regressions/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
