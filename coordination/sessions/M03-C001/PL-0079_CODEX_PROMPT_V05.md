# PL-0079 — Codex Remediation Work Order V05

Task: **PL-0079 — AR physical-owner behavior-test closure**
Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0079_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve PL-0068 OWNER_REQUIRED and all accepted M03 children. Never edit TASKS.md/audits. Never start M04.

## Mandatory remediation
1. Preserve SharedARSessionOwner and ARSessionLifecycleDriver architecture.
2. Add conditional/injected tests that construct SharedARSessionOwner(injectedDriver:) and verify repeated start/stop, unsupported world tracking, interruption/interruption-end, reset run-options and no duplicate session ownership/listener behavior.
3. Exercise ARKitTrackingService through that injected owner and verify state mapping.
4. Keep simulator unavailable behavior and non-LiDAR configuration.

Preserve all correct Batch-004 work. Add behavior-bearing tests at the production-used seam. Run focused/relevant regression, static/project, git diff --check and protected/privacy checks truthfully.

Create one implementation commit and one log-only commit. User-facing links must be full GitHub URLs, never local paths. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
