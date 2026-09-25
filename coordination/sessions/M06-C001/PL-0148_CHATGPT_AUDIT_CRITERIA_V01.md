# PL-0148 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. Existing project/raw authority and single viewport abstraction are preserved.
5. PL-0148 satisfies the frozen scope.
6. Persist project-scoped recovery markers/checkpoints for in-progress jobs and editable state without treating incomplete derived output as authoritative.
7. On reopen after abnormal termination, classify interrupted jobs/artifacts as resumable, restart-required or invalid according to explicit metadata.
8. Recovery must never mutate raw evidence and must quarantine/delete only PackLab-owned temporary/partial derived artifacts according to policy.
9. Expose recovery summary/actions to the shell through ProjectManager/JobManager services, not modal logic embedded in widgets.
10. Add tests for clean close, crash marker, resumable job, invalid partial artifact, recovery accept/discard and repeated reopen idempotency.
11. Tests/benchmarks exercise the production-used service/viewport seam rather than only mocked policy helpers.
12. Performance/native/GPU claims are measured and limitations are stated truthfully.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass.
14. Dependency/lock/license changes are reproducible and compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
