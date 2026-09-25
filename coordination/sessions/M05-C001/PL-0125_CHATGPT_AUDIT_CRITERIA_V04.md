# PL-0125 — ChatGPT Remediation Audit Criteria V04

All criteria mandatory.

1. M05-BATCH-004 / READY / CODEX authorization exists before material work.
2. All 10 accepted M05 children remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan/transfer/ingest authority is preserved.
5. PL-0125_CHATGPT_AUDIT_V03.md is fully addressed.
6. Preserve the hardened production completion gate requiring matching transfer ID, digest, authenticated=true, verified=true and terminal verified/complete state.
7. Add an injectable production URLSession/transport seam if needed so URLSessionTransferClient acknowledgement validation can be tested deterministically without native network execution.
8. Add tests for matching success, wrong transfer ID, wrong digest, unauthenticated acknowledgement, non-terminal acknowledgement, corrupted/wrong-declared package digest, retry after mismatch and no premature completion.
9. Prove every rejected acknowledgement leaves sender state retryable, preserves persisted resumable identity, and never marks the source completed/exported-to-receiver.
10. Keep receiver whole-package SHA-256 verification unchanged.
11. Tests exercise the actual production-used seam and exact failure/state boundaries.
12. Full locked suite and relevant project/static checks pass truthfully.
13. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
14. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
