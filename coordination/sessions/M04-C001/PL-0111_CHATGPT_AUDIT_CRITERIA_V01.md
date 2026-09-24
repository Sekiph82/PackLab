# PL-0111 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Shared M03/M04 capture, quality, coverage and session architecture is reused.
5. PL-0111 satisfies the frozen scope.
6. Define a versioned Matte/HDPE preset that configures quality thresholds, framing guidance, coverage density and lighting guidance without duplicating the core quality engine.
7. Favor stable exposure, broad diffuse lighting and standard coverage while retaining all hard safety/quality gates.
8. Persist the selected preset and effective policy values with the scan session so Windows analysis can reproduce the decision context.
9. Allow future tuning through configuration rather than source-code changes.
10. Add tests for preset loading, effective policy values, session persistence and fallback/default behavior.
11. Preset/mode behavior is config-driven and persisted with session context.
12. No unsupported physical/reconstruction capability is claimed.
13. Tests exercise the production-used preflight/preset/session seam.
14. Relevant regression/project checks and git diff --check pass truthfully.
15. Privacy/signing/secret boundaries remain clean.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
