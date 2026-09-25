# PL-0119 — ChatGPT Remediation Audit Criteria V04

All criteria mandatory.

1. M05-BATCH-004 / READY / CODEX authorization exists before material work.
2. All 10 accepted M05 children remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan/transfer/ingest authority is preserved.
5. PL-0119_CHATGPT_AUDIT_V03.md is fully addressed.
6. Preserve CanonicalSessionFinalizationWorkflow, SessionGalleryStore.finalizeAcceptedSession and the now-green injected rollback/failure matrix.
7. Add a real production scan-finalize/export action reachable from the active session/history workflow that invokes the canonical source-only finalization seam; do not call arbitrary SessionFinalizer.finalize(FinalizationInput...) from production UI.
8. Build manifest/payload inputs only from canonical accepted-session records, immutable source bytes and accepted metadata contracts.
9. After successful finalization, prove the resulting finalization record/history entry becomes exported and is immediately eligible for Share/Send-to-PackLab.
10. Add a production-workflow test for accepted session → canonical finalization → exported history, plus missing-authority failure with no exported state.
11. Tests exercise the actual production-used seam and exact failure/state boundaries.
12. Full locked suite and relevant project/static checks pass truthfully.
13. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
14. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
