# PL-0084 — Codex Remediation Work Order V04

Task: **PL-0084 — AR owner reset lifecycle-test closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. Preserve PL-0070 acceptance and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/audits. Never start M04.

Preserve current working Batch-003 implementation and close only the remaining frozen evidence/integration boundary.

## Mandatory remediation
1. Preserve the real SharedARSessionOwner reset/degradation/interruption logic.
2. Extract an injectable AR session driver/state callback seam used by the owner and test reset→relocalizing→recovered, reset→failed, repeated reset, degradation-threshold reset and interruption reset.
3. Prove old-epoch pose evidence is rejected after reset and reset diagnostics record reason/epoch/result from the real owner path.
4. Do not add another AR session owner.

Where Apple frameworks cannot run on Windows, add injectable production-used seams and conditional XCTest sources; report native execution honestly.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
