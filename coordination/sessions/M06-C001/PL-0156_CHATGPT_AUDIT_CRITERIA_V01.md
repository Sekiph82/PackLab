# PL-0156 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. The PL-0151 viewport backend/adapter and source-geometry immutability are preserved.
5. PL-0156 satisfies the frozen scope.
6. Add a viewport screenshot/export-preview service that captures the current camera/view state into a deterministic image file suitable for audit/report evidence.
7. Support explicit output path/format and include lightweight sidecar metadata for project/revision, camera state, visible object IDs and viewport backend/version without private absolute-path leakage.
8. Use atomic publication and never overwrite raw source evidence.
9. Handle headless/offscreen capture when supported by the chosen backend and report capability limitations truthfully.
10. Add tests for image creation, dimensions/non-empty output, sidecar metadata, atomic overwrite policy, redaction and unavailable-backend failure.
11. Tests exercise production viewport/scene behavior and source non-mutation.
12. Measurement/performance/GPU limitations are stated truthfully.
13. Full locked suite and Ruff/mypy/compileall/project checks pass.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
