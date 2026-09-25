# PL-0124 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/transfer/ingest authority is preserved.
5. PL-0124_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve ResumableTransferStore receiver checkpoints and current production URLSession client.
7. Actually use SenderTransferIdentityStore when a transfer is first created: persist transfer ID, package digest and receiver identity before/while network work begins.
8. Ensure TransferRequest/networkRequest is rewritten with the resolved transfer ID. retryNetworkTransfer must never generate a new UUID for an existing resumable transfer.
9. Add app/runtime restart restore: load persisted sender identity, verify current finalized package digest + receiver identity match, query receiver status, rebuild the request with the same transfer ID, and continue from receiver next_offset.
10. Clear persisted sender identity only after verified completion or explicit user discard; cancellation alone must preserve resumability.
11. Add deterministic fake ProductionTransferClient tests proving first ID persistence, same-ID retry, app-restart restore, receiver-confirmed offset resume, cancel/resume, conflicting identity fail-closed and no duplicate transfer creation.
12. Tests exercise the actual production-used seam and prove the relevant restart/failure boundaries.
13. No untrusted/incomplete data reaches normal import authority and no security control is weakened.
14. Full locked suite and relevant project/static checks pass truthfully.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
