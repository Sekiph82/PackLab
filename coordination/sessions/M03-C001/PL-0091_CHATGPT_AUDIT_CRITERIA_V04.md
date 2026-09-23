# PL-0091 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0091_CHATGPT_AUDIT_V03.md is fully addressed.
6. Treat .packscan output plus session finalization.json as one publication transaction when sessionRoot is supplied.
7. If finalization-record write/replace fails after package creation, remove/roll back the newly created package or otherwise restore an unambiguous pre-finalization state.
8. Add successful-finalization and injected finalization-record/destination failure tests proving no new partial/ambiguous package or record remains and the working session is still resumable.
9. Preserve full M02 manifest/path/checksum preflight and distinct error classes.
10. Filesystem/UI tests cover both success and injected partial/crash failure at the real production seam.
11. Relevant regressions and git diff --check are clean/truthful.
12. Child log records exact evidence and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
