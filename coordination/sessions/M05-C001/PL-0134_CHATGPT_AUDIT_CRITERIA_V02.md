# PL-0134 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0134_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve the existing deterministic M05 integration fixtures and Windows ingest assertions.
7. After PL-0121–PL-0126 remediation, drive the authoritative iOS/cross-language transfer client/protocol seam into the real HTTPS receiver rather than calling receiver methods with token_authenticated=True.
8. Exercise pairing, pinned/authenticated transport, partial transfer, sender/receiver restart/resume, cancel/retry, checksum verification and exactly-once ingest through raw/index/report.
9. Add an invalid PackScan fixture with valid controls/checksum index structure but the declared image/photo payload specifically missing, so missing-image failure is isolated rather than masked by missing checksums.json.
10. Retain corrupt ZIP, bad manifest, internal checksum mismatch, future schema and unsafe path quarantine tests; invalid/untrusted data must never reach raw authority.
11. Tests exercise the actual production-used seam rather than only a disconnected helper.
12. Invalid/incomplete/untrusted data never reaches normal import authority.
13. Security/privacy claims are truthful and no secrets/private keys enter Git/logs/package data.
14. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
