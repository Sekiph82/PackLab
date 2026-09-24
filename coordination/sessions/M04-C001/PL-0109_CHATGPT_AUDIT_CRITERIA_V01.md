# PL-0109 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing M03 camera/sensor/session ownership is reused.
5. PL-0109 satisfies the frozen scope.
6. Compute a deterministic completion score from mandatory rings/detail passes and quality-qualified accepted coverage.
7. Score must not hide mandatory missing sectors; provide explicit missing-area reason/guidance alongside any percentage.
8. Differentiate complete, incomplete, unavailable-evidence and optional-pass states.
9. Drive the live guidance UI from the same authoritative model and persist completion diagnostics.
10. Add tests for weighted/mandatory coverage combinations, complete/incomplete boundaries and optional unavailable passes.
11. Tests exercise the production-used coverage/auto-capture/session seam.
12. No unavailable/synthetic pose is represented as physical coverage.
13. Relevant regressions/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
