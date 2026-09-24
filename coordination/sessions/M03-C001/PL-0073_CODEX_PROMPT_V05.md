# PL-0073 — Codex Remediation Work Order V05

Task: **PL-0073 — Focus production-runtime composition closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve all already accepted M03 children and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M04.

Preserve all correct Batch-004 implementation. Close only the remaining independent-audit finding.

## Mandatory remediation
1. Create the production camera-control composition at the same selected main-wide device used by capture and call CaptureRuntimeViewModel.bindCameraControls with AVFoundationCameraControlComposition.controls.
2. Ensure focus configure/observe/lock commands used by the app flow operate only through that selected coordinator and publish their real state into the runtime UI.
3. Add injected/conditional tests for wrong-device rejection, adjusting→stable observation, lock-before-stable failure, lock-after-stable success and CaptureRuntimeViewModel state propagation.
4. Do not add a parallel focus owner or bypass the shared coordinator.

Use production-used injected seams for Apple-framework behavior where needed. Run focused behavior tests, relevant M03 regression, project/static checks, git diff --check, protected-file and privacy/signing checks. Native execution may be claimed only if actually run.

Create one implementation commit and one separate log-only commit. User-facing links in the handoff must be full GitHub URLs, never local filesystem paths.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
