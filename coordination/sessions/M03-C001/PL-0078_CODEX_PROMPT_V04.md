# PL-0078 — Codex Remediation Work Order V04

Task: **PL-0078 — Health gate physical capture enforcement closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0078_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve Batch-003 progress and close only the remaining audit boundary.

## Mandatory remediation
1. Compose HealthGatedStillPhotoBackend (or equivalent) into the real production still-capture service and feed it the same live CaptureAdmissionController updated by DeviceHealthMonitor.
2. Ensure hardStop prevents the physical capture request before NextLevel capturePhoto is called, warning still allows capture, and recovery to ready re-enables capture.
3. Keep DeviceHealthMonitor start/stop tied to capture runtime lifecycle and preserve simulator unavailable semantics.
4. Add integrated tests proving provider update→runtime admission→physical backend call/no-call behavior.

Use injected drivers/fakes where needed so Apple-framework behavior is testable in source even if Windows cannot execute Xcode. Run all available regression/static/project checks truthfully.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
