# PL-0123 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0123_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve TLSIdentity, PairingAuthenticator and PinnedReceiverSessionDelegate; do not introduce custom cryptography or insecure fallback.
7. Expose a real HTTPS pairing/auth endpoint on the Windows receiver that exchanges a valid short-lived pairing offer/code for a scoped session credential.
8. Implement a production iOS URLSession transfer client that pins the paired receiver certificate fingerprint, performs the pairing/auth exchange, and sends authenticated protocol requests.
9. Reject wrong pin, missing auth, replay/expiry, wrong receiver and insecure/downgraded transport at the real network boundary.
10. Add ephemeral-certificate loopback integration tests for successful pairing/authenticated request, wrong pin, missing auth, expired/replayed offer and secret redaction.
11. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
12. Invalid/incomplete/untrusted data never reaches normal import authority.
13. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
14. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
15. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
