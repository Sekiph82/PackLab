# PL-0077 — Codex Remediation Work Order V05

Task: **PL-0077 — Unified recovery-owner composition closure**
Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0077_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve PL-0068 OWNER_REQUIRED and all accepted M03 children. Never edit TASKS.md/audits. Never start M04.

## Mandatory remediation
1. Make preview/session restart, permission state, runtime errors and still-capture cancellation use one production CameraRecoveryOwner rather than separate preview/private and capture/runtime owners.
2. Bind the unified owner's onStateChange into CaptureRuntimeViewModel/UI and its cancellation hook into the production still adapter.
3. Ensure interruptionEnded/runtime-error retries restart the one active session owner with bounded/idempotent observer registration.
4. Add injected notification/session tests for permission, interruption/end, retry success/failure, in-flight cancellation and UI state propagation.

Preserve all correct Batch-004 work. Add behavior-bearing tests at the production-used seam. Run focused/relevant regression, static/project, git diff --check and protected/privacy checks truthfully.

Create one implementation commit and one log-only commit. User-facing links must be full GitHub URLs, never local paths. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
