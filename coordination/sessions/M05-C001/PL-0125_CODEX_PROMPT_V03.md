# PL-0125 — Codex Remediation Work Order V03

Task: **PL-0125 — Swift production completion identity/state hardening**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_LOG_V03.md

## Authorization

TASKS.md must authorize `M05-BATCH-003 / READY / CODEX`. Preserve accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 plus accepted M03/M04. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Read the V02 audit first. Preserve useful implementation and close exactly these remaining gaps.

## Mandatory remediation

1. Preserve receiver whole-package SHA-256 verification and stored expected/actual/byte-count evidence.
2. In URLSessionTransferClient validate acknowledgement transferID equals the active transfer ID, package digest matches, authenticated=true, verified=true, and state is terminal verified/complete before returning success.
3. In TransferViewModel applyCompletion also reject wrong transfer ID and non-terminal acknowledgement state; do not rely only on digest/authenticated/verified.
4. Checksum mismatch/wrong transfer/non-terminal acknowledgement must leave sender retryable and must never clear persisted resumable identity or mark source exported-to-receiver complete.
5. Add injected ProductionTransferClient/URLProtocol tests for matching success, wrong transfer ID, wrong digest, unauthenticated ack, non-terminal ack, final-byte corruption/wrong declared digest, retry after mismatch and no premature completion.

## Validation

Tests must drive production-used seams, not a disconnected helper/static grep. Run focused tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and secrets/privacy checks.

Create one implementation/evidence commit and one separate V03 log-only commit. All user-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
