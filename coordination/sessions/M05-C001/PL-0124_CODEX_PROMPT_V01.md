# PL-0124 — Codex Work Order V01

Task: **PL-0124 — Resumable large-package transfer**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0124_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03 and M04 must remain accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Reuse the accepted M02 PackScan contracts and M03/M04 session/finalization architecture. Do not create parallel package writers, camera/session owners or mutable export formats.

## Mandatory implementation

1. Implement persisted receiver-side transfer state using `.part` data plus an atomic sidecar/checkpoint keyed by transfer ID.
2. Support chunk/range upload with a deterministic next-required byte offset and idempotent retransmission of already-confirmed bytes.
3. Sender must query receiver status after reconnect/restart and resume from the authoritative confirmed offset rather than restart blindly.
4. Receiver restart and sender cancellation must not publish a completed package or lose already-verified resumable bytes.
5. Detect conflicting bytes/offsets/package identity and fail closed instead of splicing incompatible content.
6. Add tests for mid-transfer disconnect, sender restart, receiver restart, duplicate chunk, out-of-order chunk, conflicting chunk, cancel/retry and multi-chunk large-package completion.

## Validation

Add behavior-bearing success, failure, cancellation, restart and exact-boundary tests appropriate to the task. Run focused tests, the full declared locked suite, relevant iOS/static/project checks, `git diff --check`, protected-file checks, and privacy/signing/secret review. Native iPhone/Xcode/network hardware claims may be made only if genuinely executed.

Create one implementation/evidence commit and then a separate child log-only commit. Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
