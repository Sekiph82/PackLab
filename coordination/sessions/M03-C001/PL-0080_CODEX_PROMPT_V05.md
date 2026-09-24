# PL-0080 — Codex Remediation Work Order V05

Task: **PL-0080 — Accepted-still pose persistence closure**
Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0080_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve PL-0068 OWNER_REQUIRED and all accepted M03 children. Never edit TASKS.md/audits. Never start M04.

## Mandatory remediation
1. Wire the real accepted-still orchestration to ScanSessionStore.storeAcceptedCapture(still:...) so pose evidence is bound and persisted for actual captures, not only exposed as an unused overload.
2. Use the still's monotonic capture timestamp and explicit fallback bridge semantics only when needed.
3. Add integrated tests for accepted still→PoseBuffer→AcceptedCaptureRecord.poseBinding→reopen persistence, including available/stale/unavailable/out-of-order cases.
4. Do not silently omit pose status when evidence is unavailable.

Preserve all correct Batch-004 work. Add behavior-bearing tests at the production-used seam. Run focused/relevant regression, static/project, git diff --check and protected/privacy checks truthfully.

Create one implementation commit and one log-only commit. User-facing links must be full GitHub URLs, never local paths. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
