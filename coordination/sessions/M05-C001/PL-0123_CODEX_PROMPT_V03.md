# PL-0123 — Codex Remediation Work Order V03

Task: **PL-0123 — Executable pinned TLS/auth boundary without OpenSSL dependency**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0123_CODEX_LOG_V03.md

## Authorization

TASKS.md must authorize `M05-BATCH-003 / READY / CODEX`. Preserve accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 plus accepted M03/M04. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Read the V02 audit first. Preserve useful implementation and close exactly these remaining gaps.

## Mandatory remediation

1. Preserve /v1/pair, PairingAuthenticator, TLSIdentity, HTTPS-only receiver and PinnedReceiverSessionDelegate.
2. Provide deterministic TLS test material generation/loading that does not depend on an external openssl executable on the normal Windows locked-test host. Use a declared test-only/library approach or checked-in non-secret synthetic test certificate/key only if project policy explicitly permits test fixtures; never commit production keys.
3. Run real HTTPS loopback tests through certificate validation/pinning rather than ssl._create_unverified_context for the pinning cases.
4. Prove successful pairing/authenticated request plus actual wrong-certificate-pin rejection, expired offer, replayed offer, wrong receiver and missing auth over the network /v1/pair + protected transfer endpoints.
5. Prove error responses/logs never expose pairing code, bearer token, private key path/content or other secrets.

## Validation

Tests must drive production-used seams, not a parallel helper. Run focused tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and secrets/privacy/signing checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V03 log-only commit. All user-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
