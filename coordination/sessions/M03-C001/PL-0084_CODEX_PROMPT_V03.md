# PL-0084 — Codex Remediation Work Order V03

Task: **PL-0084 — AR reset recovery/diagnostics remediation**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_LOG_V03.md

TASKS.md must authorize M03-BATCH-003 / READY / CODEX. PL-0070 remains accepted and PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve every previously passing behavior and close every finding in the previous independent audit.

## Mandatory remediation
1. Complete reset lifecycle by marking the current epoch recovered only after real stable tracking returns, and failed when recovery cannot complete.
2. Wire tracking-degradation/interruption/user reset triggers to the actual SharedARSessionOwner reset path.
3. Persist reset reason/epoch/result diagnostics from the real owner, not only a standalone coordinator.
4. Add tests for reset→relocalizing→recovered/failed, repeated resets, degraded-trigger reset and old-epoch pose rejection.

Run focused behavior tests plus relevant M03 regression, project checks, git diff --check, protected-file and privacy/signing review. Native Xcode/iPhone results may be claimed only if actually executed.

Create a distinct implementation commit and a separate log-only commit. End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
