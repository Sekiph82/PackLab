# PL-0125 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0125_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve whole-package SHA-256 receiver verification and stored expected/actual/byte-count evidence.
7. Wire authenticated receiver completion acknowledgement into the production iOS transfer client and TransferViewModel.
8. Sender must not mark completed until transfer ID and package digest match, acknowledgement is authenticated, and receiver reports verified completion.
9. Checksum mismatch must never publish normal inbox content; retry behavior must remain explicit and resumable/restartable according to policy.
10. Add integrated tests for matching digest, final-byte corruption, wrong declared digest, retry after mismatch and sender never completing before verified authenticated acknowledgement.
11. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
12. Invalid/incomplete/untrusted data never reaches normal import authority.
13. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
14. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
15. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
