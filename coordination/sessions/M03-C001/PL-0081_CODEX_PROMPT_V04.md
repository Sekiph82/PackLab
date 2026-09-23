# PL-0081 — Codex Remediation Work Order V04

Task: **PL-0081 — Single MotionService + accepted binding closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve Batch-003 progress and close only the remaining audit boundary.

## Mandatory remediation
1. Remove CoreMotionController or refactor it so it cannot create a second CoreMotionMotionService/CMMotionManager; only one physical MotionService instance may own device motion.
2. Bind accepted stills to MotionService's bounded records using the same capture monotonic timestamp/domain semantics as PL-0080 and persist MotionCaptureBinding.
3. Preserve attitude quaternion and rotation-rate evidence, unavailable/error state, and bounded buffering.
4. Add tests proving one-owner composition and accepted-still motion binding for available/stale/unavailable cases.

Use injected drivers/fakes where needed so Apple-framework behavior is testable in source even if Windows cannot execute Xcode. Run all available regression/static/project checks truthfully.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
