# PL-0126 — ChatGPT Remediation Audit Criteria V04

All criteria mandatory.

1. M05-BATCH-004 / READY / CODEX authorization exists before material work.
2. All 10 accepted M05 children remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan/transfer/ingest authority is preserved.
5. PL-0126_CHATGPT_AUDIT_V03.md is fully addressed.
6. Preserve the real finalized-history → FinalizedTransferWorkflowView → TransferScreen path and PL-0124 same-ID resume.
7. Extend FakeProductionTransferClient or equivalent production-client test seam to drive network cancel, authoritative status query, same-ID reconnect/resume, monotonic confirmed progress, checksum/digest retryable failure, terminal failure and verified completion.
8. Add a fresh TransferViewModel/runtime restore test proving visible phase, confirmed bytes and receiver identity are rebuilt from persisted sender identity plus receiver status, not optimistic local counters.
9. Cancel must retain finalized source and resumable identity; terminal failure must be visibly distinct from retryable failure; verified completion alone clears sender identity.
10. Keep all frozen UI phases reachable/truthful.
11. Tests exercise the actual production-used seam and exact failure/state boundaries.
12. Full locked suite and relevant project/static checks pass truthfully.
13. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
14. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
