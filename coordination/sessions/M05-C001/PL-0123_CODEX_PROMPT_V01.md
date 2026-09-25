# PL-0123 — Codex Work Order V01

Task: **PL-0123 — Encrypted and authenticated local transfer**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03 and M04 must remain accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Reuse the accepted M02 PackScan contracts and M03/M04 session/finalization architecture. Do not create parallel package writers, camera/session owners or mutable export formats.

## Mandatory implementation

1. Implement the PL-0121 network transport over TLS using standard platform cryptography; do not design custom encryption primitives.
2. Windows receiver must use a locally generated TLS certificate/key kept outside Git; iOS must pin/verify the receiver identity from the pairing offer rather than blindly trusting any self-signed certificate.
3. Authenticate the transfer session with the short-lived pairing exchange and issue a scoped session credential/token that cannot be reused after expiry/revocation.
4. Reject unpaired clients, wrong certificate fingerprints, replayed/expired pairing offers, wrong receiver IDs and downgraded/insecure transport.
5. Keep secrets/cert private keys out of logs, diagnostics, `.packscan`, Git and user-facing QR payloads except the non-secret certificate fingerprint and short-lived pairing material required by the workflow.
6. Add deterministic integration tests with ephemeral test certificates for successful TLS/auth, wrong pin, expired/replayed code, missing auth and secret-redaction behavior.

## Validation

Add behavior-bearing success, failure, cancellation, restart and exact-boundary tests appropriate to the task. Run focused tests, the full declared locked suite, relevant iOS/static/project checks, `git diff --check`, protected-file checks, and privacy/signing/secret review. Native iPhone/Xcode/network hardware claims may be made only if genuinely executed.

Create one implementation/evidence commit and then a separate child log-only commit. Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
