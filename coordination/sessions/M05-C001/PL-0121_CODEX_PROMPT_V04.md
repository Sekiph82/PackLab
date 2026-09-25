# PL-0121 — Codex Remediation Work Order V04

Task: **PL-0121 — Fix Swift negative decoder matrix for all V1 wire models**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_LOG_V04.md

TASKS.md must authorize `M05-BATCH-004 / READY / CODEX`. Preserve all 10 accepted M05 children, accepted M03/M04, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Preserve the accepted architecture. Close only the final independent-audit gap.

## Mandatory remediation

1. Preserve the shared golden fixture resource and successful Swift/Python round-trip tests.
2. Test unsupported protocol version/name with the correct production Swift type for each applicable model: TransferStatusMessage, TransferControlMessage, TransferCompletionAcknowledgement and TransferErrorEnvelope.
3. Do not decode completion/error/control payloads as TransferStatusMessage merely to force a throw.
4. Assert stable TransferWireError.unsupportedVersion versus malformed behavior as appropriate.
5. Keep Python negative-version/error mapping tests aligned with the same authoritative fixture/contract.

Run production-seam behavior tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V04 log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
