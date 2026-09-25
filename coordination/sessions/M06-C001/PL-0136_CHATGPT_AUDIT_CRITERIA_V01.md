# PL-0136 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md or ChatGPT audit artifacts.
4. Existing M05 service authority is reused rather than duplicated.
5. PL-0136 satisfies the frozen scope.
6. Implement primary navigation for Library, Capture Inbox, Reconstruction, Editor and Settings inside one main window.
7. Use stable route/view IDs and a central navigation controller/router; do not create five unrelated top-level windows.
8. Capture Inbox must compose the accepted M05 IngestController/receiver/import results rather than duplicating ingest logic.
9. Navigation must preserve current project context and selected route deterministically.
10. Add tests for all route transitions, unknown-route failure, current-route state and Capture Inbox service composition.
11. Tests exercise the production-used Studio/app seam, not only isolated helpers.
12. UI tests are deterministic/offscreen-capable and do not require internet or a physical GPU unless explicitly benchmark-gated.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass truthfully.
14. Dependency/lock/license changes are reproducible and policy-compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
