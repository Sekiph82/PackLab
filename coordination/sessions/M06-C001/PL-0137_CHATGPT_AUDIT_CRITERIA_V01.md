# PL-0137 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md or ChatGPT audit artifacts.
4. Existing M05 service authority is reused rather than duplicated.
5. PL-0137 satisfies the frozen scope.
6. Build a QMainWindow-based workspace with central content plus logical dock areas suitable for viewport, properties/inspector, scene/object tree, job/activity and logs.
7. Define stable dock/object names so Qt saveState/restoreState can work across sessions.
8. Provide default layouts per major workspace without coupling dock logic to future reconstruction/editor implementations.
9. Prevent duplicate dock instances and invalid docking relationships.
10. Add tests for default dock inventory, stable object names, show/hide/move state and deterministic reset-to-default.
11. Tests exercise the production-used Studio/app seam, not only isolated helpers.
12. UI tests are deterministic/offscreen-capable and do not require internet or a physical GPU unless explicitly benchmark-gated.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass truthfully.
14. Dependency/lock/license changes are reproducible and policy-compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
