# PL-0119 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Accepted PackScan/session architecture is reused rather than duplicated.
5. PL-0119 satisfies the frozen task scope.
6. Reuse the accepted PackScanWriter/SessionFinalizer contracts; do not create a second container writer.
7. Finalize only from authoritative accepted-session records and immutable source bytes into one `.packscan` file.
8. Ensure manifest payload declarations, per-payload SHA-256, checksums.json coverage, deterministic ZIP layout, and canonical schema version remain valid.
9. Publish through a same-filesystem temporary file plus atomic rename/move; never expose a partial final package at the destination.
10. On any validation/write/rename failure, keep the scan resumable, clean temporary artifacts, and do not mark export/finalization complete.
11. Add real filesystem tests for success, destination exists, checksum mismatch, missing source, write/rename failure, and no-partial-file guarantees.
12. Tests exercise the production-used transfer/finalization/UI seam, not only a disconnected helper.
13. Security/privacy claims are truthful and secrets never enter Git/logs/package evidence.
14. Full locked suite, relevant project checks and git diff --check pass truthfully.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
