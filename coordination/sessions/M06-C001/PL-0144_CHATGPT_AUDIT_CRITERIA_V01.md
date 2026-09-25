# PL-0144 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. M05 raw-ingest authority and M06 service/UI separation are preserved.
5. PL-0144 satisfies the frozen scope.
6. Implement one ProjectManager/service for new/open/close lifecycle over PL-0143 layout.
7. New project must create metadata/layout atomically and fail cleanly on partial creation or existing conflicting destination.
8. Open must validate project identity/version/layout before becoming current; Close must release project-scoped resources/jobs without deleting data.
9. Main Studio shell must bind current project state and route/workspace availability to ProjectManager rather than widget-local state.
10. Add tests for create/open/close, duplicate destination, corrupt metadata/layout, switching projects, active-job close policy and crash-safe failure.
11. Tests exercise production-used project/shell seams and real filesystem boundaries.
12. No operation mutates accepted raw evidence or leaks secrets/private paths into portable state.
13. Full locked suite plus Ruff/mypy/compileall/project checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
