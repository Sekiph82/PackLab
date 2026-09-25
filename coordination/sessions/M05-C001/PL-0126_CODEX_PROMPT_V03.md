# PL-0126 — Codex Remediation Work Order V03

Task: **PL-0126 — Production transfer UI same-ID retry/cancel/failure test closure**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_LOG_V03.md

## Authorization

TASKS.md must authorize `M05-BATCH-003 / READY / CODEX`. Preserve accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 plus accepted M03/M04. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Read the V02 audit first. Preserve useful implementation and close exactly these remaining gaps.

## Mandatory remediation

1. Preserve the real finalized-history → FinalizedTransferWorkflowView → TransferScreen navigation.
2. Consume the PL-0124 persisted same-transfer resume implementation; retry must query status and continue the same transfer ID instead of starting a new transfer.
3. Cancel must invoke the production client cancellation path, retain the finalized source, and preserve resumable sender identity unless the user explicitly discards.
4. Ensure all frozen UI phases are reachable/truthful: pairingRequired, connecting, transferring, verifying, completed, cancelled, retryableFailure and terminalFailure.
5. Add deterministic fake ProductionTransferClient tests for network cancel, authoritative status query, same-ID reconnect/resume, monotonic confirmed progress, checksum retryable failure, terminal failure and verified completion.
6. Prove UI state after app/runtime restore is rebuilt from persisted sender identity + receiver status rather than optimistic local counters.

## Validation

Tests must drive production-used seams, not a disconnected helper/static grep. Run focused tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and secrets/privacy checks.

Create one implementation/evidence commit and one separate V03 log-only commit. All user-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
