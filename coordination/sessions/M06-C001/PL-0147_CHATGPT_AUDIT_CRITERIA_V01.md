# PL-0147 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. Existing project/raw authority and single viewport abstraction are preserved.
5. PL-0147 satisfies the frozen scope.
6. Implement append-only logical operation history for user edits with operation ID, project revision, timestamp, operation type, parameters/reference IDs and reversible/non-reversible marker.
7. History must never store mutable raw payload copies or secrets; reference project-relative assets/state.
8. Provide undo/redo cursor semantics only for explicitly reversible operations and never rewrite prior history entries.
9. Persist history atomically and validate revision continuity on reopen.
10. Add tests for append, undo/redo, non-reversible barrier, restart/reload, revision mismatch and tamper/corrupt history.
11. Tests/benchmarks exercise the production-used service/viewport seam rather than only mocked policy helpers.
12. Performance/native/GPU claims are measured and limitations are stated truthfully.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass.
14. Dependency/lock/license changes are reproducible and compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
