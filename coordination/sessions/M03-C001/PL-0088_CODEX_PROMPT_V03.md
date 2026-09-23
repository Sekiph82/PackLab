# PL-0088 — Codex Remediation Work Order V03

Task: **PL-0088 — Crash-atomic accepted-capture transaction remediation**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_LOG_V03.md

TASKS.md must authorize M03-BATCH-003 / READY / CODEX. PL-0070 remains accepted and PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve every previously passing behavior and close every finding in the previous independent audit.

## Mandatory remediation
1. Define one canonical per-photo persisted record format used consistently by ScanSessionStore, gallery, resume and finalization.
2. Make accepted-capture persistence crash-recoverable across source, record and state using staging/transaction marker or equivalent deterministic complete/rollback recovery.
3. Detect and recover every partial transaction stage on reopen, including orphan source, orphan record and stale state.
4. Add filesystem failure-injection tests for interruption/crash after each transaction stage plus corrupt/incomplete reopen.

Run focused behavior tests plus relevant M03 regression, project checks, git diff --check, protected-file and privacy/signing review. Native Xcode/iPhone results may be claimed only if actually executed.

Create a distinct implementation commit and a separate log-only commit. End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
