# PL-0106 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing M03 camera/sensor/session ownership is reused.
5. PL-0106 satisfies the frozen scope.
6. Define standard-bottle orbit requirements for lower, middle and upper rings using the PL-0102 coverage model.
7. Make required sectors/ring counts explicit and configurable rather than hidden in UI code.
8. Completion must require all mandatory ring coverage, not just total frame count.
9. Expose missing-ring guidance to the UI and logging pipeline.
10. Add tests for each ring incomplete/complete, uneven coverage and boundary-sector assignment.
11. Tests exercise the production-used coverage/auto-capture/session seam.
12. No unavailable/synthetic pose is represented as physical coverage.
13. Relevant regressions/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
