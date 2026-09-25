# PL-0124 — Codex Remediation Work Order V02

Task: **PL-0124 — Production sender reconnect/resume closure**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M05-BATCH-002 / READY / CODEX`. Preserve accepted PL-0127, PL-0129 and PL-0131, all accepted M03/M04 behavior, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Preserve useful V01 implementation. Close only the independent-audit gaps below, converging on one production finalized-package export/transfer/ingest architecture.

## Mandatory remediation

1. Preserve ResumableTransferStore receiver behavior and checkpoint format.
2. Implement sender-side status query/reconnect in the production iOS transfer client; after app/network restart resume from receiver-confirmed next_offset rather than starting from zero.
3. Persist only the minimum non-secret sender transfer identity required to reconnect to an existing resumable transfer.
4. Prove receiver restart and sender cancellation preserve verified resumable bytes and never publish incomplete content.
5. Add integrated sender/receiver tests for disconnect, sender restart, receiver restart, duplicate/out-of-order/conflicting chunks, cancel/resume and multi-chunk completion.

## Validation

Add behavior-bearing tests at the production-used UI/network/receiver/ingest seam as applicable. Run focused tests, full locked suite, relevant Swift/static/project checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret/signing checks. Native/physical iPhone/AirDrop/real-LAN claims may be made only if genuinely executed.

Create one implementation/evidence commit and then one separate log-only commit. Every user-facing repository reference must be a full GitHub URL.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
