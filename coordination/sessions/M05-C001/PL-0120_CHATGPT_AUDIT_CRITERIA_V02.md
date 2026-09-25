# PL-0120 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0120_CHATGPT_AUDIT_V01.md is fully addressed.
6. Wire PackScanShareCoordinator and PackScanShareSheet into the real finalized scan/history workflow with an explicit Share/Export action.
7. Never expose mutable session directories or unfinalized packages; derive eligibility from authoritative SessionFinalizationRecord.
8. Add a production-used share presentation coordinator/state seam for presenting, cancelling, completing, presentation failure, missing package, and package deletion/replacement while sharing.
9. Keep the finalized source package stable for the activity lifetime and remove only temporary staging owned by the share workflow.
10. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
11. Invalid/incomplete/untrusted data never reaches normal import authority.
12. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
13. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
14. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
