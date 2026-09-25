# PL-0122 — Codex Remediation Work Order V03

Task: **PL-0122 — Functional manual/QR pairing with real capture-camera ownership**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_LOG_V03.md

## Authorization

TASKS.md must authorize `M05-BATCH-003 / READY / CODEX`. Preserve accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 plus accepted M03/M04. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Read the V02 audit first. Preserve useful implementation and close exactly these remaining gaps.

## Mandatory remediation

1. Preserve PairingOffer, reconnect identity store and PairingCoordinator concepts.
2. Make the real Send-to-PackLab workflow support manual pairing without requiring a pre-injected PairingOffer that is unavailable in the UI. Provide a truthful offer acquisition/input mechanism containing receiver host/port/ID/fingerprint plus short-lived code, or a receiver-discovery mechanism explicitly within M05 scope.
3. Do not persist the one-time pairing code; persist only receiver ID, host, port and TLS fingerprint.
4. Do not present/start PairingQRScannerController until production camera ownership is actually acquired for pairing.
5. Bind pairing scanner ownership to the real production camera/NextLevel lifecycle: stop/release production capture before QR AVCaptureSession starts, reject scan if ownership cannot be acquired, and restore/restart capture ownership cleanly when scanning ends/cancels/fails.
6. Add Swift tests for valid manual and QR pairing, expired offer, wrong version, malformed payload, wrong receiver, reconnect persistence without code, acquisition failure, no concurrent production camera/scanner session and hand-back.

## Validation

Tests must drive production-used seams, not a parallel helper. Run focused tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and secrets/privacy/signing checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V03 log-only commit. All user-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
