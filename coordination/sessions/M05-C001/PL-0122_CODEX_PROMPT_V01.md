# PL-0122 — Codex Work Order V01

Task: **PL-0122 — QR and pairing-code workflow**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03 and M04 must remain accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Reuse the accepted M02 PackScan contracts and M03/M04 session/finalization architecture. Do not create parallel package writers, camera/session owners or mutable export formats.

## Mandatory implementation

1. Create a receiver pairing offer containing receiver instance ID, host/port, protocol version, short-lived pairing ID/code, expiry, and TLS certificate fingerprint or equivalent pinning identity supplied by PL-0123.
2. Windows receiver must expose both a human-enterable pairing code and a QR payload representing the same offer.
3. iOS must support manual pairing-code entry and QR payload parsing/scanning; any camera-based QR scanner must never run concurrently with the production capture session and must hand camera ownership back cleanly.
4. Pairing offers must expire, be single-use or explicitly revocable, and must not contain long-lived secrets in logs.
5. Store only the minimum paired-receiver identity needed for reconnect; do not persist the one-time pairing code.
6. Add tests for valid/expired/wrong receiver/wrong version/malformed QR/manual-code flows and non-concurrent camera ownership.

## Validation

Add behavior-bearing success, failure, cancellation, restart and exact-boundary tests appropriate to the task. Run focused tests, the full declared locked suite, relevant iOS/static/project checks, `git diff --check`, protected-file checks, and privacy/signing/secret review. Native iPhone/Xcode/network hardware claims may be made only if genuinely executed.

Create one implementation/evidence commit and then a separate child log-only commit. Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
