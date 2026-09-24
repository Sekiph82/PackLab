# PL-0090 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and all accepted M03 children preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Preserve SessionDiscoveryService use of ScanSessionStore.reopen, ActiveScanSession installation and safe discard.
7. Add integrated discovery/resume tests for every PL-0088 partial transaction stage, stale temp/transaction markers, missing/corrupt source or per-photo record and schema-version mismatch.
8. Ensure the SessionResumeCandidate.state installed on Resume is the recovered authoritative state returned after reopen, not a stale pre-recovery decode.
9. Add real discard behavior tests proving the selected resumable session is removed safely and blocked sessions are never offered Resume.
10. Filesystem/UI tests cover the actual production mutation/recovery/destructive boundary.
11. Validation and git diff --check clean/truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
