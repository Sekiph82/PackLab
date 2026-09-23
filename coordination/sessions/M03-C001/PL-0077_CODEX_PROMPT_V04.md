# PL-0077 — Codex Remediation Work Order V04

Task: **PL-0077 — Recovery owner production-composition closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve Batch-003 progress and close only the remaining audit boundary.

## Mandatory remediation
1. Wire CameraRecoveryOwner.onStateChange into the real capture runtime/UI so interruption/restarting/permission/failure messages become visible state rather than owner-internal values.
2. Ensure the production still adapter is bound to the same recovery owner so interruption/runtime error cancels the exact in-flight photo request.
3. Make restart callbacks invoke the one real preview/session owner and prove observer registration/unregistration remains idempotent.
4. Add injected notification/session tests covering denied/restricted, interruption, interruptionEnded restart success/failure, runtime error retry bound, in-flight cancellation and UI state propagation.

Use injected drivers/fakes where needed so Apple-framework behavior is testable in source even if Windows cannot execute Xcode. Run all available regression/static/project checks truthfully.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
