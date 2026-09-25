# PL-0126 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0126_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve TransferViewModel state semantics and confirmed-byte progress calculation.
7. Add a real SwiftUI transfer screen reachable from finalized scan/history flow and bound to the production iOS network transfer client.
8. Show receiver identity, package name/size, confirmed bytes/percentage, phase and errors for every frozen UI state.
9. Cancel must cancel active network work/notify receiver without deleting the finalized source package; retry must query authoritative receiver status and resume the same transfer.
10. Add view-model/service tests for reconnect/resume, network cancel, checksum failure, terminal failure, monotonic progress and verified completion.
11. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
12. Invalid/incomplete/untrusted data never reaches normal import authority.
13. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
14. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
15. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
