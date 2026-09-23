# PL-0071 — Codex Remediation Work Order V04

Task: **PL-0071 — Still adapter production-composition/test closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M04.

Preserve all correct Batch-003 source. Fix only the remaining audit boundary.

## Mandatory remediation
1. Create the production composition that constructs NextLevelStillCaptureAdapter from the deterministic PL-0070 main-wide CameraLensIdentity and the active NextLevel/session lens identity source.
2. Bind the adapter to CameraRecoveryOwner so interruption/session stop cancels the exact in-flight continuation once.
3. Add an injectable NextLevel photo-driver/delegate seam used by the adapter and behavior tests for success, missing data, duplicate callback, overlap, cancellation, selected-lens mismatch and session stop.
4. Preserve high-resolution original bytes/dimensions and exact-once completion.

Tests may use injected Apple-framework drivers/fakes and conditional compilation so they are reviewable on GitHub even when Windows cannot execute Xcode. Do not claim native execution unless actually run.

Create one implementation commit and one log-only commit. End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
