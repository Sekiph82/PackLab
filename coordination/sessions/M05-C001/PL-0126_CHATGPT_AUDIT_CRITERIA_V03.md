# PL-0126 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/transfer/ingest authority is preserved.
5. PL-0126_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve the real finalized-history → FinalizedTransferWorkflowView → TransferScreen navigation.
7. Consume the PL-0124 persisted same-transfer resume implementation; retry must query status and continue the same transfer ID instead of starting a new transfer.
8. Cancel must invoke the production client cancellation path, retain the finalized source, and preserve resumable sender identity unless the user explicitly discards.
9. Ensure all frozen UI phases are reachable/truthful: pairingRequired, connecting, transferring, verifying, completed, cancelled, retryableFailure and terminalFailure.
10. Add deterministic fake ProductionTransferClient tests for network cancel, authoritative status query, same-ID reconnect/resume, monotonic confirmed progress, checksum retryable failure, terminal failure and verified completion.
11. Prove UI state after app/runtime restore is rebuilt from persisted sender identity + receiver status rather than optimistic local counters.
12. Tests exercise actual production-used behavior and exact failure/restart boundaries.
13. No untrusted/incomplete data reaches normal import authority and no security control is weakened.
14. Full locked suite and relevant project/static checks pass truthfully.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
