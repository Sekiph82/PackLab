# PL-0146 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. M05 raw-ingest authority and M06 service/UI separation are preserved.
5. PL-0146 satisfies the frozen scope.
6. Implement debounced/transactional autosave for editable project state using ProjectManager/revision contracts.
7. Autosave must never write into raw evidence and must be atomic with crash-safe temp/replace behavior.
8. Concurrent/stale writes must be detected using project revision/base revision rather than silently overwriting newer state.
9. Expose save status/error state to the shell without blocking the GUI thread.
10. Add tests for debounce/coalescing, atomic save, stale conflict, write failure, shutdown flush policy and raw-store non-mutation.
11. Tests exercise production-used project/shell seams and real filesystem boundaries.
12. No operation mutates accepted raw evidence or leaks secrets/private paths into portable state.
13. Full locked suite plus Ruff/mypy/compileall/project checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
