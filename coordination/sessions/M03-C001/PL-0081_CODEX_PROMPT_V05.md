# PL-0081 — Codex Remediation Work Order V05

Task: **PL-0081 — Motion accepted-persistence closure**
Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve PL-0068 OWNER_REQUIRED and all accepted M03 children. Never edit TASKS.md/audits. Never start M04.

## Mandatory remediation
1. Keep exactly one physical MotionService/CMMotionManager ownership path; CoreMotionController may only project an injected service and may not allocate its own pipeline.
2. Wire real accepted-still orchestration to persist MotionCaptureBinding derived from MotionService records using the same monotonic capture timestamp semantics as PL-0080.
3. Add integrated tests for available/stale/unavailable motion evidence, one-owner composition and AcceptedCaptureRecord.motionBinding persistence/reopen.
4. Preserve bounded buffering, quaternion attitude and rotation-rate evidence.

Preserve all correct Batch-004 code. Use production-used injected seams and real temporary-directory failure injection where appropriate. Run focused/relevant regression, project/static, git diff --check and protected/privacy checks truthfully.

Create one implementation commit and one log-only commit. User-facing links must be full GitHub URLs, never local paths. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
