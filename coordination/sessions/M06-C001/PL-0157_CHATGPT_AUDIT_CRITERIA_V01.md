# PL-0157 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. The PL-0151 viewport backend/adapter and source-geometry immutability are preserved.
5. PL-0157 satisfies the frozen scope.
6. Create a reproducible M06 large-mesh/point-cloud benchmark using synthetic or repository-safe generated fixtures at multiple sizes representative of packaging scans.
7. Measure load time, scene initialization, memory proxy/observation and interaction/render proxy where the environment permits; record hardware/backend/runtime metadata.
8. Define and implement an initial viewport LOD/decimation/display-budget strategy that affects only interactive display representations and never overwrites authoritative source geometry.
9. LOD selection must be deterministic from scene size/performance policy and expose current display-vs-source counts for diagnostics.
10. Add tests for LOD threshold selection, source non-mutation, stable display counts, fallback when decimation unavailable and benchmark result schema.
11. Publish an M06 performance evidence artifact with truthful limitations; do not claim physical GPU performance if only software/offscreen rendering was available.
12. Tests exercise production viewport/scene behavior and source non-mutation.
13. Measurement/performance/GPU limitations are stated truthfully.
14. Full locked suite and Ruff/mypy/compileall/project checks pass.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
