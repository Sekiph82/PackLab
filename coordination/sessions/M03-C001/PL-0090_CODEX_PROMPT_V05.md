# PL-0090 — Codex Remediation Work Order V05

Task: **PL-0090 — Resume/discard failure-matrix closure**
Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve PL-0068 OWNER_REQUIRED and all accepted M03 children. Never edit TASKS.md/audits. Never start M04.

## Mandatory remediation
1. Preserve SessionDiscoveryService use of ScanSessionStore.reopen, ActiveScanSession installation and safe discard.
2. Add integrated discovery/resume tests for every PL-0088 partial transaction stage, stale temp/transaction markers, missing/corrupt source or per-photo record and schema-version mismatch.
3. Ensure the SessionResumeCandidate.state installed on Resume is the recovered authoritative state returned after reopen, not a stale pre-recovery decode.
4. Add real discard behavior tests proving the selected resumable session is removed safely and blocked sessions are never offered Resume.

Preserve all correct Batch-004 behavior. Use real temporary-directory failure injection for persistence/destructive tests. Run focused/relevant regression, project/static, git diff --check and protected/privacy checks truthfully.

Create one implementation commit and one log-only commit. User-facing links must be full GitHub URLs, never local paths. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
