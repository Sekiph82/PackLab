# PL-0125 — Codex Remediation Work Order V02

Task: **PL-0125 — End-to-end verified completion closure**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0125_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M05-BATCH-002 / READY / CODEX`. Preserve accepted PL-0127, PL-0129 and PL-0131, all accepted M03/M04 behavior, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Preserve useful V01 implementation. Close only the independent-audit gaps below, converging on one production finalized-package export/transfer/ingest architecture.

## Mandatory remediation

1. Preserve whole-package SHA-256 receiver verification and stored expected/actual/byte-count evidence.
2. Wire authenticated receiver completion acknowledgement into the production iOS transfer client and TransferViewModel.
3. Sender must not mark completed until transfer ID and package digest match, acknowledgement is authenticated, and receiver reports verified completion.
4. Checksum mismatch must never publish normal inbox content; retry behavior must remain explicit and resumable/restartable according to policy.
5. Add integrated tests for matching digest, final-byte corruption, wrong declared digest, retry after mismatch and sender never completing before verified authenticated acknowledgement.

## Validation

Add behavior-bearing tests at the production-used UI/network/receiver/ingest seam as applicable. Run focused tests, full locked suite, relevant Swift/static/project checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret/signing checks. Native/physical iPhone/AirDrop/real-LAN claims may be made only if genuinely executed.

Create one implementation/evidence commit and then one separate log-only commit. Every user-facing repository reference must be a full GitHub URL.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
