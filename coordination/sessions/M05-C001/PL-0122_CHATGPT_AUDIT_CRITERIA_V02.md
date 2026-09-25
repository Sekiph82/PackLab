# PL-0122 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0122_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve existing PairingOffer/PairingStore and PairingCameraOwnership contracts.
7. Add a real iOS pairing coordinator/UI supporting manual pairing-code entry plus QR offer parsing/scanning.
8. Wire QR scanner camera ownership to the production capture camera lifecycle so capture and scanner cannot run concurrently and ownership is cleanly returned.
9. Persist only receiver instance ID, host, port and TLS fingerprint needed for reconnect; never persist the one-time pairing code.
10. Add Swift behavior tests for valid/manual/QR, expired/wrong-version/malformed/wrong-receiver cases, persisted reconnect identity, and camera ownership hand-back.
11. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
12. Invalid/incomplete/untrusted data never reaches normal import authority.
13. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
14. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
15. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
