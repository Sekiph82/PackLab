# PL-0092 — Codex Remediation Work Order V04

Task: **PL-0092 — Authoritative history validation/test closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0092_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve all correct Batch-003 functionality and close the remaining persistence/destructive boundary only.

## Mandatory remediation
1. Validate SessionFinalizationRecord.sessionID against the containing session and restrict state to a closed enum/known values.
2. For exported/finalized records, verify the referenced packagePath exists and is a valid file before reporting exported; otherwise retain a degraded row.
3. Add tests for actual in_progress→exported transition produced by SessionFinalizer, missing exported package, corrupt/foreign-session finalization record, corrupt metadata, missing preview and deterministic multi-session ordering.
4. Keep history preview-only and authoritative-state derived.

Use real temporary-directory failure injection for filesystem boundaries. Run all available regression/static/project validation and git diff --check truthfully.

Create one implementation commit and one separate log-only commit. End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
