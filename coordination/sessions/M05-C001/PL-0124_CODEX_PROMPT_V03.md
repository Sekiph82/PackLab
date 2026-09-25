# PL-0124 — Codex Remediation Work Order V03

Task: **PL-0124 — Persisted same-transfer sender resume across retry/app restart**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_LOG_V03.md

## Authorization

TASKS.md must authorize `M05-BATCH-003 / READY / CODEX`. Preserve accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 plus accepted M03/M04. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Read the V02 audit first. Preserve useful implementation and close exactly these remaining gaps.

## Mandatory remediation

1. Preserve ResumableTransferStore receiver checkpoints and current production URLSession client.
2. Actually use SenderTransferIdentityStore when a transfer is first created: persist transfer ID, package digest and receiver identity before/while network work begins.
3. Ensure TransferRequest/networkRequest is rewritten with the resolved transfer ID. retryNetworkTransfer must never generate a new UUID for an existing resumable transfer.
4. Add app/runtime restart restore: load persisted sender identity, verify current finalized package digest + receiver identity match, query receiver status, rebuild the request with the same transfer ID, and continue from receiver next_offset.
5. Clear persisted sender identity only after verified completion or explicit user discard; cancellation alone must preserve resumability.
6. Add deterministic fake ProductionTransferClient tests proving first ID persistence, same-ID retry, app-restart restore, receiver-confirmed offset resume, cancel/resume, conflicting identity fail-closed and no duplicate transfer creation.

## Validation

Tests must drive production-used seams, not a parallel helper. Run focused tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and secrets/privacy/signing checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V03 log-only commit. All user-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
