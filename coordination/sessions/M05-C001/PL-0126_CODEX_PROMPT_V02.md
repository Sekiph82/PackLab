# PL-0126 — Codex Remediation Work Order V02

Task: **PL-0126 — Production iOS transfer screen and network-bound cancel/retry**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M05-BATCH-002 / READY / CODEX`. Preserve accepted PL-0127, PL-0129 and PL-0131, all accepted M03/M04 behavior, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Preserve useful V01 implementation. Close only the independent-audit gaps below, converging on one production finalized-package export/transfer/ingest architecture.

## Mandatory remediation

1. Preserve TransferViewModel state semantics and confirmed-byte progress calculation.
2. Add a real SwiftUI transfer screen reachable from finalized scan/history flow and bound to the production iOS network transfer client.
3. Show receiver identity, package name/size, confirmed bytes/percentage, phase and errors for every frozen UI state.
4. Cancel must cancel active network work/notify receiver without deleting the finalized source package; retry must query authoritative receiver status and resume the same transfer.
5. Add view-model/service tests for reconnect/resume, network cancel, checksum failure, terminal failure, monotonic progress and verified completion.

## Validation

Add behavior-bearing tests at the production-used UI/network/receiver/ingest seam as applicable. Run focused tests, full locked suite, relevant Swift/static/project checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret/signing checks. Native/physical iPhone/AirDrop/real-LAN claims may be made only if genuinely executed.

Create one implementation/evidence commit and then one separate log-only commit. Every user-facing repository reference must be a full GitHub URL.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
