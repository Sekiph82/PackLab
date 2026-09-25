# PL-0128 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0128_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve PackLabReceiver, resumable store and common ImportService.
7. Integrate the real network pairing/auth endpoint from PL-0123 with receiver HTTPS lifecycle.
8. Add actual TLS loopback tests that start the server, pair/authenticate a client, upload a partial transfer, stop/restart the receiver over the same root, query status and resume.
9. Prove unpaired/missing-auth requests are rejected over HTTP/TLS, concurrent transfer IDs remain isolated, and only verified packages reach Capture Inbox and common ingest.
10. Preserve resumable checkpoints across clean shutdown/restart.
11. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
12. Invalid/incomplete/untrusted data never reaches normal import authority.
13. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
14. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
15. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
