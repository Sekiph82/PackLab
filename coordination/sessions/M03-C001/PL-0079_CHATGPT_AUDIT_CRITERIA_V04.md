# PL-0079 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Prior passing behavior is preserved.
5. Previous audit PL-0079_CHATGPT_AUDIT_V03.md is fully addressed.
6. Preserve SharedARSessionOwner as the single physical owner and ARTrackingService as the app seam.
7. Extract/inject the minimum ARSession running/capability driver used by SharedARSessionOwner so lifecycle behavior can be tested without real hardware.
8. Add tests through ARTrackingService/owner for repeated start/stop, unsupported world tracking, interruption/interruption-end, state mapping and prevention of duplicate session ownership/listener setup.
9. Keep non-LiDAR world tracking and simulator unavailable behavior.
10. Tests exercise the actual production seam or its injected driver, not only a neighboring helper.
11. Regressions and git diff --check are clean/truthful.
12. Log records exact commits/files/results and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
