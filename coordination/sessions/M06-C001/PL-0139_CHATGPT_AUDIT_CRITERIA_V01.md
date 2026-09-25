# PL-0139 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md or ChatGPT audit artifacts.
4. Existing M05 service authority is reused rather than duplicated.
5. PL-0139 satisfies the frozen scope.
6. Create a central JobManager/domain model and UI panel for long-running work with stable job IDs, title/type, queued/running/succeeded/failed/cancelling/cancelled states, progress, timestamps and bounded log/status messages.
7. UI must observe JobManager state; widgets must not own worker process lifecycle.
8. Support multiple concurrent logical jobs and deterministic ordering/history retention.
9. Expose hooks for future reconstruction/subprocess adapters without starting M07.
10. Add tests for state transitions, progress monotonicity, concurrency ordering, failure details and bounded history.
11. Tests exercise the production-used Studio/app seam, not only isolated helpers.
12. UI tests are deterministic/offscreen-capable and do not require internet or a physical GPU unless explicitly benchmark-gated.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass truthfully.
14. Dependency/lock/license changes are reproducible and policy-compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
