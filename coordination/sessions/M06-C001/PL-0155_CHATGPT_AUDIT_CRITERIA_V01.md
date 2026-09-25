# PL-0155 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. The PL-0151 viewport backend/adapter and source-geometry immutability are preserved.
5. PL-0155 satisfies the frozen scope.
6. Implement viewport debug/render modes for solid/surface baseline, wireframe, normals visualization and point-cloud rendering using the selected PL-0151 backend.
7. Modes must be scene/view state only and never mutate source mesh/point-cloud data.
8. Normals display must handle missing normals truthfully and either compute a temporary derived view representation or report unavailable without persisting fake authority.
9. Expose mode toggles through a backend-independent viewport state interface.
10. Add tests for mode transitions, persistence/state serialization, missing-normal behavior, source non-mutation and one real backend/offscreen smoke path.
11. Tests exercise production viewport/scene behavior and source non-mutation.
12. Measurement/performance/GPU limitations are stated truthfully.
13. Full locked suite and Ruff/mypy/compileall/project checks pass.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
