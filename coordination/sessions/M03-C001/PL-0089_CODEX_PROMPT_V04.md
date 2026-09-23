# PL-0089 — Codex Remediation Work Order V04

Task: **PL-0089 — Atomic gallery mutation + retake UI closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve all correct Batch-003 functionality and close the remaining persistence/destructive boundary only.

## Mandatory remediation
1. Wire AcceptedFrameGalleryView Retake to an actual retake callback/capture workflow instead of message-only behavior.
2. Make delete and retake use a recoverable transaction that atomically coordinates files, PersistedSessionState and gallery audit history.
3. On any mutation failure, recover to either the complete old state or complete new state with no orphan files/records and no false acceptedIDs.
4. Add filesystem/UI-action tests for delete confirmation, retake execution, transaction failures, ordering, missing source/preview and corrupt records.

Use real temporary-directory failure injection for filesystem boundaries. Run all available regression/static/project validation and git diff --check truthfully.

Create one implementation commit and one separate log-only commit. End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
