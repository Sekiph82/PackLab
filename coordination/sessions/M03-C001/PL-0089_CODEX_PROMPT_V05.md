# PL-0089 — Codex Remediation Work Order V05

Task: **PL-0089 — Gallery mutation evidence closure**
Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0089_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve PL-0068 OWNER_REQUIRED and all accepted M03 children. Never edit TASKS.md/audits. Never start M04.

## Mandatory remediation
1. Preserve the real AcceptedFrameGalleryView retake callback and rollback-oriented SessionGalleryStore implementation.
2. Add behavior tests that invoke the real retake action/callback path and verify persisted replacement state, files and gallery audit.
3. Inject failures at multiple mutation stages, including source/record/state/audit publication for delete and retake, and prove rollback leaves one coherent old/new state with no orphan files.
4. Retain ordering, missing preview/source and corrupt-record behavior.

Preserve all correct Batch-004 behavior. Use real temporary-directory failure injection for persistence/destructive tests. Run focused/relevant regression, project/static, git diff --check and protected/privacy checks truthfully.

Create one implementation commit and one log-only commit. User-facing links must be full GitHub URLs, never local paths. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
