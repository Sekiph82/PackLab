# PL-0088 — Codex Remediation Work Order V05

Task: **PL-0088 — All-stage crash transaction evidence closure**
Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve PL-0068 OWNER_REQUIRED and all accepted M03 children. Never edit TASKS.md/audits. Never start M04.

## Mandatory remediation
1. Preserve the current previous-state rollback and partial-final-move recovery algorithm.
2. Add failure-injection tests for transaction.prepare, sourceStage, recordStage, stateStage, sourceCommit, recordCommit and stateCommit.
3. For every stage, reopen must yield either the fully accepted capture or the exact clean pre-capture state with no orphan source/record and consistent state.
4. Add malformed/missing transaction-marker recovery evidence and keep the canonical record format.

Preserve all correct Batch-004 code. Use production-used injected seams and real temporary-directory failure injection where appropriate. Run focused/relevant regression, project/static, git diff --check and protected/privacy checks truthfully.

Create one implementation commit and one log-only commit. User-facing links must be full GitHub URLs, never local paths. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
