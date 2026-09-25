# PL-0140 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md or ChatGPT audit artifacts.
4. Existing M05 service authority is reused rather than duplicated.
5. PL-0140 satisfies the frozen scope.
6. Integrate JobManager with the existing safe packlab_core.subprocess_runner cancellation semantics rather than inventing a second process-kill implementation.
7. On app close, detect active jobs and execute a bounded cancellation/shutdown policy that stops only PackLab-owned subprocess trees.
8. Do not block the GUI thread indefinitely; expose shutdown progress/state and a deterministic terminal result.
9. Preserve structured cleanup errors and do not silently claim cancellation succeeded if cleanup failed.
10. Add tests for idle close, active cancellable job, multiple jobs, cleanup failure, bounded timeout and no unrelated-process termination.
11. Tests exercise the production-used Studio/app seam, not only isolated helpers.
12. UI tests are deterministic/offscreen-capable and do not require internet or a physical GPU unless explicitly benchmark-gated.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass truthfully.
14. Dependency/lock/license changes are reproducible and policy-compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
