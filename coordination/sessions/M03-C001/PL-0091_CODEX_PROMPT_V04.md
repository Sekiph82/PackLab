# PL-0091 — Codex Remediation Work Order V04

Task: **PL-0091 — Atomic package + finalization-record publication closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0091_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve all correct Batch-003 functionality and close the remaining persistence/destructive boundary only.

## Mandatory remediation
1. Treat .packscan output plus session finalization.json as one publication transaction when sessionRoot is supplied.
2. If finalization-record write/replace fails after package creation, remove/roll back the newly created package or otherwise restore an unambiguous pre-finalization state.
3. Add successful-finalization and injected finalization-record/destination failure tests proving no new partial/ambiguous package or record remains and the working session is still resumable.
4. Preserve full M02 manifest/path/checksum preflight and distinct error classes.

Use real temporary-directory failure injection for filesystem boundaries. Run all available regression/static/project validation and git diff --check truthfully.

Create one implementation commit and one separate log-only commit. End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
