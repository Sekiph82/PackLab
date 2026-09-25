# PL-0125 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/transfer/ingest authority is preserved.
5. PL-0125_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve receiver whole-package SHA-256 verification and stored expected/actual/byte-count evidence.
7. In URLSessionTransferClient validate acknowledgement transferID equals the active transfer ID, package digest matches, authenticated=true, verified=true, and state is terminal verified/complete before returning success.
8. In TransferViewModel applyCompletion also reject wrong transfer ID and non-terminal acknowledgement state; do not rely only on digest/authenticated/verified.
9. Checksum mismatch/wrong transfer/non-terminal acknowledgement must leave sender retryable and must never clear persisted resumable identity or mark source exported-to-receiver complete.
10. Add injected ProductionTransferClient/URLProtocol tests for matching success, wrong transfer ID, wrong digest, unauthenticated ack, non-terminal ack, final-byte corruption/wrong declared digest, retry after mismatch and no premature completion.
11. Tests exercise actual production-used behavior and exact failure/restart boundaries.
12. No untrusted/incomplete data reaches normal import authority and no security control is weakened.
13. Full locked suite and relevant project/static checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
