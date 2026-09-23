# PL-0079 — Codex Remediation Work Order V04

Task: **PL-0079 — AR physical-owner lifecycle test closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve Batch-003 progress and close only the remaining audit boundary.

## Mandatory remediation
1. Preserve SharedARSessionOwner as the single physical owner and ARTrackingService as the app seam.
2. Extract/inject the minimum ARSession running/capability driver used by SharedARSessionOwner so lifecycle behavior can be tested without real hardware.
3. Add tests through ARTrackingService/owner for repeated start/stop, unsupported world tracking, interruption/interruption-end, state mapping and prevention of duplicate session ownership/listener setup.
4. Keep non-LiDAR world tracking and simulator unavailable behavior.

Use injected drivers/fakes where needed so Apple-framework behavior is testable in source even if Windows cannot execute Xcode. Run all available regression/static/project checks truthfully.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
