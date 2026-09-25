# PL-0122 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Accepted PackScan/session architecture is reused rather than duplicated.
5. PL-0122 satisfies the frozen task scope.
6. Create a receiver pairing offer containing receiver instance ID, host/port, protocol version, short-lived pairing ID/code, expiry, and TLS certificate fingerprint or equivalent pinning identity supplied by PL-0123.
7. Windows receiver must expose both a human-enterable pairing code and a QR payload representing the same offer.
8. iOS must support manual pairing-code entry and QR payload parsing/scanning; any camera-based QR scanner must never run concurrently with the production capture session and must hand camera ownership back cleanly.
9. Pairing offers must expire, be single-use or explicitly revocable, and must not contain long-lived secrets in logs.
10. Store only the minimum paired-receiver identity needed for reconnect; do not persist the one-time pairing code.
11. Add tests for valid/expired/wrong receiver/wrong version/malformed QR/manual-code flows and non-concurrent camera ownership.
12. Tests exercise the production-used transfer/finalization/UI seam, not only a disconnected helper.
13. Security/privacy claims are truthful and secrets never enter Git/logs/package evidence.
14. Full locked suite, relevant project checks and git diff --check pass truthfully.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
