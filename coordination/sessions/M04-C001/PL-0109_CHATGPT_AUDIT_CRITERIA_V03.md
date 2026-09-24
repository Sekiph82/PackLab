# PL-0109 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. M04-BATCH-003 / READY / CODEX authorization exists before material work.
2. All 16 accepted M04 children remain unregressed; M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing production M04 integration is preserved.
5. PL-0109_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve live CompletionDiagnostics UI and M04 context persistence.
7. Add a mixed required-detail-pass test where one required pass is complete and another remains missing; mandatoryMissingAreas and score must stay truthful.
8. Add a real resume/restore test using a newly configured runtime that loads persisted completion/pass state and proves deterministic restored/recomputed outcome.
9. Preserve optional-unavailable base semantics and percentage/missing-area transparency.
10. Tests exercise the actual production-used seam/state boundary.
11. Full declared suite, relevant project checks and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
