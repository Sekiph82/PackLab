# PL-0143 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. M05 raw-ingest authority and M06 service/UI separation are preserved.
5. PL-0143 satisfies the frozen scope.
6. Define a versioned PackLab project layout separating raw, working, derived, cache/temp and export data plus project metadata/history/recovery state.
7. Raw must remain immutable-by-policy and compatible with accepted M05 raw-ingest evidence; working/derived/export must never overwrite raw authority.
8. Define canonical path helpers, safe relative-path rules, directory creation/validation and schema versioning.
9. Document which later milestones own each area and which files are portable versus regenerable.
10. Add filesystem tests for creation, validation, traversal rejection, existing layout reuse and corrupt/incompatible layout detection.
11. Tests exercise production-used project/shell seams and real filesystem boundaries.
12. No operation mutates accepted raw evidence or leaks secrets/private paths into portable state.
13. Full locked suite plus Ruff/mypy/compileall/project checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
