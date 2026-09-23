# PL-0075 — Codex Remediation Work Order V04

Task: **PL-0075 — White-balance runtime/metadata binding closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M04.

Preserve all correct Batch-003 source. Fix only the remaining audit boundary.

## Mandatory remediation
1. Connect physical white-balance adapter state to CaptureRuntimeViewModel controls using the selected CameraDeviceConfigurationCoordinator.
2. Observe adjustingWhiteBalance until stable before lock; on accepted still propagate observed temperature through AcceptedPhotoMetadataFactory into persisted photo metadata.
3. Add integrated tests for wrong-device rejection, unstable-lock rejection, stable-lock success, UI propagation and accepted-photo metadata persistence.
4. Do not invent temperature/tint/gain values.

Tests may use injected Apple-framework drivers/fakes and conditional compilation so they are reviewable on GitHub even when Windows cannot execute Xcode. Do not claim native execution unless actually run.

Create one implementation commit and one log-only commit. End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
