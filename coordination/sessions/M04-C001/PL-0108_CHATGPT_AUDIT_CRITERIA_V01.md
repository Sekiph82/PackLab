# PL-0108 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing M03 camera/sensor/session ownership is reused.
5. PL-0108 satisfies the frozen scope.
6. Define an optional bottom/base detail pass that is only marked required/available when physically feasible under the selected capture workflow.
7. Never fabricate bottom coverage when the object cannot safely be tilted/raised or the view is unavailable.
8. Use explicit pass metadata and the same quality/pose/session persistence pipeline.
9. Expose skip/unavailable reason codes separately from completed coverage.
10. Add tests for feasible completion, unavailable/skipped state, partial sectors and no-false-complete behavior.
11. Tests exercise the production-used coverage/auto-capture/session seam.
12. No unavailable/synthetic pose is represented as physical coverage.
13. Relevant regressions/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
