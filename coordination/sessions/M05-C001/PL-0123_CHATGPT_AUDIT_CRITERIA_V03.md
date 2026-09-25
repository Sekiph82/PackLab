# PL-0123 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/transfer/ingest authority is preserved.
5. PL-0123_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve /v1/pair, PairingAuthenticator, TLSIdentity, HTTPS-only receiver and PinnedReceiverSessionDelegate.
7. Provide deterministic TLS test material generation/loading that does not depend on an external openssl executable on the normal Windows locked-test host. Use a declared test-only/library approach or checked-in non-secret synthetic test certificate/key only if project policy explicitly permits test fixtures; never commit production keys.
8. Run real HTTPS loopback tests through certificate validation/pinning rather than ssl._create_unverified_context for the pinning cases.
9. Prove successful pairing/authenticated request plus actual wrong-certificate-pin rejection, expired offer, replayed offer, wrong receiver and missing auth over the network /v1/pair + protected transfer endpoints.
10. Prove error responses/logs never expose pairing code, bearer token, private key path/content or other secrets.
11. Tests exercise the actual production-used seam and prove the relevant restart/failure boundaries.
12. No untrusted/incomplete data reaches normal import authority and no security control is weakened.
13. Full locked suite and relevant project/static checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
