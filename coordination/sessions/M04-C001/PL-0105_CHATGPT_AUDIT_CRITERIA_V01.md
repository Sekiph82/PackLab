# PL-0105 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing M03 camera/sensor/session ownership is reused.
5. PL-0105 satisfies the frozen scope.
6. Implement deterministic near-duplicate detection using accepted pose/coverage and, where useful, lightweight visual similarity signals.
7. Define configurable angular/translation/similarity thresholds and explicit duplicate reason codes.
8. Never delete prior accepted source images automatically; reject/prevent only the new redundant candidate.
9. Ensure missing/stale pose evidence fails safely and does not incorrectly mark useful frames as duplicates.
10. Add tests for exact duplicates, useful parallax, same-angle different elevation, stale pose and threshold boundaries.
11. Tests exercise the production-used coverage/auto-capture/session seam.
12. No unavailable/synthetic pose is represented as physical coverage.
13. Relevant regressions/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
