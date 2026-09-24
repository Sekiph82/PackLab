# PL-0075 — Codex Remediation Work Order V05

Task: **PL-0075 — White-balance production-runtime/metadata closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve all already accepted M03 children and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M04.

Preserve all correct Batch-004 implementation. Close only the remaining independent-audit finding.

## Mandatory remediation
1. Use the same production AVFoundationCameraControlComposition and publish white-balance state into CaptureRuntimeViewModel.
2. Observe adjustingWhiteBalance until stable before lock, then feed only actual observed temperature/readings into AcceptedPhotoMetadataFactory for the accepted photo persistence path.
3. Add integrated tests for wrong-device rejection, unstable-lock rejection, stable-lock success, runtime UI propagation and persisted WB metadata.
4. Do not invent temperature, tint or gain evidence.

Use production-used injected seams for Apple-framework behavior where needed. Run focused behavior tests, relevant M03 regression, project/static checks, git diff --check, protected-file and privacy/signing checks. Native execution may be claimed only if actually run.

Create one implementation commit and one separate log-only commit. User-facing links in the handoff must be full GitHub URLs, never local filesystem paths.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
