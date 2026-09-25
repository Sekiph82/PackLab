# PL-0121 — Codex Work Order V01

Task: **PL-0121 — Local-network transfer protocol V1**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03 and M04 must remain accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Reuse the accepted M02 PackScan contracts and M03/M04 session/finalization architecture. Do not create parallel package writers, camera/session owners or mutable export formats.

## Mandatory implementation

1. Define a versioned PackLab Transfer Protocol V1 shared by iOS Capture and the Python/Windows receiver.
2. Protocol must transfer a finalized `.packscan` as an opaque package, never individual mutable session files.
3. Define receiver identity, protocol version negotiation, transfer ID, package capture_id, total byte size, whole-package SHA-256, chunk/range semantics, status/query, completion acknowledgement, cancellation and stable error codes.
4. Design the protocol for HTTPS/TLS transport and authenticated pairing; PL-0123 will implement the security handshake, but insecure production fallback must not be part of the contract.
5. Make retry/resume idempotent: repeated create/status/chunk requests must not duplicate or corrupt bytes.
6. Add cross-language golden fixtures/tests proving Swift/Python message field names, validation, version rejection and stable error mapping.

## Validation

Add behavior-bearing success, failure, cancellation, restart and exact-boundary tests appropriate to the task. Run focused tests, the full declared locked suite, relevant iOS/static/project checks, `git diff --check`, protected-file checks, and privacy/signing/secret review. Native iPhone/Xcode/network hardware claims may be made only if genuinely executed.

Create one implementation/evidence commit and then a separate child log-only commit. Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
