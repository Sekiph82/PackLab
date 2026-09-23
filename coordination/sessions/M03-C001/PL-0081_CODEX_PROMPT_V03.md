# PL-0081 — Codex Remediation Work Order V03

Task: **PL-0081 — Unified CoreMotion service remediation**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_LOG_V03.md

TASKS.md must authorize M03-BATCH-003 / READY / CODEX. PL-0070 remains accepted and PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve every previously passing behavior and close every finding in the previous independent audit.

## Mandatory remediation
1. Remove or subsume the parallel CoreMotionController so the existing MotionService is the single physical motion pipeline.
2. Make the physical MotionService provide the required attitude/quaternion and rotation-rate samples, not acceleration-only data.
3. Bind actual MotionService samples to accepted captures through the same explicit timestamp-domain/tolerance rules.
4. Add tests for single ownership, unavailable/error states, attitude/rotation-rate recording, bounded buffering and accepted-capture alignment.

Run focused behavior tests plus relevant M03 regression, project checks, git diff --check, protected-file and privacy/signing review. Native Xcode/iPhone results may be claimed only if actually executed.

Create a distinct implementation commit and a separate log-only commit. End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
