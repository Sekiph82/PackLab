# PL-0074 — Codex Remediation Work Order V03

Task: **PL-0074 — Exposure selected-device/metadata remediation**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_LOG_V03.md

TASKS.md must authorize M03-BATCH-003 / READY / CODEX. PL-0070 remains accepted and PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve every previously passing behavior and close every finding in the previous independent audit.

## Mandatory remediation
1. Make selected-device identity and shared CameraConfigurationCoordinator mandatory for the physical exposure adapter.
2. Bind ExposureCaptureBinding into the accepted PhotoCaptureMetadata construction/persistence path with actual mode/value provenance.
3. Expose metering/locked/unavailable/failure state through the real capture UI/view model.
4. Add tests for wrong-device rejection, serialized configuration, bounds/unsupported lock and accepted-photo metadata persistence.

Run focused behavior tests plus relevant M03 regression, project checks, git diff --check, protected-file and privacy/signing review. Native Xcode/iPhone results may be claimed only if actually executed.

Create a distinct implementation commit and a separate log-only commit. End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
