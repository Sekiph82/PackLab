# PL-0126 — Codex Work Order V01

Task: **PL-0126 — Transfer progress, cancel and retry UI**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03 and M04 must remain accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Reuse the accepted M02 PackScan contracts and M03/M04 session/finalization architecture. Do not create parallel package writers, camera/session owners or mutable export formats.

## Mandatory implementation

1. Add iOS transfer UI bound to the production network transfer service showing paired receiver identity, package name/size, bytes sent, percentage, transfer phase and errors.
2. Progress must come from confirmed protocol bytes/offsets, not an optimistic timer.
3. Cancel must stop active network work without deleting the finalized source package and must preserve resumable receiver state unless the user explicitly discards it.
4. Retry/reconnect must resume through PL-0124 status rather than silently start a second transfer.
5. Expose clear states for pairing required, connecting, transferring, verifying, completed, cancelled, retryable failure and terminal failure.
6. Add view-model/service tests for progress monotonicity, cancel, retry, reconnect/resume, checksum failure and completed-state acknowledgement.

## Validation

Add behavior-bearing success, failure, cancellation, restart and exact-boundary tests appropriate to the task. Run focused tests, the full declared locked suite, relevant iOS/static/project checks, `git diff --check`, protected-file checks, and privacy/signing/secret review. Native iPhone/Xcode/network hardware claims may be made only if genuinely executed.

Create one implementation/evidence commit and then a separate child log-only commit. Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
