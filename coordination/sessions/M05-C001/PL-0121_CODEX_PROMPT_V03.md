# PL-0121 — Codex Remediation Work Order V03

Task: **PL-0121 — One authoritative Swift/Python golden Transfer Protocol contract**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0121_CODEX_LOG_V03.md

## Authorization

TASKS.md must authorize `M05-BATCH-003 / READY / CODEX`. Preserve accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 plus accepted M03/M04. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Read the V02 audit first. Preserve useful implementation and close exactly these remaining gaps.

## Mandatory remediation

1. Preserve the complete V1 create/chunk/status/control/completion/error models and HTTPS/version constants.
2. Make tests/fixtures/transfer-protocol-v1-golden.json available to the Swift test target as a test resource or generated authoritative equivalent sourced mechanically from that exact file.
3. Swift tests must decode/encode and compare all golden objects: create, chunk, status, cancel, resume, completion and error. Do not retype expected values independently.
4. Add fail-closed Swift decode validation for unsupported protocol versions/protocol names for status/completion/error/control as applicable, with stable error mapping.
5. Keep Python golden round-trip tests and prove both languages derive from the same fixture/contract.

## Validation

Tests must drive production-used seams, not a parallel helper. Run focused tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and secrets/privacy/signing checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V03 log-only commit. All user-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
