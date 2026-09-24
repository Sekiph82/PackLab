# PL-0102 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing M03 camera/sensor/session ownership is reused.
5. PL-0102 satisfies the frozen scope.
6. Define a deterministic orbit-coverage model using explicit azimuth/elevation sectors around the package.
7. Map accepted pose evidence from the existing ARTrackingService/PackScan coordinate convention into coverage bins; unavailable/stale pose must not create fake coverage.
8. Support configurable ring/bin definitions so packaging presets can refine requirements without changing the core model.
9. Track covered, missing, duplicate and invalid sectors with stable IDs and completion metrics.
10. Add tests for wrap-around azimuth, elevation boundaries, unavailable pose, duplicate captures and deterministic coverage totals.
11. Tests exercise the production-used coverage/auto-capture/session seam.
12. No unavailable/synthetic pose is represented as physical coverage.
13. Relevant regressions/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
