# PL-0135 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md or ChatGPT audit artifacts.
4. Existing M05 service authority is reused rather than duplicated.
5. PL-0135 satisfies the frozen scope.
6. Add PySide6 as a declared/locked runtime dependency compatible with Python 3.12 and record any required license/dependency metadata.
7. Create one production PackLab Studio application entry point with QApplication ownership, organization/app identifiers, icon/resource hooks, exception boundary and deterministic exit code.
8. Keep domain/services in packlab_core or existing packlab_studio services; do not move business logic into widgets.
9. Support headless/offscreen test execution without requiring a physical display.
10. Add shell smoke tests proving app construction, one main window, clean close and no import-time QApplication side effects.
11. Tests exercise the production-used Studio/app seam, not only isolated helpers.
12. UI tests are deterministic/offscreen-capable and do not require internet or a physical GPU unless explicitly benchmark-gated.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass truthfully.
14. Dependency/lock/license changes are reproducible and policy-compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
