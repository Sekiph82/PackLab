# PL-0104 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. M04-BATCH-003 / READY / CODEX authorization exists before material work.
2. All 16 accepted M04 children remain unregressed; M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing production M04 integration is preserved.
5. PL-0104_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve the current production GuidedAutoCaptureService, health-gated backend and canonical accepted transaction.
7. Add integrated runtime/backend-call tests for quality reject, missing coverage target, pose ineligible, overlap blocked and health hard stop.
8. Prove in-flight duplicate suppression, exact cooldown boundary, rejected-candidate rearm and accepted-capture success.
9. For every blocked gate, prove the underlying still backend is not invoked unless the gate policy explicitly allows it.
10. Tests exercise the actual production-used seam/state boundary.
11. Full declared suite, relevant project checks and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
