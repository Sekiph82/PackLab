# PL-0126 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Accepted PackScan/session architecture is reused rather than duplicated.
5. PL-0126 satisfies the frozen task scope.
6. Add iOS transfer UI bound to the production network transfer service showing paired receiver identity, package name/size, bytes sent, percentage, transfer phase and errors.
7. Progress must come from confirmed protocol bytes/offsets, not an optimistic timer.
8. Cancel must stop active network work without deleting the finalized source package and must preserve resumable receiver state unless the user explicitly discards it.
9. Retry/reconnect must resume through PL-0124 status rather than silently start a second transfer.
10. Expose clear states for pairing required, connecting, transferring, verifying, completed, cancelled, retryable failure and terminal failure.
11. Add view-model/service tests for progress monotonicity, cancel, retry, reconnect/resume, checksum failure and completed-state acknowledgement.
12. Tests exercise the production-used transfer/finalization/UI seam, not only a disconnected helper.
13. Security/privacy claims are truthful and secrets never enter Git/logs/package evidence.
14. Full locked suite, relevant project checks and git diff --check pass truthfully.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
