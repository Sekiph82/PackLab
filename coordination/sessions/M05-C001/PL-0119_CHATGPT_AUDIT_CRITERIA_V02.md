# PL-0119 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0119_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve the current PackScanWriter/SessionFinalizer implementation and committed package SHA-256/byte-count record.
7. Prove the production finalization call is built from canonical accepted-session records and immutable source bytes rather than arbitrary ad-hoc payloads.
8. Add real filesystem/injected failure tests for success, destination already exists, checksum mismatch, missing authoritative source, package write/move failure, record publication failure, and no partial destination/finalization state.
9. On every failure, prove the session remains resumable and all temporary package/record files are cleaned or rolled back truthfully.
10. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
11. Invalid/incomplete/untrusted data never reaches normal import authority.
12. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
13. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
14. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
