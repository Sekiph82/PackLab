# PL-0123 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Accepted PackScan/session architecture is reused rather than duplicated.
5. PL-0123 satisfies the frozen task scope.
6. Implement the PL-0121 network transport over TLS using standard platform cryptography; do not design custom encryption primitives.
7. Windows receiver must use a locally generated TLS certificate/key kept outside Git; iOS must pin/verify the receiver identity from the pairing offer rather than blindly trusting any self-signed certificate.
8. Authenticate the transfer session with the short-lived pairing exchange and issue a scoped session credential/token that cannot be reused after expiry/revocation.
9. Reject unpaired clients, wrong certificate fingerprints, replayed/expired pairing offers, wrong receiver IDs and downgraded/insecure transport.
10. Keep secrets/cert private keys out of logs, diagnostics, `.packscan`, Git and user-facing QR payloads except the non-secret certificate fingerprint and short-lived pairing material required by the workflow.
11. Add deterministic integration tests with ephemeral test certificates for successful TLS/auth, wrong pin, expired/replayed code, missing auth and secret-redaction behavior.
12. Tests exercise the production-used transfer/finalization/UI seam, not only a disconnected helper.
13. Security/privacy claims are truthful and secrets never enter Git/logs/package evidence.
14. Full locked suite, relevant project checks and git diff --check pass truthfully.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
