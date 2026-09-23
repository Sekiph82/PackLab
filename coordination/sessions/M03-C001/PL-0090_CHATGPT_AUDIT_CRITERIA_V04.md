# PL-0090 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0090_CHATGPT_AUDIT_V03.md is fully addressed.
6. Preserve authoritative ScanSessionStore.reopen discovery, ActiveScanSession installation and safe discard.
7. Add integrated filesystem tests through SessionDiscoveryService/ContentView-facing callbacks for clean resume, each PL-0088 partial transaction stage, stale temps, missing/corrupt record/source, schema-version mismatch and discard.
8. Ensure candidate.state used for ActiveScanSession comes from the authoritative reopened/recovered state rather than a stale pre-reopen decode.
9. Do not offer Resume for any session whose complete metadata/state/record/source graph fails validation.
10. Filesystem/UI tests cover both success and injected partial/crash failure at the real production seam.
11. Relevant regressions and git diff --check are clean/truthful.
12. Child log records exact evidence and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
