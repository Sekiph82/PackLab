# PL-0153 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. The PL-0151 viewport backend/adapter and source-geometry immutability are preserved.
5. PL-0153 satisfies the frozen scope.
6. Add viewport world grid, XYZ axes and millimetre-based scale cues consistent with PackLab's packaging/measurement coordinate conventions.
7. Grid spacing/labels must adapt to camera distance without changing underlying world units.
8. Expose visibility and scale-cue settings through the viewport state model so later Settings/workspace persistence can restore them.
9. Do not claim calibrated real-world accuracy here; this is a visual unit cue, with M09 owning measurement accuracy.
10. Add deterministic scene/state tests for axes orientation, mm unit metadata, adaptive grid spacing thresholds, visibility toggles and camera-distance changes.
11. Tests exercise production viewport/scene behavior and source non-mutation.
12. Measurement/performance/GPU limitations are stated truthfully.
13. Full locked suite and Ruff/mypy/compileall/project checks pass.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
