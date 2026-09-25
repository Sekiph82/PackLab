# PL-0138 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md or ChatGPT audit artifacts.
4. Existing M05 service authority is reused rather than duplicated.
5. PL-0138 satisfies the frozen scope.
6. Persist window geometry, maximized/fullscreen state, dock layout, last route, theme/display preferences and other M06 UI preferences using a versioned settings schema.
7. Use Qt settings or an owned JSON/settings adapter with atomic/versioned migration behavior; never persist private project payloads or secrets in UI preferences.
8. Restore safely after invalid/corrupt/older preference state and fall back to a usable default layout.
9. Keep settings injectable for tests and portable across normal Windows user profiles.
10. Add tests for round-trip, corrupt state, version migration/defaulting, off-screen/invalid geometry sanitization and reset.
11. Tests exercise the production-used Studio/app seam, not only isolated helpers.
12. UI tests are deterministic/offscreen-capable and do not require internet or a physical GPU unless explicitly benchmark-gated.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass truthfully.
14. Dependency/lock/license changes are reproducible and policy-compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
