# PL-0124 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0124_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve ResumableTransferStore receiver behavior and checkpoint format.
7. Implement sender-side status query/reconnect in the production iOS transfer client; after app/network restart resume from receiver-confirmed next_offset rather than starting from zero.
8. Persist only the minimum non-secret sender transfer identity required to reconnect to an existing resumable transfer.
9. Prove receiver restart and sender cancellation preserve verified resumable bytes and never publish incomplete content.
10. Add integrated sender/receiver tests for disconnect, sender restart, receiver restart, duplicate/out-of-order/conflicting chunks, cancel/resume and multi-chunk completion.
11. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
12. Invalid/incomplete/untrusted data never reaches normal import authority.
13. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
14. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
15. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
