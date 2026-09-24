# PL-0108 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. M04-BATCH-003 / READY / CODEX authorization exists before material work.
2. All 16 accepted M04 children remain unregressed; M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing production M04 integration is preserved.
5. PL-0108_CHATGPT_AUDIT_V02.md is fully addressed.
6. Add an explicit operator-skipped base-pass state distinct from physically unavailable, incomplete and complete.
7. Persist/restore the skipped reason/state in M04 session context and completion diagnostics.
8. Add a quality-rejected feasible base-candidate test and prove it does not create accepted source/pass evidence.
9. Add skip/reopen tests and preserve no-false-complete behavior for skipped or unavailable base coverage.
10. Tests exercise the actual production-used seam/state boundary.
11. Full declared suite, relevant project checks and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
