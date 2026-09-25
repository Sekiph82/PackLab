# PL-0125 — Codex Remediation Work Order V04

Task: **PL-0125 — Complete production Swift completion failure matrix**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_LOG_V04.md

TASKS.md must authorize `M05-BATCH-004 / READY / CODEX`. Preserve all 10 accepted M05 children, accepted M03/M04, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Preserve the accepted architecture. Close only the final independent-audit gap.

## Mandatory remediation

1. Preserve the hardened production completion gate requiring matching transfer ID, digest, authenticated=true, verified=true and terminal verified/complete state.
2. Add an injectable production URLSession/transport seam if needed so URLSessionTransferClient acknowledgement validation can be tested deterministically without native network execution.
3. Add tests for matching success, wrong transfer ID, wrong digest, unauthenticated acknowledgement, non-terminal acknowledgement, corrupted/wrong-declared package digest, retry after mismatch and no premature completion.
4. Prove every rejected acknowledgement leaves sender state retryable, preserves persisted resumable identity, and never marks the source completed/exported-to-receiver.
5. Keep receiver whole-package SHA-256 verification unchanged.

Run production-seam behavior tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V04 log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
