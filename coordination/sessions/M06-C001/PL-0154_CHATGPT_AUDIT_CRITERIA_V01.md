# PL-0154 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. The PL-0151 viewport backend/adapter and source-geometry immutability are preserved.
5. PL-0154 satisfies the frozen scope.
6. Define stable scene object IDs/types for Scan Mesh, Design Model, cap, label and reference geometry with visible/selectable state.
7. Implement single-selection baseline plus programmatic clear/select and visibility toggles through one scene model; viewport widgets must reflect domain scene state rather than own it.
8. Selection of hidden/missing objects must fail or clear deterministically; raw source assets must never be modified.
9. Expose scene object changes to the object-tree/inspector UI seams created in M06 without starting later editing milestones.
10. Add tests for object registration, selection, hidden-object behavior, visibility persistence/state restore and duplicate-ID rejection.
11. Tests exercise production viewport/scene behavior and source non-mutation.
12. Measurement/performance/GPU limitations are stated truthfully.
13. Full locked suite and Ruff/mypy/compileall/project checks pass.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
