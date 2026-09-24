# PL-0084 — Codex Remediation Work Order V05

Task: **PL-0084 — AR reset owner-test closure**
Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve PL-0068 OWNER_REQUIRED and all accepted M03 children. Never edit TASKS.md/audits. Never start M04.

## Mandatory remediation
1. Preserve the current SharedARSessionOwner reset/recovery implementation.
2. Add conditional/injected tests using ARSessionLifecycleDriver that exercise reset→relocalizing→recovered, reset→failed, repeated reset, degradation-threshold reset and interruption reset on the real owner.
3. Verify old-epoch pose rejection and ResetDiagnosticEvent reason/epoch/result from the real owner path.
4. Do not add another AR owner.

Preserve all correct Batch-004 code. Use production-used injected seams and real temporary-directory failure injection where appropriate. Run focused/relevant regression, project/static, git diff --check and protected/privacy checks truthfully.

Create one implementation commit and one log-only commit. User-facing links must be full GitHub URLs, never local paths. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
