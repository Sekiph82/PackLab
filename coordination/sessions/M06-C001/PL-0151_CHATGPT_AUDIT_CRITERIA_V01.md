# PL-0151 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. Existing project/raw authority and single viewport abstraction are preserved.
5. PL-0151 satisfies the frozen scope.
6. Perform and document a focused comparison of PySide6-compatible 3D viewport approaches appropriate for point clouds/meshes on Windows, considering Qt integration, Python 3.12 support, licensing, headless/offscreen testing, large-mesh performance, picking, wireframe/normals and future CAD coexistence.
7. At minimum compare two viable approaches; one may be VTK/PyVista-family and another Qt/OpenGL/other supported stack if available.
8. Build minimal executable spikes using representative synthetic point/triangle counts, not marketing claims.
9. Record measured startup/load/render or interaction proxy metrics, memory observations, dependency weight and limitations on the available Windows host.
10. Select one M06 viewport approach with a written ADR/decision artifact; do not implement M07 reconstruction here.
11. Add a reproducible benchmark/spike command that can run headless where supported and truthfully records unavailable GPU/native capabilities.
12. Tests/benchmarks exercise the production-used service/viewport seam rather than only mocked policy helpers.
13. Performance/native/GPU claims are measured and limitations are stated truthfully.
14. Full locked suite and relevant Ruff/mypy/compileall/project checks pass.
15. Dependency/lock/license changes are reproducible and compliant.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
