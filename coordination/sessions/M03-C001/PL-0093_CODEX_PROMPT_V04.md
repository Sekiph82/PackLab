# PL-0093 — Codex Remediation Work Order V04

Task: **PL-0093 — Deletion failure semantics/symlink closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve all correct Batch-003 functionality and close the remaining persistence/destructive boundary only.

## Mandatory remediation
1. Make SafeSessionDeleter.delete(plan:confirmed:) inspect DeletionReport and throw/report partialFailure whenever failures are non-empty; no deletion API may silently return success on partial failure.
2. Preserve authoritative candidate requirement and real UI detailed failure reporting/history cleanup.
3. Add real temporary-filesystem symlink-escape tests plus missing-session, cancellation, traversal, injected session failure and injected history-index failure tests.
4. Ensure destructive behavior never follows or deletes outside-root symlink targets.

Use real temporary-directory failure injection for filesystem boundaries. Run all available regression/static/project validation and git diff --check truthfully.

Create one implementation commit and one separate log-only commit. End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
