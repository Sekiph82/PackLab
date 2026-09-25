# PL-0152 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. Existing project/raw authority and single viewport abstraction are preserved.
5. PL-0152 satisfies the frozen scope.
6. Implement the selected PL-0151 viewport adapter behind a PackLab viewport interface owned by Studio, not directly coupled throughout widgets.
7. Load supported local mesh/point-cloud fixture formats sufficient for M06 foundation; preserve units/coordinates without modifying source files.
8. Implement camera orbit, pan, zoom, fit-to-view and reset with deterministic state serialization where practical.
9. Handle empty/corrupt/unsupported files with structured errors and keep UI responsive for bounded fixture sizes.
10. Add offscreen/headless-capable tests for load metadata, scene bounds, camera transforms, fit/reset and failure handling plus one real adapter smoke test.
11. Tests/benchmarks exercise the production-used service/viewport seam rather than only mocked policy helpers.
12. Performance/native/GPU claims are measured and limitations are stated truthfully.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass.
14. Dependency/lock/license changes are reproducible and compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
